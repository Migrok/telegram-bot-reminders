import telebot
from  telebot import types

bot_api_token = open('bot_api_token.txt', 'r')
bot = telebot.TeleBot(bot_api_token.read())
bot_api_token.close()


@bot.message_handler(commands=['start'])
def start(message):
    mess = f'<b>Привет!</b>\n' \
           f'Я помогу тебе не забыть о важных вещах.\n' \
           f'Напоминания могу присылать двумя способами:\n' \
           f'<b>- один раз в определённую дату и время\n' \
           f'- задаваемое количество раз с определённой периодичностью</b>'

    markup = types.InlineKeyboardMarkup(row_width=2)
    menu_button = types.InlineKeyboardButton('Меню', callback_data='menu')
    markup.add(menu_button)
    bot.send_message(message.chat.id, mess, parse_mode='html', reply_markup=markup)


@bot.message_handler(commands=['menu'])
def menu(message):
    mess = f'<b>Выбери действие</b>'
    bot.send_message(message.chat.id, mess, parse_mode='html')


@bot.callback_query_handler(func=lambda call:True)
def callback_inline(call):
    if call.message:
        if call.data == 'menu':
            bot.send_message(call.message.chat.id, '/menu')


if __name__ == '__main__':
    bot.infinity_polling()
