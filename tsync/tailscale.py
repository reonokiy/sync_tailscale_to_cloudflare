"""Tailscale API client abstractions."""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class TailscaleAPI:
    """Client wrapper for the Tailscale REST API."""

    base_url = "https://api.tailscale.com/api/v2"

    def __init__(self, api_key: str, tailnet: str) -> None:
        self.api_key = api_key
        self.tailnet = tailnet
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def get_devices(self) -> List[Dict]:
        """Return all devices listed in the configured tailnet."""
        url = f"{self.base_url}/tailnet/{self.tailnet}/devices"

        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            logger.error("Failed to retrieve devices from Tailscale: %s", exc)
            return []

        data = response.json()
        return data.get("devices", [])

    def get_device_mappings(
        self,
        name_pattern: Optional[str] = None,
        tags_filter: Optional[List[str]] = None,
        skip_offline: bool = False,
    ) -> Dict[str, str]:
        """
        Build a mapping of device hostname to IPv4 address.

        The mapping only includes devices that match the optional filters.
        """
        devices = self.get_devices()
        mappings: Dict[str, str] = {}

        name_regex = re.compile(name_pattern) if name_pattern else None

        for device in devices:
            if skip_offline and not device.get("online", False):
                logger.debug(
                    "Skipping offline device %s",
                    device.get("hostname", "unknown"),
                )
                continue

            hostname = device.get("hostname", "").lower()
            device_name = device.get("name", "")

            if device_name and "." in device_name:
                hostname = device_name.split(".")[0].lower()
            elif not hostname:
                hostname = device.get("hostname", "").lower()

            addresses = device.get("addresses", [])
            if not hostname or not addresses:
                continue

            if name_regex and not name_regex.match(hostname):
                continue

            if tags_filter:
                device_tags = [tag.lower() for tag in device.get("tags", [])]
                if not any(tag.lower() in device_tags for tag in tags_filter):
                    continue

            tailscale_ip = None
            for addr in addresses:
                if ":" not in addr and addr.startswith("100."):
                    tailscale_ip = addr
                    break

            if tailscale_ip:
                mappings[hostname] = tailscale_ip
                logger.info("Discovered device %s -> %s", hostname, tailscale_ip)

        return mappings
