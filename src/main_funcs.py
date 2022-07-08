import aminofix as amino
import random as rnd
import requests
import time
from src.db import *
from src.messages import system_messages
from src.google_trans import google_trans_new


client = amino.Client()
client.login(email=EMAIL, password=PASSWORD)
subs = {MAIN_COMID: amino.SubClient(comId=MAIN_COMID, profile=client.profile), '0': client}  # '0' - Global Chats
database = Database(DATABASE_NAME)
print('ready!')

duels_first_dict = dict()   # userId who invited : Duel Object
duels_second_dict = dict()  # userId who was invited : userId who invited
duels_started = dict()      # userIds who is currently dueling : Duel Object

rr_rooms = dict()           # name_rr : (RR object, chat_id)
rr_members = dict()         # member_id : name_rr


# client.get_from_id
# ObjectType. 0 - user, 12 - chat
# if comId is None - check global, else - check in community. comId is str


class Duel:
    def __init__(self, first: str, second: str, f_name: str, s_name: str, chat_id: str):  # ids
        # first and second is userIds
        self.first = first
        self.second = second
        self.chat_id = chat_id
        self.first_name = f_name
        self.second_name = s_name
        self.shots = 0
        self.start = False
        if rnd.randint(0, 1) == 0:
            self.who_start_name = f_name
            self.who_start_id = first
        else:
            self.who_start_name = s_name
            self.who_start_id = second

    def start_duel(self):
        duels_started[self.first], duels_started[self.second] = self, self
        self.start = True

    def shot(self, user_id):
        if not self.start:
            return 'nostart'
        if user_id == self.who_start_id:
            if self.shots % 2 == 0:
                self.shots += 1
                return rnd.choices(('win', 'miss'), weights=(25, 75))[0]
            return 'noturn'
        if self.shots % 2 == 1:
            self.shots += 1
            return rnd.choices(('win', 'miss'), weights=(25, 75))[0]
        return 'noturn'


class RussianRoulette:
    def __init__(self, org_id: str, org_name: str, chat_id: str, com_id: str, roulette_name: str):
        self.org_id = org_id
        self.roulette_name = roulette_name
        self.chat_id = chat_id
        self.com_id = com_id
        self.started = False
        self.players = []
        self.banned = []
        self.add_member(org_id, org_name)
        self.bullets = [0, 0, 0, 0, 0, 0]
        rr_rooms[roulette_name] = tuple([self, chat_id])

    def add_member(self, player_id, player_name):
        if self.started: return 'gamestarted'
        if player_id in self.banned: return 'banned'
        self.players.append(tuple([player_id, player_name]))
        rr_members[player_id] = self.roulette_name

    def remove_member(self, player_id, player_name):
        self.players.remove(tuple([player_id, player_name]))
        if player_id != self.org_id:
            del rr_members[player_id]

    def ban(self, player_id):
        if player_id in self.banned: return 'yet'
        self.banned.append(player_id)
        return 'ok'

    def unban(self, player_id):
        if player_id not in self.banned: return 'yet'
        self.banned.remove(player_id)
        return 'ok'

    def start(self):
        if len(self.players) < 3: return 'notenough'
        if self.started: return 'started'
        self.started = True
        rnd.shuffle(self.players)
        self.new_round()

    def new_round(self):
        self.bullets = [0, 0, 0, 0, 0, 0]
        self.bullets[rnd.randint(0, len(self.bullets) - 1)] = 1

    def stop(self):
        for player in self.players:
            del rr_members[player[0]]
        if self.org_id in rr_members.keys():
            del rr_members[self.org_id]
        del rr_rooms[self.roulette_name]

    def finish(self):
        if len(self.players) == 1 and self.started:
            self.stop()
            return True
        return False

    def list(self):
        return [f'{len(self.players)} players in "{self.roulette_name}":'] + [player[1] for player in self.players]

    def kick(self, player_id):
        for player in self.players:
            if player[0] == player_id:
                self.remove_member(*player)
                self.new_round()
                return player
        return False

    def game(self, player_id, player_name, command):
        if not self.started:
            return 'notstarted'
        if player_id != self.players[0][0]:
            return 'noturn'
        elif command == 'spin':
            self.new_round()
        elif command == 'shot':
            self.bullets.append(0)
            result = self.bullets.pop(0)
            if result == 1:
                self.remove_member(player_id, player_name)
                self.new_round()
                return 'hit'
            self.players.append(self.players.pop(0))
            return 'miss'


