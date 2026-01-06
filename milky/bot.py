"""Milky Bot Framework with Event Decorators"""

from __future__ import annotations

import asyncio
import logging
from enum import Enum
from typing import Any, Callable, Coroutine, Optional, TypeVar

from milky.async_client import AsyncMilkyClient, MilkyError, MilkyHttpError
from milky.models import (
    OutgoingMentionSegment,
    OutgoingSegment,
    OutgoingTextSegment,
    MentionSegmentData,
    TextSegmentData,
)

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Coroutine[Any, Any, Any]])


class EventType(str, Enum):
    """事件类型"""
    
    # 消息事件
    MESSAGE_RECEIVE = "message_receive"
    MESSAGE_RECALL = "message_recall"
    
    # 好友事件
    FRIEND_REQUEST = "friend_request"
    FRIEND_NUDGE = "friend_nudge"
    FRIEND_FILE_UPLOAD = "friend_file_upload"
    
    # 群事件
    GROUP_JOIN_REQUEST = "group_join_request"
    GROUP_INVITED_JOIN_REQUEST = "group_invited_join_request"
    GROUP_INVITATION = "group_invitation"
    GROUP_ADMIN_CHANGE = "group_admin_change"
    GROUP_MEMBER_INCREASE = "group_member_increase"
    GROUP_MEMBER_DECREASE = "group_member_decrease"
    GROUP_NAME_CHANGE = "group_name_change"
    GROUP_ESSENCE_MESSAGE_CHANGE = "group_essence_message_change"
    GROUP_MESSAGE_REACTION = "group_message_reaction"
    GROUP_MUTE = "group_mute"
    GROUP_WHOLE_MUTE = "group_whole_mute"
    GROUP_NUDGE = "group_nudge"
    GROUP_FILE_UPLOAD = "group_file_upload"
    
    # 系统事件
    BOT_OFFLINE = "bot_offline"


