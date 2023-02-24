from __future__ import annotations

import os
import asyncio
from subprocess import Popen, PIPE, DETACHED_PROCESS, CREATE_NEW_PROCESS_GROUP
from typing import TYPE_CHECKING

import psutil
import discord
from discord.ext import commands, tasks

from config import SERVER_CWD, OWNER_ID

if TYPE_CHECKING:
    from main import Bot


class Server(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.check_server_status.start()

    async def cog_unload(self):
        self.check_server_status.cancel()

    async def wait_then_online(self):
        await asyncio.sleep(60 * 3)
        await self.bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.playing, name='OceanBlock v1.15.1'),
            status=discord.Status.online)

    @commands.command(name='start')
    @commands.max_concurrency(1, wait=True)
    async def start_server(self, ctx: commands.Context):
        """Starts the server"""
        if self.bot.server_status:
            dt = self.bot.server_start_time
            await ctx.reply(f'The server was last started at {discord.utils.format_dt(dt)} ({discord.utils.format_dt(dt, "R")})\n'
                            f'If it has been more than a few minutes and the server is still down, please message me!')
            return

        _confirm = 'uwu yes pls'

        def confirm_check(msg: discord.Message):
            if msg.author.id != ctx.author.id or msg.channel.id != ctx.channel.id:
                return False

            if ctx.author.id == OWNER_ID:
                return msg.content.lower() in (_confirm, 'confirm')
            else:
                return msg.content.lower() == _confirm

        prompt = await ctx.reply(f'Are you sure you want to start the server? Please type `{_confirm}` within 1 minute to confirm.')

        try:
            await self.bot.wait_for('message', check=confirm_check, timeout=60)
        except asyncio.TimeoutError:
            await ctx.reply('Did not receive a confirmation within 1 minute. Cancelling server start',
                            mention_author=False)
            return

        finally:
            try:
                await prompt.delete()
            except discord.HTTPException:
                pass

        async with ctx.typing():
            oldcwd = os.getcwd()
            os.chdir(SERVER_CWD)

            CMD_ARGS = ['start.bat']

            Popen(
                CMD_ARGS,
                stdin=PIPE,
                stdout=PIPE,
                stderr=PIPE,
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
            )

            os.chdir(oldcwd)

            self.bot.server_status = True
            self.bot.server_start_time = discord.utils.utcnow()

        await ctx.reply(f'Server is starting now... Please allow a few minutes to fully load all mods.')
        await self.bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.playing, name='OceanBlock v1.15.1'),
            status=discord.Status.idle)

        self.bot.loop.create_task(self.wait_then_online())

    @staticmethod
    def check_server_running():
        try:
            for p in psutil.process_iter(['name']):
                if p.info['name'] == 'java.exe':
                    if r'Minecraft\FTB' in p.exe():
                        return True
            return False
        except psutil.AccessDenied:
            return False

    @tasks.loop(minutes=15)
    async def check_server_status(self):
        _status = self.check_server_running()
        if _status:
            if self.bot.server_status:
                return
            self.bot.server_status = True
            self.bot.server_start_time = discord.utils.utcnow()
            await self.bot.change_presence(
                activity=discord.Activity(type=discord.ActivityType.playing, name='OceanBlock v1.15.1'),
                status=discord.Status.online)
        else:
            if not self.bot.server_status:
                return
            self.bot.server_status = False
            await self.bot.change_presence(
                activity=discord.Activity(type=discord.ActivityType.listening, name="start"),
                status=discord.Status.dnd)

    @check_server_status.before_loop
    async def sleep_before(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(5)


async def setup(bot: Bot):
    if not hasattr(bot, 'server_status'):
        bot.server_status = False
    await bot.add_cog(Server(bot))
