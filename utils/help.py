from typing import Any, List, Mapping, Optional

import discord
from discord.ext import commands
from discord.ext.commands import Cog, Command


class MinimalHelp(commands.MinimalHelpCommand):
    async def send_bot_help(self, mapping: Mapping[Optional[Cog], List[Command[Any, ..., Any]]], /) -> None:
        if await self.context.bot.is_owner(self.context.author):
            return await super().send_bot_help(mapping)
        else:
            cog = self.context.bot.get_cog('Server')
            if cog is None:
                return await super().send_bot_help(mapping)
            else:
                return await self.send_cog_help(cog)

