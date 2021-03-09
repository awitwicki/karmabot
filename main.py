# -*- coding: utf8 -*-
#/usr/bin/python3.9

from datetime import datetime, timezone
from aiogram import Bot, types, executor
from aiogram.dispatcher import Dispatcher #Updater, Filters, MessageHandler, CallbackQueryHandler
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode

import os
import codecs
import asyncio

from Config import Config
from mats_counter import count_mats

#conf = Config('congfig.ini', ['telegram_token','destruction_timeout','database_filename'])

# https://github.com/python-telegram-bot/python-telegram-bot/wiki/Transition-guide-to-Version-12.0
#bot_token = conf.Data['telegram_token']

#bot will delete his owm nessage after defined time
#destruction_timeout = int(conf.Data['destruction_timeout'])

#database_filename = conf.Data['database_filename']

increase_words = ['+','спасибо','дякую','благодарю', '👍', '😁', '😂', '😄', '😆', 'хаха']
decrease_words = ['-', '👎']

database_filename = 'test.txt'

users = {}
user_karma = {}

bot_id = None
last_top = None

bot = Bot(token='TOKEN')
dp = Dispatcher(bot)
#Todo:
#ignore karmaspam from users
# def check_user_for_karma(user_id: int, dest_user_id: int):
#     try:
#         usr_ch = user_karma[user_id]
#     except:
#         return True

@dp.callback_query_handler()
async def stats(call: types.CallbackQuery):
    command = update.callback_query.data
    if command == 'refresh_top':
        replytext, reply_markup = getTop()
        replytext += f'\n`Обновлено UTC {datetime.utcnow()}`'
        query = call.message
        query.edit_message_text(text=replytext, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return None

@dp.message_handler()
async def on_msg(message: types.Message):

    user_id = message.from_user.id
    username = message.from_user.username
    _chat_id = message.chat.id
    messageText = message.text.lower()

    mats = await count_mats(messageText)
    await add_or_update_user(user_id, username, mats)
    
    #print(message)

    global last_top

    is_old = False

    if message.date and (datetime.utcnow() - message.date).seconds > 300:
        is_old = True

    # karma message
    
    if message.reply_to_message and message.reply_to_message.from_user.id and user_id and bot_id != message.reply_to_message.from_user.id:
        if messageText in increase_words or messageText in decrease_words and message.reply_to_message.from_user.is_bot is False:
            karma_changed = await increase_karma(message.reply_to_message.from_user.id, messageText)
            if karma_changed:
                msg = await bot.send_message(_chat_id, text=karma_changed)
                await autodelete_message(chat_id=_chat_id, message_id=msg.message_id, seconds=120)
    # commands
    elif messageText == "карма":
        #print(users)
        reply_text = await get_karma(user_id)
        msg = await bot.send_message(_chat_id, text=reply_text, parse_mode=ParseMode.MARKDOWN)
        #await autodelete_message(msg.chat_id, msg.message_id)
    elif messageText == "топ":
        if not last_top or (datetime.utcnow() - last_top).seconds > 120:
            reply_text, reply_markup = await getTop()
            msg = await bot.send_message(_chat_id, text=reply_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            await autodelete_message(msg.chat.id, msg.message_id, 120)
            last_top = datetime.utcnow()
async def get_karma(user_id : int):
    user = users[user_id]

    replytext = f"Привет {user['username']}, tвоя карма:\n\n"
    replytext += f"Карма: `{user['karma']}`\n"
    replytext += f"Сообшений: `{user['total_messages']}`\n"
    replytext += f"Матов: `{user['total_mats']}`"
    replytext += ''

    replytext = replytext.replace('_', '\\_')

    return replytext


async def add_or_update_user(user_id: int, username: str, mats_count: int):
    try:
        users[user_id]['total_messages'] += 1
        users[user_id]['total_mats'] += mats_count
    except:
        users[user_id] = {}
        users[user_id]['total_messages'] = 1
        users[user_id]['total_mats'] = mats_count
        users[user_id]['username'] = username
        users[user_id]['karma'] = 0

    await saveToFile(users)


async def increase_karma(dest_user_id: int, message_text: str):
    if dest_user_id == bot_id:
        if message_text in increase_words :
            return "спасибо ❤️"

    new_karma = None
    _username = None
    is_changed = False

    replytext = "Ты "
    for increase_word in increase_words:
        if increase_word in message_text:
            users[dest_user_id]['karma'] += 1
            new_karma = users[dest_user_id]['karma']
            _username = users[dest_user_id]['username']
            replytext += 'поднял '
            is_changed = True
            break
    if not is_changed:
        for decrease_word in decrease_words:
            if decrease_word == message_text :
                users[dest_user_id]['karma'] -= 1
                new_karma = users[dest_user_id]['karma']
                _username = users[dest_user_id]['username']
                replytext += 'понизил '
                is_changed = True
                break
    replytext += f'карму {_username} до {new_karma}!'
    await saveToFile(users)

    return replytext


async def getTop():
    replytext = "*Топ 10 кармы чата:*\n"
    users_list = [ v for k, v in users.items()]
    sorted_users_list = sorted(users_list, key = lambda i: i['karma'], reverse = True)[:10]

    for usr in sorted_users_list:
        username = usr['username']
        karma = usr['karma']
        replytext+=f'`{username}` - карма `{karma}`\n'

    replytext += "\n*Топ 10 актив чату:*\n"
    sorted_users_list = sorted(users_list, key = lambda i: i['total_messages'], reverse = True)[:10]

    for usr in sorted_users_list:
        username = usr['username']
        messagescount = usr['total_messages']
        replytext+=f'`{username}` - сообщений `{messagescount}`\n'

    replytext += "\n*Топ 10 эмоциональных личностей чата:*\n"
    sorted_users_list = sorted(users_list, key = lambda i: i['total_mats'], reverse = True)[:10]

    for usr in sorted_users_list:
        username = usr['username']
        matscount = usr['total_mats']
        replytext+=f'`{username}` - матов `{matscount}`\n'

    replytext = replytext.replace('@', '')

    keyboard = [[InlineKeyboardButton("Обновить", callback_data='refresh_top')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return replytext, reply_markup


async def saveToFile(dict):
    f = codecs.open(database_filename, "w", "utf-8")
    f.write(str(users))
    f.close()


async def autodelete_message(chat_id: int, message_id: int, seconds=0):
    await asyncio.sleep(seconds)
    await bot.delete_message(chat_id=chat_id, message_id=message_id)


async def openFile():
    if os.path.isfile(database_filename):
        global users
        users = eval(open(database_filename, 'r', encoding= 'utf-8').read())
    else:
        print ("File not exist")


#def main():
#    global bot_id
#
#    await openFile()
#
#    updater = Updater(bot_token, use_context=True)
#
#    dp = updater.dispatcher
#    dp.add_handler(MessageHandler(Filters.text, on_msg, edited_updates = True))
#    dp.add_handler(CallbackQueryHandler(stats))
#
#    updater.start_polling()
#    bot_id = updater.bot.id
#    print("Bot is started.")
#    updater.idle()

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=print("Bot is started."))    
