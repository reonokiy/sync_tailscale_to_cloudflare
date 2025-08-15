# Docker Build Guide

本项目使用 Docker Bake 和 Just 来管理 Docker 镜像的构建和发布。

## 前置要求

1. **Docker Buildx**: 确保已启用 Docker Buildx
   ```bash
   docker buildx version
   ```

2. **Just**: 命令运行器
   ```bash
   # 安装 just
   curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to ~/bin
   
   # 或者使用项目中的命令
   just install-just
   ```

## 快速开始

### 查看所有可用命令
```bash
just
# 或者
just help
```

### 本地开发构建
```bash
# 构建本地开发镜像
just build

# 运行镜像
just run

# 以 dry-run 模式运行
just run-dry
```

### 生产构建

#### 构建 latest 版本 (master 分支)
```bash
# 仅构建（自动包含 commit hash 标签）
just build-latest

# 构建并推送到注册表（会生成 latest、master 和 commit-hash 三个标签）
just push-latest
```

生成的标签示例：
- `ghcr.io/reonokiy/sync-tailscale-to-cloudflare:latest`
- `ghcr.io/reonokiy/sync-tailscale-to-cloudflare:master`
- `ghcr.io/reonokiy/sync-tailscale-to-cloudflare:abc1234` (commit hash)

#### 构建发布版本 (带标签)
```bash
# 仅构建
just build-release v1.0.0

# 构建并推送到注册表
just push-release v1.0.0
```

## 环境变量配置

可以通过环境变量自定义构建参数：

```bash
# 自定义注册表
export REGISTRY=ghcr.io/your-username

# 自定义镜像名称
export IMAGE_NAME=your-image-name

# 使用自定义配置构建
just build-latest
```

## Docker Bake 配置

项目使用 `docker-bake.hcl` 配置文件定义构建目标：

- `default`: 本地开发构建
- `latest`: 生产构建 (master 分支)
- `release`: 发布版本构建 (带标签)

### 查看 Bake 配置
```bash
just show-config
```

## GitHub Actions 自动发布

项目配置了 GitHub Actions 自动构建和发布：

### 触发条件

1. **推送到 master 分支**: 自动构建并发布 `latest` 和 `master` 标签的镜像
2. **推送 v* 标签**: 自动构建并发布对应版本的镜像
3. **Pull Request**: 仅构建，不发布

### 发布流程

1. 推送代码到 master 分支或创建 v* 标签
2. GitHub Actions 自动触发构建
3. 镜像发布到 `ghcr.io/reonokiy/sync-tailscale-to-cloudflare`

### 镜像标签规则

- **master 分支**: `latest`, `master`
- **v1.0.0 标签**: `v1.0.0`, `1.0`, `1`, `latest`

## 实用工具

### 验证 Dockerfile
```bash
just validate
```

### 清理本地镜像
```bash
just clean
```

### 多平台构建

默认构建支持以下平台：
- `linux/amd64`
- `linux/arm64`

## 示例工作流

### 开发测试
```bash
# 1. 构建本地镜像
just build

# 2. 测试运行
just run-dry

# 3. 正常运行
just run
```

### 发布新版本
```bash
# 1. 创建并推送标签
git tag v1.0.0
git push origin v1.0.0

# 2. GitHub Actions 自动构建发布
# 3. 或者手动构建发布
just push-release v1.0.0
```