def coin():  # useless func xd
    return rnd.choices(['heads', 'tails', 'edge'], weights=[49.75, 49.75, 0.50])[0]
    # from collections import Counter
    # print(Counter(rnd.choices(['heads', 'tails', 'edge'], weights=[49.75, 49.75, 0.50])[0] for _ in range(1000000)))
    # ~ Counter({'heads': 497835, 'tails': 497274, 'edge': 4891})


def error_catcher(func):
    def decorator(*args, **kwargs):
        try: func(*args, **kwargs)
        except Exception as e: print(f"{func.__name__}: {e}")
    return decorator


def error_message(kwargs: dict, sub_client: amino.SubClient):
    sub_client.send_message(**kwargs, message='The command failed, an error occurred. Contact the creator on github or person who hosts the bot for help.')


def func_chat_info(chat_id: str, sub_client: amino.SubClient):
    info_chat = sub_client.get_chat_thread(chatId=chat_id)
    try: chat_title = 'No info' if info_chat.title is None else info_chat.title
    except Exception: chat_title = 'No info'
    try: chat_url = client.get_from_id(objectId=info_chat.chatId, objectType=12, comId=info_chat.comId).shortUrl
    except Exception: chat_url = 'No info'
    try: chat_creator_id = 'No info' if info_chat.creatorId is None else info_chat.creatorId
    except Exception: chat_creator_id = 'No info'
    try: chat_creator_com_url = client.get_from_id(chat_creator_id, 0, comId=info_chat.comId).shortUrl
    except Exception: chat_creator_com_url = 'No info'
    try: chat_creator_global_url = client.get_from_id(chat_creator_id, 0).shortUrl
    except Exception: chat_creator_global_url = 'No info'
    try: chat_host_id = 'No info' if info_chat.json['author']['uid'] is None else info_chat.json['author']['uid']
    except Exception: chat_host_id = 'No info'
    try: chat_host_com_url = client.get_from_id(chat_host_id, 0, comId=info_chat.comId).shortUrl
    except Exception: chat_host_com_url = 'No info'
    try: chat_host_global_url = client.get_from_id(chat_host_id, 0).shortUrl
    except Exception: chat_host_global_url = 'No info'
    try: chat_language = 'No info' if info_chat.language is None else info_chat.language.upper()
    except Exception: chat_language = 'No info'
    try: chat_created = 'No info' if info_chat.createdTime is None else ' '.join(info_chat.createdTime[:-1].split('T'))
    except Exception: chat_created = 'No info'
    try: chat_users = 'No info' if info_chat.membersCount is None else info_chat.membersCount
    except Exception: chat_users = 'No info'
    try: chat_coHosts = 'No info' if info_chat.coHosts is None else len(info_chat.coHosts)
    except Exception: chat_coHosts = 'No info'
    try: chat_bannedUsers = 'No info' if info_chat.bannedUsers is None else len(info_chat.bannedUsers)
    except Exception: chat_bannedUsers = 'No info'
    try: chat_lastActivity = 'No info' if info_chat.latestActivityTime is None else ' '.join(info_chat.latestActivityTime[:-1].split('T'))
    except Exception: chat_lastActivity = 'No info'
    try: chat_tippedCoins = 'No info' if info_chat.json['tipInfo']['tippedCoins'] is None else int(info_chat.json['tipInfo']['tippedCoins'])
    except Exception: chat_tippedCoins = 'No info'
    try: chat_tippers = 'No info' if info_chat.json['tipInfo']['tippersCount'] is None else info_chat.json['tipInfo']['tippersCount']
    except Exception: chat_tippers = 'No info'
    try: chat_keywords = 'No info' if info_chat.json['keywords'] is None else info_chat.json['keywords']
    except Exception: chat_keywords = 'No info'

    # more info -> info_chat.json
    chat_message = '\n'.join((
        f'Chat title: {chat_title}',
        f'Link: {chat_url}',
        f"Chat's creator: {chat_creator_com_url}, {chat_creator_global_url}",
        f"Chat's host: {chat_host_com_url}, {chat_host_global_url}",
        f'Chat created: {chat_created}',
        f'Chat lang: {chat_language}',
        f'Members: {chat_users}',
        f'CoHosts: {chat_coHosts}',
        f'Banned: {chat_bannedUsers}',
        f'Tippers: {chat_tippers}',
        f'Tipped coins: {chat_tippedCoins}',
        f'Keywords: {chat_keywords}',
        f'Last activity: {chat_lastActivity}'
        ))
    return chat_message


