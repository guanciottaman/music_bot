import os

import discord
from discord.ext import commands
from discord import app_commands
import ytmusicapi
import yt_dlp


class Music(commands.Cog):
    """Sample cog to contain utility commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queue = []
        self.current_song_index = 0

    def set_current_song_index(self, index:int):
        self.current_song_index = index

    def search_song_url(self, query:str) -> str:
        yt = ytmusicapi.YTMusic()
        videoId = yt.search(query)[0]['videoId']
        return f'https://youtube.com/watch?v={videoId}'

    async def download_song(self, url:str) -> str:
        with yt_dlp.YoutubeDL({'extract_audio': True, 'format': 'bestaudio', 'outtmpl': '%(title)s.mp3'}) as video:
            info_dict: dict | None = video.extract_info(url, download=True)
            if info_dict is None:
                return ""
            video_title = info_dict['title']
            video.download(url)
        return f'{video_title}.mp3'

    @app_commands.command(name='search', description='Search yt link of a song')
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.describe(query='Query to search on YouTube')
    async def search(self, interaction:discord.Interaction, query:str):
        link = self.search_song_url(query)
        await interaction.response.send_message(link, ephemeral=True)

    @app_commands.command(name='download', description='Download a song and send it')
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.describe(query='Query to search on YouTube')
    async def download(self, interaction:discord.Interaction, query:str):
        await interaction.response.defer()
        link = await self.search_song_url(query)
        filename = await self.download_song(link)
        await interaction.followup.send(filename[:-4], file=discord.File(filename))
        os.remove(filename)

    async def play_song(self, filename:str, voice_client: discord.VoiceProtocol):
        voice_client.play(discord.FFmpegPCMAudio(filename), after=lambda song: [self.play_song(self.queue[self.current_song_index+1], voice_client) if len(self.queue) != 1 else print('finished queue'), self.set_current_song_index(self.current_song_index+1)])

    @app_commands.command(name='add_to_queue', description='Adds a song to the queue')
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.describe(query='Query to search on YouTube')
    async def add_to_queue(self, interaction:discord.Interaction, query:str):
        await interaction.response.defer()
        link = self.search_song_url(query)
        filename = await self.download_song(link)
        if not filename:
            await interaction.followup.send(f'The song {query} does not exist on YouTube Music.')
            return
        await interaction.followup.send(f'{filename[:-4]} now playing')
        self.queue.append(filename)
        print(self.queue)
        if not self.bot.voice_clients:
            voice_channel: discord.member.VocalGuildChannel | None = interaction.user.voice.channel
            if voice_channel is None:
                await interaction.channel.send('You must join a voice channel to play the song.')
                self.queue.clear()
                return
            vc = await voice_channel.connect()
        else:
            vc = self.bot.voice_clients[0]
        if self.queue.index(filename) == 0:
            self.set_current_song_index(0)
            await self.play_song(filename, vc)

    @app_commands.command(name='forward_queue', description='Go forward in the queue')
    @app_commands.allowed_installs(guilds=True, users=False)
    async def forward_queue(self, interaction:discord.Interaction):
        if self.queue[self.current_song_index] == self.queue[-1]:
            await interaction.response.send_message('You already reached the end of the queue')
            return
        self.current_song_index += 1
        filename = self.queue[self.current_song_index]
        if not self.bot.voice_clients:
            voice_channel = interaction.user.voice.channel
            vc = await voice_channel.connect()
        else:
            vc = self.bot.voice_clients[0]
            await vc.disconnect()
            voice_channel = interaction.user.voice.channel
            vc = await voice_channel.connect()
        await interaction.response.send_message(f'{filename[:-4]} now playing')
        await self.play_song(filename, vc)

    @app_commands.command(name='back_queue', description='Go back in the queue')
    @app_commands.allowed_installs(guilds=True, users=False)
    async def back_queue(self, interaction:discord.Interaction):
        if self.queue[self.current_song_index] == self.queue[0]:
            await interaction.response.send_message('You are already on the start of the queue')
            return
        self.current_song_index -= 1
        filename = self.queue[self.current_song_index]
        if not self.bot.voice_clients:
            voice_channel = interaction.user.voice.channel
            vc = await voice_channel.connect()
        else:
            vc = self.bot.voice_clients[0]
            await vc.disconnect()
            voice_channel = interaction.user.voice.channel
            vc = await voice_channel.connect()
        await interaction.response.send_message(f'{filename[:-4]} now playing')
        await self.play_song(filename, vc)
        
    @app_commands.command(name='see_queue', description='See the current queue')
    @app_commands.allowed_installs(guilds=True, users=False)
    async def see_queue(self, interaction:discord.Interaction):
        emb = discord.Embed(title='Songs queue', color=discord.Color.blurple(), description='')
        for i, song in enumerate(self.queue):
            emb.description += f'**{i+1}.** {song[:-4]}'
            if i == self.current_song_index:
                emb.description += ' **CURRENT**\n'
            else:
                emb.description += '\n'
        await interaction.response.send_message(embed=emb)


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))