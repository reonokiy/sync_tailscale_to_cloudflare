# docker-bake.hcl
variable "DEFAULT_TAG" {
  default = "sync-tailscale-to-cloudflare:local"
}

variable "REGISTRY" {
  default = "ghcr.io/reonokiy"
}

variable "IMAGE_NAME" {
  default = "sync-tailscale-to-cloudflare"
}

variable "TAG" {
  default = "local"
}

variable "COMMIT_SHA" {
  default = "unknown"
}

# Define base target
target "_common" {
  dockerfile = "Dockerfile"
  context = "."
  platforms = ["linux/amd64", "linux/arm64"]
}

# Development target
target "default" {
  inherits = ["_common"]
  tags = ["${DEFAULT_TAG}"]
}

# Production target for latest (master branch)
target "latest" {
  inherits = ["_common"]
  tags = [
    "${REGISTRY}/${IMAGE_NAME}:latest",
    "${REGISTRY}/${IMAGE_NAME}:master",
    "${REGISTRY}/${IMAGE_NAME}:${COMMIT_SHA}"
  ]
  cache-from = ["type=gha"]
  cache-to = ["type=gha,mode=max"]
}

# Production target for tagged releases
target "release" {
  inherits = ["_common"]
  tags = [
    "${REGISTRY}/${IMAGE_NAME}:${TAG}",
    "${REGISTRY}/${IMAGE_NAME}:latest"
  ]
  cache-from = ["type=gha"]
  cache-to = ["type=gha,mode=max"]
}

# Group for building all targets
group "default" {
  targets = ["default"]
}

group "release" {
  targets = ["release"]
}

group "latest" {
  targets = ["latest"]
}
