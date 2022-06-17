import sqlite3


EMAIL = 'youremail'  # paste your email
PASSWORD = 'yourpass'  # paste your password
PREFIX = '!'  # paste your prefix
MAIN_COMID = '123456789'  # paste your community id (str)
REPORT_CHAT = 'chatId'  # paste the chat id where the bot will send reports


with sqlite3.connect('database.db', check_same_thread=False) as db:
    sql = db.cursor()
    sql.execute("""
        CREATE TABLE IF NOT EXISTS chats (
        chat_id TEXT,
        chat_name TEXT,
        chat_icon TEXT,
        chat_bg TEXT,
        chat_desc TEXT)""")
    db.commit()
    sql.execute("""
        CREATE TABLE IF NOT EXISTS commands (
        chat_id TEXT,
        command TEXT)""")
    db.commit()


def save_chat_in_db(chat_id, chat_name, chat_icon, chat_bg, chat_desc):
    with sqlite3.connect('database.db', check_same_thread=False) as db:
        sql = db.cursor()
        chat_ids = tuple([i[0] for i in sql.execute("SELECT chat_id FROM chats")])
        if chat_id in chat_ids:
            sql.execute(f"UPDATE chats SET chat_id = '{chat_id}', chat_name = '{chat_name}', chat_icon = '{chat_icon}',"
                        f"chat_bg = '{chat_bg}', chat_desc = '{chat_desc}' WHERE chat_id = '{chat_id}'")
        else:
            sql.execute(f"INSERT INTO chats VALUES ('{chat_id}', '{chat_name}', '{chat_icon}', '{chat_bg}', '{chat_desc}')")
        db.commit()
        return True


def return_chat_info_from_db(chat_id):
    with sqlite3.connect('database.db', check_same_thread=False) as db:
        sql = db.cursor()
        s = sql.execute(f"SELECT * FROM chats WHERE chat_id = '{chat_id}'")
        chat_info = s.fetchone()
        return chat_info


def blocked_commands(chat_id):
    with sqlite3.connect('database.db', check_same_thread=False) as db:
        sql = db.cursor()
        if chat_id not in [i[0] for i in sql.execute("SELECT chat_id FROM commands")]: return ''
        commands = sql.execute(f"SELECT command FROM commands WHERE chat_id = '{chat_id}'").fetchone()[0]
        return commands.strip()


def block_command(chat_id, command):
    if command in ('block', 'allow', 'blockedlist', 'report'): return False
    with sqlite3.connect('database.db', check_same_thread=False) as db:
        sql = db.cursor()
        chat_ids = [i[0] for i in sql.execute("SELECT chat_id FROM commands")]
        if chat_id in chat_ids:
            commands = sql.execute(f"SELECT command FROM commands WHERE chat_id = '{chat_id}'").fetchone()[0].strip()
            commands += ' ' + command
            sql.execute(f"UPDATE commands SET command = ('{commands.strip()}') WHERE chat_id = '{chat_id}'")
            db.commit()
        else:
            sql.execute(f"INSERT INTO commands VALUES ('{chat_id}', '{command.strip()}')")
            db.commit()
        return True


def allow_command(chat_id, command):
    if command in ('block', 'allow', 'blockedlist', 'report', 'flag'): return False
    with sqlite3.connect('database.db', check_same_thread=False) as db:
        sql = db.cursor()
        commands = sql.execute(f"SELECT command FROM commands WHERE chat_id = '{chat_id}'").fetchone()
        commands = '' if commands is None else commands[0]
        commands = commands.replace(command, '')
        sql.execute(f"UPDATE commands SET command = ('{commands.strip()}') WHERE chat_id = '{chat_id}'")
        db.commit()
        return True
