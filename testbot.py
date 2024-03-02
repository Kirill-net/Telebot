import random
import configparser
from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup
from sqlalchemy.orm import sessionmaker
from modelsBot import engine, create_tables, insert_tables, data_random, insert_user,\
    add_word, delete_word, known_users

config = configparser.ConfigParser()                # блок чтения входных данных из ini файла
config.read('sitings.ini')
token_bot = config['data_key']['token']

print('Start telegram bot...')

state_storage = StateMemoryStorage()
bot = TeleBot(token_bot, state_storage=state_storage)

Session = sessionmaker(bind=engine)    # открываем сессию
session = Session()

create_tables(engine)
insert_tables()

known_users = known_users()  # известные юзеры
buttons = []          # кнопки
def show_hint(*lines):
    """ Функуия формирует строку сообщения (клеет)

    :param lines: список переменных
    :return: возвращает склеенную строку
    """
    return '\n'.join(lines)
def show_target(data):
    """ Функуия формирует строку для ответа

    :param data: принимает переменные состояния
    :return:  Возвращает f строку
    """
    return f"{data['target_word']} -> {data['translate_word']}"
class Command:
    """ Класс для удобства вызова постоянных переменных

    """
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'
class MyStates(StatesGroup):
    """ Класс, описывающий переменные состояния (State-StatesGroup)

    """
    target_word = State()
    translate_word = State()
    another_words = State()
@bot.message_handler(commands=['cards', 'start'])  # метод вызова обработки комманд
def create_cards(message):
    """ выполняет функции приветствия, запросы в базу данных, формирование клавиатуры
         обработку данных и передачу переменных в 'состояние'

    :param message: принимает message от telebot
    :return: None
    """
    cid = message.chat.id
    if cid not in known_users:                 # проверка chat.id в юзерах
        known_users.append(cid)
        insert_user(cid)                      # запрос в БД
        bot.send_message(cid, f"Привет, приступим к изучению Английского...")
    markup = types.ReplyKeyboardMarkup(row_width=2)     # создание разметки

    global buttons                      # глобальные переменные кнопок
    buttons = []
    random_words = data_random(cid)     # запрос в БД
    target_word = random_words[0]
    translate = random_words[1]
    target_word_btn = types.KeyboardButton(target_word)       # первая кнопка
    buttons.append(target_word_btn)                           # добавили кнопку
    others = random_words[2]  # брать из БД
    other_words_btns = [types.KeyboardButton(word) for word in others]
    buttons.extend(other_words_btns)                          # добавили остальные четыре
    random.shuffle(buttons)
    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    buttons.extend([next_btn, add_word_btn, delete_word_btn])     # добавили еще три

    markup.add(*buttons)                                       # добавили все кнопки в разметку

    greeting = f"Выбери перевод слова:\n🇷🇺 {translate}"
    bot.send_message(message.chat.id, greeting, reply_markup=markup)        # вывели разметку с сообщением на экран
    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)  # передаем
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:  # передаем в состояние переменные
        data['target_word'] = target_word
        data['translate_word'] = translate
        data['other_words'] = others

@bot.message_handler(func=lambda message: message.text == Command.NEXT)   # обработчик комманды
def next_cards(message):
    """ Перенаправляет в другую функцию при соответствующем message

    :param message: message telebot
    :return: None
    """
    create_cards(message)

@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)   # обработчик комманды
def delete_words(message):
    """ Отправляет сообщение в telebot и перенаправляет в функцию  'del_word'

    :param message: message telebot (chat.id)
    :return: None
    """
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Введите слово на английском, которое хотите удалить')
    bot.register_next_step_handler(message, del_word)
def del_word(message):
    """ Взаимодействует с БД для удаления слов

    :param message: message telebot  (chat.id, text)
    :return:
    """
    word = message.text
    cid = message.chat.id
    message_to_user = delete_word(cid, word)
    bottons3(message, message_to_user)

@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)  # обработчик комманды
def write_word(message):
    """Отправляет сообщение в telebot и перенаправляет в функцию  'save_word'

    :param message: message telebot (chat.id)
    :return: None
    """
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Введите новое слово на английском и его перевод на русском через пробел')
    bot.register_next_step_handler(message, save_word)
def save_word(message):
    """Взаимодействует с БД для добавления слов и запрашивает данные (f строку, кнопки)
            для дальнейшей передачи в telebot

    :param message: message telebot (chat.id, text)
    :return: None
    """
    word = message.text
    word = word.split()
    cid = message.chat.id
    message_to_user = add_word(cid, word[0], word[1])
    bottons3(message, message_to_user)
def bottons3(message, message_to_user):
    """ вспомогательная функция формирования клавиатуры и передачи сообщения в telebot

    :param message: message telebot(chat.id)
    :param message_to_user: f строка
    :return: None
    """
    buttons3 = []
    markup = types.ReplyKeyboardMarkup(row_width=3)
    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    buttons3.extend([next_btn, add_word_btn, delete_word_btn])
    markup.add(*buttons3)
    bot.send_message(message.chat.id, message_to_user, reply_markup=markup)

@bot.message_handler(func=lambda message: True, content_types=['text'])  # обработчик текста
def message_reply(message):
    """ проверяет правильность ответа юзера по переводу текста. Формирует ответ. При неправильном выборе ответа
          меняет (помечает кнопки) и предлагает повторить выбор

    :param message: message telebot (text)
    :return: Non
    """
    text = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:  # считываем переменную из памяти
        target_word = data['target_word']
        if text == target_word:
            hint = show_target(data)
            hint_text = ["Отлично!❤", hint]
            next_btn = types.KeyboardButton(Command.NEXT)
            add_word_btn = types.KeyboardButton(Command.ADD_WORD)
            delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
            buttons.extend([next_btn, add_word_btn, delete_word_btn])
            hint = show_hint(*hint_text)
        else:
            for btn in buttons:
                if btn.text == text:
                    btn.text = text + '❌'
                    break
            hint = show_hint("Неверно!!",
                             f"Попробуй ещё раз вспомнить слово 🇷🇺{data['translate_word']}")
    markup.add(*buttons)
    bot.send_message(message.chat.id, hint, reply_markup=markup)

bot.add_custom_filter(custom_filters.StateFilter(bot))
session.close()
bot.infinity_polling(skip_pending=True)