import datetime

import telebot
import config
import re
from datetime import date, time, datetime
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from telebot import types

bot = telebot.TeleBot(config.token)


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


@bot.message_handler(commands=['menu'])
def menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu_button = types.KeyboardButton('/new_remind')
    markup.add(menu_button)
    bot.send_message(message.chat.id, f'<b>Выберите действие</b>', parse_mode='html', reply_markup=markup)


@bot.message_handler(commands=['new_remind'])
def new_remind(message):
    if not config.writing_new_remind:
        config.writing_new_remind = not config.writing_new_remind
    bot.send_message(message.chat.id, 'Введите своё напоминание', parse_mode='html')
    bot.register_next_step_handler(message, write_new_remind_text)


@bot.message_handler(commands=None)
def write_new_remind_text(message):
    if config.writing_new_remind:
        user_id = message.from_user.id
        remind_text = message.text
        config.test_reminders[user_id] = [remind_text]
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

        config.test_reminders[c.message.chat.id].append(result)
        print(config.test_reminders[c.message.chat.id])
        bot.send_message(c.message.chat.id, 'Введите время в формате hh:mm. Например \"17:15\" или \"8:09\"')
        bot.register_next_step_handler(c.message, write_new_remind_time)


@bot.message_handler(commands=['time'])
def write_new_remind_time(message):
    remind_time = message.text.replace(" ", "")
    print(remind_time)
    if len(remind_time) <= 5 or len(remind_time) >= 3:
        remind_time_split = message.text.split(':')
        for i in remind_time_split:
            print(i)
        if len(remind_time_split) <= 2 or len(remind_time_split) <= 1:
            if not re.findall('\D', remind_time_split[0]) and not re.findall('\D', remind_time_split[1]):
                if int(remind_time_split[0]) < 23 or int(remind_time_split[1]) < 59:
                    remind_time_datetime = time(int(remind_time_split[0]), int(remind_time_split[1]))
                    config.test_reminders[message.from_user.id] = datetime.combine(config.test_reminders[message.from_user.id][1], remind_time_datetime)
                    print(config.test_reminders[message.from_user.id])
                    print(datetime.datetime.now())
                else:
                    bot.send_message(message.chat.id,
                                     'Часов не может быть больше 23\n'
                                     'Минут не может быть больше 59\n'
                                     'Максимум: 23:59 Минимум: 00:00\n\n'
                                     'Введите время в формате hh:mm. Например \"17:15\" или \"8:09\"')
                    bot.register_next_step_handler(message, write_new_remind_time)
            else:
                bot.send_message(message.chat.id, 'Для ввода допускаются только целые неотрицательные числа\n\n'
                                                  'Введите время в формате hh:mm. Например \"17:15\" или \"8:09\"')
                bot.register_next_step_handler(message, write_new_remind_time)
        else:
            bot.send_message(message.chat.id,'Между часами и минутами должно стоять двоеточие \":\"\n'
                                             'В вводимом времени должно быть только одно двоеточие\n\n'
                                             'Введите время в формате hh:mm. Например \"17:15\" или \"8:09\"')
            bot.register_next_step_handler(message, write_new_remind_time)
    else:
        bot.send_message(message.chat.id, 'В сообщении содержится больше или меньше символов, чем ожидалось\n'
                                          'Максимум: 5. Например \"12:11\"\n'
                                          'Минимум: 3. Например \"1:1\"(=01:01)\n\n'
                                          'Введите время в формате hh:mm. Например \"17:15\" или \"8:09\"')
        bot.register_next_step_handler(message, write_new_remind_time)


def check_reminder_time(reminders):
    pass


if __name__ == '__main__':
    bot.infinity_polling()
