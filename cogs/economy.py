import sys
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

import urbandictionary as urbandict

from cogs.util import *
from cogs.const import *
from cogs.classes import *
from config.settings import settings

random.seed()



class Economy(commands.Cog):


    def __init__(self, bot):
        self.bot = bot


    @commands.command(pass_context=True, name="timely", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def timely_(self, ctx):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "timely")
        if not ctx: return
        em = ctx.embed.copy()

        data = await bot.db.select(["last_timely", "cash"], "users", where={"id": ctx.author.id, "guild": ctx.guild.id})
        count = ctx.const["timely_award"]
        now = unix_time()
        if data:
            t_last = now - data["last_timely"]
            if t_last < ctx.const["timely_cd"]:
                d, h, m, s = seconds_to_args(ctx.const["timely_cd"] - t_last)
                em.description = "{later1}\n{later2}".format(
                    later1=bot.get_locale(ctx.lang, "economy_try_again_later1").format(
                        who=tagged_dname(ctx.author),
                        money=ctx.emoji
                    ),
                    later2=bot.get_locale(ctx.lang, "economy_try_again_later2").format(
                        hours=h,
                        minutes=m,
                        seconds=s
                    )
                )
            else:
                await bot.db.update({
                    "last_timely": now,
                    "cash": {count: "+"}
                }, "users", where={"id": ctx.author.id, "guild": ctx.guild.id})
                em.description = bot.get_locale(ctx.lang, "economy_received_money").format(
                    author=tagged_dname(ctx.author),
                    count=split_int(count),
                    emoji=ctx.emoji
                )
        else:
            await bot.db.insert({
                "name": ctx.author.name,
                "id": ctx.author.id,
                "last_timely": now,
                "cash": count,
                "guild": ctx.guild.id
            }, "users")
            em.description = bot.get_locale(ctx.lang, "economy_received_money").format(
                author=tagged_dname(ctx.author),
                count=split_int(count),
                emoji=ctx.emoji
            )

        await bot.true_send(ctx=ctx, embed=em)
        return


    @commands.command(pass_context=True, name="work", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def work_(self, ctx):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "work")
        if not ctx: return
        em = ctx.embed.copy()

        data = await bot.db.select("last_work", "users", where={"id": ctx.author.id, "guild": ctx.guild.id})
        now = unix_time()
        if data:
            if data["last_work"] == -1:
                await bot.db.update({"last_work": now}, "users", where={"id": ctx.author.id, "guild": ctx.guild.id})
                em.description = bot.get_locale(ctx.lang, "economy_went_to_work").format(tagged_dname(ctx.author))
            elif data["last_work"] > 0 and data["last_work"] <= now - ctx.const["work_cd"]:
                await bot.db.update({
                    "last_work": now,
                    "cash": {ctx.const['work_award']: "+"}
                }, "users", where={"id": ctx.author.id, "guild": ctx.guild.id})
                em.description = bot.get_locale(ctx.lang, "economy_went_to_work").format(tagged_dname(ctx.author))
            else:
                em.description = bot.get_locale(ctx.lang, "economy_already_at_work").format(tagged_dname(ctx.author))
        else:
            await bot.db.insert({
                "name": ctx.author.name,
                "id": ctx.author.id,
                "last_work": now,
                "guild": ctx.guild.id
            }, "users")
            em.description = bot.get_locale(ctx.lang, "economy_went_to_work").format(tagged_dname(ctx.author))

        await bot.true_send(ctx=ctx, embed=em)
        return


    @commands.command(pass_context=True, name="br", aliases=["bet-roll"], invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def br_(self, ctx, amount: str="all"):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "br")
        if not ctx: return
        em = ctx.embed.copy()

        amount = amount.lower()
        if not amount or not (amount.isdigit() or amount == 'all'):
            await bot.true_send_error(ctx=ctx, error="global_not_number", author=tagged_dname(ctx.author))
            return

        amount = amount[:20]
        data = await bot.db.select("cash", "users", where={"id": ctx.author.id, "guild": ctx.guild.id})
        if not data:
            await bot.db.insert({
                "name": ctx.author.name,
                "id": ctx.author.id,
                "guild": ctx.guild.id
            }, "users")
            await bot.true_send_error(ctx=ctx, error="global_dont_have_that_much_money", author=tagged_dname(ctx.author))
            return

        if amount == 'all':
            amount = data["cash"]
        else:
            amount = int(amount)
        if data["cash"] < amount:
            await bot.true_send_error(ctx=ctx, error="global_dont_have_that_much_money", author=tagged_dname(ctx.author))
            return
        if amount < 1:
            await bot.true_send_error(ctx=ctx, error="economy_cant_put_bet_of_zero", author=tagged_dname(ctx.author))
            return

        chance = random.randint(0, 99)
        if ctx.badges.boost:
            chance += 10
        if chance > 55:
            if not await bot.check_any_badges(ctx.author, ["nitro", "staff", "partner"]):
                amount = int(amount / 2)
            if amount == 0: amount = 1

            cash = {amount: "+"}
            em.description = bot.get_locale(ctx.lang, "economy_you_win").format(
                author=tagged_dname(ctx.author),
                amount=split_int(amount),
                emoji=ctx.emoji
            )
        else:
            cash = {amount: "-"}
            em.description = bot.get_locale(ctx.lang, "economy_you_lose").format(
                author=tagged_dname(ctx.author),
                amount=split_int(amount),
                emoji=ctx.emoji
            )
        await bot.db.update({
            "cash": cash
        }, "users", where={"id": ctx.author.id, "guild": ctx.guild.id})

        await bot.true_send(ctx=ctx, embed=em)
        return


    @commands.command(pass_context=True, name="slots", aliases=["slot"], invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def slots_(self, ctx, amount: str="all"):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "slots")
        if not ctx: return
        em = ctx.embed.copy()

        amount = amount.lower()
        if not amount or not (amount.isdigit() or amount == 'all'):
            await bot.true_send_error(ctx=ctx, error="global_not_number", author=tagged_dname(ctx.author))
            return

        amount = amount[:20]
        data = await bot.db.select("cash", "users", where={"id": ctx.author.id, "guild": ctx.guild.id})
        if not data:
            await bot.db.insert({
                "name": ctx.author.name,
                "id": ctx.author.id,
                "guild": ctx.guild.id
            }, "users")
            await bot.true_send_error(ctx=ctx, error="global_dont_have_that_much_money", author=tagged_dname(ctx.author))
            return

        if amount == 'all':
            amount = data["cash"]
        else:
            amount = int(amount)
        if data["cash"] < amount:
            await bot.true_send_error(ctx=ctx, error="global_dont_have_that_much_money", author=tagged_dname(ctx.author))
            return
        if amount < 1:
            await bot.true_send_error(ctx=ctx, error="economy_cant_put_bet_of_zero", author=tagged_dname(ctx.author))
            return

        emojis = "🍎🍊🍐🍋🍉🍇🍓🍒"

        a = random.choice(emojis)
        b = random.choice(emojis)
        c = random.choice(emojis)

        a_ = random.choice(emojis)
        b_ = random.choice(emojis)
        c_ = random.choice(emojis)

        _a = random.choice(emojis)
        _b = random.choice(emojis)
        _c = random.choice(emojis)

        if (a == b == c):
            amount = int(amount * 3)
            cash = {amount: "+"}
            result = bot.get_locale(ctx.lang, "economy_you_win")
        elif (a == b) or (a == c) or (b == c):
            amount = int(amount * 1.5)
            cash = {amount: "+"}
            result = bot.get_locale(ctx.lang, "economy_you_win")
        else:
            cash = {amount: "-"}
            result = bot.get_locale(ctx.lang, "economy_you_lose")

        em.title = "S L O T S"
        em.description = "{slot1}{slot2}{slot3}{result}".format(
            slot1=f"{_a}{_b}{_c}\n",
            slot2=f"{a}{b}{c} \◀\n",
            slot3=f"{a_}{b_}{c_}\n",
            result=result.format(
                author=tagged_dname(ctx.author),
                amount=split_int(amount),
                emoji=ctx.emoji
            )
        )

        await bot.db.update({
            "cash": cash
        }, "users", where={"id": ctx.author.id, "guild": ctx.guild.id})

        await bot.true_send(ctx=ctx, embed=em)
        return


    @commands.command(pass_context=True, name="flipcoin", aliases=["flip-coin", "coin", "flip", "fc"], invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def flipcoin_(self, ctx, amount: str="all", side: str="h"):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "flip")
        if not ctx: return
        em = ctx.embed.copy()

        amount = amount.lower()
        if not amount or not (amount.isdigit() or amount == 'all'):
            await bot.true_send_error(ctx=ctx, error="global_not_number", author=tagged_dname(ctx.author))
            return

        amount = amount[:20]
        data = await bot.db.select("cash", "users", where={"id": ctx.author.id, "guild": ctx.guild.id})
        if not data:
            await bot.db.insert({
                "name": ctx.author.name,
                "id": ctx.author.id,
                "guild": ctx.guild.id
            }, "users")
            await bot.true_send_error(ctx=ctx, error="global_dont_have_that_much_money", author=tagged_dname(ctx.author))
            return

        if amount == 'all':
            amount = data["cash"]
        else:
            amount = int(amount)
        if data["cash"] < amount:
            await bot.true_send_error(ctx=ctx, error="global_dont_have_that_much_money", author=tagged_dname(ctx.author))
            return
        if amount < 1:
            await bot.true_send_error(ctx=ctx, error="economy_cant_put_bet_of_zero", author=tagged_dname(ctx.author))
            return

        side = flipcoin_sides.get(side.lower(), "heads")
        win_side = random.choice(list(flipcoin_images.keys()))
        if side == win_side:
            if not await bot.check_any_badges(ctx.author, ["nitro", "staff", "partner"]):
                amount = int(amount / 2)
            if amount == 0: amount = 1

            cash = {amount: "+"}
            em.description = bot.get_locale(ctx.lang, "economy_you_win").format(
                author=tagged_dname(ctx.author),
                amount=split_int(amount),
                emoji=ctx.emoji
            )
        else:
            cash = {amount: "-"}
            em.description = bot.get_locale(ctx.lang, "economy_you_lose").format(
                author=tagged_dname(ctx.author),
                amount=split_int(amount),
                emoji=ctx.emoji
            )
        await bot.db.update({
            "cash": cash
        }, "users", where={"id": ctx.author.id, "guild": ctx.guild.id})

        # tenor_name = "coin flip"
        # if ctx.const["anime_gif"]: tenor_name = f"{tenor_name} anime"
        # gif_url = await bot.get_tenor_gif(tenor_name)
        gif_url = flipcoin_images.get(win_side)
        em.set_image(url=gif_url)

        await bot.true_send(ctx=ctx, embed=em)
        return


    @commands.command(pass_context=True, name="cash", aliases=["$", "balance"], invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def cash_(self, ctx, user: discord.Member=None):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "cash")
        if not ctx: return
        em = ctx.embed.copy()

        if not user:
            user = ctx.author
        if user.bot:
            await bot.true_send_error(ctx=ctx, error="cm_bot_mentioned")
            return

        data = await bot.db.select("cash", "users", where={"id": user.id, "guild": ctx.guild.id})
        if data:
            count = data["cash"]
        else:
            count = 0
        em.description = bot.get_locale(ctx.lang, "economy_user_balance").format(
            author=tagged_dname(user),
            count=split_int(count),
            emoji=ctx.emoji
        )

        await bot.true_send(ctx=ctx, embed=em)
        return


    @commands.command(pass_context=True, name="give", aliases=["send"], invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def give_(self, ctx, user: discord.Member, amount: str="all"):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "give")
        if not ctx: return
        em = ctx.embed.copy()

        amount = amount.lower()
        if not amount or not (amount.isdigit() or amount == 'all'):
            await bot.true_send_error(ctx=ctx, error="global_not_number", author=tagged_dname(ctx.author))
            return

        amount = amount[:20]
        data = await bot.db.select("cash", "users", where={"id": ctx.author.id, "guild": ctx.guild.id})
        if data:
            if amount == 'all':
                amount = data["cash"]
            else:
                amount = int(amount)
            if data["cash"] < amount:
                await bot.true_send_error(ctx=ctx, error="global_dont_have_that_much_money", author=tagged_dname(ctx.author))
                return
            if amount < 1:
                await bot.true_send_error(ctx=ctx, error="economy_cant_give_zero", author=tagged_dname(ctx.author))
                return

            await bot.db.insert_update({
                "cash": {amount: "+"},
                "name": user.name,
                "discriminator": str(user.discriminator),
                "id": user.id,
                "guild": ctx.guild.id
            }, "users", where={"id": user.id, "guild": ctx.guild.id}, constraint="unic_profile")
            await bot.db.update({
                "cash": {amount: "-"}
            }, "users", where={"id": ctx.author.id, "guild": ctx.guild.id})
            em.description = bot.get_locale(ctx.lang, "economy_give").format(
                author=tagged_dname(ctx.author),
                amount=split_int(amount),
                emoji=ctx.emoji,
                user=tagged_dname(user)
            )
        else:
            await bot.db.insert({
                "name": ctx.author.name,
                "id": ctx.author.id,
                "guild": ctx.guild.id
            }, "users")
            await bot.true_send_error(ctx=ctx, error="global_dont_have_that_much_money", author=tagged_dname(ctx.author))
            return

        await bot.true_send(ctx=ctx, embed=em)
        return


    @commands.command(pass_context=True, name="take", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def take_(self, ctx, user: discord.Member, amount: str="all"):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "take")
        if not ctx or not is_admin(ctx.author): return
        em = ctx.embed.copy()

        amount = amount.lower()
        if not amount or not (amount.isdigit() or amount == 'all'):
            await bot.true_send_error(ctx=ctx, error="global_not_number", author=tagged_dname(ctx.author))
            return

        data = await bot.db.select("cash", "users", where={"id": user.id, "guild": ctx.guild.id})

        amount = amount[:20]
        if amount == 'all':
            amount = data["cash"]
        else:
            amount = int(amount)
        if amount < 1:
            amount = 1
        if amount > data["cash"]:
            amount = data["cash"]

        if data:
            await bot.db.update({
                "cash": {amount: "-"},
                "name": user.name,
                "discriminator": str(user.discriminator),
                "id": user.id,
                "guild": ctx.guild.id
            }, "users", where={"id": user.id, "guild": ctx.guild.id})
        else:
            await bot.db.insert({
                "name": user.name,
                "discriminator": str(user.discriminator),
                "id": user.id,
                "guild": ctx.guild.id
            }, "users")
        em.description = bot.get_locale(ctx.lang, "admin_you_dont_like_him").format(
            user=tagged_dname(user),
            amount=split_int(amount),
            emoji=ctx.emoji
        )

        await bot.true_send(ctx=ctx, embed=em)
        return


    @commands.command(pass_context=True, name="gift", aliases=["pay"], invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def gift_(self, ctx, amount: int=373):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "gift")
        if not ctx or not is_admin(ctx.author): return
        em = ctx.embed.copy()

        if amount < 1:
            await bot.true_send_error(
                ctx=ctx,
                error="economy_cant_give_zero",
                author=tagged_dname(ctx.author),
                emoji=ctx.emoji
            )
            return

        await bot.db.insert_update({
            "cash": {amount: "+"},
            "name": ctx.author.name,
            "id": ctx.author.id,
            "guild": ctx.guild.id
        }, "users", where={"id": ctx.author.id, "guild": ctx.guild.id}, constraint="unic_profile")
        em.description = bot.get_locale(ctx.lang, "economy_gift").format(
            amount=split_int(amount),
            emoji=ctx.emoji
        )

        await bot.true_send(ctx=ctx, channel=ctx.author, embed=em)
        return


    @commands.command(pass_context=True, name="shop", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def shop_(self, ctx, page: int=1):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "shop")
        if not ctx: return
        em = ctx.embed.copy()

        data = await bot.db.select("COUNT(name) as count", "mods", where={"guild_id": ctx.guild.id, "type": "shop"})
        all_count = data["count"]
        pages = (((all_count - 1) // 25) + 1)
        if page < 1:
            page = 1
        em.title = bot.get_locale(ctx.lang, "economy_shop_title")
        if all_count == 0:
            await bot.true_send_error(ctx=ctx, channel=ctx.channel, error="global_list_is_empty")
            return
        if page > pages:
            await bot.true_send_error(ctx=ctx, channel=ctx.channel, error="global_page_not_exists", who=tagged_dname(ctx.author), arg=page)
            return

        data = await bot.db.select_all(
                "*",
                "mods",
                where = {
                    "guild_id": ctx.guild.id,
                    "type": "shop"
                },
                order = {
                    "condition::bigint": False,
                    "name::bigint": True
                },
                limit = 25,
                offset = (page-1)*25
            )
        if not data:
            await bot.true_send_error(ctx=ctx, channel=ctx.channel, error="global_list_is_empty")
            return

        delete_roles = []
        shop_roles = []
        for row in data:
            role = None
            try:
                role = ctx.guild.get_role(int(row["name"]))
            except discord.Forbidden:
                await bot.true_send_error(ctx=ctx, channel=ctx.channel, error="cant_get_role")
            except Exception as e:
                logger.info(f"shop: Unknown exception ({e}) - {ctx.guild.name} [{ctx.guild.id}] | User: {ctx.author.mention}")
                await bot.true_send_error(ctx=ctx, channel=ctx.channel, error="default")
            if role:
                shop_roles.append(f"{role.mention}**\n{split_int(int(row['condition'])%999999999)} {ctx.emoji}")
            else:
                delete_roles.append(str(row["id"]))
        if delete_roles:
            await bot.db.execute(f"DELETE FROM mods WHERE id in ({','.join(delete_roles)})")

        for index, role in enumerate(shop_roles):
            em.add_field(
                name="󠂪",
                value=f"**№{index+1+(page-1)*25} {role}",
                inline=True
            )
        em.set_footer(text=bot.get_locale(ctx.lang, "other_footer_page").format(number=page, length=pages) + " | " + bot.get_locale(ctx.lang, "other_shop_how_to_buy").format(prefix=ctx.const["prefix"]))

        await bot.true_send(ctx=ctx, embed=em)
        return


    @commands.command(pass_context=True, name="buy", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def buy_(self, ctx, *, name: str):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "shop")
        if not ctx: return
        em = ctx.embed.copy()

        data = None
        role = discord.utils.get(ctx.guild.roles, name=name)
        if not role:
            name = re.sub(r'\D', '', name)
            if not name:
                await bot.true_send_error(
                    ctx=ctx,
                    channel=ctx.channel,
                    error="incorrect_argument",
                    arg="Number"
                )
                return
            name = int(name)
            role = ctx.guild.get_role(name)
        if not role:
            if name < 1:
                name = 1
            data = await bot.db.select(
                "*",
                "mods",
                where = {
                    "type": "shop",
                    "guild_id": ctx.guild.id
                },
                order = {
                    "condition::bigint": False,
                    "name::bigint": True
                },
                offset=name-1
            )
            if data:
                role = ctx.guild.get_role(int(data["name"]))
        if not role:
            await bot.true_send_error(ctx=ctx, channel=ctx.channel, error="global_role_not_exists", who=tagged_dname(ctx.author))
            return
        if role in ctx.author.roles:
            await bot.true_send_error(ctx=ctx, channel=ctx.channel, error="global_role_already_have", who=tagged_dname(ctx.author), role=role.mention)
            return

        if not data:
            data = await bot.db.select(
                "*",
                "mods",
                where = {
                    "type": "shop",
                    "guild_id": ctx.guild.id,
                    "name": str(role.id)
                }
            )
        if not data:
            await bot.true_send_error(ctx=ctx, channel=ctx.channel, error="economy_role_not_in_shop", who=tagged_dname(ctx.author), role=role.mention)
            return

        user = await bot.db.select("cash", "users", where={"id": ctx.author.id, "guild": ctx.guild.id})
        if not user:
            await bot.db.insert({
                "name": user.name,
                "discriminator": str(user.discriminator),
                "id": user.id,
                "guild": ctx.guild.id,
                "avatar_url": str(message.author.avatar_url_as(static_format='png'))
            }, "users")
            await bot.true_send_error(ctx=ctx, channel=ctx.channel, error="global_dont_have_that_much_money", who=tagged_dname(ctx.author))
            return

        cost = int(data["condition"])%999999999
        if cost > user["cash"]:
            await bot.true_send_error(ctx=ctx, channel=ctx.channel, error="global_dont_have_that_much_money", who=tagged_dname(ctx.author))
            return

        try:
            await ctx.author.add_roles(role, reason="Tomori Shop Buy")
            await bot.db.update({
                "name": ctx.author.name,
                "discriminator": ctx.author.discriminator,
                "id": ctx.author.id,
                "guild": ctx.guild.id,
                "cash": {cost: "-"}
            }, "users", where={"id": ctx.author.id, "guild": ctx.guild.id})
            em.description = bot.get_locale(ctx.lang, "economy_role_response").format(
                who=tagged_dname(ctx.author),
                role=role.mention
            )
        except discord.Forbidden:
            await bot.true_send_error(ctx=ctx, channel=ctx.channel, error="economy_role_not_permission", who=member.mention, role=role.mention)
            return
        except Exception as e:
            logger.info(f"buy: Unknown exception ({e}) - {ctx.guild.name} [{ctx.guild.id}] | User: {ctx.author.mention} | Role: {role.mention}")
            await bot.true_send_error(ctx=ctx, channel=ctx.channel, error="default")
            return

        await bot.true_send(ctx=ctx, embed=em)
        return




def setup(bot):
    bot.add_cog(Economy(bot))
