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
import discord
from discord.ext import commands
from urllib import request
from html.parser import HTMLParser

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
# Initialize this variable globally; it's used often.
server = client.get_server(server_id)

# =========================================================================== #

# Helper functions
# INPUT: A role in the discord server, by its name in the role list.
# OUTPUT: A string that allows you to @mention the role by name.
def get_role(target_name):
    server_roles = client.get_server(server_id).roles
    for each in server_roles:
        if each.name == target_name:
            # This is what produces our magic string.
            return each.mention
    return None


# A function so that the asynchronous 'connect' and 'cuddle' commands
# can be more readable.
# INPUT: The current message context.
# OUTPUT: The voice channel to join.
def join_channel(ctx):
    author = ctx.message.author
    voice_channel = author.voice_channel
    if voice_channel is None:
        return
    return voice_channel


# INPUT: The length of the longest string in a block.
# OUTPUT: A string of dashes as long as that block.
def make_border(length):
    str = ''
    for num in range(length):
        str += '-'
    print(str)

class FoxParser(HTMLParser):
    # TODO: Document this function.
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
    parser = FoxParser()
    parser.feed(html)
    return parser.foxurl


# =========================================================================== #


# This function runs in the console whenever the bot starts up.
@client.event
async def on_ready():
    server = client.get_server(server_id)
    msg1 = "Yip! FoxBot is running.\n"
    msg2 = "We are on the server " + server.name + "!"
    make_border(len(msg2))
    print(msg1 + msg2)
    make_border(len(msg2))
    await client.change_presence(game=discord.Game(name='with Humans'))


# =========================================================================== #
# Follows are the commands the bot accepts.


# Cat command.
# INPUT: !cat
# OUTPUT: Fox-bot uploads a random cat.
@client.command(pass_context = True)
async def cat(ctx):
    async with aiohttp.ClientSession() as session:
        async with session.get('http://random.cat/meow') as r:
            if (r.status == 200):
                js = await r.json()
                em = discord.Embed(title='Random cat! :fox:',
                                   color=728077,
                                   thumbnail="http://random.cat/random.cat-logo.png",
                                   url=js['file'])
                em.set_image(url=js['file'])
                await client.say('<'+js['file']+'>', embed=em)


# ChangePrefix command.
# INPUT !changeprefix
# OUTPUT: The bot will begin responding to a different bot prefix.
@client.command(pass_context = True)
async def changeprefix(ctx):
    # TODO: Document this function.
    arg = ctx.message.content.split()
    try:
        bot_prefix = arg[1]
        client.command_prefix = bot_prefix
        await client.say("I've changed my bot prefix to: **" + client.command_prefix + "**")
    except IndexError:
        await client.say("*Fox-Bot looks at you confused. You must provide an argument!*")


# Commands command.
# INPUT: !commands
# OUTPUT: Fox-bot tells you all of her commands and their syntax.
@client.command(pass_context = True)
async def commands(ctx):
    # TODO: Keep this command updated.
    preamble = "My current command prefix is '" + client.command_prefix + "', and my commands are:"
    commands = "\n" + bot_prefix + "cat: I give you a random cute cat!" + \
               "\n" + bot_prefix + "commands: You're using me!" + \
               "\n" + bot_prefix + "connect: I connect to your voice channel." + \
               "\n" + bot_prefix + "cuddle: I say something cute, then connect to you." + \
               "\n" + bot_prefix + "disconnect: I leave your voice channel." + \
               "\n" + bot_prefix + "info: Trivia about me!" + \
               "\n" + bot_prefix + "lol: I call Deku's players for a LoL game." + \
               "\n" + bot_prefix + "ping: I say 'Pong!'." + \
               "\n" + bot_prefix + "sleep: Fox-Bot curls up and turns her power switch off." + \
               "\n" + bot_prefix + "stupidfox: A random stupidfox comic!."
    post = "\n\nFor any further questions, directly message the administrator."
    desc = preamble + commands + post
    embed = discord.Embed(title="Fox-bot Guide", description=desc, color=0xFFFFF)
    return await client.say(embed=embed, delete_after=10)


# Connect command.
# INPUT: !connect
# OUTPUT: Fox-bot will follow you to your current voice channel.
@client.command(pass_context=True)
async def connect(ctx):
    voice_channel = join_channel(ctx)
    vc = await client.join_voice_channel(voice_channel)


# Cuddle command.
# INPUT: !cuddle
# OUTPUT: The bot says something cute and joins the author's voice channel.
@client.command(pass_context=True)
async def cuddle(ctx):
    # A repeat of the connect command, since Commands aren't callable.
    voice_channel = join_channel(ctx)
    if client.is_voice_connected(ctx.message.server):
        voice_client = client.voice_client_in(client.get_server(server_id))
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


# Disconnect command.
# INPUT: !disconnect
# OUTPUT: Fox-bot will leave your current voice channel.
@client.command(pass_context = True)
async def disconnect(ctx):
    for x in client.voice_clients:
        if(x.server == ctx.message.server):
            return await x.disconnect()


# Info command.
# INPUT: !info
# OUTPUT: Fox-bot tells you about herself.
@client.command(pass_context = True)
async def info(ctx):
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


# LoL command.
# INPUT: !lol
# OUTPUT: "@Lemon :lemon: it's time for League of Legends! Yip yip!"
@client.command(pass_context=True)
async def lol(ctx):
    if (ctx.message.channel != client.get_server(server_id).get_channel(league_id)):
        await client.say("Yip! This is the wrong channel for that! You're on " + ctx.message.channel.name + ".")
        return None
    msg = " :lemon: it's time for League of Legends! Yip yip!"
    role = get_role("Lemon")
    await client.say(role + msg)


# Ping command.
# INPUT: !ping
# OUTPUT: "Pong!"
@client.command(pass_context=True)
async def ping(ctx):
    await client.say("Pong! *Message disappearing in 10 seconds...*", delete_after=10)


# Sleep command
# INPUT: !sleep
# OUTPUT: FoxBot terminates.
@client.command(pass_context=True)
async def sleep(ctx):
    await client.say("*FoxBot curls up in a ball, and takes a nap. Bye!* :rainbow:")
    client.close()
    exit(1)


# StupidFox command
# INPUT: !stupidfox
# OUTPUT: A "random" StupidFox comic.
@client.command(pass_context = True)
async def stupidfox(ctx):
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
        imageurl.replace("--", "-")
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