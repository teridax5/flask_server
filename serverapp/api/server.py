# для запуска приложения flask в отдельном потоке
import threading
# для парсинга конфигурационного файла
import argparse

# импортируем классы приложения, запросов; а так же перевод в json-документ и обрыв соединения
from flask import Flask, request, jsonify, abort

# из внутренних модулей импортируем: функция считывания конфигурационного файла,
# API для PostgreSQL-Flask, пользовательские исключения, схемы для сериализации
from serverapp.api.utils import reading_configs
from serverapp.db.db_api.control import DBControl
from serverapp.db.exceptions import AuthorNotFoundException, BookNotFoundException
from serverapp.db.models.models import BookSchema, AuthorSchema


class Server:
    """Класс сервер предназначен для развёртывания веб-сервера
    на flask с подключением сервера БД PostgreSQL."""
    def __init__(self, host, port,
                 db_host, db_port, user, password, db_name, rebuild_db=False):
        self.host = host
        self.port = port

        # создаём объект API для использования внутри сервера
        self.db_connection = DBControl(
            host=db_host, port=db_port,
            user=user, password=password,
            db_name=db_name, rebuild_db=rebuild_db
        )

        # переменная для потока сервера
        self.server = None
        # задаём сериализацию для каждой из таблиц
        self.book_schema, self.author_schema = BookSchema(), AuthorSchema()
        # задаём множественную сериализацию
        self.books_schema = BookSchema(many=True)

        # создаём приложение веб-сервера на flask
        self.flask_app = Flask(__name__)
        # создаём ручки (через декораторы не столь удобно)
        self.flask_app.add_url_rule('/', view_func=self.get_home)
        self.flask_app.add_url_rule('/home', view_func=self.get_home)
        self.flask_app.add_url_rule('/add_author', view_func=self.add_author,
                                    methods=['POST'])
        self.flask_app.add_url_rule('/get_author/<author_name>',
                                    view_func=self.get_author_info)
        self.flask_app.add_url_rule('/edit_author/<author_name>',
                                    view_func=self.edit_author_info,
                                    methods=['PUT'])
        self.flask_app.add_url_rule('/add_book',
                                    view_func=self.add_book,
                                    methods=['POST'])
        self.flask_app.add_url_rule('/get_book/<book_name>',
                                    view_func=self.get_book_info)
        self.flask_app.add_url_rule('/get_all_books',
                                    view_func=self.get_all_books)
        self.flask_app.add_url_rule('/get_all_books_by_<author_name>',
                                    view_func=self.get_all_books_by_author)
        # пользовательский обработчик
        self.flask_app.register_error_handler(404, self.page_not_found)

    def page_not_found(self, err_description):
        return jsonify(error=str(err_description)), 404

    def run_server(self):
        """Запускаем поток сервера и возвращаем его"""
        self.server = threading.Thread(target=self.flask_app.run,
                                  kwargs={'host': self.host,
                                          'port': self.port})
        self.server.start()
        return self.server

    def get_home(self):
        """Домашняя страница (просто есть)"""
        return 'Welcome to our e-library!'

    def get_all_books(self):
        """Получаем все книги"""
        all_books = self.db_connection.get_all_books()
        result = self.books_schema.dump(all_books)
        return jsonify(result)

    def get_all_books_by_author(self, author_name):
        """Получаем все книги конкретного пользователя"""
        all_books = self.db_connection.get_books_by_author(
            author_name=author_name
        )
        result = self.books_schema.dump(all_books)
        return jsonify(result)

    def add_author(self):
        """Добавляем автора"""
        request_body = dict(request.json)
        self.db_connection.add_author(
            author_info=request_body
        )
        return f'Success added {request_body["author_name"]}', 201

    def add_book(self):
        """Добавляем книгу (и автора, если есть в реквесте)"""
        request_body = dict(request.json)
        self.db_connection.add_book(
            info=request_body
        )
        return f'Success! Added {request_body["book_name"]}', 201

    def get_book_info(self, book_name):
        """Ищем конкретную книгу"""
        try:
            book_info = self.db_connection.get_book_info(
                book_name=book_name
            )
            result = jsonify(self.book_schema.dump(book_info))
            return result, 200
        except BookNotFoundException:
            # если не нашли - собственноручная ошибка
            abort(404, 'Book not found!')

    def get_author_info(self, author_name):
        """Получаем информацию об авторе по его имени"""
        try:
            author_info = self.db_connection.get_author_info(
                author_name=author_name
            )
            result = self.author_schema.dump(author_info)
            return jsonify(result), 200
        except AuthorNotFoundException:
            abort(404, 'Author not found!')

    def edit_author_info(self, author_name):
        """Изменяем информацию об авторе"""
        request_body = dict(request.json)
        new_name = request_body['author_name']
        new_biography = request_body['short_biography']
        new_email = request_body['email']
        self.db_connection.edit_author_info(
            author_name=author_name,
            new_name=new_name,
            new_biography=new_biography,
            new_email=new_email
        )
        return 'Success', 200


if __name__ == '__main__':
    # прогружаем парсер, прокидываем дополнительный параметр
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, dest='config')

    args = parser.parse_args()
    # считываем конфигурацию
    config = reading_configs(args.config)
    # заносим в словарь конфигураций соответствующие поля
    server_host = config['SERVER_HOST']
    server_port = config['SERVER_PORT']
    db_host = config['DB_HOST']
    db_port = config['DB_PORT']
    user = config['DB_USER']
    password = config['DB_PASS']
    db_name = config['DB_NAME']
    # прокидываем параметры и запускаем сервер
    server = Server(host=server_host,
                    port=server_port,
                    db_host=db_host,
                    db_port=db_port,
                    user=user,
                    password=password,
                    db_name=db_name)
    server.run_server()
