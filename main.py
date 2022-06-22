from datetime import datetime
from operator import is_
import os
from pydoc import describe
import random
from django.shortcuts import render
from flask import Flask, render_template, request, redirect, send_file
from werkzeug.utils import secure_filename

import sqlite3

from matplotlib.image import thumbnail
app = Flask(__name__)
app.config['VIDEO_UPLOAD_FOLDER'] = "files/videos"
app.config['THUMB_UPLOAD_FOLDER'] = "files/thumb"

conn = sqlite3.connect("videos.db", check_same_thread=False)
cur = conn.cursor()

l_conn = sqlite3.connect("likes.db", check_same_thread=False)
l_cur = l_conn.cursor()

u_conn = sqlite3.connect("users.db", check_same_thread=False)
u_cur = u_conn.cursor()

p_conn = sqlite3.connect("paid.db", check_same_thread=False)
p_cur = p_conn.cursor()

s_conn = sqlite3.connect("subscriptions.db", check_same_thread=False)
s_cur = s_conn.cursor()

@app.route("/")
def index():
    video_urls = []
    video_urls_row = []
    thumb_urls = []
    thumb_urls_row = []
    i = 0
    cur.execute("SELECT video_url FROM videos ORDER BY upload_at DESC")
    video_urls = cur.fetchmany(12)
    cur.execute("SELECT thumb_url FROM videos ORDER BY upload_at DESC")
    thumb_urls = cur.fetchmany(12)
    cur.execute("SELECT title FROM videos ORDER BY upload_at DESC")
    titles = cur.fetchmany(12)
    cur.execute("SELECT video_id FROM videos ORDER BY upload_at DESC")
    video_ids = cur.fetchmany(12)
    # for video_url in video_urls_array:
    #     if i % 3 != 0:
    #         video_urls_row.append(video_url[0])
    #     elif i % 3 == 0:
    #         video_urls.append(video_urls_row)
    #     i = i + 1
    # print(video_urls)
    # for thumb_url in thumb_urls_array:
    #     if i % 3 != 0:
    #         thumb_urls_row.append(thumb_url[0])
    #     elif i % 3 == 0:
    #         thumb_urls.append(thumb_urls_row)
    #     i = i + 1
    # print(thumb_urls)
    infos = []
    for thumb_url, title, video_id in zip(thumb_urls, titles, video_ids):
        infos.append({"thumb_url":thumb_url, "title": title, "video_id": video_id})
    return render_template("index.html", video_urls=video_urls, infos=infos)

@app.route("/mypage/login")
def login_page():
    return render_template("mypage/login.html")
@app.route("/login", methods=["POST"])
def login_request():
    email = request.form["email"]
    password = request.form["password"]
    
    u_cur.execute(f'SELECT user_id FROM users WHERE email="{email}" AND password="{password}"')
    try: 
        user_id = u_cur.fetchone()[0]
        print(user_id)
        return render_template("mypage/index.html", user_id=user_id)
    except:
        return render_template("mypage/denied.html")

@app.route("/subscription/unlimited", methods=["POST"])
def add_subscription():
    datas = request.get_json()
    user_id = datas["user_id"]
    months = datas["months"]
    s_cur.execute(f'INSERT INTO unlimited VALUES ("{user_id}", date("now", "+{months} months"), date("now"))')
    s_conn.commit()

@app.route("/subscription/success/unlimited")
def subscription_success():
    return render_template("subscription/unlimited.html")

@app.route("/mypage")
def mypage():
    return render_template("mypage/index.html")

@app.route("/mypage/post")
def post_page():
    return render_template("mypage/post.html")

@app.route("/mypage/register")
def register_page():
    return render_template("mypage/register.html")

@app.route("/mypage/subscription", methods=["POST"])
def subscription_page():
    return render_template("subscription/index.html")

