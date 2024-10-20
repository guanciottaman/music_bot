import os

import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv



load_dotenv('.env')

TOKEN = os.environ['TOKEN']


class Bot(commands.Bot):
    """Bot class"""
    def __init__(self):
        """Initializing the class. Put anything you need to do first here"""

        intents = discord.Intents.default()
        intents.members = True

        super().__init__(command_prefix='!', intents=intents) # Setting command prefix and intents

    async def on_ready(self):
        """Event when the bot starts. You can set a welcome message like the one below"""
        print(f'Bot online as {self.user.name}')

    async def setup_hook(self):
        synced = len(await self.tree.sync())
        print(f'Comandi sincronizzati: {synced}')


async def load_extensions(bot: commands.Bot, extensions: list[str]):
    """This function will load the files with our cogs looping through them"""
    for ext in extensions:
        await bot.load_extension(ext)


if __name__ == '__main__':
    bot = Bot() # Initializing the bot instance

    # Extension list, add the cogs files here in dot notation, like the example below
    extensions = [
        'cogs.music'
    ]

    asyncio.run(load_extensions(bot, extensions))

    bot.run(TOKEN)