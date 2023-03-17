import re
import discord
from discord.ext import commands

from typing import Optional, TYPE_CHECKING

from config import OWNER_ID

if TYPE_CHECKING:
    from utils.context import Context

list_re = re.compile(r'There are (?P<count>\d+) of a max of (?P<max>\d+) players online: (?P<players>.*)')


def parse_list_resp(resp: str) -> dict:
    match = list_re.match(resp)
    if match:
        return match.groupdict()
    return {}


def cooldown_with_bypass(ctx: Context) -> Optional[commands.Cooldown]:
    if ctx.author.id == OWNER_ID:
        return None
    return commands.Cooldown(1, 60)


class ConfirmView(discord.ui.View):
    def __init__(self, *, context: Context, timeout: float, author: discord.User, delete_after: bool):
        super().__init__(timeout=timeout)
        self.ctx: Context = context
        self.author: discord.User = author
        self.delete_after: bool = delete_after
        self.message: Optional[discord.Message] = None
        self.choice: Optional[bool] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user is None:
            return False
        if await self.ctx.bot.is_owner(interaction.user):
            return True
        if interaction.user == self.author:
            return True
        else:
            await interaction.response.send_message('You cannot use this', ephemeral=True)
            return False

    async def on_timeout(self) -> None:
        if self.message and self.delete_after:
            await self.message.delete()

    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.choice = True
        await interaction.response.defer()
        if self.delete_after:
            await interaction.delete_original_response()
        self.stop()

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.choice = False
        await interaction.response.defer()
        if self.delete_after:
            await interaction.delete_original_response()
        self.stop()
