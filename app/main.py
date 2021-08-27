# -*- coding: utf8 -*-
#/usr/bin/python3.9

import asyncio
import codecs
from datetime import datetime, timezone
import os

from aiogram import Bot, types, executor
from aiogram.dispatcher import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from aiogram.types.message import Message
from aiogram.dispatcher.filters import Filter

from NewbiesModel import NewbiesModel
from mats_counter import count_mats

bot_token = os.getenv('KARMABOT_TELEGRAM_TOKEN')
flood_timeout = int(os.getenv('KARMABOT_FLOOD_TIMEOUT', '10'))
destruction_timeout = int(os.getenv('KARMABOT_DELETE_TIMEOUT', '30'))
database_filename = 'data/' + (os.getenv('KARMABOT_DATABASE_FILENAME', 'karmabot_db.json'))
whitelist_chats = os.getenv('KARMABOT_ALLOWED_CHATS', '')

whitelist_chats: list = None if whitelist_chats == '' else [int(chat) for chat in whitelist_chats.split(',')]


increase_words = ['+','спасибо','дякую','благодарю', '👍', '😁', '😂', '😄', '😆', 'хаха']
decrease_words = ['-', '👎']

users = {}
user_karma = {}
chat_messages = {}

last_top = None

bot: Bot = Bot(token=bot_token)
dp: Dispatcher = Dispatcher(bot)

newbiesModel = NewbiesModel()
newbiesModel.upload_model("model_clf.pickle")


def is_flood_message(message: types.Message):
    chat_id: int = message.chat.id
    chat_last_msg: Message = chat_messages.get(chat_id)
    if not chat_last_msg:
        chat_messages[chat_id] = message.date
        return False
    else:
        is_flood = (message.date - chat_last_msg).seconds < flood_timeout
        chat_messages[chat_id] = message.date
        return is_flood


def add_or_update_user(func):
    async def wrapper(message: Message):
        user_id = message.from_user.id
        username = message.from_user.mention
        messageText = message.text.lower()

        mats = await count_mats(messageText)
        await add_or_update_user(user_id, username, mats)
        return await func(message)
    return wrapper

class ignore_old_messages(Filter):
    async def check(self, message: types.Message):
        return (datetime.now() - message.date).seconds < destruction_timeout

class white_list_chats(Filter):
    async def check(self, message: types.Message):
        if whitelist_chats:
            return message.chat.id in whitelist_chats
        return True


@dp.callback_query_handler(lambda c: c.data == 'refresh_top')
async def process_callback_update_top(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.message_id

    reply_text, reply_markup = await get_top()
    reply_text += f'\n`Обновлено UTC {datetime.utcnow()}`'
    await bot.edit_message_text(text=reply_text, chat_id=chat_id, message_id=message_id, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(white_list_chats(), ignore_old_messages(), regexp='(^карма$|^karma$)')
@add_or_update_user
async def on_msg_karma(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    reply_text = await get_karma(user_id)
    msg = await bot.send_message(chat_id, text=reply_text, parse_mode=ParseMode.MARKDOWN)
    await autodelete_message(msg.chat.id, msg.message_id, destruction_timeout)


@dp.message_handler(white_list_chats(), ignore_old_messages(), regexp='(^топ$|^top$)')
@add_or_update_user
async def on_msg_karma(message: types.Message):
    chat_id = message.chat.id

    global last_top
    top_list_destruction_timeout = 300
    if not last_top or (datetime.now(timezone.utc) - last_top).seconds > top_list_destruction_timeout:
        reply_text, inline_kb = await get_top()
        msg: types.Message = await bot.send_message(chat_id, text=reply_text, reply_markup=inline_kb, parse_mode=ParseMode.MARKDOWN)
        last_top = datetime.now(timezone.utc)
        await autodelete_message(msg.chat.id, msg.message_id, top_list_destruction_timeout)


@dp.message_handler(white_list_chats(), ignore_old_messages())
@add_or_update_user
async def on_msg(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    messageText = message.text.lower()

    # karma message
    if message.reply_to_message and message.reply_to_message.from_user.id and user_id != message.reply_to_message.from_user.id:
        # check user on karmaspam
        if not is_flood_message(message):
            karma_changed = await increase_karma(message.reply_to_message.from_user.id, messageText)
            if karma_changed:
                msg = await bot.send_message(chat_id, text=karma_changed, reply_to_message_id=message.message_id)
                await autodelete_message(msg.chat.id, message_id=msg.message_id, seconds=destruction_timeout)

    is_python_advice = newbiesModel.predict_senctence(messageText)
    if is_python_advice == 1:
        advice_reply = 'Кто-то сказал курс по питону?\nВот тут мы для тебя все собрали!\n\n#курсы'
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="Курсы без смс и регистрации", url="https://github.com/vviedienieiev/Learning/blob/main/python_guide_by_vv.ipynb"))

        msg = await bot.send_message(chat_id, text=advice_reply, reply_to_message_id=message.message_id, reply_markup=keyboard)


async def get_karma(user_id : int):
    user = users[user_id]

    username = user['username']
    karma = user['karma']
    total_messages = user['total_messages']
    total_mats = user['total_mats']
    mats_percent = 0

    if total_mats > 0 and total_messages > 0:
        mats_percent = total_mats / total_messages
        mats_percent *= 100
        mats_percent = round(mats_percent, 2)

    replytext = f"Привет {username}, tвоя карма:\n\n"
    replytext += f"Карма: `{karma}`\n"
    replytext += f"Сообщений: `{total_messages}`\n"
    replytext += f"Матов: `{total_mats} ({mats_percent}%)`"

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

    await save_to_file(users)


async def increase_karma(dest_user_id: int, message_text: str):
    global bot
    if dest_user_id == bot.id:
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
    if not is_changed:
        return

    replytext += f'карму {_username} до {new_karma}!'
    await save_to_file(users)

    return replytext


async def get_top():
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
        mats_count = usr['total_mats']

        total_messages = usr['total_messages']
        mats_percent = 0

        if mats_count > 0 and total_messages > 0:
            mats_percent = mats_count / total_messages
            mats_percent *= 100
            mats_percent = round(mats_percent, 2)

        replytext+=f'`{username}` - матов `{mats_count} ({mats_percent}%)`\n'

    replytext = replytext.replace('@', '')

    # keyboards.py
    inline_btn = InlineKeyboardButton('Обновить', callback_data='refresh_top')
    inline_kb = InlineKeyboardMarkup().add(inline_btn)

    return replytext, inline_kb


def read_users():
    if os.path.isfile(database_filename):
        global users
        with open(database_filename, 'r', encoding= 'utf-8') as f:
            users = eval(f.read())
    else:
        print ("File not exist")


async def save_to_file(dict):
    f = codecs.open(database_filename, "w", "utf-8")
    f.write(str(users))
    f.close()


async def autodelete_message(chat_id: int, message_id: int, seconds=0):
    await asyncio.sleep(seconds)
    await bot.delete_message(chat_id=chat_id, message_id=message_id)


if __name__ == '__main__':
    read_users()
    dp.bind_filter(white_list_chats)
    dp.bind_filter(ignore_old_messages)
    executor.start_polling(dp, on_startup=print(f"Bot is started."))
