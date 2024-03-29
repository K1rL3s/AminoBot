import aminofix as amino
import random as rnd
from threading import Timer


duels_first_dict = dict()   # userId who invited : [Duel Object, userId who was invited]
duels_second_dict = dict()  # userId who was invited : userId who invited
duels_started = dict()      # userId who is currently dueling : Duel Object
rr_rooms = dict()           # name_rr : [RR Object, chat_id]
rr_members = dict()         # userId : name_rr
casino_chats = dict()       # chatId : Casino Object
blackjack_players = dict()  # userId : BJ object
ladder_members = dict()     # userId : LadderGame object


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

        
class Deck:  # Fluent Python, Luciano Ramalho
    ranks = [str(n) for n in range(2, 11)] + list('JQKA')
    suits = '♠ ♦ ♣ ♥'.split()

    def __init__(self, shuffle: bool = False):
        self._cards = [(rank, suit) for suit in self.suits for rank in self.ranks]
        if shuffle:
            rnd.shuffle(self._cards)

    def __len__(self):
        return len(self._cards)

    def __getitem__(self, position):
        return self._cards[position]

    def __setitem__(self, position, card):
        self._cards[position] = card

    def pop(self, index: int = 0):
        return self._cards.pop(index)


class BlackJack:
    def __init__(self, player_id: str):
        self.player_id = player_id
        self.deck = Deck(shuffle=True)
        self.pc_cards = []
        self.player_cards = []
        self.finish = False
        for _ in range(2):
            self._add_card(self.pc_cards)
            self._add_card(self.player_cards)
        self.cost = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
                     'J': 10, 'Q': 10, 'K': 10, 'A': 11}
        blackjack_players[player_id] = self

    def _add_card(self, hand: list):
        hand.append(self.deck.pop())

    def _calculate(self, hand: list):
        total, aces = 0, 0
        for card in hand:
            if card[0] == 'A' and aces:  # two aces = 11 + 1, three aces = 11 + 1 + 1
                total += 1
            else:
                total += self.cost[card[0]]
                if card[0] == 'A':
                    aces += 1
        if len(hand) == aces == 2:  # two aces is won
            return 21
        return total

    def end_message(self, result: str):
        self._someone_win()
        message = f'[bc]{result}\n' + self.cards_to_text(check_autowin=False)
        return message

    def _someone_win(self):
        self.finish = True
        del blackjack_players[self.player_id]

    def cards_to_text(self, check_autowin=True):
        pc_score = self._calculate(self.pc_cards)
        player_score = self._calculate(self.player_cards)
        message = [f'[c]Dealer:',
                   f'[c]{",  ".join([card[0] + card[1][0] for card in self.pc_cards])}',
                   f'[c]Value: {pc_score}.\n',
                   f'[c]You:',
                   f'[c]{",  ".join([card[0] + card[1][0] for card in self.player_cards])}',
                   f'[c]Value: {player_score}.\n']

        if check_autowin:  # win with two cards
            if player_score == 21 != pc_score:
                message = ['[bc]You win!'] + message
                self._someone_win()
            elif pc_score == 21 != player_score:
                message = ['[bc]You lose!'] + message
                self._someone_win()
            elif pc_score == player_score == 21:
                message = ["[bc]It's a draw."] + message
                self._someone_win()

        if not self.finish:  # do not show second dealer's card
            message[1] = f'[c]{",  ".join([card[0] + card[1][0] for card in self.pc_cards[:-1]])},  🃏?'
            message[2] = f'[c]Value: {self._calculate(self.pc_cards[:-1])}.\n'

        return '\n'.join(message)

    def _pc_game(self):
        pc_score = self._calculate(self.pc_cards)
        player_score = self._calculate(self.player_cards)
        if pc_score > 21 or player_score > pc_score >= 18:  # pc_score >= 18 and player_score > pc_score
            return 'win'
        if pc_score > player_score:
            return 'lose'
        if player_score == pc_score >= 18:
            return 'draw'
        self._add_card(self.pc_cards)
        return self._pc_game()

    def game(self, command: str):
        if command == 'hit':
            self._add_card(self.player_cards)
            score = self._calculate(self.player_cards)
            if score > 21:
                return self.end_message('You lose!')
            if score == 21:
                return self.end_message('You win!')
            return self.cards_to_text(check_autowin=False)

        if command == 'stand':
            result = self._pc_game()
            if result != 'draw':
                return self.end_message(f'You {result}!')
            return self.end_message("It's a draw.")


class LadderGame:
    def __init__(self, user_name, user_id):
        self.user_name = user_name
        self.user_id = user_id
        self.level = 1
        self.field = [
                      ['[bc]', '  ', 'A', 'B', 'C', 'D'],
                      ['[bic]1', '#', '#', '#', '#'],
                      ['[bc]2', '#', '#', '#', '#'],
                      ['[bc]3', '#', '#', '#', '#'],
                      ['[bc]4', '#', '#', '#', '#'],
                      ['[bc]5', '#', '#', '#', '#'],
                      ['[c]End is here.']
                     ]
        self.abcd_int = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
        ladder_members[user_id] = self

    def update_field(self, where_mine, update_level):
        updated_row = [f'[bc]{update_level}', '–', '–', '–', '–']
        updated_row[where_mine] = '*'
        self.field[update_level] = updated_row
        if update_level == 5:
            self.field[-1] = ['[ibc]End is here.']
        else:
            self.field[self.level] = [f'[ibc]{self.level}'] + self.field[self.level][1:]
        return self.view_field()

    def stop(self):
        del ladder_members[self.user_id]

    def view_field(self):
        return '\n'.join([' '.join(row) for row in self.field])

    def game(self, column):
        column = self.abcd_int[column]
        mine = rnd.randint(1, 4)
        if column == mine:
            self.stop()
            return 'gameover', self.level - 1
        if self.level == 5:
            self.stop()
            return 'win', self.update_field(mine, self.level)
        self.level += 1
        return 'okay', self.update_field(mine, self.level - 1)
