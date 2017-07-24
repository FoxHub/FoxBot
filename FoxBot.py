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

import json
import aiohttp
import asyncio
import discord
from discord.ext import commands
from gtts import gTTS
from html.parser import HTMLParser
import os
from urllib import request

config_data = open('configs/config.json').read()
config = json.loads(config_data)

# TODO: Add dice-rolling, death, random chance of foxes, reddit reading, update documentation

# =========================================================================== #

Client = discord.Client()
bot_prefix = config['bot_prefix']
bot_token = config['bot_token']
server_id = config['server_id']
league_id = config['league_id']
client = commands.Bot(command_prefix=bot_prefix, description="A cute social bot.")

# Initialize these variables globally; they're used often.
server = None
awake = True

# =========================================================================== #

# Helper functions in this section


def get_role(target_name):
    """
    This function lets us easily ping members of a role in Discord.

    :param target_name: A role in the discord server, by its name on the role list.
    :return: A string that allows you to @mention the role by name.
    """
    server_roles = server.roles
    for each in server_roles:
        if each.name == target_name:
            # This is what produces our magic string.
            return each.mention
    return None


def join_channel(ctx):
    """
    This function allows the asynchronous 'connect' and 'cuddle' commands
    to be more readable.

    :param ctx: The current message context passed into the async command.
    :return: The voice channel object to join.
    """
    author = ctx.message.author
    voice_channel = author.voice_channel
    if voice_channel is None:
        return
    return voice_channel


def is_num(arg):
    """
    This function determines whether the given argument is a number.
    """
    try:
        float(arg)
        return True
    except ValueError:
        return False


def make_border(length):
    """
    A function that creates a line of dashes length long.

    :param length: The length of the longest line in a block of text.
    :return: None
    """
    str = ''
    for num in range(length):
        str += '-'
    print(str)


class FoxParser(HTMLParser):
    """
    A helper class that overrides the base Python HTML parser.

    This is used to screap StupidFox.net.
    """
    foxurl = None
    def handle_starttag(self, tag, attrs):
        # Only parse the 'anchor' tag.
        if tag == "a":
            # Check the list of defined attributes.
            for name, value in attrs:
                if name == "title" and value == "Random Comic":
                    # This will pull the link out of stupidfox.net
                    self.foxurl = (attrs[0][1])
                    return

def parse_fox(html):
    """
    This function obtains a random StupidFox page from raw HTML.

    :param html: Raw StupidFox page html.
    :return: A link to a random StupidFox page.
    """
    parser = FoxParser()
    parser.feed(html)
    return parser.foxurl


# =========================================================================== #


@client.check
def is_awake(func):
    return awake


# =========================================================================== #


@client.event
async def on_ready():
    """
    The output of this function signals that Fox-Bot is up and running.
    """
    global server
    server = client.get_server(server_id)
    msg1 = "Yip! FoxBot is running.\n"
    msg2 = "We are on the server " + server.name + "!"
    make_border(len(msg2))
    print(msg1 + msg2)
    make_border(len(msg2))
    await client.change_presence(game=discord.Game(name='with Humans'))


# =========================================================================== #
# Follows are the commands the bot accepts.


