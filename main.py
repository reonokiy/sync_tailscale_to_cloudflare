import os
import re
import sys
import logging
import argparse
from typing import Dict, List, Optional, Tuple
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class TailscaleAPI:
    """Tailscale API client for retrieving device information."""

    def __init__(self, api_key: str, tailnet: str):
        self.api_key = api_key
        self.tailnet = tailnet
        self.base_url = "https://api.tailscale.com/api/v2"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def get_devices(self) -> List[Dict]:
        """Get all devices in the tailnet."""
        url = f"{self.base_url}/tailnet/{self.tailnet}/devices"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            print(f"Retrieved {data.get('devices', [])}")
            return data.get("devices", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get devices from Tailscale: {e}")
            return []

    def get_device_mappings(
        self,
        name_pattern: Optional[str] = None,
        tags_filter: Optional[List[str]] = None,
        skip_offline: bool = False,
    ) -> Dict[str, str]:
        """Get device name to IP mappings."""
        devices = self.get_devices()
        mappings = {}

        name_regex = re.compile(name_pattern) if name_pattern else None

        for device in devices:
            # Skip offline devices only if requested
            if skip_offline and not device.get("online", False):
                logger.debug(
                    f"Skipping offline device: {device.get('hostname', 'unknown')}"
                )
                continue

            hostname = device.get("hostname", "").lower()
            # Extract hostname from the name field (format: hostname.domain.ts.net)
            device_name = device.get("name", "")
            if device_name and "." in device_name:
                hostname = device_name.split(".")[0].lower()
            elif not hostname:
                # Fallback to hostname field if name extraction fails
                hostname = device.get("hostname", "").lower()

            addresses = device.get("addresses", [])

            if not hostname or not addresses:
                continue

            # Filter by name pattern
            if name_regex and not name_regex.match(hostname):
                continue

            # Filter by tags
            if tags_filter:
                device_tags = [tag.lower() for tag in device.get("tags", [])]
                if not any(tag.lower() in device_tags for tag in tags_filter):
                    continue

            # Use the first IPv4 address (Tailscale addresses are typically first)
            tailscale_ip = None
            for addr in addresses:
                # Skip IPv6 addresses and find the Tailscale IPv4 address
                if ":" not in addr and addr.startswith("100."):
                    tailscale_ip = addr
                    break

            if tailscale_ip:
                mappings[hostname] = tailscale_ip
                logger.info(f"Found device: {hostname} -> {tailscale_ip}")

        return mappings


class CloudflareAPI:
    """Cloudflare API client for managing DNS records."""

    def __init__(
        self,
        api_token: str,
        zone_id: str,
        domain: str,
        base_domain: Optional[str] = None,
    ):
        self.api_token = api_token
        self.zone_id = zone_id
        self.domain = domain  # The main domain (e.g., example.com)
        # Base domain for DNS records (e.g., tailscale.example.com or just example.com)
        self.base_domain = base_domain or domain
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

    def get_dns_records(self, record_type: str = "A") -> List[Dict]:
        """Get all DNS records of specified type."""
        url = f"{self.base_url}/zones/{self.zone_id}/dns_records"
        params = {"type": record_type}

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("result", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get DNS records from Cloudflare: {e}")
            return []

    def create_dns_record(
        self, name: str, content: str, record_type: str = "A"
    ) -> bool:
        """Create a new DNS record."""
        url = f"{self.base_url}/zones/{self.zone_id}/dns_records"
        data = {
            "type": record_type,
            "name": name,
            "content": content,
            "ttl": 300,  # 5 minutes
        }

        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            logger.info(f"Created DNS record: {name} -> {content}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create DNS record {name}: {e}")
            return False

    def update_dns_record(
        self, record_id: str, name: str, content: str, record_type: str = "A"
    ) -> bool:
        """Update an existing DNS record."""
        url = f"{self.base_url}/zones/{self.zone_id}/dns_records/{record_id}"
        data = {"type": record_type, "name": name, "content": content, "ttl": 300}

        try:
            response = requests.put(url, headers=self.headers, json=data)
            response.raise_for_status()
            logger.info(f"Updated DNS record: {name} -> {content}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update DNS record {name}: {e}")
            return False

    def delete_dns_record(self, record_id: str, name: str) -> bool:
        """Delete a DNS record."""
        url = f"{self.base_url}/zones/{self.zone_id}/dns_records/{record_id}"

        try:
            response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            logger.info(f"Deleted DNS record: {name}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to delete DNS record {name}: {e}")
            return False


class NotificationService:
    """Service for sending notifications via ntfy.sh."""

    def __init__(
        self, ntfy_topic: Optional[str] = None, ntfy_server: str = "https://ntfy.sh"
    ):
        self.ntfy_topic = ntfy_topic
        self.ntfy_server = ntfy_server.rstrip("/")
        self.enabled = bool(ntfy_topic)

    def send_notification(
        self,
        message: str,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        priority: int = 3,
    ) -> bool:
        """
        Send a notification via ntfy.sh.

        Args:
            message: The notification message
            title: Optional title for the notification
            tags: Optional list of tags/emojis
            priority: Priority level (1=min, 3=default, 5=max)
        """
        if not self.enabled:
            logger.debug("Notifications disabled (no NTFY_TOPIC configured)")
            return True

        url = f"{self.ntfy_server}/{self.ntfy_topic}"
        headers = {
            "Content-Type": "text/plain; charset=utf-8",
            "X-Priority": str(priority),
        }

        if title:
            headers["X-Title"] = title

        if tags:
            headers["X-Tags"] = ",".join(tags)

        try:
            response = requests.post(
                url, data=message.encode("utf-8"), headers=headers, timeout=10
            )
            response.raise_for_status()
            logger.debug(f"Notification sent successfully to {self.ntfy_topic}")
            return True
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to send notification: {e}")
            return False

    def send_sync_success(
        self, created: int, updated: int, deleted: int, dry_run: bool = False
    ) -> bool:
        """Send a success notification for sync completion."""
        mode = "DRY RUN" if dry_run else "SYNC"
        title = f"Tailscale DNS {mode} Complete"

        if created == 0 and updated == 0 and deleted == 0:
            message = "No DNS changes needed - all records are up to date! ✅"
            tags = ["white_check_mark"]
        else:
            changes = []
            if created > 0:
                changes.append(f"{created} created")
            if updated > 0:
                changes.append(f"{updated} updated")
            if deleted > 0:
                changes.append(f"{deleted} deleted")

            message = f"DNS records {', '.join(changes)} successfully! 🎉"
            tags = ["partying_face", "dns"]

        return self.send_notification(message, title, tags)

    def send_sync_failure(self, error_msg: str, dry_run: bool = False) -> bool:
        """Send a failure notification for sync errors."""
        mode = "DRY RUN" if dry_run else "SYNC"
        title = f"Tailscale DNS {mode} Failed"
        message = f"Synchronization failed: {error_msg} ❌"
        tags = ["x", "warning"]

        return self.send_notification(message, title, tags, priority=4)


class DNSSync:
    """Main synchronization class."""

    def __init__(
        self,
        tailscale_api: TailscaleAPI,
        cloudflare_api: CloudflareAPI,
        notification_service: Optional[NotificationService] = None,
    ):
        self.tailscale = tailscale_api
        self.cloudflare = cloudflare_api
        self.notification = notification_service

    def sync(
        self,
        name_pattern: Optional[str] = None,
        tags_filter: Optional[List[str]] = None,
        skip_offline: bool = False,
        dry_run: bool = False,
    ) -> Tuple[int, int, int]:
        """
        Sync Tailscale devices to Cloudflare DNS.

        Returns:
            Tuple of (created, updated, deleted) record counts
        """
        logger.info("Starting DNS synchronization...")

        # Get current device mappings from Tailscale
        tailscale_devices = self.tailscale.get_device_mappings(
            name_pattern, tags_filter, skip_offline
        )
        if not tailscale_devices:
            logger.warning("No devices found in Tailscale")
            return 0, 0, 0

        # Get current DNS records from Cloudflare
        dns_records = self.cloudflare.get_dns_records("A")

        # Build current DNS mapping (name -> {record_id, content})
        dns_mapping = {}
        for record in dns_records:
            name = record["name"]
            # Only consider records that match our base domain pattern
            if name.endswith(f".{self.cloudflare.base_domain}"):
                hostname = name.replace(f".{self.cloudflare.base_domain}", "")
                dns_mapping[hostname] = {
                    "id": record["id"],
                    "content": record["content"],
                    "full_name": name,
                }

        created = updated = deleted = 0

        # Create or update records for Tailscale devices
        for hostname, ip in tailscale_devices.items():
            full_name = f"{hostname}.{self.cloudflare.base_domain}"

            if hostname in dns_mapping:
                # Record exists, check if IP changed
                if dns_mapping[hostname]["content"] != ip:
                    logger.info(
                        f"IP changed for {hostname}: {dns_mapping[hostname]['content']} -> {ip}"
                    )
                    if not dry_run:
                        if self.cloudflare.update_dns_record(
                            dns_mapping[hostname]["id"], full_name, ip
                        ):
                            updated += 1
                    else:
                        logger.info(f"[DRY RUN] Would update {hostname} to {ip}")
                        updated += 1
                else:
                    logger.debug(f"No change needed for {hostname}")
                # Remove from DNS mapping so we don't delete it later
                del dns_mapping[hostname]
            else:
                # New device, create DNS record
                logger.info(f"Creating new DNS record for {hostname} -> {ip}")
                if not dry_run:
                    if self.cloudflare.create_dns_record(full_name, ip):
                        created += 1
                else:
                    logger.info(f"[DRY RUN] Would create {hostname} -> {ip}")
                    created += 1

        # Delete records for devices no longer in Tailscale
        for hostname, record_info in dns_mapping.items():
            logger.info(f"Deleting DNS record for removed device: {hostname}")
            if not dry_run:
                if self.cloudflare.delete_dns_record(record_info["id"], hostname):
                    deleted += 1
            else:
                logger.info(f"[DRY RUN] Would delete {hostname}")
                deleted += 1

        logger.info(
            f"Sync complete: {created} created, {updated} updated, {deleted} deleted"
        )
        return created, updated, deleted


def main():
    """Main entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Sync Tailscale device names and IPs to Cloudflare DNS A records",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Normal sync
  %(prog)s --dry-run          # Preview changes without applying them
  %(prog)s --verbose          # Enable debug logging

Configuration:
  All configuration is done via environment variables in .env file.
  See .env.example for required variables.
        """,
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without applying them"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable debug logging"
    )
    parser.add_argument(
        "--skip-offline",
        action="store_true",
        help="Skip offline devices (default: include offline devices)",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load environment variables
    load_dotenv()

    # Get configuration from environment
    tailscale_api_key = os.getenv("TAILSCALE_API_KEY")
    tailscale_tailnet = os.getenv("TAILSCALE_TAILNET")
    cloudflare_api_token = os.getenv("CLOUDFLARE_API_TOKEN")
    cloudflare_zone_id = os.getenv("CLOUDFLARE_ZONE_ID")
    cloudflare_domain = os.getenv("CLOUDFLARE_DOMAIN")
    # Base domain for DNS records (e.g., tailscale.example.com)
    # If not specified, defaults to the main domain
    cloudflare_base_domain = os.getenv("CLOUDFLARE_BASE_DOMAIN")

    # Notification configuration
    ntfy_topic = os.getenv("NTFY_TOPIC")
    ntfy_server = os.getenv("NTFY_SERVER", "https://ntfy.sh")

    # Optional filters
    device_name_pattern = os.getenv("DEVICE_NAME_PATTERN")
    device_tags = os.getenv("DEVICE_TAGS")
    tags_filter = (
        [tag.strip() for tag in device_tags.split(",")] if device_tags else None
    )

    # Validate required configuration
    required_vars = {
        "TAILSCALE_API_KEY": tailscale_api_key,
        "TAILSCALE_TAILNET": tailscale_tailnet,
        "CLOUDFLARE_API_TOKEN": cloudflare_api_token,
        "CLOUDFLARE_ZONE_ID": cloudflare_zone_id,
        "CLOUDFLARE_DOMAIN": cloudflare_domain,
    }

    missing_vars = [var for var, value in required_vars.items() if not value]
    if missing_vars:
        logger.error(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
        logger.error(
            "Please check your .env file and ensure all required variables are set."
        )
        logger.error("See .env.example for a template with all required variables.")
        sys.exit(1)

    # Initialize notification service
    notification_service = NotificationService(ntfy_topic, ntfy_server)

    try:
        # Initialize API clients - we can safely cast to str since we validated above
        tailscale_api = TailscaleAPI(str(tailscale_api_key), str(tailscale_tailnet))
        cloudflare_api = CloudflareAPI(
            str(cloudflare_api_token),
            str(cloudflare_zone_id),
            str(cloudflare_domain),
            cloudflare_base_domain,  # This can be None, which will default to cloudflare_domain
        )

        # Create DNS sync instance and run
        dns_sync = DNSSync(tailscale_api, cloudflare_api, notification_service)

        if args.dry_run:
            logger.info("Running in dry-run mode - no actual changes will be made")

        created, updated, deleted = dns_sync.sync(
            name_pattern=device_name_pattern,
            tags_filter=tags_filter,
            skip_offline=args.skip_offline,
            dry_run=args.dry_run,
        )

        logger.info("Synchronization completed successfully!")
        logger.info(
            f"Summary: {created} records created, {updated} updated, {deleted} deleted"
        )

        # Send success notification
        notification_service.send_sync_success(created, updated, deleted, args.dry_run)

    except Exception as e:
        logger.error(f"Synchronization failed: {e}")

        # Send failure notification
        notification_service.send_sync_failure(str(e), args.dry_run)

        if args.verbose:
            import traceback

            logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
