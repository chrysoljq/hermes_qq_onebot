# hermes-qq-onebot

QQ OneBot v11 平台适配器插件，为 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 添加 QQ 支持。

基于 NapCatQQ / go-cqhttp / Lagrange.OneBot / LLOneBot 等 OneBot v11 兼容实现。

## 架构

```
QQ 客户端 ←→ OneBot 实现 (NapCat/go-cqhttp)
                  ↓ WebSocket (事件) + HTTP (API，可选)
             QQ 适配器插件 (hermes-qq-onebot)
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
- 用户授权（通过网关层 `QQ_ONEBOT_ALLOWED_USERS` 环境变量统一管理）
- HTTP API 独立通道 (可与 WS 并用)
- 消息去重

## 安装（插件方式）

```bash
# 1. 克隆仓库
git clone https://github.com/chrysoljq/hermes-qq-onebot.git
cd hermes-qq-onebot

# 2. 复制适配器到 hermes gateway platforms
cp qq_adapter.py ~/.hermes/hermes-agent/gateway/platforms/qqonebot.py

# 3. 复制插件到 hermes plugins 目录
cp -r plugins/qqonebot ~/.hermes/plugins/

# 4. 启用插件
hermes plugins enable qqonebot

# 5. 安装依赖
pip install websockets
```

## 配置

在 `~/.hermes/config.yaml` 中添加：

```yaml
platforms:
  qqonebot:
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
      show_qq_id: false         # 在 user_name 里附带 QQ 号，如 用户名(123456)
      # 群聊关键词触发（正则，不区分大小写），匹配到即触发回复（不需要 @）
      # 支持字符串或列表，也可用环境变量 QQ_MENTION_PATTERNS=芙芙,帮我
      # mention_patterns:
      #   - "芙芙"
      #   - "帮我"
```

## 环境变量（可选）

```bash
QQ_ONEBOT_WS_URL=ws://127.0.0.1:3001/onebot/v11/ws  # 正向模式
QQ_ONEBOT_ALLOWED_USERS=123456,789012                 # 允许的 QQ 号
QQ_ONEBOT_ALLOW_ALL_USERS=false                       # 允许所有用户
QQ_HOME_CHANNEL=qq_group_123456789                    # 默认发送目标
```

## 卸载

```bash
# 1. 禁用插件
hermes plugins disable qqonebot

# 2. 删除文件
rm ~/.hermes/hermes-agent/gateway/platforms/qqonebot.py
rm -rf ~/.hermes/plugins/qqonebot

# 3. 重启 gateway
hermes gateway restart
```

## 文件说明

```
hermes-qq-onebot/
├── qq_adapter.py          # QQ 适配器主文件
├── plugins/
│   └── qqonebot/
│       ├── plugin.yaml    # 插件声明
│       ├── __init__.py    # 导出 register
│       └── adapter.py     # 注册到 platform_registry
├── README.md
└── ...
```

## 与旧版安装方式的区别

旧版使用 `install.py` 修改 hermes 核心代码（补丁方式），新版使用插件系统：

| 项目 | 旧版（补丁） | 新版（插件） |
|------|-------------|-------------|
| 安装方式 | 修改核心代码 | 独立插件目录 |
| 更新 hermes | 需要重新打补丁 | 不受影响 |
| 卸载 | 需要恢复备份 | 删除插件即可 |
| 配置位置 | `platforms.qq` | `platforms.qqonebot` |
