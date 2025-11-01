"""Command line interface for the Tailscale to Cloudflare sync tool."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from dotenv import load_dotenv

from .cloudflare import CloudflareAPI
from .notifications import NotificationService
from .sync import DNSSync
from .tailscale import TailscaleAPI


@dataclass
class AppConfig:
    """Container for environment configuration values."""

    tailscale_api_key: str
    tailscale_tailnet: str
    cloudflare_api_token: str
    cloudflare_zone_id: str
    cloudflare_domain: str
    cloudflare_base_domain: Optional[str]
    create_wildcard_records: bool
    device_name_pattern: Optional[str]
    device_tags: Optional[List[str]]
    ntfy_topic: Optional[str]
    ntfy_server: str


def configure_logging(verbose: bool) -> None:
    """Configure root logging handlers."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Sync Tailscale device names and IPs to Cloudflare DNS A records",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s                    # Normal sync\n"
            "  %(prog)s --dry-run          # Preview changes without applying them\n"
            "  %(prog)s --verbose          # Enable debug logging\n\n"
            "Configuration:\n"
            "  All configuration is done via environment variables in a .env file.\n"
            "  See .env.example for required variables."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--skip-offline",
        action="store_true",
        help="Skip offline devices (default: include offline devices)",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    return parser.parse_args(argv)


def _parse_bool(value: Optional[str], default: bool = False) -> bool:
    """Convert truthy environment values into booleans."""
    if value is None:
        return default
    return value.strip().lower() in {"true", "1", "yes", "on"}


def _parse_list(value: Optional[str]) -> Optional[List[str]]:
    """Convert a comma-separated string into a list of strings."""
    if not value:
        return None
    items = [item.strip() for item in value.split(",")]
    return [item for item in items if item]


def load_config() -> AppConfig:
    """Load application configuration from environment variables."""
    config = AppConfig(
        tailscale_api_key=os.getenv("TAILSCALE_API_KEY", ""),
        tailscale_tailnet=os.getenv("TAILSCALE_TAILNET", ""),
        cloudflare_api_token=os.getenv("CLOUDFLARE_API_TOKEN", ""),
        cloudflare_zone_id=os.getenv("CLOUDFLARE_ZONE_ID", ""),
        cloudflare_domain=os.getenv("CLOUDFLARE_DOMAIN", ""),
        cloudflare_base_domain=os.getenv("CLOUDFLARE_BASE_DOMAIN"),
        create_wildcard_records=_parse_bool(
            os.getenv("CREATE_WILDCARD_RECORDS"),
            default=True,
        ),
        device_name_pattern=os.getenv("DEVICE_NAME_PATTERN"),
        device_tags=_parse_list(
            os.getenv("DEVICE_TAG_FILTER") or os.getenv("DEVICE_TAGS")
        ),
        ntfy_topic=os.getenv("NTFY_TOPIC"),
        ntfy_server=os.getenv("NTFY_SERVER", "https://ntfy.sh"),
    )

    required_fields = {
        "TAILSCALE_API_KEY": config.tailscale_api_key,
        "TAILSCALE_TAILNET": config.tailscale_tailnet,
        "CLOUDFLARE_API_TOKEN": config.cloudflare_api_token,
        "CLOUDFLARE_ZONE_ID": config.cloudflare_zone_id,
        "CLOUDFLARE_DOMAIN": config.cloudflare_domain,
    }

    missing = [key for key, value in required_fields.items() if not value]
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

    return config


def run_sync(
    args: argparse.Namespace,
    config: AppConfig,
    notification_service: NotificationService,
) -> Tuple[int, int, int]:
    """Execute the synchronization and send notifications."""
    tailscale_api = TailscaleAPI(
        api_key=config.tailscale_api_key,
        tailnet=config.tailscale_tailnet,
    )
    cloudflare_api = CloudflareAPI(
        api_token=config.cloudflare_api_token,
        zone_id=config.cloudflare_zone_id,
        domain=config.cloudflare_domain,
        base_domain=config.cloudflare_base_domain,
        create_wildcard_records=config.create_wildcard_records,
    )

    dns_sync = DNSSync(tailscale_api, cloudflare_api)
    created, updated, deleted = dns_sync.sync(
        name_pattern=config.device_name_pattern,
        tags_filter=config.device_tags,
        skip_offline=args.skip_offline,
        dry_run=args.dry_run,
    )

    notification_service.send_sync_success(
        created,
        updated,
        deleted,
        args.dry_run,
    )

    return created, updated, deleted


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entrypoint."""
    args = parse_args(argv)
    configure_logging(args.verbose)

    load_dotenv()

    try:
        config = load_config()
    except ValueError as exc:
        logger = logging.getLogger(__name__)
        logger.error(str(exc))
        logger.error(
            "Please check your environment configuration. "
            "See .env.example for the required variables.",
        )
        return 1

    notification_service = NotificationService(
        config.ntfy_topic,
        config.ntfy_server,
    )

    try:
        created, updated, deleted = run_sync(args, config, notification_service)
        logger = logging.getLogger(__name__)
        logger.info(
            "Synchronization completed successfully: %s created, %s updated, %s deleted",
            created,
            updated,
            deleted,
        )
        return 0
    except Exception as exc:  # pylint: disable=broad-except
        logger = logging.getLogger(__name__)
        logger.error("Synchronization failed: %s", exc)
        notification_service.send_sync_failure(str(exc), args.dry_run)
        if args.verbose:
            logger.debug("Exception details", exc_info=True)
        return 1
