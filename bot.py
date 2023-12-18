import asyncio
import datetime
import logging
from typing import Optional

import aiogram
import g4f
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import ChatActions
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from peewee import DoesNotExist

import database
import telega
from telega.Keyboard import get_delete_keyboard
from utils import get_config

# model = g4f.models.gpt_35_turbo
# model = g4f.models.gpt_4
# model = g4f.models.gpt_35_turbo_16k_0613
models = [
    # GPT-3.5 4K Context
    g4f.models.gpt_35_turbo,
    g4f.models.gpt_35_turbo_0613,

    # GPT-3.5 16K Context
    g4f.models.gpt_35_turbo_16k,
    g4f.models.gpt_35_turbo_16k_0613,

    # # GPT-4 8K Context
    g4f.models.gpt_4,
    g4f.models.gpt_4_0613,

    # GPT-4 32K Context
    g4f.models.gpt_4_32k,
    g4f.models.gpt_4_32k_0613,
]

# Установка уровня логирования
logging.basicConfig(level=logging.DEBUG)

# Получаем конфиг
config = get_config('config.yaml')

# Инициализация БД
db = database
db.db_name = config.db_name
db.create_tables()

# Создаем бота и диспетчер
if config.proxy:
    bot = Bot(token=config.bot_token, proxy=config.proxy['http'])
else:
    bot = Bot(token=config.bot_token)

dp = Dispatcher(bot, storage=MemoryStorage())


# Стэйт для установки api_key в бд
class RegistrationForm(StatesGroup):
    user_api = State()


@dp.callback_query_handler(text="delete_kb")
async def send_random_value(callback: types.CallbackQuery):
    await delete_user_api_key(callback)


async def delete_user_api_key(callback: types.CallbackQuery):
    """ Удалить из бд апи ключ пользователя """
    user = db.TelegaPerson.get(telega_id=callback.from_user.id)
    # Обновляем поле username
    setattr(user, 'api_token', "")
    # Сохраняем изменения в базе данных
    user.save()
    await callback.bot.send_message(
        callback.from_user.id, "Ваш токен удален из бд, нажмите /start что-бы внести новый")


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await bot.send_message(chat_id=message.chat.id,
                           text="Привет! Я chatgpt бот. Добро пожаловать! Напиши сюда свой вопрос.\n"
                                "Есть вопросы? -> /help")
    # await check_the_user_registration(message)


@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    await message.answer(
        "<b>Использование бота: </b>>\n"
        "<i> - Задаете вопрос, бот начинает генерировать ответ (может занимать какое-то время)\n\n</i>"
        "<i> - Если нужно допросить бота по какому-то ответу то выбираете нужное сообщение и жмете "
        "ответить\n</i> "
        "<i>в ответе задаете вопрос, бот так-же вам ответит на него через определенное время</i>",
        parse_mode="HTML")
    # await check_the_user_registration(message)


@dp.message_handler(commands=['settings'])
async def cmd_settings(message: types.Message):
    await message.answer(f"<i><b>Plug</b></i> \n"
                         f"your tg id - {message.chat.id}\n"
                         f"your username - {message.chat.username}\n"
                         f"your last name - {message.chat.last_name}\n"
                         f"your first name - {message.chat.first_name}\n",
                         parse_mode="HTML",
                         reply_markup=await get_delete_keyboard())


async def send_answer_gpt_3_5_turbo(message_from_bot_obj: aiogram.types.Message, txt: str):
    """ Пока ответ в обработке, отправлять пользователю, что печатается сообщение """

    # Запрос к GPT-3.5 Turbo
    async def get_feedback(_txt, message: types.Message) -> str:
        async def zapros(model, _txt) -> str:
            """ Отправить запрос к api """
            try:
                text = ""

                for i, response in enumerate(await g4f.ChatCompletion.create_async(
                        model=model,
                        messages=[
                            {
                                "role": "user",
                                "content": f"{_txt}"
                                f" \nВ ответе правильно сформулируй суть вопроса, "
                                f"и предоставь максимально точный ответ"
                            }
                        ],
                        proxy=config.proxy['http'],
                        temperature=0.1,
                )):
                    text += response
                if "" in text:
                    raise Exception(f"Not working - {model.name}")
                return text + f"\n\n Отработала модель {model.name}"

            except Exception as e:
                c = f"not working: {e}; {model.name}, not working: {e}"
                # print(c)
                raise Exception(c)

        max_attempts = 5
        attempts = 0

        while attempts < max_attempts:
            # Создать список задач для каждой модели
            tasks = [asyncio.create_task(zapros(model, txt)) for model in models]

            # Дождаться выполнения самой быстрой задачи
            done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

            # Получить результат самой быстрой задачи без ошибки
            for task in done:
                if not task.exception():
                    return task.result()

            attempts += 1

        return "Ошибка"


    async def wait_feedback(task):
        """ Дождаться ответа от запроса к api, пока ждет, отправлять что печатает """
        while not task.done():
            await bot.send_chat_action(message_from_bot_obj.chat.id, ChatActions.TYPING)
            await asyncio.sleep(5)

    # Создать 2 задачи, одна обращается к апи и ждет ответа, 2-ая ждет завершения первой задачи и все время выводит
    # пользователю статус, что бот печатает
    task1 = asyncio.create_task(get_feedback(txt, message_from_bot_obj))
    task2 = asyncio.create_task(wait_feedback(task1))
    await asyncio.gather(task1, task2)  # Дождаться выполнения задач

    return task1.result()


# Функция для обработки ответов на сообщения
async def handle_answer(message_from_bot_obj: aiogram.types.Message):
    """ Обработчик 'ответа' на сообщение """

    txt = '\n'.join([message_from_bot_obj.reply_to_message.text, message_from_bot_obj.text])
    final_result = await send_answer_gpt_3_5_turbo(message_from_bot_obj, txt)
    await message_from_bot_obj.reply(final_result)


# Обработка входящих сообщений
@dp.message_handler()
async def answer_question(message_from_bot: aiogram.types.Message):

    if not message_from_bot.text:
        return
    else:

        # Если сообщение является ответом на другое сообщение, вызываем соответствующую функцию
        if message_from_bot.reply_to_message is not None:
            return await handle_answer(message_from_bot)

        sent_message = await message_from_bot.reply("Отправка запроса...")  # Отправляем первое сообщение

        final_result = await send_answer_gpt_3_5_turbo(message_from_bot, message_from_bot.text)
        try:
            await sent_message.reply(
                final_result
            )
        except:
            await message_from_bot.answer("Произошла ошибка\n\n" + str(final_result),
                                          # reply_markup=await get_delete_keyboard()
                                          )


if __name__ == '__main__':
    print("HI")
    executor.start_polling(dp, skip_updates=True)
