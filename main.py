import asyncio
from datetime import datetime
import os

from aiogram import Bot, types, executor
from aiogram.dispatcher import Dispatcher
from aiogram.types.message import Message
from aiogram.dispatcher.filters import Filter

from helpers import stackoverflow_search
from mats_counter import count_mats

bot_token = os.getenv('KARMABOT_TELEGRAM_TOKEN')
flood_timeout = int(os.getenv('KARMABOT_FLOOD_TIMEOUT', '10'))
destruction_timeout = int(os.getenv('KARMABOT_DELETE_TIMEOUT', '30'))
whitelist_chats = os.getenv('KARMABOT_ALLOWED_CHATS', '')

whitelist_chats: list = None if whitelist_chats == '' else [int(chat) for chat in whitelist_chats.split(',')]


chat_messages = {}


bot: Bot = Bot(token=bot_token)
dp: Dispatcher = Dispatcher(bot)


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


class ignore_old_messages(Filter):
    async def check(self, message: types.Message):
        return (datetime.now() - message.date).seconds < destruction_timeout


class white_list_chats(Filter):
    async def check(self, message: types.Message):
        if whitelist_chats:
            return message.chat.id in whitelist_chats
        return True


@dp.message_handler(white_list_chats(), ignore_old_messages(), commands=['google'])
async def google(message: types.Message):
    #check if its reply
    if not message.reply_to_message or message.reply_to_message.from_user.id == bot.id:
        reply_text = 'Команда /google должна быть ответом на чье-то сообщение в чате'
        msg = await bot.send_message(message.chat.id, text=reply_text, reply_to_message_id=message.message_id)

        await asyncio.sleep(5)
        await bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

        return

    text_to_search = message.reply_to_message.text
    if text_to_search != None:
        result = stackoverflow_search(text_to_search)
        result_str = f'Вот что я нашел по запросу\n"{text_to_search}"\n\n{result}'
        await bot.send_message(message.chat.id, text=result_str, reply_to_message_id=message.reply_to_message.message_id)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)


@dp.message_handler(white_list_chats(), ignore_old_messages())
async def on_msg(message: types.Message):
    chat_id = message.chat.id

    # is_python_advice = newbiesModel.predict_senctence(messageText)
    # if is_python_advice == 1:
    if 'курсы' in message.text.lower():
        advice_reply = 'Кто-то сказал курс по питону?\nВот тут мы для тебя все собрали!\n\n#курсы'
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="Курсы без смс и регистрации", url="https://github.com/vviedienieiev/Learning/blob/main/python_guide_by_vv.ipynb"))

        msg = await bot.send_message(chat_id, text=advice_reply, reply_to_message_id=message.message_id, reply_markup=keyboard)


async def autodelete_message(chat_id: int, message_id: int, seconds=0):
    await asyncio.sleep(seconds)
    await bot.delete_message(chat_id=chat_id, message_id=message_id)


if __name__ == '__main__':
    dp.bind_filter(white_list_chats)
    dp.bind_filter(ignore_old_messages)
    executor.start_polling(dp, on_startup=print(f"Bot is started."))
