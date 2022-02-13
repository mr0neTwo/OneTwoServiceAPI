import sqlalchemy
from sqlalchemy.orm import sessionmaker
import psycopg2 as psql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT # <-- ADD THIS LINE

# Создаем соединение
class PGSQL_connetction:

    def __init__(self, host, port, user, password, db_name, rebuild_db=False):

        self.user = user                    # Имя пользователя БД
        self.password = password            # Пароль пользователя
        self.db_name = db_name              # Имя бызы данных
        self.rebuild_db = rebuild_db        # Удалить старую базы данных и создать новую

        self.host = host                    # Адрес хоста
        self.port = port                    # Порт хоста
        self.connection = self.connect()    # Оъект соединения
        self.db = self.create_db(self.db_name)

        # Сессиню
        session = sessionmaker(
            bind=self.connection.engine,        # Движек соединения
            # autocommit=True,                    # Автосохранение операций в БД
            autoflush=True,
            # enable_baked_queries=False,
            # expire_on_commit=True
        )

        self.session = session()


    def get_connection(self, db_created=False):
        engine = sqlalchemy.create_engine(
            f'postgresql+psycopg2://{self.user}:{self.password}@{self.host}/{self.db_name if db_created else ""}',
            encoding='utf8'
        )
        return engine.connect()

    def connect(self):
        connection = self.get_connection()
        if self.rebuild_db:
            connection.execute(f'DROP DATABASE IF EXISTS {self.db_name}')
            connection.execute(f'CREATE DATABASE {self.db_name}')
        return self.get_connection(db_created=True)

    def execute_query(self, query):
        result = self.connection.execute(query)
        return result

    def create_db(self, db_name):
        '''
        Создает Базу данныз из корневой базы
        :param nameDataBase: - str - Имя базы данных
        :return:
        '''
        try:
            # Конектимся к нашей базе
            conn = psql.connect(dbname='postgres',       # Корневая база
                                user=self.user,          # Имя пользователя
                                password=self.password,  # Пароль
                                host=self.host,
                                # port=self.port
                                )
            # Установка уровня изолированности транзакций (не знаю, что это, но без этого не работает)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)  # <-- ADD THIS LINE
            # Создаем курсор
            cursor = conn.cursor()
            # Создаем базу данных
            # cursor.execute(f'DROP DATABASE {db_name}')
            cursor.execute(f'CREATE DATABASE {db_name}')
            print(f'База данных {db_name} успешно создана')
        except psql.errors.DuplicateDatabase:
            print(f'База данных {db_name} уже существует')
        finally:
            conn.close()




if __name__ == '__main__':

    conn_test = PGSQL_connetction(
       host='5.53.124.252',
       port='5432',
       user='postgres',
       password='225567',
       db_name='one_two',
       rebuild_db=False
    )
    # conn_test.create_db()
