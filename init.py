import inspect

from app.db.interaction.interaction import DbInteraction
from app.db.models.models import Events, Clients

db = DbInteraction(
    # host='5.53.124.252',
    host='localhost',
    port='5432',
    user='postgres',
    password='225567',
    db_name='one_two',
    rebuild_db=False
)

# Создание новых таблиц
# db.create_tables([Events.__table__])

# db.drop_all_tables()


