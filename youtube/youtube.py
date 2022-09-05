import os, sys, re, json, requests, time
from youtube_api.client import CommentThreadsAPI, VideoAPI

import sqlite3 as sql
from sqlite3 import Error

import detectlanguage as dtl

from config import *



def next_dtl_key():
    if len(dtl_api_keys) == 0:
        return None
    try:
        key = dtl_api_keys.pop()
        if not key:
            return False
        dtl.configuration.api_key = key
        status = dtl.user_status()
        print("\n{}\n".format(json.dumps(status, indent=4, ensure_ascii=False)))
        return True
    except:
        return False

def check_dtl():
    status = dtl.user_status()
    if status['status'] != 'ACTIVE' \
     or (int(status['requests']) >= int(status['daily_requests_limit']) and int(status['requests']) > 0) \
     or (int(status['bytes']) >= int(status['daily_bytes_limit']) and int(status['bytes']) > 0):
        if not next_dtl_key():
            raise Exception('DetectLanguage API keys are gone')
        return True
    return True

def check_lang(text):
    if not check_dtl():
        print("Can't detect text. Error with dtl service")
        return
    text = str(text)
    try:
        lang = dtl.simple_detect(text)
    except:
        lang = None
    return lang

def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sql.connect(db_file)
    except Error as e:
        print(e)
    return conn

def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def sql_add(comment):
    cur = conn.cursor()
    cur.execute(f""" INSERT INTO comments (
                        id,
                        video_id
                    ) VALUES (
                        '{comment.id}',
                        '{comment.videoId}'
                    ); """)
    conn.commit()
    cur.close()

def sql_select(target, table, where={}, limit=0):
    cur = conn.cursor()
    try:
        if isinstance(target, list):
            t = ", ".join(target)
        elif target:
            t = str(target)
        else:
            t = "*"
        w = ""
        l = ""
        if isinstance(where, dict):
            args = []
            for key, value in where.items():
                arg = str(key) + "="
                if isinstance(value, int):
                    arg = arg + str(value)
                else:
                    arg = arg + "'" + str(value).replace('\\', '\\\\').replace('\'', '\\\'') + "'"
                args.append(arg)
            if args:
                w = "WHERE " + " AND ".join(args)
        if limit > 0:
            l = "LIMIT " + str(int(limit))
        cur.execute(f""" SELECT {t} FROM {table} {w} {l}; """)
        res = cur.fetchall()
        cur.close()
        if res:
            return res
    except Exception as e:
        print(e)
        if cur:
            cur.close()
    return None

def sql_delete(comments=None):
    cur = conn.cursor()
    if not comments:
        cur.execute(f""" DELETE FROM comments; """)
    elif isinstance(comments, list):
        for comment in comments:
            cur.execute(f""" DELETE FROM comments WHERE id = '{comment.id}'; """)
    else:
        cur.close()
        return False
    conn.commit()
    cur.close()
    return True

def sql_check(comment):
    cur = conn.cursor()
    try:
        cur.execute(f""" SELECT * FROM comments WHERE id = '{comment.id}'; """)
        res = cur.fetchone()
        cur.close()
        if res:
            return True
    except:
        if cur:
            cur.close()
        pass
    return False

sql_create_comments_table = """ CREATE TABLE IF NOT EXISTS comments (
                                    p_id INTEGER PRIMARY KEY,
                                    id TEXT UNIQUE,
                                    video_id TEXT,
                                    response NUMERIC DEFAULT 0
                                ); """




yt_c_client = CommentThreadsAPI(YT_TOKEN)
yt_v_client = VideoAPI(YT_TOKEN)
if not next_dtl_key():
    raise Exception('DetectLanguage API keys are gone')

conn = create_connection(r"YtComments.db")
assert conn != None, "Can't connect to Database"

create_table(conn, sql_create_comments_table)

# sql_delete()



while True:
    for i, comment in enumerate(yt_c_client.get_comments_by_channel_id('UC2JzylaIF8qeowc7-5VwwmA'), 1):
        # if i == 100:
        #     break
        if sql_check(comment):
            break
        if len(comment.replies) > 0:
            continue
        sql_add(comment)

        lang = check_lang(comment.text[:50])

        if lang == "ja":
            whook = wh_tokens["ja"]
        elif lang == "en":
            whook = wh_tokens["en"]
        elif lang == "ru":
            whook = wh_tokens["ru"]
        else:
            whook = wh_tokens["other"]

        payload = {
            "username": comment.author.name,
            "avatar_url": comment.author.avatar,
            "embeds": [
                {
                    "color": 3553599,
                    "description": comment.text,
                    "timestamp": str(comment.publishedAt),
                    "fields": [
                        {
                            "name": "Url",
                            "value": f"https://www.youtube.com/watch?v={comment.videoId}&lc={comment.id}",
                            "inline": False
                        }
                    ]
                }
            ]
        }

        try:
            video = yt_v_client.get_video_by_id(comment.videoId)
            title = video["items"][0]["snippet"]["title"]
            payload["embeds"][0]["title"] = title
            print(title)
        except:
            pass

        requests.post(
            f"https://discordapp.com/api/webhooks/{whook}",
            json=payload,
            headers={
                'Content-Type': 'application/json'
            }
        )

        print(f"[{i}] {comment.author.name}: {comment.text}"+"\n    "+"\n    ".join(f"{com.author.name}: {com.text}" for com in comment.replies))
    time.sleep(30)
