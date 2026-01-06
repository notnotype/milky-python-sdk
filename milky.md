# Milky SDK 开发指南

## 概述

Milky SDK 是用于与 Milky 协议端通信的 Python SDK，支持同步/异步两种模式和装饰器风格的事件系统。

## 安装依赖

```bash
pip install httpx pydantic
```

---

## 快速开始

### 方式一：MilkyBot 框架（推荐）

```python
from milky import MilkyBot

bot = MilkyBot("http://localhost:3010", "token")

@bot.on_mention()
async def handle(event):
    await bot.reply(event, "你好！")

@bot.on_command("help")
async def help_cmd(event, args):
    await bot.reply(event, "帮助信息")

bot.run()
```

### 方式二：异步客户端

```python
from milky import AsyncMilkyClient

async def main():
    async with AsyncMilkyClient("http://localhost:3010", "token") as client:
        info = await client.get_login_info()
        print(info.nickname)

asyncio.run(main())
```

### 方式三：同步客户端

```python
from milky import MilkyClient

client = MilkyClient("http://localhost:3010", "token")
info = client.get_login_info()
```

---

## 装饰器事件系统

| 装饰器 | 说明 |
|--------|------|
| `@bot.on(EventType.*)` | 监听指定事件类型 |
| `@bot.on_message()` | 监听所有消息 |
| `@bot.on_message("group")` | 只监听群消息 |
| `@bot.on_mention()` | 只在 bot 被 @ 时触发 |
| `@bot.on_command("cmd")` | 监听 `/cmd` 命令 |

---

## 消息段

### 发送文本

```python
from milky import OutgoingTextSegment, TextSegmentData

message = [OutgoingTextSegment(data=TextSegmentData(text="Hello!"))]
await client.send_group_message(group_id, message)
```

### 发送 @ + 文本

```python
from milky import OutgoingMentionSegment, MentionSegmentData

message = [
    OutgoingMentionSegment(data=MentionSegmentData(user_id=123)),
    OutgoingTextSegment(data=TextSegmentData(text=" 你好"))
]
```

### Bot.reply 快捷方法

```python
@bot.on_mention()
async def handle(event):
    await bot.reply(event, "你好！")  # 自动 @ 发送者
    await bot.reply(event, "消息", at_sender=False)  # 不 @
```

---

## 事件类型

```python
from milky import EventType

EventType.MESSAGE_RECEIVE      # 收到消息
EventType.MESSAGE_RECALL       # 消息撤回
EventType.FRIEND_REQUEST       # 好友请求
EventType.GROUP_MEMBER_INCREASE # 群成员增加
EventType.GROUP_NUDGE          # 群戳一戳
```

---

## 常用 API

```python
# 系统
await client.get_login_info()
await client.get_friend_list()
await client.get_group_list()

# 消息
await client.send_group_message(group_id, message)
await client.send_private_message(user_id, message)
await client.recall_group_message(group_id, message_seq)

# 群管理
await client.set_group_member_mute(group_id, user_id, 60)
await client.kick_group_member(group_id, user_id)
```

---

## 错误处理

```python
from milky.async_client import MilkyError, MilkyHttpError

try:
    await client.send_group_message(group_id, message)
except MilkyHttpError as e:
    print(f"HTTP {e.status_code}: {e.message}")
except MilkyError as e:
    print(f"API [{e.retcode}]: {e.message}")
```

---

## 完整示例

```python
from milky import MilkyBot

bot = MilkyBot("http://localhost:3010", "token")

@bot.on_mention()
async def reply_mention(event):
    await bot.reply(event, "你好！")

@bot.on_command("echo")
async def echo(event, args):
    if args:
        await bot.reply(event, args, at_sender=False)

@bot.on_message("group")
async def log_group(event):
    data = event["data"]
    print(f"群 {data['peer_id']}: {data['segments']}")

bot.run()
```
