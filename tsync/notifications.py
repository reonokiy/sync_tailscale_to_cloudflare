"""Notification helpers built on ntfy.sh."""

from __future__ import annotations

import logging
from typing import List, Optional

import requests

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending optional ntfy.sh notifications."""

    def __init__(
        self,
        ntfy_topic: Optional[str] = None,
        ntfy_server: str = "https://ntfy.sh",
    ) -> None:
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
        """Send a raw notification payload to ntfy.sh."""
        if not self.enabled:
            logger.debug("Notifications disabled because NTFY_TOPIC is not set")
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
                url,
                data=message.encode("utf-8"),
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            logger.warning("Failed to send notification: %s", exc)
            return False

        logger.debug("Notification sent to %s", self.ntfy_topic)
        return True

    def send_sync_success(
        self,
        created: int,
        updated: int,
        deleted: int,
        dry_run: bool = False,
    ) -> bool:
        """Send a summary notification when synchronization succeeds."""
        mode = "DRY RUN" if dry_run else "SYNC"
        title = f"Tailscale DNS {mode} Complete"

        if created == 0 and updated == 0 and deleted == 0:
            message = "No DNS changes were required."
            tags = ["success"]
        else:
            changes = []
            if created > 0:
                changes.append(f"{created} created")
            if updated > 0:
                changes.append(f"{updated} updated")
            if deleted > 0:
                changes.append(f"{deleted} deleted")
            message = f"DNS records {', '.join(changes)} successfully."
            tags = ["info", "dns"]

        return self.send_notification(message, title, tags)

    def send_sync_failure(self, error_msg: str, dry_run: bool = False) -> bool:
        """Send an error notification when synchronization fails."""
        mode = "DRY RUN" if dry_run else "SYNC"
        title = f"Tailscale DNS {mode} Failed"
        message = f"Synchronization failed: {error_msg}"
        tags = ["error", "warning"]

        return self.send_notification(message, title, tags, priority=4)
