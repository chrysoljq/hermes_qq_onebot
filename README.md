# hermes_qq_onebot

QQ OneBot v11 平台适配器，为 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 添加 QQ 支持。

基于 NapCatQQ / go-cqhttp / Lagrange.OneBot / LLOneBot 等 OneBot v11 兼容实现。

## 架构

```
QQ 客户端 ←→ OneBot 实现 (NapCat/go-cqhttp)
                  ↓ WebSocket (事件) + HTTP (API，可选)
             QQ 适配器 (hermes_qq_onebot)
```

- **WebSocket**：必须，用于接收事件和发送 API 调用
- **HTTP API**：可选但推荐开启，便于调试（curl 即可调用）、长程任务不受 WS 超时限制、`get_file` 等操作更稳定

## 支持的功能

- 私聊 / 群聊消息收发
- @提及检测
- 关键词触发（`mention_patterns`，群聊中匹配关键词即回复，类似 Telegram）
- 图片、语音、文件收发
- 回复消息
- emoji 表情回应（群聊）和戳一戳（私聊）
- 长消息自动拆分 + 合并转发（群聊，避免刷屏）
- 正向 WebSocket (Hermes → LLBot) + 反向 WebSocket (LLBot → Hermes)
- 用户白名单 / 全放行模式
- HTTP API 独立通道 (可与 WS 并用)
- 消息去重

## 安装

```bash
git clone https://github.com/chrysoljq/hermes_qq_onebot.git
cd hermes_qq_onebot
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

### 方式一：config.yaml（推荐）

在 `~/.hermes/config.yaml` 中添加：

```yaml
platforms:
  qq:
    enabled: true
    extra:
      # OneBot HTTP API 地址（可选，推荐开启）
      http_api_url: "http://127.0.0.1:5700"
      # WebSocket 反向模式（推荐，adapter 起 server 等 OneBot 连上来）
      reverse_mode: true
      reverse_host: "0.0.0.0"
      reverse_port: 6700
      # 正向模式（adapter 主动连 OneBot）
      # ws_host: "127.0.0.1"
      # ws_port: 3001
      # ws_path: "/onebot/v11/ws"
      access_token: ""
      allowed_qq_ids: ""
      allow_all_users: false
      # 群聊关键词触发（正则，不区分大小写），匹配到即触发回复（不需要 @）
      # 支持字符串或列表，也可用环境变量 QQ_MENTION_PATTERNS=芙芙,帮我
      # mention_patterns:
      #   - "芙芙"
      #   - "帮我"
    home_channel:
      chat_id: "123456789"
      name: "Home"
```

### 方式二：环境变量

如需在 `.env` 中配置：

```bash
QQ_ONEBOT_ENABLED=true
QQ_ONEBOT_API_URL=http://127.0.0.1:5700
QQ_ONEBOT_LISTEN_HOST=0.0.0.0
QQ_ONEBOT_LISTEN_PORT=6700
QQ_ONEBOT_ACCESS_TOKEN=
QQ_ONEBOT_ALLOWED_USERS=
QQ_ONEBOT_HOME_CHANNEL=
```

### 方式三：setup 向导

```bash
hermes gateway setup
# 选择 "QQ (OneBot v11)"
```

## NapCat 配置

NapCatQQ 需要配置 WebSocket 连接到 hermes_qq_onebot 监听的端口。HTTP API 可选但推荐开启：

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
- Python 3.11+
- 依赖：`websockets`

## 许可证

MIT
