import sys
import asyncio, aiohttp, logging, time, string, random, copy, json, asyncpg, re
from aiohttp import ClientSession
from datetime import datetime, date

import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

import time
from datetime import datetime, date, timedelta

from cogs.const import *
from cogs.classes import *
from config.settings import settings



async def request_parse(request):
    headers = request.headers
    data = await request.json
    args = request.args
    form = await request.form

    if not data:
        data = {}

    for key, value in args.items():
        data[key] = value

    return headers, data, args, form

def get_int_from_data(data, key, min=1, max=1, default=1):
    try:
        value = int(data[key])
    except:
        value = default
    if value > max:
        value = max
    if value < min:
        value = min
    return value

def get_value_from_data(data, key, default=None):
    try:
        value = data[key]
    except:
        value = default
    return value

# Youtube timestamp converter
def get_utc_from_string(timestamp):
    YT_CREATION_TIMESTAMP = 1108339200

    if not timestamp:
        return datetime.utcfromtimestamp(YT_CREATION_TIMESTAMP)
    try:
        timestamp = datetime.strptime(str(timestamp), "%Y-%m-%dT%H:%M:%S.%fZ")
        return timestamp
    except:
        pass
    try:
        timestamp = datetime.strptime(str(timestamp), "%Y-%m-%dT%H:%M:%SZ")
        return timestamp
    except:
        return datetime.utcfromtimestamp(YT_CREATION_TIMESTAMP)

def unix_time():
    return int(datetime.utcnow().timestamp())

def get_lvl(xp: int):
    lvl = 0
    i = 1
    if xp > 0:
        while xp >= (i * (i + 1) * 5):
            lvl += 1
            i += 1
    return lvl

def starred_name(user):
    return "**{}**".format(user.name.replace('*', '\\*'))

def starred_dname(user):
    return "**{}**".format(user.display_name.replace('*', '\\*'))

def tagged_name(user):
    return "{0.name}#{0.discriminator}".format(user)

def tagged_name_id(user):
    return "{0.name}#{0.discriminator} [{0.id}]".format(user)

def tagged_dname(user):
    return "{0.display_name}#{0.discriminator}".format(user)

def tagged_gname(guild):
    return "{0.name} | {0.id}".format(guild)


async def publish_message(message: discord.Message, delay=0):
    try:
        await asyncio.sleep(delay)

        msg = await message.channel.fetch_message(message.id)

        await msg.publish()
    except Exception as e:
        print(f"publish_message: {e}")


MAIN_GUILD_ID = 549251000167301120
def dsi_check_user_like(bot: discord.Client, message: discord.Message):
    # Log Channel on DSI discord server
    if message.channel.id != 581415119645573121:
        return None
    # Message sent by user/bot, not webhook log
    if message.webhook_id == None:
        return None
    # Message has no embeds
    if not message.embeds:
        return None

    for embed in message.embeds:
        try:
            server = message.author.name
            server = server.split(" | ")
            server = server[-1].rsplit("#", maxsplit=1)[0]
            server_id = int(server)
            if server_id != MAIN_GUILD_ID:
                # Like for another server
                return None

            author = embed.author.name
            author = author.split(" | ")
            author = bot.get_user(int(author[-1]))

            if not author:
                # Can't find user
                return None
            # Returns found user
            return author
        except Exception as e:
            pass
    # If valid embed not found
    return None


def beauty_icon(url, default="webp"):
    url = str(url)
    urls = url.rsplit(".", maxsplit=1)
    code = urls[0]
    code = code.rsplit("/", maxsplit=1)
    if code[1].startswith("a_"):
        return code[0]+"/"+code[1]+".gif"
    if not default:
        return code[0]+"/"+code[1] + "." + urls[1].split("/", maxsplit=1)[0].split("?", maxsplit=1)[0]
    return code[0] + "/" + code[1] + "." + str(default)

def clear_name(name):
    return name.replace("\\", "\\\\").replace("\"", "\\\"").replace("\'", "\\\'")