@app.route("/register", methods=["POST"])
def register():
    email = request.form["email"]
    password = request.form["password"]
    user_id = "u" + str(random.randint(100000, 1000000))
    u_cur.execute(f'INSERT INTO users VALUES("{user_id}", "{email}", "{password}", 0)')
    u_conn.commit()
    p_cur.execute(f'CREATE TABLE {user_id} (video_id nvarchar, paid_at datetime)')
    p_conn.commit()
    return redirect("/mypage/login")
@app.route("/get_view_count", methods=["GET"])
def get_view_count():
    video_id = request.args.get("video_id")
    cur.execute(f'SELECT count FROM videos WHERE video_id={video_id}')
    count = cur.fetchone()[0]
    count += 1
    cur.execute(f"UPDATE videos set count={str(count)}")
    conn.commit()
    return {"count": count}

@app.route("/get_like_count")
def get_like_count():
    video_id = request.args.get("video_id")
    user_id = request.args.get("user_id")
    cur.execute(f'SELECT count FROM likes WHERE video_id={video_id}')
    count = cur.fetchone()[0]
    l_cur.execute(f'SELECT is_liked FROM {video_id} WHERE user_id="{user_id}"')
    is_liked = l_cur.fetchone()[0]
    return {"count": count, "is_liked":is_liked}

@app.route("/like", methods=["POST"])
def like():
    video_id = request.get_json()["video_id"]
    user_id = request.get_json()["user_id"]
    cur.execute(f'SELECT count FROM videos WHERE video_id="{video_id}"')
    l_cur.execute(f'SELECT is_liked FROM {video_id} WHERE user_id="{user_id}"')
    is_liked = l_cur.fetchone()[0]
    cur.execute(f'SELECT count FROM videos WHERE video_id="{video_id}"')
    count = cur.fetchone()[0]
    if is_liked:
        is_like = False
        count = count - 1
    else:
        is_like = True
        count += 1
    cur.execute(f'UPDATE videos set count={str(count)}')
    l_cur.execute(f'UPDATE {video_id} set is_liked={is_like} WHERE user_id="{user_id}"')
    l_conn.commit()
    return {"count": count, "is_like":is_like}

@app.route("/paid/<string:video_id>", methods=["POST"])
def paid_video(video_id):
    user_id = request.get_json()["user_id"]
    p_cur.execute(f'INSERT INTO {user_id} VALUES("{video_id}", CURRENT_TIMESTAMP)')
    p_conn.commit()
    return redirect("/watch/" + video_id)

@app.route("/search", methods=["POST"])
def search_page():
    keyword = request.form["keyword"]
    cur.execute(f'SELECT video_url FROM videos WHERE title like "%{keyword}%"')
    video_urls = cur.fetchmany(12)
    cur.execute(f'SELECT thumb_url FROM videos WHERE title like "%{keyword}%"')
    thumb_urls = cur.fetchmany(12)
    cur.execute(f'SELECT title FROM videos WHERE title like "%{keyword}%"')
    titles = cur.fetchmany(12)
    cur.execute(f'SELECT video_id FROM videos WHERE title like "%{keyword}%"')
    video_ids = cur.fetchmany(12)
    infos = []
    for thumb_url, title, video_id in zip(thumb_urls, titles, video_ids):
        infos.append({"thumb_url":thumb_url, "title": title, "video_id": video_id})
    return render_template("results.html", video_urls=video_urls, infos=infos)        
    
