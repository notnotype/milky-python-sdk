import unittest

from milky.async_client import AsyncMilkyClient
from milky.client import MilkyClient
from milky.models import FriendMessage, GroupMessage, MessageScene


FRIEND_MESSAGE = {
    "message_scene": "friend",
    "peer_id": 10001,
    "message_seq": 1,
    "sender_id": 10001,
    "time": 1710000000,
    "segments": [{"type": "text", "data": {"text": "hello"}}],
    "friend": {
        "user_id": 10001,
        "nickname": "Alice",
        "sex": "unknown",
        "qid": "",
        "remark": "",
        "category": {"category_id": 0, "category_name": "default"},
    },
}

GROUP_MESSAGE = {
    "message_scene": "group",
    "peer_id": 20001,
    "message_seq": 2,
    "sender_id": 10002,
    "time": 1710000001,
    "segments": [{"type": "text", "data": {"text": "hi"}}],
    "group": {
        "group_id": 20001,
        "group_name": "Test",
        "member_count": 2,
        "max_member_count": 500,
    },
    "group_member": {
        "user_id": 10002,
        "nickname": "Bob",
        "sex": "male",
        "group_id": 20001,
        "card": "",
        "title": "",
        "level": 1,
        "role": "member",
        "join_time": 1700000000,
        "last_sent_time": 1710000001,
    },
}


class FakeMilkyClient(MilkyClient):
    def __init__(self):
        pass

    def _request(self, endpoint: str, data: dict | None = None) -> dict:
        if endpoint == "get_message":
            return {"message": FRIEND_MESSAGE}
        if endpoint == "get_history_messages":
            return {"messages": [FRIEND_MESSAGE, GROUP_MESSAGE], "next_message_seq": 3}
        raise AssertionError(endpoint)


class FakeAsyncMilkyClient(AsyncMilkyClient):
    def __init__(self):
        pass

    async def _request(self, endpoint: str, data: dict | None = None) -> dict:
        if endpoint == "get_message":
            return {"message": FRIEND_MESSAGE}
        if endpoint == "get_history_messages":
            return {"messages": [FRIEND_MESSAGE, GROUP_MESSAGE], "next_message_seq": 3}
        raise AssertionError(endpoint)


class IncomingMessageParsingTest(unittest.TestCase):
    def test_sync_message_apis_return_models(self) -> None:
        client = FakeMilkyClient()

        message = client.get_message(MessageScene.FRIEND, 10001, 1)
        messages, next_seq = client.get_history_messages(MessageScene.GROUP, 20001)

        self.assertIsInstance(message, FriendMessage)
        self.assertIsInstance(messages[0], FriendMessage)
        self.assertIsInstance(messages[1], GroupMessage)
        self.assertEqual(next_seq, 3)

    def test_async_message_apis_return_models(self) -> None:
        async def run() -> None:
            client = FakeAsyncMilkyClient()

            message = await client.get_message(MessageScene.FRIEND, 10001, 1)
            messages, next_seq = await client.get_history_messages(MessageScene.GROUP, 20001)

            self.assertIsInstance(message, FriendMessage)
            self.assertIsInstance(messages[0], FriendMessage)
            self.assertIsInstance(messages[1], GroupMessage)
            self.assertEqual(next_seq, 3)

        import asyncio

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
