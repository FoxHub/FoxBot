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

config_data = open('configs/config.json').read()
config = json.loads(config_data)

# TODO: Add dice-rolling, death, random chance of foxes, update documentation

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
                em = discord.Embed(title='Your random cat! :fox:',
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
        #break
    except IndexError:
        await client.say("*Fox-Bot looks at you confused. You must provide an argument!*")


# ChuckNorris command.
# INPUT: !chucknorris
# OUTPUT: A random chuck norris joke.
@client.command(pass_context = True)
async def chucknorris(ctx):
    # TODO: Document this function.
    async with aiohttp.ClientSession() as session:
        async with session.get("http://api.icndb.com/jokes/random") as r:
            if (r.status == 200):
                js = await r.json()
                await client.say(js['value']['joke'])


# Commands command.
# INPUT: !commands
# OUTPUT: Fox-bot tells you all of her commands and their syntax.
@client.command(pass_context = True)
async def commands(ctx):
    # TODO: Keep this command updated.
    preamble = "My current command prefix is '" + bot_prefix + "', and my commands are:"
    commands = "\n" + bot_prefix + "cat: I give you a random cute cat!" + \
               "\n" + bot_prefix + "commands: You're using me!" + \
               "\n" + bot_prefix + "connect: I connect to your voice channel." + \
               "\n" + bot_prefix + "cuddle: I say something cute, then connect to you." + \
               "\n" + bot_prefix + "disconnect: I leave your voice channel." + \
               "\n" + bot_prefix + "info: Trivia about me!" + \
               "\n" + bot_prefix + "lol: I call Deku's players for a LoL game." + \
               "\n" + bot_prefix + "ping: I say 'Pong!'."
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
        await client.say("Fox-Bot can't find you!")
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
    # TODO: Pretty up this command.
    desc = "Current command prefix: " + bot_prefix + \
           "\nPython version: 3.6.3" + \
           "\nAuthor: Sage Callon"
    embed = discord.Embed(title="Hi! I'm Fox-bot.", description=desc, color=0xFFFFF)
    return await client.say(embed=embed)


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
    await client.say("Pong!", delete_after=10)


# Sleep command
# INPUT: !sleep
# OUTPUT: FoxBot terminates.
@client.command(pass_context=True)
async def sleep(ctx):
    # TODO: Document this function.
    await client.say("*FoxBot curls up in a ball, and takes a nap. Bye!* :rainbow:")
    client.close()
    exit(1)


client.run(bot_token)