def func_com_info(com_id: str):
    if int(com_id) not in list(client.sub_clients(start=0, size=100).comId):  # more than 100?
        client.join_community(comId=com_id)
    info_com = client.get_community_info(com_id)
    sub_client_for_com = amino.SubClient(comId=com_id, profile=client.profile)
    try: com_link = 'No info' if info_com.link is None else info_com.link
    except Exception: com_link = 'No info'
    try: com_name = 'No info' if info_com.name is None else info_com.name
    except Exception: com_name = 'No info'
    try: com_createdTimed = 'No info' if info_com.createdTime is None else ' '.join(info_com.createdTime[:-1].split('T'))
    except Exception: com_createdTimed = 'No info'
    try: com_comId = 'No info' if info_com.comId is None else info_com.comId
    except Exception: com_comId = 'No info'
    try: com_searchable = False if info_com.searchable is None else info_com.searchable
    except Exception: com_searchable = False
    try: com_welcomeMessageEnabled = False if info_com.welcomeMessageEnabled is None else info_com.welcomeMessageEnabled
    except Exception: com_welcomeMessageEnabled = False
    try: com_invitePermission = 'No info' if info_com.json['configuration']['general']['invitePermission'] is None else info_com.json['configuration']['general']['invitePermission']
    except Exception: com_invitePermission = 'No info'
    try: com_membersCount = 'No info' if info_com.usersCount is None else info_com.usersCount
    except Exception: com_membersCount = 'No info'
    try: com_onlineCount = sub_client_for_com.get_online_users().userProfileCount
    except Exception: com_onlineCount = 'No info'
    try: com_adminsCount = 'No info' if info_com.json['communityHeadList'] is None else len(info_com.json['communityHeadList'])
    except Exception: com_adminsCount = 'No info'
    try: com_primaryLanguage = 'No info' if info_com.primaryLanguage is None else info_com.primaryLanguage.upper()
    except Exception: com_primaryLanguage = 'No info'
    try: com_agent_name = 'No info' if info_com.agent.nickname is None else info_com.agent.nickname
    except Exception: com_agent_name = 'No info'
    try: com_agent_id = 'No info' if info_com.agent.userId is None else info_com.agent.userId
    except Exception: com_agent_id = 'No info'
    try: com_agent_global_url = 'No info' if client.get_from_id(com_agent_id, 0).shortUrl is None else client.get_from_id(com_agent_id, 0).shortUrl
    except Exception: com_agent_global_url = 'No info'
    # try: com_rankingTable = 'No info' if info_com.rankingTable.title is None else ', '.join(info_com.rankingTable.title)
    # except Exception: com_rankingTable = 'No info'
    try: com_keywords = 'No info' if info_com.keywords is None else ', '.join(info_com.keywords.split(','))
    except Exception: com_keywords = 'No info'

    if com_invitePermission == 1:
        com_invitePermission = 'Everyone can join'
    elif com_invitePermission == 2:
        com_invitePermission = 'By application'
    elif com_invitePermission == 3:
        com_invitePermission = 'By invitation'

    # more info -> info_com.json
    com_message = '\n'.join((
        f'Link: {com_link}',
        f'Community title: {com_name}',
        f'Created: {com_createdTimed}',
        f'ComId: {com_comId}',
        f'Searchable: {"Yes" if com_searchable else "No"}',
        f'Welcome message: {"Enable" if com_welcomeMessageEnabled else "Disable"}',
        f'Invite permission: {com_invitePermission}',
        f'Total members: {com_membersCount}',
        f'Online members: {com_onlineCount}',
        f'Admins: {com_adminsCount}',
        f'Language: {com_primaryLanguage}',
        f"Agent's name: {com_agent_name}",
        f"Agent's global profile: {com_agent_global_url}",
        # f'Ranking table: {com_rankingTable}',
        f'Keywords: {com_keywords}'
        ))
    return com_message


