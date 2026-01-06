"""Milky API Client with Event Support"""

from __future__ import annotations

import json
from typing import Callable, Generator, Optional

import httpx

from milky.models import (
    CreateFolderResult,
    FileDownloadUrl,
    FriendEntity,
    FriendRequest,
    GroupAnnouncementEntity,
    GroupEntity,
    GroupEssenceMessage,
    GroupFileEntity,
    GroupFolderEntity,
    GroupMemberEntity,
    ImplInfo,
    IncomingForwardedMessage,
    IncomingMessage,
    LoginInfo,
    MessageScene,
    NotificationType,
    OutgoingSegment,
    ResourceTempUrl,
    SendMessageResult,
    UploadFileResult,
    UserProfile,
)


class MilkyError(Exception):
    """Milky API Error"""

    def __init__(self, retcode: int, message: str):
        self.retcode = retcode
        self.message = message
        super().__init__(f"[{retcode}] {message}")


class MilkyHttpError(Exception):
    """HTTP 层错误"""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"HTTP {status_code}: {message}")


class MilkyClient:
    """Milky Protocol API Client
    
    支持三种事件接收方式：
    - SSE (Server-Sent Events): 调用 `events_sse()` 方法
    - WebSocket: 调用 `events_ws()` 方法  
    - WebHook: 需自行实现 HTTP 服务接收推送
    """

    def __init__(
        self,
        base_url: str,
        access_token: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize Milky Client.

        Args:
            base_url: API base URL (e.g., "http://localhost:8080")
            access_token: Bearer token for authentication (optional)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token
        self.timeout = timeout
        
        headers = {"Content-Type": "application/json"}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        
        self._client = httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout,
        )

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "MilkyClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def _request(self, endpoint: str, data: Optional[dict] = None) -> dict:
        """Make a POST request to the API."""
        try:
            response = self._client.post(f"/api/{endpoint}", json=data or {})
        except httpx.ConnectError as e:
            raise MilkyHttpError(0, f"连接失败: {e}")
        except httpx.TimeoutException as e:
            raise MilkyHttpError(0, f"请求超时: {e}")
        
        # Handle HTTP errors
        if response.status_code == 401:
            raise MilkyHttpError(401, "鉴权失败，未携带或提供了错误的 access_token")
        elif response.status_code == 404:
            raise MilkyHttpError(404, f"请求的 API 不存在: {endpoint}")
        elif response.status_code == 415:
            raise MilkyHttpError(415, "Content-Type 非 application/json")
        elif response.status_code != 200:
            raise MilkyHttpError(response.status_code, f"HTTP 错误: {response.text}")
        
        # Parse JSON response
        try:
            result = response.json()
        except json.JSONDecodeError:
            raise MilkyHttpError(response.status_code, f"无法解析响应: {response.text}")
        
        # Check API status
        if result.get("status") != "ok":
            raise MilkyError(
                result.get("retcode", -1),
                result.get("message", "Unknown error")
            )
        
        return result.get("data", {})

    # ========================================================================
    # 事件接收
    # ========================================================================

    def events_sse(self) -> Generator[dict, None, None]:
        """
        通过 SSE (Server-Sent Events) 接收事件流。
        
        Yields:
            dict: 事件数据，格式参见 Event schema
            
        Example:
            for event in client.events_sse():
                print(f"收到事件: {event['event_type']}")
        """
        headers = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        with httpx.stream(
            "GET",
            f"{self.base_url}/event",
            headers=headers,
            timeout=None,  # SSE 需要长连接
        ) as response:
            if response.status_code == 401:
                raise MilkyHttpError(401, "鉴权失败")
            response.raise_for_status()
            
            buffer = ""
            for chunk in response.iter_text():
                buffer += chunk
                while "\n\n" in buffer:
                    message, buffer = buffer.split("\n\n", 1)
                    # 解析 SSE 消息
                    data_lines = []
                    for line in message.split("\n"):
                        if line.startswith("data: "):
                            data_lines.append(line[6:])
                        elif line.startswith("data:"):
                            data_lines.append(line[5:])
                    
                    if data_lines:
                        try:
                            event_data = json.loads("".join(data_lines))
                            yield event_data
                        except json.JSONDecodeError:
                            continue

    def events_ws(
        self,
        on_event: Callable[[dict], None],
        on_error: Optional[Callable[[Exception], None]] = None,
    ) -> None:
        """
        通过 WebSocket 接收事件（需要 websockets 库）。
        
        Args:
            on_event: 事件回调函数
            on_error: 错误回调函数（可选）
            
        Example:
            def handle_event(event):
                print(f"收到事件: {event['event_type']}")
            
            client.events_ws(handle_event)
        """
        try:
            import websockets.sync.client as ws_client
        except ImportError:
            raise ImportError("请安装 websockets: pip install websockets")
        
        ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/event"
        if self.access_token:
            ws_url = f"{ws_url}?access_token={self.access_token}"
        
        try:
            with ws_client.connect(ws_url) as websocket:
                for message in websocket:
                    try:
                        event_data = json.loads(message)
                        on_event(event_data)
                    except json.JSONDecodeError as e:
                        if on_error:
                            on_error(e)
        except Exception as e:
            if on_error:
                on_error(e)
            else:
                raise

    # ========================================================================
    # 系统 API
    # ========================================================================

    def get_login_info(self) -> LoginInfo:
        """获取登录信息"""
        data = self._request("get_login_info")
        return LoginInfo(**data)

    def get_impl_info(self) -> ImplInfo:
        """获取协议端信息"""
        data = self._request("get_impl_info")
        return ImplInfo(**data)

    def get_user_profile(self, user_id: int) -> UserProfile:
        """获取用户个人信息"""
        data = self._request("get_user_profile", {"user_id": user_id})
        return UserProfile(**data)

    def get_friend_list(self, no_cache: bool = False) -> list[FriendEntity]:
        """获取好友列表"""
        data = self._request("get_friend_list", {"no_cache": no_cache})
        return [FriendEntity(**f) for f in data.get("friends", [])]

    def get_friend_info(self, user_id: int, no_cache: bool = False) -> FriendEntity:
        """获取好友信息"""
        data = self._request("get_friend_info", {"user_id": user_id, "no_cache": no_cache})
        return FriendEntity(**data.get("friend", {}))

    def get_group_list(self, no_cache: bool = False) -> list[GroupEntity]:
        """获取群列表"""
        data = self._request("get_group_list", {"no_cache": no_cache})
        return [GroupEntity(**g) for g in data.get("groups", [])]

    def get_group_info(self, group_id: int, no_cache: bool = False) -> GroupEntity:
        """获取群信息"""
        data = self._request("get_group_info", {"group_id": group_id, "no_cache": no_cache})
        return GroupEntity(**data.get("group", {}))

    def get_group_member_list(self, group_id: int, no_cache: bool = False) -> list[GroupMemberEntity]:
        """获取群成员列表"""
        data = self._request("get_group_member_list", {"group_id": group_id, "no_cache": no_cache})
        return [GroupMemberEntity(**m) for m in data.get("members", [])]

    def get_group_member_info(
        self, group_id: int, user_id: int, no_cache: bool = False
    ) -> GroupMemberEntity:
        """获取群成员信息"""
        data = self._request(
            "get_group_member_info",
            {"group_id": group_id, "user_id": user_id, "no_cache": no_cache},
        )
        return GroupMemberEntity(**data.get("member", {}))

    def get_cookies(self, domain: str) -> str:
        """获取 Cookies"""
        data = self._request("get_cookies", {"domain": domain})
        return data.get("cookies", "")

    def get_csrf_token(self) -> str:
        """获取 CSRF Token"""
        data = self._request("get_csrf_token")
        return data.get("csrf_token", "")

    # ========================================================================
    # 消息 API
    # ========================================================================

    def send_private_message(
        self, user_id: int, message: list[OutgoingSegment]
    ) -> SendMessageResult:
        """发送私聊消息"""
        data = self._request(
            "send_private_message",
            {"user_id": user_id, "message": [s.model_dump() for s in message]},
        )
        return SendMessageResult(**data)

    def send_group_message(
        self, group_id: int, message: list[OutgoingSegment]
    ) -> SendMessageResult:
        """发送群聊消息"""
        data = self._request(
            "send_group_message",
            {"group_id": group_id, "message": [s.model_dump() for s in message]},
        )
        return SendMessageResult(**data)

    def recall_private_message(self, user_id: int, message_seq: int) -> None:
        """撤回私聊消息"""
        self._request("recall_private_message", {"user_id": user_id, "message_seq": message_seq})

    def recall_group_message(self, group_id: int, message_seq: int) -> None:
        """撤回群聊消息"""
        self._request("recall_group_message", {"group_id": group_id, "message_seq": message_seq})

    def get_message(
        self, message_scene: MessageScene, peer_id: int, message_seq: int
    ) -> IncomingMessage:
        """获取消息"""
        data = self._request(
            "get_message",
            {"message_scene": message_scene.value, "peer_id": peer_id, "message_seq": message_seq},
        )
        return data.get("message", {})

    def get_history_messages(
        self,
        message_scene: MessageScene,
        peer_id: int,
        start_message_seq: Optional[int] = None,
        limit: int = 20,
    ) -> tuple[list[IncomingMessage], Optional[int]]:
        """获取历史消息列表"""
        params: dict = {"message_scene": message_scene.value, "peer_id": peer_id, "limit": limit}
        if start_message_seq is not None:
            params["start_message_seq"] = start_message_seq
        data = self._request("get_history_messages", params)
        return data.get("messages", []), data.get("next_message_seq")

    def get_resource_temp_url(self, resource_id: str) -> ResourceTempUrl:
        """获取临时资源链接"""
        data = self._request("get_resource_temp_url", {"resource_id": resource_id})
        return ResourceTempUrl(**data)

    def get_forwarded_messages(self, forward_id: str) -> list[IncomingForwardedMessage]:
        """获取合并转发消息内容"""
        data = self._request("get_forwarded_messages", {"forward_id": forward_id})
        return [IncomingForwardedMessage(**m) for m in data.get("messages", [])]

    def mark_message_as_read(
        self, message_scene: MessageScene, peer_id: int, message_seq: int
    ) -> None:
        """标记消息为已读"""
        self._request(
            "mark_message_as_read",
            {"message_scene": message_scene.value, "peer_id": peer_id, "message_seq": message_seq},
        )

    # ========================================================================
    # 好友 API
    # ========================================================================

    def send_friend_nudge(self, user_id: int, is_self: bool = False) -> None:
        """发送好友戳一戳"""
        self._request("send_friend_nudge", {"user_id": user_id, "is_self": is_self})

    def send_profile_like(self, user_id: int, count: int = 1) -> None:
        """发送名片点赞"""
        self._request("send_profile_like", {"user_id": user_id, "count": count})

    def get_friend_requests(
        self, limit: int = 20, is_filtered: bool = False
    ) -> list[FriendRequest]:
        """获取好友请求列表"""
        data = self._request("get_friend_requests", {"limit": limit, "is_filtered": is_filtered})
        return [FriendRequest(**r) for r in data.get("requests", [])]

    def accept_friend_request(self, initiator_uid: str, is_filtered: bool = False) -> None:
        """同意好友请求"""
        self._request(
            "accept_friend_request", {"initiator_uid": initiator_uid, "is_filtered": is_filtered}
        )

    def reject_friend_request(
        self, initiator_uid: str, is_filtered: bool = False, reason: Optional[str] = None
    ) -> None:
        """拒绝好友请求"""
        params: dict = {"initiator_uid": initiator_uid, "is_filtered": is_filtered}
        if reason is not None:
            params["reason"] = reason
        self._request("reject_friend_request", params)

    # ========================================================================
    # 群聊 API
    # ========================================================================

    def set_group_name(self, group_id: int, new_group_name: str) -> None:
        """设置群名称"""
        self._request("set_group_name", {"group_id": group_id, "new_group_name": new_group_name})

    def set_group_avatar(self, group_id: int, image_uri: str) -> None:
        """设置群头像"""
        self._request("set_group_avatar", {"group_id": group_id, "image_uri": image_uri})

    def set_group_member_card(self, group_id: int, user_id: int, card: str) -> None:
        """设置群名片"""
        self._request(
            "set_group_member_card", {"group_id": group_id, "user_id": user_id, "card": card}
        )

    def set_group_member_special_title(
        self, group_id: int, user_id: int, special_title: str
    ) -> None:
        """设置群成员专属头衔"""
        self._request(
            "set_group_member_special_title",
            {"group_id": group_id, "user_id": user_id, "special_title": special_title},
        )

    def set_group_member_admin(
        self, group_id: int, user_id: int, is_set: bool = True
    ) -> None:
        """设置群管理员"""
        self._request(
            "set_group_member_admin", {"group_id": group_id, "user_id": user_id, "is_set": is_set}
        )

    def set_group_member_mute(
        self, group_id: int, user_id: int, duration: int = 0
    ) -> None:
        """设置群成员禁言"""
        self._request(
            "set_group_member_mute",
            {"group_id": group_id, "user_id": user_id, "duration": duration},
        )

    def set_group_whole_mute(self, group_id: int, is_mute: bool = True) -> None:
        """设置群全员禁言"""
        self._request("set_group_whole_mute", {"group_id": group_id, "is_mute": is_mute})

    def kick_group_member(
        self, group_id: int, user_id: int, reject_add_request: bool = False
    ) -> None:
        """踢出群成员"""
        self._request(
            "kick_group_member",
            {"group_id": group_id, "user_id": user_id, "reject_add_request": reject_add_request},
        )

    def get_group_announcements(self, group_id: int) -> list[GroupAnnouncementEntity]:
        """获取群公告列表"""
        data = self._request("get_group_announcements", {"group_id": group_id})
        return [GroupAnnouncementEntity(**a) for a in data.get("announcements", [])]

    def send_group_announcement(
        self, group_id: int, content: str, image_uri: Optional[str] = None
    ) -> None:
        """发送群公告"""
        params: dict = {"group_id": group_id, "content": content}
        if image_uri is not None:
            params["image_uri"] = image_uri
        self._request("send_group_announcement", params)

    def delete_group_announcement(self, group_id: int, announcement_id: str) -> None:
        """删除群公告"""
        self._request(
            "delete_group_announcement",
            {"group_id": group_id, "announcement_id": announcement_id},
        )

    def get_group_essence_messages(
        self, group_id: int, page_index: int, page_size: int
    ) -> tuple[list[GroupEssenceMessage], bool]:
        """获取群精华消息列表"""
        data = self._request(
            "get_group_essence_messages",
            {"group_id": group_id, "page_index": page_index, "page_size": page_size},
        )
        messages = [GroupEssenceMessage(**m) for m in data.get("messages", [])]
        return messages, data.get("is_end", True)

    def set_group_essence_message(
        self, group_id: int, message_seq: int, is_set: bool = True
    ) -> None:
        """设置群精华消息"""
        self._request(
            "set_group_essence_message",
            {"group_id": group_id, "message_seq": message_seq, "is_set": is_set},
        )

    def quit_group(self, group_id: int) -> None:
        """退出群"""
        self._request("quit_group", {"group_id": group_id})

    def send_group_message_reaction(
        self, group_id: int, message_seq: int, reaction: str, is_add: bool = True
    ) -> None:
        """发送群消息表情回应"""
        self._request(
            "send_group_message_reaction",
            {"group_id": group_id, "message_seq": message_seq, "reaction": reaction, "is_add": is_add},
        )

    def send_group_nudge(self, group_id: int, user_id: int) -> None:
        """发送群戳一戳"""
        self._request("send_group_nudge", {"group_id": group_id, "user_id": user_id})

    def get_group_notifications(
        self,
        start_notification_seq: Optional[int] = None,
        is_filtered: bool = False,
        limit: int = 20,
    ) -> tuple[list[dict], Optional[int]]:
        """获取群通知列表"""
        params: dict = {"is_filtered": is_filtered, "limit": limit}
        if start_notification_seq is not None:
            params["start_notification_seq"] = start_notification_seq
        data = self._request("get_group_notifications", params)
        return data.get("notifications", []), data.get("next_notification_seq")

    def accept_group_request(
        self,
        notification_seq: int,
        notification_type: NotificationType,
        group_id: int,
        is_filtered: bool = False,
    ) -> None:
        """同意入群/邀请他人入群请求"""
        self._request(
            "accept_group_request",
            {
                "notification_seq": notification_seq,
                "notification_type": notification_type.value,
                "group_id": group_id,
                "is_filtered": is_filtered,
            },
        )

    def reject_group_request(
        self,
        notification_seq: int,
        notification_type: NotificationType,
        group_id: int,
        is_filtered: bool = False,
        reason: Optional[str] = None,
    ) -> None:
        """拒绝入群/邀请他人入群请求"""
        params: dict = {
            "notification_seq": notification_seq,
            "notification_type": notification_type.value,
            "group_id": group_id,
            "is_filtered": is_filtered,
        }
        if reason is not None:
            params["reason"] = reason
        self._request("reject_group_request", params)

    def accept_group_invitation(self, group_id: int, invitation_seq: int) -> None:
        """同意他人邀请自身入群"""
        self._request(
            "accept_group_invitation", {"group_id": group_id, "invitation_seq": invitation_seq}
        )

    def reject_group_invitation(self, group_id: int, invitation_seq: int) -> None:
        """拒绝他人邀请自身入群"""
        self._request(
            "reject_group_invitation", {"group_id": group_id, "invitation_seq": invitation_seq}
        )

    # ========================================================================
    # 文件 API
    # ========================================================================

    def upload_private_file(
        self, user_id: int, file_uri: str, file_name: str
    ) -> UploadFileResult:
        """上传私聊文件"""
        data = self._request(
            "upload_private_file",
            {"user_id": user_id, "file_uri": file_uri, "file_name": file_name},
        )
        return UploadFileResult(**data)

    def upload_group_file(
        self,
        group_id: int,
        file_uri: str,
        file_name: str,
        parent_folder_id: str = "/",
    ) -> UploadFileResult:
        """上传群文件"""
        data = self._request(
            "upload_group_file",
            {
                "group_id": group_id,
                "file_uri": file_uri,
                "file_name": file_name,
                "parent_folder_id": parent_folder_id,
            },
        )
        return UploadFileResult(**data)

    def get_private_file_download_url(
        self, user_id: int, file_id: str, file_hash: str
    ) -> FileDownloadUrl:
        """获取私聊文件下载链接"""
        data = self._request(
            "get_private_file_download_url",
            {"user_id": user_id, "file_id": file_id, "file_hash": file_hash},
        )
        return FileDownloadUrl(**data)

    def get_group_file_download_url(self, group_id: int, file_id: str) -> FileDownloadUrl:
        """获取群文件下载链接"""
        data = self._request(
            "get_group_file_download_url", {"group_id": group_id, "file_id": file_id}
        )
        return FileDownloadUrl(**data)

    def get_group_files(
        self, group_id: int, parent_folder_id: str = "/"
    ) -> tuple[list[GroupFileEntity], list[GroupFolderEntity]]:
        """获取群文件列表"""
        data = self._request(
            "get_group_files", {"group_id": group_id, "parent_folder_id": parent_folder_id}
        )
        files = [GroupFileEntity(**f) for f in data.get("files", [])]
        folders = [GroupFolderEntity(**f) for f in data.get("folders", [])]
        return files, folders

    def move_group_file(
        self,
        group_id: int,
        file_id: str,
        parent_folder_id: str = "/",
        target_folder_id: str = "/",
    ) -> None:
        """移动群文件"""
        self._request(
            "move_group_file",
            {
                "group_id": group_id,
                "file_id": file_id,
                "parent_folder_id": parent_folder_id,
                "target_folder_id": target_folder_id,
            },
        )

    def rename_group_file(
        self,
        group_id: int,
        file_id: str,
        new_file_name: str,
        parent_folder_id: str = "/",
    ) -> None:
        """重命名群文件"""
        self._request(
            "rename_group_file",
            {
                "group_id": group_id,
                "file_id": file_id,
                "new_file_name": new_file_name,
                "parent_folder_id": parent_folder_id,
            },
        )

    def delete_group_file(self, group_id: int, file_id: str) -> None:
        """删除群文件"""
        self._request("delete_group_file", {"group_id": group_id, "file_id": file_id})

    def create_group_folder(self, group_id: int, folder_name: str) -> CreateFolderResult:
        """创建群文件夹"""
        data = self._request(
            "create_group_folder", {"group_id": group_id, "folder_name": folder_name}
        )
        return CreateFolderResult(**data)

    def rename_group_folder(
        self, group_id: int, folder_id: str, new_folder_name: str
    ) -> None:
        """重命名群文件夹"""
        self._request(
            "rename_group_folder",
            {"group_id": group_id, "folder_id": folder_id, "new_folder_name": new_folder_name},
        )

    def delete_group_folder(self, group_id: int, folder_id: str) -> None:
        """删除群文件夹"""
        self._request("delete_group_folder", {"group_id": group_id, "folder_id": folder_id})
