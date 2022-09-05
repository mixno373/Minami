import sys
import asyncio, aiohttp, logging, time, string, random, copy, json, asyncpg, dbl
from aiohttp import ClientSession
from datetime import datetime, date

import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

import time
from datetime import datetime, date, timedelta

from config.settings import settings
from config.const import *


async def working(self):
    if not SHARD_ID == 1:
        return
    await client.wait_until_ready()
    while not client.is_closed:
        now = int(time.time())
        begin_time = datetime.utcnow()
        workCooldownNow = now - WORK_COOLDOWN
        servers = await conn.fetch("SELECT discord_id, work_count FROM settings WHERE is_work = True")

        if not servers:
            await asyncio.sleep(WORK_DELAY)
            continue

        for discordId, workCount in servers:
            await conn.execute("UPDATE users SET work_time = 0, cash = cash + {workCount} WHERE work_time > 0 AND work_time <= {workCooldown}".format(
                workCount=workCount,
                workCooldown=workCooldownNow
            ))

        logger.info("working time = {}ms\n".format(int((datetime.utcnow() - begin_time).microseconds / 1000)))
        await asyncio.sleep(WORK_DELAY)


async def statuses():
    await client.wait_until_ready()
    while not client.is_closed:
        await client.change_presence(game=discord.Game(type=1, url="https://www.twitch.tv/tomori_bot", name="https://www.twitch.tv/tomori_bot"))

        servers_count = len(client.servers)
        users_count = 0
        try:
            for server in client.servers:
                users_count += server.member_count
        except:
            pass
        count = str(users_count)
        if int(users_count/1000000) > 0:
            count = str(int(users_count/1000000))+"M"
        elif int(users_count/1000) > 0:
            count = str(int(users_count/1000))+"K"
        msg = Webhook(
            web_url=wh_log_url["shards"],
            color=3553599,
            description="SHARD #{} | Servers {} | Users {}".format(SHARD_ID, servers_count, count)
        )
        await msg.post()

        await asyncio.sleep(600)



async def mutting():
    global muted_users
    await client.wait_until_ready()
    while True:
        if muted_users:
            t = int(time.time())
            min_t = min(muted_users.keys())
            if t >= min_t:
                objs = muted_users.pop(min_t)
                for o in objs:
                    if o["type"] == "unmute":
                        await u_unmute(client, conn, o["server"], o["member"])
                await asyncio.sleep(60)
            else:
                await asyncio.sleep(10)
        else:
            await asyncio.sleep(10)


async def reset_nitro():
    if not SHARD_ID == 1:
        return
    await client.wait_until_ready()
    while True:
        dat = await conn.fetch("SELECT * FROM mods WHERE type='reset_badge' AND condition::bigint < {time} AND condition::bigint > 10".format(time=int(time.time())))
        if dat:
            for user in dat:
                await asyncio.wait([
                    remove_badges(conn, user["name"], [user["value"]]),
                    conn.execute("DELETE FROM mods WHERE id={id}".format(id=user["id"]))
                ])
        await asyncio.sleep(300)