class MilkyBot:
    """Milky Bot Framework
    
    提供装饰器风格的事件注册系统。
    
    Example:
        bot = MilkyBot("http://localhost:3010", "token")
        
        @bot.on_message()
        async def handle(event):
            print(event)
        
        @bot.on_mention()
        async def reply(event):
            await bot.reply(event, "你好!")
        
        bot.run()
    """
    
    def __init__(
        self,
        base_url: str,
        access_token: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.client = AsyncMilkyClient(base_url, access_token, timeout)
        self._handlers: dict[str, list[Callable]] = {}
        self._bot_id: Optional[int] = None
    
    @property
    def bot_id(self) -> Optional[int]:
        """Bot QQ 号"""
        return self._bot_id
    
    # ========================================================================
    # 事件装饰器
    # ========================================================================
    
    def on(self, event_type: EventType) -> Callable[[F], F]:
        """
        通用事件装饰器
        
        Args:
            event_type: 事件类型
        
        Example:
            @bot.on(EventType.MESSAGE_RECEIVE)
            async def handle(event):
                pass
        """
        def decorator(func: F) -> F:
            self._handlers.setdefault(event_type.value, []).append(func)
            return func
        return decorator
    
    def on_message(self, scene: Optional[str] = None) -> Callable[[F], F]:
        """
        消息接收装饰器
        
        Args:
            scene: 可选，限定消息场景 ("friend"/"group"/"temp")
        
        Example:
            @bot.on_message()
            async def all_messages(event):
                pass
            
            @bot.on_message("group")
            async def group_only(event):
                pass
        """
        def decorator(func: F) -> F:
            async def wrapper(event: dict) -> None:
                data = event.get("data", {})
                if scene is None or data.get("message_scene") == scene:
                    await func(event)
            self._handlers.setdefault("message_receive", []).append(wrapper)
            return func
        return decorator
    
    def on_mention(self) -> Callable[[F], F]:
        """
        被 @ 时触发的装饰器
        
        只有当 bot 被 @ 时才会触发
        
        Example:
            @bot.on_mention()
            async def handle(event):
                await bot.reply(event, "你好!")
        """
        def decorator(func: F) -> F:
            async def wrapper(event: dict) -> None:
                if self._is_mentioned(event):
                    await func(event)
            self._handlers.setdefault("message_receive", []).append(wrapper)
            return func
        return decorator
    
    def on_command(self, command: str, prefix: str = "/") -> Callable[[F], F]:
        """
        命令装饰器
        
        当消息以指定前缀+命令开头时触发
        
        Args:
            command: 命令名
            prefix: 命令前缀，默认 "/"
        
        Example:
            @bot.on_command("help")
            async def help_cmd(event, args):
                await bot.reply(event, "帮助信息")
        """
        full_command = f"{prefix}{command}"
        
        def decorator(func: F) -> F:
            async def wrapper(event: dict) -> None:
                text = self._get_text(event)
                if text.startswith(full_command):
                    args = text[len(full_command):].strip()
                    await func(event, args)
            self._handlers.setdefault("message_receive", []).append(wrapper)
            return func
        return decorator
    
    # ========================================================================
    # 辅助方法
    # ========================================================================
    
    def _is_mentioned(self, event: dict) -> bool:
        """检查 bot 是否被 @"""
        if self._bot_id is None:
            return False
        data = event.get("data", {})
        for seg in data.get("segments", []):
            if seg.get("type") == "mention":
                if seg.get("data", {}).get("user_id") == self._bot_id:
                    return True
        return False
    
    def _get_text(self, event: dict) -> str:
        """提取消息中的纯文本"""
        data = event.get("data", {})
        texts = []
        for seg in data.get("segments", []):
            if seg.get("type") == "text":
                texts.append(seg.get("data", {}).get("text", ""))
        return "".join(texts).strip()
    
    async def reply(
        self,
        event: dict,
        content: str,
        at_sender: bool = True,
    ) -> None:
        """
        快捷回复消息
        
        Args:
            event: 原始事件
            content: 回复内容
            at_sender: 是否 @ 发送者（仅群聊有效）
        """
        data = event.get("data", {})
        scene = data.get("message_scene")
        peer_id = data.get("peer_id")
        sender_id = data.get("sender_id")
        
        message: list[OutgoingSegment] = []
        
        if at_sender and scene == "group":
            message.append(OutgoingMentionSegment(
                data=MentionSegmentData(user_id=sender_id)
            ))
            content = " " + content
        
        message.append(OutgoingTextSegment(data=TextSegmentData(text=content)))
        
        if scene == "group":
            await self.client.send_group_message(peer_id, message)
        elif scene == "friend":
            await self.client.send_private_message(sender_id, message)
    
    async def send(
        self,
        event: dict,
        message: list[OutgoingSegment],
    ) -> None:
        """
        发送消息到事件来源
        
        Args:
            event: 原始事件
            message: 消息段列表
        """
        data = event.get("data", {})
        scene = data.get("message_scene")
        peer_id = data.get("peer_id")
        sender_id = data.get("sender_id")
        
        if scene == "group":
            await self.client.send_group_message(peer_id, message)
        elif scene == "friend":
            await self.client.send_private_message(sender_id, message)
    
    # ========================================================================
    # 运行
    # ========================================================================
    
    async def _dispatch(self, event: dict) -> None:
        """分发事件到处理器"""
        event_type = event.get("event_type")
        handlers = self._handlers.get(event_type, [])
        
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.exception(f"Handler error: {e}")
    
    async def _run_async(self) -> None:
        """异步运行主循环"""
        # 获取 bot 信息
        try:
            info = await self.client.get_login_info()
            self._bot_id = info.uin
            logger.info(f"Bot logged in: {info.nickname} ({info.uin})")
        except (MilkyError, MilkyHttpError) as e:
            logger.error(f"Login failed: {e}")
            return
        
        logger.info("Starting event loop...")
        
        try:
            async for event in self.client.events_sse():
                await self._dispatch(event)
        except asyncio.CancelledError:
            logger.info("Event loop cancelled")
        except (MilkyError, MilkyHttpError) as e:
            logger.error(f"Event stream error: {e}")
        finally:
            await self.client.close()
            logger.info("Bot stopped")
    
    def run(self) -> None:
        """
        启动 bot
        
        这会阻塞当前线程，开始监听和处理事件
        """
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
        )
        
        try:
            asyncio.run(self._run_async())
        except KeyboardInterrupt:
            pass  # 已在 _run_async 中处理

