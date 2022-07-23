from pprint import pprint

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from datetime import datetime, timedelta

from app.db.interaction.db_iteraction import db_iteraction
from app.db.models.models import Orders


### Отображение всего DataFrame ###
pd.options.display.max_rows = 60
pd.options.display.max_columns = 200
desired_width = 320
pd.set_option('display.width', desired_width)
pd.set_option('display.max_rows', 1500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
pd.set_option('display.expand_frame_repr', False)
# pd.set_option('display.max_columns', None)

# Количество недель, которые берем в рассчет
period = 15

# Дата на которуй формируем отчет
date = '27.06.2021'
# date = datetime.today().strftime("%d.%m.%Y")
finish_date = datetime.today()
start_date = finish_date - timedelta(days = period * 7)


# Список сотруднико для отчета
list_employees = [68021, 68023, 68025, 79236] # id
list_name = ['Стас', 'Антон', 'Юра', 'Альбиночка']
list_telegram_id = [442971377, 633363605, 857858976, 315479668]




# Подгрузим таблицу заказов из базы данных
query = db_iteraction.pgsql_connetction.session.query(Orders)
query = query.filter(Orders.created_at >= start_date.timestamp())
query = query.filter(Orders.created_at <= finish_date.timestamp())
# Преобразуем таблицу в DataFrame pandas
orders = pd.read_sql_query(query.statement, db_iteraction.pgsql_connetction.connection)

# Преобразуем формат Timestamp в удобный для нас DateTime
orders.index = pd.to_datetime(orders['created_at'] * 1000000000)
# orders.drop('created_at', axis = 1, inplace = True)
orders['done_at'] = pd.to_datetime(orders['done_at'] * 1000000000)
orders['estimated_done_at'] = pd.to_datetime(orders['estimated_done_at'] * 1000000000)
orders['closed_at'] = pd.to_datetime(orders['closed_at'] * 1000000000)
# orders['operations'] = [', '.join([GetTitleToId(i) for i in list_id]) for list_id in orders['operations']]
pprint(orders)
# Считаем количество заказов за каждую неделю
orders_week = orders['created_at'].resample('W').count()
pprint(orders_week)
