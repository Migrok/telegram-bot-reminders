import datetime
import db
import telebot
import re
import time as t
import config
from config import users_reminders, users_change_reminders
from token_and_db_pass import token
from datetime import date, time, datetime, timedelta
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from telebot import types

bot = telebot.TeleBot(token)


class Remind:
    def __init__(self, user_id, remind, remind_datetime=date.today(), remind_count=-1, remind_delay='no delay',
                 remind_id=0):
        self.user_id = user_id
        self.remind = remind
        self.remind_datetime = remind_datetime
        self.remind_count = remind_count
        self.remind_delay = remind_delay
        self.remind_id = remind_id

    def set_remind_datetime(self, new_remind_datetime):
        self.remind_datetime = new_remind_datetime

    def add_remind_datetime(self, to_add_remind_datetime):
        self.remind_datetime = datetime.combine(self.remind_datetime, to_add_remind_datetime)

    def set_remind_count(self, count):
        self.remind_count = count

    def set_remind_delay(self, delay):
        self.remind_delay = delay

    def set_remind_text(self, text):
        self.remind = text


@bot.message_handler(commands=['start'])
def start(message):
    mess = f'<b>Привет!</b>\n' \
           f'Я помогу вам не забыть о важных вещах.\n' \
           f'Напоминания могу присылать двумя способами:\n' \
           f'<b>- один раз в определённую дату и время\n' \
           f'- задаваемое количество раз с определённой периодичностью</b>'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu_button = types.KeyboardButton('Меню')
    markup.add(menu_button)
    bot.send_message(message.chat.id, mess, parse_mode='html', reply_markup=markup)
    if not config.checking_reminders_time:
        config.checking_reminders_time = not config.checking_reminders_time
        check_reminders_time()
    try:
        if users_reminders[message.from_user.id][0] != 0:
            users_reminders[message.from_user.id][0] = 0
    except KeyError:
        pass


@bot.message_handler(func=lambda message: message.text == 'Меню')
def menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    new_remind_button = types.KeyboardButton('Новое напоминание')
    check_remind_button = types.KeyboardButton('Проверить напоминания')
    change_remind_button = types.KeyboardButton('Изменить напоминание')
    delete_remind_button = types.KeyboardButton('Удалить напоминание')
    markup.add(new_remind_button, check_remind_button, change_remind_button, delete_remind_button)
    bot.send_message(message.chat.id, f'<b>Выберите действие</b>', parse_mode='html', reply_markup=markup)
    try:
        if users_reminders[message.from_user.id][0]:
            users_reminders[message.from_user.id][0] = not users_reminders[message.from_user.id][0]
    except KeyError:
        pass


@bot.message_handler(func=lambda message: message.text == 'Новое напоминание')
def new_remind(message):
    users_reminders[message.from_user.id] = [1]
    bot.send_message(message.chat.id, 'Введите своё напоминание', parse_mode='html')
    bot.register_next_step_handler(message, write_new_remind_text)


@bot.message_handler(func=lambda message: message.text == 'Одинарное напоминание')
def new_remind_created(message):
    try:
        if users_reminders[message.from_user.id][0] == 2:
            db.add_new_remind_in_db(users_reminders[message.from_user.id][1])
            del users_reminders[message.from_user.id]
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            menu_button = types.KeyboardButton('Меню')
            markup.add(menu_button)
            bot.send_message(message.chat.id, "Напоминание успешно создано!", reply_markup=markup)
    except KeyError:
        pass


