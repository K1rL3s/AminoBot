from src.main_funcs import *


@client.event("on_chat_invite")
@error_catcher
def on_chat_invite(data):
    data = data.json
    chat_id = data['chatMessage']['threadId']
    com_id = str(data['ndcId'])
    sub_client = subs.get(com_id)
    if sub_client is None:
        sub_client = amino.SubClient(comId=com_id, profile=client.profile)
        subs[com_id] = sub_client
    sub_client.join_chat(chat_id)
    sub_client.send_message(chatId=chat_id, message=
                            '[c]Hello <3\n'
                            f'Use {PREFIX}help for command list.')


@client.event("on_text_message")
@error_catcher
def on_text_message(data):
    data = data.json
    if data['chatMessage']['content'][:len(PREFIX)] != PREFIX: return
    # Data processing
    com_id = str(data['ndcId'])
    sub_client = subs.get(com_id)
    if sub_client is None:
        sub_client = amino.SubClient(comId=com_id, profile=client.profile)
        subs[com_id] = sub_client
    chat_id = data['chatMessage']['threadId']
    author_name = data['chatMessage']['author']['nickname']
    author_id = data['chatMessage']['author']['uid']
    msg_id = data['chatMessage']['messageId']
    msg_time = data['chatMessage']['createdTime']
    msg_content = data['chatMessage']['content']
    kwargs = {"chatId": chat_id, "replyTo": msg_id}  # "comId": com_id
    content = str(msg_content).lower().split()   # after that the newlines (\n) is removed

    if len(content[0]) == len(PREFIX):  # content == "! sddfh", "/ save" etc
        return

    if author_id == client.userId:  # it was a very big exploit
        return

    content[0] = content[0][len(PREFIX):]  # from ['!duel', 'yes'] to ['duel', 'yes'] (content is lower, line 38)

    blocked = list(database.blocked_commands_in_chat(chat_id).split())
    if 'all' in blocked and content[0] not in ('block', 'allow', 'blockedlist', 'help', 'chatmanage', 'report'):
        return sub_client.send_message(**kwargs, message=f'All comands are blocked here.\nUse "{PREFIX}allow all" to disable it.')
    if content[0] in blocked:
        return sub_client.send_message(**kwargs, message='This command is blocked here.')

    chat_info = sub_client.get_chat_thread(chat_id)
    chat_host_id = chat_info.json['author']['uid']
    chat_host_name = chat_info.json['author']['nickname']
    chat_managers = [chat_host_id]
    if chat_info.coHosts is not None:
        chat_managers.extend(chat_info.coHosts)
    
    if content[0] == 'help':
        return sub_client.send_message(**kwargs, message=system_messages['help'])

    if content[0] == 'info':
        return sub_client.send_message(**kwargs, message=system_messages['info'])

    if content[0] == 'chatmanage':
        return sub_client.send_message(**kwargs, message=system_messages['chatmanage'])

    if content[0] == 'fun':
        return sub_client.send_message(**kwargs, message=system_messages['fun'])

    if content[0] == 'bot':
        return sub_client.send_message(**kwargs, message=system_messages['bot'])

    if content[0] == '8ball':
        return sub_client.send_message(**kwargs, message=f'{rnd.choice(system_messages["8ball"])}.')

    if content[0] == 'a':
        text = ' '.join(content[1:])
        if len(text) == 0: return
        translator = google_trans_new.google_translator()
        text = translator.translate(text, lang_tgt='en')
        response = requests.get(f'http://api.brainshop.ai/get?bid=153868&key=rcKonOgrUFmn5usX&uid=1&msg={text}')
        message = translator.translate(response.json()['cnt'], lang_src='en', lang_tgt='ru')  # lang_tgt - your language
        return sub_client.send_message(**kwargs, message=message)

    if content[0] == 'allow':
        if author_id not in chat_managers:
            return sub_client.send_message(**kwargs, message='You are not a Host or coHost.')
        command = content[1]
        if database.allow_command_in_chat(chat_id, command):
            return sub_client.send_message(**kwargs, message=f'Command "{command}" allowed!')
        return sub_client.send_message(**kwargs, message=f'Cant allow this command!')

    if content[0] == 'block':
        if author_id not in chat_managers:
            return sub_client.send_message(**kwargs, message='You are not a Host or coHost.')
        command = content[1]
        if database.block_command_in_chat(chat_id, command):
            return sub_client.send_message(**kwargs, message=f'Command "{command}" blocked!')
        return sub_client.send_message(**kwargs, message=f'Cant block this command!')

    if content[0] == 'blockedlist':
        blocked_list = ', '.join(sorted(list(set(database.blocked_commands_in_chat(chat_id).split()))))
        return sub_client.send_message(**kwargs, message=f'Blocked commands: {blocked_list if blocked_list else "Nope"}.')

    if content[0] == 'chat':
        if len(content) != 1:  # for call with link
            chat_id = id_from_url(content[1])
            if chat_id in ('None', None):  # bad link etc
                return sub_client.send_message(**kwargs, message='Bad argument (link).')
        try: chat_message = func_chat_info(chat_id, sub_client)
        except Exception as error:
            return sub_client.send_message(**kwargs, message=f"{error}")
        return sub_client.send_message(**kwargs, message=chat_message)

    if content[0] == 'chatimages':
        chat_icon = chat_info.icon
        chat_bg = chat_info.backgroundImage
        return sub_client.send_message(**kwargs, message=
                                       f'Icon: {"There is no icon" if chat_icon is None else chat_icon}\n'
                                       f'Background: {"There is no bg" if chat_bg is None else chat_bg}')

    if content[0] == 'choice':
        message = rnd.choice(content[1:]) if len(content[1:]) > 0 else '\n[i]You are so smart, pretty kid'
        return sub_client.send_message(**kwargs, message=f'Your random word is... {message}!')

    if content[0] == 'coin':
        return sub_client.send_message(**kwargs, message=f'Tossing a coin...\nIt is {coin()}!')

    if content[0] == 'com':
        if len(content) != 1:  # for call with link
            com_id = id_from_url(content[1])
            if com_id in ('None', None):  # bad link etc
                return sub_client.send_message(**kwargs, message='Bad argument (link).')
        try: com_message = func_com_info(com_id)
        except Exception as error:
            return sub_client.send_message(**kwargs, message=f"{error}")
        return sub_client.send_message(**kwargs, message=com_message)

    if content[0] == 'dare':
        rating = 'pg'
        if len(content) > 1:
            rating = content[1] if content[1] in ('pg', 'pg13', 'r') else 'pg'
        dare = requests.get(f'https://api.truthordarebot.xyz/api/dare?rating={rating}').json()
        sub_client.send_message(**kwargs, message=dare['question'])
    
    if content[0] == 'duel':
        if len(content) == 1:
            return sub_client.send_message(**kwargs, message=system_messages['duel'])

        if content[1] == 'no':
            if author_id in duels_first_dict.keys():
                second = duels_first_dict[author_id][1]
                stop_duel(author_id, second)
                return sub_client.send_message(**kwargs, message='Your duel request has been cancelled.')
            if author_id in duels_second_dict.keys():
                first = duels_second_dict[author_id]
                stop_duel(first, author_id)
                return sub_client.send_message(**kwargs, message='Your duel request has been cancelled.')
            return sub_client.send_message(**kwargs, message='You dont have any requests.')

        if content[1] == 'send':
            first = author_id
            second = data['chatMessage']['extensions']['mentionedArray'][0]['uid']
            if first in duels_first_dict.keys() or first in duels_second_dict.keys():
                return sub_client.send_message(**kwargs, message='You cant send duels right now.')
            if second in duels_second_dict.keys() or second in duels_first_dict.keys():
                return sub_client.send_message(**kwargs, message='Cannot send duel to this user.')
            if second == client.userId:
                return sub_client.send_message(**kwargs, message='You are so smart, pretty kid.')
            second_name = sub_client.get_user_info(userId=second).nickname
            duel = Duel(author_id, second, author_name, second_name, chat_id)
            duels_first_dict[author_id] = tuple([duel, second])
            duels_second_dict[second] = author_id
            sub_client.send_message(**kwargs, message=
                                    f'Waiting for accept the duel by {second_name}...\n'
                                    f'({PREFIX}duel yes, {PREFIX}duel no)')
            return

        if content[1] == 'yes':
            second = author_id
            if second in duels_first_dict.keys():
                return sub_client.send_message(**kwargs, message='You already have a duel request.')
            if second not in duels_second_dict.keys():
                return sub_client.send_message(**kwargs, message='You dont have any requests.')
            if second in duels_started.keys():
                return sub_client.send_message(**kwargs, message='Your duel has already begun.')
            duel = duels_first_dict[duels_second_dict[second]][0]
            duel.start_duel()
            sub_client.send_message(chatId=chat_id, mentionUserIds=[duel.first, duel.second, duel.who_start_id], message=
                                    f'The duel between <${duel.first_name}$> and <${duel.second_name}$> begins!\n'
                                    f'({PREFIX}duel shot, <${duel.who_start_name}$> starts)')
            return

        if content[1] == 'shot':
            if author_id not in duels_started.keys():
                return sub_client.send_message(**kwargs, message='You dont have a duel right now.')
            duel = duels_started[author_id]
            message = duel.shot(author_id)
            if message == 'nostart':
                return sub_client.send_message(**kwargs, message='The duel hasnt started yet!')
            if message == 'noturn':
                return sub_client.send_message(**kwargs, message='Not your turn!')
            if message == 'miss':
                return sub_client.send_message(**kwargs, message=f'Miss. Next player shot!\n'
                                                                 f'Shots: {duel.shots}')
            if message == 'win':
                name = duel.first_name if author_id == duel.first else duel.second_name
                sub_client.send_message(**kwargs, mentionUserIds=[author_id], message=
                                        f'[bc]Hit! <${name}$> won this duel!\n'
                                        f'[c]Total shots: {duel.shots}')
                stop_duel(duel.first, duel.second)
                return

    if content[0] == 'endvc':
        if client.userId not in chat_managers:
            return sub_client.send_message(**kwargs, message='Im not a Host or coHost.')
        client.end_vc(comId=com_id, chatId=chat_id)
        return sub_client.send_message(**kwargs, message='Successfully!')

    if content[0] == 'fancy':
        text = ' '.join(msg_content[len(PREFIX) + 6:].split())
        if len(text) == 0:
            text = 'Bruh'
        text = text[:60] if len(text) > 60 else text  # 2000 / 33 = 60 symbols is max, 2k is limit for message
        data = {'text': text, 'mode': 1}
        req = requests.post('https://finewords.ru/beafonts/gofonts.php', data=data)
        req.encoding = 'utf-8'
        return sub_client.send_message(**kwargs, message='\n'.join(list(set([item for item in req.json().values()]))))

    if content[0] == 'follow':
        sub_client.follow(userId=author_id)
        return sub_client.send_message(**kwargs, message='Successful subscription!')

    if content[0] == 'get':
        try: url_id = str(id_from_url(content[1]))
        except Exception: url_id = 'None'
        if url_id in ('None', None):  #  bad link etc
            return sub_client.send_message(**kwargs, message='Bad argument (link).')
        return sub_client.send_message(**kwargs, message=url_id)

    if content[0] == 'joinchat':
        if len(content) == 1:
            return sub_client.join_chat(chatId=chat_id)
        chat_from_code = client.get_from_code(content[1])
        chat_id_to_join = chat_from_code.objectId
        com_id_to_join = chat_from_code.comId
        if com_id_to_join not in client.sub_clients(start=0, size=100).comId:  # more than 100?
            try:
                client.join_community(comId=com_id_to_join)
                sub_client.send_message(**kwargs, message='Joined the community...')
            except Exception as e:
                return sub_client.send_message(**kwargs, message=f'Cannot join community.\n{e}')

        sub_client_to_join = amino.SubClient(comId=com_id_to_join, profile=client.profile)
        try:
            sub_client_to_join.join_chat(chatId=chat_id_to_join)
            return sub_client.send_message(**kwargs, message='Joined the chat!')
        except Exception as e:
            return sub_client.send_message(**kwargs, message=f'Cannot join chat.\n{e}')

    if content[0] == 'joincom':
        com_id_to_join = client.get_from_code(content[1]).comId
        if com_id_to_join in client.sub_clients(start=0, size=100).comId:  # more than 100?
            return sub_client.send_message(**kwargs, message='Im already in this community.')
        try:
            client.join_community(comId=com_id_to_join)
            return sub_client.send_message(**kwargs, message='Joined the community.')
        except Exception as e:
            return sub_client.send_message(**kwargs, message=f'Cannot join community.\n{e}.')

    if content[0] == 'kickorg':  # like a prank
        sub_client.send_message(**kwargs, mentionUserIds=[author_id], message=f'Starting host transfer to <${author_name}$>...')
        time.sleep(3)  # ???
        # The author doesnt know this system message in english language. Use translation to correct it
        sub_client.send_message(chatId=chat_id, messageType=107, message=f'Участник {author_name} стал огранизатором этого чата.')
        time.sleep(3)  # ???
        sub_client.send_message(chatId=chat_id, messageType=107, message=f'{chat_host_name} has left the conversation.')
        return

    if content[0] == 'lurk':  # thanks vedansh#4039
        return sub_client.send_message(**kwargs, message=lurk_list(sub_client, chat_id))

    if content[0] == 'mafia':
        return sub_client.send_message(**kwargs, message=mafia_roles(content[1:]))

    if content[0] == 'mention':
        if author_id != chat_host_id:
            return sub_client.send_message(**kwargs, message='You are not a Host.')
        message, mention_message, mention_users = mention(content[1:], chat_info, sub_client)
        for numbers, uids in zip(mention_message, mention_users):
            sub_client.send_message(**kwargs, message=' '.join([message] + numbers), mentionUserIds=uids)
        return

    if content[0] == 'msg':
        message = msg_content[len(PREFIX) + 4:]
        if not message: return
        try: mentions = [uid['uid'] for uid in data['chatMessage']['extensions']['mentionedArray']]
        except Exception: mentions = None
        try: reply_id = data['chatMessage']['extensions']['replyMessage']['messageId']
        except Exception: reply_id = None
        return sub_client.send_message(chatId=chat_id, replyTo=reply_id, message=message, mentionUserIds=mentions)

    if content[0] == 'ping':
        message = ('<$Working now!$>',
                   f'Host or coHost: {client.userId in chat_managers}.')
        return sub_client.send_message(**kwargs, message='\n'.join(message), mentionUserIds=[author_id])

    if content[0] == 'report':
        message = report(content[1:], author_id, com_id, chat_id, msg_time)
        subs[MAIN_COMID].send_message(chatId=REPORT_CHAT, message=message)
        return sub_client.send_message(**kwargs, message='Your message has been sent to the person who hosts the bot!')

    if content[0] == 'roll':
        return sub_client.send_message(**kwargs, message=roll(content))

    if content[0] == 'rr':
        if len(content) == 1:
            return sub_client.send_message(**kwargs, message=system_messages['rr'])

        if content[1] not in ('leave', 'start', 'shot', 'spin', 'stop', 'list', 'kick', 'create', 'join', 'ban', 'unban'):
            return

        if content[1] in ('leave', 'start', 'shot', 'spin', 'stop', 'list', 'kick', 'ban', 'unban'):
            if author_id not in rr_members.keys():
                return sub_client.send_message(**kwargs, message='You are not in the room now.')

        if content[1] in ('create', 'join'):
            if author_id in rr_members.keys():
                return sub_client.send_message(**kwargs, message='You are already in the game room.')

        if content[1] == 'create':
            room_name = content[2]
            if room_name in rr_rooms.keys():
                return sub_client.send_message(**kwargs, message='This name is taken. Use another name for room.')
            RussianRoulette(author_id, author_name, chat_id, com_id, room_name)
            return sub_client.send_message(**kwargs, message=
                                           f'[c]You created a room "{room_name}"!\n'
                                           f'[c]({PREFIX}rr join {room_name}, {PREFIX}rr list,\n'
                                           f'[c]{PREFIX}rr start, {PREFIX}rr stop,\n'
                                           f'[c]{PREFIX}rr kick @notify,\n'
                                           f'[c]{PREFIX}rr ban @notify,\n'
                                           f'[c]{PREFIX}rr unban @notify)')  # 1

        if content[1] == 'join':
            room_name = content[2]
            if room_name not in rr_rooms.keys():
                return sub_client.send_message(**kwargs, message='Wrong room name.')
            rr, rr_chat = rr_rooms[room_name]
            if rr_chat != chat_id:
                return sub_client.send_message(**kwargs, message='The game is in another chat.')
            answer = rr.add_member(author_id, author_name)
            if answer == 'gamestarted':
                return sub_client.send_message(**kwargs, message='Cannot join, game started yet.')
            if answer == 'banned':
                return sub_client.send_message(**kwargs, message='You are banned here.')
            return sub_client.send_message(**kwargs, message=f'Successfully joined the room "{room_name}"!')

        room_name = rr_members[author_id]
        rr, rr_chat = rr_rooms[room_name]

        if content[1] in ('start', 'stop', 'kick', 'ban', 'unban'):
            if author_id != rr.org_id:
                return sub_client.send_message(**kwargs, message=f'You are not the creator "{room_name}".')

        if content[1] == 'leave':
            if author_id == rr.org_id:
                return sub_client.send_message(**kwargs, message=f'Use [{PREFIX}rr stop] to delete your room.')
            rr.remove_member(author_id, author_name)
            sub_client.send_message(**kwargs, message=f'Successfully leaved from the game room "{room_name}".')
            if not rr.started: return
            chat_id = rr.chat_id
            sub_client = subs[rr.com_id]
            if rr.finish():
                return sub_client.send_message(chatId=chat_id, mentionUserIds=[rr.players[0][0]], message=
                                               f'[bc]Game over!\n[c]Winner: <${rr.players[0][1]}$>!')
            return sub_client.send_message(chatId=chat_id, mentionUserIds=[rr.players[0][0]], message=
                                           f'[c]{author_name} leaved.\n[c]Next player: <${rr.players[0][1]}$>!')

        if content[1] == 'stop':
            rr.stop()
            return sub_client.send_message(**kwargs, message=f'Succesfully delete "{room_name}".')

        if rr_chat != chat_id:  # !
            return sub_client.send_message(**kwargs, message='The game is in another chat.')

        if content[1] == 'list':
            return sub_client.send_message(**kwargs, message='\n'.join(rr.list()))

        if content[1] == 'kick':
            kick_id = data['chatMessage']['extensions']['mentionedArray'][0]['uid']
            if kick_id == rr.org_id:
                return sub_client.send_message(**kwargs, message=f'Cannot kick the owner.')
            answer = rr.kick(kick_id)
            if not answer:
                return sub_client.send_message(**kwargs, message=f'Cannot find this player in "{room_name}".')
            sub_client.send_message(**kwargs, message=f'{answer[1]} succesfully kicked!')
            if not rr.started:
                return
            if not rr.finish():
                return sub_client.send_message(**kwargs, mentionUserIds=[rr.players[0][0]], message=
                                               f'[c]{len(rr.players) - 1} round(s) left.\n'
                                               f'[c]Next player:\n[c]<${rr.players[0][1]}$>')
            return sub_client.send_message(chatId=chat_id, mentionUserIds=[rr.players[0][0]], message=
                                           f'[bc]Game over!\n[c]Winner: <${rr.players[0][1]}$>!')

        if content[1] == 'ban':
            ban_id = data['chatMessage']['extensions']['mentionedArray'][0]['uid']
            if ban_id == rr.org_id:
                return sub_client.send_message(**kwargs, message=f'Cannot ban the owner.')
            answer = rr.ban(ban_id)
            if answer == 'yet':
                return sub_client.send_message(**kwargs, message=f'This player banned yet.')
            if answer == 'ok':
                return sub_client.send_message(**kwargs, message=f'The player succesfully banned!'
                                                                 f'\nUse "{PREFIX}rr kick @notify" to kick.')
        if content[1] == 'unban':
            unban_id = data['chatMessage']['extensions']['mentionedArray'][0]['uid']
            if unban_id == rr.org_id:
                return sub_client.send_message(**kwargs, message=f'Cannot unban the owner.')
            answer = rr.unban(unban_id)
            if answer == 'yet':
                return sub_client.send_message(**kwargs, message=f'This player unbanned yet.')
            if answer == 'ok':
                return sub_client.send_message(**kwargs, message=f'The player succesfully unbanned!'
                                                                 f'\nUse "{PREFIX}rr join {room_name}" to join.')

        if content[1] == 'start':
            answer = rr.start()
            if answer == 'notenough':
                return sub_client.send_message(**kwargs, message=f'Not enough players to start. (At least 3, you have {len(rr.players)})')
            if answer == 'started':
                return sub_client.send_message(**kwargs, message=f'Game already started.')
            return sub_client.send_message(**kwargs, mentionUserIds=[rr.players[0][0]], message=
                                           f'[c]Game started!\n'
                                           f'[c]<${rr.players[0][1]}$> is first.\n'
                                           f'[c]There will be {len(rr.players) - 1} rounds and only one winner!\n'
                                           f'[c]({PREFIX}rr shot, {PREFIX}rr spin, {PREFIX}rr leave)')

        if content[1] == 'shot':
            answer = rr.game(author_id, author_name, 'shot')
            if answer == 'notstarted':
                return sub_client.send_message(**kwargs, message='Game hasnt started yet.')
            if answer == 'noturn':
                return sub_client.send_message(**kwargs, message='Not your turn!')
            if answer == 'hit':
                if len(rr.players) == 1:
                    sub_client.send_message(**kwargs, mentionUserIds=[rr.players[0][0]], message=
                                            '[BC]BOOM!\n[c]You are dead!\n')
                else: sub_client.send_message(**kwargs, mentionUserIds=[rr.players[0][0]], message=
                                              '[BC]BOOM!\n'f'[c]You are dead! '
                                              f'{len(rr.players) - 1} round(s) left.\n[c]Next player:\n[c]<${rr.players[0][1]}$>')

            if answer == 'miss':
                return sub_client.send_message(**kwargs, mentionUserIds=[rr.players[0][0]], message=
                                               '[bC]Click.\n'
                                               f'[c]You are okay, next player:\n'
                                               f'[c]<${rr.players[0][1]}$>')
            if rr.finish():
                return sub_client.send_message(chatId=chat_id, mentionUserIds=[rr.players[0][0]], message=
                                               f'[bc]Game over!\n[c]Winner: <${rr.players[0][1]}$>!')

        if content[1] == 'spin':
            answer = rr.game(author_id, author_name, 'spin')
            if answer == 'notstarted':
                return sub_client.send_message(**kwargs, message='Game hasnt started yet.')
            if answer == 'noturn':
                return sub_client.send_message(**kwargs, message='Not your turn!')
            return sub_client.send_message(**kwargs, message='Done!')

    if content[0] == 'save':
        if author_id not in chat_managers:
            return sub_client.send_message(**kwargs, message='You are not a Host or coHost.')
        if save_chat(chat_id, sub_client):
            return sub_client.send_message(**kwargs, message='The title, description, icon and background of the chat have been successfully saved.')
        return error_message(kwargs, sub_client)

    if content[0] == 'startvc':
        if client.userId not in chat_managers:
            return sub_client.send_message(**kwargs, message='Im not a Host or coHost.')
        client.start_vc(comId=com_id, chatId=chat_id)
        return sub_client.send_message(**kwargs, message='Successfully!')

    if content[0] == 'sticker':
        reply_msg = data['chatMessage']['extensions']['replyMessage']
        sticker_info = reply_msg['extensions']['sticker']
        sticker_message = func_sticker_info(sticker_info, sub_client)
        return sub_client.send_message(**kwargs, message=sticker_message)

    if content[0] == 'tr':  # thanks vedansh#4039
        try:
            reply_content = data['chatMessage']['extensions']['replyMessage']['content']
            reply_id = data['chatMessage']['extensions']['replyMessage']['messageId']
        except KeyError:
            reply_content = ' '.join(content[1:])
            reply_id = msg_id
        if reply_content is None:
            return
        if len(reply_content) == 0:
            return
        translator = google_trans_new.google_translator()
        translated_text = translator.translate(reply_content)
        detected_result = translator.detect(reply_content)[1]  # ['ru', 'russian']
        message = f'[ic]{translated_text}\n\n[c]Translated from {detected_result}.'
        return sub_client.send_message(chatId=chat_id, replyTo=reply_id, message=message)
    
    if content[0] == 'truth':
        rating = 'pg'
        if len(content) > 1:
            rating = content[1] if content[1] in ('pg', 'pg13', 'r') else 'pg'
        truth = requests.get(f'https://api.truthordarebot.xyz/api/truth?rating={rating}').json()
        sub_client.send_message(**kwargs, message=truth['question'])

    if content[0] == 'unfollow':
        sub_client.unfollow(userId=author_id)
        return sub_client.send_message(**kwargs, message='Successful unsubscribe!')

    if content[0] == 'upload':
        if author_id not in chat_managers:
            return sub_client.send_message(**kwargs, message='You are not a Host or coHost.')
        if client.userId not in chat_managers:
            return sub_client.send_message(**kwargs, message='Cant do that, not enough rights.')
        if upload_chat(chat_id, sub_client):
            return sub_client.send_message(**kwargs, message='The title, description, icon and background of the chat uploaded successfully.')
        return error_message(kwargs, sub_client)

    if content[0] == 'user':
        if len(content) != 1:  # for call with link
            author_id = id_from_url(content[1])
            if author_id in ('None', None):  # bad link etc
                return sub_client.send_message(**kwargs, message='Bad argument (link).')
        try: user_message = func_user_info(author_id, sub_client)
        except Exception as e:
            return sub_client.send_message(**kwargs, message=f"{e}")
        return sub_client.send_message(**kwargs, message=user_message)
