import sys
import asyncio, aiohttp, logging, time, string, random, copy, json, asyncpg, requests
from aiohttp import ClientSession
from datetime import datetime, date

import discord
from discord.ext import commands
from discord import Webhook, AsyncWebhookAdapter
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



class Admin(commands.Cog):


    def __init__(self, bot):
        self.bot = bot


    @commands.group(pass_context=True, name="sql", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def sql_(self, ctx, *, query: str):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx or not ctx.badges.staff: return
        em = ctx.embed.copy()

        try:
            resp = await bot.db.fetchrow(query)
            if not resp:
                resp = {}
        except Exception as e:
            await bot.true_send_error(ctx=ctx, error="sql_bad_query")
            return

        embeds = []
        em.color = COLORS["idk"]
        embed = em.copy()

        for key, value in resp.items():
            if len(embed.fields) == 25:
                embeds.append(embed)
                embed = em.copy()
            value = f"'{value}'" if isinstance(value, str) else str(value)
            embed.add_field(
                name=key,
                value=value,
                inline=True
            )
        if len(embed.fields) != 25:
            embeds.append(embed)

        embeds[-1].set_footer(text=tagged_dname(ctx.author), icon_url=str(ctx.author.avatar_url))
        embeds[0].description = bot.get_locale(ctx.lang, "admin_request_completed").format(query)

        await bot.cache["guilds"].clear()
        await bot.cache["badges"].clear()

        await bot.true_send(ctx=ctx, embeds=embeds, nitro=True)
        return


    @sql_.group(pass_context=True, name="many", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def sql_many_(self, ctx, limit: int, *, query: str):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx or not ctx.badges.staff: return
        em = ctx.embed.copy()

        try:
            resp = await bot.db.fetch(f"{query} LIMIT {limit}")
            if not resp:
                resp = []
        except Exception as e:
            await bot.true_send_error(ctx=ctx, error="sql_bad_query")
            return

        embeds = []
        for row in resp:
            embed = em.copy()
            embed.color = random.randint(0, 0xffffff)
            for key, value in row.items():
                if len(embed.fields) == 25:
                    embeds.append(embed)
                    embed = em.copy()
                value = f"'{value}'" if isinstance(value, str) else str(value)
                embed.add_field(
                    name=key,
                    value=value,
                    inline=True
                )
            if len(embed.fields) != 25:
                embeds.append(embed)

        embeds[-1].set_footer(text=tagged_dname(ctx.author), icon_url=str(ctx.author.avatar_url))
        embeds[0].description = bot.get_locale(ctx.lang, "admin_request_completed").format(query)

        await bot.cache["guilds"].clear()
        await bot.cache["badges"].clear()

        await bot.true_send(ctx=ctx, embeds=embeds, nitro=True)
        return


    @commands.command(pass_context=True, name="say", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def say_(self, ctx, *, value: str):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "say")
        if not ctx or not is_admin(ctx.author): return

        channel = ctx.channel
        values = value.split(" ", maxsplit=1)
        if len(values) == 2:
            ch_id = values[0]
            channel = discord.utils.get(ctx.guild.text_channels, name=ch_id)
            if not channel:
                ch_id = re.sub(r'[<#>]', '', ch_id)
                try:
                    channel = bot.get_channel(int(ch_id))
                except:
                    pass
            if channel:
                value = values[1]
            else:
                channel = ctx.channel
        if not isinstance(channel, discord.TextChannel):
            channel = ctx.channel

        text, em = get_embed(value)

        await bot.true_send(ctx=ctx, channel=channel, content=text, embed=em)
        return


    @commands.command(pass_context=True, name="clear", aliases=["cl"], invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def clear_(self, ctx, count: int=1, user: discord.Member=None):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "clear")
        if not ctx or not is_admin(ctx.author): return

        if count < 1:
            count = 1

        if user:
            def check_user(m):
                return m.author == user
        else:
            check_user = None

        try:
            deleted = await ctx.channel.purge(limit=count, before=ctx.message, check=check_user)
        except discord.Forbidden:
            await self.bot.true_send_error(ctx=ctx, error="clear_cant_delete")
        except Exception as e:
            logger.info(f"clear: Unknown exception ({e}) - {ctx.guild.name} [{ctx.guild.id}]")

        return


    @commands.command(pass_context=True, name="webhook", aliases=["wh"], invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def webhook_(self, ctx, name: str, *, value: str):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "say")
        if not ctx or not is_admin(ctx.author): return

        data = await bot.db.select("*", "mods", where={
            "type": "webhook",
            "name": name.lower(),
            "guild_id": ctx.guild.id
        })
        if not (data and data["value"]):
            await bot.true_send_error(
                ctx=ctx,
                error="other_webhook_not_exists",
                who=tagged_dname(ctx.author),
                name=name
            )
            return

        text, em = get_embed(value)

        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(data["value"], adapter=AsyncWebhookAdapter(session))
            try:
                await webhook.send(content=text, embed=em)
            except discord.Forbidden:
                await self.bot.true_send_error(ctx=ctx, error="wh_cant_execute")
            except Exception as e:
                logger.info(f"webhook: Unknown exception ({e}) - {ctx.guild.name} [{ctx.guild.id}]")


    @commands.command(pass_context=True, name="ban", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def ban_(self, ctx, user: discord.Member, *, reason: str="-"):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "ban")
        if not ctx or not is_admin(ctx.author): return
        em = ctx.embed.copy()

        try:
            await user.ban(reason=reason)
        except discord.Forbidden:
            await self.bot.true_send_error(ctx=ctx, error="admin_didnt_manage_to_ban", user=user.mention)
            return
        except Exception as e:
            logger.info(f"ban: Unknown exception ({e}) - {ctx.guild.name} [{ctx.guild.id}]")
            return

        em.color = COLORS["ban"]
        em.set_author(name=bot.get_locale(ctx.lang, "admin_user_ban"), icon_url=str(ctx.guild.icon_url))
        em.add_field(
            name=bot.get_locale(ctx.lang, "admin_user"),
            value=user.mention,
            inline=True
        )
        em.add_field(
            name=bot.get_locale(ctx.lang, "admin_moderator"),
            value=ctx.author.mention,
            inline=True
        )
        em.add_field(
            name=bot.get_locale(ctx.lang, "admin_reason"),
            value=reason,
            inline=True
        )
        em.set_footer(text=f"ID: {user.id}")
        em.timestamp = datetime.utcnow()

        await bot.true_send(ctx=ctx, embed=em)
        return


    @commands.command(pass_context=True, name="unban", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def unban_(self, ctx, user: str, *, reason: str="-"):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "ban")
        if not ctx or not is_admin(ctx.author): return
        em = ctx.embed.copy()

        try:
            user = await ctx.guild.fetch_ban(user)
            user = user.user
        except discord.Forbidden:
            await self.bot.true_send_error(ctx=ctx, error="admin_didnt_manage_to_unban", user=user.mention)
            return
        except discord.NotFound:
            await self.bot.true_send_error(ctx=ctx, error="global_not_mention_on_user")
            return
        except Exception as e:
            logger.info(f"unban: Unknown exception ({e}) - {ctx.guild.name} [{ctx.guild.id}]")
            return

        try:
            await user.unban(reason=reason)
        except discord.Forbidden:
            await self.bot.true_send_error(ctx=ctx, error="admin_didnt_manage_to_unban", user=user.mention)
            return
        except Exception as e:
            logger.info(f"ban: Unknown exception ({e}) - {ctx.guild.name} [{ctx.guild.id}]")
            return

        em.color = COLORS["unban"]
        em.set_author(name=bot.get_locale(ctx.lang, "admin_user_unban"), icon_url=str(ctx.guild.icon_url))
        em.add_field(
            name=bot.get_locale(ctx.lang, "admin_user"),
            value=user.mention,
            inline=True
        )
        em.add_field(
            name=bot.get_locale(ctx.lang, "admin_moderator"),
            value=ctx.author.mention,
            inline=True
        )
        em.add_field(
            name=bot.get_locale(ctx.lang, "admin_reason"),
            value=reason,
            inline=True
        )
        em.set_footer(text=f"ID: {user.id}")
        em.timestamp = datetime.utcnow()

        await bot.true_send(ctx=ctx, embed=em)
        return


    @commands.command(pass_context=True, name="kick", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def kick_(self, ctx, user: discord.Member, *, reason: str="-"):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "kick")
        if not ctx or not is_admin(ctx.author): return
        em = ctx.embed.copy()

        try:
            await user.kick(reason=reason)
        except discord.Forbidden:
            await self.bot.true_send_error(ctx=ctx, error="admin_didnt_manage_to_kick", user=user.mention)
            return
        except Exception as e:
            logger.info(f"ban: Unknown exception ({e}) - {ctx.guild.name} [{ctx.guild.id}]")
            return

        em.color = COLORS["kick"]
        em.set_author(name=bot.get_locale(ctx.lang, "admin_user_kick"), icon_url=str(ctx.guild.icon_url))
        em.add_field(
            name=bot.get_locale(ctx.lang, "admin_user"),
            value=user.mention,
            inline=True
        )
        em.add_field(
            name=bot.get_locale(ctx.lang, "admin_moderator"),
            value=ctx.author.mention,
            inline=True
        )
        em.add_field(
            name=bot.get_locale(ctx.lang, "admin_reason"),
            value=reason,
            inline=True
        )
        em.set_footer(text=f"ID: {user.id}")
        em.timestamp = datetime.utcnow()

        await bot.true_send(ctx=ctx, embed=em)
        return

    @commands.command(pass_context=True, name="createvoice", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def createvoice_(self, ctx):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx or not is_admin(ctx.author): return

        try:
            guild = ctx.guild
            overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=True, connect=True)}
            category = await guild.create_category_channel(
                "Private Voices",
                overwrites=overwrites,
                reason="Tomori Private Voices"
            )
            voice = await guild.create_voice_channel(
                "Create Voice [+]",
                overwrites=overwrites,
                category=category,
                reason="Tomori Private Voices"
            )
            await bot.db.update({
                "create_voice_id": voice.id,
                "create_voice_category": category.id
            }, "guilds", where={"id": guild.id})
        except discord.Forbidden:
            await self.bot.true_send_error(ctx=ctx, error="createvoice_cant_create")
            return
        except Exception as e:
            logger.info(f"createvoice: Unknown exception ({e}) - {ctx.guild.name} [{ctx.guild.id}]")
            return

    @commands.command(pass_context=True, name="synclvlup", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def synclvlup_(self, ctx):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx or not is_admin(ctx.author): return

        await bot.true_send(ctx=ctx, content="⌛")

        roles_data = await bot.db.select_all("*", "mods", where={
            "guild_id": ctx.guild.id,
            "type": "lvlup"
        })
        roles_data = sorted(roles_data, key=lambda k:int(k["condition"]), reverse=False)

        for member in ctx.guild.members:
            try:
                member_data = await bot.db.select("*", "users", where={
                    "id": member.id,
                    "guild": ctx.guild.id
                })

                lvl = get_lvl(member_data["xp"]) if member_data["xp"] else 0
                roles = member.roles

                if roles_data:
                    for role in member.roles:
                        if any(role.id == int(row["value"]) for row in roles_data):
                            roles.pop(roles.index(role))
                    role = ctx.guild.get_role(ctx.const["autorole"]) if ctx.const["autorole"] else None
                    for row in roles_data:
                        if row["condition"] == "0":
                            new_role = ctx.guild.get_role(int(row["value"]))
                            if new_role and not new_role in roles:
                                roles.append(new_role)
                            continue
                        if lvl < int(row["condition"]):
                            break
                        new_role = ctx.guild.get_role(int(row["value"]))
                        if new_role:
                            role = new_role

                    if role:
                        roles.append(role)

                try:
                    await member.edit(roles=roles, reason="Tomori sync lvlup")
                except discord.Forbidden:
                    await self.bot.channel_send_error(channel=member, error="cant_update_user_roles", who=member.mention)
                except Exception as e:
                    logger.info(f"check_lvlup: Unknown exception ({e}) - {ctx.guild.name} [{ctx.guild.id}] Roles: {', '.join(roles)}")
            except Exception as e:
                pass

        await bot.true_send(ctx=ctx, content="🆗")
        return


def setup(bot):
    bot.add_cog(Admin(bot))
