# hermes-qq-onebot

QQ OneBot v11 平台适配器，为 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 添加 QQ 支持。

基于 NapCatQQ / go-cqhttp / Lagrange.OneBot / LLOneBot 等 OneBot v11 兼容实现。

## 架构

```
QQ 客户端 ←→ OneBot 实现 (NapCat/go-cqhttp)
                  ↓ WebSocket (事件) + HTTP (API)
             QQ 适配器 (hermes-qq-onebot)
```

## 支持的功能

- 私聊 / 群聊消息收发
- @提及检测
- 图片、语音、文件收发
- 回复消息
- emoji 表情回应 (戳一戳)
- 正向 WebSocket (Hermes → LLBot) + 反向 WebSocket (LLBot → Hermes)
- 用户白名单 / 全放行模式
- HTTP API 独立通道 (可与 WS 并用)
- 消息去重

## 安装

```bash
git clone https://github.com/yourname/hermes-qq-onebot.git
cd hermes-qq-onebot
chmod +x install.sh
./install.sh
```

安装脚本会自动：
1. 检测 hermes-agent 安装路径（默认 `~/.hermes/hermes-agent`）
2. 备份所有被修改的文件（`.bak`）
3. 安装 QQ 适配器和相关补丁
4. 在 hermes venv 中安装 `websockets` 依赖

卸载：

```bash
./uninstall.sh
# 或
python3 install.py uninstall
```

## 配置

### 方式一：环境变量（推荐）

在 `~/.hermes/.env` 中添加：

```bash
# 启用 QQ OneBot
QQ_ONEBOT_ENABLED=true

# OneBot HTTP API 地址 (NapCat 默认 5700)
QQ_ONEBOT_API_URL=http://127.0.0.1:5700

# 适配器监听端口，用于接收 OneBot 推送的事件
QQ_ONEBOT_LISTEN_PORT=5701

# 可选：access_token
QQ_ONEBOT_ACCESS_TOKEN=

# 可选：允许的 QQ 号（逗号分隔，留空表示全部允许）
QQ_ONEBOT_ALLOWED_USERS=123456,789012

# 可选：home group ID（定时任务投递目标）
QQ_ONEBOT_HOME_CHANNEL=123456789
```

### 方式二：config.yaml

```yaml
platforms:
  qq:
    enabled: true
    extra:
      api_host: "127.0.0.1"
      api_port: 5700
      listen_host: "0.0.0.0"
      listen_port: 5701
      access_token: ""
      allowed_qq_ids: ""
      allow_all_users: false
    home_channel:
      chat_id: "123456789"
      name: "Home"
```

### 方式三：setup 向导

```bash
hermes gateway setup
# 选择 "QQ (OneBot v11)"
```

## NapCat 配置

NapCatQQ 需要配置 WebSocket 连接到 hermes-qq-onebot 监听的端口：

```json
{
  "ws": {
    "enable": true,
    "host": "127.0.0.1",
    "port": 5701,
    "messagePostFormat": "array"
  },
  "http": {
    "enable": true,
    "host": "127.0.0.1",
    "port": 5700
  }
}
```

## 修改的文件

安装脚本会修改 hermes-agent 的以下文件（均有备份）：

| 文件 | 修改内容 |
|------|---------|
| `gateway/platforms/qq.py` | 适配器本体（新增） |
| `gateway/config.py` | `Platform.QQ` 枚举 + 环境变量解析 |
| `gateway/run.py` | 平台实例化 + 用户权限映射 |
| `gateway/platforms/__init__.py` | 导入 QQAdapter |
| `agent/prompt_builder.py` | QQ 平台上下文注入（告诉 agent 不要用 markdown） |
| `hermes_cli/platforms.py` | setup 向导平台列表 |
| `hermes_cli/gateway.py` | setup 向导交互配置 |
| `hermes_cli/status.py` | 状态显示 |
| `toolsets.py` | hermes-qq 工具集定义 |

## 兼容性

- hermes-agent 最新 main 分支
- Python 3.10+
- 依赖：`websockets`

## 许可证

MIT
