# Tailscale to Cloudflare DNS Sync

[![Docker Build](https://github.com/reonokiy/sync_tailscale_to_cloudflare/actions/workflows/docker.yml/badge.svg)](https://github.com/reonokiy/sync_tailscale_to_cloudflare/actions/workflows/docker.yml)
[![Docker Image](https://img.shields.io/badge/docker-ghcr.io-blue.svg)](https://github.com/reonokiy/sync_tailscale_to_cloudflare/pkgs/container/sync_tailscale_to_cloudflare)

这个工具会自动从 Tailscale API 获取设备名称和 IP 地址的对应关系，然后同步更新到 Cloudflare 上对应的 DNS A 记录。支持 Docker 部署和多平台架构。

## ✨ 功能特性

- 🔄 **自动同步**: 从 Tailscale 自动同步设备信息到 Cloudflare DNS
- 🏷️ **智能过滤**: 支持按设备标签和名称模式过滤设备
- 🔍 **预览模式**: 支持 dry-run 模式预览更改
- 📝 **详细日志**: 提供详细的操作日志记录
- ⚡ **增量更新**: 只更新变化的记录，避免不必要的 API 调用
- 📲 **通知支持**: 支持通过 ntfy.sh 发送同步通知
- 🐳 **Docker 支持**: 完整的 Docker 构建和部署支持
- 🏗️ **多平台**: 支持 `linux/amd64` 和 `linux/arm64` 架构
- 🚀 **自动发布**: GitHub Actions 自动构建和发布 Docker 镜像

## 🚀 快速开始

### 使用 Docker（推荐）

1. **拉取预构建镜像**：
```bash
docker pull ghcr.io/reonokiy/sync_tailscale_to_cloudflare:latest
```

2. **准备环境变量文件**：
```bash
# 复制示例配置
curl -o .env https://raw.githubusercontent.com/reonokiy/sync_tailscale_to_cloudflare/master/.env.example

# 编辑配置文件，填入你的 API 密钥
nano .env
```

3. **运行同步**：
```bash
# 干运行模式，预览将要进行的更改
docker run --rm --env-file .env -e DRY_RUN=true ghcr.io/reonokiy/sync_tailscale_to_cloudflare:latest

# 正式运行
docker run --rm --env-file .env ghcr.io/reonokiy/sync_tailscale_to_cloudflare:latest
```

### 本地安装

1. **克隆仓库**：
```bash
git clone https://github.com/reonokiy/sync_tailscale_to_cloudflare.git
cd sync_tailscale_to_cloudflare
```

2. **安装依赖**：
```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install -e .
```

3. **配置环境变量**：
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥
```

4. **运行**：
```bash
python main.py
```

## 🔧 配置

### 必需的环境变量

在 `.env` 文件中设置以下变量：

```bash
# Tailscale API 配置
TAILSCALE_API_KEY=tskey-api-xxxxxxxxxxxxxxxxx
TAILSCALE_TAILNET=your-tailnet-name

# Cloudflare API 配置
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token
CLOUDFLARE_ZONE_ID=your_cloudflare_zone_id
CLOUDFLARE_DOMAIN=your-domain.com
```

### 可选的环境变量

```bash
# 设备过滤（可选）
DEVICE_TAG_FILTER=dns,public                    # 只同步带有这些标签的设备
DEVICE_NAME_PATTERN=server-*                    # 只同步匹配模式的设备名

# 基础域名（可选）
CLOUDFLARE_BASE_DOMAIN=tailscale.example.com    # 在子域下创建记录

# 通知设置（可选）
NTFY_TOPIC=your-unique-topic-name               # ntfy.sh 通知主题
NTFY_SERVER=https://ntfy.sh                     # 自定义 ntfy 服务器

# 运行模式（可选）
DRY_RUN=false                                   # 设为 true 只预览不执行
LOG_LEVEL=INFO                                  # 日志级别：DEBUG, INFO, WARNING, ERROR
```

### 获取 API 密钥

#### Tailscale API 密钥

1. 访问 [Tailscale Admin Console](https://login.tailscale.com/admin/settings/keys)
2. 点击 "Generate API key"
3. 给密钥一个描述性的名称，如 "DNS Sync"
4. 选择权限：至少需要 "Devices: Read"
5. 复制生成的密钥到 `TAILSCALE_API_KEY`

#### Cloudflare API 令牌

1. 访问 [Cloudflare API 令牌页面](https://dash.cloudflare.com/profile/api-tokens)
2. 点击 "创建令牌"
3. 使用 "自定义令牌" 模板
4. 设置权限：
   - Zone: Zone:Read
   - Zone: DNS:Edit
5. 设置 Zone Resources 为您的特定域名
6. 复制生成的令牌到 `CLOUDFLARE_API_TOKEN`

#### Cloudflare Zone ID

1. 在 Cloudflare Dashboard 中选择您的域名
2. 在右侧边栏的 "API" 部分找到 "Zone ID"
3. 复制到 `CLOUDFLARE_ZONE_ID`

## 🐳 Docker 部署

### 使用预构建镜像

最简单的方式是使用 GitHub Container Registry 中的预构建镜像：

```bash
# 拉取最新版本
docker pull ghcr.io/reonokiy/sync_tailscale_to_cloudflare:latest

# 拉取特定版本
docker pull ghcr.io/reonokiy/sync_tailscale_to_cloudflare:v1.0.0

# 拉取特定 commit 版本（用于精确版本控制）
docker pull ghcr.io/reonokiy/sync_tailscale_to_cloudflare:abc1234
```

### 运行容器

```bash
# 使用环境变量文件
docker run --rm --env-file .env ghcr.io/reonokiy/sync_tailscale_to_cloudflare:latest

# 直接传递环境变量
docker run --rm \
  -e TAILSCALE_API_KEY=your_key \
  -e TAILSCALE_TAILNET=your_tailnet \
  -e CLOUDFLARE_API_TOKEN=your_token \
  -e CLOUDFLARE_ZONE_ID=your_zone_id \
  -e CLOUDFLARE_DOMAIN=your_domain.com \
  ghcr.io/reonokiy/sync_tailscale_to_cloudflare:latest

# 干运行模式
docker run --rm --env-file .env -e DRY_RUN=true \
  ghcr.io/reonokiy/sync_tailscale_to_cloudflare:latest
```

### 定时运行

#### 使用 Docker Compose

创建 `docker-compose.yml` 文件：

```yaml
version: '3.8'
services:
  tailscale-dns-sync:
    image: ghcr.io/reonokiy/sync_tailscale_to_cloudflare:latest
    env_file: .env
    restart: unless-stopped
    command: >
      sh -c 'while true; do 
        echo "$(date): Starting Tailscale DNS sync..."; 
        python3 main.py; 
        echo "$(date): Sync completed, sleeping for 5 minutes..."; 
        sleep 300; 
      done'
```

运行：
```bash
docker-compose up -d
```

#### 使用 cron

```bash
# 添加到 crontab - 每 5 分钟运行一次
*/5 * * * * docker run --rm --env-file /path/to/.env ghcr.io/reonokiy/sync_tailscale_to_cloudflare:latest
```

### 本地构建

如果需要本地构建镜像，项目使用 Docker Bake 和 Just 来管理构建过程。

#### 前置要求

1. **安装 Just**:
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to ~/bin
   ```

2. **确保 Docker Buildx 已启用**

#### 构建命令

```bash
# 查看所有可用命令
just

# 构建本地开发镜像
just build

# 运行本地构建的镜像
just run

# 干运行模式
just run-dry

# 构建多平台镜像
just build-latest
```

更多构建选项请参考 [BUILD.md](BUILD.md)。

## 🚀 自动发布和版本管理

项目配置了 GitHub Actions，可以自动构建和发布 Docker 镜像。

### 发布触发条件

- **推送到 `master` 分支**: 自动构建并发布 `latest`、`master` 和 `commit-hash` 标签
- **推送 `v*` 标签**: 自动构建并发布对应版本的镜像
- **Pull Request**: 仅构建验证，不发布

### 镜像标签规则

| 触发条件 | 生成的标签 |
|---------|----------|
| `master` 分支 | `latest`, `master`, `<commit-hash>` |
| `v1.0.0` 标签 | `v1.0.0`, `1.0`, `1`, `latest` |
| `v1.2.3` 标签 | `v1.2.3`, `1.2`, `1`, `latest` |

> **注意**: `<commit-hash>` 是 7 位的 Git commit SHA，例如 `abc1234`

### 发布新版本

1. **创建并推送标签**:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **GitHub Actions 自动执行**:
   - 多平台构建 (`linux/amd64`, `linux/arm64`)
   - 自动推送到 `ghcr.io/reonokiy/sync_tailscale_to_cloudflare`
   - 生成相应的版本标签

### 可用镜像

所有发布的镜像都可以在以下地址找到：
- **GitHub Packages**: https://github.com/reonokiy/sync_tailscale_to_cloudflare/pkgs/container/sync_tailscale_to_cloudflare
- **镜像地址**: `ghcr.io/reonokiy/sync_tailscale_to_cloudflare`

## ⚙️ 工作原理

1. **获取设备列表**: 从 Tailscale API 获取当前在线的设备列表
2. **过滤设备**: 根据配置的标签和名称模式过滤设备
3. **检查现有记录**: 从 Cloudflare API 获取现有的 DNS 记录
4. **计算差异**: 比较设备列表和 DNS 记录，确定需要的操作：
   - 为新设备创建 DNS 记录
   - 为 IP 变更的设备更新 DNS 记录
   - 删除不再存在的设备的 DNS 记录
5. **执行更改**: 调用 Cloudflare API 执行实际的 DNS 更改
6. **发送通知**: （可选）通过 ntfy.sh 发送同步结果通知

## 📋 DNS 记录格式

设备会以以下格式创建 DNS 记录：
```
<device-hostname>.<base-domain> -> <tailscale-ip>
```

例如：
- 设备名：`my-laptop`
- 基础域名：`example.com`
- Tailscale IP：`100.64.1.2`
- 创建的 DNS 记录：`my-laptop.example.com -> 100.64.1.2`

如果设置了 `CLOUDFLARE_BASE_DOMAIN`，记录会创建在子域下：
- 基础域名：`tailscale.example.com`
- 创建的 DNS 记录：`my-laptop.tailscale.example.com -> 100.64.1.2`

## 📝 注意事项

- 只会同步**在线**的 Tailscale 设备
- 只处理 Tailscale IPv4 地址（100.x.x.x 网段）
- DNS 记录的 TTL 设置为 300 秒（5 分钟）
- 程序会跳过 IPv6 地址
- 支持多平台 Docker 镜像（AMD64 和 ARM64）

## 🔧 故障排除

### 常见错误

1. **401 Unauthorized**
   - 检查 `TAILSCALE_API_KEY` 或 `CLOUDFLARE_API_TOKEN` 是否正确
   - 确认 API 密钥没有过期

2. **403 Forbidden**
   - 检查 Cloudflare API 令牌权限是否足够
   - 确认 Zone 权限已正确设置

3. **Zone ID 错误**
   - 在 Cloudflare Dashboard 中确认 Zone ID
   - 确保域名在正确的 Cloudflare 账户中

4. **设备未找到**
   - 确认设备是否在线
   - 检查设备标签过滤条件
   - 验证设备名称模式匹配

### 调试步骤

1. **使用干运行模式**：
   ```bash
   # Docker
   docker run --rm --env-file .env -e DRY_RUN=true ghcr.io/reonokiy/sync_tailscale_to_cloudflare:latest
   
   # 本地
   DRY_RUN=true python main.py
   ```

2. **检查环境变量**：
   ```bash
   # 验证环境变量是否正确加载
   docker run --rm --env-file .env ghcr.io/reonokiy/sync_tailscale_to_cloudflare:latest env | grep -E "(TAILSCALE|CLOUDFLARE)"
   ```

3. **查看详细日志**：
   ```bash
   # 启用详细日志
   docker run --rm --env-file .env -e LOG_LEVEL=DEBUG ghcr.io/reonokiy/sync_tailscale_to_cloudflare:latest
   ```

### Docker 相关问题

1. **镜像拉取失败**：
   ```bash
   # 检查网络连接
   docker pull ghcr.io/reonokiy/sync_tailscale_to_cloudflare:latest
   
   # 使用特定版本
   docker pull ghcr.io/reonokiy/sync_tailscale_to_cloudflare:v1.0.0
   ```

2. **权限问题**：
   ```bash
   # 确保 Docker 守护进程运行
   sudo systemctl start docker
   
   # 检查用户权限
   sudo usermod -aG docker $USER
   newgrp docker
   ```

### API 调试

使用 curl 测试 API 连接：

```bash
# 测试 Tailscale API
curl -H "Authorization: Bearer $TAILSCALE_API_KEY" \
     "https://api.tailscale.com/api/v2/tailnet/$TAILSCALE_TAILNET/devices"

# 测试 Cloudflare API
curl -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
     "https://api.cloudflare.com/client/v4/zones/$CLOUDFLARE_ZONE_ID"
```

## 🤝 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

### 开发环境

```bash
# 克隆仓库
git clone https://github.com/reonokiy/sync_tailscale_to_cloudflare.git
cd sync_tailscale_to_cloudflare

# 安装依赖
uv sync

# 运行测试
just build
just run-dry

# 验证 Docker 配置
just show-config
```

## 📋 待办事项

- [ ] 支持 IPv6 地址同步
- [ ] 添加更多通知后端（Slack、Discord 等）
- [ ] 支持自定义 DNS 记录模板
- [ ] 添加 Web UI 界面
- [ ] 支持多个 Cloudflare Zone
- [ ] 添加 Prometheus 指标导出

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Tailscale](https://tailscale.com/) - 优秀的 VPN 服务
- [Cloudflare](https://www.cloudflare.com/) - 强大的 DNS 和 CDN 服务
- [uv](https://github.com/astral-sh/uv) - 快速的 Python 包管理器
- [Just](https://just.systems/) - 便捷的命令运行器

---

如果这个项目对你有帮助，请考虑给它一个 ⭐️！
