# Justfile for sync-tailscale-to-cloudflare project

# Default registry and image configuration
registry := env_var_or_default("REGISTRY", "ghcr.io/reonokiy")
image_name := env_var_or_default("IMAGE_NAME", "sync-tailscale-to-cloudflare")
tag := env_var_or_default("TAG", "local")
commit_sha := `git rev-parse --short HEAD 2>/dev/null || echo "unknown"`

# List all available commands
default:
    @just --list

# Build local development image
build:
    @echo "📦 Building local development image..."
    docker buildx bake default

# Build latest images (for main branch)
build-latest:
    @echo "📦 Building latest images with commit hash: {{commit_sha}}..."
    REGISTRY={{registry}} IMAGE_NAME={{image_name}} COMMIT_SHA={{commit_sha}} docker buildx bake latest

# Build release images with tag
build-release tag=tag:
    @echo "📦 Building release images with tag: {{tag}}"
    REGISTRY={{registry}} IMAGE_NAME={{image_name}} TAG={{tag}} docker buildx bake release

# Push latest images to registry
push-latest:
    @echo "🚀 Building and pushing latest images with commit hash: {{commit_sha}}..."
    REGISTRY={{registry}} IMAGE_NAME={{image_name}} COMMIT_SHA={{commit_sha}} docker buildx bake latest --push

# Push release images with tag to registry
push-release tag=tag:
    @echo "🚀 Building and pushing release images with tag: {{tag}}"
    REGISTRY={{registry}} IMAGE_NAME={{image_name}} TAG={{tag}} docker buildx bake release --push

# Clean up local images
clean:
    @echo "🧹 Cleaning up local images..."
    docker image prune -f
    docker builder prune -f

# Run the built image locally
run *args="":
    @echo "🏃 Running local image..."
    docker run --rm -it --env-file .env {{registry}}/{{image_name}}:local {{args}}

# Run with dry-run mode
run-dry:
    @echo "🔍 Running in dry-run mode..."
    docker run --rm -it --env-file .env -e DRY_RUN=true {{registry}}/{{image_name}}:local

# Show Docker Bake configuration
show-config:
    @echo "🔍 Docker Bake configuration:"
    docker buildx bake --print

# Validate Dockerfile
validate:
    @echo "✅ Validating Dockerfile..."
    docker run --rm -i hadolint/hadolint < Dockerfile

# Install just (if not already installed)
install-just:
    @echo "📥 Installing just..."
    curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to ~/bin

# Show help
help:
    @echo "🐳 Docker Bake Commands for sync-tailscale-to-cloudflare"
    @echo ""
    @echo "Build commands:"
    @echo "  just build         - Build local development image"
    @echo "  just build-latest  - Build latest images"
    @echo "  just build-release TAG - Build release images with tag"
    @echo ""
    @echo "Push commands:"
    @echo "  just push-latest   - Build and push latest images"
    @echo "  just push-release TAG - Build and push release images"
    @echo ""
    @echo "Run commands:"
    @echo "  just run [args]    - Run the built image locally"
    @echo "  just run-dry       - Run in dry-run mode"
    @echo ""
    @echo "Utility commands:"
    @echo "  just clean         - Clean up local images"
    @echo "  just show-config   - Show Docker Bake configuration"
    @echo "  just validate      - Validate Dockerfile with hadolint"
    @echo ""
    @echo "Environment variables:"
    @echo "  REGISTRY={{registry}}"
    @echo "  IMAGE_NAME={{image_name}}"
    @echo "  TAG={{tag}}"
    @echo "  COMMIT_SHA={{commit_sha}}"
