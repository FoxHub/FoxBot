# Copyright 2017 Sage Callon

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import asyncio
from datetime import datetime
import json
import os

from html.parser import HTMLParser
from urllib import request
import aiohttp
import discord
from discord import app_commands, FFmpegPCMAudio
from discord.ext import commands

from PollyHelpers import tts
from StupidFoxHelpers import embed_stupidfox

config_data = open('configs/config.json').read()
config = json.loads(config_data)

# =========================================================================== #

guild_to_voice_client = dict()

bot_intents = discord.Intents.all()
bot_prefix = config['bot_prefix']
bot_token = config['bot_token']
fox_chance = float(config['fox_chance'][:-1])
league_id = config['league_id']
whitelist = config['whitelist']
exclusive = True

client = commands.Bot(command_prefix=bot_prefix, description="A cute social bot.", intents=bot_intents)

AUDIOFILE = "./tts.wav"
CAT_DESCRIPTION = "Get a random cat!"
CONNECT_DESCRIPTION = "Connect Fox-Bot to your voice channel, or move Fox-Bot to your voice channel."
CUDDLE_DESCRIPTION = "Fox-Bot follows you into a voice channel. Cuter than connect. Otherwise the same."
DISCONNECT_DESCRIPTION = "Disconnect Fox-Bot from a voice channel."
DOG_DESCRIPTION = "Get a random dog!"
INFO_DESCRIPTION = "Display bot creator information."
SLEEP_DESCRIPTION = "Shut down Fox-Bot."
SPEAK_DESCRIPTION = "Have Fox-Bot talk in a voice channel. Uses Polly TTS."
STUPIDFOX_DESCRIPTION = "Get a random page of the stupidfox comic series!"
TOGGLE_EXCLUSIVE_DESCRIPTION = "Set Fox-bot's more privileged commands to use permissions checks."

MESSAGE_TEXT = "The message for Fox-Bot to speak."

# =========================================================================== #


@client.event
async def on_ready():
    """
    The output of this function signals that Fox-Bot is up and running.
    """
    await client.change_presence(activity=discord.Game(name='Pathfinder'))
    msg0 = "Syncing commands...\n"
    try:
        synced = await client.tree.sync()
        msg1 = "Fox-Bot is running as {}.\n".format(client.user.name)
        msg2 = "Our id is {}. Synced {} command(s).\n".format(client.user.id, len(synced))
        msg3 = "Invite link: https://discordapp.com/oauth2/authorize?client_id={}&scope=bot&scope=applications.commands%20bot".format(client.user.id)
        _make_border(len(msg3))
        print(msg0 + msg1 + msg2 + msg3)
        _make_border(len(msg3))
    except Exception as e:
        print(e)


def _make_border(length):
    """
    A function that creates a line of dashes length long.

    :param length: The length of the longest line in a block of text.
    :return: None
    """
    str = ''
    for num in range(length):
        str += '-'
    print(str)


def _context_to_voice_channel(ctx):
    return ctx.user.voice.channel if ctx.user.voice else None


async def _perms_check(ctx: discord.Interaction):
    """
    A function that checks if a Discord user is in Fox-Bot's whitelist.

    :param ctx: The context of the message.
    :return: true or false
    """
    if str(ctx.user) in whitelist:
        return True
    else:
        await ctx.response.send(
            "*You're not permitted to do this command. Exclusive mode is on!*",
            ephemeral=True
        )
        return False


async def _get_or_create_voice_client(ctx) -> tuple[discord.VoiceClient, bool]:
    print("Getting voice client...")
    global guild_to_voice_client
    joined = False
    if ctx.guild.id in guild_to_voice_client:
        print("Already connected to voice in this server. Returning client.")
        voice_client, last_used = guild_to_voice_client[ctx.guild.id]
    else:
        print("Not in voice on this server. Connecting to server.")
        voice_channel = _context_to_voice_channel(ctx)
        if voice_channel is None:
            voice_client = None
        else:
            voice_client = await voice_channel.connect()
            print(f'Connected to channel: [{ctx.guild.id}: {voice_client},{datetime.utcnow()}]')
            guild_to_voice_client[ctx.guild.id] = (voice_client, datetime.utcnow())
            joined = True
    return voice_client, joined


