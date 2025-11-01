"""Synchronization logic tying Tailscale and Cloudflare together."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from .cloudflare import CloudflareAPI
from .tailscale import TailscaleAPI

logger = logging.getLogger(__name__)


class DNSSync:
    """Synchronize Tailscale devices into Cloudflare DNS records."""

    def __init__(
        self,
        tailscale_api: TailscaleAPI,
        cloudflare_api: CloudflareAPI,
    ) -> None:
        self.tailscale = tailscale_api
        self.cloudflare = cloudflare_api

    def sync(
        self,
        name_pattern: Optional[str] = None,
        tags_filter: Optional[List[str]] = None,
        skip_offline: bool = False,
        dry_run: bool = False,
    ) -> Tuple[int, int, int]:
        """Synchronize device mappings and return counts of created/updated/deleted."""
        logger.info("Starting DNS synchronization.")

        tailscale_devices = self.tailscale.get_device_mappings(
            name_pattern=name_pattern,
            tags_filter=tags_filter,
            skip_offline=skip_offline,
        )

        if not tailscale_devices:
            logger.warning("No matching devices found in Tailscale.")
            return 0, 0, 0

        dns_records = self.cloudflare.get_dns_records("A")
        dns_mapping: Dict[str, Dict[str, str]] = {}
        wildcard_mapping: Dict[str, Dict[str, str]] = {}

        for record in dns_records:
            name = record["name"]
            if not name.endswith(f".{self.cloudflare.base_domain}"):
                continue

            hostname = name.replace(f".{self.cloudflare.base_domain}", "")
            record_info = {
                "id": record["id"],
                "content": record["content"],
                "full_name": name,
            }

            if hostname.startswith("*."):
                wildcard_mapping[hostname[2:]] = record_info
            else:
                dns_mapping[hostname] = record_info

        created = updated = deleted = 0

        for hostname, ip in tailscale_devices.items():
            full_name = f"{hostname}.{self.cloudflare.base_domain}"
            wildcard_name = f"*.{hostname}.{self.cloudflare.base_domain}"

            if hostname in dns_mapping:
                current_ip = dns_mapping[hostname]["content"]
                if current_ip != ip:
                    logger.info("Updating %s: %s -> %s", hostname, current_ip, ip)
                    if dry_run:
                        updated += 1
                    elif self.cloudflare.update_dns_record(
                        dns_mapping[hostname]["id"],
                        full_name,
                        ip,
                    ):
                        updated += 1
                else:
                    logger.debug("No change required for %s", hostname)
                dns_mapping.pop(hostname, None)
            else:
                logger.info("Creating DNS record for %s -> %s", hostname, ip)
                if dry_run:
                    created += 1
                elif self.cloudflare.create_dns_record(full_name, ip):
                    created += 1

            if self.cloudflare.create_wildcard_records:
                if hostname in wildcard_mapping:
                    current_ip = wildcard_mapping[hostname]["content"]
                    if current_ip != ip:
                        logger.info(
                            "Updating wildcard *.%s: %s -> %s",
                            hostname,
                            current_ip,
                            ip,
                        )
                        if dry_run:
                            updated += 1
                        elif self.cloudflare.update_dns_record(
                            wildcard_mapping[hostname]["id"],
                            wildcard_name,
                            ip,
                        ):
                            updated += 1
                    wildcard_mapping.pop(hostname, None)
                else:
                    logger.info(
                        "Creating wildcard DNS record for *.%s -> %s",
                        hostname,
                        ip,
                    )
                    if dry_run:
                        created += 1
                    elif self.cloudflare.create_dns_record(wildcard_name, ip):
                        created += 1

        for hostname, record_info in dns_mapping.items():
            logger.info("Deleting DNS record for stale device %s", hostname)
            if dry_run:
                deleted += 1
            elif self.cloudflare.delete_dns_record(record_info["id"], hostname):
                deleted += 1

        if self.cloudflare.create_wildcard_records:
            for hostname, record_info in wildcard_mapping.items():
                logger.info("Deleting wildcard DNS record for stale device *.%s", hostname)
                if dry_run:
                    deleted += 1
                elif self.cloudflare.delete_dns_record(
                    record_info["id"],
                    f"*.{hostname}",
                ):
                    deleted += 1

        logger.info(
            "Sync complete: %s created, %s updated, %s deleted",
            created,
            updated,
            deleted,
        )
        return created, updated, deleted
