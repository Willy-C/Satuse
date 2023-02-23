from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from main import Bot


class Admin(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
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


async def setup(bot: Bot):
    await bot.add_cog(Admin(bot))
