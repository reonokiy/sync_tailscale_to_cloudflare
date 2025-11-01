"""Cloudflare DNS API helpers."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class CloudflareAPI:
    """Client wrapper for Cloudflare DNS record management."""

    base_url = "https://api.cloudflare.com/client/v4"

    def __init__(
        self,
        api_token: str,
        zone_id: str,
        domain: str,
        base_domain: Optional[str] = None,
        create_wildcard_records: bool = False,
    ) -> None:
        self.api_token = api_token
        self.zone_id = zone_id
        self.domain = domain
        self.base_domain = base_domain or domain
        self.create_wildcard_records = create_wildcard_records
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

    def get_dns_records(self, record_type: str = "A") -> List[Dict]:
        """Return all DNS records of the requested type."""
        url = f"{self.base_url}/zones/{self.zone_id}/dns_records"
        params = {"type": record_type}

        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=15,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            logger.error("Failed to retrieve Cloudflare DNS records: %s", exc)
            return []

        data = response.json()
        return data.get("result", [])

    def create_dns_record(
        self,
        name: str,
        content: str,
        record_type: str = "A",
    ) -> bool:
        """Create a new DNS record."""
        url = f"{self.base_url}/zones/{self.zone_id}/dns_records"
        payload = {
            "type": record_type,
            "name": name,
            "content": content,
            "ttl": 300,
        }

        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=15,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            logger.error("Failed to create DNS record %s: %s", name, exc)
            return False

        logger.info("Created DNS record %s -> %s", name, content)
        return True

    def update_dns_record(
        self,
        record_id: str,
        name: str,
        content: str,
        record_type: str = "A",
    ) -> bool:
        """Update an existing DNS record."""
        url = f"{self.base_url}/zones/{self.zone_id}/dns_records/{record_id}"
        payload = {
            "type": record_type,
            "name": name,
            "content": content,
            "ttl": 300,
        }

        try:
            response = requests.put(
                url,
                headers=self.headers,
                json=payload,
                timeout=15,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            logger.error("Failed to update DNS record %s: %s", name, exc)
            return False

        logger.info("Updated DNS record %s -> %s", name, content)
        return True

    def delete_dns_record(self, record_id: str, name: str) -> bool:
        """Delete a DNS record."""
        url = f"{self.base_url}/zones/{self.zone_id}/dns_records/{record_id}"

        try:
            response = requests.delete(
                url,
                headers=self.headers,
                timeout=15,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            logger.error("Failed to delete DNS record %s: %s", name, exc)
            return False

        logger.info("Deleted DNS record %s", name)
        return True
