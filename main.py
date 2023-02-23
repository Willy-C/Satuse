from __future__ import annotations

import traceback
from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands

from config import BOT_TOKEN, OWNER_ID, WHITELIST


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents(
            guilds=True,
            # members=True,
            messages=True,
            message_content=True,
        )
        super().__init__(command_prefix='hey server ',
                         intents=intents,
                         description='Hello, I am a bot that helps start the server',
                         allowed_mentions=discord.AllowedMentions.none(),
                         help_command=commands.MinimalHelpCommand(),
                         status=discord.Status.dnd,
                         activity=discord.Activity(type=discord.ActivityType.listening, name="start")
                         )
        self.server_status: bool = False
        self.server_start_time: Optional[datetime] = None

    async def setup_hook(self) -> None:
        extensions = (
            'jishaku',
            'extensions.server',
            'extensions.admin',
        )
        for ext in extensions:
            await self.load_extension(ext)
            print(f'Loaded {ext}')

    async def on_command_error(self, ctx, error):
        ignored = (commands.CommandNotFound, commands.NotOwner)  # Tuple of errors to ignore
        error = getattr(error, 'original', error)

        if isinstance(error, ignored):
            return

        # Unhandled error, so just return the traceback
        tb = traceback.format_exception(type(error), error, error.__traceback__)
        await ctx.send(f'An unexpected error has occurred! My owner has been notified.\n'
                       f'If you really want to know what went wrong:\n'
                       f'||```py\n{tb[-1][:150]}```||')

        e = discord.Embed(title=f'An unhandled error occurred in {ctx.guild} | #{ctx.channel}',
                          description=f'Invocation message: {ctx.message.content}\n'
                                      f'[Jump to message]({ctx.message.jump_url})',
                          color=discord.Color.red())
        e.set_author(name=ctx.author, icon_url=ctx.author.display_avatar.url)

        app_info = await self.application_info()
        owner = app_info.owner
        await owner.send(embed=e)
        fmt = "".join(tb)
        if len(fmt) >= 1980:
            await owner.send(f'Traceback too long. See logs')
        else:
            await owner.send(f'```py\n{fmt}```')

    async def process_commands(self, message: discord.Message):
        if message.author.id not in WHITELIST:
            return

        ctx = await self.get_context(message)
        await self.invoke(ctx)


bot = Bot()

bot.run(BOT_TOKEN)
