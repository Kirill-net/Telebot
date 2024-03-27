import random
import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from Constants import DNS

Base = declarative_base()
engine = sq.create_engine(DNS)
Session = sessionmaker(bind=engine)


class User_Words(Base):
    """ Класс таблица уникальных ключей Юзеров-Слов (от Base)
      колонки (id, user_id, word_id)

    """
    __tablename__ = "user_words"

    id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey("user.id"))
    word_id = sq.Column(sq.Integer, sq.ForeignKey("words.id"))


class Words(Base):
    """Класс таблица слов (от Base)
      колонки (id, target_word, translate)

    """
    __tablename__ = "words"

    id = sq.Column(sq.Integer, primary_key=True)
    target_word = sq.Column(sq.String(length=15), unique=True)
    translate = sq.Column(sq.String(length=15), unique=True)
    user = relationship("User_Words", backref='word')


class User(Base):
    """Класс таблица юзеров (от Base)
      колонки (id, cid, word)

    """
    __tablename__ = "user"

    id = sq.Column(sq.Integer, primary_key=True)
    cid = sq.Column(sq.Integer, unique=True)
    words = relationship("User_Words", backref='users')


def create_tables():
    """Создает таблицы

    :param engine: параметры движка
    :return: None
    """
    # Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def insert_tables():
    """заполняет таблицу words данными

    :return: None
    """
    session = Session()
    words = session.query(Words.id).all()
    if len(words) < 1:
        word1 = Words(translate='история', target_word='history')
        word2 = Words(translate='плохой', target_word='bad')
        word3 = Words(translate='зеленый', target_word='green')
        word4 = Words(translate='свобода', target_word='liberty')
        word5 = Words(translate='мечта', target_word='dream')
        word6 = Words(translate='большой', target_word='big')
        word7 = Words(translate='красный', target_word='red')
        word8 = Words(translate='веселый', target_word='funny')
        word9 = Words(translate='дом', target_word='house')
        word10 = Words(translate='велосипед', target_word='bike')
        session.add_all([
            word1, word2, word3, word4, word5,
            word6, word7, word8, word9, word10
        ])
        session.commit()
        session.close()


def insert_user(cid):
    """ добавляет юзера в таблицу user

    :param cid: уникальный id юзера (telebot)
    :return: None
    """
    session = Session()
    user = User(cid=cid)
    session.add(user)
    session.commit()
    user_id = get_user(cid)
    insert_uw(user_id)
    session.close()


def insert_uw(user_id):
    """ функция присваивания начальной базы слов
     для пользователя в таблице user_words

    :param user_id: user_id
    :return: None
    """
    session = Session()
    for el in range(1, 11):
        user_words = User_Words(user_id=user_id, word_id=el)
        session.add(user_words)
        session.commit()
    session.close()


def data_random(cid):
    """ получает рандомно слова с переводом и список слов для клавиш
         для конкретного пользователя

    :param cid: уникальный id юзера (telebot)
    :return: (target_word), (translate), (список для кнопок)
    """
    session = Session()
    data = {}
    user_id = get_user(cid)
    res = session.query(Words) \
        .with_entities(Words.target_word, Words.translate) \
        .join(User_Words, User_Words.word_id == Words.id) \
        .filter(User_Words.user_id == user_id)
    for d in res.all():
        data.update({d[0]: d[1]})
    list_words = list(data.keys())
    data_r = random.choices(list_words)  # берем случайное слово
    list_words.remove(data_r[0])  # убираем то что взяли из списка
    random.shuffle(list_words)  # смешиваем
    list_words = list_words[:4]
    session.close()
    return data_r[0], data[data_r[0]], list_words


def get_user(cid):
    """ вспомогательная функция для определения id юзера

    :param cid: уникальный id юзера (telebot)
    :return: user_id
    """
    session = Session()
    user_id = session.query(User.id).filter(User.cid == cid)
    session.close()
    return user_id.first()[0]


def known_users():
    """формирует список юзеров из таблицы user

    :return: list(users)
    """
    session = Session()
    users = []
    for user in session.query(User.cid).all():
        users += list(user)
    session.close()
    return users


def add_word(cid, word, translate):
    """функция проверяет наличие слова в базе
    и в случае отстутствия заносит его с переводом в базу даннх
    а также закрепляет его за юзером и выводит результат

    :param cid: уникальный id юзера (telebot)
    :param word: новое слово от юзера
    :param translate: перевод нового слова
    :return: f строка с результатом
    """
    session = Session()
    user_id = get_user(cid)
    words = session.query(Words.target_word).all()
    list_words = [list(el) for el in words]
    if [word] not in list_words:
        session.add(Words(target_word=word, translate=translate))
        word_id = session.query(Words.id).\
            filter(Words.target_word == word).first()[0]
        session.add(User_Words(user_id=user_id, word_id=word_id))
        result_last = count_words(user_id, word, translate)
    else:
        word_id = session.query(Words.id).\
            filter(Words.target_word == word).first()[0]
        word_user_id = (session.query(User_Words.word_id).
                        filter(User_Words.user_id == user_id).all())
        w = [list(el) for el in word_user_id]
        if [word_id] not in w:
            session.add(User_Words(user_id=user_id, word_id=word_id))
            result_last = count_words(user_id, word, translate)
        else:
            result_last = f'слово {word} уже есть в вашей базе'
    session.commit()
    session.close()
    return result_last


def count_words(user_id, word, translate):
    """при внесении нового слова в базу , выводит количество слов,
    закрепенных за юзером с учетом внесенного

    :param user_id: user_id
    :param word: новое слово от юзера
    :param translate: перевод нового слова
    :return: f строка с результатом
    """
    session = Session()
    count_w = (session.query(User_Words.word_id).
               filter(User_Words.user_id == user_id).count())
    result = (f'Добавлено слово -"{word}" и его перевод - "{translate}" \n '
              f'Общее количество слов в твоей базе - {count_w + 1}')
    session.close()
    return result


def delete_word(cid, word):
    """функция удаляет слово, принимаемое от юзера из его базы
    (при его наличии и отсутсвии в базовом ноборе) и Выводит результат

    :param cid: уникальный id юзера (telebot)
    :param word: слово от юзера для удаления
    :return: f строка с результатом
    """
    session = Session()
    user_id = get_user(cid)
    result = f'Слово "{word}" удалить нельзя. \
    Слово отсутствует или находится в "базовом списке"'
    words = session.query(Words.target_word).filter(Words.id > 10).all()
    list_words = [list(el) for el in words]
    if [word] in list_words:
        word_id = session.query(Words.id).\
            filter(Words.target_word == word).first()[0]
        word_user_id = (session.query(User_Words.word_id).
                        filter(User_Words.user_id == user_id).all())
        w = [list(el) for el in word_user_id]
        if [word_id] in w:
            (session.query(User_Words).
             filter(
                User_Words.user_id == user_id,
                User_Words.word_id == word_id).delete())
            session.commit()
            result_last = f'слово "{word}" успешно удалено из вашего списка'
        else:
            result_last = result
    else:
        result_last = result
    session.close()
    return result_last
