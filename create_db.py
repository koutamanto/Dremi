import sqlite3

conn = sqlite3.connect("videos.db")
cur = conn.cursor()
l_conn = sqlite3.connect("likes.db")
l_cur = l_conn.cursor()

u_conn = sqlite3.connect("users.db")
u_cur = u_conn.cursor()

p_conn = sqlite3.connect("paid.db")
p_cur = p_conn.cursor()

s_conn = sqlite3.connect("subscriptions.db", check_same_thread=False)
s_cur = s_conn.cursor()

s_cur.execute(f'DROP TABLE unlimited')
s_conn.commit()
s_cur.execute(f'CREATE TABLE unlimited ( user_id nvarchar, expire_at datetime, started_at datetime)')
s_conn.commit()

# l_cur.execute(f'CREATE TABLE {video_id} (user_id nvarchar, is_liked boolean')

# cur.execute(f"DROP TABLE videos")
# conn.commit()
# cur.execute(f'CREATE TABLE videos ( video_id nvarchar , count int, video_url nvarchar, thumb_url nvarchar, user_id nvarchar, upload_at datetime, title nvarchar, description nvarchar, price int)')
# conn.commit()

# u_cur.execute("DROP TABLE users")
# u_conn.commit()
# u_cur.execute("CREATE TABLE users( user_id nvarchar, email nvarchar, password nvarchar, follower int)")
# u_conn.commit()

