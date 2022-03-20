import pytest
import requests
from sqlalchemy import inspect

from app.db.interaction.db_iteraction import db_iteraction


@pytest.fixture()
def db():
    return db_iteraction


@pytest.fixture()
def insp(db):
    return inspect(db_iteraction.engine)


@pytest.fixture(scope='module')
def headers():
    data_login = {'email': 'tywin_lannister@gmail.com', 'password': 'power_and_money'}
    result = requests.post('http://192.168.1.48:5005/login', json=data_login).json()
    return {'Content-Type': 'application/json', 'Authorization': f'Bearer {result["access_token"]}'}


@pytest.fixture()
def server_url():
    return 'http://192.168.1.48:5005/'
