import sys
import asyncio, aiohttp, logging, time, string, random, copy, json, asyncpg
from aiohttp import ClientSession
from datetime import datetime, date

import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

import youtube_dl

import time
from datetime import datetime, date, timedelta

from config.settings import settings
from cogs.const import *



# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn -sn -dn -ignore_unknown'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Badges:

    def __init__(self, name=[]):
        _badges = []
        if name:
            if isinstance(name, str):
                _badges = name.lower().split(",")
            elif isinstance(name, list):
                for badge in name:
                    _badges.append(badge.lower())
        for badge in badges_list:
            badge = badge.lower()
            value = True if badge in _badges else False
            setattr(self, badge, value)

    def get_badges(self):
        _badges = []
        for badge in badges_list:
            if getattr(self, badge, None):
                _badges.append(badge)
        return _badges

    def __str__(self):
        return "<Badges: {}>".format(", ".join(self.get_badges()))

    def __repr__(self):
        return "<Badges: {}>".format(", ".join(self.get_badges()))


class Achievements:

    def __init__(self, name=[]):
        _achievements = []
        if name:
            if isinstance(name, str):
                _achievements = name.lower().split(",")
            elif isinstance(name, list):
                for achievement in name:
                    _achievements.append(achievement.lower())
        for achievement in achievements_list:
            achievement = achievement.lower()
            value = True if achievement in _achievements else False
            setattr(self, achievement, value)

    def get_achievements(self):
        _achievements = []
        for achievement in achievements_list:
            if getattr(self, achievement, None):
                _achievements.append(achievement)
        return _achievements

    def __str__(self):
        return "<Achievements: {}>".format(", ".join(self.get_achievements()))

    def __repr__(self):
        return "<Achievements: {}>".format(", ".join(self.get_achievements()))



