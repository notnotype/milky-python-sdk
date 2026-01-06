# Agent Development Guide

This document is intended to assist AI agents and developers in extending and working with the `milky-python-sdk`.

## OpenAPI Specification

The raw OpenAPI specifications for the Milky Protocol server are located in the `openapi/` directory.
- Use these files to understand the underlying API endpoints, request/response structures, and available operations.
- **Path**: `@[openapi]` (e.g., `milky.openapi.json`)

## SDK Structure

- **`milky/`**: The core package.
  - `client.py`: Synchronous client implementation.
  - `async_client.py`: Asynchronous client implementation.
  - `bot.py`: `MilkyBot` framework implementation.
  - `models.py`: Pydantic models for API data structures.

## Development Tips

1. **Type Checking**: The SDK relies heavily on Pydantic models. Always refer to `milky/models.py` when constructing message segments or handling API responses.
2. **Event Handling**: When adding new event handlers, ensure the decorator matches the event type defined in `EventType`.
3. **Async First**: The `MilkyBot` is built on top of `AsyncMilkyClient`. Prefer asynchronous operations for IO-bound tasks.

## Examples

### 1. Complex State Management (Conversation)

```python
from milky import MilkyBot
from collections import defaultdict

bot = MilkyBot("http://localhost:3010", "token")
# Simple in-memory state: user_id -> step
user_state = defaultdict(int)

@bot.on_command("survey")
async def start_survey(event, args):
    """Start a multi-step survey"""
    user_id = event["data"]["sender_id"]
    user_state[user_id] = 1
    await bot.reply(event, "Step 1: What is your favorite color?")

@bot.on_message("friend")
async def handle_survey_response(event):
    user_id = event["data"]["sender_id"]
    state = user_state[user_id]
    
    if state == 1:
        color = bot._get_text(event)
        await bot.reply(event, f"You liked {color}. Step 2: What is your quest?")
        user_state[user_id] = 2
    elif state == 2:
        quest = bot._get_text(event)
        await bot.reply(event, f"Quest: {quest}. Survey complete!")
        del user_state[user_id]
```

### 2. Handling Image Uploads and Sending Images

```python
from milky import MilkyBot
from milky.models import OutgoingImageSegment, OutgoingImageSegmentData

bot = MilkyBot("http://localhost:3010", "token")

@bot.on_message("friend")
async def echo_image(event):
    data = event["data"]
    for seg in data["segments"]:
        if seg["type"] == "image":
            image_id = seg["data"]["image_id"]
            # To send an image back, we can use the file_id if the server supports it, 
            # or upload a new one. Here we demonstrate constructing an outgoing segment.
            # Assuming we have a URL or file path:
            message = [
                OutgoingImageSegment(
                    data=OutgoingImageSegmentData(image_uri="https://example.com/image.png")
                )
            ]
            await bot.client.send_private_message(data["sender_id"], message)
```

### 3. Dynamic API Usage with Error Handling

```python
from milky import AsyncMilkyClient, MilkyHttpError, MilkyError

async def safe_get_info(client: AsyncMilkyClient, group_id: int):
    try:
        group_info = await client.get_group_info(group_id)
        print(f"Group Name: {group_info.group_name}")
    except MilkyHttpError as e:
        if e.status_code == 404:
            print("Group not found")
        else:
            print(f"Network error: {e}")
    except MilkyError as e:
        print(f"API logic error: {e.message}")
```

## Common Tasks

### adding a new API method
Check the `openapi/` spec for the endpoint definition, then implement the corresponding method in both `AsyncMilkyClient` and `MilkyClient`.

### Adding a new Segment type
Define the segment class in `milky/models.py` inheriting from the base segment class, and ensure it's registered in the relevant Pydantic unions.
