import sys
import asyncio, aiohttp, logging, time, string, random, copy, json, asyncpg
import re
from aiohttp import ClientSession

from aiocache import cached, Cache

import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

import time
from datetime import datetime, date, timedelta

import threading

from cogs.util import *
from cogs.const import *
from cogs.classes import *
from config.settings import settings



__name__ = "Minami Fan"
__author__ = "Pineapple Cookie"
__version__ = "5.12.4 Go"

SHARD_COUNT = 1


random.seed()


class Tomori(commands.AutoShardedBot):


    def __init__(self, **kwargs):
        super().__init__(
            intents=discord.Intents.all(),
            command_prefix="!",
            case_insensitive=True,
            shard_count=SHARD_COUNT,
            cache_auth=False,
            activity = discord.Activity(
                type=discord.ActivityType.playing,
                name="trying to launch (^_^)"
            )
        )

        self.db = PostgresqlDatabase(dsn=f'postgres://{settings["base_user"]}:{settings["base_password"]}@localhost:5432/anime')
        self.minami_db = PostgresqlDatabase(dsn=f'postgres://{settings["base_user"]}:{settings["base_password"]}@localhost:5432/minami')
        # self.odb = PostgresqlDatabase(dsn=f'postgres://{settings["base_user"]}:{settings["base_password"]}@localhost:5432/tomori')
        self.launch_time = datetime.utcnow()
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.t_name = __name__
        self.t_version = __version__
        self.commands_activity = {}
        self.handling_twitch_streams = []
        self.cache = {
            "guilds": Cache(namespace="guilds"),
            "badges": Cache(namespace="badges")
        }

        self.locks = {}


    async def _init_database(self):
        await self.db.connect()
        await self.minami_db.connect()
        self._locale = await self._init_locale()


    async def _init_locale(self):
        locale = {}
        columnNames = await self.db.select_all("column_name", "information_schema.columns", where={"table_name": "locale"})
        columns = ""
        for column in columnNames:
            columns += "{}, ".format(column[0])
        fromBase = await self.db.select_all(columns[:-2], "locale")
        _locales = columnNames
        for name, *columns in fromBase:
            for index, column in enumerate(columns):
                if not columnNames[index+1][0] in locale.keys():
                    locale[columnNames[index+1][0]] = {}
                locale[columnNames[index+1][0]].setdefault(name, column)
        return locale


    def get_locale(self, lang, key):
        lang = lang.lower()
        key = key.lower()
        text = self._locale.get(lang, {key: "Error! Language not found"}).get(key)
        if not text:
            text = self._locale.get("english", {key: "Error! Language not found"}).get(key)
        return text

    @cached(ttl=60, namespace="guilds")
    async def get_cached_guild(self, guild):
        dat = await self.db.update({"icon_url": str(guild.icon_url)}, "guilds", where={"id": guild.id})
        if not dat:
            lang = "english"
            if guild.region == discord.VoiceRegion.russia:
                lang = "russian"
            dat = await self.db.insert({
                "id": guild.id,
                "name": guild.name,
                "icon_url": str(guild.icon_url),
                "locale": lang
            }, "guilds")
        return dat

    @cached(ttl=60, namespace="badges")
    async def get_badges(self, user):
        if isinstance(user, int):
            id = user
        elif isinstance(user, str):
            id = int(user)
        else:
            id = user.id
        badges = await self.db.select("arguments", "mods", where={"type": "badges", "name":str(id)})
        if badges:
            badges = badges["arguments"]
        else:
            badges = []
        badges = Badges(badges)
        return badges

    async def check_any_badges(self, user, _badges):
        badges = await self.get_badges(user)
        badges = badges.get_badges()
        if isinstance(_badges, list):
            for badge in _badges:
                if badge.lower() in badges:
                    return True
            return False
        else:
            return True if str(_badges).lower() in badges else False

    async def check_badges(self, user, _badges):
        badges = await self.get_badges(user)
        badges = badges.get_badges()
        if isinstance(_badges, list):
            for badge in _badges:
                if not badge.lower() in badges:
                    return False
            return True
        else:
            return True if str(_badges).lower() in badges else False

    async def get_weeb_gif(self, name: str):
        gif = None
        try:
            params = {
                "type": name,
                "filetype": "gif",
                "nsfw": 1
            }
            resp = await self.session.get(
                "https://api.weeb.sh/images/random",
                params = params,
                headers = {
                    "Authorization": settings["weeb_token"]
                })
            if resp.status == 200:
                data = await resp.json()
                gif = data.get("url", None)
        except Exception as e:
            logger.info(f"get_weeb_gif: Unknown exception ({e}) - Name: {name}")
        return gif


    async def add_follow_links(self, ctx, embed):
        embed.add_field(
            name=self.get_locale(ctx.lang, "global_follow_us"),
            value=tomori_links,
            inline=False
        )
        return embed


    async def statuses(self):
        while True:
            while not self.is_closed():

                await self.change_presence(activity=discord.Activity(
                        type=discord.ActivityType.listening,
                        name="minami.fan"
                    )
                )

                await asyncio.sleep(600)
            await asyncio.sleep(60)

    def lock_once(coro):
        async def lock_work(self):
            if self.locks.get(coro.__name__):
                return None
            self.locks[coro.__name__] = True
            return coro
        return lock_work

    @lock_once
    async def partnershiping(self):
        now = datetime.utcnow()
        now = COOLDOWNS["half-day"]-((now.hour*3600 + now.minute*60 + now.second) % COOLDOWNS["half-day"])
        await asyncio.sleep(now)

        while not self.is_closed():
            channel = self.get_channel(550031583348916256)
            if not channel:
                break

            messages = await channel.history(limit=1, oldest_first=True).flatten()
            if not messages:
                break

            msg = messages[0]

            await self.true_send(
                channel=channel,
                content=msg.content,
                embeds=msg.embeds,
                nonce=msg.nonce,
                tts=msg.tts,
                attachments=msg.attachments,
                username="Partnerships",
                nitro=True
            )
            await msg.delete()

            await asyncio.sleep(COOLDOWNS["half-day"])


    async def init_twitch_streams(self):
        offset = 0
        limit = 25
        while True:
            data = await self.db.fetch(f"SELECT * FROM mods WHERE type='twitch_notify' ORDER BY guild_id ASC LIMIT {limit} OFFSET {offset}")
            if not data:
                return
            for row in data:
                if row["id"] in self.handling_twitch_streams:
                    continue
                self.handling_twitch_streams.append(row["id"])
                self.loop.create_task(self.handle_twitch_notification(login=row["name"]))
            offset += limit

    async def handle_twitch_notification(self, login):
        await asyncio.sleep(random.randint(5, 30))

        async def delete_that_row():
            await self.db.execute(f"DELETE FROM mods where type = 'twitch_notify' AND name = E'{self.db.clear(login)}'")

        latest = None

        while True:
            await self.wait_until_ready()
            try:
                other = self.get_cog('Other')
                user = await other.get_twitch_user(login)
                if not user:
                    # await delete_that_row()
                    return

                data = await other.get_twitch_streams(login)

                if data:
                    for stream in data:
                        if not stream.get("type") == "live":
                            continue

                        stream_data = await self.db.select("*", "mods", where={"type": "twitch_notify", "name": login})
                        if not stream_data:
                            return
                        if not stream_data["value"]:
                            continue
                        channel = self.get_channel(stream_data["guild_id"])

                        if not channel:
                            # await delete_that_row()
                            return

                        const = await self.get_cached_guild(channel.guild)

                        latest = stream_data["condition"]
                        if latest == stream.get("id"):
                            break


                        text = stream_data["value"]
                        try:
                            text = text.format(
                                title=stream.get("title", "Stream"),
                                views=stream.get("viewer_count", 0)
                            )
                        except:
                            pass

                        await self.true_send(
                            channel=channel,
                            content=text,
                            nitro=const["is_nitro"],
                            username=const["nitro_name"],
                            avatar_url=const["nitro_avatar"]
                        )

                        await self.db.insert_update(
                            {
                                "guild_id": channel.id,
                                "type": "twitch_notify",
                                "name": login,
                                "condition": stream.get("id", "-"),
                                "value": stream_data["value"]
                            }, "mods", where={"type": "twitch_notify", "name": login},
                            constraint="uniq_type"
                        )
            except Exception as e:
                logger.info(f"handle_twitch_notification: Unknown exception ({e}) - {login}")

            await asyncio.sleep(COOLDOWNS["streams"])


    def get_songs_list(self):
        songs = []
        path = os.curdir+"/music"
        try:
            for file in os.listdir(path):
                song = f"{path}/{file}"
                songs.append(song)
                # print("Добавлено:", song)
        except Exception as e:
            print(e)
        return songs

    async def connect_voice(self, id):
        voice_channel = self.get_channel(id)
        assert voice_channel, f"Не удалось найти голосовой канал {id}"
        assert isinstance(voice_channel, discord.VoiceChannel), f"Канал {id} не является голосовым"

        voice_client = await voice_channel.connect()
        assert voice_client.is_connected(), f"Не удалось подключиться к голосовому каналу {id}"

        # await voice_channel.guild.me.request_to_speak()

        return voice_client

    async def start_music(self):
        guild = self.get_guild(GUILD_ID)
        assert guild, f"Не удалось найти сервер {GUILD_ID}"

        voice_channel = self.get_channel(INFINITE_STREAM_CHANNEL_ID)
        songs_log_channel = self.get_channel(INFINITE_STREAM__SONGS_LOG_CHANNEL_ID)

        voice_client = guild.voice_client
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect(force=True)

        voice_client = await self.connect_voice(INFINITE_STREAM_CHANNEL_ID)
        # try:
        #     await voice_channel.edit(topic=INFINITE_STREAM_CHANNEL_TOPIC)
        # except Exception as e:
        #     pass

        while True:
            songs = self.get_songs_list()
            random.shuffle(songs)

            for song in songs:
                # if not voice_client.is_connected():
                #     await voice_client.disconnect(force=True)
                #     voice_client = await self.connect_voice(INFINITE_STREAM_CHANNEL_ID)

                try:
                    voice_client = guild.voice_client
                    if not (voice_client and voice_client.is_connected()):
                        voice_client = await self.connect_voice(INFINITE_STREAM_CHANNEL_ID)

                    source = discord.FFmpegPCMAudio(song, **ffmpeg_options)
                    source.volume = 0.5

                    try:

                        songname = song.rsplit("/", maxsplit=1)[-1]
                        songname = songname.rsplit(".", maxsplit=1)[0]
                        # await voice_channel.edit(topic = songname)
                        # async with aiohttp.ClientSession() as session:
                        #     try:
                        #         payload = {
                        #             "topic": songname
                        #         }
                        #         resp = await session.patch(f"https://discord.com/api/channels/{voice_channel.id}", json=payload, headers={'authorization': f"Bot {settings['token']}", 'accept': 'application/json'})
                        #     except Exception as e:
                        #         print(f"start_music: Unknown exception on webhook ({e}) - {songname}")
                        await songs_log_channel.send(content = f"<:chillin:550385656967331841> Now playing - {songname}")
                    except Exception as e:
                        print(f"start_music: Exception in voice_channel.edit -> {e}")

                    voice_client.play(source)

                    while voice_client.is_playing():
                        # print(f"Playing now - {songname}")
                        await asyncio.sleep(5)
                except Exception as e:
                    print(e)
                    try:
                        voice_client.cleanup()
                    except Exception as e:
                        print(f"cleanup: {e}")

            # await self.stop_music()
            # voice_client = await self.connect_voice(INFINITE_STREAM_CHANNEL_ID)

        print("Музыка остановлена..")


    async def stop_music(self):
        guild = self.get_guild(GUILD_ID)
        assert guild, f"Не удалось найти сервер {GUILD_ID}"

        voice_client = guild.voice_client
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect(force=True)

    # Infinite Lofi Music
    async def infinite_lofi_music_playing(self):
    	while True:
    		try:
    			channel = await self.fetch_channel(INFINITE_STREAM_CHANNEL_ID)
    		except discord.NotFound:
    			return

    		infinite_lofi = None

    		try:
    			if not infinite_lofi or not infinite_lofi.is_connected():
    				infinite_lofi = await channel.connect(timeout=5)

    				member = await channel.guild.fetch_member(self.user.id)
    				await member.request_to_speak()
    		except discord.ClientException as e:
    			await asyncio.sleep(5)
    			continue
    		except Exception as e:
    			print(f"infinite_lofi_music_playing: {e}")
    			continue
    		else:
    			print("[IR] Connected to voice channel. 🚧 Loading from config livestream URL...")

    		async def music_play():
    			player = await YTDLSource.from_url(INFINITE_STREAM_URL, loop=self.loop, stream=True)
    			infinite_lofi.play(player, after=lambda e: self.loop.run_until_complete(music_play()))

    		await music_play()

    		await asyncio.sleep(5)


    async def affialte_text_posting(self):
        await self.wait_until_ready()
        while True:
            try:
                t_now = datetime.utcnow()
                seconds_to_sleep = (AFFILIATES_TEXT_POST_CD - (t_now.hour*3600 + t_now.minute*60 + t_now.second)) % AFFILIATES_TEXT_POST_CD
                await asyncio.sleep(seconds_to_sleep)

                day_of_year = t_now.timetuple().tm_yday
                hour_of_year = day_of_year * 3 + int(t_now.hour * COOLDOWNS["hour"] / AFFILIATES_TEXT_POST_CD)

                text = AFFILIATES_TEXTS[hour_of_year % len(AFFILIATES_TEXTS)]

                channel = self.get_channel(AFFILIATES_TEXTS_CHANNEL_ID)

                await self.true_send(
                                    channel = channel,
                                    content = text,
                                    nitro = True,
                                    username = "Partnerships",
                                    )
            except Exception as e:
                pass
            await asyncio.sleep(AFFILIATES_TEXT_POST_CD)


    async def on_resumed(self):
        exit(373)
        # self.launch_time = datetime.utcnow()
        # self.commands_activity = {}
        # channel = self.get_channel(550000437349318666)
        # if channel: await channel.send(f"ぱいなぴるー君、見ってください。 (v{__version__})")


    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print("Started in "+str(datetime.utcnow() - self.launch_time))
        print('------')

        channel = self.get_channel(550000437349318666)
        if channel: await channel.send(f"おはようございますぱいなぴるー君。(Launch time: {round((datetime.utcnow() - self.launch_time).total_seconds(), 2)} sec | v{__version__})")

        self.loop.create_task(self.statuses())
        self.loop.create_task(self.affialte_text_posting())

        # INFINITE MUSIC
        self.loop.create_task(self.start_music())
        # INFINITE YOUTUBE STREAM
        # self.loop.create_task(self.infinite_lofi_music_playing())

    async def handle_nitro_emotes(self, message, const):
        try:
            new_content = message.content
            bot_member = discord.utils.get(message.guild.members, id=self.user.id)
            is_edited = False

            def can_mention(user):
                if user.id == message.guild.owner.id:
                    return True
                return any(role.permissions.administrator or role.permissions.mention_everyone for role in user.roles)

            if can_mention(message.author) != can_mention(bot_member):
                # new_content = discord.utils.escape_mentions(new_content)
                replace_links = [
                    "@everyone",
                    "@here"
                ]
                for link in replace_links:
                    new_content = new_content.replace(link, link[:-1]+"е")

            emoji_pattern = r"<?a?:[\w\d_]+:[0-9]*>?"
            name_pattern = r":[\w\d_]+:"
            replaced_emotes = []

            for match in re.findall(emoji_pattern, new_content):
                name = re.search(name_pattern, match)
                emoji = discord.utils.get(message.guild.emojis, name=name.group(0)[1:-1])
                if not emoji:
                    continue
                if emoji.animated:
                    is_edited = True

                if emoji in replaced_emotes:
                    continue
                replaced_emotes.append(emoji)

                new_content = new_content.replace(match, str(emoji))

            if is_edited:
                for emoji in replaced_emotes:
                    emote = str(emoji)
                    emote = emote.replace(f":{emoji.name}:", str(emoji))
                    new_content = new_content.replace(emote, str(emoji))

                await self.true_send(
                    channel=message.channel,
                    content=new_content,
                    username=message.author.display_name,
                    avatar_url=str(message.author.avatar_url),
                    attachments=message.attachments,
                    nitro=True
                )
                await message.delete()
        except Exception as e:
            await self.true_send(channel=message.channel, content=str(e))

    async def on_command_error(self, ctx, error):
        ctx = await context_init(ctx)
        if not ctx: return
        if isinstance(error, commands.CommandOnCooldown):
            await self.true_send(ctx=ctx, content="{who}, command is on cooldown. Wait {seconds} seconds".format(
                    who=ctx.author.mention,
                    seconds=round(error.retry_after, 2)
                ),
                delete_after=5
            )
        elif isinstance(error, commands.BadArgument):
            await self.true_send_error(ctx=ctx, channel=ctx.channel, error="incorrect_argument", arg=error.args[0])
        elif isinstance(error, commands.MissingRequiredArgument):
            await self.true_send_error(ctx=ctx, channel=ctx.channel, error="missed_argument", arg=error.param.name)


    def add_command_activity(self, name):
        name = name.lower()
        count = self.commands_activity.get(name, 0)
        self.commands_activity[name] = count + 1


    async def on_command(self, ctx):
        try:
            self.add_command_activity(ctx.invoked_with)
        except:
            pass


    async def on_command_completion(self, ctx):
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        except Exception as e:
            logger.info(f"on_command: Unknown exception ({e}) - {ctx.channel.guild.name} [{ctx.channel.guild.id}]")


    async def handle_command(self, message):
        const = await self.get_cached_guild(message.guild)
        data = await self.db.pool.fetchrow(f"""INSERT INTO users(
            id,
            guild,
            discriminator,
            xp,
            last_xp,
            messages,
            cash,
            name,
            avatar_url
        ) VALUES(
            {message.author.id},
            {message.guild.id},
            '{message.author.discriminator}',
            {const['xp_award']},
            {unix_time()},
            1,
            {const['message_award']},
            E'{self.db.clear(message.author.name)}',
            E'{self.db.clear(str(message.author.avatar_url_as(static_format='png')))}'
        ) ON CONFLICT ON CONSTRAINT unic_profile DO UPDATE SET
            discriminator='{message.author.discriminator}',
            avatar_url=E'{self.db.clear(str(message.author.avatar_url_as(format='png')))}',
            xp=users.xp+{const['xp_award']},
            last_xp={unix_time()},
            messages=users.messages + 1,
            cash=users.cash+{const['message_award']}
        WHERE
            users.id={message.author.id} AND
            users.guild={message.guild.id} AND
            users.last_xp<={unix_time()}-{const['xp_cd']}
        RETURNING *;""")

        try:
            other = self.get_cog('Other')
            await other.check_lvlup(message.author, data["xp"]-const['xp_award'], data["xp"], data=const, channel=message.channel)
        except Exception as e:
            pass
            # if self.is_ready():
            #     logger.info(f"handle_command->other.check_lvlup: Unknown exception ({e}) - {message.guild.name} [{message.guild.id}]")

        if message.content.startswith(const["prefix"]) or message.content.lower() == "!help":
            message.content = message.content.replace(const["prefix"], "!", 1)
            await self.process_commands(message)
        elif message.content and const["is_nitro_emotes"]:
            await self.loop.create_task(self.handle_nitro_emotes(message, const))


    async def on_message(self, message):
        user = dsi_check_user_like(self, message)
        if user:
            await self.db.insert_update({
                "cash": {3730: "+"},
                "name": user.name,
                "discriminator": str(user.discriminator),
                "id": user.id,
                "guild": MAIN_GUILD_ID
            }, "users", where={"id": user.id, "guild": MAIN_GUILD_ID}, constraint="unic_profile")
            channel = self.get_channel(549265213069721638)
            if channel:
                await channel.send(f"{user.mention}, you liked the server in DiscordServer.Info Monitoring and got 3730 <:lilac:550225868304285707> from me. Thank you!")

        # Автопостинг в выбранных каналах (подписка на канал в дискорде)
        if message.channel.id in AUTOPUBLISH_CHANNELS:
            self.loop.create_task(publish_message(message)) # Спать 5 минут перед отправкой


        if message.author.discriminator == "0000":
            if message.content:
                if re.match(webhook_cd_pattern, message.content):
                    await asyncio.sleep(5)
                    await message.delete()
            return
        if message.author.bot:
            return
        if not message.guild:
            return
        await self.handle_command(message)


        # Autoposting news from discord server to Lilac app
        if message.channel.id in [549264963873669130]:
            description = message.content
            icon_url = None

            attachments = message.attachments
            for attachment in attachments:
                if str(attachment.content_type).lower().startswith("image/"):
                    icon_url = attachment.url
                    break

            await self.minami_db.insert({
                "title": "Minami Fan Zone | Discord",
                "description": description,
                "icon_url": icon_url
            }, "news")


    async def true_send(self, *args, **kwargs):
        try:
            channel = kwargs.pop("channel")
        except:
            channel = None
        try:
            ctx = kwargs.pop("ctx")
        except:
            ctx = None
        if not channel and ctx:
            channel = ctx.channel
        assert channel, "true_send: Channel is null"
        try:
            nitro = kwargs.pop("nitro")
        except:
            nitro = None
        error = kwargs.pop("error", None)
        msg = None

        try:
            file = kwargs.pop("file")
        except:
            file = None
        try:
            files = kwargs.pop("files")
        except:
            files = None
        try:
            attachments = kwargs.pop("attachments")
        except:
            attachments = None
        new_files = []
        if file and isinstance(file, discord.File):
            new_files.append(file)
        if files:
            for file_ in files:
                if isinstance(file_, discord.File):
                    new_files.append(file_)
        if attachments:
            for attach in attachments:
                fp = BytesIO()
                await attach.save(fp)
                new_files.append(discord.File(fp, filename=attach.filename, spoiler=attach.is_spoiler()))
        kwargs["files"] = new_files[:10]


        if (nitro or (ctx and ctx.is_nitro)) and not (isinstance(channel, discord.User) or isinstance(channel, discord.Member)):
            try:
                webhooks = await channel.webhooks()
                if not webhooks:
                    webhooks = [await channel.create_webhook(
                        name='Tomori Nitro Webhook',
                        avatar=await self.user.avatar_url_as(format="png").read()
                    )]

                name = self.user.display_name
                url = str(self.user.avatar_url_as(format="png", size=512))

                if ctx:
                    const = ctx.const
                    if const["nitro_name"]:
                        name = const["nitro_name"]
                    if const["nitro_avatar"]:
                        url = const["nitro_avatar"]

                if not kwargs.get("username", None):
                    kwargs["username"] = name
                if not kwargs.get("avatar_url", None):
                    kwargs["avatar_url"] = url

                new_kwargs = {}
                keys = [
                    "content",
                    "tts",
                    "embed",
                    "embeds",
                    "file",
                    "files",
                    "nonce",
                    "username",
                    "avatar_url"
                ]
                for key in keys:
                    if kwargs.get(key, None) != None:
                        new_kwargs[key] = kwargs.get(key)
                new_kwargs["wait"] = True
                msg = await webhooks[0].send(**new_kwargs)
                return
            except discord.Forbidden:
                if error != False:
                    logger.info(f"true_send: Tomori Nitro doesnt allow by server owner - {ctx.channel.guild.name} [{ctx.channel.guild.id}]")
                    msg = await self.true_send_error(ctx=ctx, error="wh_forbidden")
                else:
                    raise e
            except Exception as e:
                if error != False:
                    logger.info(f"true_send: Unknown exception at webhooks ({e}) - {ctx.channel.guild.name} [{ctx.channel.guild.id}]")
                    # msg = await self.true_send_error(ctx=ctx)
                else:
                    raise e
                return

        try:
            new_kwargs = {}
            keys = [
                "content",
                "tts",
                "embed",
                "file",
                "files",
                "nonce",
                "delete_after"
            ]
            for key in keys:
                if kwargs.get(key, None) != None:
                    new_kwargs[key] = kwargs.get(key)
            msg = await channel.send(**new_kwargs)
        except discord.Forbidden:
            pass
            #
            #  TODO Тут идет игнор команд в чатах, где бот видит сообщения, а отвечать не может (Это фича)
            #
            # await self.true_send_error(ctx=ctx, error="send_forbidden")
            # print(f"true_send: Tomori Nitro doesnt allow by server owner - {channel.guild.name} [{channel.guild.id}]")
        except Exception as e:
            if error != False:
                logger.info(f"true_send: Unknown exception ({e}) - {channel.guild.name} [{channel.guild.id}]")
                # msg = await self.true_send_error(ctx=ctx)
            else:
                raise e
        return msg



    async def send_or_edit(self, *args, **kwargs):
        msg = None
        try:
            message = kwargs.pop("message", None)
        except:
            message = None

        if not message:
            msg = await self.true_send(*args, **kwargs)
        else:
            try:
                await message.edit(
                    content=kwargs.get("content", None),
                    embed=kwargs.get("embed", None),
                    suppress=kwargs.get("suppress", None),
                    delete_after=kwargs.get("delete_after", None)
                )
                msg = message
            except Exception as e:
                msg = None
                print(e)

        return msg



    async def true_send_error(self, *args, **kwargs):
        ctx = kwargs.pop("ctx")
        assert ctx, "true_send_error: Context is null"
        try:
            author = ctx.author
        except Exception as e:
            logger.info(f"true_send_error: Unknown exception at get author ({e})")
        assert author, "true_send_error: Author is null"

        def format_error(text):
            return text.format(
                user=kwargs.get("user", ctx.author.mention),
                who=kwargs.get("who", ctx.author.mention),
                author=kwargs.get("who", ctx.author.mention),
                bot=kwargs.get("bot", self.user.mention),
                guild=kwargs.get("guild", ctx.guild.name),
                name=kwargs.get("name", ""),
                arg=kwargs.get("arg", ""),
                emoji=ctx.const["emoji"],
                voice=kwargs.get("voice", ""),
                number=kwargs.get("number", ""),
                role=kwargs.get("role", "")
            )

        code = kwargs.get("error", "default")
        embed = copy.deepcopy(ERRORS.get(code, None))
        if not embed:
            error_text = self._locale.get(ctx.lang, {code: "Error! Language not found"}).get(code, None)
            if error_text:
                embed = discord.Embed(
                                        title="Tomori Exception",
                                        description=error_text,
                                        color=COLORS["error"]
                                    )
            else:
                embed = ERRORS.get("default")
        embed.title = format_error(embed.title)
        embed.description = format_error(embed.description)
        channel = kwargs.get("channel", author)
        return await channel.send(embed=embed, delete_after=60)

    async def channel_send_error(self, *args, **kwargs):
        channel = kwargs.pop("channel")
        assert channel, "true_send_error: Channel is null"

        def format_error(text):
            return text.format(
                user=kwargs.get("user", ""),
                who=kwargs.get("who", ""),
                author=kwargs.get("who", ""),
                bot=kwargs.get("bot", ""),
                guild=kwargs.get("guild", ""),
                name=kwargs.get("name", ""),
                arg=kwargs.get("arg", ""),
                emoji=kwargs.get("emoji", ""),
                voice=kwargs.get("voice", ""),
                number=kwargs.get("number", ""),
                role=kwargs.get("role", "")
            )

        code = kwargs.get("error", "default")
        lang = kwargs.get("lang", "english")
        embed = copy.deepcopy(ERRORS.get(code, None))
        if not embed:
            error_text = self._locale.get(lang, {code: "Error! Language not found"}).get(code, None)
            if error_text:
                embed = discord.Embed(
                                        title="Tomori Exception",
                                        description=error_text,
                                        color=COLORS["error"]
                                    )
            else:
                embed = ERRORS.get("default")
        embed.title = format_error(embed.title)
        embed.description = format_error(embed.description)
        return await channel.send(embed=embed, delete_after=60)


    def run(self, token):
        self.loop.run_until_complete(self._init_database())
        self.remove_command("help")
        for extension in settings["extensions"]:
            try:
                self.load_extension(extension)
            except Exception as e:
                logger.info(f"[x] Can't load Cog because: {e}")
        # quart_app.client = self
        # self.quart_thread = threading.Thread(target=quart_app.run, args=["54.37.18.227", 8080], kwargs={
        #     "debug": False,
        #     "use_reloader": True
        # })
        # self.quart_thread.start()
        super().run(token)


tomori = Tomori()
tomori.run(settings["token"])
