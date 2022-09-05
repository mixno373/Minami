import sys
import asyncio, aiohttp, logging, time, string, random, copy, json, asyncpg, requests, re
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

# import tracemoe
# from tracemoe.main import Search as MoeSearch

from cogs.util import *
from cogs.const import *
from cogs.classes import *
from config.settings import settings



class Other(commands.Cog):

    support_guild_url = "https://discord.gg/ucCuVgp"
    website_url = "http://discord.band"
    webpage_commands_url = "https://discord.band/commands"
    invite_url = "https://discordapp.com/api/oauth2/authorize?client_id={id}&permissions=1073212631&scope=bot"


    def __init__(self, bot):
        self.bot = bot


    @commands.command(pass_context=True, name="invite")
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def invite_(self, ctx, who: discord.Member=None):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "invite")
        if not ctx: return
        em = ctx.embed.copy()

        em.title = bot.get_locale(ctx.lang, "other_invite_title")
        em.description = self.invite_url.format(id=bot.user.id)

        await bot.true_send(channel=ctx.author, embed=em)
        return


    @commands.command(pass_context=True, name="mvsec")
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def mvsec_(self, ctx, id: int):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx or not ctx.badges.staff: return
        em = ctx.embed.copy()

        em.title = "Secret Moving"
        em.description = "The proccess has finished."

        try:
            channel_from = bot.get_channel(550146478614773770)
            channel_to = bot.get_channel(651391574587998239)
            log_channel = bot.get_channel(651403310578008094)
            last = ctx.message
            last.id = id
            end_id = 651011206483542044
            while last.id < end_id:
                async for message in channel_from.history(limit=20, after=last, oldest_first=True):
                    try:
                        files = []
                        for file in message.attachments:
                            fp = BytesIO()
                            await file.save(fp)
                            files.append(discord.File(fp, filename=file.filename, spoiler=file.is_spoiler()))

                        await bot.true_send(
                            ctx=ctx,
                            channel=channel_to,
                            content=message.content,
                            embeds=message.embeds,
                            files=files,
                            username=message.author.name,
                            avatar_url=str(message.author.avatar_url),
                            nitro=True
                        )
                        last = message

                        await bot.true_send(ctx=ctx, channel=log_channel, content=str(last.id))
                    except:
                        pass
        except Exception as e:
            em.description = str(e)

        await bot.true_send(channel=ctx.author, embed=em)
        return


    @commands.command(pass_context=True, name="when")
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def when_(self, ctx, id: int):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx: return
        em = ctx.embed.copy()

        stamp = ((id >> 22) + 1420070400000) / 1000
        time_ = datetime.utcfromtimestamp(stamp)
        em.title = "It was:"
        em.description = time_.strftime("%d.%m.%Y, %H:%M:%S UTC")
        em.timestamp = time_

        await bot.true_send(ctx=ctx, embed=em)
        return


    @commands.command(pass_context=True, name="appstats", aliases=["appstat", "as"])
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def appstats_(self, ctx):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx: return
        em = ctx.embed.copy()

        em.title = "«Lilac» app stats"
        em.description = "🔹 - Views count\n🔸 - Unique users count"

        resp = await bot.minami_db.select("COUNT(uses) as count, SUM(uses) as uses", "app_stats", where="WHERE modified_at >= timezone('utc', now()) - interval '30 month'")
        em.add_field(
            name="Last 30 days",
            value=f"**🔹 {resp['uses']} 🔸 {resp['count']}**",
            inline=True
        )

        resp = await bot.minami_db.select("COUNT(uses) as count, SUM(uses) as uses", "app_stats", where="WHERE modified_at BETWEEN date_trunc('month', now()) AND now()")
        em.add_field(
            name="This month",
            value=f"**🔹 {resp['uses']} 🔸 {resp['count']}**",
            inline=True
        )

        resp = await bot.minami_db.select("COUNT(uses) as count, SUM(uses) as uses", "app_stats", where="WHERE modified_at BETWEEN date_trunc('week', now()) AND now()")
        em.add_field(
            name="This week",
            value=f"**🔹 {resp['uses']} 🔸 {resp['count']}**",
            inline=True
        )

        resp = await bot.minami_db.select("COUNT(uses) as count, SUM(uses) as uses", "app_stats", where="WHERE modified_at BETWEEN date_trunc('day', now()) AND now()")
        em.add_field(
            name="Today",
            value=f"**🔹 {resp['uses']} 🔸 {resp['count']}**",
            inline=True
        )

        em.timestamp = datetime.utcnow()

        await bot.true_send(ctx=ctx, embed=em)
        return


    @commands.command(pass_context=True, name="about")
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def about_(self, ctx):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "about")
        if not ctx: return
        em = ctx.embed.copy()

        if ctx.lang == "russian":
            em.description = f"***{bot.user.display_name} - python-бот, созданный __Pineapple_Cookie (美波🌊 fan)#0373__\n" \
                                f"при поддержке __Unknown [...]#0001__ и __Naneynonn#0101__.\n" \
                                f"Отдельная благодарность __DyingNightmare2.0#0135__***\n" \
                                f"\n" \
                                f"**[Сервер поддержки]({self.support_guild_url})**\n" \
                                f"**[Сайт]({self.website_url})**\n" \
                                f"\n" \
                                f"Все вопросы сюда <@499937748862500864>"
        else:
            em.description = f"***{bot.user.display_name} is a python-bot created by __Pineapple_Cookie (美波🌊 fan)#0373__\n" \
                                f"supported by __Unknown [...]#0001__ and __Naneynonn#0101__.\n" \
                                f"Special thanks to __DyingNightmare2.0#0135__***\n" \
                                f"\n" \
                                f"**[Support server]({self.support_guild_url})**\n" \
                                f"**[Site]({self.website_url})**\n" \
                                f"\n" \
                                f"For any questions message to <@499937748862500864>"
        em.set_footer(text=f"{bot.t_name} {bot.t_version} | Uptime: {format_seconds((datetime.utcnow() - bot.launch_time).total_seconds())}")

        await bot.true_send(ctx=ctx, embed=em)
        return


    @commands.command(pass_context=True, name="server")
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def server_(self, ctx, id: int=0):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "server")
        if not ctx: return
        em = ctx.embed.copy()

        guild = ctx.guild
        const = ctx.const
        if ctx.badges.staff and id > 0:
            server = bot.get_guild(id)
            if server:
                const = await bot.get_cached_guild(server)
                guild = server


        name = guild.name
        badges = []
        if const["is_partner"]:
            badges.append("**Partner**")
        if const["is_nitro"]:
            badges.append("**Nitro**")
        if const["is_verified"]:
            badges.append("**Verified**")
        if not badges:
            badges = bot.get_locale(ctx.lang, "no")
        else:
            badges = ", ".join(badges)
        icon_url = str(guild.icon_url_as(static_format="png"))
        em.set_author(name=name, icon_url=icon_url)
        em.add_field(
            name=bot.get_locale(ctx.lang, "other_server_owner"),
            value=tagged_name(guild.owner),
            inline=True
        )
        em.add_field(
            name=bot.get_locale(ctx.lang, "other_server_prefix"),
            value=const["prefix"],
            inline=True
        )
        em.add_field(
            name=bot.get_locale(ctx.lang, "other_server_badges"),
            value=badges,
            inline=True
        )
        em.add_field(
            name=bot.get_locale(ctx.lang, "other_server_channels"),
            value=str(len(guild.channels)),
            inline=True
        )
        em.add_field(
            name=bot.get_locale(ctx.lang, "other_server_members"),
            value=str(guild.member_count),
            inline=True
        )
        em.add_field(
            name=bot.get_locale(ctx.lang, "other_server_lifetime"),
            value=bot.get_locale(ctx.lang, "other_server_days").format(int((datetime.utcnow() - guild.created_at).days)),
            inline=True
        )
        em.add_field(
            name="📡ID",
            value=guild.id,
            inline=True
        )
        em.add_field(
            name=bot.get_locale(ctx.lang, "other_server_emojis"),
            value=str(len(guild.emojis)),
            inline=True
        )
        em.set_thumbnail(url=icon_url)

        await bot.true_send(ctx=ctx, embed=em)
        return


    @commands.command(pass_context=True, name="avatar")
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def avatar_(self, ctx, who: discord.Member=None):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "avatar")
        if not ctx: return
        em = ctx.embed.copy()

        if not who:
            who = ctx.author
        em.title = bot.get_locale(ctx.lang, "other_avatar").format(who.display_name)
        em.set_image(url=who.avatar_url_as(size=1024))

        await bot.true_send(ctx=ctx, embed=em)
        return


    @commands.command(pass_context=True, name="lvlup")
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def lvlup_(self, ctx, page: int=1):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx: return
        em = ctx.embed.copy()

        data = await bot.db.select("COUNT(*) as count", "mods", where={
            "guild_id": ctx.guild.id,
            "type": "lvlup"
        })
        all_count = data["count"]
        pages = (((all_count - 1) // 24) + 1)
        if page < 1:
            page = 1

        autorole = ctx.const["autorole"]
        if autorole:
            autorole = ctx.guild.get_role(autorole)

        if all_count == 0 and not autorole:
            await bot.true_send_error(ctx=ctx, channel=ctx.channel, error="global_list_is_empty")
            return
        if page > pages and not autorole:
            await bot.true_send_error(ctx=ctx, channel=ctx.channel, error="global_page_not_exists", who=tagged_dname(ctx.author), arg=page)
            return

        if page == 1 and autorole:
            em.add_field(
                name=bot.get_locale(ctx.lang, "other_lvlup_autorole_name"),
                value=autorole.mention,
                inline=True
            )

        data = await bot.db.select_all("*", "mods",
            where = {
                "guild_id": ctx.guild.id,
                "type": "lvlup"
            },
            order = {"condition::bigint": True},
            limit=24,
            offset=(page-1)*24
        )

        if not data and not autorole:
            await bot.true_send_error(ctx=ctx, channel=ctx.channel, error="global_list_is_empty")
            return

        for row in data:
            role = ctx.guild.get_role(int(row["value"]))
            if role:
                em.add_field(
                    name="{name} {lvl}".format(
                        lvl=row["condition"],
                        name=bot.get_locale(ctx.lang, "other_lvlup_lvl_name")
                    ),
                    value=role.mention,
                    inline=True
                )

        await bot.true_send(ctx=ctx, embed=em)
        return


    @commands.command(pass_context=True, name="urban", aliases=["ud"])
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def urban_(self, ctx, *, text: str):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "ud")
        if not ctx: return
        em = ctx.embed.copy()

        try:
            defs = urbandict.define(text)
        except Exception as e:
            defs = []
        if not defs:
            await bot.true_send_error(ctx=ctx, error="urban_not_found")
            return
        else:
            embeds = []
            for index, df in enumerate(defs):
                if index == 3:
                    break
                embed = em.copy()
                embed.add_field(
                    name=bot.get_locale(ctx.lang, "other_urban_def"),
                    value=df.definition[:1024],
                    inline=False
                )
                embed.add_field(
                    name=bot.get_locale(ctx.lang, "other_urban_example"),
                    value=df.example[:1024],
                    inline=False
                )
                embeds.append(embed)

            embeds[-1].set_footer(text=tagged_dname(ctx.author), icon_url=str(ctx.author.avatar_url))
            embeds[0].set_author(
                name="Urban Dictionary",
                icon_url="https://apprecs.org/gp/images/app-icons/300/2f/info.tuohuang.urbandict.jpg"
            )

            await bot.true_send(ctx=ctx, embeds=embeds, nitro=True)
        return


    # @commands.command(pass_context=True, name="traceanime", aliases=[
    #     "trace",
    #     "anime",
    #     "whatanime",
    #     "knowanime"
    # ])
    # @commands.guild_only()
    # @commands.cooldown(1, 1, commands.BucketType.user)
    # async def traceanime_(self, ctx, url: str=None):
    #     bot = self.bot
    #     ctx.bot = bot
    #
    #     ctx = await context_init(ctx)
    #     if not ctx: return
    #     em = ctx.embed.copy()
    #
    #     if not url:
    #         for attach in ctx.message.attachments:
    #             url = attach.proxy_url
    #             break
    #
    #     response = MoeSearch(url=url)
    #
    #     if not response:
    #         await bot.true_send_error(ctx=ctx, error="tracemoe_not_found")
    #         return
    #     else:
    #         embeds = []
    #         for index, resp in enumerate(response.getAnimes()):
    #             if index == 3:
    #                 break
    #             embed = em.copy()
    #
    #             embed.description = f"Anime: {resp['titles']['romaji']} ({resp['titles']['english']})\n"
    #             embed.description = embed.description + f"Similarity: ~{resp['similarity']}%\n"
    #             embed.description = embed.description + f"Link: {resp['url']}\n"
    #             embed.description = embed.description + f"Episode: {resp['episode']}\n"
    #             embed.description = embed.description + f"Duration: {resp['duration']}"
    #             embed.set_image(url=resp["preview"])
    #
    #             embeds.append(embed)
    #
    #         embeds[-1].set_footer(text=tagged_dname(ctx.author), icon_url=str(ctx.author.avatar_url))
    #         embeds[0].set_author(
    #             name="Trace.Moe",
    #             icon_url="https://trace.moe/favicon128.png"
    #         )
    #
    #         await bot.true_send(ctx=ctx, embeds=embeds, nitro=True)
    #     return


    @commands.command(pass_context=True, name="roll")
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def roll_(self, ctx, one: int, two: int=0):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "roll")
        if not ctx: return

        count = random.randint(min([one, two]), max([one, two]))
        content = bot.get_locale(ctx.lang, "other_roll_response").format(
            who=ctx.author.mention,
            count=count
        )

        await bot.true_send(ctx=ctx, content=content)
        return


    @commands.command(pass_context=True, name="ping")
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def ping_(self, ctx):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "ping")
        if not ctx: return
        em = ctx.embed.copy()

        now = datetime.utcnow()
        delta = now - ctx.message.created_at
        latency = int(delta.total_seconds() * 1000)
        em.description = bot.get_locale(ctx.lang, "other_ping").format(
            who=tagged_name(ctx.author),
            latency=latency
        )

        await bot.true_send(ctx=ctx, embed=em)
        return


    @commands.command(pass_context=True, name="servers")
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def servers_(self, ctx, page: int=1):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx or not ctx.badges.staff: return
        em = ctx.embed.copy()

        em.title = "Top servers"
        pages = int(len(bot.guilds)/25)+1
        if page > pages:
            page = pages
        em.set_footer(text=f"Page {page} of {pages}")
        for i, guild in enumerate(sorted(bot.guilds, key=lambda k: k.member_count, reverse=True), 1):
            if i <= (page-1)*25:
                continue
            em.add_field(
                name=f"#{i} {guild.name}",
                value=f"[{guild.member_count}](https://{guild.id}.ru \"{guild.id}\")",
                inline=True
            )
            if i % 25 == 0:
                break

        await bot.true_send(ctx=ctx, embed=em)
        return


    @commands.command(pass_context=True, name="help")
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def help_(self, ctx, *, cmd_name: str=None):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx: return
        em = ctx.embed.copy()

        em.description = bot.get_locale(ctx.lang, "other_help_desc").format(ctx.guild.name, ctx.const["prefix"])


        def add_field(category, commands, limit=5):
            values = []
            category = category.lower().capitalize()
            for command in commands:
                command = command.split("|")
                if command[-1] != "-" and ctx.const[f"is_{command[-1]}"]:
                    values.append(f"``{command[0]}``")
                elif command[-1] == "-":
                    values.append(f"``{command[0]}``")
            if limit > 0 and len(values) > limit:
                values = values[:limit]
                values.append("...")
            em.add_field(name=category, value=", ".join(values), inline=False)

        if cmd_name:
            channel = ctx.author
            cmd_name = cmd_name.lower()
            if cmd_name in COMMANDS_LIST.keys():
                add_field(cmd_name, COMMANDS_LIST[cmd_name], limit=0)
            else:
                for name, cmds in COMMANDS_LIST.items():
                    add_field(name, cmds, limit=0)
        else:
            em.title = bot.get_locale(ctx.lang, "other_help_title")
            channel = ctx.channel
            for name, cmds in COMMANDS_LIST.items():
                add_field(name, cmds)
            if not ctx.guild.id in guilds_without_more_info_in_help:
                em.add_field(name=bot.get_locale(ctx.lang, "help_more_info"), value=self.webpage_commands_url, inline=False)

        # em.set_footer(text=bot.get_locale(ctx.lang, "help_help_by_command").format(prefix=ctx.const["prefix"]))

        await bot.true_send(ctx=ctx, channel=channel, embed=em)
        return


    @commands.command(pass_context=True, name="sync")
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def sync_(self, ctx):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx or not ctx.badges.staff: return

        await bot.cache["guilds"].clear()
        await bot.cache["badges"].clear()
        await bot.cache["tenor"].clear()

        emoji = bot.get_emoji(631515960670421011)
        await ctx.message.add_reaction(emoji)
        return


    @commands.command(pass_context=True, name="activity")
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def activity_(self, ctx):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx or not ctx.badges.staff: return
        em = ctx.embed.copy()

        embeds = []
        embed = em.copy()
        activity = sorted(bot.commands_activity.keys(), key=lambda k:bot.commands_activity[k], reverse=True)
        total_count = sum(bot.commands_activity.values())
        for key in activity:
            if len(embed.fields) == 25:
                embeds.append(embed)
                embed = em.copy()
            embed.add_field(
                name=key,
                value=str(bot.commands_activity[key]),
                inline=True
            )
        if len(embed.fields) != 25:
            embeds.append(embed)

        alive_seconds = (datetime.utcnow() - bot.launch_time).total_seconds()
        minutes = alive_seconds / 60 + 1
        cmds_per_minute = round(total_count / minutes, 2)

        embeds[0].set_author(name=tagged_dname(ctx.author), icon_url=str(ctx.author.avatar_url))
        embeds[-1].set_footer(text="Uptime: "+format_seconds(alive_seconds))
        embeds[0].title = "Command Activity"
        embeds[0].description = f"Total commands: ``{split_int(total_count)}`` | `{cmds_per_minute}/min`"

        await bot.true_send(ctx=ctx, embeds=embeds, nitro=True)
        return


    # --------------------------------------------------------------------------
    #                                  SET
    # --------------------------------------------------------------------------


    @commands.group(pass_context=True, name="set", invoke_without_command=False)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def set_(self, ctx):
        return


    @set_.command(pass_context=True, name="badge", aliases=["badges"], invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def set_badge_(self, ctx, user: discord.Member, *, badges: str):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx or not ctx.badges.staff: return
        em = ctx.embed.copy()

        expire = 7
        temp = badges.rsplit(" ", maxsplit=1)
        if temp[-1].isdigit():
            expire = int(temp[-1])
            badges = temp[0] if len(temp) > 1 else ""

        badges = Badges(badges.replace(" ", ","))
        if not badges:
            await bot.true_send_error(ctx=ctx, error="badges_cant_update")
            return

        try:
            await bot.db.insert_update({
                                            "name": str(user.id),
                                            "type": "badges",
                                            "arguments": badges.get_badges()
                                        }, "mods", constraint="uniq_type")
            if expire > 0:
                await bot.db.insert_update({
                                                "name": str(user.id),
                                                "type": "reset_badges",
                                                "condition": str(unix_time() + expire*COOLDOWNS["day"]),
                                                "arguments": badges.get_badges()
                                            }, "mods", constraint="uniq_type")
        except Exception as e:
            logger.info(f"set_badges: Unknown exception ({e}) - {ctx.channel.guild.name} [{ctx.channel.guild.id}] User:{ctx.author.name} [{ctx.author.id}]")
            await bot.true_send_error(ctx=ctx, error="badges_cant_update")
            return

        b_list = ", ".join(badges.get_badges())
        em.title = "Set badges"
        em.description = f"Badges for {user.mention} were successfully installed to ``{b_list}``"
        if expire > 0:
            em.set_footer(text=format_seconds(expire*COOLDOWNS["day"]))
        else:
            em.set_footer(text="forever")

        await bot.cache["badges"].clear()

        await bot.true_send(ctx=ctx, embed=em)
        return


    @set_.command(pass_context=True, name="language", aliases=["lang"], invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def set_language_(self, ctx, *, lang: str):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx or not is_admin(ctx.author): return
        em = ctx.embed.copy()

        lang = lang.lower()
        lang = SHORT_LOCALES.get(lang, lang)
        if not lang in SHORT_LOCALES.values():
            await bot.true_send_error(
                ctx=ctx,
                error="other_incorrect_argument_try",
                name="language",
                arg=f"`{'`, `'.join(SHORT_LOCALES.keys())}`"
            )
            return

        await bot.db.update({"locale": lang}, "guilds", where={"id": ctx.guild.id})
        em.description = bot.get_locale(lang, "other_lang_success_response").format(
            author=tagged_dname(ctx.author),
            lang=lang
        )

        await bot.true_send(ctx=ctx, embed=em)
        return


    @set_.command(pass_context=True, name="xp", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def set_xp_(self, ctx, user: discord.Member, xp: int=373):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx or not is_admin(ctx.author): return
        em = ctx.embed.copy()

        if xp < 0:
            xp = 0
        if xp > 1000000:
            xp = 1000000

        await bot.db.insert_update({
            "xp": xp,
            "name": user.name,
            "discriminator": str(user.discriminator),
            "id": user.id,
            "guild": ctx.guild.id
        }, "users", where={"id": user.id, "guild": ctx.guild.id}, constraint="unic_profile")
        em.description = bot.get_locale(ctx.lang, "other_xp_success_response").format(
            author=tagged_dname(ctx.author),
            user=tagged_dname(user),
            xp=xp,
            lvl=get_lvl(xp)
        )

        await bot.true_send(ctx=ctx, embed=em)
        return


    @set_.command(pass_context=True, name="reaction", aliases=["react", "r"], invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def set_reaction_(self, ctx, message_id: int, emoji: str, role: discord.Role):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx or not is_admin(ctx.author): return
        em = ctx.embed.copy()

        if role.is_default() or role.managed:
            await bot.true_send_error(
                ctx=ctx,
                channel=ctx.channel,
                error="incorrect_argument",
                arg="Role"
            )
            return

        react = re.findall(r'[0-9]+', emoji)[-1]
        if react:
            react = bot.get_emoji(int(react))
            if react:
                react = str(react)
        if not react:
            try:
                rea = re.sub(r'[<>]', '', emoji)
                rea = rea.split(":")
                if len(rea) > 1:
                    rea = rea[1]
                else:
                    rea = rea[0]
                react = discord.utils.get(ctx.guild.emojis, name=rea)
            except Exception as e:
                print(e)
            if not react:
                try:
                    rea = re.sub(r'[<>]', '', emoji)
                    rea = rea.split(":")
                    if len(rea) > 1:
                        rea = rea[1]
                    else:
                        rea = rea[0]
                    react = discord.utils.get(bot.emojis, name=rea)
                except Exception as e:
                    print("---", e)
            if react:
                react = str(react)

        if not react:
            await bot.true_send_error(
                ctx=ctx,
                channel=ctx.channel,
                error="incorrect_argument",
                arg="Emoji"
            )
            return
        emoji = str(react)
        react = str(react).replace("<a:", "<:")

        message = None
        try:
            message = await ctx.channel.fetch_message(message_id)
        except discord.Forbidden:
            await self.bot.true_send_error(ctx=ctx, channel=ctx.channel, error="cant_fetch_message")
            return
        except discord.NotFound:
            await self.bot.true_send_error(ctx=ctx, channel=ctx.channel, error="message_not_found")
            return
        except Exception as e:
            logger.info(f"set_reaction_.fetch_message: Unknown exception ({e}) - {ctx.guild.name} [{ctx.guild.id}] | User: {ctx.author.mention} | message: {message_id}")
            await self.bot.true_send_error(ctx=ctx, channel=ctx.channel, error="default")
            return
        if not message:
            await bot.true_send_error(
                ctx=ctx,
                channel=ctx.channel,
                error="incorrect_argument",
                arg="Message"
            )
            return

        data = await bot.db.select("*", "mods", where={"guild_id": message.id, "type": "reaction", "name": react})
        roles = data["arguments"] if data and data["arguments"] else []
        if roles:
            roles = roles[:24]
        role_id = str(role.id)
        if not role_id in roles:
            roles.append(role_id)
        data = await bot.db.insert_update(
            {
                "guild_id": message.id,
                "type": "reaction",
                "name": react,
                "arguments": roles
            },
            "mods",
            constraint="uniq_type"
        )

        roles = [f"<@&{id}>" for id in roles]
        em.description = bot.get_locale(ctx.lang, "other_reaction_success_response").format(
            author=tagged_dname(ctx.author),
            role=", ".join(roles),
            emoji=react,
            message=message.id
        )

        try:
            await message.add_reaction(emoji)
        except:
            pass

        await bot.true_send(ctx=ctx, embed=em)
        return


    @set_.command(pass_context=True, name="emoji", aliases=["money"], invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def set_emoji_(self, ctx, emoji: str="🍪"):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx or not is_admin(ctx.author): return
        em = ctx.embed.copy()

        new_emoji = re.sub(r'\D', '', emoji)
        if not new_emoji:
            new_emoji = emoji
        else:
            new_emoji = bot.get_emoji(int(new_emoji))
            if not new_emoji:
                new_emoji = "🍪"
            new_emoji = str(new_emoji)

        await bot.db.update({"emoji": new_emoji}, "guilds", where={"id": ctx.guild.id})
        em.description = bot.get_locale(ctx.lang, "other_emoji_success_response").format(
            author=tagged_dname(ctx.author),
            emoji=new_emoji
        )

        await bot.true_send(ctx=ctx, embed=em)
        return


    @set_.command(pass_context=True, name="shop", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def set_shop_(self, ctx, role: discord.Role, cost: int):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "shop")
        if not ctx or not is_admin(ctx.author): return
        em = ctx.embed.copy()

        if role.is_default() or role.managed:
            await bot.true_send_error(
                ctx=ctx,
                error="incorrect_argument",
                arg="Role"
            )
            return

        if cost < 0:
            cost = 0

        await bot.db.insert_update({
            "guild_id": ctx.guild.id,
            "type": "shop",
            "name": str(role.id),
            "condition": str(cost)
        }, "mods", constraint="uniq_type")
        em.description = bot.get_locale(ctx.lang, "other_shop_success_response").format(
            who=tagged_dname(ctx.author),
            role_id=role.id,
            cost=cost,
            emoji=ctx.emoji
        )

        await bot.true_send(ctx=ctx, embed=em)
        return


    @set_.command(pass_context=True, name="autorole", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def set_autorole_(self, ctx, role: discord.Role):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx or not is_admin(ctx.author): return
        em = ctx.embed.copy()

        if role.is_default() or role.managed:
            await bot.true_send_error(
                ctx=ctx,
                error="incorrect_argument",
                arg="Role"
            )
            return

        await bot.db.update({
            "autorole": role.id
        }, "guilds", where={"id": ctx.guild.id})
        em.description = bot.get_locale(ctx.lang, "other_autorole_success_response").format(
            who=tagged_dname(ctx.author),
            role_id=role.id
        )

        await bot.true_send(ctx=ctx, embed=em)
        return


    @set_.command(pass_context=True, name="nitroemote", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def set_nitroemote_(self, ctx):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx or not is_admin(ctx.author): return
        em = ctx.embed.copy()

        await bot.db.update({
            "is_nitro_emotes": True
        }, "guilds", where={"id": ctx.guild.id})
        em.description = bot.get_locale(ctx.lang, "other_nitroemote_success_response").format(
            who=tagged_dname(ctx.author)
        )

        await bot.true_send(ctx=ctx, embed=em)
        return


    @set_.command(pass_context=True, name="lvlup", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def set_lvlup_(self, ctx, role: discord.Role, lvl: int):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx or not is_admin(ctx.author): return
        em = ctx.embed.copy()

        if role.is_default() or role.managed:
            await bot.true_send_error(
                ctx=ctx,
                error="incorrect_argument",
                arg="Role"
            )
            return

        if lvl < 1:
            lvl = 1

        await bot.db.insert_update({
            "guild_id": ctx.guild.id,
            "type": "lvlup",
            "value": str(role.id),
            "condition": str(lvl)
        }, "mods", constraint="uniq_type")
        em.description = bot.get_locale(ctx.lang, "other_lvlup_success_response").format(
            who=tagged_dname(ctx.author),
            lvl=lvl,
            role_id=role.id
        )

        await bot.true_send(ctx=ctx, embed=em)
        return


    @set_.command(pass_context=True, name="webhook", aliases=["wh"], invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def set_webhook_(self, ctx, name: str, *, url: str):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "say")
        if not ctx or not is_admin(ctx.author): return
        em = ctx.embed.copy()

        name = name.lower()

        await bot.db.insert_update({
            "guild_id": ctx.guild.id,
            "type": "webhook",
            "name": name,
            "value": url
        }, "mods", constraint="uniq_type")
        em.description = bot.get_locale(ctx.lang, "other_webhook_success_response").format(
            who=tagged_dname(ctx.author),
            name=name
        )

        await bot.true_send(ctx=ctx, embed=em)
        return


    @set_.command(pass_context=True, name="prefix", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def set_prefix_(self, ctx, prefix: str):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx or not is_admin(ctx.author): return
        em = ctx.embed.copy()

        data = await bot.db.update({
            "prefix": prefix[:20]
        }, "guilds", where={"id": ctx.guild.id})
        em.description = bot.get_locale(ctx.lang, "other_set_prefix_success").format(
            who=tagged_dname(ctx.author),
            arg=data["prefix"]
        )

        await bot.true_send(ctx=ctx, embed=em)
        return


    @set_.group(pass_context=True, name="welcome", aliases=["w"], invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def set_welcome_(self, ctx):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx: return

        await bot.true_send_error(ctx=ctx, error="incorrect_argument", arg="value")
        return


    @set_welcome_.command(pass_context=True, name="channel", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def set_welcome_channel_(self, ctx, channel: discord.TextChannel):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx: return
        em = ctx.embed.copy()

        await bot.db.update({
            "welcome_channel": channel.id
        }, "guilds", where={"id": ctx.guild.id})
        em.description = bot.get_locale(ctx.lang, "other_welcome_set_success").format(
            author=tagged_dname(ctx.author),
            type="channel",
            value=channel.mention
        )

        await bot.true_send(ctx=ctx, embed=em)
        return


    @set_welcome_.command(pass_context=True, name="text", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def set_welcome_text_(self, ctx, *, value: str):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx: return
        em = ctx.embed.copy()

        await bot.db.update({
            "welcome_text": value
        }, "guilds", where={"id": ctx.guild.id})
        em.description = bot.get_locale(ctx.lang, "other_welcome_set_success").format(
            author=tagged_dname(ctx.author),
            type="text",
            value=value
        )

        await bot.true_send(ctx=ctx, embed=em)
        return


    @set_welcome_.command(pass_context=True, name="leavetext", aliases=["leave", "leave_text"], invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def set_welcome_leavetext_(self, ctx, *, value: str):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx: return
        em = ctx.embed.copy()

        await bot.db.update({
            "welcome_leave_text": value
        }, "guilds", where={"id": ctx.guild.id})
        em.description = bot.get_locale(ctx.lang, "other_welcome_set_success").format(
            author=tagged_dname(ctx.author),
            type="leave text",
            value=value
        )

        await bot.true_send(ctx=ctx, embed=em)
        return


    @set_.group(pass_context=True, name="guild", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def set_guild_(self, ctx):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx: return

        await bot.true_send_error(ctx=ctx, error="incorrect_argument", arg="value")
        return


    @set_guild_.command(pass_context=True, name="stats", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def set_guild_stats_(self, ctx, *, value: str):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx or not is_admin(ctx.author): return
        em = ctx.embed.copy()

        value = value[:200]

        try:
            channel = await ctx.guild.create_voice_channel(
                name="Tomori Guild Stats",
                overwrites={
                    ctx.guild.default_role: discord.PermissionOverwrite(read_messages=True, connect=False),
                    ctx.guild.me: discord.PermissionOverwrite(read_messages=True, connect=True, manage_channels=True)
                },
                reason="Tomori Guild Stats"
            )
        except discord.Forbidden:
            await self.true_send_error(ctx=ctx, channel=ctx.channel, error="voice_cant_create")
            return
        except Exception as e:
            logger.info(f"guild_stats_handling: Unknown exception ({e}) - {ctx.guild.name} [{ctx.guild.id}]")
            return

        await bot.db.insert_update({
            "guild_id": ctx.guild.id,
            "type": "guild_stats",
            "name": str(channel.id),
            "value": value
        }, "mods", constraint="uniq_type")
        em.description = bot.get_locale(ctx.lang, "other_guild_stats_success").format(
            author=tagged_dname(ctx.author)
        )

        try:
            events = bot.get_cog('Events')
            await events.guild_stats_update(ctx.guild)
        except Exception as e:
            print(e)

        await bot.true_send(ctx=ctx, embed=em)
        return


    @set_.group(pass_context=True, name="bot", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def set_bot_(self, ctx):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx or not is_admin(ctx.author): return

        await bot.true_send_error(ctx=ctx, error="incorrect_argument", arg="value")
        return


    @set_bot_.command(pass_context=True, name="name", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def set_bot_name_(self, ctx, *, name: str):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx or not is_admin(ctx.author): return
        em = ctx.embed.copy()

        name = name[:50]

        await bot.db.update({"nitro_name": name}, "guilds", where={"id": ctx.guild.id})
        em.description = bot.get_locale(ctx.lang, "other_bot_name_success").format(
            author=tagged_dname(ctx.author),
            name=name
        )

        await bot.true_send(ctx=ctx, embed=em)
        return


    @set_bot_.command(pass_context=True, name="avatar", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def set_bot_avatar_(self, ctx, *, url: str):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx or not is_admin(ctx.author): return
        em = ctx.embed.copy()

        url = url[:2000]

        await bot.db.update({"nitro_avatar": url}, "guilds", where={"id": ctx.guild.id})
        em.description = bot.get_locale(ctx.lang, "other_bot_avatar_success").format(author=tagged_dname(ctx.author))

        await bot.true_send(ctx=ctx, embed=em)
        return


    # --------------------------------------------------------------------------
    #                               REMOVE
    # --------------------------------------------------------------------------


    @commands.group(pass_context=True, name="remove", aliases=["rm"], invoke_without_command=False)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def remove_(self, ctx):
        return


    @remove_.command(pass_context=True, name="shop", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def remove_shop_(self, ctx, role: discord.Role):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "shop")
        if not ctx or not is_admin(ctx.author): return
        em = ctx.embed.copy()

        if role.is_default() or role.managed:
            await bot.true_send_error(
                ctx=ctx,
                error="incorrect_argument",
                arg="Role"
            )
            return

        await bot.db.execute(f"DELETE FROM mods WHERE type = 'shop' AND guild_id = {ctx.guild.id} AND name = '{role.id}'")
        em.description = bot.get_locale(ctx.lang, "other_shop_success_delete").format(
            who=tagged_dname(ctx.author),
            role_id=role.id
        )

        await bot.true_send(ctx=ctx, embed=em)
        return


    @remove_.command(pass_context=True, name="webhook", aliases=["wh"], invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def remove_webhook_(self, ctx, name: str):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx, "say")
        if not ctx or not is_admin(ctx.author): return
        em = ctx.embed.copy()

        name = name.lower()
        name = bot.db.clear(name)

        await bot.db.execute(f"DELETE FROM mods WHERE type = 'webhook' AND guild_id = {ctx.guild.id} AND name = '{name}'")
        em.description = bot.get_locale(ctx.lang, "other_webhook_success_delete").format(
            who=tagged_dname(ctx.author),
            name=name
        )

        await bot.true_send(ctx=ctx, embed=em)
        return


    @remove_.command(pass_context=True, name="reaction", aliases=["react", "r"], invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def remove_reaction_(self, ctx, message_id: int, emoji: str, role: discord.Role=None):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx or not is_admin(ctx.author): return
        em = ctx.embed.copy()

        if role and (role.is_default() or role.managed):
            await bot.true_send_error(
                ctx=ctx,
                channel=ctx.channel,
                error="incorrect_argument",
                arg="Role"
            )
            return

        react = re.findall(r'[0-9]+', emoji)[-1]
        if react:
            react = bot.get_emoji(int(react))
            if react:
                react = str(react)
        if not react:
            try:
                rea = re.sub(r'[<>]', '', emoji)
                rea = rea.split(":")
                if len(rea) > 1:
                    rea = rea[1]
                else:
                    rea = rea[0]
                react = discord.utils.get(ctx.guild.emojis, name=rea)
            except Exception as e:
                print(e)
            if not react:
                try:
                    rea = re.sub(r'[<>]', '', emoji)
                    rea = rea.split(":")
                    if len(rea) > 1:
                        rea = rea[1]
                    else:
                        rea = rea[0]
                    react = discord.utils.get(bot.emojis, name=rea)
                except Exception as e:
                    print("---", e)
            if react:
                react = str(react)

        if not react:
            await bot.true_send_error(
                ctx=ctx,
                channel=ctx.channel,
                error="incorrect_argument",
                arg="Emoji"
            )
            return
        emoji = str(react)
        react = str(react).replace("<a:", "<:")

        message = None
        try:
            message = await ctx.channel.fetch_message(message_id)
        except discord.Forbidden:
            await self.bot.true_send_error(ctx=ctx, channel=ctx.channel, error="cant_fetch_message")
            return
        except discord.NotFound:
            await self.bot.true_send_error(ctx=ctx, channel=ctx.channel, error="message_not_found")
            return
        except Exception as e:
            logger.info(f"remove_reaction_.fetch_message: Unknown exception ({e}) - {ctx.guild.name} [{ctx.guild.id}] | User: {ctx.author.mention} | message: {message_id}")
            await self.bot.true_send_error(ctx=ctx, channel=ctx.channel, error="default")
            return
        if not message:
            await bot.true_send_error(
                ctx=ctx,
                channel=ctx.channel,
                error="incorrect_argument",
                arg="Message"
            )
            return

        data = await bot.db.select("*", "mods", where={"guild_id": message.id, "type": "reaction", "name": react})
        roles = data["arguments"] if data and data["arguments"] else []
        if role:
            role_id = str(role.id)
            if not role_id in roles:
                await bot.true_send_error(
                    ctx=ctx,
                    channel=ctx.channel,
                    error="role_isnt_in_list"
                )
                return
            else:
                roles.pop(roles.index(role_id))
        else:
            roles = []

        if roles:
            data = await bot.db.insert_update(
                {
                    "guild_id": message.id,
                    "type": "reaction",
                    "name": react,
                    "arguments": roles
                },
                "mods",
                constraint="uniq_type"
            )
        else:
            if data:
                await bot.db.execute(f"DELETE FROM mods WHERE id = {data['id']}")

        if roles:
            roles = [f"<@&{id}>" for id in roles]
        em.description = bot.get_locale(ctx.lang, "other_reaction_success_delete").format(
            author=tagged_dname(ctx.author),
            role=role.mention if role else "**all**",
            emoji=react,
            message=message.id,
            roles=", ".join(roles) if roles else "-"
        )

        await bot.true_send(ctx=ctx, embed=em)
        return


    @remove_.command(pass_context=True, name="autorole", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def remove_autorole_(self, ctx):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx or not is_admin(ctx.author): return
        em = ctx.embed.copy()

        await bot.db.execute(f"UPDATE guilds SET autorole = DEFAULT WHERE id = {ctx.guild.id}")
        em.description = bot.get_locale(ctx.lang, "other_autorole_success_delete").format(
            who=tagged_dname(ctx.author)
        )

        await bot.true_send(ctx=ctx, embed=em)
        return


    @remove_.command(pass_context=True, name="nitroemote", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def remove_nitroemote_(self, ctx):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx or not is_admin(ctx.author): return
        em = ctx.embed.copy()

        await bot.db.update({
            "is_nitro_emotes": False
        }, "guilds", where={"id": ctx.guild.id})
        em.description = bot.get_locale(ctx.lang, "other_nitroemote_success_delete").format(
            who=tagged_dname(ctx.author)
        )

        await bot.true_send(ctx=ctx, embed=em)
        return


    @remove_.command(pass_context=True, name="lvlup", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def remove_lvlup_(self, ctx, lvl: int):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx or not is_admin(ctx.author): return
        em = ctx.embed.copy()

        if lvl < 1:
            lvl = 1

        data = await bot.db.select("*", "mods", where={"guild_id": ctx.guild.id, "type": "lvlup", "condition": str(lvl)})
        if data:
            await bot.db.execute(f"DELETE FROM mods WHERE id = {data['id']}")
            em.description = bot.get_locale(ctx.lang, "other_autorole_success_delete").format(
                who=tagged_dname(ctx.author),
                role_id=dat["value"],
                lvl=lvl
            )
        else:
            em.description = bot.get_locale(ctx.lang, "other_lvlup_not_exists").format(
                who=tagged_dname(ctx.author),
                lvl=lvl
            )

        await bot.true_send(ctx=ctx, embed=em)
        return


    @commands.command(pass_context=True, name="achievement", aliases=["achievements", "stats"])
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def achievements_(self, ctx, user: discord.Member=None):
        bot = self.bot
        ctx.bot = bot

        ctx = await context_init(ctx)
        if not ctx: return
        em = ctx.embed.copy()

        # data = await bot.db.select("arguments", "mods", where={
        #     "guild_id": ctx.guild.id,
        #     "name": str(ctx.author.id),
        #     "type": "achievements"
        # })
        #
        # embeds = []
        # for row in resp:
        #     embed = em.copy()
        #     embed.color = random.randint(0, 0xffffff)
        #     for key, value in row.items():
        #         if len(embed.fields) == 25:
        #             embeds.append(embed)
        #             embed = em.copy()
        #         value = f"'{value}'" if isinstance(value, str) else str(value)
        #         embed.add_field(
        #             name=key,
        #             value=value,
        #             inline=True
        #         )
        #     if len(embed.fields) != 25:
        #         embeds.append(embed)
        #
        # embeds[-1].set_footer(text=tagged_dname(ctx.author), icon_url=str(ctx.author.avatar_url))
        # embeds[0].description = bot.get_locale(ctx.lang, "admin_request_completed").format(query)

        em.title = "Achievements"
        em.description = "In progress..."

        await bot.true_send(ctx=ctx, embed=em)
        return


    async def check_lvlup(self, member, last_xp, new_xp, data=None, channel=None):
        bot = self.bot
        guild = member.guild
        if not data:
            data = await bot.get_cached_guild(guild)
        if not data["is_lvlup_notice"]:
            return

        ch = channel
        if data["lvlup_channel"]:
            channel = bot.get_channel(data["lvlup_channel"])
        if not channel:
            channel = ch
        if not channel:
            return

        last_lvl = get_lvl(last_xp)
        new_lvl = get_lvl(new_xp)
        if new_lvl <= last_lvl:
            return

        lang = data["locale"]
        em = discord.Embed(colour=int(data["em_color"], 16) + 512)
        em.description = bot.get_locale(lang, "lvlup").format(
            who=member.mention,
            lvl=new_lvl
        )

        roles_data = await bot.db.select_all("*", "mods", where={
            "guild_id": guild.id,
            "type": "lvlup"
        })
        roles = []
        is_new_role = False
        new_roles = []
        new_role = None
        if roles_data:
            for role in member.roles:
                if not any(role.id == int(row["value"]) for row in roles_data):
                    roles.append(role)
            for row in roles_data:
                if row["condition"] == "0":
                    new_role = guild.get_role(int(row["value"]))
                    if new_role and not new_role in roles:
                        roles.append(new_role)
            new_role = None
            for lvl in range(last_lvl+1, new_lvl+1):
                for row in roles_data:
                    if not row["condition"] == str(lvl):
                        continue
                    role = guild.get_role(int(row["value"]))
                    if role and not role in roles:
                        new_role = role
        if new_role:
            is_new_role = True
            new_roles.append(new_role.mention)
            roles.append(new_role)
        if is_new_role:
            em.description += bot.get_locale(lang, "lvlup_continue").format(role=", ".join(new_roles))
            try:
                await member.edit(roles=roles, reason="Tomori lvlup")
            except discord.Forbidden:
                await self.bot.channel_send_error(channel=member, error="cant_update_user_roles", who=member.mention)
            except Exception as e:
                logger.info(f"check_lvlup: Unknown exception ({e}) - {guild.name} [{guild.id}] Roles: {', '.join(new_roles)}")
        em.set_image(url=data["lvlup_image"])
        msg = await bot.true_send(
            channel=channel,
            embed=em,
            nitro=data["is_nitro"],
            username=data["nitro_name"] if data["nitro_name"] else None,
            avatar_url=data["nitro_avatar"] if data["nitro_avatar"] else None,
            delete_after=25
        )

    async def get_twitch_user(self, login: str):
        user = None
        try:
            resp = await self.bot.session.get(f"{TWITCH_BASE}/users",
                params={"login": login},
                headers={"Client-ID": TWITCH_CLIENT_ID}
            )
            data = await resp.json()
            user = data.get("data", [None])
            user = user[0]
        except Exception as e:
            logger.info(f"get_twitch_user: Unknown exception ({e}) - {login}")
        return user

    async def get_twitch_streams(self, login: str):
        streams = None
        try:
            resp = await self.bot.session.get(f"{TWITCH_BASE}/streams",
                params={"user_login": login},
                headers={"Client-ID": TWITCH_CLIENT_ID}
            )
            data = await resp.json()
            streams = data.get("data")
        except Exception as e:
            logger.info(f"get_twitch_stream: Unknown exception ({e}) - {login}")
        return streams



def setup(bot):
    bot.add_cog(Other(bot))