async def _connect(interaction: discord.Interaction, cute=False):
    global exclusive
    if exclusive:
        if not await _perms_check(interaction):
            return

    voice_client, joined = await _get_or_create_voice_client(interaction)
    if voice_client is None:
        if cute:
            await interaction.response.send_message(
                "*Fox-Bot can't find you!*",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                "You're not in a voice channel. Join a voice channel to invite Fox-Bot!",
                ephemeral=True,
            )
    elif interaction.user.voice and voice_client.channel.id != interaction.user.voice.channel.id:
        print("User in a different channel. Connecting...")
        old_channel_name = voice_client.channel.name
        await voice_client.disconnect()
        voice_client = await interaction.user.voice.channel.connect()
        new_channel_name = voice_client.channel.name
        print(f'Connected to: {new_channel_name}.')
        guild_to_voice_client[interaction.guild.id] = (voice_client, datetime.utcnow())
        print(f'Added dict item: [{interaction.guild.id}:{voice_client},{datetime.utcnow()}]')
        if cute:
            await interaction.response.send_message(
                f'*Fox-bot chases {interaction.user.name} from #{old_channel_name} to #{new_channel_name}!*'
            )
        else:
            await interaction.response.send_message(
                f"Switched from #{old_channel_name} to #{new_channel_name}!",
                ephemeral=True
            )
    else:
        guild_to_voice_client[interaction.guild.id] = (voice_client, datetime.utcnow())
        if cute:
            await interaction.response.send_message("*Fox-Bot rubs against your leg and yips. :revolving_hearts:*")
        else:
            await interaction.response.send_message("Connected to voice channel!", ephemeral=True)


# =========================================================================== #

@client.tree.command(name="cat", description=CAT_DESCRIPTION)
async def cat(interaction: discord.Interaction):
    """
    The Random Cat

    Fox-Bot looks up and embeds a random cat from random.cat.
    """
    await interaction.response.send_message(
        "Random.cat has been taken down. Unfortunately, this function is deprecated. :fox:"
    )


@client.tree.command(name="connect", description=CONNECT_DESCRIPTION)
async def connect(interaction: discord.Interaction):
    """
    Connect to Voice Chat

    Fox-Bot comes to connect to your current voice channel.

    If exclusive mode is on, you must be on Fox-Bot's whitelist
    to use this command.
    """
    await _connect(interaction)


@client.tree.command(name="cuddle", description=CUDDLE_DESCRIPTION)
async def cuddle(interaction: discord.Interaction):
    """
    Cuddle

    Fox-Bot says something cute, and follows you to your current
    voice channel.
    """
    await _connect(interaction, cute=True)


@client.tree.command(name="disconnect", description=DISCONNECT_DESCRIPTION)
async def disconnect(interaction: discord.Interaction):
    """
    Disconnect from Voice Channel

    Fox-Bot disconnects from voice chat, if connected.

    If exclusive mode is on, you must be on Fox-Bot's whitelist
    to use this command.
    """
    global guild_to_voice_client
    if interaction.guild.id in guild_to_voice_client:
        voice_client, _ = guild_to_voice_client.pop(interaction.guild.id)
        await voice_client.disconnect()
        await interaction.response.send_message("Disconnected from voice channel.")
    else:
        await interaction.response.send_message(
            "Bot is not connected to a voice channel. Nothing to disconnect.", ephemeral=True
        )


@client.tree.command(name="dog", description=DOG_DESCRIPTION)
async def dog(interaction: discord.Interaction):
    async with aiohttp.ClientSession() as session:
        async with session.get('http://random.dog/woof.json') as r:
            if r.status == 200:
                js = await r.json()
                em = discord.Embed(title='Random dog! :fox:',
                                   color=728077,
                                   url='http://random.dog')
                em.set_image(url=js['url'])
                em.set_footer(text="Courtesy of random.dog. © Aden Florian",
                              icon_url="https://pbs.twimg.com/media/Cbg6oKqUkAI2PAB.jpg")
                await interaction.response.send_message('<'+js['url']+'>', embed=em)


