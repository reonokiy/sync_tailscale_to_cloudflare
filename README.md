# Tailscale to Cloudflare DNS Sync

[![Docker Build](https://github.com/reonokiy/sync_tailscale_to_cloudflare/actions/workflows/docker.yml/badge.svg)](https://github.com/reonokiy/sync_tailscale_to_cloudflare/actions/workflows/docker.yml)
[![Docker Image](https://img.shields.io/badge/docker-ghcr.io-blue.svg)](https://github.com/reonokiy/sync_tailscale_to_cloudflare/pkgs/container/sync_tailscale_to_cloudflare)

Synchronise your Tailscale network with Cloudflare DNS. The tool fetches device
hostnames and IPv4 addresses from the Tailscale API and keeps matching
Cloudflare `A` records up to date. It can run locally or inside Docker, supports
dry-run previews, and ships with optional ntfy.sh notifications.

## Features

- Automatic sync from Tailscale devices to Cloudflare DNS
- Flexible filtering based on tags and hostname rules
- Dry-run mode to preview planned DNS changes
- Detailed logging with optional verbose/debug output
- Incremental updates reduce unnecessary API calls
- Optional wildcard records per device (`*.hostname.domain`)
- Optional ntfy.sh notifications (success and failure)
- Docker and multi-architecture support (`linux/amd64`, `linux/arm64`)
- GitHub Actions workflow for automated container publishing

## Quick Start

### Docker (recommended)

```bash
# Pull the latest image
docker pull ghcr.io/reonokiy/tsync:latest

# Download the sample environment file
curl -o .env https://raw.githubusercontent.com/reonokiy/sync_tailscale_to_cloudflare/master/.env.example

# Edit .env and enter your API credentials
nano .env

# Preview DNS changes without applying them
docker run --rm --env-file .env -e DRY_RUN=true \
  ghcr.io/reonokiy/tsync:latest

# Apply the changes
docker run --rm --env-file .env \
  ghcr.io/reonokiy/tsync:latest
```

### Local execution

```bash
git clone https://github.com/reonokiy/sync_tailscale_to_cloudflare.git
cd sync_tailscale_to_cloudflare

# Install dependencies (uv recommended)
uv sync
# or
pip install -e .

# Copy the sample configuration and fill it in
cp .env.example .env

# Run the synchronisation
python -m tsync
```

### Run on a schedule

**Docker Compose**

```yaml
version: "3.8"
services:
  tailscale-dns-sync:
    image: ghcr.io/reonokiy/tsync:latest
    env_file: .env
    restart: unless-stopped
    command: >
      sh -c '
        while true; do
          echo "$(date): Starting Tailscale DNS sync...";
          python3 -m tsync;
          echo "$(date): Sync completed, sleeping for 5 minutes...";
          sleep 300;
        done
      '
```

```bash
docker compose up -d
```

**cron**

```bash
*/5 * * * * docker run --rm --env-file /path/to/.env \
  ghcr.io/reonokiy/tsync:latest
```

## Configuration

Populate the following environment variables (or use a `.env` file alongside
`python-dotenv`).

### Required

| Variable | Description |
| --- | --- |
| `TAILSCALE_API_KEY` | Tailscale API key with `Devices:Read` scope |
| `TAILSCALE_TAILNET` | Tailnet name (e.g. `example.com`) |
| `CLOUDFLARE_API_TOKEN` | Cloudflare API token with `Zone:Read` + `DNS:Edit` |
| `CLOUDFLARE_ZONE_ID` | Cloudflare zone identifier |
| `CLOUDFLARE_DOMAIN` | Root domain (e.g. `example.com`) |

### Optional

| Variable | Default | Description |
| --- | --- | --- |
| `CLOUDFLARE_BASE_DOMAIN` | `CLOUDFLARE_DOMAIN` | Alternate DNS suffix for records |
| `CREATE_WILDCARD_RECORDS` | `true` | Manage `*.hostname` records in addition to root |
| `DEVICE_NAME_PATTERN` | None | Regular expression to filter device hostnames |
| `DEVICE_TAG_FILTER` | None | Comma-separated list of required tags (`DEVICE_TAGS` is also honoured) |
| `NTFY_TOPIC` | None | ntfy.sh topic for notifications |
| `NTFY_SERVER` | `https://ntfy.sh` | Custom ntfy-compatible endpoint |

### CLI flags

| Flag | Purpose |
| --- | --- |
| `--dry-run` | Preview changes without touching DNS |
| `--verbose` / `-v` | Enable debug logging |
| `--skip-offline` | Skip devices that are currently offline |

## How it works

1. Fetch the device list from Tailscale.
2. Apply optional filters (tags and hostname regex).
3. Fetch existing `A` records from Cloudflare for the configured base domain.
4. Compute the delta (create, update, delete).
5. Call the Cloudflare API to apply the changes (or log them in dry-run mode).
6. Optionally send a notification summarising the result.

Records are created as `<hostname>.<base-domain> -> 100.x.x.x`. When wildcard
management is enabled, matching `*.hostname.<base-domain>` records are created or
updated alongside the primary record.

## Docker build & release

The repository includes `docker-bake.hcl` and [Just](https://just.systems/)
recipes.

```bash
just help            # list commands
just build           # local development build
just run-dry         # run the local image in dry-run mode
just build-latest    # build multi-arch images tagged latest/master
just push-latest     # push latest/master/commit-hash tags
just build-release v1.2.3
just push-release v1.2.3
```

Customise the registry/image name with environment variables:

```bash
export REGISTRY=ghcr.io/your-username
export IMAGE_NAME=your-image-name
just build-latest
```

GitHub Actions automatically builds and publishes images when you push to
`master`, push a tag matching `v*`, or open a pull request.

## Troubleshooting

- Use `--dry-run` before applying changes to confirm the planned updates.
- Run with `--verbose` to collect detailed logs for support tickets.
- Ensure your Cloudflare token has both `Zone:Read` and `DNS:Edit` permissions.
- Device tags must exist in Tailscale and be authorised before use.

## License

Released under the MIT License. See `LICENSE` for details.
