import aminofix as amino
import random as rnd
from threading import Timer


duels_first_dict = dict()   # userId who invited : [Duel Object, userId who was invited]
duels_second_dict = dict()  # userId who was invited : userId who invited
duels_started = dict()      # userId who is currently dueling : Duel Object
rr_rooms = dict()           # name_rr : [RR Object, chat_id]
rr_members = dict()         # userId : name_rr
casino_chats = dict()       # chatId : Casino Object


class Duel:
    def __init__(self, first: str, second: str, f_name: str, s_name: str):  # ids
        # first and second is userIds
        self.first = first
        self.second = second
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
        duels_first_dict[first] = [self, second]
        duels_second_dict[second] = first

    def start_duel(self):
        duels_started[self.first], duels_started[self.second] = self, self
        self.start = True

    def stop_duel(self):
        del duels_first_dict[self.first]
        del duels_second_dict[self.second]
        if self.first in duels_started.keys():
            del duels_started[self.first]
        if self.second in duels_started.keys():
            del duels_started[self.second]

    def shot(self, user_id: str):
        if not self.start:
            return 'nostart'
        if user_id == self.who_start_id:
            if self.shots % 2 == 0:
                self.shots += 1
                shot = rnd.choices(('win', 'miss'), weights=(25, 75))[0]
                if shot == 'win':
                    self.stop_duel()
                return shot
            return 'noturn'
        if self.shots % 2 == 1:
            self.shots += 1
            shot = rnd.choices(('win', 'miss'), weights=(25, 75))[0]
            if shot == 'win':
                self.stop_duel()
            return shot
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

    def add_member(self, player_id: str, player_name: str):
        if self.started: return 'gamestarted'
        if player_id in self.banned: return 'banned'
        self.players.append(tuple([player_id, player_name]))
        rr_members[player_id] = self.roulette_name

    def remove_member(self, player_id: str, player_name: str):
        self.players.remove(tuple([player_id, player_name]))
        if player_id != self.org_id:
            del rr_members[player_id]

    def ban(self, player_id: str):
        if player_id in self.banned: return 'yet'
        self.banned.append(player_id)
        return 'ok'

    def unban(self, player_id: str):
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
        return '\n'.join([f'{len(self.players)} players in "{self.roulette_name}":'] + [player[1] for player in self.players])

    def kick(self, player_id: str):
        for player in self.players:
            if player[0] == player_id:
                self.remove_member(*player)
                self.new_round()
                return player
        return False

    def game(self, player_id: str, player_name: str, command: str):
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


class CasinoRoulette:
    def __init__(self, chat_id: str, sub_client: amino.SubClient):
        self.chat_id = chat_id
        self.players = dict()
        self.sub_client = sub_client
        self.timer = Timer(30, self.game)
        self.timer.start()
        casino_chats[chat_id] = self

    def add_player(self, player_id: str, player_name: str, player_bet: str):
        if player_id in self.players.keys():
            return 'yet'
        self.players[player_id] = (player_name, player_bet)
        return 'ok'

    def del_player(self, player_id: str):
        if player_id not in self.players.keys():
            return 'yet'
        del self.players[player_id]
        if len(self.players) == 0:
            del casino_chats[self.chat_id]
            self.timer.cancel()
            return 'deleted'
        return 'ok'

    def game(self):
        red = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
        black = {2, 4, 6, 8, 10, 11, 13, 15, 16, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}
        result_number = rnd.randint(0, 37)  # 37 = 00
        if result_number in red:
            color = 'red'
        elif result_number in black:
            color = 'black'
        else:
            color = 'green'
            
        if result_number % 2 == 1:
            odd_or_even = 'odd'
        elif result_number % 2 == 0 and result_number not in (0, 37):
            odd_or_even = 'even'
        else:
            odd_or_even = None

        result_number = str(result_number) if result_number in range(0, 37) else '00'  # [0; 36] cast to str, else "00"

        message = [f'[bc]Roulette!\n[c]Result: {result_number} {color}, {odd_or_even}.\n', 'Winners:']
        mention_users = []
        for uid, player in self.players.items():
            name, bet = player
            if bet in (result_number, color, odd_or_even):
                message.append(f'<${name}$>, bet - {bet}!')
                mention_users.append(uid)

        if len(message) == 2:
            message.append('No one ;(')

        self.sub_client.send_message(self.chat_id, '\n'.join(message), mentionUserIds=mention_users)
        del casino_chats[self.chat_id]
