import amino


client = amino.Client()
email = input('Email >>> ')
password = input('Password >>> ')
client.login(email=email, password=password)
print(f'{email} - paste it in EMAIL in db.py')
print(f'{password} - paste it in PASSWORD in db.py')
reportlink = input('Chat link where bot will send reports >>> ')
print(f"'{client.get_from_code(code=reportlink).comId}' - paste it in MAIN_COMID in db.py\n")
print(f"'{client.get_from_code(code=reportlink).objectId}' - paste it in REPORT_CHAT in db.py\n")
print("if you want send report to the dm or private chat, use it:\n\n"
      "import aminofix as amino\n"
      "client = amino.Client()\n"
      "client.login(email=EMAIL, password=PASSWORD)\n"
      "sub_client = amino.SubClient(comId='MAIN_COMID', profile=client.profile)\n"
      "chats_info = sub_client.get_chat_threads(start=0, size=100)\n"
      "for name, chat_id in zip(chats_info.title, chats_info.chatId):\n"
      "----print(name, chat_id)\n")
print('For any questions: discord K1rLes#3663')
