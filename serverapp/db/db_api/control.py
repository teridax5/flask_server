# вытягиваем класс клиентского приложения, пользовательскую ошибку и
# модели SQLAlchemy
from serverapp.db.client.client import PostgreSQLConnection
from serverapp.db.exceptions import AuthorNotFoundException, BookNotFoundException
from serverapp.db.models.models import Base, Author, Book


class DBControl:
    """Запускаем API для общения flask и клиентского приложения для PostgreSQL"""
    def __init__(self, host, port, user, password, db_name, rebuild_db=False):
        self.postgres_connection = PostgreSQLConnection(
            host=host,
            port=port,
            user=user,
            password=password,
            db_name=db_name,
            rebuild_db=rebuild_db
        )

        self.engine = self.postgres_connection.connection.engine
        # в случае перестройки БД по-новой создаём таблицы
        if rebuild_db:
            self.create_table('authors')
            self.create_table('books')

    def create_table(self, tablename):
        Base.metadata.tables[tablename].create(self.engine)

    def add_author(self, author_info: dict):
        """Метод на добавление нового автора, на вход принимает словарь
        и возвращает объектное представление добавленной записи"""
        author = Author(
            author_name=author_info['name'],
            short_biography=author_info['biography'],
            email=author_info['email']
        )
        self.postgres_connection.session.add(author)
        return self.get_author_info(author_name=author_info['name'])

    def add_book(self, info: dict):
        """Аналогично add_author, только для новых книг. Особенностью
        является то, что входной словарь так же содержит информацию об
        авторе, так как новый автор может быть добавлен."""
        author_exists = self.postgres_connection.session.query(Author). \
            filter_by(author_name=info['name']).first()
        if not author_exists:
            self.add_author(author_info={
                'name': info['name'],
                'biography':info['biography'],
                'email': info['email']
            })
            author_exists = self.postgres_connection.session.query(Author). \
                filter_by(author_name=info['name']).first()
        book = Book(
            author_id=author_exists.id,
            book_name=info['book_name'],
            description=info['description']
        )
        self.postgres_connection.session.add(book)
        return None

    def get_book_info(self, book_name):
        """Метод получения информации о конкретной книге. Хитростью
        является то, что его вызывают почти все методы, а данный
        метод содержит expire."""
        book_exists = self.postgres_connection.session.query(Book).\
            filter_by(book_name=book_name).first()
        if book_exists:
            self.postgres_connection.session.expire_all()
            return book_exists
        else:
            raise BookNotFoundException('Bokk not found!')

    def get_all_books(self):
        """Метод получения всех книг."""
        result = self.postgres_connection.session.query(Book).all()
        return result

    def get_books_by_author(self, author_name):
        """Метод получения всех книг конкретного автора"""
        author_exists = self.postgres_connection.session.query(Author). \
            filter_by(author_name=author_name).first()
        if author_exists:
            return author_exists.list_of_books
        else:
            return AuthorNotFoundException('Author not found!')

    def get_author_info(self, author_name):
        """Метод получения информации об авторе, аналогичен get_book_info."""
        author_exists = self.postgres_connection.session.query(Author).\
            filter_by(author_name=author_name).first()
        if author_exists:
            self.postgres_connection.session.expire_all()
            return author_exists
        else:
            raise AuthorNotFoundException('Author not found!')

    def edit_author_info(self,
                         author_name, new_name=None,
                         new_biography=None, new_email=None):
        """Метод изменения информации об авторе"""
        author_exists = self.postgres_connection.session.query(Author). \
            filter_by(author_name=author_name).first()
        if author_exists:
            if new_name is not None:
                author_exists.author_name = new_name
                author_name = new_name
            if new_biography is not None:
                author_exists.short_biography = new_biography
            if new_email is not None:
                author_exists.email = new_email
            return self.get_author_info(author_name)
        else:
            raise AuthorNotFoundException('Author not found!')


if __name__ == '__main__':
    # запускаем API
    db = DBControl(
        host='localhost',
        port=5433,
        user='postgres',
        password='pwd123',
        db_name='some_db',
        rebuild_db=True
    )
    # пример заполнения информации по добавлению автора
    db.add_author(
        {
            'name': 'Kuja',
            'biography': 'Lived a long life!',
            'email': 'None'
        }
    )
    # пример заполнения информации по добавлению книги
    db.add_book(info={'name': 'Kuja',
            'biography': 'Lived a long life!',
            'email': 'None', 'book_name': 'Gogi',
                           'description': 'A nice book!'})
    # пример изменения информации об авторе
    db.edit_author_info(author_name='Kuja', new_name='Jecht')
