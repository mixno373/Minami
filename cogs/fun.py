import sys, os
import asyncio, aiohttp, logging, time, string, random, copy, json, asyncpg, requests
from aiohttp import ClientSession
from datetime import datetime, date

import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

import time
from datetime import datetime, date, timedelta

from PIL import Image, ImageChops, ImageFont, ImageDraw, ImageSequence, ImageFilter, GifImagePlugin
from PIL.GifImagePlugin import getheader, getdata
from functools import partial
from io import BytesIO

from cogs.util import *
from cogs.const import *
from cogs.classes import *
from config.settings import settings



mask = Image.new('L', (1000, 1000), 0)
draws = ImageDraw.Draw(mask)
draws.ellipse((0, 0) + (1000, 1000), fill=255)
mask = mask.resize((200, 200), Image.ANTIALIAS)

mask_profile = Image.new('L', (800, 800), 0)
draws_profile = ImageDraw.Draw(mask_profile)
draws_profile.rectangle((0, 295) + (800, 505), fill=77)
mask_profile = mask_profile.resize((800, 800), Image.ANTIALIAS)

mask_top = Image.new('L', (269, 269), 0)
draws_top = ImageDraw.Draw(mask_top)
draws_top.ellipse((0, 0) + (269, 269), fill=255)
mask_top = mask_top.resize((269, 269), Image.ANTIALIAS)

mask_top_back = Image.new('L', (549, 549), 0)
draws_top_back = ImageDraw.Draw(mask_top_back)
draws_top_back.rectangle((274, 0) + (474, 549), fill=255)
mask_top_back = mask_top_back.resize((549, 549), Image.ANTIALIAS)



