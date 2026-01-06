# Milky Python SDK

[![PyPI](https://img.shields.io/pypi/v/milky-python-sdk)](https://pypi.org/project/milky-python-sdk/)
[![License](https://img.shields.io/github/license/notnotype/milky-python-sdk)](LICENSE)

Python SDK for the Milky Protocol, designed for building bots and integrations with ease. It supports both synchronous and asynchronous modes and features a decorator-based event system.

## Installation

```bash
pip install milky-python-sdk
```

## Quick Start

### Using MilkyBot Framework (Recommended)

The `MilkyBot` class provides a high-level interface for creating bots.

```python
from milky import MilkyBot

# Initialize bot with API endpoint and token
bot = MilkyBot("http://localhost:3010", "your_token")

@bot.on_mention()
async def handle_mention(event):
    await bot.reply(event, "Hello!")

@bot.on_command("echo")
async def echo_command(event, args):
    if args:
        await bot.reply(event, args, at_sender=False)

if __name__ == "__main__":
    bot.run()
```

### Using Async Client

For more control or integration into existing async applications:

```python
import asyncio
from milky import AsyncMilkyClient

async def main():
    async with AsyncMilkyClient("http://localhost:3010", "your_token") as client:
        info = await client.get_login_info()
        print(f"Logged in as: {info.nickname}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Features

- **Event System**: Decorators for handling specific events like mentions, commands, and messages.
- **Message Segments**: Rich message support including text, images, mentions, and more.
- **Async & Sync**: Flexible client options to suit your project needs.
- **Type Hints**: Fully typed for better development experience.

## Documentation

For more detailed usage, including segment types and API reference, please refer to the source code or `milky.md` (if available in the repo).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