class PostgresqlDatabase:

    def __init__(self, dsn):
        self._dsn = dsn
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(dsn=self._dsn, command_timeout=60)

    def clear(self, value):
        return str(value).replace('\\', '\\\\').replace('\'', '\\\'').replace('\"', '\\\"')

    def _where(self, where, table=None):
        w = ""
        if isinstance(where, dict):
            args = []
            for key, value in where.items():
                if table:
                    key = f"{table}.{key}"
                if isinstance(value, int):
                    arg = f"{key}={value}"
                else:
                    arg = f"{key}=E'{self.clear(value)}'"
                args.append(arg)
            if args:
                w = "WHERE " + " AND ".join(args)
        else:
            w = str(where)
        return w

    def _target(self, target):
        t = ""
        if isinstance(target, list):
            t = ", ".join(target)
        elif target:
            t = str(target)
        else:
            t = "*"
        return t

    def _order(self, order):
        o = ""
        if isinstance(order, dict):
            args = []
            for key, value in order.items():
                if value:
                    arg =f"{key} ASC"
                else:
                    arg = f"{key} DESC"
                args.append(arg)
            if args:
                o = "ORDER BY " + ", ".join(args)
        return o

    def _limit(self, limit):
        l = ""
        if limit > 0:
            l = f"LIMIT {int(limit)}"
        return l

    def _offset(self, offset):
        of = ""
        if offset > 0:
            of = f"OFFSET {int(offset)}"
        return of

    async def fetchrow(self, *args, **kwargs):
        return await self.pool.fetchrow(*args, **kwargs)

    async def fetch(self, *args, **kwargs):
        return await self.pool.fetch(*args, **kwargs)

    async def execute(self, *args, **kwargs):
        return await self.pool.execute(*args, **kwargs)

    async def select(self, target, table: str, where={}, order={}, offset=0):
        t = self._target(target)
        w = self._where(where)
        o = self._order(order)
        of = self._offset(offset)
        return await self.pool.fetchrow(f"""SELECT {t} FROM {table} {w} {o} {of};""")

    async def select_all(self, target, table: str, where={}, order={}, limit=0, offset=0):
        t = self._target(target)
        w = self._where(where)
        o = self._order(order)
        l = self._limit(limit)
        of = self._offset(offset)
        return await self.pool.fetch(f"""SELECT {t} FROM {table} {w} {o} {l} {of};""")

    async def insert(self, target: dict, table):
        assert target, "Values is None"

        names = []
        values = []
        for key, value in target.items():
            names.append(str(key))
            if isinstance(value, int):
                values.append(str(value))
            elif isinstance(value, bool):
                values.append("TRUE" if value else "FALSE")
            elif value == None:
                values.append("NULL")
            elif isinstance(value, list):
                v = []
                for val in value:
                    if isinstance(val, int):
                        v.append(str(val))
                    elif isinstance(val, bool):
                        v.append("TRUE" if val else "FALSE")
                    elif val == None:
                        v.append("NULL")
                    else:
                        v.append(f"E'{self.clear(val)}'")
                value = ",".join(v)
                values.append(f"ARRAY[{value}]")
            else:
                values.append(f"E'{self.clear(value)}'")
        names = ",".join(names)
        values = ",".join(values)
        return await self.pool.fetchrow(f"""INSERT INTO {table}({names}) VALUES ({values}) RETURNING *;""")

    async def insert_update(self, target: dict, table: str, constraint: str=None, where={}, column: str=None):
        assert target, "Values is None"

        names = []
        values = []
        for key, value in target.items():
            names.append(str(key))
            if isinstance(value, int):
                values.append(str(value))
            elif isinstance(value, bool):
                values.append("TRUE" if value else "FALSE")
            elif value == None:
                values.append("NULL")
            elif isinstance(value, list):
                v = []
                for val in value:
                    if isinstance(val, int):
                        v.append(str(val))
                    elif isinstance(val, bool):
                        v.append("TRUE" if val else "FALSE")
                    elif val == None:
                        v.append("NULL")
                    else:
                        v.append(f"E'{self.clear(val)}'")
                value = ",".join(v)
                values.append(f"ARRAY[{value}]")
            elif isinstance(value, dict):
                for _k, _v in value.items():
                    values.append(f"{_k}")
                    break
            else:
                values.append(f"E'{self.clear(value)}'")
        names = ",".join(names)
        values = ",".join(values)
        s = []
        for key, value in target.items():
            if isinstance(value, int):
                val = value
            elif isinstance(value, bool):
                val = "TRUE" if value else "FALSE"
            elif value == None:
                val = "NULL"
            elif isinstance(value, list):
                v = []
                for val_ in value:
                    if isinstance(val_, int):
                        v.append(str(val_))
                    elif isinstance(val_, bool):
                        v.append("TRUE" if val_ else "FALSE")
                    elif val_ == None:
                        v.append("NULL")
                    else:
                        v.append(f"E'{self.clear(val_)}'")
                value = ",".join(v)
                val = f"ARRAY[{value}]"
            elif isinstance(value, dict):
                for _k, _v in value.items():
                    val = f"{table}.{key}{_v}{_k}"
            else:
                val = f"E'{self.clear(value)}'"
            s.append(f"{key}={val}")
        s = ",".join(s)
        c = ""
        if constraint:
            c = f"ON CONSTRAINT {constraint}"
        w = self._where(where, table)
        if column:
            column = f"({column})"
        else:
            column = ""
        return await self.pool.fetchrow(f"""INSERT INTO {table}({names}) VALUES ({values}) ON CONFLICT {column} {c} DO UPDATE SET {s} {w} RETURNING *;""")

    async def update(self, target: dict, table: str, where={}):
        assert target, "Values is None"

        w = self._where(where)
        s = []
        for key, value in target.items():
            if isinstance(value, int):
                val = value
            elif isinstance(value, bool):
                val = "TRUE" if value else "FALSE"
            elif value == None:
                val = "NULL"
            elif isinstance(value, dict):
                for _k, _v in value.items():
                    val = f"{table}.{key}{_v}{_k}"
            else:
                val = f"E'{self.clear(value)}'"
            s.append(f"{key}={val}")
        s = ",".join(s)
        return await self.pool.fetchrow(f"""UPDATE {table} SET {s} {w} RETURNING *;""")
