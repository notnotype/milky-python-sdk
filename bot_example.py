"""
使用 MilkyBot 框架的示例
当 bot 被 @ 时回复"你好"
"""

from milky import MilkyBot

bot = MilkyBot("http://100.94.111.67:3010", "Notnotype114514")


@bot.on_mention()
async def handle_mention(event):
    """被 @ 时回复"""
    await bot.reply(event, "你好！")


@bot.on_command("help")
async def help_command(event, args):
    """处理 /help 命令"""
    await bot.reply(event, "这是帮助信息", at_sender=False)


@bot.on_command("echo")
async def echo_command(event, args):
    """处理 /echo 命令"""
    if args:
        await bot.reply(event, args, at_sender=False)


if __name__ == "__main__":
    bot.run()