def func_sticker_info(sticker_info: dict, sub_client: amino.SubClient):
    try: sticker_icon = sticker_info['icon']
    except Exception: sticker_icon = 'No info'
    try: sticker_id = sticker_info['stickerId']
    except Exception: sticker_id = 'No info'
    try: collection_id = sticker_info['stickerCollectionId']
    except Exception: collection_id = 'No info'
    try: collection_info = sub_client.get_sticker_collection(collection_id)
    except Exception: collection_info = 'No info'
    try: collection_name = collection_info.title
    except Exception: collection_name = 'No info'
    try: collection_used_count = collection_info.usedCount
    except Exception: collection_used_count = 'No info'
    try: collention_stickers = collection_info.stickersCount
    except Exception: collention_stickers = 'No info'
    try: collection_author_id = collection_info.author.userId
    except Exception: collection_author_id = 'No info'
    try: collection_author_com_link = client.get_from_id(collection_author_id, 0).shortUrl
    except Exception: collection_author_com_link = 'No info'
    sticker_used_count = 'No info'
    # more info -> collection_info.json
    try:
        for sticker in collection_info.json['stickerList']:
            if sticker['stickerId'] == sticker_id:
                sticker_used_count = sticker['usedCount']
                break
    except Exception:
        pass

    sticker_message = '\n'.join((
        f'Sticker: {sticker_icon}',
        f'Author (global): {collection_author_com_link}',
        f'Sticker used count: {sticker_used_count}',
        f'Collection: {collection_name}',
        f'Collection stickers: {collention_stickers}',
        f'Collection used count: {collection_used_count}'
        ))
    return sticker_message


