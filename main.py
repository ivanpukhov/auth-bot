from sqlite3 import connect

import bcrypt
from aiogram import Bot, types, Dispatcher, executor

bot = Bot(token='6287396523:AAHU8Ak8hV_1GWhZngLDQ3EO0-Jxy0NyuP4')
dp = Dispatcher(bot)

user_data = {}


async def send_action_buttons(chat_id):
    buttons = [
        types.InlineKeyboardButton(text='Вход', callback_data='login'),
        types.InlineKeyboardButton(text='Регистрация', callback_data='register'),
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(*buttons)
    await bot.send_message(chat_id, 'Выберите действие:', reply_markup=keyboard)


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await send_action_buttons(message.chat.id)


@dp.callback_query_handler(lambda c: c.data in ['login', 'register'])
async def process_callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    action = callback_query.data
    user_data[callback_query.from_user.id] = {'action': action}

    if action == 'register':
        await bot.send_message(callback_query.from_user.id, "Введите имя:")
    else:
        await bot.send_message(callback_query.from_user.id, "Введите почту:")


@dp.message_handler()
async def process_message(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_data:
        action = user_data[user_id]['action']

        if 'name' not in user_data[user_id] and action == 'register':
            user_data[user_id]['name'] = message.text
            await bot.send_message(user_id, "Введите почту:")

        elif 'email' not in user_data[user_id]:
            user_data[user_id]['email'] = message.text
            await bot.send_message(user_id, "Введите пароль:")

        elif 'password' not in user_data[user_id]:
            email = user_data[user_id]['email']
            password = message.text
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            if action == 'register':
                name = user_data[user_id]['name']
                with connect('users.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("CREATE TABLE IF NOT EXISTS users (name TEXT, email TEXT, password TEXT)")
                    cursor.execute("SELECT * FROM users WHERE email=?", (email,))
                    if cursor.fetchone():
                        await message.answer("Пользователь уже существует!")
                    else:
                        cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (name, email, hashed_password))
                        await message.answer("Пользователь успешно зарегистрирован!")
                        await send_action_buttons(user_id)
            else:
                with connect('users.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT password FROM users WHERE email=?", (email,))
                    result = cursor.fetchone()
                    if result and bcrypt.checkpw(password.encode('utf-8'), result[0]):
                        await message.answer("Успешная авторизация!")
                    else:
                        await message.answer("Неправильный пароль или несуществующий email!")

            del user_data[user_id]
    else:
        await message.answer("Пожалуйста, начните с команды /start")


if __name__ == '__main__':
    executor.start_polling(dp)
