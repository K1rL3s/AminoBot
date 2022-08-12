import amino


client = amino.Client()
email = input('Email >> ')
password = input('Password >> ')
client.login(email=email, password=password)
print(f'{email} - paste it in EMAIL in src/db.py')
print(f'{password} - paste it in PASSWORD in src/db.py')
reportlink = input('Chat link where bot will send reports >> ')
print(f"'{client.get_from_code(code=reportlink).comId}' - paste it in MAIN_COMID in src/db.py")
print(f"'{client.get_from_code(code=reportlink).objectId}' - paste it in REPORT_CHAT in src/db.py")
print("""
if you want send report to the dm or private chat, use it:

import aminofix as amino
client = amino.Client()
client.login(email=EMAIL, password=PASSWORD)
sub_client = amino.SubClient(comId='MAIN_COMID', profile=client.profile)
chats_info = sub_client.get_chat_threads(start=0, size=100)
for name, chat_id in zip(chats_info.title, chats_info.chatId):
    print(name, chat_id)
""")
