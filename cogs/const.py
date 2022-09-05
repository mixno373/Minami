import os, sys
import asyncio
import logging
import re

import discord

from datetime import datetime, date, timedelta

from PIL import Image, ImageChops, ImageFont, ImageDraw, ImageSequence, ImageFilter, GifImagePlugin
from PIL.GifImagePlugin import getheader, getdata
from functools import partial
from io import BytesIO

from config.settings import settings



logger = logging.getLogger('tomori')
logger.setLevel(logging.DEBUG)
now = datetime.utcnow()
logname = 'logs/log{}_{}.log'.format(now.day, now.month)
try:
	os.mkdir("logs")
except:
	pass
try:
	f = open(logname, 'r')
except:
	f = open(logname, 'w')
	f.close()
finally:
	handler = logging.FileHandler(
		filename=logname,
		encoding='utf-8',
		mode='a')
handler.setFormatter(logging.Formatter(
	'%(asctime)s %(relativeCreated)6d %(threadName)s\n%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


APP_LATEST_VERSION = "1.2.373-4"
APP_LATEST_UPDATE_URI = f"/home/ubuntu/bots/Minami/apk/Lilac_v{APP_LATEST_VERSION}.apk"

WH_LOG_URL = {
	"news": "https://discord.com/api/webhooks/552531213575913483/xL5V7o1gIm6uGiPwxrkDPKxRYFPLH0ky1tR87OWiYRwyzGmVYm7FtkT6db1G77gzafPV"
}

webhook_cd_pattern = r"<@[0-9]+>, command is on cooldown. Wait [0-9]+(.[0-9]+)? seconds"

TWITCH_BASE = "https://api.twitch.tv/helix"
TWITCH_CLIENT_ID = "035q0bzco58tljuqg3pgt4b5yfp1zt"

HTTP_METHODS = ['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH']


GUILD_ID = 549251000167301120
INFINITE_STREAM_CHANNEL_ID = 555080809472720906
INFINITE_STREAM__SONGS_LOG_CHANNEL_ID = 549265213069721638
INFINITE_STREAM_CHANNEL_TOPIC = "Minami Best Girl"
INFINITE_STREAM_URL = "https://www.youtube.com/watch?v=D6J_CwcOp0o"
INFINITE_STREAM_URLS = [
	"https://www.youtube.com/watch?v=766qmHTc2ro",
	"https://www.youtube.com/watch?v=0YF8vecQWYs",
	"https://www.youtube.com/watch?v=HIRiduzNLzQ",
	"https://www.youtube.com/watch?v=GQ3V50XoLOM",
	"https://www.youtube.com/watch?v=jb4ybTQwcdw",
	"https://www.youtube.com/watch?v=dYkQGZBI2JU",
	"https://www.youtube.com/watch?v=9pN7UKpyCc4",
	"https://www.youtube.com/watch?v=_xnuoNjqo4Y",
	"https://www.youtube.com/watch?v=kWSbYcU4Vts",
	"https://www.youtube.com/watch?v=qyeF2-0OHyk"
]


DEFAULT_PIC_URL = "https://minami.fan/images/home-bg.png"


AUTOPUBLISH_CHANNELS = [
	549264963873669130
]


AFFILIATES_TEXTS_CHANNEL_ID = 550031583348916256
AFFILIATES_TEXT_POST_CD = 8 * 60 * 60 # 8 hours
AFFILIATES_TEXTS = [
"""Welcome to the server dedicated to Yorushika, where you can find other fans, information related to Yorushika, discuss other music, and many more!

https://discord.gg/wdam3HB""",
"""Welcome to the **BAND-MAID** Discord Server!
This is the place for anyone who wants the best of the best from rock, from a fantastic quintet of amazing Ladies.
Miku//Saiki//Misa//Akane//Kanami

https://discord.gg/XYvzy6V""",
"""__Welcome to Amazarashi ROOM__

Amazarashi (Japanese for weather beaten) is a melancholic band from Aomori known for their flow-of-conciousness style of music.
The group's most notable songs are
"Sora ni Utaeba", the third opening of My Hero Academia;
"Kisetsu wa Tsugitsugi Shindeiku", the ending theme for the anime Tokyo Ghoul √A;
"Inochi ni Fusawashii", tie-up with the famous video-game writer, director and designer, Yoko Taro, and his game NieR:Automata and most recently,
"Sayonara Gokko", the ending theme for Dororo.

https://discord.gg/PCJZmtF""",
"""List of Japanese artist servers
https://discord.gg/ySJrced""",
"""__"Welcome to the unoffical ReoNa* fan server, a server dedicated to ReoNa* aka Kanzaki Elza__

:feet: Translation all of ReoNa's tweets and related content.
:feet: Huge collection of ReoNa's photos dating back to when she was a cosplayer under the name Reopeko
:feet: Archives of many of her videos (radios, lives etc)
:feet: Weekly trival quizes about ReoNa*
Join us now and support the upcoming 絶望系アニソンシンガー ReoNa*!

https://discord.gg/UmWp8JY
https://media.discordapp.net/attachments/564830779939487754/569911271391232022/Dy4XdILUcAAgIhh.jpg""",
"""We are now friends with the Reol server. Reol is an amazing singer and you should check both her and the server out.
https://discord.gg/NpYCFQ6""",
""""High schooler Natsuo is hopelessly in love with his cheerful and popular teacher, Hina. However, one day at a mixer, he meets a moody girl by the name of Rui and ends up sleeping with her. Soon after, his father announces that he's getting remarried to a woman with two daughters of her own. And who shows up in town, other than both Hina and Rui?! Natsuo's outrageous new life starts now!"

https://discord.gg/PkUZktw""",
"""**__:small_blue_diamond: /r/KimiSui__**

*This is a Discord server dedicated for the fans of "Kimi no Suizou wo Tabetai", also known as "KimiSui" for short or "I want to eat your pancreas" in English.*

Discord invite link: https://discord.gg/JdU7kqK""",
"""```fix
﹋々『Axis Cult』々﹋```

**Are you interested in __Learning__ or __Teaching Japanese__?
If so, you're more than welcome to join our Konosuba inspired anime/Japanese Culture server!

We're friendly, active, and multicultural! Play with our bots, share your art, music, or games! We have __Japanese teaching__ mentors and are growing, join us today and drop by and chat!**

**We have:**
:white_check_mark: Qualified teachers and natives who can help you on your trip to learning Japanese!
:white_check_mark: Specific channels for videogames!
:white_check_mark: NSFW channels
:white_check_mark: Anime channels!
:white_check_mark: Minigames!
:white_check_mark: Active voice channels!
:white_check_mark: Karaoke sessions!
:white_check_mark: Self-roles!
:white_check_mark: Active and nice members!
:white_check_mark: Open for partnerships!
:white_check_mark: 1200+ members and growing!
**__And more!__**

PS; Eris pads her breast.

**Permanent Invite Link:** https://discord.gg/y9eWV4h

https://img.fireden.net/a/image/1483/72/1483723087871.gif""",
"""**__:small_blue_diamond: Minase Inori fan server__**

https://discord.gg/dH96hWdKXc""",
"""Welcome to Paramore, a server dedicated to the band. We have a caring, loving community, as well as great staff. For fans of the band, or people who just want to come and hang out.
https://discord.gg/HZDFQth""",
"""Find other music servers here
https://discord.gg/SYuxCBp""",
"""Hello and welcome to the Sayuri Discord server. Sayuri is a Japanese pop singer with amazing voice and amazing fans. People who love her, people who are not familiar with her -- everyone is welcome!
https://discord.gg/fp6wU2Q""",
"""ZUTOMAYO are a Japanese rock group who debuted in 2018, with their first song --Byoushin wo Kamu-- achieving 65M+ views on YouTube.
If you're already a fan of ACAne's stunning vocals, or want to find a new J-Rock/Pop artist to stan, ZUTOMAYO ZONE is the server for you.
We're a pretty laidback, yet active server, with tons of fun bot commands, exclusive content (such as lives and concerts!), and a positive, caring community spirit.
Come check us out!
https://discord.gg/htSDkHH""",
"""Hello and welcome to the Aimer Discord server. Aimer is a Japanese pop singer with amazing voice and amazing fans. People who love her, people who are not familiar with her -- everyone is welcome!
https://discord.gg/Sn96CDJ""",
"""TUYU (ツユ) is a Japanese Rock (J-Rock) band consisting of 5 band members. TUYU has made their debute since 2019, and has been widely known because of the release of Compared Child. We also have a great and chill community. Please consider joining TUYU's Fan Discord server, and also supporting the band.
https://discord.gg/zvyrUZF""",
"""Vesperbell is a Japanese pop band and Utaite group consisting of the virtual girl duo Kasuka & Yomi. They started in 2020, and have been making waves and steadily growing a cult fanbase. If you are fans of the group, or even just want to check out a few great covers, then we are the community for you!
https://discord.gg/U4ZYjZs2v9""",
"""YOASOBI  is a Japanese music duo composed of Vocaloid (voice synthesizer software) producer Ayase and singer-songwriter Ikura (Lilas Ikuta).
The group has released songs based on short stories posted on Monogatary.com, a website operated by Sony Music Entertainment Japan, later also from various novels and book tie-up!
Consider to join in if you like their music and would love to discover more!
https://discord.gg/5wCkGPj""",
"""Welcome to the fan server for Eve harapeco, an utaite and J-pop artist whose songs are known for their deep meaning and unique feel - Do check us out, whether you are a long time fan or just hearing about him!
https://discord.gg/vvgH8D9""",
"""Ado is a Japanese singer and utaite who first debuted in 2020 with her original single, "USSEWA" reaching number one on Billboard Japan Hot 100, Oricon Digital Singles Chart, Oricon Streaming Chart, and Spotify Viral 50 Japan. If you are a fan of Ado, would like to meet new friends or a new favorite artist then come and say hello!
https://discord.gg/hPDrDETuVX""",
"""Yama is a Japanese pop singer who started her musical career in 2018.
if you would like to make new friends or talk about yama you are welcome to join.
https://discord.gg/ndvTDpedMg"""
]


COOLDOWNS = {
	"cache": 600,
	"day": 60*60*24,
	"half-day": 60*60*12,
	"hour": 60*60,
	"half-hour": 60*30,
	"streams": 30
}



CHANNELS = {
	"guild_events": 550000437349318666
}

prefix_list = [
	"!"
]

MINAMI_SERVER_ID = 549251000167301120

WORK_CHANNELS = [
	549265213069721638,
	550000414263738369,
	550000437349318666
]

FAQ = {
	"373": "The meaning of「373」.\n\
\"373\" could be read \"Mi-Na-Mi\". The Chinese character for 3 could be read as \"mi\" instead of the regular reading \"san\" , 7 is pronounced \"nana\" in Japanese which will have 373 pronounced MI-NA-MI. We use this as our team logo."
}



badges_obj = {
	"staff": Image.open("cogs/stat/badges/staff.png").convert("RGBA"),
	"partner": Image.open("cogs/stat/badges/partner.png").convert("RGBA"),
	"hypesquad": Image.open("cogs/stat/badges/hypesquad.png").convert("RGBA"),
	"bug_hunter": Image.open("cogs/stat/badges/bug_hunter.png").convert("RGBA"),
	"nitro": Image.open("cogs/stat/badges/nitro.png").convert("RGBA"),
	"boost": Image.open("cogs/stat/badges/boost.png").convert("RGBA"),
	"early": Image.open("cogs/stat/badges/early.png").convert("RGBA"),
	"verified": Image.open("cogs/stat/badges/verified.png").convert("RGBA"),
	"youtube": Image.open("cogs/stat/badges/youtube.png").convert("RGBA"),
	"twitch": Image.open("cogs/stat/badges/twitch.png").convert("RGBA")
}

badges_list = [
	"staff",
	"partner",
	"hypesquad",
	"bug_hunter",
	"nitro",
	"boost",
	"early",
	"verified",
	"youtube",
	"twitch"
]

achievements_list = [
	"oldman",
	"lucker",
	"minami"
]

SHORT_LOCALES = {
	"en": "english",
	"ru": "russian",
	"ua": "ukrainian",
	"id": "indonesian",
	"ge": "german"
}

COLORS = {
	'error': 0x5714AD,
	'idk': 0xFAD6A5,
	'hidden': 0x36393F,
	'ban': 0xF10118,
	'unban': 0xF10118,
	'kick': 0xF10118,

	'minami_main_color': 0x1DA1F2 # 1942002
}

flipcoin_sides = {
	"h": "heads",
	"head": "heads",
	"t": "tails",
	"tail": "tails"
}

flipcoin_images = {
	"heads": "https://discord.band/img/economy/coin_heads.png",
	"tails": "https://discord.band/img/economy/coin_tails.png"
}

ERRORS = {
	"default": discord.Embed(
						title="Unknown Exception",
						description="I don't know what broken. Ask my developers, please ^_^",
						color=COLORS["idk"]
					),
	"wh_forbidden": discord.Embed(
						title="Webhook Forbidden",
						description="Add access to manage webhooks, please ^_^",
						color=COLORS["error"]
					),
	"send_forbidden": discord.Embed(
						title="Message Forbidden",
						description="Add access to send messages, please ^_^",
						color=COLORS["error"]
					),
	"cm_not_available": discord.Embed(
						title="Command Error",
						description="That command isn't available for, sorry ^_^",
						color=COLORS["error"]
					),
	"cm_bot_mentioned": discord.Embed(
						title="Command Error",
						description="Bots aren't your friends, sorry ^_^\nChoose someone else",
						color=COLORS["error"]
					),
	"urban_not_found": discord.Embed(
						title="Urban Dictionary",
						description="Definitions didn't find, sorry ^_^\n",
						color=COLORS["idk"]
					),
	"tracemoe_not_found": discord.Embed(
						title="Trace.Moe API",
						description="Anime didn't find, sorry ^_^\n",
						color=COLORS["idk"]
					),
	"sql_bad_query": discord.Embed(
						title="PostgreSQL",
						description="Bad SQL query, :(",
						color=COLORS["idk"]
					),
	"sql_no_response": discord.Embed(
						title="PostgreSQL",
						description="There's nothing to return",
						color=COLORS["idk"]
					),
	"badges_cant_update": discord.Embed(
						title="Set Badges",
						description="I can't update them...",
						color=COLORS["idk"]
					),
	"voice_cant_delete": discord.Embed(
						title="Private Voices",
						description="I can't delete voice {voice}.. It's forbidden for me :(",
						color=COLORS["error"]
					),
	"voice_cant_create": discord.Embed(
						title="Private Voices",
						description="I can't create a voice for you.. It's forbidden for me :(",
						color=COLORS["error"]
					),
	"voice_cant_move": discord.Embed(
						title="Private Voices",
						description="I can't move you in your voice.. It's forbidden for me :(",
						color=COLORS["error"]
					),
	"cant_update_user_roles": discord.Embed(
						title="Roles",
						description="I can't update roles for {who}.. It's forbidden for me :(",
						color=COLORS["error"]
					),
	"wh_cant_execute": discord.Embed(
						title="Webhook",
						description="I can't execute that webhook.. It's forbidden for me :(",
						color=COLORS["error"]
					),
	"createvoice_cant_create": discord.Embed(
						title="Private Voices",
						description="I can't create private voices for you.. It's forbidden for me :(",
						color=COLORS["error"]
					),
	"cant_fetch_message": discord.Embed(
						title="Find Message",
						description="I can't find that message here.. It's forbidden for me :(",
						color=COLORS["error"]
					),
	"message_not_found": discord.Embed(
						title="Find Message",
						description="That message didn't find, sorry ^_^",
						color=COLORS["idk"]
					),
	"role_isnt_in_list": discord.Embed(
						title="Role",
						description="That role isn't in list.. ^_^",
						color=COLORS["idk"]
					),
	"clear_cant_delete": discord.Embed(
						title="Clear Messages",
						description="I can't delete messages here.. It's forbidden for me :(",
						color=COLORS["error"]
					),
	"cant_get_role": discord.Embed(
						title="Find Role",
						description="I can't find a role.. It's forbidden for me :(",
						color=COLORS["error"]
					)
}


lvlup_image_url = "https://discord.band/img/lvlup.png"


guilds_without_follow_us = [
	502913055559254036,
	433350258941100032,
	485400595235340303,
	455121989825331200,
	458947364137467906
]

guilds_without_more_info_in_help = [
	502913055559254036
]

COMMANDS_LIST = {
	"admin": [
				"say|say",
				"webhook|say",
				"clear|clear",
				"kick|kick",
				"ban|ban",
				"unban|ban",
				"gift|gift",
				"take|take"
			  ],
	"economy": [
				"timely|timely",
				"work|work",
				"br|br",
				"flipcoin|flip",
				"slots|slots",
				"give|give",
				"shop|shop"
			   ],
	"fun": [
				"kiss|kiss",
				"hug|hug",
				"punch|punch",
				"highfive|five",
				"wink|wink",
				"fuck|fuck",
				"drink|drink",
				"bite|bite",
				"lick|lick",
				"pat|pat",
				"slap|slap",
				"poke|poke"
			],
	"stats": [
				"$|cash",
				"top|top",
				"money|top",
				"voice|top",
				"me|me"
			 ],
	"other": [
				"help|-",
				"ping|ping",
				"avatar|avatar",
				"anime|-",
				"roll|roll",
				"server|server",
				"invite|invite",
				"about|about",
				"when|when",
				"urban|ud"
			 ]
}

ACTIVITIES = {
	"hug": {
		"tenor": "hug",
		"cmd": "hug"
	},
	"kiss": {
		"tenor": "kiss",
		"cmd": "kiss"
	},
	"wink": {
		"tenor": "wink",
		"cmd": "wink"
	},
	"punch": {
		"tenor": "punch",
		"cmd": "punch"
	},
	"drink": {
		"tenor": "drink",
		"cmd": "drink"
	},
	"five": {
		"tenor": "high-five",
		"cmd": "five"
	},
	"high-five": {
		"tenor": "high-five",
		"cmd": "five"
	},
	"highfive": {
		"tenor": "high-five",
		"cmd": "five"
	},
	"fuck": {
		"tenor": "fuck you",
		"cmd": "fuck"
	},
	"bite": {
		"tenor": "bite",
		"cmd": "bite"
	},
	"lick": {
		"tenor": "lick",
		"cmd": "lick"
	},
	"pat": {
		"tenor": "pat",
		"cmd": "pat"
	},
	"slap": {
		"tenor": "slap",
		"cmd": "slap"
	},
	"poke": {
		"tenor": "poke",
		"cmd": "poke"
	}
}


WORK_TYPES = {
	"default": {
		"exp": 1,
		"chance": 100
	},
	"worker": {
		"exp": 1.1,
		"chance": 80
	},
	"student": {
		"exp": 0.3,
		"chance": 30
	},
	"freelance": {
		"exp": 0.5,
		"chance": 50
	},
	"developer": {
		"exp": 2,
		"chance": 20
	}
}


tomori_links = '\
[Vote](https://discordbots.org/bot/491605739635212298/vote "for Tomori") \
[Donate](https://discord.band/donate "Donate") \
[YouTube](https://www.youtube.com/channel/UCxqg3WZws6KxftnC-MdrIpw "Tomori Project\'s channel") \
[Telegram](https://t.me/TomoriDiscord "Our telegram channel") \
[Website](https://discord.band "Our website") \
[VK](https://vk.com/tomori_discord "Our group on vk.com")'



cached_voice_joins = {}





mask_welcome = Image.new('L', (1002, 1002), 0)
draws = ImageDraw.Draw(mask_welcome)
draws.ellipse((471, 5) + (531, 35), fill=255)
draws.ellipse((471, 967) + (531, 997), fill=255)
draws.ellipse((5, 471) + (35, 531), fill=255)
draws.ellipse((967, 471) + (997, 531), fill=255)
draws.polygon([(531, 15), (471, 15), (15, 471), (15, 531), (471, 987), (531, 987), (987, 531), (987, 471)], fill=255)
mask_welcome = mask_welcome.resize((343, 343), Image.ANTIALIAS)
