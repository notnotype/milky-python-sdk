"""Milky SDK - Python SDK for Milky Protocol"""

from milky.client import MilkyClient
from milky.async_client import AsyncMilkyClient
from milky.bot import MilkyBot, EventType
from milky.models import (
    # Enums
    Sex,
    Role,
    MessageScene,
    ImageSubType,
    # Entities
    FriendCategoryEntity,
    FriendEntity,
    GroupEntity,
    GroupMemberEntity,
    # Incoming Segments
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
    # Outgoing Segments
    OutgoingTextSegment,
    OutgoingMentionSegment,
    OutgoingImageSegment,
    OutgoingRecordSegment,
    OutgoingVideoSegment,
    OutgoingForwardSegment,
    # Segment Data
    TextSegmentData,
    MentionSegmentData,
    OutgoingImageSegmentData,
    # Messages
    FriendMessage,
    GroupMessage,
    TempMessage,
)

__all__ = [
    # Clients
    "MilkyClient",
    "AsyncMilkyClient",
    "MilkyBot",
    "EventType",
    # Enums
    "Sex",
    "Role",
    "MessageScene",
    "ImageSubType",
    # Entities
    "FriendCategoryEntity",
    "FriendEntity",
    "GroupEntity",
    "GroupMemberEntity",
    # Incoming Segments
    "TextSegment",
    "MentionSegment",
    "MentionAllSegment",
    "FaceSegment",
    "ReplySegment",
    "ImageSegment",
    "RecordSegment",
    "VideoSegment",
    "FileSegment",
    "ForwardSegment",
    # Outgoing Segments
    "OutgoingTextSegment",
    "OutgoingMentionSegment",
    "OutgoingImageSegment",
    "OutgoingRecordSegment",
    "OutgoingVideoSegment",
    "OutgoingForwardSegment",
    # Segment Data
    "TextSegmentData",
    "MentionSegmentData",
    "OutgoingImageSegmentData",
    # Messages
    "FriendMessage",
    "GroupMessage",
    "TempMessage",
]

__version__ = "0.2.0"
