import telebot

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
    bot.send_message(message.chat.id, mess, parse_mode='html')


bot.polling(none_stop=True)
