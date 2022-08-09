import telebot
import config
import time
from telebot import types

bot = telebot.TeleBot(config.token)


@bot.message_handler(commands=['start'])
def start(message):
    mess = f'<b>Привет!</b>\n' \
           f'Я помогу тебе не забыть о важных вещах.\n' \
           f'Напоминания могу присылать двумя способами:\n' \
           f'<b>- один раз в определённую дату и время\n' \
           f'- задаваемое количество раз с определённой периодичностью</b>'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu_button = types.KeyboardButton('/menu')
    markup.add(menu_button)
    bot.send_message(message.chat.id, mess, parse_mode='html', reply_markup=markup)


@bot.message_handler(commands=['menu'])
def menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu_button = types.KeyboardButton('/new_remind')
    markup.add(menu_button)
    bot.send_message(message.chat.id, f'<b>Выбери действие</b>', parse_mode='html', reply_markup=markup)


@bot.message_handler(commands=['new_remind'])
def new_remind(message):
    if not config.writing_new_remind:
        config.writing_new_remind = not config.writing_new_remind
    bot.send_message(message.chat.id, 'Введи своё напоминание', parse_mode='html')
    bot.register_next_step_handler(message, write_new_remind)


@bot.message_handler(commands=None)
def write_new_remind(message):
    if config.writing_new_remind :
        user_id = message.from_user.id
        remind_text = message.text
        config.test_reminders[user_id] = [remind_text]
        bot.register_next_step_handler(message, write_new_remind_time)
    else:
        bot.send_message(message.chat.id, 'Выберите в меню \"Новое напоминание\"')


@bot.message_handler(commands=None)
def write_new_remind_time(message):
    bot.send_message(message.chat.id, 'Введите время')

def check_reminder_time(reminders):
    pass


if __name__ == '__main__':
    bot.infinity_polling()
