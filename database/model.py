from peewee import *

db_name = 'base.db'
sql_db = SqliteDatabase(db_name)  # дефолтное название бд


class TelegaPerson(Model):
    telega_id = IntegerField()
    user_name = CharField()
    first_name = CharField()
    last_name = CharField()
    api_token = CharField()

    class Meta:
        database = sql_db


def create_tables():
    sql_db.connect()
    sql_db.create_tables([TelegaPerson])


if __name__ == "__main__":
    create_tables()
