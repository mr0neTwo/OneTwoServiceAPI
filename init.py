import inspect
from telebot import TeleBot

from sqlalchemy import Column, BOOLEAN, INTEGER, TEXT

from app.db.interaction.interaction import DbInteraction
from app.db.models.models import Events, Clients, Payments, Employees

db = DbInteraction(
    host='5.53.124.252',
    # host='localhost',
    port='5432',
    user='postgres',
    password='225567',
    db_name='one_two',
    rebuild_db=False
)

# Создание новых таблиц
# db.create_tables([Events.__table__])

# Добавление столбца
column = Column('avatar', TEXT)
db.add_column(Employees.__table__, column)

# db.drop_all_tables()

# Создаем токен для бота
# token = "1729021750:AAHObATFNa1uO0cyFrWZezNSG8YMBugNhjE"
#
# list_name = ['Стас', 'Антон', 'Юра', 'Альбиночка']
# list_telegram_id = [442971377, 633363605, 857858976, 315479668]

# Подключаемся к боту
# bot = TeleBot(token)
# bot.send_message(442971377, text='С возвращением бро!', )