def func_user_info(user_id: str, sub_client: amino.SubClient):  # for other info check info_user.json or objects.py
    info_user_com = sub_client.get_user_info(userId=user_id)
    info_user_amino = client.get_user_info(userId=user_id)
    try: user_name = 'No info' if info_user_com.nickname is None else info_user_com.nickname
    except Exception: user_name = 'No info'
    try: user_global_url = 'No info' if client.get_from_id(user_id, 0).shortUrl is None else client.get_from_id(user_id, 0).shortUrl
    except Exception: user_global_url = 'No info'
    try: user_created = 'No info' if info_user_amino.createdTime is None else ' '.join(info_user_amino.createdTime[:-1].split('T'))
    except Exception: user_created = 'No info'
    try: user_join_com = 'No info' if info_user_com.createdTime is None else ' '.join(info_user_com.createdTime[:-1].split('T'))
    except Exception: user_join_com = 'No info'
    try: user_role = 'No info' if info_user_com.role is None else info_user_com.role
    except Exception: user_role = 'No info'
    try: user_modified = 'No info' if info_user_com.modifiedTime is None else ' '.join(info_user_com.modifiedTime[:-1].split('T'))
    except Exception: user_modified = 'No info'
    try: user_level = 'No info' if info_user_com.level is None else info_user_com.level
    except Exception: user_level = 'No info'
    try: user_reputation = 'No info' if info_user_com.reputation is None else info_user_com.reputation
    except Exception: user_reputation = 'No info'
    try: user_followers = 'No info' if info_user_com.followersCount is None else info_user_com.followersCount
    except Exception: user_followers = 'No info'
    try: user_following = 'No info' if info_user_com.followingCount is None else info_user_com.followingCount
    except Exception: user_following = 'No info'
    try: user_comments = 'No info' if info_user_com.commentsCount is None else info_user_com.commentsCount
    except Exception: user_comments = 'No info'
    try: user_posts = 'No info' if info_user_com.postsCount is None else info_user_com.postsCount
    except Exception: user_posts = 'No info'
    try: user_blogs = 'No info' if info_user_com.blogsCount is None else info_user_com.blogsCount
    except Exception: user_blogs = 'No info'
    try: user_statiy = 'No info' if info_user_com.itemsCount is None else info_user_com.itemsCount
    except Exception: user_statiy = 'No info'
    try: user_stories = 'No info' if info_user_com.storiesCount is None else info_user_com.storiesCount
    except Exception: user_stories = 'No info'
    try: user_titles = 'No info' if info_user_com.json['extensions']['customTitles'] is None else len(info_user_com.json['extensions']['customTitles'])
    except Exception: user_titles = 'No info'
    try: user_online = 'No info' if info_user_com.onlineStatus is None else info_user_com.onlineStatus
    except Exception: user_online = 'No info'

    if user_role == 0:
        user_role = 'Member'
    elif user_role == 100:
        user_role = 'Leader'
    elif user_role == 101:
        user_role = 'Curator'
    elif user_role == 102:
        user_role = 'Agent'

    user_message = '\n'.join((
        f'Nickname: {user_name}',
        f'Global profile: {user_global_url}',
        f'Account created: {user_created}',
        f'Joined to community: {user_join_com}',
        f'Role in coo: {user_role}',
        f'Profile changed: {user_modified}',
        f'Level and reputation: {user_level}, {user_reputation}',
        f'Followers: {user_followers}',
        f'Following: {user_following}',
        f'Comments: {user_comments}',
        f'Posts: {user_posts}',
        f'Articles, blogs, stories: {user_statiy}, {user_blogs}, {user_stories}',
        f'Titles: {user_titles}',
        f'Online status: {"Online" if user_online == 1 else "Offline"}'
        ))
    return user_message


def get_chat_lurkers(self: amino.SubClient, start: int = 0, size: int = 100):  # big thanks to vedansh#4039
    # dont import json bcoz it is import in amino __init__
    response = requests.get(f"{self.api}/x{self.comId}/s/live-layer/public-chats?start={start}&size={size}", headers=self.parse_headers(), proxies=self.proxies, verify=self.certificatePath)
    return amino.loads(response.text)


def id_from_url(url: str):
    url = url.strip('.,/')
    try:
        from_code = client.get_from_code(url)
        return from_code.objectId if from_code.objectId is not None else from_code.comId
    except Exception: return 'None'


def lurk_list(self: amino.SubClient, chatId: str):  # big thanks to vedansh#4039
    try:
        chat_info = get_chat_lurkers(self)
        chat_info = chat_info['userInfoInThread'][chatId]
        names = [name['nickname'] for name in chat_info['userProfileList']]
        count = chat_info['userProfileCount']
        message = [f'[bc]Lurkers: {count}\n\n'] + [f'{name}\n' for name in names]
        return ''.join(message)
    except Exception:
        return 'Chat too dead, no lurkers, bruh.'


