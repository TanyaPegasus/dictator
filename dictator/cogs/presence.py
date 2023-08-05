import discord
from discord.ext import commands, tasks
from itertools import cycle


class Presence(commands.Cog):
    def __init__(self, dictator: commands.Bot) -> None:
        self.dictator = dictator

        self.status = cycle(
            [
                "Dictatorship",
                "-help",
                "Bullying Colin",
                "Guarding Newport",
                "Praising Sam",
                "Baking the pies",
                "Cheesing Uno",
                "Hidei ho ho ho",
                "Celebrating Four Years",
                "Munching Berries",
            ]
        )

    @commands.Cog.listener()
    async def on_ready(self):
        self.change_status.start()

    @tasks.loop(seconds=10)
    async def change_status(self):
        await self.dictator.change_presence(activity=discord.Game(next(self.status)))


async def setup(dictator: commands.Bot) -> None:
    await dictator.add_cog(Presence(dictator))
