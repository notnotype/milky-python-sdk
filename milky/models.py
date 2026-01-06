"""Pydantic models for Milky SDK"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================


class Sex(str, Enum):
    """用户性别"""

    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"


class Role(str, Enum):
    """群成员权限等级"""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class MessageScene(str, Enum):
    """消息场景"""

    FRIEND = "friend"
    GROUP = "group"
    TEMP = "temp"


class ImageSubType(str, Enum):
    """图片类型"""

    NORMAL = "normal"
    STICKER = "sticker"


class RequestState(str, Enum):
    """请求状态"""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    IGNORED = "ignored"


class NotificationType(str, Enum):
    """群通知类型"""

    JOIN_REQUEST = "join_request"
    INVITED_JOIN_REQUEST = "invited_join_request"


# ============================================================================
# Entities
# ============================================================================


class FriendCategoryEntity(BaseModel):
    """好友分组实体"""

    category_id: int = Field(description="好友分组 ID")
    category_name: str = Field(description="好友分组名称")


class FriendEntity(BaseModel):
    """好友实体"""

    user_id: int = Field(description="用户 QQ 号")
    nickname: str = Field(description="用户昵称")
    sex: Sex = Field(description="用户性别")
    qid: str = Field(description="用户 QID")
    remark: str = Field(description="好友备注")
    category: FriendCategoryEntity = Field(description="好友分组")


class GroupEntity(BaseModel):
    """群实体"""

    group_id: int = Field(description="群号")
    group_name: str = Field(description="群名称")
    member_count: int = Field(description="群成员数量")
    max_member_count: int = Field(description="群容量")


class GroupMemberEntity(BaseModel):
    """群成员实体"""

    user_id: int = Field(description="用户 QQ 号")
    nickname: str = Field(description="用户昵称")
    sex: Sex = Field(description="用户性别")
    group_id: int = Field(description="群号")
    card: str = Field(description="成员备注")
    title: str = Field(description="专属头衔")
    level: int = Field(description="群等级")
    role: Role = Field(description="权限等级")
    join_time: int = Field(description="入群时间，Unix 时间戳（秒）")
    last_sent_time: int = Field(description="最后发言时间，Unix 时间戳（秒）")
    shut_up_end_time: Optional[int] = Field(
        default=None, description="禁言结束时间，Unix 时间戳（秒）"
    )


class GroupAnnouncementEntity(BaseModel):
    """群公告实体"""

    group_id: int = Field(description="群号")
    announcement_id: str = Field(description="公告 ID")
    user_id: int = Field(description="发送者 QQ 号")
    time: int = Field(description="Unix 时间戳（秒）")
    content: str = Field(description="公告内容")
    image_url: Optional[str] = Field(default=None, description="公告图片 URL")


class GroupFileEntity(BaseModel):
    """群文件实体"""

    group_id: int = Field(description="群号")
    file_id: str = Field(description="文件 ID")
    file_name: str = Field(description="文件名称")
    parent_folder_id: str = Field(description="父文件夹 ID")
    file_size: int = Field(description="文件大小（字节）")
    uploaded_time: int = Field(description="上传时的 Unix 时间戳（秒）")
    expire_time: Optional[int] = Field(
        default=None, description="过期时的 Unix 时间戳（秒）"
    )
    uploader_id: int = Field(description="上传者 QQ 号")
    downloaded_times: int = Field(description="下载次数")


class GroupFolderEntity(BaseModel):
    """群文件夹实体"""

    group_id: int = Field(description="群号")
    folder_id: str = Field(description="文件夹 ID")
    parent_folder_id: str = Field(description="父文件夹 ID")
    folder_name: str = Field(description="文件夹名称")
    created_time: int = Field(description="创建时的 Unix 时间戳（秒）")
    last_modified_time: int = Field(description="最后修改时的 Unix 时间戳（秒）")
    creator_id: int = Field(description="创建者 QQ 号")
    file_count: int = Field(description="文件数量")


class FriendRequest(BaseModel):
    """好友请求实体"""

    time: int = Field(description="请求发起时的 Unix 时间戳（秒）")
    initiator_id: int = Field(description="请求发起者 QQ 号")
    initiator_uid: str = Field(description="请求发起者 UID")
    target_user_id: int = Field(description="目标用户 QQ 号")
    target_user_uid: str = Field(description="目标用户 UID")
    state: RequestState = Field(description="请求状态")
    comment: str = Field(description="申请附加信息")
    via: str = Field(description="申请来源")
    is_filtered: bool = Field(description="请求是否被过滤（发起自风险账户）")


# ============================================================================
# Incoming Message Segments (接收消息段)
# ============================================================================


class TextSegmentData(BaseModel):
    """文本消息段数据"""

    text: str = Field(description="文本内容")


class TextSegment(BaseModel):
    """文本消息段"""

    type: Literal["text"] = "text"
    data: TextSegmentData


class MentionSegmentData(BaseModel):
    """提及消息段数据"""

    user_id: int = Field(description="提及的 QQ 号")


class MentionSegment(BaseModel):
    """提及消息段"""

    type: Literal["mention"] = "mention"
    data: MentionSegmentData


class MentionAllSegmentData(BaseModel):
    """提及全体消息段数据"""

    pass


class MentionAllSegment(BaseModel):
    """提及全体消息段"""

    type: Literal["mention_all"] = "mention_all"
    data: MentionAllSegmentData


class FaceSegmentData(BaseModel):
    """表情消息段数据"""

    face_id: str = Field(description="表情 ID")


class FaceSegment(BaseModel):
    """表情消息段"""

    type: Literal["face"] = "face"
    data: FaceSegmentData


class ReplySegmentData(BaseModel):
    """回复消息段数据"""

    message_seq: int = Field(description="被引用的消息序列号")


class ReplySegment(BaseModel):
    """回复消息段"""

    type: Literal["reply"] = "reply"
    data: ReplySegmentData


class ImageSegmentData(BaseModel):
    """图片消息段数据"""

    resource_id: str = Field(description="资源 ID")
    temp_url: str = Field(description="临时 URL")
    width: int = Field(description="图片宽度")
    height: int = Field(description="图片高度")
    summary: str = Field(description="图片预览文本")
    sub_type: ImageSubType = Field(description="图片类型")


class ImageSegment(BaseModel):
    """图片消息段"""

    type: Literal["image"] = "image"
    data: ImageSegmentData


class RecordSegmentData(BaseModel):
    """语音消息段数据"""

    resource_id: str = Field(description="资源 ID")
    temp_url: str = Field(description="临时 URL")
    duration: int = Field(description="语音时长（秒）")


class RecordSegment(BaseModel):
    """语音消息段"""

    type: Literal["record"] = "record"
    data: RecordSegmentData


class VideoSegmentData(BaseModel):
    """视频消息段数据"""

    resource_id: str = Field(description="资源 ID")
    temp_url: str = Field(description="临时 URL")
    width: int = Field(description="视频宽度")
    height: int = Field(description="视频高度")
    duration: int = Field(description="视频时长（秒）")


class VideoSegment(BaseModel):
    """视频消息段"""

    type: Literal["video"] = "video"
    data: VideoSegmentData


class FileSegmentData(BaseModel):
    """文件消息段数据"""

    file_id: str = Field(description="文件 ID")
    file_name: str = Field(description="文件名称")
    file_size: int = Field(description="文件大小（字节）")
    file_hash: Optional[str] = Field(default=None, description="文件的 TriSHA1 哈希值")


class FileSegment(BaseModel):
    """文件消息段"""

    type: Literal["file"] = "file"
    data: FileSegmentData


class ForwardSegmentData(BaseModel):
    """合并转发消息段数据"""

    forward_id: str = Field(description="合并转发 ID")


class ForwardSegment(BaseModel):
    """合并转发消息段"""

    type: Literal["forward"] = "forward"
    data: ForwardSegmentData


class MarketFaceSegmentData(BaseModel):
    """市场表情消息段数据"""

    url: str = Field(description="市场表情 URL")


class MarketFaceSegment(BaseModel):
    """市场表情消息段"""

    type: Literal["market_face"] = "market_face"
    data: MarketFaceSegmentData


class LightAppSegmentData(BaseModel):
    """小程序消息段数据"""

    app_name: str = Field(description="小程序名称")
    json_payload: str = Field(description="小程序 JSON 数据")


class LightAppSegment(BaseModel):
    """小程序消息段"""

    type: Literal["light_app"] = "light_app"
    data: LightAppSegmentData


class XmlSegmentData(BaseModel):
    """XML 消息段数据"""

    service_id: int = Field(description="服务 ID")
    xml_payload: str = Field(description="XML 数据")


class XmlSegment(BaseModel):
    """XML 消息段"""

    type: Literal["xml"] = "xml"
    data: XmlSegmentData


# Union type for incoming segments
IncomingSegment = Annotated[
    Union[
        TextSegment,
        MentionSegment,
        MentionAllSegment,
        FaceSegment,
        ReplySegment,
        ImageSegment,
        RecordSegment,
        VideoSegment,
        FileSegment,
        ForwardSegment,
        MarketFaceSegment,
        LightAppSegment,
        XmlSegment,
    ],
    Field(discriminator="type"),
]


# ============================================================================
# Outgoing Message Segments (发送消息段)
# ============================================================================


class OutgoingTextSegment(BaseModel):
    """发送文本消息段"""

    type: Literal["text"] = "text"
    data: TextSegmentData


class OutgoingMentionSegment(BaseModel):
    """发送提及消息段"""

    type: Literal["mention"] = "mention"
    data: MentionSegmentData


class OutgoingMentionAllSegment(BaseModel):
    """发送提及全体消息段"""

    type: Literal["mention_all"] = "mention_all"
    data: MentionAllSegmentData


class OutgoingFaceSegment(BaseModel):
    """发送表情消息段"""

    type: Literal["face"] = "face"
    data: FaceSegmentData


class OutgoingReplySegment(BaseModel):
    """发送回复消息段"""

    type: Literal["reply"] = "reply"
    data: ReplySegmentData


class OutgoingImageSegmentData(BaseModel):
    """发送图片消息段数据"""

    uri: str = Field(
        description="文件 URI，支持 `file://` `http(s)://` `base64://` 三种格式"
    )
    summary: Optional[str] = Field(default=None, description="图片预览文本")
    sub_type: ImageSubType = Field(description="图片类型")


class OutgoingImageSegment(BaseModel):
    """发送图片消息段"""

    type: Literal["image"] = "image"
    data: OutgoingImageSegmentData


class OutgoingRecordSegmentData(BaseModel):
    """发送语音消息段数据"""

    uri: str = Field(
        description="文件 URI，支持 `file://` `http(s)://` `base64://` 三种格式"
    )


class OutgoingRecordSegment(BaseModel):
    """发送语音消息段"""

    type: Literal["record"] = "record"
    data: OutgoingRecordSegmentData


class OutgoingVideoSegmentData(BaseModel):
    """发送视频消息段数据"""

    uri: str = Field(
        description="文件 URI，支持 `file://` `http(s)://` `base64://` 三种格式"
    )
    thumb_uri: Optional[str] = Field(default=None, description="封面图片 URI")


class OutgoingVideoSegment(BaseModel):
    """发送视频消息段"""

    type: Literal["video"] = "video"
    data: OutgoingVideoSegmentData


class OutgoingForwardedMessage(BaseModel):
    """发送转发消息"""

    user_id: int = Field(description="发送者 QQ 号")
    sender_name: str = Field(description="发送者名称")
    segments: list["OutgoingSegment"] = Field(description="消息段列表")


class OutgoingForwardSegmentData(BaseModel):
    """发送合并转发消息段数据"""

    messages: list[OutgoingForwardedMessage] = Field(description="合并转发消息段")


class OutgoingForwardSegment(BaseModel):
    """发送合并转发消息段"""

    type: Literal["forward"] = "forward"
    data: OutgoingForwardSegmentData


# Union type for outgoing segments
OutgoingSegment = Annotated[
    Union[
        OutgoingTextSegment,
        OutgoingMentionSegment,
        OutgoingMentionAllSegment,
        OutgoingFaceSegment,
        OutgoingReplySegment,
        OutgoingImageSegment,
        OutgoingRecordSegment,
        OutgoingVideoSegment,
        OutgoingForwardSegment,
    ],
    Field(discriminator="type"),
]


# ============================================================================
# Incoming Messages (接收消息)
# ============================================================================


class FriendMessage(BaseModel):
    """好友消息"""

    message_scene: Literal["friend"] = "friend"
    peer_id: int = Field(description="好友 QQ 号")
    message_seq: int = Field(description="消息序列号")
    sender_id: int = Field(description="发送者 QQ 号")
    time: int = Field(description="消息 Unix 时间戳（秒）")
    segments: list[IncomingSegment] = Field(description="消息段列表")
    friend: FriendEntity = Field(description="好友信息")


class GroupMessage(BaseModel):
    """群消息"""

    message_scene: Literal["group"] = "group"
    peer_id: int = Field(description="群号")
    message_seq: int = Field(description="消息序列号")
    sender_id: int = Field(description="发送者 QQ 号")
    time: int = Field(description="消息 Unix 时间戳（秒）")
    segments: list[IncomingSegment] = Field(description="消息段列表")
    group: GroupEntity = Field(description="群信息")
    group_member: GroupMemberEntity = Field(description="群成员信息")


class TempMessage(BaseModel):
    """临时会话消息"""

    message_scene: Literal["temp"] = "temp"
    peer_id: int = Field(description="好友 QQ 号或群号")
    message_seq: int = Field(description="消息序列号")
    sender_id: int = Field(description="发送者 QQ 号")
    time: int = Field(description="消息 Unix 时间戳（秒）")
    segments: list[IncomingSegment] = Field(description="消息段列表")
    group: Optional[GroupEntity] = Field(
        default=None, description="临时会话发送者的所在的群信息"
    )


# Union type for incoming messages
IncomingMessage = Annotated[
    Union[FriendMessage, GroupMessage, TempMessage],
    Field(discriminator="message_scene"),
]


# ============================================================================
# Forwarded Messages
# ============================================================================


class IncomingForwardedMessage(BaseModel):
    """接收转发消息"""

    sender_name: str = Field(description="发送者名称")
    avatar_url: str = Field(description="发送者头像 URL")
    time: int = Field(description="消息 Unix 时间戳（秒）")
    segments: list[IncomingSegment] = Field(description="消息段列表")


class GroupEssenceMessage(BaseModel):
    """群精华消息"""

    group_id: int = Field(description="群号")
    message_seq: int = Field(description="消息序列号")
    message_time: int = Field(description="消息发送时的 Unix 时间戳（秒）")
    sender_id: int = Field(description="发送者 QQ 号")
    sender_name: str = Field(description="发送者名称")
    operator_id: int = Field(description="设置精华的操作者 QQ 号")
    operator_name: str = Field(description="设置精华的操作者名称")
    operation_time: int = Field(description="消息被设置精华时的 Unix 时间戳（秒）")
    segments: list[IncomingSegment] = Field(description="消息段列表")


# ============================================================================
# API Response Models
# ============================================================================


class ApiResponse(BaseModel):
    """API 响应"""

    status: Literal["ok", "failed"]
    retcode: int = Field(description="业务状态码，0 表示成功")
    data: Optional[Any] = None
    message: Optional[str] = Field(default=None, description="错误消息")


class LoginInfo(BaseModel):
    """登录信息"""

    uin: int = Field(description="登录 QQ 号")
    nickname: str = Field(description="登录昵称")


class ImplInfo(BaseModel):
    """协议端信息"""

    impl_name: str = Field(description="协议端名称")
    impl_version: str = Field(description="协议端版本")
    qq_protocol_version: str = Field(description="协议端使用的 QQ 协议版本")
    qq_protocol_type: str = Field(description="协议端使用的 QQ 协议平台")
    milky_version: str = Field(description="协议端实现的 Milky 协议版本")


class UserProfile(BaseModel):
    """用户个人信息"""

    nickname: str = Field(description="昵称")
    qid: str = Field(description="QID")
    age: int = Field(description="年龄")
    sex: Sex = Field(description="性别")
    remark: str = Field(description="备注")
    bio: str = Field(description="个性签名")
    level: int = Field(description="QQ 等级")
    country: str = Field(description="国家或地区")
    city: str = Field(description="城市")
    school: str = Field(description="学校")


class SendMessageResult(BaseModel):
    """发送消息结果"""

    message_seq: int = Field(description="消息序列号")
    time: int = Field(description="消息发送时间")


class ResourceTempUrl(BaseModel):
    """临时资源链接"""

    url: str = Field(description="临时资源链接")


class UploadFileResult(BaseModel):
    """上传文件结果"""

    file_id: str = Field(description="文件 ID")


class FileDownloadUrl(BaseModel):
    """文件下载链接"""

    download_url: str = Field(description="文件下载链接")


class CreateFolderResult(BaseModel):
    """创建文件夹结果"""

    folder_id: str = Field(description="文件夹 ID")
