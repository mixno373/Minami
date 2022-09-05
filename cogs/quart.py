import sys
import asyncio, aiohttp, logging, time, string, random, copy, json, asyncpg, dbl
from aiohttp import ClientSession
from datetime import datetime, date

from aiocache import cached, Cache

import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

import time
from datetime import datetime, date, timedelta

from quart import Quart, request, abort



quart_app = Quart(__name__)

@quart_app.route('/dbl', methods=['POST'])
async def interkassa():
    if request.method == 'POST':
        data = await request.json
        headers = request.headers
        print(data)
        print(headers)
        # if not data.get("bot", "") == "491605739635212298" or not headers.get("Authorization", "") == "TomoriISAnAwesomeDiscordBot":
        #     return
        # id = data.get("user", 0)
        # id = int(id)
        id = 554418178940338194
        user = quart_app.client.get_user(id)
        channel = quart_app.client.get_channel(590178222713339920)
        await channel.send(content=f"{user.mention}, thank you for your vote!")
        return "", 200
    else:
        abort(400)
