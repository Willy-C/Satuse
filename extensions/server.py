from __future__ import annotations

import os
import logging
import asyncio
from subprocess import Popen, PIPE, DETACHED_PROCESS, CREATE_NEW_PROCESS_GROUP
from typing import TYPE_CHECKING

import psutil
import discord
from discord.ext import commands, tasks

from utils.mcrcon import RCONClient
from utils.common import parse_list_resp, cooldown_with_bypass
from config import SERVER_DIR, OWNER_ID, SERVER_IP, RCON_PORT, RCON_PASS

if TYPE_CHECKING:
    from main import Bot
    from utils.context import Context


logging = logging.getLogger(__name__)


class Server(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.server_checker_loop.start()
        self._checker_lock: asyncio.Lock = asyncio.Lock()

    async def cog_unload(self):
        self.server_checker_loop.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        if self.server_checker_loop.current_loop > 1:
            self.server_checker_loop.restart()

    async def wait_then_online(self):
        await asyncio.sleep(60 * 3)
        await self.bot.set_online_status()

    @commands.command(name='start')
    @commands.max_concurrency(1, wait=True)
    async def start_server(self, ctx: Context):
        """Starts the server"""
        async with ctx.typing():
            await self.check_server_status()

        async with self._checker_lock:
            if ctx.author.id != OWNER_ID:
                if 'uwu' not in ctx.prefix:
                    await ctx.reply('To start the server: `uwu pls start`', mention_author=False)
                    return

            if self.bot.server_status:
                dt = self.bot.server_start_time
                await ctx.reply(f'Server is already running! The server was last started at {discord.utils.format_dt(dt)} ({discord.utils.format_dt(dt, "R")})\n'
                                f'If it has been more than a few minutes and the server is still down, please message me!')
                return

            _confirm = 'uwu yes pls'

            def confirm_check(msg: discord.Message):
                if msg.author.id != ctx.author.id or msg.channel.id != ctx.channel.id:
                    return False

                if ctx.author.id == OWNER_ID:
                    return msg.content.lower() in (_confirm, 'confirm', 'cancel')
                else:
                    return msg.content.lower() in (_confirm, 'cancel')

            prompt = await ctx.reply(f'Are you sure you want to start the server? Please type `{_confirm}` within 1 minute to confirm.')

            try:
                answer = await self.bot.wait_for('message', check=confirm_check, timeout=60)
            except asyncio.TimeoutError:
                await ctx.reply('Did not receive a confirmation within 1 minute. Cancelling server start',
                                mention_author=False)
                return
            else:
                if answer.content.lower() == 'cancel':
                    await ctx.reply('Cancelling server start',
                                    mention_author=False)
                    return
            finally:
                try:
                    await prompt.delete()
                except discord.HTTPException:
                    pass

            async with ctx.typing():
                logging.info(f'Starting server... | {ctx.author}')
                oldcwd = os.getcwd()
                os.chdir(SERVER_DIR)

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

            await self.bot.set_online_status()
            logging.info(f'Server successfully started')

    @staticmethod
    def check_server_exe():
        for p in psutil.process_iter(['name']):
            try:
                if p.name() == 'java.exe':
                    if r'Minecraft\FTB' in p.exe():
                        return True
            except psutil.AccessDenied:
                continue
        return False

    async def check_server_status(self):
        async with self._checker_lock:
            logging.debug('Checking server status...')
            _status = self.check_server_exe()
            if _status:
                if self.bot.server_status:
                    return
                logging.info('Server is running, changing status...')
                self.bot.server_status = True
                self.bot.server_start_time = discord.utils.utcnow()
                await self.bot.set_online_status()
            else:
                if not self.bot.server_status:
                    return
                logging.info('Server is not running, changing status...')
                self.bot.server_status = False
                await self.bot.set_offline_status()

    @tasks.loop(minutes=15)
    async def server_checker_loop(self):
        await self.check_server_status()

    @server_checker_loop.before_loop
    async def sleep_before(self):
        async with self._checker_lock:
            await self.bot.wait_until_ready()
            # await asyncio.sleep(5)
            logging.info('Server status checker started')

    @commands.command(hidden=True)
    @commands.is_owner()
    async def update(self, ctx: Context):
        await self.check_server_status()
        await ctx.tick(True)

    @commands.command()
    async def ip(self, ctx: Context):
        try:
            await ctx.author.send(f'The server IP is: `{SERVER_IP}`')
        except discord.Forbidden:
            await ctx.reply('I cannot DM you. Please enable DMs from server members to receive the server IP.')
        else:
            await ctx.reply('I have sent you the server IP via DM.')
            await ctx.tick(True)

    @commands.command(name='uptime')
    async def server_uptime(self, ctx: Context):
        """Check server uptime"""
        if not self.bot.server_status:
            await ctx.reply('The server is currently offline')
            return

        dt = self.bot.server_start_time
        await ctx.reply(f'The server was last started at {discord.utils.format_dt(dt)} ({discord.utils.format_dt(dt, "R")})')

    @commands.command(name='list')
    @commands.max_concurrency(1, wait=True)
    async def list_players(self, ctx: Context):
        """List players online"""
        if not self.bot.server_status:
            await ctx.reply('The server is currently offline')
            return

        async with ctx.typing(), RCONClient('localhost', RCON_PORT, RCON_PASS) as rcon:
            resp = await rcon.send('list')
            current_online = parse_list_resp(resp)
            if not current_online:
                await ctx.reply('Unable to get player list. Please try again later.', mention_author=False)
                await ctx.tick(False)
                return

            if current_online['count'] == '0':
                await ctx.reply('There are currently no players online.', mention_author=False)
            else:
                await ctx.reply(f'There are currently {current_online["count"]} players online:\n'
                                f'{current_online["players"]}', mention_author=False)
            await ctx.tick(True)

    @commands.command(name='stop')
    @commands.dynamic_cooldown(cooldown_with_bypass, type=commands.BucketType.user)
    @commands.max_concurrency(1, wait=True)
    async def stop_server(self, ctx: Context):
        """Stop the server"""
        if not self.bot.server_status:
            await ctx.reply('The server is currently offline')
            return

        async with ctx.typing(), RCONClient('localhost', RCON_PORT, RCON_PASS) as rcon:
            list_resp = await rcon.send('list')
            current_online = parse_list_resp(list_resp)
            if not current_online:
                await ctx.reply('Unable to get player list. Please try again later.', mention_author=False)
                return

            if int(current_online['count']) > 0:
                await ctx.reply(f'There are currently {current_online["count"]} players online.\n'
                                f'Please wait for them to leave before stopping the server.', mention_author=False)
                await ctx.tick(False)
                return

            if not await ctx.confirm_prompt('Shutdown server?'):
                await ctx.tick(False)
                return

            await rcon.send('stop')

        logging.info(f'Stopping server... | {ctx.author}')
        await ctx.reply('Shutting down server...', mention_author=False)
        await ctx.tick(True)
        await self.check_server_status()


async def setup(bot: Bot):
    if not hasattr(bot, 'server_status'):
        bot.server_status = False
    await bot.add_cog(Server(bot))
