import os, sys
import discord
import asyncio, aiohttp
import requests
import logging
import time
from datetime import datetime, date, timedelta, timezone
from email.utils import parsedate_to_datetime
import string
import random
import copy
import json, yaml
import asyncpg
import re

from quart import Quart, request, abort, jsonify, send_file, redirect

from discord import Webhook, AsyncWebhookAdapter, Embed

from cogs.util import *
from cogs.const import *
from cogs.classes import *
from config.settings import settings



__name__ = "Minami-API"
__version__ = "1.2.0"

app = Quart(__name__)

@app.before_first_request
async def create_db():
    try:
        app.pool = PostgresqlDatabase(dsn=f'postgres://{settings["base_user"]}:{settings["base_password"]}@localhost:5432/minami')
        await app.pool.connect()
        print('PostgreSQL successfully loaded!')
    except Exception as e:
        print('PostgreSQL doesn\'t load.\n'+str(e))
        exit(0)





@app.route('/discord')
def discord_redirect():
    return redirect("https://discord.gg/BedkuvFTuU", code=301)

@app.route('/cd')
def cd_redirect():
    return redirect("https://www.cdjapan.co.jp/person/700823407", code=301)

@app.route('/goods')
def goods_redirect():
    return redirect("https://minami-goods.com/", code=301)

@app.route('/inst')
def inst_redirect():
    return redirect("https://instagram.com/373off", code=301)

@app.route('/live')
def live_redirect():
    return redirect("https://twitcasting.tv/373staff", code=301)

@app.route('/youtube')
def youtube_redirect():
    return redirect("https://www.youtube.com/c/%E7%BE%8E%E6%B3%A2minami373writer", code=301)

@app.route('/collections')
def collections_redirect():
    return redirect("https://373minami.collections.repl.co/", code=301)


@app.route('/android', methods=HTTP_METHODS)
@app.route('/android/', methods=HTTP_METHODS)
async def android_():
    if request.method == 'GET':
        headers, data, args, form = await request_parse(request)

        if not os.path.isfile(APP_LATEST_UPDATE_URI):
            return file_unavailable_error()

        return await send_file(APP_LATEST_UPDATE_URI, attachment_filename=f"Lilac v{APP_LATEST_VERSION}.apk", as_attachment=True)

    return unsupported_method_error()


@app.route('/api/news', methods=HTTP_METHODS)
async def news__():
    if request.method == 'GET':
        headers, data, args, form = await request_parse(request)

        ret = []

        page = get_int_from_data(data, "page", 1, 100, 1)
        limit = get_int_from_data(data, "limit", 1, 50, 25)

        offset = ((page - 1) * limit)

        await app.pool.insert_update({
            "ip": headers.get("X-Remote-Ip", "-"),
            "modified_at": datetime.utcnow(),
            "uses": {1: "+"}
        }, "app_stats", column="ip")

        news_info = await app.pool.select_all("*", "news", order={"created_at": False}, offset=offset, limit=limit)

        for n_info in news_info:
            ret.append({
                "id": n_info["id"],
                "title": n_info["title"],
                "description": n_info["description"],
                "icon_url": n_info["icon_url"],
                "created_at": n_info["created_at"]
            })

        return jsonify(ret)

    return unsupported_method_error()

@app.route('/api/zapier/twitter', methods=HTTP_METHODS)
async def zapier_twitter__():
    if request.method == 'POST':
        headers, data, args, form = await request_parse(request)

        try:
            twit_url = get_value_from_data(data, "url")
            twit_text = get_value_from_data(data, "text")
            twit_attachment_pic = get_value_from_data(data, "attachment_pic", DEFAULT_PIC_URL)
            twit_created_at = get_value_from_data(data, "created_at")

            twit_text = re.sub(r"https:(\/\/t\.co\/([A-Za-z0-9]|[A-Za-z]){10})", "", twit_text)
            twit_text = twit_text.rstrip()

            twit_created_at = parsedate_to_datetime(twit_created_at)

            dt_now = datetime.now(tz=timezone.utc)
            twit_created_at = datetime.fromtimestamp(twit_created_at.timestamp(), tz=timezone.utc)

            await app.pool.insert({
                "title": "Twitter.com/373STAFF",
                "description": f"{twit_text}\n\n{twit_url}",
                "icon_url": twit_attachment_pic,
                "flair": "OFFICIAL",
                "created_at": twit_created_at
            }, "news")


            embed = discord.Embed(colour=COLORS["minami_main_color"])
            embed.set_author(
            	name="Twitter.com/373STAFF",
            	icon_url="https://pbs.twimg.com/profile_images/1171741925566582784/cn_0ISeY_400x400.jpg"
            )
            embed.description = f"{twit_text}\n\n{twit_url}"
            embed.timestamp = twit_created_at
            embed.set_image(url=twit_attachment_pic)

            async with aiohttp.ClientSession() as session:
            	webhook = Webhook.from_url(WH_LOG_URL["news"], adapter=AsyncWebhookAdapter(session))
            	try:
            		await webhook.send(embed=embed)
            	except Exception as e:
            		pass
        except Exception as e:
            print(f"zapier/twitter: {get_value_from_data(data, 'url')} | {e}")

        return "", 200

    return unsupported_method_error()

@app.route('/api/zapier/youtube', methods=HTTP_METHODS)
async def zapier_youtube__():
    if request.method == 'POST':
        headers, data, args, form = await request_parse(request)

        try:
            youtube_url = get_value_from_data(data, "url")
            youtube_title = get_value_from_data(data, "title")
            youtube_description = get_value_from_data(data, "description")
            youtube_pic_url = get_value_from_data(data, "pic_url", DEFAULT_PIC_URL)
            youtube_created_at = get_value_from_data(data, "created_at", datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z"))

            youtube_created_at = get_utc_from_string(youtube_created_at)
            print(youtube_created_at)

            await app.pool.insert({
                "title": youtube_title,
                "description": f"{youtube_description}\n\n{youtube_url}",
                "icon_url": youtube_pic_url,
                "flair": "OFFICIAL",
                "created_at": youtube_created_at
            }, "news")


            embed = discord.Embed(colour=COLORS["minami_main_color"])
            embed.set_author(
            	name=youtube_title,
            	icon_url=youtube_pic_url
            )
            embed.description = f"{youtube_description}\n\n{youtube_url}"
            embed.timestamp = youtube_created_at
            embed.set_image(url=youtube_pic_url)

            async with aiohttp.ClientSession() as session:
            	webhook = Webhook.from_url(WH_LOG_URL["news"], adapter=AsyncWebhookAdapter(session))
            	try:
            		await webhook.send(content="@everyone", embed=embed)
            	except Exception as e:
            		pass
        except Exception as e:
            print(f"zapier/youtube: {get_value_from_data(data, 'url')} | {e}")

        return "", 200

    return unsupported_method_error()


app.run(host='localhost', port=8082, debug=False, use_reloader=True)
