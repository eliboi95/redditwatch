import sqlite3
import time

DB_PATH = "utils/wsbwatch.db"


def list_redditors_db():
    try:
        with sqlite3.connect(DB_PATH) as connection:
            cursor = connection.cursor()
            sql_statement = "SELECT user_name, rating FROM redditors;"
            redditors = cursor.execute(sql_statement).fetchall()
            return redditors
    except sqlite3.Error as e:
        print(f"Error occurred in list_redditors: {e}")
        return None


def add_redditor_db(redditor, ranking=None):
    try:
        with sqlite3.connect(DB_PATH) as connection:
            cursor = connection.cursor()
            if ranking:
                sql_statement = "INSERT INTO redditors (user_name, rating, mute_timer) VALUES (?, ?, 0);"
                cursor.execute(sql_statement, (redditor, ranking))
            else:
                sql_statement = "INSERT INTO redditors (user_name, rating, mute_timer) VALUES (?, 1, 0);"
                cursor.execute(sql_statement, (redditor,))
            connection.commit()
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error occurred in add_redditor: {e}")
        return None


def remove_redditor_db(redditor):
    try:
        with sqlite3.connect(DB_PATH) as connection:
            cursor = connection.cursor()
            sql_statement = "DELETE FROM redditors WHERE user_name = ?;"
            cursor.execute(sql_statement, (redditor,))
            connection.commit()
            return cursor.rowcount > 0  # Returns True if a row was deleted
    except sqlite3.Error as e:
        print(f"Error occurred in remove_redditor: {e}")
        return False


def add_bot_user_db(user, chat_id):
    try:
        with sqlite3.connect(DB_PATH) as connection:
            cursor = connection.cursor()
            sql_statement = "INSERT INTO users (name, chat_id) VALUES (?, ?);"
            cursor.execute(sql_statement, (user, chat_id))
            connection.commit()
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error occurred in add_bot_user: {e}")
        return None


def remove_bot_user_db(user):
    try:
        with sqlite3.connect(DB_PATH) as connection:
            cursor = connection.cursor()
            sql_statement = "DELETE FROM users WHERE name = ?;"
            cursor.execute(sql_statement, (user,))
            connection.commit()
            return cursor.rowcount > 0  # Returns True if a row was deleted
    except sqlite3.Error as e:
        print(f"Error occurred in remove_bot_user: {e}")
        return False


def save_offset_db(offset):
    try:
        with sqlite3.connect(DB_PATH) as connection:
            cursor = connection.cursor()
            sql_statement = "INSERT INTO offset (offset) VALUES (?);"
            cursor.execute(sql_statement, (offset,))
            connection.commit()
    except sqlite3.Error as e:
        print(f"Error occurred in save_offset: {e}")


def get_offset_db():
    try:
        with sqlite3.connect(DB_PATH) as connection:
            cursor = connection.cursor()
            sql_statement = "SELECT offset FROM offset ORDER BY id DESC LIMIT 1;"
            cursor.execute(sql_statement)
            result = cursor.fetchone()
            return result[0] if result else 0
    except sqlite3.Error as e:
        print(f"Error occurred in get_offset: {e}")


def get_chat_ids():
    try:
        with sqlite3.connect(DB_PATH) as connection:
            cursor = connection.cursor()
            sql_statement = "SELECT chat_id FROM users;"
            cursor.execute(sql_statement)
            result = cursor.fetchall()
            return result
    except sqlite3.Error as e:
        print(f"Error occurred in get_chat_ids: {e}")


def mute_redditor_db(redditor, mute_time):
    try:
        with sqlite3.connect(DB_PATH) as connection:
            cursor = connection.cursor()
            sql_statement = "UPDATE redditors SET mute_timer = ? WHERE user_name = ?;"
            current_time = time.time()
            mute_time_in_seconds = 24 * 60 * 60 * int(mute_time)
            time_until_unmute = current_time + mute_time_in_seconds
            cursor.execute(sql_statement, (time_until_unmute, redditor))
            connection.commit()
    except sqlite3.Error as e:
        print(f"Error occurred in mute_redditor_db: {e}")


def is_muted(redditor):
    try:
        with sqlite3.connect(DB_PATH) as connection:
            cursor = connection.cursor()
            sql_statement = "SELECT mute_timer FROM redditors WHERE user_name = ?;"
            cursor.execute(sql_statement, (redditor,))
            user_mute_timer = cursor.fetchone()
            if user_mute_timer[0] is None:
                return False
            current_time = time.time()
            print(user_mute_timer[0])
            if float(user_mute_timer[0]) > current_time:
                print(f"{redditor} is muted")
                return True
            else:
                return False
    except sqlite3.Error as e:
        print(f"Error occured in is_muted: {e}")


def unmute_redditor_db(redditor):
    try:
        with sqlite3.connect(DB_PATH) as connection:
            cursor = connection.cursor()
            sql_statement = "UPDATE redditors SET mute_timer = ? WHERE user_name = ?;"
            time_until_unmute = 0.0
            cursor.execute(sql_statement, (time_until_unmute, redditor))
            connection.commit()
    except sqlite3.Error as e:
        print(f"Error occurred in unmute_redditor_db: {e}")


def give_rockets_db(redditor, amount):
    try:
        with sqlite3.connect(DB_PATH) as connection:
            rating = get_rating(redditor) + int(amount)
            cursor = connection.cursor()
            sql_statement = "UPDATE redditors SET rating = ? WHERE user_name = ?;"
            cursor.execute(sql_statement, (rating, redditor))
            connection.commit()
    except sqlite3.Error as e:
        print(f"Error occurred in give_rockets_db: {e}")


def get_rating(redditor):
    try:
        with sqlite3.connect(DB_PATH) as connection:
            cursor = connection.cursor()
            sql_statement = "SELECT rating FROM redditors WHERE user_name = ?;"
            cursor.execute(sql_statement, (redditor,))
            result = cursor.fetchone()
            return int(result[0])
    except sqlite3.Error as e:
        print(f"Error occurred in get_rating: {e}")
