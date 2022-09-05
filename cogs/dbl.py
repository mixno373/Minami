import dbl
import discord
from discord.ext import commands

import asyncio
import logging

from config.settings import settings



class DiscordBotsOrgAPI(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.token = settings["dbl_token"]
        self.dblpy = dbl.DBLClient(self.bot, self.token)
        self.updating = self.bot.loop.create_task(self.update_stats())

    async def update_stats(self):
        while not self.bot.is_closed():
            try:
                await self.dblpy.post_guild_count()
            except Exception as e:
                pass
            await asyncio.sleep(1800)

def setup(bot):
    bot.add_cog(DiscordBotsOrgAPI(bot))
