import datetime
import db
import telebot
import config
import re
import time as t
from token_and_db_pass import token
from datetime import date, time, datetime
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from telebot import types

bot = telebot.TeleBot(token)


class Remind:
    def __init__(self, user_id, remind, remind_datetime=date.today(), remind_count=-1, remind_delay='no delay'):
        self.user_id = user_id
        self.remind = remind
        self.remind_datetime = remind_datetime
        self.remind_count = remind_count
        self.remind_delay = remind_delay

    def set_remind_datetime(self, new_remind_datetime):
        self.remind_datetime = new_remind_datetime

    def add_remind_datetime(self, to_add_remind_datetime):
        self.remind_datetime = datetime.combine(self.remind_datetime, to_add_remind_datetime)

    def set_remind_count(self, count):
        self.remind_count = count

    def set_remind_delay(self, delay):
        self.remind_delay = delay


@bot.message_handler(commands=['start'])
def start(message):
    mess = f'<b>Привет!</b>\n' \
           f'Я помогу вам не забыть о важных вещах.\n' \
           f'Напоминания могу присылать двумя способами:\n' \
           f'<b>- один раз в определённую дату и время\n' \
           f'- задаваемое количество раз с определённой периодичностью</b>'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu_button = types.KeyboardButton('/menu')
    markup.add(menu_button)
    bot.send_message(message.chat.id, mess, parse_mode='html', reply_markup=markup)
    if not config.checking_reminders_time:
        check_reminders_time()
        config.checking_reminders_time = not config.checking_reminders_time


@bot.message_handler(commands=['menu'])
def menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu_button = types.KeyboardButton('В')
    markup.add(menu_button)
    bot.send_message(message.chat.id, f'<b>Выберите действие</b>', parse_mode='html', reply_markup=markup)
    bot.register_next_step_handler(message, choice)


@bot.message_handler(commands=['new_single_remind'])
def new_single_remind(message):
    if not config.writing_new_remind:
        config.writing_new_remind = not config.writing_new_remind
    bot.send_message(message.chat.id, 'Введите своё напоминание', parse_mode='html')
    bot.register_next_step_handler(message, write_new_remind_text)


@bot.message_handler(commands=None)
def write_new_remind_text(message):
    if config.writing_new_remind:
        config.new_remind = Remind(message.from_user.id, message.text)
        write_new_remind_date(message)
    else:
        bot.send_message(message.chat.id, 'Выберите в меню \"Новое напоминание\"')


@bot.message_handler(commands=None)
def write_new_remind_date(message):
    calendar, step = DetailedTelegramCalendar().build()
    bot.send_message(message.chat.id,
                     f"Select {LSTEP[step]}",
                     reply_markup=calendar)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
def cal(c):
    result, key, step = DetailedTelegramCalendar().process(c.data)
    if not result and key:
        bot.edit_message_text(f'Select {LSTEP[step]}',
                              c.message.chat.id,
                              c.message.message_id,
                              reply_markup=key)
    elif result:
        bot.edit_message_text(f'You selected {result}',
                              c.message.chat.id,
                              c.message.message_id)

        config.new_remind.set_remind_datetime(result)
        bot.send_message(c.message.chat.id, 'Введите время в формате hh:mm. Например \"17:15\" или \"8:09\"')
        bot.register_next_step_handler(c.message, write_new_remind_time)


@bot.message_handler(commands=None)
def write_new_remind_time(message):
    remind_time = message.text.replace(" ", "")
    if len(remind_time) <= 5 and len(remind_time) >= 3:
        remind_time_split = message.text.split(':')
        if len(remind_time_split) == 2:
            if not re.findall('\D', remind_time_split[0]) and not re.findall('\D', remind_time_split[1]):
                if int(remind_time_split[0]) <= 23 and int(remind_time_split[1]) <= 59:
                    remind_time_datetime = time(int(remind_time_split[0]), int(remind_time_split[1]))
                    config.new_remind.add_remind_datetime(remind_time_datetime)
                    config.writing_new_remind = not config.writing_new_remind
                    db.add_new_remind_in_db(config.new_remind)
                else:
                    bot.send_message(message.chat.id,
                                     'Часов не может быть больше 23\n'
                                     'Минут не может быть больше 59\n'
                                     'Максимум: 23:59 Минимум: 00:00\n\n'
                                     'Введите время в формате hh:mm. Например 17:15 или 8:09')
                    bot.register_next_step_handler(message, write_new_remind_time)
            else:
                bot.send_message(message.chat.id, 'Для ввода допускаются только целые неотрицательные числа\n\n'
                                                  'Введите время в формате hh:mm. Например 17:15 или 8:09')
                bot.register_next_step_handler(message, write_new_remind_time)
        else:
            bot.send_message(message.chat.id,'Между часами и минутами должно стоять двоеточие \":\"\n'
                                             'В вводимом времени должно быть только одно двоеточие\n\n'
                                             'Введите время в формате hh:mm. Например 17:15 или 8:09')
            bot.register_next_step_handler(message, write_new_remind_time)
    else:
        bot.send_message(message.chat.id, 'В сообщении содержится больше или меньше символов, чем ожидалось\n'
                                          'Максимум: 5. Например 12:11\n'
                                          'Минимум: 3. Например 1:1(=01:01)\n\n'
                                          'Введите время в формате hh:mm. Например 17:15 или 8:09')
        bot.register_next_step_handler(message, write_new_remind_time)


@bot.message_handler(commands=None)
def send_reminder(reminder):
    bot.send_message(reminder[1], reminder[2])
    db.delete_remind(reminder[0])


def choice():
    pass


def check_reminders_time():
    while True:
        reminders_datetime_list = db.get_reminders_datetime()
        datetime_now = datetime.now().replace(second=0, microsecond=0)
        for remind_datetime in reminders_datetime_list:
            if datetime_now == remind_datetime:
                reminder = db.get_entries_by_datetime(remind_datetime)
                send_reminder(reminder)
        t.sleep(55)


if __name__ == '__main__':
    bot.infinity_polling()


