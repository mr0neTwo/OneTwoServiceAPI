from datetime import timedelta, datetime
from pprint import pprint
import time
import os
from urllib.request import urlopen

from flask import Flask, request, jsonify, render_template, make_response, send_from_directory, flash, redirect, url_for
from flask_cors import CORS, cross_origin
from flask_jwt_extended import create_access_token, decode_token
from flask_jwt_extended import JWTManager, jwt_required
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from flask_wtf.csrf import CSRFProtect, generate_csrf

from werkzeug.security import generate_password_hash, check_password_hash
from flask_apscheduler import APScheduler

from app.API_requests.branches import branches_api
from app.API_requests.cashboxes import cashboxes_api
from app.API_requests.change_order_status import change_status_api
from app.API_requests.employees import employees_api
from app.API_requests.equipments import equipments_api
from app.API_requests.filters import filters_api
from app.API_requests.get_main_data import main_data
from app.API_requests.operations import operation_api
from app.API_requests.order_parts import order_parts_api
from app.API_requests.orders import orders_api
from app.API_requests.payments import payment_api
from app.API_requests.payrolls import payrolls_api
from app.db.interaction.db_iteraction import db_iteraction, scheduler
from app.db.models.models import Employees

from app.reports.dailyReport import daily_report

import ssl

# pip freeze > requirements.txt
from app.user_login import UserLogin

host = os.environ['SERVER_HOST']
port = os.environ['SERVER_PORT']

print_logs = False

app = Flask(__name__, static_folder="build/static", template_folder="build")
app.register_blueprint(operation_api)
app.register_blueprint(filters_api)
app.register_blueprint(orders_api)
app.register_blueprint(equipments_api)
app.register_blueprint(change_status_api)
app.register_blueprint(payment_api)
app.register_blueprint(order_parts_api)
app.register_blueprint(cashboxes_api)
app.register_blueprint(payrolls_api)
app.register_blueprint(daily_report)
app.register_blueprint(branches_api)
app.register_blueprint(main_data)
app.register_blueprint(employees_api)

jwt = JWTManager(app)



app.config.update(
    DEBUG=False,
    SECRET_KEY='07446af7da2e08c395ac7d7a65c2d1e85b7610bbab79',
    SESSION_COOKIE_HTTPONLY=True,
    REMEMBER_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE=os.environ['SESSION_COOKIE_SAMESITE'],
    SCHEDULER_API_ENABLED=True
)



csrf = CSRFProtect(app)
cors = CORS(
    app,
    # resources={r"*": {"origins": "http://localhost:3000"}},
    resources={r"*": {"origins": "*"}},
    expose_headers=["Content-Type", "X-CSRFToken"],
    supports_credentials=True,
)


scheduler.init_app(app)
scheduler.start()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = "strong"
# login_manager.login_view = 'flogin'


@app.after_request
def after_request(response):
    # print(request.headers)
    # response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin'))
    # response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    # response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    # response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response


def page_not_found(err_description):
    return jsonify(error=str(err_description)), 404


def run_server():
    # server = threading.Thread(target=app.run, kwargs={'host': host, 'port': port})
    # server.start()
    app.run(
        debug=False,
        load_dotenv=True,
        host=os.environ['SERVER_HOST'],
        port=os.environ['SERVER_PORT']
        # ssl_context=context
        # ssl_context='adhoc'
        # ssl_context=('cert.pem', 'key.pem')
    )
    # return server


def shutdown_server():
    request.get(f'http://{host}:{port}/shutdown')


def shutdown():
    terminate_func = request.environ.get('werkzeug.server.shutdown')
    if terminate_func:
        terminate_func()

@app.route("/getcsrf", methods=["GET"])
def get_csrf():
    token = generate_csrf()
    response = jsonify({"detail": "CSRF cookie set"})
    response.headers.set("X-CSRFToken", token)
    return response



@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
# @login_required
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return render_template('index.html')

@app.route('/flogin', methods=['GET', 'POST'])
def flogin():
    if request.method == 'POST':

        request_body = dict(request.json)
        username = request_body.get('email')
        password = request_body.get('password')
        user = db_iteraction.pgsql_connetction.session.query(Employees).filter_by(email=username).first()
        if user:
            if check_password_hash(user.password, password):
                userlogin = UserLogin().create(user)
                login_user(userlogin)
                return {'success': True, 'message': "login success"}, 200
            else:
                return {'success': False, 'message': "Неверный пароль пользователя"}, 400
        else:
            return {'success': False, 'message': "Пользователь с таким логином не найден"}, 400


