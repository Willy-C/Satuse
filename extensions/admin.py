from __future__ import annotations

import logging
import pathlib
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from config import SERVER_DIR, WHITELIST

if TYPE_CHECKING:
    from main import Bot
    from utils.context import Context


logging = logging.getLogger(__name__)


class Admin(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_check(self, ctx: Context):
        if not await self.bot.is_owner(ctx.author):
            raise commands.NotOwner
        return True

    @commands.command()
    async def status(self, ctx: Context, status: bool):
        """Change status of server"""
        if status:
            self.bot.server_status = True
            self.bot.server_start_time = discord.utils.utcnow()
            await self.bot.set_online_status()
            await ctx.reply('Server status set to ON')
        else:
            self.bot.server_status = False
            await self.bot.set_offline_status()
            await ctx.reply('Server status set to OFF')

    @commands.command(name='shutdown')
    async def shutdown_bot(self, ctx: Context):
        if not await ctx.confirm_prompt('Shutdown?'):
            return
        await ctx.message.add_reaction('\U0001f620')
        await ctx.bot.close()

    @commands.command(name='logs')
    async def logs(self, ctx: Context):
        cmd = self.bot.get_command('jsk cat')
        if cmd is None:
            return await ctx.reply('Command not found', mention_author=False)

        log_file = pathlib.Path(SERVER_DIR) / 'logs' / 'latest.log'
        if not log_file.is_file():
            return await ctx.reply('Log file not found', mention_author=False)

        await ctx.invoke(cmd, str(log_file)) # type: ignore

    @commands.command(name='message')
    async def dm_user(self, ctx: Context, user: discord.User, *, message: str):
        if not await ctx.confirm_prompt(message):
            return
        await user.send(message)
        await ctx.tick(True)

    async def do_broadcast(self, message, **kwargs):
        success = []
        failed = []
        not_found = []
        import asyncio
        for user_id in WHITELIST:
            try:
                user = await self.bot.fetch_user(user_id)
            except discord.NotFound:
                logging.info(f'User {user_id} not found')
                not_found.append(user_id)
            except discord.HTTPException as e:
                logging.error(f'Failed to fetch user {user_id} | {e}')
                failed.append(user_id)
            else:
                await asyncio.sleep(60)
                try:
                    await user.send(message, **kwargs)
                except discord.HTTPException as e:
                    logging.error(f'Failed to send broadcast to {user} ({user_id}) | {e}')
                    failed.append(user)
                else:
                    logging.info(f'Sent broadcast to {user} ({user_id})')
                    success.append(user)
        return success, failed, not_found


    @commands.command()
    async def broadcast(self, ctx: Context, *, message: str):
        """Broadcast a message to all users"""
        if not await ctx.confirm_prompt(message):
            return
        await ctx.send('Sending broadcast...')
        success, failed, not_found = await self.do_broadcast(message)
        await ctx.reply(f'Successfully sent to {len(success)} users: {" ".join(map(str, success))}\n'
                        f'Failed to send to {len(failed)} users: {" ".join(map(str, failed))}\n'
                        f'Not found {len(not_found)} users: {" ".join(map(str, not_found))}\n'
                        f'Total: {len(success) + len(failed) + len(not_found)} users',
                        mention_author=False)
        await ctx.tick(True)

    @commands.command(name='silentbroadcast')
    async def broadcast_silent(self, ctx: Context, *, message: str):
        """Broadcast a message to all users but as a silent message"""
        if not await ctx.confirm_prompt(message):
            return
        await ctx.send('Sending broadcast...')
        success, failed, not_found = await self.do_broadcast(message, silent=True)
        await ctx.reply(f'Successfully sent to {len(success)} users: {" ".join(map(str, success))}\n'
                        f'Failed to send to {len(failed)} users: {" ".join(map(str, failed))}\n'
                        f'Not found {len(not_found)} users: {" ".join(map(str, not_found))}\n'
                        f'Total: {len(success) + len(failed) + len(not_found)} users',
                        mention_author=False)
        await ctx.tick(True)


async def setup(bot: Bot):
    await bot.add_cog(Admin(bot))
