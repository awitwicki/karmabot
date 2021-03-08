# -*- coding: utf8 -*-
#/usr/bin/python3.7

from datetime import datetime, timezone
from telegram import bot
from telegram.ext import Updater, Filters, MessageHandler, CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
import os
import codecs

from Config import Config
from mats_counter import count_mats

conf = Config('congfig.ini', ['telegram_token','destruction_timeout','database_filename'])

# https://github.com/python-telegram-bot/python-telegram-bot/wiki/Transition-guide-to-Version-12.0
bot_token = conf.Data['telegram_token']

#bot will delete his owm nessage after defined time
destruction_timeout = int(conf.Data['destruction_timeout'])

database_filename = conf.Data['database_filename']

increase_words = ['+','спасибо','дякую','благодарю', '👍', '😁', '😂', '😄', '😆', 'хаха']
decrease_words = ['-', '👎']

users = {}
user_karma = {}

bot_id = None
last_top = None

#Todo:
#ignore karmaspam from users
# def check_user_for_karma(user_id: int, dest_user_id: int):
#     try:
#         usr_ch = user_karma[user_id]
#     except:
#         return True

def get_karma(user_id : int):
    user = users[user_id]

    replytext = f"Привет {user['username']}, tвоя карма:\n\n"
    replytext += f"Карма: `{user['karma']}`\n"
    replytext += f"Сообшений: `{user['total_messages']}`\n"
    replytext += f"Матов: `{user['total_mats']}`"
    replytext += ''

    replytext = replytext.replace('_', '\\_')

    return replytext


def add_or_update_user(user_id: int, username: str, mats_count: int):
    try:
        users[user_id]['total_messages'] += 1
        users[user_id]['total_mats'] += mats_count
    except:
        users[user_id] = {}
        users[user_id]['total_messages'] = 1
        users[user_id]['total_mats'] = mats_count
        users[user_id]['username'] = username
        users[user_id]['karma'] = 0

    saveToFile(users)


def increase_karma(dest_user_id: int, message_text: str):
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
    if not is_changed:
        return

    replytext += f'карму {_username} до {new_karma}!'
    saveToFile(users)

    return replytext


def stats(update, context):
    command = update.callback_query.data
    if command == 'refresh_top':
        replytext, reply_markup = getTop()
        replytext += f'\n`Обновлено UTC {datetime.now(timezone.utc)}`'
        query = update.callback_query
        query.edit_message_text(text=replytext, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return


def getTop():
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

    replytext += "\nКулдаун топа - 5 минут"

    replytext = replytext.replace('@', '')

    keyboard = [[InlineKeyboardButton("Обновить", callback_data='refresh_top')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return replytext, reply_markup


def saveToFile(dict):
    f = codecs.open(database_filename, "w", "utf-8")
    f.write(str(users))
    f.close()


def autodelete_message(context):
    context.bot.delete_message(chat_id=context.job.context[0], message_id=context.job.context[1])


def openFile():
    if os.path.isfile(database_filename):
        global users
        users = eval(open(database_filename, 'r', encoding= 'utf-8').read())
    else:
        print ("File not exist")


def on_msg(update, context):
    global last_top
    try:
        message = update.message
        if message is None:
            return

        if message.text == None:
            return

        is_old = False
        if message.date and (datetime.now(timezone.utc) - message.date).seconds > 300:
            is_old = True

        user_id = message.from_user.id
        username = message.from_user.name
        _chat_id = message.chat_id

        messageText = message.text.lower()

        # karma message
        if message.reply_to_message and message.reply_to_message.from_user.id and user_id != message.reply_to_message.from_user.id:
            karma_changed = increase_karma(message.reply_to_message.from_user.id, messageText)
            if karma_changed and not is_old:
                msg = context.bot.send_message(_chat_id, text=karma_changed)
                context.job_queue.run_once(autodelete_message, destruction_timeout, context=[msg.chat_id, msg.message_id])

        # commands
        if messageText == "карма" and not is_old:
            reply_text = get_karma(user_id)
            msg = context.bot.send_message(_chat_id, text=reply_text, parse_mode=ParseMode.MARKDOWN)
            context.job_queue.run_once(autodelete_message, destruction_timeout, context=[msg.chat_id, msg.message_id])
        if messageText == "топ" and not is_old:
            if not last_top or (datetime.now(timezone.utc) - last_top).seconds > 300:
                reply_text, reply_markup = getTop()
                msg = context.bot.send_message(_chat_id, text=reply_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
                context.job_queue.run_once(autodelete_message, 300, context=[msg.chat_id, msg.message_id])
                last_top = datetime.now(timezone.utc)

        mats = count_mats(messageText)
        add_or_update_user(user_id, username, mats)

    except Exception as e:
        print(e)


def main():
    global bot_id

    openFile()

    updater = Updater(bot_token, use_context=True)

    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text, on_msg, edited_updates = True))
    dp.add_handler(CallbackQueryHandler(stats))

    updater.start_polling()
    bot_id = updater.bot.id
    print("Bot is started.")
    updater.idle()

if __name__ == '__main__':
    main()
