# импортируем ORM SQLAlchemy, сам класс и дополнительные утилиты во
# избежание чистых SQL-инъекций
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database, drop_database


class PostgreSQLConnection:
    """Класс, описывающий клиентское приложение для подключение к СУБД"""
    def __init__(self, host, port, user, password, db_name, rebuild_db=False):
        self.user = user
        self.password = password
        self.db_name = db_name

        self.host = host
        self.port = port

        # переменная для перестройки базы данных
        self.rebuild_db = rebuild_db
        self.connection = self.connect()

        # конфигурация сессии подключения
        session = sessionmaker(
            bind=self.connection.engine,
            autocommit=True,
            autoflush=True,
            enable_baked_queries=False,
            expire_on_commit=True,
        )
        # запуск сессии подключения
        self.session = session()
        # оставляем место под движок
        self.engine = None

    def get_connection(self):
        """Формируем url и создаём движок,
        прокидываем на него метод connect()"""
        url = f'postgresql://{self.user}:{self.password}' \
              f'@{self.host}:{self.port}/{self.db_name}'
        self.engine = sqlalchemy.create_engine(url, encoding='utf8')
        return self.engine.connect()

    def connect(self):
        """В случае перестройки БД, мы не сразу подключаемся,
        а удаляем старую базу данных если она есть или сразу создаём новую.
        Возвращаем соединение."""
        if self.rebuild_db:
            url = f'postgresql://{self.user}:{self.password}' \
              f'@{self.host}:{self.port}/{self.db_name}'
            if database_exists(url):
                drop_database(url)
            create_database(url)
        return self.get_connection()
