import sqlite3


EMAIL = 'youremail'            # paste your email
PASSWORD = 'yourpassword'      # paste your password
PREFIX = '!'                   # paste your prefix
DATABASE_NAME = 'database.db'  # do not change if the name is free
MAIN_COMID = '123456789'       # paste your community id (str)
REPORT_CHAT = 'chatId'         # paste the chat id where the bot will send reports


class Database:
    def __init__(self, database_name: str):
        with sqlite3.connect(database_name, check_same_thread=False) as db:
            self.db = db
            self.sql = db.cursor()
            self.sql.execute("""
                             CREATE TABLE IF NOT EXISTS chats (
                             chat_id TEXT,
                             chat_name TEXT,
                             chat_icon TEXT,
                             chat_bg TEXT,
                             chat_desc TEXT)
                             """)
            self.db.commit()
            self.sql.execute("""
                             CREATE TABLE IF NOT EXISTS commands (
                             chat_id TEXT,
                             command TEXT)
                             """)
            self.db.commit()

    def save_chat_in_db(self, chat_id: str, chat_name: str, chat_icon: str, chat_bg: str, chat_desc: str):
        is_in_table = self.sql.execute(f"SELECT chat_id FROM chats WHERE chat_id = '{chat_id}'").fetchone()
        if is_in_table is None:
            self.sql.execute(f"""
                             INSERT INTO chats VALUES (
                             '{chat_id}',
                             '{chat_name}',
                             '{chat_icon}',
                             '{chat_bg}',
                             '{chat_desc}')
                             """)
        else:
            self.sql.execute(f"""
                             UPDATE chats SET
                             chat_id = '{chat_id}',
                             chat_name = '{chat_name}',
                             chat_icon = '{chat_icon}',
                             chat_bg = '{chat_bg}',
                             chat_desc = '{chat_desc}' 
                             WHERE chat_id = '{chat_id}'
                             """)
        self.db.commit()
        return True

    def return_chat_info_from_db(self, chat_id: str):
        chat_info = self.sql.execute(f"SELECT * FROM chats WHERE chat_id = '{chat_id}'").fetchone()
        return chat_info

    def blocked_commands_in_chat(self, chat_id: str):
        commands = self.sql.execute(f"SELECT command FROM commands WHERE chat_id = '{chat_id}'").fetchone()
        if commands is None:
            return ''
        return commands[0].strip()

    def block_command_in_chat(self, chat_id: str, command: str):
        if command in ('block', 'allow', 'blockedlist', 'report'):
            return False
        is_in_table = self.sql.execute(f"SELECT chat_id FROM commands WHERE chat_id = '{chat_id}'").fetchone()
        if is_in_table is None:
            self.sql.execute(f"INSERT INTO commands VALUES ('{chat_id}', '{command}')")
        else:
            commands = self.sql.execute(f"SELECT command FROM commands WHERE chat_id = '{chat_id}'").fetchone()[0].strip()
            commands = list(commands.split())
            if command not in commands:
                commands.append(command)
            commands = ' '.join(commands)
            self.sql.execute(f"UPDATE commands SET command = ('{commands}') WHERE chat_id = '{chat_id}'")
        self.db.commit()
        return True

    def allow_command_in_chat(self, chat_id: str, command: str):
        if command in ('block', 'allow', 'blockedlist', 'report'):
            return False
        commands = self.sql.execute(f"SELECT command FROM commands WHERE chat_id = '{chat_id}'").fetchone()
        commands = '' if commands is None else commands[0]
        commands = list(commands.split())
        if command in commands:
            commands.remove(command)
        commands = ' '.join(commands)
        self.sql.execute(f"UPDATE commands SET command = ('{commands}') WHERE chat_id = '{chat_id}'")
        self.db.commit()
        return True
