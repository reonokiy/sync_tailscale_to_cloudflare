# Tailscale to Cloudflare DNS Sync

这个工具会自动从 Tailscale API 获取设备名称和 IP 地址的对应关系，然后同步更新到 Cloudflare 上对应的 DNS A 记录。

## 功能特性

- 🔄 自动同步 Tailscale 设备到 Cloudflare DNS A 记录
- 🏷️ 支持按设备标签和名称模式过滤设备
- 🔍 支持 dry-run 模式预览更改
- 📝 详细的日志记录
- ⚡ 只更新变化的记录，避免不必要的 API 调用
- 📲 支持通过 ntfy.sh 发送同步通知

## 安装

1. 克隆仓库：
```bash
git clone <repository-url>
cd sync_tailscale_to_dns
```

2. 安装依赖：
```bash
pip install -e .
```

3. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，填入您的 API 密钥
```

## 配置

### 必需的环境变量

在 `.env` 文件中设置以下变量：

```bash
# Tailscale API 配置
TAILSCALE_API_KEY=tskey-api-xxxxxxxxxxxxxxxxx
TAILSCALE_TAILNET=your-tailnet-name

```bash
# Cloudflare API 配置
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token
CLOUDFLARE_ZONE_ID=your_cloudflare_zone_id
CLOUDFLARE_DOMAIN=your-domain.com

# 通知配置（可选）
NTFY_TOPIC=your-unique-topic-name
```
```

### 可选的环境变量

```bash
# 设备名称过滤（正则表达式）
DEVICE_NAME_PATTERN=^(server|laptop).*

# 设备标签过滤（逗号分隔）
DEVICE_TAGS=server,home
```

### 获取 API 密钥

#### Tailscale API 密钥

1. 访问 [Tailscale Admin Console](https://login.tailscale.com/admin/settings/keys)
2. 点击 "Generate API key"
3. 选择合适的权限（需要 "Read" 权限来访问设备列表）
4. 复制生成的密钥到 `TAILSCALE_API_KEY`

#### Cloudflare API 令牌

1. 访问 [Cloudflare API Tokens](https://dash.cloudflare.com/profile/api-tokens)
2. 点击 "Create Token"
3. 使用 "Custom token" 模板
4. 设置权限：
   - Zone: Zone:Read
   - Zone: DNS:Edit
5. 设置 Zone Resources 为您的特定域名
6. 复制生成的令牌到 `CLOUDFLARE_API_TOKEN`

#### Cloudflare Zone ID

1. 在 Cloudflare Dashboard 中选择您的域名
2. 在右侧边栏的 "API" 部分找到 "Zone ID"
3. 复制到 `CLOUDFLARE_ZONE_ID`

#### 通知配置（可选）

如果您想接收同步完成的通知，可以使用 [ntfy.sh](https://ntfy.sh/) 服务：

1. 选择一个唯一的主题名称（例如：`tailscale-dns-sync-yourname`）
2. 设置 `NTFY_TOPIC=your-unique-topic-name`
3. （可选）如果使用自己的 ntfy.sh 服务器，设置 `NTFY_SERVER=https://your-server.com`

通知将包含：
- ✅ 同步成功：显示创建、更新、删除的记录数量
- ❌ 同步失败：显示错误信息
- 🔍 Dry-run 模式标识

您可以通过以下方式订阅通知：
- 网页：访问 `https://ntfy.sh/your-topic-name`
- 手机 App：下载 ntfy 应用，订阅您的主题
- 命令行：`curl -s ntfy.sh/your-topic-name/json`

## 使用方法

### 基本使用

```bash
# 同步所有在线设备
python main.py

# 预览模式（不实际修改 DNS 记录）
python main.py --dry-run
```

### 高级用法

通过环境变量过滤设备：

```bash
# 只同步以 "server" 开头的设备
export DEVICE_NAME_PATTERN="^server.*"
python main.py

# 只同步带有 "production" 标签的设备
export DEVICE_TAGS="production"
python main.py
```

## 工作原理

1. **获取 Tailscale 设备**：使用 Tailscale API 获取所有在线设备的名称和 Tailscale IP 地址
2. **获取当前 DNS 记录**：从 Cloudflare 获取现有的 A 记录
3. **比较和同步**：
   - 为新设备创建 DNS 记录
   - 为 IP 变更的设备更新 DNS 记录
   - 删除不再存在的设备的 DNS 记录

## DNS 记录格式

设备会以以下格式创建 DNS 记录：
```
<device-hostname>.<your-domain> -> <tailscale-ip>
```

例如：
- 设备名：`my-laptop`
- 域名：`example.com`
- Tailscale IP：`100.64.1.2`
- 创建的 DNS 记录：`my-laptop.example.com -> 100.64.1.2`

## 日志

程序会输出详细的操作日志，包括：
- 发现的设备信息
- 创建、更新、删除的 DNS 记录
- API 调用错误信息

## 注意事项

- 只会同步**在线**的 Tailscale 设备
- 只处理 Tailscale IPv4 地址（100.x.x.x 网段）
- DNS 记录的 TTL 设置为 300 秒（5 分钟）
- 程序会跳过 IPv6 地址

## 故障排除

### 常见错误

1. **401 Unauthorized**：检查 API 密钥是否正确
2. **403 Forbidden**：检查 API 权限是否足够
3. **Zone ID 错误**：确认 Cloudflare Zone ID 是否正确
4. **设备未找到**：确认设备是否在线，以及过滤条件是否正确

### 调试

使用 `--dry-run` 选项来预览将要执行的操作而不实际修改 DNS 记录。

## 许可证

MIT License
