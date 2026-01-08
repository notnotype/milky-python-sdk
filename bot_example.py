"""
使用 MilkyBot 框架的示例
当 bot 被 @ 时回复"你好"
"""

from milky import MilkyBot
from milky.models import MessageEvent

bot = MilkyBot("http://100.94.111.67:3010", "Notnotype114514")


@bot.on_mention()
async def handle_mention(event: MessageEvent):
    """被 @ 时回复"""
    await bot.reply(event, "你好！")


@bot.on_command("help")
async def help_command(event: MessageEvent, args: str):
    """处理 /help 命令"""
    await bot.reply(event, "这是帮助信息", at_sender=False)


@bot.on_message()
async def handle_group_msg(event: MessageEvent):
    """处理群消息"""
    data = event.data
    print(f"收到来自 {data.sender_id} 的消息: {bot._get_text(event)}")


if __name__ == "__main__":
    bot.run()
