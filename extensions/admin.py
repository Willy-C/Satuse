from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from config import SERVER_DIR

if TYPE_CHECKING:
    from main import Bot


class Admin(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context):
        if not await self.bot.is_owner(ctx.author):
            raise commands.NotOwner
        return True

    @commands.command()
    async def status(self, ctx: commands.Context, status: bool):
        """Change status of server"""
        if status:
            self.bot.server_status = True
            self.bot.server_start_time = discord.utils.utcnow()
            await self.bot.change_presence(
                activity=discord.Activity(type=discord.ActivityType.playing, name='OceanBlock v1.15.1'),
                status=discord.Status.online)
            await ctx.reply('Server status set to ON')
        else:
            self.bot.server_status = False
            await self.bot.change_presence(
                activity=discord.Activity(type=discord.ActivityType.listening, name="start"),
                status=discord.Status.dnd)
            await ctx.reply('Server status set to OFF')

    @commands.command(name='shutdown')
    async def shutdown_bot(self, ctx: commands.Context):
        await ctx.message.add_reaction('\U0001f620')
        await ctx.bot.close()

    @commands.command(name='logs')
    @commands.is_owner()
    async def logs(self, ctx: commands.Context):
        cmd = self.bot.get_command('jsk cat')
        if cmd is None:
            return await ctx.reply('Command not found', mention_author=False)

        log_file = pathlib.Path(SERVER_DIR) / 'logs' / 'latest.log'
        if not log_file.is_file():
            return await ctx.reply('Log file not found', mention_author=False)

        await ctx.invoke(cmd, str(log_file)) # type: ignore


async def setup(bot: Bot):
    await bot.add_cog(Admin(bot))