@app.route("/watch/<string:video_id>")
def video_page(video_id):
    viewer_id = request.cookies.get("user_id")
    cur.execute(f'SELECT video_url, count, thumb_url, user_id, upload_at, title, description, price FROM videos WHERE video_id="{video_id}"')
    print(f'SELECT video_url, count, thumb_url, user_id, upload_at, title, description, price FROM videos WHERE video_id="{video_id}"')
    video_url, count, thumb_url, user_id, upload_at, title, description, price = cur.fetchone()
    l_cur.execute(f'SELECT is_liked FROM {video_id} WHERE user_id="{viewer_id}"')
    is_liked = l_cur.fetchone()
    if is_liked != None:
        is_liked = is_liked[0]
    else:
        l_cur.execute(f'INSERT INTO {video_id} VALUES("{viewer_id}", {False})')
    cur.execute(f'SELECT count FROM videos WHERE video_id="{video_id}"')
    print(f'SELECT count FROM videos WHERE video_id="{video_id}"')
    count = int(cur.fetchone()[0])
    count = count + 1
    cur.execute(f'UPDATE videos SET count={count} WHERE video_id="{video_id}"')
    conn.commit()

    if price == 0:
        return render_template("video/index.html", video_url=video_url, count=count, thumb_url=thumb_url, user_id=user_id, upload_at=upload_at, title=title, description=description, is_liked=is_liked, price=price)
    else:
        try:
            p_cur.execute(f'SELECT paid_at FROM {viewer_id} WHERE video_id="{video_id}"')
            paid_at = p_cur.fetchone()
            if paid_at == None:
                s_cur.execute(f'SELECT started_at FROM unlimited WHERE user_id="{viewer_id}" AND expire_at > CURRENT_TIMESTAMP')
                started_at = s_cur.fetchone()
                if started_at != None:
                    return render_template("video/index.html", video_url=video_url, count=count, thumb_url=thumb_url, user_id=user_id, upload_at=upload_at, title=title, description=description, is_liked=is_liked, price=price) 
                else: 
                    return render_template("video/pay.html", video_url=video_url, count=count, thumb_url=thumb_url, user_id=user_id, upload_at=upload_at, title=title, description=description, is_liked=is_liked, price=price)
            else:
                return render_template("video/index.html", video_url=video_url, count=count, thumb_url=thumb_url, user_id=user_id, upload_at=upload_at, title=title, description=description, is_liked=is_liked, price=price) 
        except:
            return render_template("video/pay.html", video_url=video_url, count=count, thumb_url=thumb_url, user_id=user_id, upload_at=upload_at, title=title, description=description, is_liked=is_liked, price=price)
@app.route("/videos/<string:video_file_name>")
def send_video_file(video_file_name):
    print("files/videos/" + video_file_name)
    return send_file("files/videos/" + video_file_name, as_attachment=True, attachment_filename=video_file_name, mimetype="video/mp4")

@app.route("/thumbs/<string:thumb_file_name>")
def send_thumb_file(thumb_file_name):
    print("files/thumbs/" + thumb_file_name)
    return send_file("files/thumb/" + thumb_file_name, as_attachment=True, attachment_filename=thumb_file_name, mimetype="image/jpg")

@app.route("/post_video", methods=["POST"])
def post_video():
    video_file = request.files["video"]
    thumb_file = request.files["thumb"]
    video_filename = video_file.filename
    video_file.save(os.path.join(app.config['VIDEO_UPLOAD_FOLDER'], video_filename))
    thumb_filename = thumb_file.filename
    thumb_file.save(os.path.join(app.config['THUMB_UPLOAD_FOLDER'], thumb_filename))
    user_id = request.form["user_id"]
    title = request.form["title"]
    description = request.form["description"]
    price = request.form["price"]
    
    video_id = "v" + str(random.randint(10000000, 100000000))
    cur.execute(f'INSERT INTO videos VALUES("{video_id}", 0, "/videos/{video_filename}", "/thumbs/{thumb_filename}", "{user_id}", CURRENT_TIMESTAMP, "{title}", "{description}", {price})')
    conn.commit()
    l_cur.execute(f'CREATE TABLE {video_id} (user_id nvarchar, is_liked boolean)')
    l_conn.commit()
    return render_template("video/success.html", video_id=video_id)
if __name__ == "__main__":
    app.debug = True
    import ssl

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    ssl_context.load_cert_chain("fullchain.pem", "privkey.pem")
    app.config["SERVER_NAME"] = "dremi.site:443"
    #app.debug = True
    app.run(
        host="0.0.0.0", port=443, threaded=True, ssl_context=ssl_context
        )#, debug=True
    # app.run(host="0.0.0.0", port=443)