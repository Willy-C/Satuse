import discord
from discord.ext import commands


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
