from app.db.interaction.db_iteraction import db_iteraction
from app.db.models.models import Employees


class UserLogin:

    def __init__(self):
        self.db_iteraction = db_iteraction

    def fromDB(self, user_id):
        self.__user = self.db_iteraction.pgsql_connetction.session.query(Employees).get(user_id)
        print(self.__user)
        return self

    def create(self, user):
        self.__user = user
        return self

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.__user.id)

    def get_user(self):
        return self.__user