def clear_icon(url):
    try:
        code = url.rsplit(".", maxsplit=1)
        code = code[0] + "." + code[1].split("/", maxsplit=1)[0].split("?", maxsplit=1)[0]
        return code
    except:
        return None

def split_int(value, char = "."):
    char = str(char)
    value = str(value)
    pattern = "([0-9]{3})"
    value = value[::-1]
    value = re.sub(pattern, r"\1"+char, value)
    value = value[::-1]
    value = value.lstrip(char)
    return value

def format_seconds(t, is_left=False, no_text: str="now"):
    t = int(t)
    d = t//86400
    h = (t%86400)//3600
    m = (t//60)%60
    s = t%60
    left = ""
    if d > 1:
        left = left + str(d) + " days "
    elif d > 0:
        left = left + str(d) + " day "
    else:
        if h > 1:
            left = left + str(h) + " hours "
        elif h > 0:
            left = left + str(h) + " hour "
        if m > 1:
            left = left + str(m) + " minutes "
        elif m > 0:
            left = left + str(m) + " minute "
        else:
            if s > 1:
                left = left + str(s) + " seconds "
            elif s > 0:
                left = left + str(s) + " seconds "
            else:
                return no_text
    if is_left:
        left = left + "left"
    return left


def welcomer_format(member, data, text: str=None):
    guild = member.guild
    if not text:
        text = data["welcome_text"]
    return text.format(
        name=member.name,
        tagged_name=tagged_name(member),
        discriminator=member.discriminator,
        mention=member.mention,
        guild=guild.name,
        server=guild.name,
        count=guild.member_count,
        member_id=member.id,
        display_name=member.display_name,
        guild_id=guild.id,
        emoji=data["emoji"],
        prefix=data["prefix"],
        timely=data["timely_award"],
        work=data["work_award"],
        private_voice=f"<@&{data['create_voice_id']}>" if data['create_voice_id'] else "-"
    )[:2000]


def get_embed(value):
    em = discord.Embed.Empty
    try:
        ret = json.loads(value)
        if ret and isinstance(ret, dict):
            text = ret.pop("text", None)

            urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', str(ret.get("image", "")))
            if urls:
                ret["image"] = {"url": urls[0]}
            urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', str(ret.get("thumbnail", "")))
            if urls:
                ret["thumbnail"] = {"url": urls[0]}

            if ret:
                em = discord.Embed.from_dict(ret)
        else:
            text = value
    except:
        text = value[:2000]
        em = None
    return text, em


def is_admin(user):
    if user.guild_permissions.administrator:
        return True
    if user.guild.owner.id == user.id:
        return True
    return False

def seconds_to_args(t):
    t = int(t)
    d = t//86400
    h = (t%86400)//3600
    m = (t//60)%60
    s = t%60
    return d, h, m, s

async def context_init(ctx, cmd: str=None):
    nctx = ctx
    nctx.channel = nctx.message.channel
    nctx.author = nctx.message.author
    nctx.guild_id = nctx.message.guild.id
    nctx.const = await nctx.bot.get_cached_guild(nctx.message.guild)
    nctx.badges = await nctx.bot.get_badges(nctx.author)
    if not nctx.const or (cmd and not nctx.const["is_"+cmd]):
        await nctx.bot.true_send_error(ctx=ctx, channel=nctx.channel, error="global_not_available")
        return None

    nctx.lang = nctx.const["locale"]
    emoji = nctx.const["emoji"]
    emoji = re.sub(r'\D', '', emoji)
    if not emoji:
        emoji = nctx.const["emoji"]
    else:
        emoji = nctx.bot.get_emoji(int(emoji))
        if not emoji:
            emoji = "🍪"
        emoji = str(emoji)
    nctx.emoji = emoji

    nctx.embed = discord.Embed(colour=int(nctx.const["em_color"], 16) + 512)

    if nctx.const["is_nitro"]:
        nctx.is_nitro = True
    else:
        nctx.is_nitro = False

    return nctx