@client.tree.command(name="info", description=INFO_DESCRIPTION)
async def info(interaction: discord.Interaction):
    embed = discord.Embed(title="Welcome to Fox-bot.",
                          url="https://github.com/FoxHub/FoxBot",
                          description="Now integrated with slash commands!",
                          color=0xFFFFF)
    embed.set_author(name="Sage Callon",
                     url="https://github.com/FoxHub/",
                     icon_url="https://avatars1.githubusercontent.com/u/5873865?v=4&s=40")
    embed.set_footer(text="Licensed under the MIT license.",
                     icon_url="https://ucarecdn.com/71946d9b-adad-4d6e-9130-0a480ddcc553/")
    embed.add_field(name="Developed in Python.",
                    value="An Open-Source bot in Python 3.6.2.")
    embed.set_image(url="https://favim.com/orig/201106/02/animal-beauty-cute-fox-snow-Favim.com-63975.jpg")
    await interaction.response.send_message(embed=embed)


@client.tree.command(name="sleep", description=SLEEP_DESCRIPTION)
async def sleep(interaction: discord.Interaction):
    """
    Shut down Fox-Bot.

    Fox-bot will shut down with a farewell message.
    WARNING: Using this command takes Fox-Bot offline until restarted.
    """
    global exclusive
    if exclusive:
        if not await _perms_check(interaction):
            return
    await interaction.response.send_message("*Fox-Bot curls up, and goes into a deep slumber.* :zzz:")
    # Closes the bot.
    loop = client.loop
    await client.close()
    loop.stop()
    pending = asyncio.Task.all_tasks()
    loop.run_until_complete(asyncio.gather(*pending))
    raise SystemExit


@client.tree.command(name="speak", description=SPEAK_DESCRIPTION)
@app_commands.describe(message=MESSAGE_TEXT)
async def speak(interaction: discord.Interaction, message: str):
    """
    Speak

    Fox-Bot translates your words into speech and speaks in the current
    voice channel. Only permitted users may use this command if exclusive
    mode is on.

    Usage: {prefix}speak {words-to-speak}
    """
    global exclusive
    if exclusive:
        if not await _perms_check(interaction):
            return
    voice_client, _ = await _get_or_create_voice_client(interaction)
    if voice_client:
        global guild_to_voice_client
        guild_to_voice_client[interaction.guild.id] = (voice_client, datetime.utcnow())
        tts(message, AUDIOFILE)
        source = FFmpegPCMAudio(AUDIOFILE, executable='ffmpeg')
        voice_client.play(source, after=None)
        while voice_client.is_playing():
            await asyncio.sleep(0.2)
        os.unlink(AUDIOFILE)
        await interaction.response.send_message("Got your message!", delete_after=5.0, ephemeral=True)
    else:
        await interaction.response.send_message(
            "*Fox-Bot isn't in a voice channel!*",
            ephemeral=True,
            delete_after=5.0
        )
        return


@client.tree.command(name="stupidfox", description=STUPIDFOX_DESCRIPTION)
async def stupidfox(interaction: discord.Interaction):
    """
    StupidFox

    Fox-Bot looks up a random StupidFox and embeds it.
    """
    await embed_stupidfox(interaction)


@client.tree.command(name="toggle_exclusive", description=TOGGLE_EXCLUSIVE_DESCRIPTION)
async def toggle_exclusive(interaction: discord.Interaction):
    """
    Toggle Permissions checking

    After entering exclusive mode, FoxBot will check permissions
    before executing some of her more 'abusable' commands.

    This is only usable by members on FoxBot's whitelist.
    """
    if await _perms_check(interaction):
        global exclusive
        exclusive = not exclusive
        await interaction.response.send_message(f'*Exclusive mode toggled to {exclusive}.*')

# =========================================================================== #
# The final command here starts the bot.

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(client.start(bot_token))
    except KeyboardInterrupt:
        loop.run_until_complete(client.close())
    finally:
        loop.close()