@client.command(pass_context = True)
async def cat(ctx):
    """
    The Random Cat

    Fox-Bot looks up and embeds a random cat from random.cat.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get('http://random.cat/meow') as r:
            if (r.status == 200):
                js = await r.json()
                em = discord.Embed(title='Random cat! :fox:',
                                   color=728077,
                                   url=js['file'])
                em.set_image(url=js['file'])
                em.set_footer(text="Courtesy of Random.cat",
                              icon_url="http://random.cat/random.cat-logo.png")
                await client.say('<'+js['file']+'>', embed=em)


@client.command(pass_context = True)
async def changeprefix(ctx):
    """
    Change Prefix

    Fox-Bot takes the argument, and begins responding to it as a bot prefix.

    Usage: {prefix}changeprefix {new-prefix}
    """
    arg = ctx.message.content.split()
    try:
        bot_prefix = arg[1]
        client.command_prefix = bot_prefix
        await client.say("I've changed my bot prefix to: **" + client.command_prefix + "**")
    except IndexError:
        await client.say("*Fox-Bot looks at you confused. You must provide an argument!*")


@client.command(pass_context=True)
async def connect(ctx):
    """
    Connect to Voice Chat

    Fox-Bot comes to connect to your current voice channel.
    If she is already connected, she will remain where she is.
    To make her follow you, see Cuddle.
    """
    voice_channel = join_channel(ctx)
    vc = await client.join_voice_channel(voice_channel)


@client.command(pass_context=True)
async def cuddle(ctx):
    """
    Cuddle

    Fox-Bot says something cute, and follows you to your current
    voice channel.
    """
    # A repeat of the connect command, since Commands aren't callable.
    voice_channel = join_channel(ctx)
    if client.is_voice_connected(ctx.message.server):
        voice_client = client.voice_client_in(server)
        if voice_client.channel != voice_channel:
            await client.say("*Fox-bot chases " + ctx.message.author.name + "!*")
            await voice_client.move_to(voice_channel)
            return
        else:
            await client.say("*Fox-Bot is asleep in your lap. Be careful only to wake her with !disconnect.*")
            return
    if voice_channel is None:
        await client.say("*Fox-Bot can't find you!*")
        return
    vc = await client.join_voice_channel(voice_channel)
    await client.say("*Fox-Bot rubs against your leg and yips. :revolving_hearts:*")


@client.command(pass_context = True)
async def disconnect(ctx):
    """
    Disconnect from Voice Channel

    Fox-Bot disconnects from voice chat, if connected.
    """
    for x in client.voice_clients:
        if(x.server == ctx.message.server):
            return await x.disconnect()


@client.command(pass_context = True)
async def dog(ctx):
    """
    Random Dog

    Fox-Bot looks up a random dog and embeds it in Discord.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get('http://random.dog/woof.json') as r:
            if (r.status == 200):
                js = await r.json()
                em = discord.Embed(title='Random dog! :fox:',
                                   color=728077,
                                   url='http://random.dog')
                em.set_image(url=js['url'])
                em.set_footer(text="Courtesy of random.dog. © Aden Florian",
                              icon_url="https://pbs.twimg.com/media/Cbg6oKqUkAI2PAB.jpg")
                await client.say('<'+js['url']+'>', embed=em)


@client.command(pass_context = True)
async def info(ctx):
    """
    FoxBot Info

    FoxBot tells you about herself.
    """
    desc = "Current command prefix: " + client.command_prefix
    embed = discord.Embed(title="Welcome to Fox-bot.",
                          url="https://github.com/FoxHub/FoxBot",
                          description=desc,
                          color=0xFFFFF)
    embed.set_author(name="Sage Callon",
                     url="https://github.com/FoxHub/",
                     icon_url="https://avatars1.githubusercontent.com/u/5873865?v=4&s=40")
    embed.set_footer(text="Licensed under the MIT license.",
                     icon_url="https://ucarecdn.com/71946d9b-adad-4d6e-9130-0a480ddcc553/")
    embed.add_field(name="Developed in Python.",
                    value="An Open-Source bot in Python 3.6.2.")
    embed.set_image(url="http://favim.com/orig/201106/02/animal-beauty-cute-fox-snow-Favim.com-63975.jpg")
    return await client.say("<https://github.com/FoxHub/FoxBot>",embed=embed)


@client.command(pass_context=True)
async def lol(ctx):
    """
    The LoL Signal

    FoxBot pings all members of the League of Legends affiliated role.
    """
    if ctx.message.server != server:
        await client.say("*This command must be used from inside a server!*")
        return
    if (ctx.message.channel != server.get_channel(league_id)):
        await client.say("Yip! This is the wrong channel for that! You're on " + ctx.message.channel.name + ".")
        return None
    msg = " :lemon: it's time for League of Legends! Yip yip!"
    role = get_role("Lemon")
    await client.say(role + msg)