@app.route('/start12', methods=['GET', 'POST', 'PUT', 'DELETE'])
def get_start():
    start_time = time.time()
    db_iteraction.create_all_tables()
    db_iteraction.initial_data()
    db_iteraction.update_date_from_remonline()
    db_iteraction.reset_dict()

    dtime = time.time() - start_time
    hours = int(dtime // 3600)
    minutes = int((dtime % 3600) // 60)
    seconds = int((dtime % 3600) % 60)
    print(f'Обновление завершено за {hours}:{minutes:02}:{seconds:02}')
    return {'success': True}, 200

@app.route("/getsession", methods=["GET"])
def check_session():
    if current_user.is_authenticated:
        return jsonify({"login": True})

    return jsonify({"login": False})

@app.route("/data", methods=["POST"])
@login_required
def user_data():

    return jsonify({"username": 'Джейме Ланистер'})

# @app.route('/login')
# def login():
#     request_body = dict(request.json)
#     if request.method == 'POST':
#         user = db_iteraction.get_employee(email=request_body['email'])['data'][0] if \
#         db_iteraction.get_employee(email=request_body['email'])['data'] else None
#         if user:
#             if check_password_hash(user['password'], request_body['password']):
#                 expire_delta = timedelta(hours=12)
#                 token = create_access_token(identity=user['id'], expires_delta=expire_delta)
#
#                 response = make_response({'success': True, 'access_token': token, 'user': user}, 200)
#                 response.headers['Content-Type'] = 'application/json'
#                 return response
#             return {'success': False, 'message': 'Неверный пароль пользователя'}, 400
#         return {'success': False, 'message': 'Пользователь не найден'}, 400



@login_manager.user_loader
def load_user(user_id):
    return UserLogin().fromDB(user_id)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    print('loguot')
    return jsonify({"logout": True})



# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@app.route('/get_ad_campaign', methods=['POST'])
@login_required
def get_ad_campaign():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    name = request_body.get('name')
    if name:
        name = str(name)

    result = db_iteraction.get_adCampaign(
        id=id,  # int - id рекламной компании - полное совпадение
        name=name  # str - Имя рекламной компании - частичное совпадение
    )
    return result, 200


@app.route('/ad_campaign', methods=['POST', 'PUT', 'DELETE'])
@login_required
def ad_campaign():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    name = request_body.get('name')
    if name:
        name = str(name)

    if request.method == 'POST':

        if not name:
            return {'success': False, 'message': 'name required'}, 400

        db_iteraction.add_adCampaign(
            name=name  # str - Название рекламной компании - обязательное поле
        )
        return {'success': True, 'message': f'{name} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_adCampaign(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_adCampaign(
            id=id,  # int - id записи - полное совпаден
            name=name,  # str - Новое название рекламной компании
        )
        return {'success': True, 'message': f'{name} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_adCampaign(
            id=id)  # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202





@app.route('/get_table_headers', methods=['POST'])
@login_required
def get_table_headers():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    title = request_body.get('title')
    if title and type(title) != list:
        return {'success': False, 'message': "title is not list"}, 400
    if title and any([type(tit) != str for tit in title]):
        return {'success': False, 'message': "title include not str"}, 400

    field = request_body.get('field')
    if field and type(field) != list:
        return {'success': False, 'message': "field is not list"}, 400
    if field and any([type(tit) != str for tit in field]):
        return {'success': False, 'message': "field include not str"}, 400

    employee_id = request_body.get('employee_id')
    if employee_id and type(employee_id) != int:
        return {'success': False, 'message': "employee_id is not integer"}, 400
    if employee_id:
        if db_iteraction.get_employee(id=employee_id)['count'] == 0:
            return {'success': False, 'message': 'employee_id is not defined'}, 400

    visible = request_body.get('visible')
    if visible:
        visible = bool(visible)

    result = db_iteraction.get_table_headers(
        id=id,  # int - id поля - полное совпадение
        title=title,  # [str, ...str] - текст поля - полное совпадение
        field=field,  # [str, ...str] - имя поля - полное совпадение
        employee_id=employee_id,  # int - id инженера, которому пренадлежит поле - полное совпадение
        visible=visible  # bool - статус отображения - - полное совпадение
    )
    return result, 200


@app.route('/table_headers', methods=['POST', 'PUT', 'DELETE'])
@login_required
def table_headers():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    title = request_body.get('title')
    if title:
        title = str(title)

    field = request_body.get('field')
    if field:
        field = str(field)

    width = request_body.get('width')
    if width and type(width) != int:
        return {'success': False, 'message': "width is not integer"}, 400

    employee_id = request_body.get('employee_id')
    if employee_id and type(employee_id) != int:
        return {'success': False, 'message': "employee_id is not integer"}, 400
    if employee_id:
        if db_iteraction.get_employee(id=employee_id)['count'] == 0:
            return {'success': False, 'message': 'employee_id is not defined'}, 400

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_branch(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    visible = request_body.get('visible')
    if visible:
        visible = bool(visible)

    if request.method == 'POST':

        if not title:
            return {'success': False, 'message': 'title required'}, 400

        if not field:
            return {'success': False, 'message': 'field required'}, 400

        if not width:
            return {'success': False, 'message': 'width required'}, 400

        if not employee_id:
            return {'success': False, 'message': 'employee_id required'}, 400

        db_iteraction.add_table_headers(
            title=title,  # str - Текст поля - обязательное поле
            field=field,  # str - Имя поля - обязательное поле
            width=width,  # str - Ширина поля - обязательное поле
            employee_id=employee_id,  # int - id сотрудника - обязательное поле
            visible=visible  # bool - Статус отображения
        )
        return {'success': True, 'message': f'{title} added'}, 201

    if request.method == 'PUT':
        db_iteraction.edit_table_headers(
            id=id,  # int - id записи - полное совпаден
            title=title,  # str - Текст поля
            field=field,  # str - Имя поля
            width=width,  # str - Ширина поля
            employee_id=employee_id,  # int - id сотрудника
            visible=visible  # bool - Статус отображения
        )
        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_table_headers(
            id=id)  # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202


@app.route('/get_attachments', methods=['POST'])
@login_required
def get_attachments():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    # Проверим входные данные
    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    created_by_id = request_body.get('created_by_id')
    if created_by_id and type(created_by_id) != int:
        return {'success': False, 'message': "created_by_id is not integer"}, 400

    # Проверим сущестует ли запись по данному id
    if created_by_id:
        if db_iteraction.get_employee(id=created_by_id)['count'] == 0:
            return {'success': False, 'message': 'created_by_id is not defined'}, 400

    filename = request_body.get('filename')
    if filename:
        filename = str(filename)

    # Проверка массива дат для поиска
    created_at = request_body.get('created_at')
    if created_at:
        if type(created_at) != list:
            return {'success': False, 'message': "created_at is not list"}, 400
        if len(created_at) != 2:
            return {'success': False, 'message': "created_at is not correct"}, 400
        if (type(created_at[0]) != int) or (type(created_at[1]) != int):
            return {'success': False, 'message': "created_at has not integers"}, 400

    result = db_iteraction.get_attachments(
        id=id,  # int - ID записи о вложении -  полное совпадение
        created_by_id=created_by_id,  # int - ID сотрудника - полное совпадение
        created_at=created_at,  # array - Из двах дат в timestamp - диапазон выбоки по времени
        filename=filename,  # str - Имя файла - частичное совподение
        page=page  # Номер страницы для вывода пагинацией
    )
    return result, 200


@app.route('/attachments', methods=['POST', 'PUT', 'DELETE'])
@login_required
def attachments():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    # Проверим входные данные
    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    created_by_id = request_body.get('created_by_id')
    if created_by_id and type(created_by_id) != int:
        return {'success': False, 'message': "created_by_id is not integer"}, 400

    # Проверим сущестует ли запись по данному id
    if created_by_id:
        if db_iteraction.get_employee(id=created_by_id)['count'] == 0:
            return {'success': False, 'message': 'created_by_id is not defined'}, 400

    filename = request_body.get('filename')
    if filename:
        filename = str(filename)

    url = request_body.get('url')
    if url:
        url = str(url)

    # Проверка заданной даты создания
    created_at = request_body.get('created_at')
    if created_at and type(created_at) != int:
        return {'success': False, 'message': "created_at is not integer"}, 400

    if request.method == 'POST':

        if not created_by_id:
            return {'success': False, 'message': 'created_by_id required'}, 400

        if not filename:
            return {'success': False, 'message': 'filename required'}, 400

        if not url:
            return {'success': False, 'message': 'url required'}, 400

        db_iteraction.add_attachments(
            created_by_id=created_by_id,  # int - ID сотрудника
            created_at=created_at,  # int (timestamp) - Дата создания, по дефолту now
            filename=filename,  # str - Имя файла
            url=url,  # str - Путь к файлу
        )
        return {'success': True, 'message': f"{request_body.get('filename')} added"}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_attachments(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_attachments(
            id=id,  # int - id записи - полное совпадение
            created_by_id=created_by_id,  # int - Новый id инженера
            created_at=created_at,  # int - Ноывая дата создания
            filename=filename,  # str - Новое имя файла
            url=url,  # str - Новый путь к файлу
        )
        return {'success': True, 'message': f"{id} changed"}, 202

    if request.method == 'DELETE':
        db_iteraction.del_attachments(id=id)  # int - id записи - полное совпадение
        return {'success': True, 'message': f"{id} deleted"}, 202


@app.route('/get_discount_margin', methods=['POST'])
@login_required
def get_discount_margin():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    margin_type = request_body.get('margin_type')
    if margin_type and type(margin_type) != int:
        return {'success': False, 'message': "margin_type is not integer"}, 400

    deleted = request_body.get('deleted')
    if deleted:
        deleted = bool(deleted)

    title = request_body.get('title')
    if title:
        title = str(title)

    result = db_iteraction.get_discount_margin(
        id=id,  # int - id наценки - полное совпадение
        title=title,  # str - Имя наценки - частичное совпадение
        margin_type=margin_type,
        deleted=deleted,
        page=page  # int - Старница погинации
    )
    return result, 200


@app.route('/discount_margin', methods=['POST', 'PUT', 'DELETE'])
@login_required
def discount_margin():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    margin = request_body.get('margin')
    if margin:
        try:
            margin = float(margin)
        except:
            return {'success': False, 'message': 'Margin is not number'}, 400

    margin_type = request_body.get('margin_type')
    if margin_type and type(margin_type) != int:
        return {'success': False, 'message': "margin_type is not integer"}, 400

    title = request_body.get('title')
    if title:
        title = str(title)

    deleted = request_body.get('deleted')
    if deleted:
        deleted = bool(deleted)

    if request.method == 'POST':

        if not margin and margin != 0:
            return {'success': False, 'message': 'Margin required'}, 400

        if not title:
            return {'success': False, 'message': 'Title required'}, 400

        db_iteraction.add_discount_margin(
            title=title,  # str - Название наценки - обязательное поле
            margin=margin,  # float - Значение наценки - обязательное полу
            margin_type=margin_type,
            deleted=deleted
        )
        return {'success': True, 'message': f'{title} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_discount_margin(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_discount_margin(
            id=id,  # int - id записи - полное совпаден
            title=title,  # str - Новое название наценки
            margin=margin,  # str - Новое значение наценки
            margin_type=margin_type,
            deleted=deleted
        )
        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_discount_margin(
            id=id)  # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202


@app.route('/get_order_type', methods=['POST'])
@login_required
def get_order_type():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    name = request_body.get('name')
    if name:
        name = str(name)

    result = db_iteraction.get_order_type(
        id=id,  # int - id типа - полное совпадение
        name=name,  # str - Имя типа - частичное совпадение
        page=page  # int - Старница погинации
    )
    return result, 200


@app.route('/order_type', methods=['POST', 'PUT', 'DELETE'])
@login_required
def order_type():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    name = request_body.get('name')
    if name:
        name = str(name)

    if request.method == 'POST':

        if not name:
            return {'success': False, 'message': 'Name required'}, 400

        db_iteraction.add_order_type(
            name=name  # str - Название типа - обязательное поле
        )
        return {'success': True, 'message': f'{name} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_order_type(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_order_type(
            id=id,  # int - id записи - полное совпаден
            name=name,  # str - Новое название типа
        )
        return {'success': True, 'message': f'{name} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_order_type(
            id=id)  # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202


@app.route('/get_status_group', methods=['POST'])
@login_required
def get_status_group():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    name = request_body.get('name')
    if name:
        name = str(name)

    type_group = request_body.get('type_group')
    if type_group and type(type_group) != int:
        return {'success': False, 'message': "type_group is not integer"}, 400

    result = db_iteraction.get_status_group(
        id=id,  # int - id группы статусов - полное совпадение
        name=name,  # str - Имя группы статуов - частичное совпадение
        type_group=type_group,  # int - Номер группы - полное совпадение
        page=page  # int - Старница погинации
    )
    return result, 200


@app.route('/status_group', methods=['POST', 'PUT', 'DELETE'])
@login_required
def status_group():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    name = request_body.get('name')
    if name:
        name = str(name)

    type_group = request_body.get('type_group')
    if type_group and type(type_group) != int:
        return {'success': False, 'message': "type_group is not integer"}, 400

    color = request_body.get('color')
    if color:
        color = str(color)

    if request.method == 'POST':

        # Проверим уникальность type_group
        if db_iteraction.get_status_group(type_group=type_group)['count'] != 0:
            return {'success': False, 'message': 'type_group is not unique'}, 400

        if not name:
            return {'success': False, 'message': 'name required'}, 400

        if not type_group:
            return {'success': False, 'message': 'type_group required'}, 400

        db_iteraction.add_status_group(
            name=name,  # str - Имя группы статуов - обязательное поле
            type_group=type_group,  # int - Номер группы - обязательное поле
            color=color  # str - цвет группы
        )
        return {'success': True, 'message': f'{name} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_status_group(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_status_group(
            id=id,  # int - id записи - полное совпаден
            name=name,  # str - Новое название группы статусов
            type_group=type_group,  # int - Новый номер группы
            color=color  # str - Новый цвет группы
        )
        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_status_group(
            id=id)  # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202


@app.route('/get_status', methods=['POST'])
@login_required
def get_status():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    name = request_body.get('name')
    if name:
        name = str(name)

    color = request_body.get('color')
    if color:
        color = str(color)

    group = request_body.get('group')
    if group and type(group) != int:
        return {'success': False, 'message': "group is not integer"}, 400

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_status_group(type_group=group)['count'] == 0:
        return {'success': False, 'message': 'group is not defined'}, 400

    result = db_iteraction.get_status(
        id=id,  # int - id статуса - полное совпадение
        name=name,  # str - Имя статуса - частичное совпадение
        color=color,  # str - Цвет статуса - полное совпадение
        group=group,  # int - Номер группы - полное совпадение
        page=page  # int - Старница погинации
    )
    return result


@app.route('/status', methods=['POST', 'PUT', 'DELETE'])
@login_required
def status():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    name = request_body.get('name')
    if name:
        name = str(name)

    color = request_body.get('color')
    if color:
        color = str(color)

    group = request_body.get('group')
    if group and type(group) != int:
        return {'success': False, 'message': "group is not integer"}, 400

    deadline = request_body.get('deadline')
    if deadline and type(deadline) != int:
        return {'success': False, 'message': "deadline is not integer"}, 400

    comment_required = request_body.get('comment_required')
    if comment_required:
        comment_required = bool(comment_required)

    payment_required = request_body.get('payment_required')
    if payment_required:
        payment_required = bool(payment_required)

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_status_group(type_group=group)['count'] == 0:
        return {'success': False, 'message': 'group is not defined'}, 400

    available_to = request_body.get('available_to')
    if available_to and type(available_to) != list:
        return {'success': False, 'message': "available_to is not list"}, 400
    if available_to:
        if not all([type(available) == int for available in available_to]):
            return {'success': False, 'message': "available_to has not integer"}, 400

    if request.method == 'POST':
        if not name:
            return {'success': False, 'message': 'name required'}, 400

        if not group:
            return {'success': False, 'message': 'group required'}, 400

        if not color:
            return {'success': False, 'message': 'color required'}, 400

        db_iteraction.add_status(
            name=name,  # str - Имя группы статуов - обязательное поле
            color=color,  # str - Цвет статуса - обязательное поле
            group=group,  # int - Номер группы - обязательное поле
            deadline=deadline,  # int - Дедлайн статуса
            comment_required=comment_required,  # bool - Требуется ли коментарий
            payment_required=payment_required,  # bool - Требуется ли платеж
            available_to=available_to  # [int, ...int] - Список статусов доступных для прехода
        )
        return {'success': True, 'message': f'{name} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_status(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_status(
            id=id,  # int - id записи - полное совпаден
            name=name,  # str - Новое название статуса
            color=color,  # str - Новый цвет статуса
            group=group,  # int - Новый номер группы
            deadline=deadline,  # int - Новый дедлайн статуса
            comment_required=comment_required,  # bool - Требуется коментарий
            payment_required=payment_required,  # bool - Требуется платеж
            available_to=available_to  # [int, ...int] - Новый список статусов для перехода
        )
        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_status(
            id=id)  # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202


@app.route('/get_clients', methods=['POST'])
@login_required
def get_clients():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    conflicted = request_body.get('conflicted')
    if conflicted:
        conflicted = bool(conflicted)

    deleted = request_body.get('deleted')
    if deleted:
        deleted = bool(deleted)

    discount_goods_margin_id = request_body.get('discount_goods_margin_id')
    if discount_goods_margin_id and type(discount_goods_margin_id) != int:
        return {'success': False, 'message': "discount_goods_margin_id is not integer"}, 400

    if discount_goods_margin_id and db_iteraction.get_discount_margin(id=discount_goods_margin_id)['count'] == 0:
        return {'success': False, 'message': 'discount_goods_margin_id is not defined'}, 400

    discount_materials = request_body.get('discount_materials', 0)
    if discount_materials:
        try:
            discount_materials = float(discount_materials)
        except:
            return {'success': False, 'message': 'discount_materials is not number'}, 400

    discount_materials_margin_id = request_body.get('discount_materials_margin_id')
    if discount_materials_margin_id and type(discount_materials_margin_id) != int:
        return {'success': False, 'message': "discount_materials_margin_id is not integer"}

    if discount_materials_margin_id and db_iteraction.get_discount_margin(id=discount_materials_margin_id)[
        'count'] == 0:
        return {'success': False, 'message': 'discount_materials_margin_id is not defined'}, 400

    discount_services = request_body.get('discount_services', 0)
    if discount_materials:
        try:
            discount_services = float(discount_services)
        except:
            return {'success': False, 'message': 'discount_services is not number'}, 400

    email = request_body.get('email')
    if email:
        email = str(email)

    juridical = request_body.get('juridical')
    if juridical:
        juridical = bool(juridical)

    name = request_body.get('name')
    if name:
        name = str(name)

    notes = request_body.get('notes')
    if notes:
        notes = str(notes)

    supplier = request_body.get('supplier')
    if supplier:
        supplier = bool(supplier)

    created_at = request_body.get('created_at')

    phone = request_body.get('phone')

    if created_at:
        if type(created_at) != list:
            return {'success': False, 'message': "created_at is not list"}, 400
        if len(created_at) != 2:
            return {'success': False, 'message': "created_at is not correct"}, 400
        if type(created_at[0]) != int:
            return {'success': False, 'message': "created_at has not integers"}, 400
        if type(created_at[1]) and type(created_at[1]) != int:
            return {'success': False, 'message': "created_at has not integers"}, 400

    result = db_iteraction.get_clients(
        id=id,  # int - id клиента - полное совпадение
        conflicted=conflicted,  # bool - Конфликтный - полное совпадение
        email=email,  # str - Электронная почта - частичное совпадение
        juridical=juridical,  # bool - Юридическое лицо - полное совпадение
        deleted=deleted,
        name=name,  # str - ФИО клиета - частично совпадение
        supplier=supplier,  # bool - Поставщик - полное совпадение
        phone=phone,
        page=page  # int - Старница погинации
        # ad_campaign_id=ad_campaign_id,                              # int - id рекламной компании - прлное совпадение
        # address=address,                                            # str - Адрес клиента - частичное совпадение
        # name_doc=name_doc,                                          # str - Имя в печатных документах - частичное совпадение
        # discount_code=discount_code,                                # str - Скидочная карта - частичное совпадение
        # discount_goods=discount_goods,                              # float - Скидка на товары - полное совпадение
        # discount_goods_margin_id=discount_goods_margin_id,          # int - id типа наценки - полное совпадение
        # discount_materials=discount_materials,                      # float - Скидка на материалы - полное совпадение
        # discount_materials_margin_id=discount_materials_margin_id,  # int - id типа наценки - полное совпадение
        # discount_services=discount_services,                        # float - скидка на услуги - полное совпадение
        # created_at=created_at,                                      # [int, int] - дата создания - массив из начальной и конечной даты поиска
        # notes=notes,                                                # str - Заметки - частичное совпадение
    )
    return result, 200


@app.route('/clients', methods=['POST', 'PUT', 'DELETE'])
@login_required
def clients():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    juridical = request_body.get('juridical')
    if juridical and type(juridical) != bool:
        return {'success': False, 'message': 'juridical is not boolean'}, 400

    supplier = request_body.get('supplier')
    if supplier and type(supplier) != bool:
        return {'success': False, 'message': 'supplier is not boolean'}, 400

    conflicted = request_body.get('conflicted')
    if conflicted and type(conflicted) != bool:
        return {'success': False, 'message': 'conflicted is not boolean'}, 400

    should_send_email = request_body.get('should_send_email')
    if should_send_email and type(should_send_email) != bool:
        return {'success': False, 'message': 'should_send_email is not boolean'}, 400

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    discount_good_type = request_body.get('discount_good_type')
    if discount_good_type and type(discount_good_type) != bool:
        return {'success': False, 'message': 'discount_good_type is not boolean'}, 400

    discount_materials_type = request_body.get('discount_materials_type')
    if discount_materials_type and type(discount_materials_type) != bool:
        return {'success': False, 'message': 'discount_materials_type is not boolean'}, 400

    discount_service_type = request_body.get('discount_service_type')
    if discount_service_type and type(discount_service_type) != bool:
        return {'success': False, 'message': 'discount_service_type is not boolean'}, 400

    name = request_body.get('name')
    if name:
        name = str(name)

    name_doc = request_body.get('name_doc')
    if name_doc:
        name_doc = str(name_doc)

    email = request_body.get('email')
    if email:
        email = str(email)

    address = request_body.get('address')
    if address:
        address = str(address)

    discount_code = request_body.get('discount_code')
    if discount_code:
        discount_code = str(discount_code)

    notes = request_body.get('notes')
    if notes:
        notes = str(notes)

    ogrn = request_body.get('ogrn')
    if ogrn:
        ogrn = str(ogrn)

    inn = request_body.get('inn')
    if inn:
        inn = str(inn)

    kpp = request_body.get('kpp')
    if kpp:
        kpp = str(kpp)

    juridical_address = request_body.get('juridical_address')
    if juridical_address:
        juridical_address = str(juridical_address)

    director = request_body.get('director')
    if director:
        director = str(director)

    bank_name = request_body.get('bank_name')
    if bank_name:
        bank_name = str(bank_name)

    settlement_account = request_body.get('settlement_account')
    if settlement_account:
        settlement_account = str(settlement_account)

    corr_account = request_body.get('corr_account')
    if corr_account:
        corr_account = str(corr_account)

    bic = request_body.get('bic')
    if bic:
        bic = str(bic)

    discount_goods = request_body.get('discount_goods', 0)
    if discount_goods:
        try:
            discount_goods = float(discount_goods)
        except:
            return {'success': False, 'message': 'discount_goods is not number'}, 400

    discount_materials = request_body.get('discount_materials', 0)
    if discount_materials:
        try:
            discount_materials = float(discount_materials)
        except:
            return {'success': False, 'message': 'discount_materials is not number'}, 400

    discount_services = request_body.get('discount_services', 0)
    if discount_materials:
        try:
            discount_services = float(discount_services)
        except:
            return {'success': False, 'message': 'discount_services is not number'}, 400

    ad_campaign_id = request_body.get('ad_campaign_id')
    if ad_campaign_id and type(ad_campaign_id) != int:
        return {'success': False, 'message': "ad_campaign_id is not integer"}, 400
    if ad_campaign_id and db_iteraction.get_adCampaign(id=ad_campaign_id)['count'] == 0:
        return {'success': False, 'message': 'ad_campaign_id is not defined'}, 400

    discount_goods_margin_id = request_body.get('discount_goods_margin_id')
    if discount_goods_margin_id and type(discount_goods_margin_id) != int:
        return {'success': False, 'message': "discount_goods_margin_id is not integer"}, 400
    if discount_goods_margin_id and db_iteraction.get_discount_margin(id=discount_goods_margin_id)['count'] == 0:
        return {'success': False, 'message': 'discount_goods_margin_id is not defined'}, 400

    discount_materials_margin_id = request_body.get('discount_materials_margin_id')
    if discount_materials_margin_id and type(discount_materials_margin_id) != int:
        return {'success': False, 'message': "discount_materials_margin_id is not integer"}
    if discount_materials_margin_id and db_iteraction.get_discount_margin(id=discount_materials_margin_id)[
        'count'] == 0:
        return {'success': False, 'message': 'discount_materials_margin_id is not defined'}, 400

    discount_service_margin_id = request_body.get('discount_service_margin_id')
    if discount_service_margin_id and type(discount_service_margin_id) != int:
        return {'success': False, 'message': "discount_service_margin_id is not integer"}
    if discount_service_margin_id and db_iteraction.get_discount_margin(id=discount_service_margin_id)[
        'count'] == 0:
        return {'success': False, 'message': 'discount_service_margin_id is not defined'}, 400

    tags = request_body.get('tags')
    if tags and type(tags) != list:
        return {'success': False, 'message': "tags is not list"}, 400
    if tags:
        if not all([type(tag) == str for tag in tags]):
            return {'success': False, 'message': "tags has not string"}, 400

    created_at = request_body.get('created_at')

    phone = request_body.get('phone')

    if request.method == 'POST':

        if not ad_campaign_id:
            return {'success': False, 'message': 'ad_campaign_id required'}, 400

        if not discount_goods_margin_id:
            return {'success': False, 'message': 'discount_goods_margin_id required'}, 400

        if not discount_materials_margin_id:
            return {'success': False, 'message': 'discount_materials_margin_id required'}, 400

        if created_at and type(created_at) != int:
            return {'success': False, 'message': "created_at is not integer"}, 400

        if not name:
            return {'success': False, 'message': 'name required'}, 400

        id_create_client = db_iteraction.add_clients(
            juridical=juridical,  # bool - Юридическое лицо
            supplier=supplier,  # bool - Поставщик - полное совпадение
            conflicted=conflicted,  # bool - Конфликтный
            should_send_email=should_send_email,  # bool - Согласен получать email
            deleted=deleted,
            discount_good_type=discount_good_type,
            discount_materials_type=discount_materials_type,
            discount_service_type=discount_service_type,

            name=name,  # str - ФИО клиета - обязательное поле
            name_doc=name_doc,  # str - Имя в печатных документах
            email=email,  # str - Электронная почта
            address=address,  # str - Адрес клиента
            discount_code=discount_code,  # str - Скидочная карта
            notes=notes,  # str - Заметки
            ogrn=ogrn,  # str - ОГРН
            inn=inn,  # str - ИНН
            kpp=kpp,  # str - КПП
            juridical_address=juridical_address,  # str - Юредический адресс
            director=director,  # str - Директор
            bank_name=bank_name,  # str - Наименование банка
            settlement_account=settlement_account,  # str - Расчетный счет
            corr_account=corr_account,  # str - Кор. счет
            bic=bic,  # str - БИК

            discount_goods=discount_goods,  # float - Скидка на товары
            discount_materials=discount_materials,  # float - Скидка на материалы
            discount_services=discount_services,  # float - скидка на услуги

            ad_campaign_id=ad_campaign_id,  # int - id рекламной компании
            discount_goods_margin_id=discount_goods_margin_id,  # int - id типа наценки
            discount_materials_margin_id=discount_materials_margin_id,  # int - id типа наценки
            discount_service_margin_id=discount_service_margin_id,

            tags=tags,  # [str, ...str] - теги
            created_at=created_at,  # int - дата создания
        )
        if phone:
            for ph in phone:
                db_iteraction.add_phone(
                    number=ph['number'],
                    title=ph['title'],
                    notify=ph['notify'],
                    client_id=id_create_client
                )
        create_client = db_iteraction.get_clients(id=id_create_client)['data'][0]

        return {'success': True, 'data': create_client, 'message': f'{name} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_clients(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_clients(
            id=id,  # int - id записи - полное совпаден
            juridical=juridical,  # bool - Юридическое лицо
            supplier=supplier,  # bool - Поставщик - полное совпадение
            conflicted=conflicted,  # bool - Конфликтный
            should_send_email=should_send_email,  # bool - Согласен получать email
            deleted=deleted,
            discount_good_type=discount_good_type,
            discount_materials_type=discount_materials_type,
            discount_service_type=discount_service_type,

            name=name,  # str - ФИО клиета - обязательное поле
            name_doc=name_doc,  # str - Имя в печатных документах
            email=email,  # str - Электронная почта
            address=address,  # str - Адрес клиента
            discount_code=discount_code,  # str - Скидочная карта
            notes=notes,  # str - Заметки
            ogrn=ogrn,  # str - ОГРН
            inn=inn,  # str - ИНН
            kpp=kpp,  # str - КПП
            juridical_address=juridical_address,  # str - Юредический адресс
            director=director,  # str - Директор
            bank_name=bank_name,  # str - Наименование банка
            settlement_account=settlement_account,  # str - Расчетный счет
            corr_account=corr_account,  # str - Кор. счет
            bic=bic,  # str - БИК

            discount_goods=discount_goods,  # float - Скидка на товары
            discount_materials=discount_materials,  # float - Скидка на материалы
            discount_services=discount_services,  # float - скидка на услуги

            ad_campaign_id=ad_campaign_id,  # int - id рекламной компании
            discount_goods_margin_id=discount_goods_margin_id,  # int - id типа наценки
            discount_materials_margin_id=discount_materials_margin_id,  # int - id типа наценки
            discount_service_margin_id=discount_service_margin_id,

            tags=tags,  # [str, ...str] - теги
        )
        if phone:
            for ph in phone:
                if ph.get('id'):
                    db_iteraction.edit_phones(
                        id=ph['id'],
                        number=ph['number'],
                        title=ph['title'],
                        notify=ph['notify'],
                        client_id=id
                    )
                else:
                    db_iteraction.add_phone(
                        number=ph['number'],
                        title=ph['title'],
                        notify=ph['notify'],
                        client_id=id
                    )

        client = db_iteraction.get_clients(id=id)['data'][0]

        return {'success': True, 'data': client, 'message': f'{name} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_clients(
            id=id)  # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202


@app.route('/get_menu_rows', methods=['POST'])
@login_required
def get_menu_rows():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    title = request_body.get('title')
    if title and type(title) != list:
        return {'success': False, 'message': "id is not list"}, 400
    if title and any([type(tit) != str for tit in title]):
        return {'success': False, 'message': "title include not str"}, 400

    group_name = request_body.get('group_name')
    if group_name and type(group_name) != list:
        return {'success': False, 'message': "title is not list"}, 400
    if group_name and any([type(group_name) != str for tit in group_name]):
        return {'success': False, 'message': "group_name include not str"}, 400

    result = db_iteraction.get_menu_row(
        id=id,  # int - id строчки - полное совпадение
        title=title,  # [str, ...str] - Список имен строчек
        group_name=group_name  # [str, ...str] - Список имен групп
    )
    return result, 200


@app.route('/get_setting_menu', methods=['POST'])
@login_required
def get_setting_menu():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    title = request_body.get('title')
    if title and type(title) != list:
        return {'success': False, 'message': "id is not list"}, 400
    if title and any([type(tit) != str for tit in title]):
        return {'success': False, 'message': "title include not str"}, 400

    group_name = request_body.get('group_name')
    if group_name and type(group_name) != list:
        return {'success': False, 'message': "title is not list"}, 400
    if group_name and any([type(group_name) != str for tit in group_name]):
        return {'success': False, 'message': "group_name include not str"}, 400

    result = db_iteraction.get_setting_menu(
        id=id,  # int - id строчки - полное совпадение
        title=title,  # [str, ...str] - Список имен строчек
        group_name=group_name  # [str, ...str] - Список имен групп
    )
    return result, 200


@app.route('/get_roles', methods=['POST'])
@login_required
def get_roles():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    title = request_body.get('title')
    if title:
        title = str(title)

    result = db_iteraction.get_role(
        id=id,  # int - id роли - полное совпадение
        title=title,  # str - Роль - частичное совпадение
        page=page  # int - Старница погинации
    )
    return result, 200


@app.route('/roles', methods=['POST', 'PUT', 'DELETE'])
@login_required
def roles():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    title = request_body.get('title')
    if title:
        title = str(title)

    earnings_visibility = request_body.get('earnings_visibility')
    if earnings_visibility:
        earnings_visibility = bool(earnings_visibility)

    leads_visibility = request_body.get('leads_visibility')
    if leads_visibility:
        leads_visibility = bool(leads_visibility)

    orders_visibility = request_body.get('orders_visibility')
    if orders_visibility:
        orders_visibility = bool(orders_visibility)

    permissions = request_body.get('permissions')
    if permissions and type(permissions) != list:
        return {'success': False, 'message': "permissions is not list"}, 400
    if permissions:
        if not all([type(permission) == str for permission in permissions]):
            return {'success': False, 'message': "permissions has not string"}, 400

    settable_statuses = request_body.get('settable_statuses')
    if settable_statuses and type(settable_statuses) != list:
        return {'success': False, 'message': "settable_statuses is not list"}, 400
    if settable_statuses:
        if not all([type(settable_status) == int for settable_status in settable_statuses]):
            return {'success': False, 'message': "settable_statuses has not integer"}, 400

    visible_statuses = request_body.get('visible_statuses')
    if visible_statuses and type(visible_statuses) != list:
        return {'success': False, 'message': "visible_statuses is not list"}, 400
    if visible_statuses:
        if not all([type(visible_status) == int for visible_status in visible_statuses]):
            return {'success': False, 'message': "visible_statuses has not integer"}, 400

    settable_discount_margin = request_body.get('settable_discount_margin')
    if settable_discount_margin and type(settable_discount_margin) != list:
        return {'success': False, 'message': "settable_discount_margin is not list"}, 400
    if settable_discount_margin:
        if not all([type(discount_margin) == int for discount_margin in settable_discount_margin]):
            return {'success': False, 'message': "settable_discount_margin has not integer"}, 400

    if request.method == 'POST':

        if not title:
            return {'success': False, 'message': 'title required'}, 400

        db_iteraction.add_role(
            title=title,  # str - Роль - обязательное поле
            earnings_visibility=earnings_visibility,  # bool - Видит только свою ЗП
            leads_visibility=leads_visibility,  # bool - Видит только свои обращения
            orders_visibility=orders_visibility,  # bool - Видит тольк свои заказы
            permissions=permissions,  # [str, ...str] - Список разрешений
            settable_statuses=settable_statuses,  # [int, ...int] - Может устанавливать статусы
            visible_statuses=visible_statuses,  # [int, ...int] - Может видеть статусы
            settable_discount_margin=settable_discount_margin  # [int, ...int] - Может использовать цены
        )
        return {'success': True, 'message': f'{title} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_role(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_role(
            id=id,  # int - id записи - полное совпаден
            title=title,  # str - Новое название роли
            earnings_visibility=earnings_visibility,  # bool - Видит только свою ЗП
            leads_visibility=leads_visibility,  # bool - Видит только свои обращения
            orders_visibility=orders_visibility,  # bool - Видит тольк свои заказы
            permissions=permissions,  # [str, ...str] - Новый список разрешений
            settable_statuses=settable_statuses,  # [int, ...int] - Новый список статуов, которые может устанавливать
            visible_statuses=visible_statuses,  # [int, ...int] - Новый список статуов, которые может видеть
            settable_discount_margin=settable_discount_margin  # [int, ...int] - Может использовать цены
        )
        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_roles(
            id=id)  # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202


@app.route('/get_generally_info', methods=['POST'])
@login_required
def get_generally_info():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    result = db_iteraction.get_generally_info(
        id=id,  # int - id филиала - полное совпадение
    )
    return result, 200


@app.route('/generally_info', methods=['POST', 'PUT', 'DELETE'])
@login_required
def generally_info():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    name = request_body.get('name')
    if name:
        name = str(name)

    address = request_body.get('address')
    if address:
        address = str(address)

    email = request_body.get('email')
    if email:
        email = str(email)

    ogrn = request_body.get('ogrn')
    if ogrn:
        ogrn = str(ogrn)

    inn = request_body.get('inn')
    if inn:
        inn = str(inn)

    kpp = request_body.get('kpp')
    if kpp:
        kpp = str(kpp)

    juridical_address = request_body.get('juridical_address')
    if juridical_address:
        juridical_address = str(juridical_address)

    director = request_body.get('director')
    if director:
        director = str(director)

    bank_name = request_body.get('bank_name')
    if bank_name:
        bank_name = str(bank_name)

    settlement_account = request_body.get('settlement_account')
    if settlement_account:
        settlement_account = str(settlement_account)

    corr_account = request_body.get('corr_account')
    if corr_account:
        corr_account = str(corr_account)

    bic = request_body.get('bic')
    if bic:
        bic = str(bic)

    description = request_body.get('description')
    if description:
        description = str(description)

    phone = request_body.get('phone')
    if phone:
        phone = str(phone)

    logo = request_body.get('logo')
    if logo:
        logo = str(logo)

    if request.method == 'POST':

        if not name:
            return {'success': False, 'message': 'name required'}, 400

        db_iteraction.add_generally_info(
            name=name,
            address=address,
            email=email,

            ogrn=ogrn,
            inn=inn,
            kpp=kpp,
            juridical_address=juridical_address,
            director=director,
            bank_name=bank_name,
            settlement_account=settlement_account,
            corr_account=corr_account,
            bic=bic,

            description=description,
            phone=phone,
            logo=logo
        )
        return {'success': True, 'message': f'{name} added'}, 201

    # # Проверим сущестует ли запись по данному id
    # if db_iteraction.get_generally_info(id=id)['count'] == 0:
    #     return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_generally_info(
            id=id,  # int - id записи - полное совпаден
            name=name,
            address=address,
            email=email,

            ogrn=ogrn,
            inn=inn,
            kpp=kpp,
            juridical_address=juridical_address,
            director=director,
            bank_name=bank_name,
            settlement_account=settlement_account,
            corr_account=corr_account,
            bic=bic,

            description=description,
            phone=phone,
            logo=logo
        )
        return {'success': True, 'message': f'{name} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_generally_info(
            id=id)  # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202


@app.route('/get_counts', methods=['POST'])
@login_required
def get_counts():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    result = db_iteraction.get_counts(
        id=id  # int - id  - полное совпадение
    )
    return result, 200


@app.route('/counts', methods=['POST', 'PUT', 'DELETE'])
@login_required
def counts():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    prefix = request_body.get('prefix')
    if prefix:
        prefix = str(prefix)

    count = request_body.get('count')
    if count and type(count) != int:
        return {'success': False, 'message': "count is not integer"}, 400

    description = request_body.get('description')
    if description:
        description = str(description)

    if request.method == 'POST':
        db_iteraction.add_counts(
            prefix=prefix,
            count=count,
            description=description
        )

        return {'success': True, 'message': f'{prefix} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_counts(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_counts(
            id=id,  # int - id записи - полное совпаден
            prefix=prefix,
            count=count,
            description=description
        )
        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_counts(
            id=id)  # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202


@app.route('/get_malfunction', methods=['POST'])
@login_required
def get_malfunction():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    title = request_body.get('title')
    if title:
        title = str(title)

    result = db_iteraction.get_malfunction(
        id=id,  # int - id  - полное совпадение
        page=page,
        title=title
    )
    return result, 200


@app.route('/malfunction', methods=['POST', 'PUT', 'DELETE'])
@login_required
def malfunction():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    title = request_body.get('title')
    if title:
        title = str(title)

    count = request_body.get('count')
    if count and type(count) != int:
        return {'success': False, 'message': "count is not integer"}, 400

    del_ids = request_body.get('del_ids')
    if del_ids and type(del_ids) != list:
        return {'success': False, 'message': "del_ids is not list"}, 400
    if del_ids:
        if not all([type(del_id) == int for del_id in del_ids]):
            return {'success': False, 'message': "del_ids has not integer"}, 400

    if request.method == 'POST':
        malfunction = db_iteraction.get_malfunction(title=title).get('data')
        if malfunction:
            db_iteraction.edit_malfunction(
                id=malfunction[0]['id'],  # int - id записи - полное совпаден
                title=title,
                count=malfunction[0]['count'] + 1
            )
        else:
            db_iteraction.add_malfunction(
                title=title,
                count=1
            )

        return {'success': True, 'message': f'{title} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_malfunction(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_malfunction(
            id=id,  # int - id записи - полное совпаден
            title=title,
            count=count
        )
        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':

        if del_ids:
            for ids in del_ids:
                db_iteraction.del_malfunction(
                    id=ids  # int - id записи - полное совпаден
                )
        else:
            db_iteraction.del_malfunction(
                id=id  # int - id записи - полное совпаден
            )
        return {'success': True, 'message': f'{id} deleted'}, 202


@app.route('/get_packagelist', methods=['POST'])
@login_required
def get_packagelist():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    title = request_body.get('title')
    if title:
        title = str(title)

    result = db_iteraction.get_packagelist(
        id=id,  # int - id  - полное совпадение
        page=page,
        title=title
    )
    return result, 200


@app.route('/packagelist', methods=['POST', 'PUT', 'DELETE'])
@login_required
def packagelist():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    title = request_body.get('title')
    if title:
        title = str(title)

    count = request_body.get('count')
    if count and type(count) != int:
        return {'success': False, 'message': "count is not integer"}, 400

    del_ids = request_body.get('del_ids')
    if del_ids and type(del_ids) != list:
        return {'success': False, 'message': "del_ids is not list"}, 400
    if del_ids:
        if not all([type(del_id) == int for del_id in del_ids]):
            return {'success': False, 'message': "del_ids has not integer"}, 400

    if request.method == 'POST':
        packagelist = db_iteraction.get_packagelist(title=title).get('data')
        if packagelist:
            db_iteraction.edit_packagelist(
                id=packagelist[0]['id'],  # int - id записи - полное совпаден
                title=title,
                count=packagelist[0]['count'] + 1
            )
        else:
            db_iteraction.add_packagelist(
                title=title,
                count=1
            )

        return {'success': True, 'message': f'{title} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_packagelist(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_packagelist(
            id=id,  # int - id записи - полное совпаден
            title=title,
            count=count
        )
        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        if del_ids:
            for ids in del_ids:
                db_iteraction.del_packagelist(
                    id=ids  # int - id записи - полное совпаден
                )
        else:
            db_iteraction.del_packagelist(
                id=id  # int - id записи - полное совпаден
            )
        return {'success': True, 'message': f'{id} deleted'}, 202


@app.route('/get_item_payments', methods=['POST'])
@login_required
def get_item_payments():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    title = request_body.get('title')
    if title:
        title = str(title)

    direction = request_body.get('direction')
    if direction and type(direction) != int:
        return {'success': False, 'message': "direction is not integer"}, 400

    result = db_iteraction.get_item_payments(
        id=id,  # int - id  - полное совпадение
        page=page,
        direction=direction
    )
    return result, 200


@app.route('/item_payments', methods=['POST', 'PUT', 'DELETE'])
@login_required
def item_payments():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    title = request_body.get('title')
    if title:
        title = str(title)

    direction = request_body.get('direction')
    if direction and type(direction) != int:
        return {'success': False, 'message': "direction is not integer"}, 400

    del_ids = request_body.get('del_ids')
    if del_ids and type(del_ids) != list:
        return {'success': False, 'message': "del_ids is not list"}, 400
    if del_ids:
        if not all([type(del_id) == int for del_id in del_ids]):
            return {'success': False, 'message': "del_ids has not integer"}, 400

    if request.method == 'POST':
        db_iteraction.add_item_payments(
            title=title,
            direction=direction
        )

        return {'success': True, 'message': f'{title} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_item_payments(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_item_payments(
            id=id,  # int - id записи - полное совпаден
            title=title,
            direction=direction
        )
        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        if del_ids:
            for ids in del_ids:
                db_iteraction.del_item_payments(
                    id=ids  # int - id записи - полное совпаден
                )
        else:
            db_iteraction.del_item_payments(
                id=id  # int - id записи - полное совпаден
            )
        return {'success': True, 'message': f'{id} deleted'}, 202


@app.route('/get_payrules', methods=['POST'])
@login_required
def get_payrules():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    title = request_body.get('title')
    if title:
        title = str(title)

    type_rule = request_body.get('type_rule')
    if type_rule and type(type_rule) != int:
        return {'success': False, 'message': "type_rule is not integer"}, 400

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    employee_id = request_body.get('employee_id')
    if employee_id and type(employee_id) != int:
        return {'success': False, 'message': "employee_id is not integer"}, 400
    if employee_id and db_iteraction.get_employee(id=employee_id)['count'] == 0:
        return {'success': False, 'message': 'employee_id is not defined'}, 400

    result = db_iteraction.get_payrules(
        id=id,  # int - id  - полное совпадение
        title=title,
        type_rule=type_rule,
        deleted=deleted,
        employee_id=employee_id
    )
    return result, 200


@app.route('/payrule', methods=['POST', 'PUT', 'DELETE'])
@login_required
def payrule():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    title = request_body.get('title')
    if title:
        title = str(title)

    type_rule = request_body.get('type_rule')
    if type_rule and type(type_rule) != int:
        return {'success': False, 'message': "type_rule is not integer"}, 400

    order_type = request_body.get('order_type')
    if order_type and type(order_type) != int:
        return {'success': False, 'message': "order_type is not integer"}, 400

    check_status = request_body.get('check_status')
    if check_status and type(check_status) != int:
        return {'success': False, 'message': "check_status is not integer"}, 400

    method = request_body.get('method')
    if method and type(method) != int:
        return {'success': False, 'message': "method is not integer"}, 400

    coefficient = request_body.get('coefficient')
    if coefficient:
        try:
            coefficient = float(coefficient)
        except:
            return {'success': False, 'message': 'coefficient is not number'}, 400

    count_coeff = request_body.get('count_coeff')

    fix_salary = request_body.get('fix_salary')
    if fix_salary and type(fix_salary) != int:
        return {'success': False, 'message': "fix_salary is not integer"}, 400

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    employee_id = request_body.get('employee_id')
    if employee_id and type(employee_id) != int:
        return {'success': False, 'message': "employee_id is not integer"}, 400
    if employee_id and db_iteraction.get_employee(id=employee_id)['count'] == 0:
        return {'success': False, 'message': 'employee_id is not defined'}, 400

    if request.method == 'POST':
        id = db_iteraction.add_payrule(
            title=title,
            type_rule=type_rule,
            order_type=order_type,
            method=method,
            coefficient=coefficient,
            count_coeff=count_coeff,
            fix_salary=fix_salary,
            deleted=deleted,
            employee_id=employee_id,
            check_status=check_status
        )

        return {'success': True, 'message': f'{id} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_payrules(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_payrule(
            id=id,  # int - id записи - полное совпаден
            title=title,
            type_rule=type_rule,
            order_type=order_type,
            method=method,
            coefficient=coefficient,
            count_coeff=count_coeff,
            fix_salary=fix_salary,
            deleted=deleted,
            employee_id=employee_id,
            check_status=check_status
        )

        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_payrule(
            id=id)  # int - id записи - полное совпаден

        return {'success': True, 'message': f'{id} deleted'}, 202


@app.route('/get_group_dict_service', methods=['POST'])
@login_required
def get_group_dict_service():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    title = request_body.get('title')
    if title:
        title = str(title)

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    result = db_iteraction.get_group_dict_service(
        id=id,  # int - id  - полное совпадение
        title=title,
        deleted=deleted
    )
    return result, 200


@app.route('/group_dict_service', methods=['POST', 'PUT', 'DELETE'])
@login_required
def group_dict_service():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    title = request_body.get('title')
    if title:
        title = str(title)

    icon = request_body.get('icon')
    if icon:
        icon = str(icon)

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    if request.method == 'POST':
        id = db_iteraction.add_group_dict_service(
            title=title,
            icon=icon,
            deleted=deleted
        )

        return {'success': True, 'message': f'{id} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_group_dict_service(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_group_dict_service(
            id=id,  # int - id записи - полное совпаден
            title=title,
            icon=icon,
            deleted=deleted
        )

        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_group_dict_service(
            id=id)  # int - id записи - полное совпаден

        return {'success': True, 'message': f'{id} deleted'}, 202


@app.route('/get_dict_service', methods=['POST'])
@login_required
def get_dict_service():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    title = request_body.get('title')
    if title:
        title = str(title)

    warranty = request_body.get('warranty')
    if warranty and type(warranty) != int:
        return {'success': False, 'message': "warranty is not integer"}, 400

    code = request_body.get('code')
    if code:
        code = str(code)

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    category_id = request_body.get('category_id')
    if category_id and type(category_id) != int:
        return {'success': False, 'message': "category_id is not integer"}, 400
    if category_id and db_iteraction.get_group_dict_service(id=category_id)['count'] == 0:
        return {'success': False, 'message': 'category_id is not defined'}, 400

    result = db_iteraction.get_dict_service(
        id=id,  # int - id  - полное совпадение
        title=title,
        warranty=warranty,
        code=code,
        deleted=deleted,
        category_id=category_id
    )
    return result, 200


@app.route('/dict_service', methods=['POST', 'PUT', 'DELETE'])
@login_required
def dict_service():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    title = request_body.get('title')
    if title:
        title = str(title)

    price = request_body.get('price')
    if price:
        try:
            price = float(price)
        except:
            return {'success': False, 'message': 'price is not number'}, 400

    cost = request_body.get('cost')
    if cost:
        try:
            cost = float(cost)
        except:
            return {'success': False, 'message': 'cost is not number'}, 400

    warranty = request_body.get('warranty')
    if warranty and type(warranty) != int:
        return {'success': False, 'message': "warranty is not integer"}, 400

    code = request_body.get('code')
    if code:
        code = str(code)

    earnings_percent = request_body.get('earnings_percent')
    if earnings_percent:
        try:
            cost = float(earnings_percent)
        except:
            return {'success': False, 'message': 'earnings_percent is not number'}, 400

    earnings_summ = request_body.get('earnings_summ')
    if earnings_summ:
        try:
            cost = float(earnings_summ)
        except:
            return {'success': False, 'message': 'earnings_summ is not number'}, 400

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    category_id = request_body.get('category_id')
    if category_id and type(category_id) != int:
        return {'success': False, 'message': "category_id is not integer"}, 400
    if category_id and db_iteraction.get_group_dict_service(id=category_id)['count'] == 0:
        return {'success': False, 'message': 'category_id is not defined'}, 400

    if request.method == 'POST':
        id = db_iteraction.add_dict_service(
            title=title,
            price=price,
            cost=cost,
            warranty=warranty,
            code=code,
            earnings_percent=earnings_percent,
            earnings_summ=earnings_summ,
            deleted=deleted,
            category_id=category_id
        )

        return {'success': True, 'message': f'{id} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_dict_service(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_dict_service(
            id=id,  # int - id записи - полное совпаден
            title=title,
            price=price,
            cost=cost,
            warranty=warranty,
            code=code,
            earnings_percent=earnings_percent,
            earnings_summ=earnings_summ,
            deleted=deleted,
            category_id=category_id
        )

        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_dict_service(
            id=id)  # int - id записи - полное совпаден

        return {'success': True, 'message': f'{id} deleted'}, 202


@app.route('/get_service_prices', methods=['POST'])
@login_required
def get_service_prices():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    discount_margin_id = request_body.get('discount_margin_id')
    if discount_margin_id and type(discount_margin_id) != int:
        return {'success': False, 'message': "discount_margin_id is not integer"}, 400
    if discount_margin_id and db_iteraction.get_discount_margin(id=discount_margin_id)['count'] == 0:
        return {'success': False, 'message': 'discount_margin_id is not defined'}, 400

    service_id = request_body.get('service_id')
    if service_id and type(service_id) != int:
        return {'success': False, 'message': "service_id is not integer"}, 400
    if service_id and db_iteraction.get_dict_service(id=service_id)['count'] == 0:
        return {'success': False, 'message': 'service_id is not defined'}, 400

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    result = db_iteraction.get_service_prices(
        id=id,  # int - id  - полное совпадение
        discount_margin_id=discount_margin_id,
        service_id=service_id,
        deleted=deleted
    )
    return result, 200


@app.route('/service_prices', methods=['POST', 'PUT', 'DELETE'])
@login_required
def service_prices():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    cost = request_body.get('cost')
    if cost and type(cost) != int:
        return {'success': False, 'message': "cost is not integer"}, 400

    discount_margin_id = request_body.get('discount_margin_id')
    if discount_margin_id and type(discount_margin_id) != int:
        return {'success': False, 'message': "discount_margin_id is not integer"}, 400
    if discount_margin_id and db_iteraction.get_discount_margin(id=discount_margin_id)['count'] == 0:
        return {'success': False, 'message': 'discount_margin_id is not defined'}, 400

    service_id = request_body.get('service_id')
    if service_id and type(service_id) != int:
        return {'success': False, 'message': "service_id is not integer"}, 400
    if service_id and db_iteraction.get_dict_service(id=service_id)['count'] == 0:
        return {'success': False, 'message': 'service_id is not defined'}, 400

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    if request.method == 'POST':
        # Проверим сущестует ли запись по данному id
        if id:
            if db_iteraction.get_service_prices(id=id)['count'] == 0:
                return {'success': False, 'message': 'id is not defined'}, 400
            db_iteraction.edit_service_prices(
                id=id,  # int - id записи - полное совпаден
                cost=cost,
                discount_margin_id=discount_margin_id,
                service_id=service_id,
                deleted=deleted
            )

            return {'success': True, 'message': f'{id} changed'}, 202
        else:
            id = db_iteraction.add_service_prices(
                cost=cost,
                discount_margin_id=discount_margin_id,
                service_id=service_id,
                deleted=False
            )

            return {'success': True, 'message': f'{id} added'}, 201

    if db_iteraction.get_service_prices(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_service_prices(
            id=id,  # int - id записи - полное совпаден
            cost=cost,
            discount_margin_id=discount_margin_id,
            service_id=service_id,
            deleted=deleted
        )
        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_service_prices(
            id=id)  # int - id записи - полное совпаден

        return {'success': True, 'message': f'{id} deleted'}, 202


@app.route('/get_parts', methods=['POST'])
@login_required
def get_parts():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    title = request_body.get('title')
    if title:
        title = str(title)

    marking = request_body.get('marking')
    if marking:
        marking = str(marking)

    article = request_body.get('article')
    if article:
        article = str(article)

    barcode = request_body.get('barcode')
    if barcode:
        barcode = str(barcode)

    code = request_body.get('code')
    if code:
        code = str(code)

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    warehouse_category_id = request_body.get('warehouse_category_id')
    if warehouse_category_id and type(warehouse_category_id) != int:
        return {'success': False, 'message': "warehouse_category_id is not integer"}, 400
    if warehouse_category_id and db_iteraction.get_warehouse_category(id=warehouse_category_id)['count'] == 0:
        return {'success': False, 'message': 'warehouse_category_id is not defined'}, 400

    result = db_iteraction.get_parts(
        id=id,  # int - id  - полное совпадение
        title=title,
        marking=marking,
        article=article,
        barcode=barcode,
        code=code,
        deleted=deleted,
        warehouse_category_id=warehouse_category_id,
        page=page
    )
    return result, 200


@app.route('/parts', methods=['POST', 'PUT', 'DELETE'])
@login_required
def parts():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    title = request_body.get('title')
    if title:
        title = str(title)

    description = request_body.get('description')
    if description:
        description = str(description)

    marking = request_body.get('marking')
    if marking:
        marking = str(marking)

    article = request_body.get('article')
    if article:
        article = str(article)

    barcode = request_body.get('barcode')
    if barcode:
        barcode = str(barcode)

    code = request_body.get('code')
    if code:
        code = str(code)

    image_url = request_body.get('image_url')
    if image_url:
        image_url = str(image_url)

    doc_url = request_body.get('doc_url')
    if doc_url:
        doc_url = str(doc_url)

    specifications = request_body.get('specifications')

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    warehouse_category_id = request_body.get('warehouse_category_id')
    if warehouse_category_id and type(warehouse_category_id) != int:
        return {'success': False, 'message': "warehouse_category_id is not integer"}, 400
    if warehouse_category_id and db_iteraction.get_warehouse_category(id=warehouse_category_id)['count'] == 0:
        return {'success': False, 'message': 'warehouse_category_id is not defined'}, 400

    # загрузка/замена изображения
    img_uri = request_body.get('img')
    if img_uri:
        # открываем файл с помощью urlopen
        with urlopen(img_uri) as response:
            # читаем данные файла в переменную data
            data = response.read()
        # определяем место для хранения данного файла и его имя
        url = f'build/static/data/Parts/part_{title}_{id}.jpeg'
        # сохраняем файл по дному адресу
        with open(url, 'wb') as f:
            f.write(data)
        # создаем ссылку для для занесения ее в БД
        image_url = f'data/Parts/part_{title}_{id}.jpeg'

        # загрузка/замена PDF
    doc_uri = request_body.get('doc')
    if doc_uri:
        # открываем файл с помощью urlopen
        with urlopen(doc_uri) as response:
            # читаем данные файла в переменную data
            data = response.read()
        # определяем место для хранения данного файла и его имя
        url = f'build/static/data/Datasheets/datasheet_{title}_{id}.pdf'
        # сохраняем файл по дному адресу
        with open(url, 'wb') as f:
            f.write(data)
        # создаем ссылку для для занесения ее в БД
        doc_url = f'data/Datasheets/datasheet_{title}_{id}.pdf'

    if request.method == 'POST':
        id = db_iteraction.add_parts(
            title=title,
            description=description,
            marking=marking,
            article=article,
            barcode=barcode,
            code=code,
            image_url=image_url,
            doc_url=doc_url,
            specifications=specifications,
            deleted=deleted,
            warehouse_category_id=warehouse_category_id
        )

        return {'success': True, 'message': f'{id} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_parts(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_parts(
            id=id,  # int - id записи - полное совпаден
            title=title,
            description=description,
            marking=marking,
            article=article,
            barcode=barcode,
            code=code,
            image_url=image_url,
            doc_url=doc_url,
            specifications=specifications,
            deleted=deleted,
            warehouse_category_id=warehouse_category_id
        )

        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_parts(
            id=id)  # int - id записи - полное совпаден

        return {'success': True, 'message': f'{id} deleted'}, 202


@app.route('/get_warehouse', methods=['POST'])
@login_required
def get_warehouse():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    title = request_body.get('title')
    if title:
        title = str(title)

    branch_id = request_body.get('branch_id')
    if branch_id and type(branch_id) != int:
        return {'success': False, 'message': "branch_id is not integer"}, 400
    if branch_id and db_iteraction.get_branch(id=branch_id)['count'] == 0:
        return {'success': False, 'message': 'branch_id is not defined'}, 400

    isGlobal = request_body.get('isGlobal')
    if isGlobal and type(isGlobal) != bool:
        return {'success': False, 'message': 'isGlobal is not boolean'}, 400

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    result = db_iteraction.get_warehouse(
        id=id,  # int - id  - полное совпадение
        title=title,
        branch_id=branch_id,
        isGlobal=isGlobal,
        deleted=deleted,
        page=page
    )
    return result, 200


@app.route('/warehouse', methods=['POST', 'PUT', 'DELETE'])
@login_required
def warehouse():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    title = request_body.get('title')
    if title:
        title = str(title)

    description = request_body.get('description')
    if description:
        description = str(description)

    branch_id = request_body.get('branch_id')
    if branch_id and type(branch_id) != int:
        return {'success': False, 'message': "branch_id is not integer"}, 400
    if branch_id and db_iteraction.get_branch(id=branch_id)['count'] == 0:
        return {'success': False, 'message': 'branch_id is not defined'}, 400

    permissions = request_body.get('permissions')
    if permissions and type(permissions) != list:
        return {'success': False, 'message': "permissions is not list"}, 400
    if permissions:
        if not all([type(permission) == str for permission in permissions]):
            return {'success': False, 'message': "permissions has not string"}, 400

    employees = request_body.get('employees')

    isGlobal = request_body.get('isGlobal')
    if isGlobal and type(isGlobal) != bool:
        return {'success': False, 'message': 'isGlobal is not boolean'}, 400

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    if request.method == 'POST':
        id = db_iteraction.add_warehouse(
            title=title,
            description=description,
            isGlobal=isGlobal,
            permissions=permissions,
            employees=employees,
            branch_id=branch_id,
            deleted=deleted
        )

        return {'success': True, 'message': f'{id} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_warehouse(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_warehouse(
            id=id,  # int - id записи - полное совпаден
            title=title,
            description=description,
            isGlobal=isGlobal,
            permissions=permissions,
            employees=employees,
            branch_id=branch_id,
            deleted=deleted
        )

        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_warehouse(
            id=id)  # int - id записи - полное совпаден

        return {'success': True, 'message': f'{id} deleted'}, 202


@app.route('/get_warehouse_category', methods=['POST'])
@login_required
def get_warehouse_category():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    title = request_body.get('title')
    if title:
        title = str(title)

    parent_category_id = request_body.get('parent_category_id')
    if parent_category_id and type(parent_category_id) != int:
        return {'success': False, 'message': "parent_category_id is not integer"}, 400
    if parent_category_id and db_iteraction.get_warehouse_category(id=parent_category_id)['count'] == 0:
        return {'success': False, 'message': 'parent_category_id is not defined'}, 400

    warehouse_id = request_body.get('warehouse_id')
    if warehouse_id and type(warehouse_id) != int:
        return {'success': False, 'message': "warehouse_id is not integer"}, 400
    if warehouse_id and db_iteraction.get_warehouse(id=warehouse_id)['count'] == 0:
        return {'success': False, 'message': 'warehouse_id is not defined'}, 400

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    result = db_iteraction.get_warehouse_category(
        id=id,  # int - id  - полное совпадение
        title=title,
        parent_category_id=parent_category_id,
        warehouse_id=warehouse_id,
        deleted=deleted,
        page=page
    )

    # рекурсивная функция которя возвращает список категорий используя текущюю категория и общий список категрий
    def getcat(cat, categories):
        list_cat = list(filter(lambda x: x['parent_category_id'] == cat['id'], categories))
        if list_cat:
            for catn in list_cat:
                catn['categories'] = getcat(catn, categories)
        return list_cat

    categories = db_iteraction.get_warehouse_category(deleted=deleted)['data']
    for cat in result['data']:
        cat['categories'] = getcat(cat, categories)

    return result, 200


@app.route('/warehouse_category', methods=['POST', 'PUT', 'DELETE'])
@login_required
def warehouse_category():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    title = request_body.get('title')
    if title:
        title = str(title)

    parent_category_id = request_body.get('parent_category_id')
    if parent_category_id and type(parent_category_id) != int:
        return {'success': False, 'message': "parent_category_id is not integer"}, 400
    if parent_category_id and db_iteraction.get_warehouse_category(id=parent_category_id)['count'] == 0:
        return {'success': False, 'message': 'parent_category_id is not defined'}, 400

    warehouse_id = request_body.get('warehouse_id')
    if warehouse_id and type(warehouse_id) != int:
        return {'success': False, 'message': "warehouse_id is not integer"}, 400
    if warehouse_id and db_iteraction.get_warehouse(id=warehouse_id)['count'] == 0:
        return {'success': False, 'message': 'warehouse_id is not defined'}, 400

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    if request.method == 'POST':
        id = db_iteraction.add_warehouse_category(
            title=title,
            parent_category_id=parent_category_id,
            warehouse_id=warehouse_id,
            deleted=deleted
        )

        return {'success': True, 'message': f'{id} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_warehouse_category(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_warehouse_category(
            id=id,  # int - id записи - полное совпаден
            title=title,
            parent_category_id=parent_category_id,
            warehouse_id=warehouse_id,
            deleted=deleted
        )

        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_warehouse_category(
            id=id)  # int - id записи - полное совпаден

        return {'success': True, 'message': f'{id} deleted'}, 202


@app.route('/get_warehouse_parts', methods=['POST'])
@login_required
def get_warehouse_parts():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    cell = request_body.get('cell')
    if cell:
        cell = str(cell)

    title = request_body.get('title')
    if title:
        title = str(title)

    marking = request_body.get('marking')
    if marking:
        marking = str(marking)

    count = request_body.get('count')
    if count and type(count) != int:
        return {'success': False, 'message': "count is not integer"}, 400

    min_residue = request_body.get('min_residue')
    if min_residue and type(min_residue) != int:
        return {'success': False, 'message': "min_residue is not integer"}, 400

    part_id = request_body.get('part_id')
    if part_id and type(part_id) != int:
        return {'success': False, 'message': "part_id is not integer"}, 400
    if part_id and db_iteraction.get_parts(id=part_id)['count'] == 0:
        return {'success': False, 'message': 'part_id is not defined'}, 400

    category_id = request_body.get('category_id')
    if category_id and type(category_id) != int:
        return {'success': False, 'message': "category_id is not integer"}, 400
    if category_id and db_iteraction.get_warehouse_category(id=category_id)['count'] == 0:
        return {'success': False, 'message': 'category_id is not defined'}, 400

    warehouse_id = request_body.get('warehouse_id')
    if warehouse_id and type(warehouse_id) != int:
        return {'success': False, 'message': "warehouse_id is not integer"}, 400
    if warehouse_id and db_iteraction.get_warehouse(id=warehouse_id)['count'] == 0:
        return {'success': False, 'message': 'warehouse_id is not defined'}, 400

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    result = db_iteraction.get_warehouse_parts(
        id=id,  # int - id  - полное совпадение
        cell=cell,
        title=title,
        marking=marking,
        count=count,
        min_residue=min_residue,
        part_id=part_id,
        category_id=category_id,
        warehouse_id=warehouse_id,
        deleted=deleted,
        page=page
    )
    return result, 200


@app.route('/warehouse_parts', methods=['POST', 'PUT', 'DELETE'])
@login_required
def warehouse_parts():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    where_to_buy = request_body.get('where_to_buy')
    if where_to_buy:
        where_to_buy = str(where_to_buy)

    cell = request_body.get('cell')
    if cell:
        cell = str(cell)

    count = request_body.get('count')
    if count and type(count) != int:
        return {'success': False, 'message': "count is not integer"}, 400

    min_residue = request_body.get('min_residue')
    if min_residue and type(min_residue) != int:
        return {'success': False, 'message': "min_residue is not integer"}, 400

    warranty_period = request_body.get('warranty_period')
    if warranty_period and type(warranty_period) != int:
        return {'success': False, 'message': "warranty_period is not integer"}, 400

    necessary_amount = request_body.get('necessary_amount')
    if necessary_amount and type(necessary_amount) != int:
        return {'success': False, 'message': "necessary_amount is not integer"}, 400

    part_id = request_body.get('part_id')
    if part_id and type(part_id) != int:
        return {'success': False, 'message': "part_id is not integer"}, 400
    if part_id and part_id.get_parts(id=part_id)['count'] == 0:
        return {'success': False, 'message': 'part_id is not defined'}, 400

    category_id = request_body.get('category_id')
    if category_id and type(category_id) != int:
        return {'success': False, 'message': "category_id is not integer"}, 400
    if category_id and db_iteraction.get_warehouse_category(id=category_id)['count'] == 0:
        return {'success': False, 'message': 'category_id is not defined'}, 400

    warehouse_id = request_body.get('warehouse_id')
    if warehouse_id and type(warehouse_id) != int:
        return {'success': False, 'message': "warehouse_id is not integer"}, 400
    if warehouse_id and db_iteraction.get_warehouse(id=warehouse_id)['count'] == 0:
        return {'success': False, 'message': 'warehouse_id is not defined'}, 400

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    if request.method == 'POST':
        id = db_iteraction.add_warehouse_parts(
            where_to_buy=where_to_buy,
            cell=cell,
            count=count,
            min_residue=min_residue,
            warranty_period=warranty_period,
            necessary_amount=necessary_amount,
            part_id=part_id,
            category_id=category_id,
            warehouse_id=warehouse_id,
            deleted=deleted
        )

        return {'success': True, 'message': f'{id} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_warehouse_parts(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_warehouse_parts(
            id=id,  # int - id записи - полное совпаден
            where_to_buy=where_to_buy,
            cell=cell,
            count=count,
            min_residue=min_residue,
            warranty_period=warranty_period,
            necessary_amount=necessary_amount,
            part_id=part_id,
            category_id=category_id,
            warehouse_id=warehouse_id,
            deleted=deleted
        )

        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_warehouse_parts(
            id=id)  # int - id записи - полное совпаден

        return {'success': True, 'message': f'{id} deleted'}, 202


@app.route('/get_notification_template', methods=['POST'])
@login_required
def get_notification_template():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    title = request_body.get('title')
    if title:
        title = str(title)

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    result = db_iteraction.get_notification_template(
        id=id,  # int - id  - полное совпадение
        title=title,
        deleted=deleted,
        page=page
    )
    return result, 200


@app.route('/notification_template', methods=['POST', 'PUT', 'DELETE'])
@login_required
def notification_template():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    title = request_body.get('title')
    if title:
        title = str(title)

    template = request_body.get('template')
    if template:
        template = str(template)

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    if request.method == 'POST':
        id = db_iteraction.add_notification_template(
            title=title,
            template=template,
            deleted=deleted
        )

        return {'success': True, 'message': f'{id} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_notification_template(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_notification_template(
            id=id,  # int - id записи - полное совпаден
            title=title,
            template=template,
            deleted=deleted
        )

        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_notification_template(
            id=id)  # int - id записи - полное совпаден

        return {'success': True, 'message': f'{id} deleted'}, 202


@app.route('/get_notification_events', methods=['POST'])
@login_required
def get_notification_events():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    target_audience = request_body.get('target_audience')
    if target_audience and type(target_audience) != int:
        return {'success': False, 'message': "target_audience is not integer"}, 400

    notification_type = request_body.get('notification_type', 0)
    if notification_type and type(notification_type) != int:
        return {'success': False, 'message': "notification_type is not integer"}, 400

    event = request_body.get('event')
    if event:
        event = str(event)

    notification_template_id = request_body.get('notification_template_id')
    if notification_template_id and type(notification_template_id) != int:
        return {'success': False, 'message': "notification_template_id is not integer"}, 400
    if notification_template_id and db_iteraction.get_notification_template(id=notification_template_id)['count'] == 0:
        return {'success': False, 'message': 'notification_template_id is not defined'}, 400

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    result = db_iteraction.get_notification_events(
        id=id,  # int - id  - полное совпадение
        event=event,
        target_audience=target_audience,
        notification_template_id=notification_template_id,
        notification_type=notification_type,
        deleted=deleted,
        page=page
    )
    return result, 200


@app.route('/notification_events', methods=['POST', 'PUT', 'DELETE'])
@login_required
def notification_events():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    event = request_body.get('event')
    if event:
        event = str(event)

    target_audience = request_body.get('target_audience')
    if target_audience and type(target_audience) != int:
        return {'success': False, 'message': "target_audience is not integer"}, 400

    notification_type = request_body.get('notification_type', 0)
    if notification_type and type(notification_type) != int:
        return {'success': False, 'message': "notification_type is not integer"}, 400

    statuses = request_body.get('statuses')
    if statuses and type(statuses) != list:
        return {'success': False, 'message': "statuses is not list"}, 400
    if statuses:
        if not all([type(status) == int for status in statuses]):
            return {'success': False, 'message': "statuses has not integer"}, 400

    notification_template_id = request_body.get('notification_template_id')
    if notification_template_id and type(notification_template_id) != int:
        return {'success': False, 'message': "notification_template_id is not integer"}, 400
    if notification_template_id and db_iteraction.get_notification_template(id=notification_template_id)['count'] == 0:
        return {'success': False, 'message': 'notification_template_id is not defined'}, 400

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    if request.method == 'POST':
        id = db_iteraction.add_notification_events(
            event=event,
            target_audience=target_audience,
            statuses=statuses,
            notification_type=notification_type,
            notification_template_id=notification_template_id,
            deleted=deleted
        )

        return {'success': True, 'message': f'{id} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_notification_events(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_notification_events(
            id=id,  # int - id записи - полное совпаден
            event=event,
            target_audience=target_audience,
            statuses=statuses,
            notification_type=notification_type,
            notification_template_id=notification_template_id,
            deleted=deleted
        )

        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_notification_events(
            id=id)  # int - id записи - полное совпаден

        return {'success': True, 'message': f'{id} deleted'}, 202


app.add_url_rule('/shutdown', view_func=shutdown)
app.register_error_handler(404, page_not_found)

# app.add_url_rule('/login', view_func=login, methods=['POST'])





run_server()
# app.run(debug=True)


'''
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, dest='config')

    args = parser.parse_args()

    # print(args)
    # print(config_parser('app/api/config.txt'))

    config = config_parser('app/api/config.txt')

    server_host = config['SERVER_HOST']
    server_port = config['SERVER_PORT']

    db_host = config['DB_HOST']
    db_port = config['DB_PORT']
    user = config['DB_USER']
    password = config['DB_PASSWORD']
    db_name = config['DB_NAME']



    server = Server(
        host=server_host,
        port=server_port,
        db_host=db_host,
        db_port=db_port,
        user=user,
        password=password,
        db_name=db_name
    )
    server.run_server()
    # server.app.run()
'''