@bot.message_handler(func=lambda message: message.text == 'Повторяемое напоминание')
def repeated_remind_get_delay(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    hour = types.KeyboardButton('Час')
    day = types.KeyboardButton('День')
    week = types.KeyboardButton('Неделя')
    month = types.KeyboardButton('Месяц (30 дней)')
    year = types.KeyboardButton('Год')
    markup.add(hour, day, week, month, year)
    bot.send_message(message.chat.id, 'Выберите интервал напоминаний', reply_markup=markup)
    try:
        if users_reminders[message.from_user.id][0] == 2:
            bot.register_next_step_handler(message, repeated_remind_set_delay)
    except KeyError:
        try:
            if users_change_reminders[message.from_user.id]:
                bot.register_next_step_handler(message, repeated_remind_set_delay)
        except KeyError:
            pass


@bot.message_handler(func=lambda message: message.text == 'Проверить напоминания')
def check_reminders(message):
    reminders_info_for_message = get_info_about_reminders_by_user_id(message)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu_button = types.KeyboardButton('Меню')
    markup.add(menu_button)
    bot.send_message(message.chat.id, reminders_info_for_message, parse_mode='html', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == 'Изменить напоминание')
def change_reminder_choice_reminder(message):
    reminders_info_for_message = get_info_about_reminders_by_user_id(message)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu_button = types.KeyboardButton('Меню')
    markup.add(menu_button)
    bot.send_message(message.chat.id, reminders_info_for_message, parse_mode='html', reply_markup=markup)
    bot.send_message(message.chat.id, 'Введите номер напоминания')
    bot.register_next_step_handler(message, change_reminder_choice)


@bot.message_handler(func=lambda message: message.text == 'Удалить напоминание')
def delete_reminder(message):
    reminders_info_for_message = get_info_about_reminders_by_user_id(message)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu_button = types.KeyboardButton('Меню')
    markup.add(menu_button)
    bot.send_message(message.chat.id, reminders_info_for_message, parse_mode='html', reply_markup=markup)
    bot.send_message(message.chat.id, 'Введите номер напоминания')
    bot.register_next_step_handler(message, reminder_deleted)


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
        try:
            if users_reminders[c.message.chat.id][0] == 1:
                set_new_remind_date(c.message, result)
        except KeyError:
            users_change_reminders[c.message.chat.id].remind_datetime = \
                users_change_reminders[c.message.chat.id].remind_datetime. \
                    replace(year=result.year, month=result.month, day=result.day)
            change_date(c.message)


def write_new_remind_text(message):
    users_reminders[message.from_user.id].append(Remind(message.from_user.id, message.text))
    write_new_remind_date(message)


def write_new_remind_date(message):
    calendar, step = DetailedTelegramCalendar().build()
    bot.send_message(message.chat.id,
                     f"Select {LSTEP[step]}",
                     reply_markup=calendar)


def set_new_remind_date(message, remind_date):
    message.from_user.id = message.chat.id
    users_reminders[message.from_user.id][1].set_remind_datetime(remind_date)
    bot.send_message(message.chat.id, 'Введите время в формате hh:mm. Например \"17:15\" или \"8:09\"')
    bot.register_next_step_handler(message, write_new_remind_time)


def write_new_remind_time(message):
    remind_time = message.text.replace(" ", "")
    if 5 >= len(remind_time) >= 3:
        remind_time_split = message.text.split(':')
        if len(remind_time_split) == 2:
            if not re.findall('\D', remind_time_split[0]) and not re.findall('\D', remind_time_split[1]):
                if int(remind_time_split[0]) <= 23 and int(remind_time_split[1]) <= 59:
                    remind_time_datetime = time(int(remind_time_split[0]), int(remind_time_split[1]))
                    try:
                        users_reminders[message.from_user.id][1].add_remind_datetime(remind_time_datetime)
                        choice_new_remind_type(message)
                    except KeyError:
                        users_change_reminders[message.from_user.id].add_remind_datetime(remind_time_datetime)
                        change_time(message)
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
            bot.send_message(message.chat.id, 'Между часами и минутами должно стоять двоеточие \":\"\n'
                                              'В вводимом времени должно быть только одно двоеточие\n\n'
                                              'Введите время в формате hh:mm. Например 17:15 или 8:09')
            bot.register_next_step_handler(message, write_new_remind_time)
    else:
        bot.send_message(message.chat.id, 'В сообщении содержится больше или меньше символов, чем ожидалось\n'
                                          'Максимум: 5. Например 12:11\n'
                                          'Минимум: 3. Например 1:1(=01:01)\n\n'
                                          'Введите время в формате hh:mm. Например 17:15 или 8:09')
        bot.register_next_step_handler(message, write_new_remind_time)


def choice_new_remind_type(message):
    users_reminders[message.from_user.id][0] = 2
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    single_remind_button = types.KeyboardButton('Одинарное напоминание')
    repeated_remind_button = types.KeyboardButton('Повторяемое напоминание')
    markup.add(single_remind_button, repeated_remind_button)
    bot.send_message(message.chat.id, 'Выберите тип напоминания', reply_markup=markup)


def repeated_remind_set_delay(message):
    if message.text in ['Час', 'День', 'Неделя', 'Месяц', 'Год']:
        try:
            users_reminders[message.from_user.id][1].set_remind_delay(message.text)
            repeated_remind_get_count(message)
        except KeyError:
            users_change_reminders[message.from_user.id].set_remind_delay(message.text)
            change_delay(message)
    else:
        bot.send_message(message.chat.id, f'Некоректное значение\n\n'
                                          f'Выберите интервал напоминаний')
        bot.register_next_step_handler(message, repeated_remind_set_delay)


def repeated_remind_get_count(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    c2 = types.KeyboardButton('2')
    c7 = types.KeyboardButton('7')
    c12 = types.KeyboardButton('12')
    c24 = types.KeyboardButton('24')
    c30 = types.KeyboardButton('30')
    no_c = types.KeyboardButton('Напоминать до отключения')
    markup.add(c2, c7, c12, c24, c30, no_c)
    bot.send_message(message.chat.id, 'Выберите или введите количество напоминаний', reply_markup=markup)
    bot.register_next_step_handler(message, repeated_remind_set_count)


def repeated_remind_set_count(message):
    if message.text == 'Напоминать до отключения' or message.text == '-2':
        try:
            users_reminders[message.from_user.id][1].set_remind_count(-2)
            new_remind_created(message)
        except KeyError:
            users_change_reminders[message.from_user.id].set_remind_count(-2)
            change_count(message)
    elif re.findall('\D', message.text):
        bot.send_message(message.chat.id, f'Количество напоминаний дожно содержать только цифры\n\n'
                                          f'Выберите или введите количество напоминаний')
        bot.register_next_step_handler(message, repeated_remind_set_count)
    elif int(message.text) <= 0:
        bot.send_message(message.chat.id, f'Количество напоминаний дожно быть строго больше 0\n\n'
                                          f'Выберите или введите количество напоминаний')
        bot.register_next_step_handler(message, repeated_remind_set_count)
    else:
        try:
            users_reminders[message.from_user.id][1].set_remind_count(int(message.text))
            new_remind_created(message)
        except KeyError:
            users_change_reminders[message.from_user.id].set_remind_count(int(message.text))
            change_count(message)


def send_reminder(reminder):
    bot.send_message(reminder.user_id, reminder.remind)
    if reminder.remind_count - 1 > 0 or reminder.remind_count == -2:
        reminder.remind_count -= 1
        reminder.remind_datetime = datetime_change_by_delay(reminder.remind_datetime, reminder.remind_delay)
        db.update_remind_datetime_and_count_in_db(reminder)
    else:
        db.delete_remind(reminder.remind_id)


def datetime_change_by_delay(remind_datetime, delay):
    if delay == 'Час':
        remind_datetime += timedelta(hours=1)
    elif delay == 'День':
        remind_datetime += timedelta(days=1)
    elif delay == 'Неделя':
        remind_datetime += timedelta(weeks=1)
    elif delay == 'Месяц':
        remind_datetime += timedelta(days=30)
    else:
        if (remind_datetime.year % 4 == 0 and remind_datetime.year % 100 != 0) or remind_datetime.year % 400 == 0:
            remind_datetime += timedelta(days=366)
        else:
            remind_datetime += timedelta(days=365)
    return remind_datetime


def get_info_about_reminders_by_user_id(message):
    reminders = db.get_entries_by_user_id(message.from_user.id)
    reminders_for_message = f''
    for reminder in reminders:
        reminders_for_message += f'{str(reminder[0])}) '
        reminders_for_message += f'Напоминание: {reminder[3]}|'
        reminders_for_message += f'Дата: {str(reminder[4].day)}.{str(reminder[4].month)}.{str(reminder[4].year)}|'
        reminders_for_message += f'Время: {str(reminder[4].hour)}:{str(reminder[4].minute)}'
        if reminder[5] != -1:
            if reminder[5] <= -2:
                reminders_for_message += f'\n<b>Работает до отключения</b> c интервалом <b>{reminder[6]}</b>'
            else:
                reminders_for_message += f'\nОсталось <b>{reminder[5]}</b> напоминания c интервалом <b>{reminder[6]}</b>'
        reminders_for_message += f'\n\n'
    return reminders_for_message


def change_reminder_choice(message):
    numbered_remind_id = db.get_numbered_remind_id_by_user_id(message.from_user.id)
    if not re.findall('\D', message.text):
        try:
            reminder_number = message.text
            reminder_entry = db.get_reminder_entry_by_remind_id(int(numbered_remind_id[reminder_number]))
            changeable_reminder = Remind(remind_id=reminder_entry[0], user_id=reminder_entry[1],
                                         remind=reminder_entry[2], remind_datetime=reminder_entry[3],
                                         remind_count=reminder_entry[4], remind_delay=reminder_entry[5])
            users_change_reminders[changeable_reminder.user_id] = changeable_reminder
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            change_remind_button = types.KeyboardButton('Изменить текст')
            change_date_button = types.KeyboardButton('Изменить дату')
            change_time_button = types.KeyboardButton('Изменить время')
            change_count_button = types.KeyboardButton('Изменить количество напоминаний')
            change_delay_button = types.KeyboardButton('Изменить интервал')
            menu_button = types.KeyboardButton('Меню')
            markup.add(change_remind_button, change_date_button, change_time_button,
                       change_count_button, change_delay_button, menu_button)
            bot.send_message(message.chat.id, 'Выберете действие', reply_markup=markup)
            bot.register_next_step_handler(message, change_reminder)
        except KeyError:
            bot.send_message(message.chat.id, f'Введен некоректный номер напоминания\n\n'
                                              f'Введите номер напоминания')
            bot.register_next_step_handler(message, change_reminder_choice)
    else:
        if message.text == 'Меню':
            menu(message)
        else:
            bot.send_message(message.chat.id, f'Введено некоректное значение\n\n'
                                              f'Введите номер напоминания')
            bot.register_next_step_handler(message, change_reminder_choice)


def change_reminder(message):
    if message.text == 'Изменить текст':
        bot.send_message(message.chat.id, f'Введите текст напоминания')
        bot.register_next_step_handler(message, change_text)
    elif message.text == 'Изменить дату':
        calendar, step = DetailedTelegramCalendar().build()
        bot.send_message(message.chat.id,
                         f"Select {LSTEP[step]}",
                         reply_markup=calendar)
    elif message.text == 'Изменить время':
        bot.send_message(message.chat.id, f'Введите время в формате hh:mm. Например 17:15 или 8:09')
        bot.register_next_step_handler(message, write_new_remind_time)
    elif message.text == 'Изменить количество напоминаний':
        if users_change_reminders[message.from_user.id].remind_count != -1:
            repeated_remind_get_count(message)
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            menu_button = types.KeyboardButton('Меню')
            markup.add(menu_button)
            bot.send_message(message.chat.id,
                             'Нельзя изменить количество напоминаний в одинарных напоминаниях', reply_markup=markup)
    elif message.text == 'Изменить интервал':
        if users_change_reminders[message.from_user.id].remind_delay != 'no delay':
            repeated_remind_get_delay(message)
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            menu_button = types.KeyboardButton('Меню')
            markup.add(menu_button)
            bot.send_message(message.chat.id,
                             'Нельзя изменить интервал напоминания в одинарных напоминаниях', reply_markup=markup)


def change_text(message):
    users_change_reminders[message.from_user.id].set_remind_text(message.text)
    db.update_remind_text(users_change_reminders[message.from_user.id])
    reminder_changed(message)


def change_date(message):
    message.from_user.id = message.chat.id
    db.update_remind_datetime(users_change_reminders[message.from_user.id])
    reminder_changed(message)


def change_time(message):
    db.update_remind_datetime(users_change_reminders[message.from_user.id])
    reminder_changed(message)


def change_count(message):
    db.update_remind_count(users_change_reminders[message.from_user.id])
    reminder_changed(message)


def change_delay(message):
    db.update_remind_delay(users_change_reminders[message.from_user.id])
    reminder_changed(message)


def reminder_changed(message):
    del users_change_reminders[message.from_user.id]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu_button = types.KeyboardButton('Меню')
    markup.add(menu_button)
    bot.send_message(message.chat.id, 'Напоминание изменино', reply_markup=markup)


def reminder_deleted(message):
    reminders_id = db.get_numbered_remind_id_by_user_id(message.from_user.id)
    if not re.findall('\D', message.text):
        try:
            db.delete_remind(reminders_id[message.text])
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            menu_button = types.KeyboardButton('Меню')
            markup.add(menu_button)
            bot.send_message(message.chat.id, 'Напоминание удалено', reply_markup=markup)
        except KeyError:
            bot.send_message(message.chat.id, f'Введен некоректный номер напоминания\n\n'
                                              f'Введите номер напоминания')
            bot.register_next_step_handler(message, reminder_deleted)
    else:
        bot.send_message(message.chat.id, f'Введено некоректное значение\n\n'
                                          f'Введите номер напоминания')
        bot.register_next_step_handler(message, reminder_deleted)


def check_reminders_time():
    while True:
        reminders_datetime_list = db.get_reminders_datetime()
        datetime_now = datetime.now().replace(second=0, microsecond=0)
        for remind_datetime in reminders_datetime_list:
            if datetime_now == remind_datetime:
                reminder_entry = db.get_entries_by_datetime(remind_datetime)
                reminder = Remind(remind_id=reminder_entry[0], user_id=reminder_entry[1],
                                  remind=reminder_entry[2], remind_datetime=reminder_entry[3],
                                  remind_count=reminder_entry[4], remind_delay=reminder_entry[5])
                send_reminder(reminder)
        t.sleep(60)


if __name__ == '__main__':
    bot.infinity_polling()
