import discord
from discord.ext import commands

from utils.common import ConfirmView


class Context(commands.Context):

    async def tick(self, value=True, reaction=True):
        emojis = {True:  '<:greenTick:602811779835494410>',
                  False: '<:redTick:602811779474522113>',
                  None:  '<:greyTick:602811779810328596>'}
        emoji = emojis.get(value, '<:redTick:602811779474522113>')
        if reaction:
            try:
                await self.message.add_reaction(emoji)
            except discord.HTTPException:
                pass
        else:
            return emoji

    async def confirm_prompt(self, msg, *, timeout=60, delete_after=True, **kwargs):
        """
        Asks author for confirmation
        Returns True if confirmed, False if cancelled, None if timed out
        """
        view = ConfirmView(context=self, timeout=timeout, author=self.author, delete_after=delete_after)
        view.message = await self.send(msg, view=view, **kwargs)
        await view.wait()
        return view.choice