class Fun(commands.Cog):


    def __init__(self, bot):
        self.bot = bot


    @commands.command(pass_context=True, name="me", aliases=["profile"])
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def me_(self, ctx, user: discord.Member=None):
        """Shows user's profile.

        Arguments
        -----------
        user: :class:`Member`

        Returns
        ---------
        An image with user's profile
        """

        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "me")
        if not ctx: return
        em = ctx.embed.copy()

        if not user:
            user = ctx.author
        if user.bot:
            await bot.true_send_error(ctx=ctx, error="cm_bot_mentioned")
            return

        async with ctx.channel.typing():
            data = await bot.db.select("*", "users", where={"guild": ctx.guild.id, "id": user.id})
            if not data:
                data = await bot.db.insert({
                    "name": user.display_name,
                    "discriminator": user.discriminator,
                    "id": user.id,
                    "guild": ctx.guild.id
                }, "users")
            badges = await bot.get_badges(user.id)
        #================================================== stats 1
            xp_lvl = get_lvl(data["xp"])
            xp_count = str(data["xp"])
            xp_nex_lvl = "/"+str((xp_lvl + 1) * (xp_lvl + 2) * 5)

            cash = split_int(data["cash"])
        #==================================================
            img = Image.open("cogs/stat/backgrounds/profile.png")
            draw = ImageDraw.Draw(img)


            ava_url = user.avatar_url_as(size=4096)
            try:
                avatar = Image.open(BytesIO(await ava_url.read()))
                avatar = avatar.convert("RGBA")
            except Exception as e:
                logger.info(f"profile: Unknown exception ({e}) - {ctx.guild.name} [{ctx.guild.id}] User:{ctx.author.name} [{ctx.author.id}]")
                await bot.true_send_error(ctx=ctx, error="global_url_not_image")
                return

            back = avatar.filter(ImageFilter.GaussianBlur(5))
            back = avatar.resize((800, 800))
            back.putalpha(mask_profile)
            img.paste(back, (0, -295), back)
            avatar = avatar.resize((200, 200))
            avatar.putalpha(mask)
            img.paste(avatar, (24, 5), avatar)
            draw = ImageDraw.Draw(img)
            shift = 0
            for badge in badges.get_badges():
                icon = badges_obj.get(badge)
                if icon:
                    img.paste(icon, (260+shift, 90), icon)
                    shift += icon.size[1] + 10

            name = u"{}".format(tagged_name(user))
            name_size = 1
            font_name = ImageFont.truetype("cogs/stat/ProximaNova-Bold.otf", name_size)
            while font_name.getsize(name)[0] < 450:
                name_size += 1
                font_name = ImageFont.truetype("cogs/stat/ProximaNova-Bold.otf", name_size)
                if name_size == 50:
                    break
            name_size -= 1
            font_name = ImageFont.truetype("cogs/stat/ProximaNova-Bold.otf", name_size)
            draw.text(
                (258, 70-font_name.getsize(name)[1]),
                name,
                (255, 255, 255),
                font=font_name
            )

            t=data["voice_seconds"]
            hours=str(t//3600)
            minutes=str((t//60)%60)
            seconds=str(t%60)
            messages = data["messages"]
            if messages > 50000:
                messages = "50.000+"
            else:
                messages = split_int(messages)
            stats = "{messages}sms | {h}h {m}m {s}s voice".format(
                messages=messages,
                h=split_int(hours),
                m=minutes,
                s=seconds
            )
            font_stats = ImageFont.truetype("cogs/stat/ProximaNova-Regular.ttf", 30)
            draw.text(
                (258, 148),
                stats,
                (255, 255, 255),
                font=font_stats
            )

            down_name = "LVL:\nXP:\nBALANCE:"
            font_down_name = ImageFont.truetype("cogs/stat/ProximaNova-Bold.otf", 33)
            draw.text(
                (24, 221),
                down_name,
                (255, 255, 255),
                font=font_down_name
            )

            font_down = ImageFont.truetype("cogs/stat/ProximaNova-Regular.ttf", 33)
            font_down_xp = ImageFont.truetype("cogs/stat/ProximaNova-Regular.ttf", 17)
            draw.text(
                (95, 221),
                str(xp_lvl),
                (255, 255, 255),
                font=font_down
            )
            draw.text(
                (80, 256),
                str(xp_count),
                (255, 255, 255),
                font=font_down
            )
            draw.text(
                (80+font_down.getsize(str(xp_count))[0], 270),
                str(xp_nex_lvl),
                (255, 255, 255),
                font=font_down_xp
            )
            draw.text(
                (187, 292),
                cash,
                (255, 255, 255),
                font=font_down
            )
            draw.text(
                (187+font_down.getsize(cash)[0], 306),
                "$",
                (255, 255, 255),
                font=font_down_xp
            )

            fp = BytesIO()
            img.save(fp, "PNG")
            fp.seek(0)
            await bot.true_send(ctx=ctx, file=discord.File(fp, f'profile_{ctx.author.id}_{ctx.guild.id}.png'))
            return


    @commands.command(pass_context=True, name="hug", aliases=[
        "kiss",
        "wink",
        "punch",
        "drink",
        "five",
        "high-five",
        "highfive",
        "fuck",
        "bite",
        "lick",
        "pat",
        "slap",
        "poke"
    ])
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def activities_(self, ctx, user: discord.Member=None):
        bot = self.bot
        ctx.bot = bot

        cmd = ctx.invoked_with.lower()

        act = ACTIVITIES.get(cmd, "hug")

        ctx = await context_init(ctx, act['cmd'])
        if not ctx: return
        em = ctx.embed.copy()

        if not user:
            user = ctx.author

        tenor_name = act["tenor"]
        if ctx.const["anime_gif"]: tenor_name = f"{tenor_name} anime"
        gif_url = await bot.get_tenor_gif(tenor_name)
        content = "💬 "+bot.get_locale(ctx.lang, f"fun_{act['cmd']}").format(
            author=starred_dname(ctx.author),
            user=starred_dname(user)
        )
        em.color = 0x36393F
        em.set_image(url=gif_url)

        await bot.true_send(ctx=ctx, content=content, embed=em)
        return


    @commands.command(pass_context=True, name="owo", aliases=[
        "lewd",
        "neko",
        "megumin",
        "deredere",
        "cry",
        "shrug",
        "trap",
        "baka",
        "sleepy",
        "jojo",
        "awoo",
        "smile",
        "smug",
        "nani",
        "poi",
        "pout",
        "wasted"
    ])
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def secret_activities_(self, ctx, user: discord.Member=None):
        bot = self.bot
        ctx.bot = bot

        cmd = ctx.invoked_with.lower()

        ctx = await context_init(ctx, "secret")
        if not ctx: return
        em = ctx.embed.copy()

        gif_url = await bot.get_weeb_gif(cmd)
        em.set_author(name=tagged_dname(ctx.author), icon_url=str(ctx.author.avatar_url))
        em.set_image(url=gif_url)
        em.color = 0x36393F

        await bot.true_send(ctx=ctx, embed=em)
        return



    @commands.command(pass_context=True, name="top", aliases=[
        "voice",
        "money"
    ])
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def top_(self, ctx, page: int=1):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "top")
        if not ctx: return

        async with ctx.channel.typing():
            data = await bot.db.select("COUNT(name) as count", "users", where={"guild": ctx.guild.id})
            all_count = data["count"]
            pages = (((all_count - 1) // 5) + 1)
            if page < 1:
                page = 1
            if all_count == 0:
                await bot.true_send_error(ctx=ctx, error="global_list_is_empty")
                return
            if page > pages:
                await bot.true_send_error(ctx=ctx, error="global_page_not_exists", who=tagged_dname(ctx.author), arg=page)
                return
            type = ctx.invoked_with.lower()
            if type == "top":
                order = "xp"
            elif type == "money":
                order = "cash"
            elif type == "voice":
                order = "voice_seconds"
            else:
                order = "name"
            data = await bot.db.select_all(
                "*",
                "users",
                where={"guild": ctx.guild.id},
                order={order: False},
                limit=5,
                offset=(page-1)*5
            )
        #==================================================
            img = Image.open("cogs/stat/top5.png")
            back = Image.open("cogs/stat/top5.png")
            draw = ImageDraw.Draw(img)
            draws = ImageDraw.Draw(back)

            font_position = ImageFont.truetype("cogs/stat/Roboto-Bold.ttf", 24)
            font_count = ImageFont.truetype("cogs/stat/Roboto-Regular.ttf", 16)

            for i, user in enumerate(data):
                name = user["name"]
                name = u"{}".format(name)
                name_size = 1
                font_name = ImageFont.truetype("cogs/stat/Roboto-Bold.ttf", name_size)
                while font_name.getsize(name)[0] < 180:
                    name_size += 1
                    font_name = ImageFont.truetype("cogs/stat/Roboto-Bold.ttf", name_size)
                    if name_size == 31:
                        break
                name_size -= 1
                font_name = ImageFont.truetype("cogs/stat/Roboto-Bold.ttf", name_size)
                if not name:
                    name = " "
                ava_url = user["avatar_url"]
                if ava_url:
                    try:
                        response = str(requests.session().get(ava_url).content)
                        if not response[2:-1]:
                            ava_url = None
                    except:
                        ava_url = None
                if not ava_url:
                    ava_url = str(bot.user.default_avatar_url)

                response = requests.get(ava_url)
                avatar = Image.open(BytesIO(response.content)).convert('RGB')
                avatar_circle = avatar.resize((549, 549))
                avatar_circle.putalpha(mask_top_back)
                avatar_circle = avatar_circle.crop((274, 0, 474, 549))
                back.paste(avatar_circle, (i*200, 0), avatar_circle)
                avatar_circle = avatar.resize((269, 269))
                bigsize = (avatar_circle.size[0] * 3, avatar_circle.size[1] * 3)
                avatar_circle.putalpha(mask_top)
                avatar_circle = avatar_circle.crop((0, 0, 134, 269))
                img.paste(avatar_circle, (66+i*200, 125), avatar_circle)
                position = "#{}".format(i+1+(page-1)*5)
                draw.text(
                    (
                        100-font_position.getsize(position)[0]/2+i*200,
                        440-font_position.getsize(position)[1]/2
                    ),
                    position,
                    (255, 255, 255),
                    font=font_position
                )
                draw.text((100-font_name.getsize(name)[0]/2+i*200, 50-font_name.getsize(name)[1]/2), name, (255, 255, 255), font=font_name)
                if type == "top":
                    count = bot.get_locale(ctx.lang, "fun_top5_xp_count").format((user["xp"]))
                    _type = "xp"
                elif type == "money":
                    count = f"{split_int(user['cash'])}$"
                    _type = "money"
                elif type == "voice":
                    count = format_seconds(user["voice_seconds"], no_text="-")
                    _type = "voice"
                else:
                    count = "0"
                    _type = "name"
                draw.text(
                    (
                        100-font_count.getsize(count)[0]/2+i*200,
                        475-font_count.getsize(count)[1]/2
                    ),
                    count,
                    (255, 255, 255),
                    font=font_count
                )

            back.paste(img, (0, 0), img)

            fp = BytesIO()
            back.save(fp, "PNG")
            fp.seek(0)
            await bot.true_send(
                ctx=ctx,
                content=bot.get_locale(ctx.lang, "fun_top5_response").format(type=bot.get_locale(ctx.lang, "fun_top5_type_"+_type)),
                file=discord.File(fp, f'top_{ctx.author.id}_{ctx.guild.id}.png')
            )
            return



def setup(bot):
    bot.add_cog(Fun(bot))
