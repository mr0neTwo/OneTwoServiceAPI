from app.db.interaction.interaction import DbInteraction
from utils import config_parser

config = config_parser('config.txt')
# config = config_parser('local_config.txt')

host = config['SERVER_HOST']
port = config['SERVER_PORT']

db_host = config['DB_HOST']
db_port = config['DB_PORT']
user = config['DB_USER']
password = config['DB_PASSWORD']
db_name = config['DB_NAME']

# Добавляем объект управления БД
db_iteraction = DbInteraction(
    host=db_host,
    port=db_port,
    user=user,
    password=password,
    db_name=db_name,
    rebuild_db=False
)