def mafia_roles(content: list):
    names = [name.strip(',.!-() ') for name in content]
    mafia, doctor, police, lover = 0, 0, 0, 0
    if len(names) > 18 or len(names) < 3:
        return f'At least 3 and no more than 18. You have {len(names)}.'
    if len(names) >= 3: mafia += 1
    if len(names) >= 6: mafia += 1; doctor += 1
    if len(names) >= 7: police += 1
    if len(names) >= 9: mafia += 1; lover += 1
    if len(names) >= 12: mafia += 1
    innocents = len(names) - mafia - doctor - police - lover
    roles = ['Innocent'] * innocents + ['Mafia'] * mafia + ['Doctor'] * doctor + ['Police'] * police + ['Lover'] * lover
    rnd.shuffle(roles)
    mafia_message = [f'Role list for {len(names)} players:'] + [f'{name} - {roles}' for name, roles, in zip(names, roles)]
    return '\n'.join(mafia_message)


def mention(message: str, chat_info: amino.lib.util.Thread, sub_client: amino.SubClient):
    chat_id = chat_info.chatId
    if not message: message = 'Notify!\n'
    else: message = ' '.join(message) + '\n'
    chat_members = chat_info.membersCount - (chat_info.membersCount % 100 - 1)
    mention_ids = [sub_client.get_chat_users(chatId=chat_id, start=i, size=100).userId for i in range(0, chat_members, 100)]
    message_mention = [[f'<${i}$>' for i in range(len(mention_ids[j // 100]))] for j in range(0, chat_members, 100)]
    # print(message_mention, '\n', mention_ids)
    return message, message_mention, mention_ids


def report(content: list, user_id: str, com_id: str, chat_id: str, msg_time: str):
    if len(content) == 0: raise Exception('No message after "report"')  # just '!report'
    try: user_link = client.get_from_id(user_id, 0, comId=com_id).shortUrl
    except Exception: user_link = '-'
    try: chat_link = client.get_from_id(chat_id, 12, comId=com_id).shortUrl
    except Exception: chat_link = '-'
    message = f'Report from {user_link}\nChat: {chat_link}\nUTC Time: {" ".join(msg_time[:-1].split("T"))}\nMessage: {" ".join(content)}'
    return message


def roll(content: list):
    content = list(map(int, content[1:]))
    if len(content) == 0:
        return f"🎲 {rnd.randint(1, 100)} (1, 100)"
    if len(content) == 1:
        return f"🎲 {rnd.randint(1, content[0])} (1, {content[0]})"
    if len(content) == 2:
        return f"🎲 {rnd.randint(content[0], content[1])} ({content[0]}, {content[1]})"
    if len(content) == 3:
        rolls = [str(rnd.randint(content[0], content[1])) for _ in range(content[2])]
        return f"🎲 {', '.join(rolls)} ({content[0]}, {content[1]})"
    raise ValueError


def save_chat(chat_id: str, sub_client: amino.SubClient):  # Save chat info in database.db
    chat = sub_client.get_chat_thread(chat_id)
    chat_id, chat_name, chat_icon, chat_bg, chat_desc = chat.chatId, chat.title, chat.icon, chat.backgroundImage, chat.content
    return database.save_chat_in_db(chat_id, chat_name, chat_icon, chat_bg, chat_desc)


def stop_duel(first: str, second: str):
    del duels_first_dict[first]
    del duels_second_dict[second]
    if first in duels_started.keys():
        del duels_started[first]
    if second in duels_started.keys():
        del duels_started[second]


def upload_chat(chat_id: str, sub_client: amino.SubClient):
    materials = database.return_chat_info_from_db(chat_id)
    if materials is None: return False
    title, icon, bg, desc = materials[1:]
    sub_client.edit_chat(chatId=chat_id, title=title, icon=icon, content=desc)
    try: sub_client.edit_chat(chatId=chat_id, backgroundImage=bg)  # There is always an error when updating the background
    except Exception: pass
    return True
