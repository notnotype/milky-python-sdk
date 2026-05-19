import unittest

from milky.async_client import AsyncMilkyClient
from milky.client import MilkyClient
from milky.models import (
    GroupAdminChangeNotification,
    GroupInvitedJoinRequestNotification,
    GroupJoinRequestNotification,
    GroupMemberKickNotification,
    GroupMemberQuitNotification,
)


NOTIFICATIONS = [
    {
        "type": "join_request",
        "group_id": 20001,
        "notification_seq": 1,
        "is_filtered": False,
        "initiator_id": 10001,
        "state": "pending",
        "comment": "hello",
    },
    {
        "type": "admin_change",
        "group_id": 20001,
        "notification_seq": 2,
        "target_user_id": 10002,
        "is_set": True,
        "operator_id": 10003,
    },
    {
        "type": "kick",
        "group_id": 20001,
        "notification_seq": 3,
        "target_user_id": 10004,
        "operator_id": 10003,
    },
    {
        "type": "quit",
        "group_id": 20001,
        "notification_seq": 4,
        "target_user_id": 10005,
    },
    {
        "type": "invited_join_request",
        "group_id": 20001,
        "notification_seq": 5,
        "initiator_id": 10006,
        "target_user_id": 10007,
        "state": "accepted",
    },
]


class FakeMilkyClient(MilkyClient):
    def __init__(self):
        pass

    def _request(self, endpoint: str, data: dict | None = None) -> dict:
        if endpoint == "get_group_notifications":
            return {"notifications": NOTIFICATIONS, "next_notification_seq": 6}
        raise AssertionError(endpoint)


class FakeAsyncMilkyClient(AsyncMilkyClient):
    def __init__(self):
        pass

    async def _request(self, endpoint: str, data: dict | None = None) -> dict:
        if endpoint == "get_group_notifications":
            return {"notifications": NOTIFICATIONS, "next_notification_seq": 6}
        raise AssertionError(endpoint)


class GroupNotificationParsingTest(unittest.TestCase):
    def assert_notification_models(self, notifications, next_seq) -> None:
        self.assertIsInstance(notifications[0], GroupJoinRequestNotification)
        self.assertIsInstance(notifications[1], GroupAdminChangeNotification)
        self.assertIsInstance(notifications[2], GroupMemberKickNotification)
        self.assertIsInstance(notifications[3], GroupMemberQuitNotification)
        self.assertIsInstance(notifications[4], GroupInvitedJoinRequestNotification)
        self.assertEqual(next_seq, 6)

    def test_sync_group_notifications_return_models(self) -> None:
        notifications, next_seq = FakeMilkyClient().get_group_notifications()

        self.assert_notification_models(notifications, next_seq)

    def test_async_group_notifications_return_models(self) -> None:
        async def run() -> None:
            notifications, next_seq = await FakeAsyncMilkyClient().get_group_notifications()

            self.assert_notification_models(notifications, next_seq)

        import asyncio

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
