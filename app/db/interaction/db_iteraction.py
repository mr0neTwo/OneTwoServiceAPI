import os

from app.db.interaction.interaction import DbInteraction
from flask_apscheduler import APScheduler




# Добавляем объект управления БД
db_iteraction = DbInteraction(
    host=os.environ['DB_HOST'],
    port=os.environ['DB_PORT'],
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
    db_name=os.environ['DB_NAME'],
    rebuild_db=False
)

scheduler = APScheduler()