@client.command(pass_context=True)
async def ping(ctx):
    """
    Ping

    Fox-Bot replies with 'Pong!' and then deletes the message.
    """
    await client.say("Pong! *Message disappearing in 10 seconds...*", delete_after=10)


@client.command(pass_context=True)
async def sleep(ctx):
    """
    Sleep for a few minutes.

    Fox-Bot shuts down with a farewell message.
    She'll sleep for the number of minutes specified.

    Usage: {prefix}sleep {minutes}
    """
    # TODO: Give some sort of indicator that Fox-Bot is sleeping.
    # TODO: Catch the exception thrown by sleep check.
    arg = ctx.message.content.replace(ctx.message.content.split()[0] + " ", '')
    if is_num(arg):
        minutes = float(arg)*60 # 60 seconds per minute
        await client.say("*Fox-Bot curls up in a ball, and takes a nap for " + arg + " minutes.* :zzz:")
        #client.logout()
        global awake
        awake = False
        await asyncio.sleep(minutes)
        awake = True
        #client.login()
        await client.say("*Fox-Bot wakes up. :sunny:*")
    else:
        await client.say("*Argument must be a number, yip!* :fire:")


@client.command(pass_context=True)
async def speak(ctx):
    """
    Speak

    Fox-Bot translates your words into speech and speaks in the current
    voice channel.

    Usage: {prefix}speak {words-to-speak}
    """
    # We need to make sure Fox-Bot is actually in a voice channel.
    if ctx.message.server != server:
        await client.say("*This command must be used from inside a server!*")
        return
    if client.is_voice_connected(ctx.message.server):
        voice_client = client.voice_client_in(server)
    else:
        await client.say("*Fox-Bot isn't in a voice channel!*")
        return
    # Parse out the first word from the message context so that we have the rest of the line.
    arg = ctx.message.content.replace(ctx.message.content.split()[0] + " ", '')
    # Create the audio file from our argument
    audiofile = "./tts.mp3"
    tts = gTTS(text=arg, lang='en', slow=False)
    tts.save(audiofile)
    # And then play it.
    player = voice_client.create_ffmpeg_player(audiofile)
    player.volume = 0.7
    player.start()
    while player.is_playing():
        # Do nothing
        await asyncio.sleep(0.2)
        # continue
    os.unlink(audiofile)


@client.command(pass_context = True)
async def stupidfox(ctx):
    """
    StupidFox

    Fox-Bot looks up a random StupidFox and embeds it.
    """
    html = request.urlopen("http://stupidfox.net/168-home-sweet-home")
    foxurl = parse_fox(str(html.read()))
    if foxurl is not None:
        # foxurl will preserve the original url of the random web page.
        imageurl = foxurl.split("/")[3]
        foxnum = imageurl.split("-")[0]
        try:
            # Entries older than 145 on the website are in .jpg format.
            if int(foxnum) > 145:
                extension = ".png"
            # And number 24 randomly truncates its name.
            elif int(foxnum) == 24:
                imageurl = "24"
                extension = ".jpg"
            else:
                extension = ".jpg"
        except ValueError:
            extension = ".jpg"
        imageurl = "http://stupidfox.net/art/" + imageurl + extension
        # For some reason, many of the page links on the website have duplicate dashes...
        imageurl = imageurl.replace("--", "-")
        em = discord.Embed(title='Random stupidfox! :fox:',
                           color=728077,
                           url=foxurl)
        em.set_image(url=imageurl)
        em.set_footer(text="Courtesy of Stupidfox.net. © Emily Chan",
                         icon_url="https://scontent.fsnc1-1.fna.fbcdn.net/v/t1.0-9/14225402_10154540054369791_5558995243858647155_n.png?oh=2ea815515d0d1c7c3e4bbc561ff22f0e&oe=5A01CAD1")
        await client.say("<" + imageurl + ">", embed=em)
    else:
        # StupidFox is likely down if this command fails.
        await client.say("Yip! I can't find a URL! I'm a stupid fox. :fox:")


# =========================================================================== #
# The final command here starts the bot. Nice and simple!


client.run(bot_token)