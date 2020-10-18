import sqlite3
import datetime


def ensure_connection(func):
    def inner(*args, **kwargs):
        with sqlite3.connect('telegram_bot.db') as conn:
            res = func(conn=conn, *args, **kwargs)
            return res

    return inner


@ensure_connection
def init_db(conn, force: bool = False):
    c = conn.cursor()

    if force:
        c.execute('DROP TABLE IF EXISTS map_table')

    c.execute('''
        CREATE TABLE IF NOT EXISTS map_table (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            longitude   FLOAT(9,6) NOT NULL,
            latitude    FLOAT(9,6) NOT NULL,
            time_add    DATETIME NOT NULL,
            comment     VARCHAR(256),
            path_to_photo VARCHAR(256)
        )
    ''')
    conn.commit()


@ensure_connection
def add_message(conn, user_id: int, text: str):
    c = conn.cursor()
    c.execute('INSERT INTO user_message (user_id, text) VALUES (?, ?)', (user_id, text))
    conn.commit()


@ensure_connection
def add_user_location(conn, user_id: int, longitude: float, latitude: float,
                      comment: str, path_to_photo: str):
    c = conn.cursor()
    c.execute('INSERT INTO map_table (user_id, longitude, latitude, time_add, comment, path_to_photo) '
              'VALUES (?, ?, ?, ?, ?, ?)',
              (user_id, longitude, latitude, datetime.datetime.now(), comment, path_to_photo))
    conn.commit()


@ensure_connection
def get_user_location(conn, user_id: int):
    c = conn.cursor()
    c.execute('SELECT longitude, latitude, comment, path_to_photo FROM map_table WHERE user_id == (?) '
              'ORDER BY time_add DESC LIMIT 10', [(user_id)])
    return c.fetchall()


@ensure_connection
def get_user_photo(conn, user_id: int):
    c = conn.cursor()
    c.execute('SELECT path_to_photo FROM map_table WHERE user_id == (?)', [(user_id)])
    return c.fetchall()


@ensure_connection
def delete_user_location(conn, user_id: int):
    print()
    c = conn.cursor()
    c.execute('DELETE FROM map_table WHERE user_id == (?)', [(user_id)])
    conn.commit()
