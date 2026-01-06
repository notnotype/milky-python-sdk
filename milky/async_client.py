"""Async Milky API Client"""

from __future__ import annotations

import json
from typing import AsyncGenerator, Optional

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


class AsyncMilkyClient:
    """Async Milky Protocol API Client"""

    def __init__(
        self,
        base_url: str,
        access_token: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token
        self.timeout = timeout
        
        headers = {"Content-Type": "application/json"}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncMilkyClient":
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()

    async def _request(self, endpoint: str, data: Optional[dict] = None) -> dict:
        try:
            response = await self._client.post(f"/api/{endpoint}", json=data or {})
        except httpx.ConnectError as e:
            raise MilkyHttpError(0, f"连接失败: {e}")
        except httpx.TimeoutException as e:
            raise MilkyHttpError(0, f"请求超时: {e}")
        
        if response.status_code == 401:
            raise MilkyHttpError(401, "鉴权失败")
        elif response.status_code == 404:
            raise MilkyHttpError(404, f"API 不存在: {endpoint}")
        elif response.status_code == 415:
            raise MilkyHttpError(415, "Content-Type 错误")
        elif response.status_code != 200:
            raise MilkyHttpError(response.status_code, response.text)
        
        try:
            result = response.json()
        except json.JSONDecodeError:
            raise MilkyHttpError(response.status_code, f"无法解析: {response.text}")
        
        if result.get("status") != "ok":
            raise MilkyError(result.get("retcode", -1), result.get("message", "Unknown"))
        
        return result.get("data", {})

    # ========================================================================
    # 事件接收
    # ========================================================================

    async def events_sse(self) -> AsyncGenerator[dict, None]:
        """异步 SSE 事件流"""
        headers = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", f"{self.base_url}/event", headers=headers) as response:
                if response.status_code == 401:
                    raise MilkyHttpError(401, "鉴权失败")
                response.raise_for_status()
                
                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    while "\n\n" in buffer:
                        message, buffer = buffer.split("\n\n", 1)
                        data_lines = []
                        for line in message.split("\n"):
                            if line.startswith("data: "):
                                data_lines.append(line[6:])
                            elif line.startswith("data:"):
                                data_lines.append(line[5:])
                        
                        if data_lines:
                            try:
                                yield json.loads("".join(data_lines))
                            except json.JSONDecodeError:
                                continue

    # ========================================================================
    # 系统 API
    # ========================================================================

    async def get_login_info(self) -> LoginInfo:
        data = await self._request("get_login_info")
        return LoginInfo(**data)

    async def get_impl_info(self) -> ImplInfo:
        data = await self._request("get_impl_info")
        return ImplInfo(**data)

    async def get_user_profile(self, user_id: int) -> UserProfile:
        data = await self._request("get_user_profile", {"user_id": user_id})
        return UserProfile(**data)

    async def get_friend_list(self, no_cache: bool = False) -> list[FriendEntity]:
        data = await self._request("get_friend_list", {"no_cache": no_cache})
        return [FriendEntity(**f) for f in data.get("friends", [])]

    async def get_friend_info(self, user_id: int, no_cache: bool = False) -> FriendEntity:
        data = await self._request("get_friend_info", {"user_id": user_id, "no_cache": no_cache})
        return FriendEntity(**data.get("friend", {}))

    async def get_group_list(self, no_cache: bool = False) -> list[GroupEntity]:
        data = await self._request("get_group_list", {"no_cache": no_cache})
        return [GroupEntity(**g) for g in data.get("groups", [])]

    async def get_group_info(self, group_id: int, no_cache: bool = False) -> GroupEntity:
        data = await self._request("get_group_info", {"group_id": group_id, "no_cache": no_cache})
        return GroupEntity(**data.get("group", {}))

    async def get_group_member_list(self, group_id: int, no_cache: bool = False) -> list[GroupMemberEntity]:
        data = await self._request("get_group_member_list", {"group_id": group_id, "no_cache": no_cache})
        return [GroupMemberEntity(**m) for m in data.get("members", [])]

    async def get_group_member_info(self, group_id: int, user_id: int, no_cache: bool = False) -> GroupMemberEntity:
        data = await self._request("get_group_member_info", {"group_id": group_id, "user_id": user_id, "no_cache": no_cache})
        return GroupMemberEntity(**data.get("member", {}))

    async def get_cookies(self, domain: str) -> str:
        data = await self._request("get_cookies", {"domain": domain})
        return data.get("cookies", "")

    async def get_csrf_token(self) -> str:
        data = await self._request("get_csrf_token")
        return data.get("csrf_token", "")

    # ========================================================================
    # 消息 API
    # ========================================================================

    async def send_private_message(self, user_id: int, message: list[OutgoingSegment]) -> SendMessageResult:
        data = await self._request("send_private_message", {"user_id": user_id, "message": [s.model_dump() for s in message]})
        return SendMessageResult(**data)

    async def send_group_message(self, group_id: int, message: list[OutgoingSegment]) -> SendMessageResult:
        data = await self._request("send_group_message", {"group_id": group_id, "message": [s.model_dump() for s in message]})
        return SendMessageResult(**data)

    async def recall_private_message(self, user_id: int, message_seq: int) -> None:
        await self._request("recall_private_message", {"user_id": user_id, "message_seq": message_seq})

    async def recall_group_message(self, group_id: int, message_seq: int) -> None:
        await self._request("recall_group_message", {"group_id": group_id, "message_seq": message_seq})

    async def get_message(self, message_scene: MessageScene, peer_id: int, message_seq: int) -> IncomingMessage:
        data = await self._request("get_message", {"message_scene": message_scene.value, "peer_id": peer_id, "message_seq": message_seq})
        return data.get("message", {})

    async def get_history_messages(self, message_scene: MessageScene, peer_id: int, start_message_seq: Optional[int] = None, limit: int = 20) -> tuple[list[IncomingMessage], Optional[int]]:
        params: dict = {"message_scene": message_scene.value, "peer_id": peer_id, "limit": limit}
        if start_message_seq is not None:
            params["start_message_seq"] = start_message_seq
        data = await self._request("get_history_messages", params)
        return data.get("messages", []), data.get("next_message_seq")

    async def get_resource_temp_url(self, resource_id: str) -> ResourceTempUrl:
        data = await self._request("get_resource_temp_url", {"resource_id": resource_id})
        return ResourceTempUrl(**data)

    async def get_forwarded_messages(self, forward_id: str) -> list[IncomingForwardedMessage]:
        data = await self._request("get_forwarded_messages", {"forward_id": forward_id})
        return [IncomingForwardedMessage(**m) for m in data.get("messages", [])]

    async def mark_message_as_read(self, message_scene: MessageScene, peer_id: int, message_seq: int) -> None:
        await self._request("mark_message_as_read", {"message_scene": message_scene.value, "peer_id": peer_id, "message_seq": message_seq})

    # ========================================================================
    # 好友 API
    # ========================================================================

    async def send_friend_nudge(self, user_id: int, is_self: bool = False) -> None:
        await self._request("send_friend_nudge", {"user_id": user_id, "is_self": is_self})

    async def send_profile_like(self, user_id: int, count: int = 1) -> None:
        await self._request("send_profile_like", {"user_id": user_id, "count": count})

    async def get_friend_requests(self, limit: int = 20, is_filtered: bool = False) -> list[FriendRequest]:
        data = await self._request("get_friend_requests", {"limit": limit, "is_filtered": is_filtered})
        return [FriendRequest(**r) for r in data.get("requests", [])]

    async def accept_friend_request(self, initiator_uid: str, is_filtered: bool = False) -> None:
        await self._request("accept_friend_request", {"initiator_uid": initiator_uid, "is_filtered": is_filtered})

    async def reject_friend_request(self, initiator_uid: str, is_filtered: bool = False, reason: Optional[str] = None) -> None:
        params: dict = {"initiator_uid": initiator_uid, "is_filtered": is_filtered}
        if reason:
            params["reason"] = reason
        await self._request("reject_friend_request", params)

    # ========================================================================
    # 群聊 API
    # ========================================================================

    async def set_group_name(self, group_id: int, new_group_name: str) -> None:
        await self._request("set_group_name", {"group_id": group_id, "new_group_name": new_group_name})

    async def set_group_avatar(self, group_id: int, image_uri: str) -> None:
        await self._request("set_group_avatar", {"group_id": group_id, "image_uri": image_uri})

    async def set_group_member_card(self, group_id: int, user_id: int, card: str) -> None:
        await self._request("set_group_member_card", {"group_id": group_id, "user_id": user_id, "card": card})

    async def set_group_member_special_title(self, group_id: int, user_id: int, special_title: str) -> None:
        await self._request("set_group_member_special_title", {"group_id": group_id, "user_id": user_id, "special_title": special_title})

    async def set_group_member_admin(self, group_id: int, user_id: int, is_set: bool = True) -> None:
        await self._request("set_group_member_admin", {"group_id": group_id, "user_id": user_id, "is_set": is_set})

    async def set_group_member_mute(self, group_id: int, user_id: int, duration: int = 0) -> None:
        await self._request("set_group_member_mute", {"group_id": group_id, "user_id": user_id, "duration": duration})

    async def set_group_whole_mute(self, group_id: int, is_mute: bool = True) -> None:
        await self._request("set_group_whole_mute", {"group_id": group_id, "is_mute": is_mute})

    async def kick_group_member(self, group_id: int, user_id: int, reject_add_request: bool = False) -> None:
        await self._request("kick_group_member", {"group_id": group_id, "user_id": user_id, "reject_add_request": reject_add_request})

    async def get_group_announcements(self, group_id: int) -> list[GroupAnnouncementEntity]:
        data = await self._request("get_group_announcements", {"group_id": group_id})
        return [GroupAnnouncementEntity(**a) for a in data.get("announcements", [])]

    async def send_group_announcement(self, group_id: int, content: str, image_uri: Optional[str] = None) -> None:
        params: dict = {"group_id": group_id, "content": content}
        if image_uri:
            params["image_uri"] = image_uri
        await self._request("send_group_announcement", params)

    async def delete_group_announcement(self, group_id: int, announcement_id: str) -> None:
        await self._request("delete_group_announcement", {"group_id": group_id, "announcement_id": announcement_id})

    async def get_group_essence_messages(self, group_id: int, page_index: int, page_size: int) -> tuple[list[GroupEssenceMessage], bool]:
        data = await self._request("get_group_essence_messages", {"group_id": group_id, "page_index": page_index, "page_size": page_size})
        return [GroupEssenceMessage(**m) for m in data.get("messages", [])], data.get("is_end", True)

    async def set_group_essence_message(self, group_id: int, message_seq: int, is_set: bool = True) -> None:
        await self._request("set_group_essence_message", {"group_id": group_id, "message_seq": message_seq, "is_set": is_set})

    async def quit_group(self, group_id: int) -> None:
        await self._request("quit_group", {"group_id": group_id})

    async def send_group_message_reaction(self, group_id: int, message_seq: int, reaction: str, is_add: bool = True) -> None:
        await self._request("send_group_message_reaction", {"group_id": group_id, "message_seq": message_seq, "reaction": reaction, "is_add": is_add})

    async def send_group_nudge(self, group_id: int, user_id: int) -> None:
        await self._request("send_group_nudge", {"group_id": group_id, "user_id": user_id})

    async def get_group_notifications(self, start_notification_seq: Optional[int] = None, is_filtered: bool = False, limit: int = 20) -> tuple[list[dict], Optional[int]]:
        params: dict = {"is_filtered": is_filtered, "limit": limit}
        if start_notification_seq is not None:
            params["start_notification_seq"] = start_notification_seq
        data = await self._request("get_group_notifications", params)
        return data.get("notifications", []), data.get("next_notification_seq")

    async def accept_group_request(self, notification_seq: int, notification_type: NotificationType, group_id: int, is_filtered: bool = False) -> None:
        await self._request("accept_group_request", {"notification_seq": notification_seq, "notification_type": notification_type.value, "group_id": group_id, "is_filtered": is_filtered})

    async def reject_group_request(self, notification_seq: int, notification_type: NotificationType, group_id: int, is_filtered: bool = False, reason: Optional[str] = None) -> None:
        params: dict = {"notification_seq": notification_seq, "notification_type": notification_type.value, "group_id": group_id, "is_filtered": is_filtered}
        if reason:
            params["reason"] = reason
        await self._request("reject_group_request", params)

    async def accept_group_invitation(self, group_id: int, invitation_seq: int) -> None:
        await self._request("accept_group_invitation", {"group_id": group_id, "invitation_seq": invitation_seq})

    async def reject_group_invitation(self, group_id: int, invitation_seq: int) -> None:
        await self._request("reject_group_invitation", {"group_id": group_id, "invitation_seq": invitation_seq})

    # ========================================================================
    # 文件 API
    # ========================================================================

    async def upload_private_file(self, user_id: int, file_uri: str, file_name: str) -> UploadFileResult:
        data = await self._request("upload_private_file", {"user_id": user_id, "file_uri": file_uri, "file_name": file_name})
        return UploadFileResult(**data)

    async def upload_group_file(self, group_id: int, file_uri: str, file_name: str, parent_folder_id: str = "/") -> UploadFileResult:
        data = await self._request("upload_group_file", {"group_id": group_id, "file_uri": file_uri, "file_name": file_name, "parent_folder_id": parent_folder_id})
        return UploadFileResult(**data)

    async def get_private_file_download_url(self, user_id: int, file_id: str, file_hash: str) -> FileDownloadUrl:
        data = await self._request("get_private_file_download_url", {"user_id": user_id, "file_id": file_id, "file_hash": file_hash})
        return FileDownloadUrl(**data)

    async def get_group_file_download_url(self, group_id: int, file_id: str) -> FileDownloadUrl:
        data = await self._request("get_group_file_download_url", {"group_id": group_id, "file_id": file_id})
        return FileDownloadUrl(**data)

    async def get_group_files(self, group_id: int, parent_folder_id: str = "/") -> tuple[list[GroupFileEntity], list[GroupFolderEntity]]:
        data = await self._request("get_group_files", {"group_id": group_id, "parent_folder_id": parent_folder_id})
        return [GroupFileEntity(**f) for f in data.get("files", [])], [GroupFolderEntity(**f) for f in data.get("folders", [])]

    async def move_group_file(self, group_id: int, file_id: str, parent_folder_id: str = "/", target_folder_id: str = "/") -> None:
        await self._request("move_group_file", {"group_id": group_id, "file_id": file_id, "parent_folder_id": parent_folder_id, "target_folder_id": target_folder_id})

    async def rename_group_file(self, group_id: int, file_id: str, new_file_name: str, parent_folder_id: str = "/") -> None:
        await self._request("rename_group_file", {"group_id": group_id, "file_id": file_id, "new_file_name": new_file_name, "parent_folder_id": parent_folder_id})

    async def delete_group_file(self, group_id: int, file_id: str) -> None:
        await self._request("delete_group_file", {"group_id": group_id, "file_id": file_id})

    async def create_group_folder(self, group_id: int, folder_name: str) -> CreateFolderResult:
        data = await self._request("create_group_folder", {"group_id": group_id, "folder_name": folder_name})
        return CreateFolderResult(**data)

    async def rename_group_folder(self, group_id: int, folder_id: str, new_folder_name: str) -> None:
        await self._request("rename_group_folder", {"group_id": group_id, "folder_id": folder_id, "new_folder_name": new_folder_name})

    async def delete_group_folder(self, group_id: int, folder_id: str) -> None:
        await self._request("delete_group_folder", {"group_id": group_id, "folder_id": folder_id})
