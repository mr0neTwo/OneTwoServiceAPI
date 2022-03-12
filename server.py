from datetime import timedelta
from pprint import pprint
import time
import os
# from base64 import b64decode
from urllib.request import urlopen


from flask import Flask, request, jsonify, render_template, make_response, send_from_directory
from flask_cors import CORS, cross_origin
# from flask_login import LoginManager, login_manager, login_user, login_required, logout_user, current_user

import threading
from flask_jwt_extended import create_access_token, decode_token
from flask_jwt_extended import JWTManager, jwt_required
# from flask_session import Session

from werkzeug.security import generate_password_hash, check_password_hash

from app.API_requests.operations import operation_api
from app.db.interaction.db_iteraction import db_iteraction, config
from app.events import event_change_status_to, event_create_order


import ssl
# pip freeze > requirements.txt


host = config['SERVER_HOST']
port = config['SERVER_PORT']

print_logs = False




# context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
# context.load_cert_chain("server.crt", "server.key")


app = Flask(__name__, static_folder="build/static", template_folder="build")
app.register_blueprint(operation_api)


jwt = JWTManager(app)

app.config['SECRET_KEY'] = '07446af7da2e08c395ac7d7a65c2d1e85b7610bbab79'
# app.permanent_session_lifetime = timedelta(days=1)
# app.config.update(
#     FLASK_ENV = 'development',
#     # SESSION_TYPE = 'redis',
#     SESSION_COOKIE_SAMESITE = "Strict",
#     PERMANENT_SESSION_LIFETIME = 86400,
#     SECRET_KEY = '07446af7da2e08c395ac7d7a65c2d1e85b7610bbab79')

# sess = Session()
# sess.init_app(app)


CORS(app, supports_credentials=True)
# cors = CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
cors = CORS(app, resources={r"/*": {"origins": "*"}})
# cors = CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5000"}})
# logging.getLogger('flask_cors').level = logging.DEBUG


@app.after_request
def after_request(response):
  response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin'))
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
  response.headers.add('Access-Control-Allow-Credentials', 'true')
  return response


def page_not_found(err_description):
    return jsonify(error=str(err_description)), 404


def run_server():
    # server = threading.Thread(target=app.run, kwargs={'host': host, 'port': port})
    # server.start()
    app.run(
        debug=False,
        host=host,
        port=port,
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



@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return render_template('index.html')

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

@app.route('/login')
def login():
    request_body = dict(request.json)
    if request.method == 'POST':
        user = db_iteraction.get_employee(email=request_body['email'])['data'][0] if db_iteraction.get_employee(email=request_body['email'])['data'] else None
        if user:
            if check_password_hash(user['password'], request_body['password']):
                expire_delta = timedelta(hours=12)
                token = create_access_token(identity=user['id'], expires_delta=expire_delta)

                response = make_response({'success': True, 'access_token': token, 'user': user}, 200)
                response.headers['Content-Type'] = 'application/json'
                return response
            return {'success': False, 'message': 'Неверный пароль пользователя'}, 400
        return {'success': False, 'message': 'Пользователь не найден'}, 400


@app.route('/get_ad_campaign', methods=['POST'])
@jwt_required()
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
        id=id,              # int - id рекламной компании - полное совпадение
        name=name           # str - Имя рекламной компании - частичное совпадение
    )
    return result, 200

@app.route('/ad_campaign', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
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
            name=name           # str - Название рекламной компании - обязательное поле
        )
        return {'success': True, 'message': f'{name} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_adCampaign(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_adCampaign(
            id=id,                  # int - id записи - полное совпаден
            name=name,              # str - Новое название рекламной компании
        )
        return {'success': True, 'message': f'{name} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_adCampaign(
            id=id)                        # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202

@app.route('/get_employee', methods=['POST'])
@jwt_required()
def get_employee():
    token = request.headers['Authorization'][7:]
    user_id = decode_token(token)['sub']
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

    first_name = request_body.get('first_name')
    if first_name:
        first_name = str(first_name)

    last_name = request_body.get('last_name')
    if last_name:
        last_name = str(last_name)

    email = request_body.get('email')
    if email:
        email = str(email)

    phone = request_body.get('phone')
    if phone:
        phone = str(phone)

    notes = request_body.get('notes')
    if notes:
        notes = str(notes)

    post = request_body.get('post')
    if post:
        post = str(post)

    deleted = request_body.get('deleted', False)
    if deleted:
        deleted = bool(deleted)

    role_id = request_body.get('role_id')
    if role_id and type(role_id) != int:
        return {'success': False, 'message': "role_id is not integer"}, 400


    login = request_body.get('login')
    if login:
        login = str(login)

    result = db_iteraction.get_employee(
        id=id,                               # int - id сотрудника - полное совпадение
        first_name=first_name,               # str - Имя сотрудника - частичное совпадение
        last_name=last_name,                 # str - Фамилия сотрудника - частичное совпадение
        email=email,                         # str - Электронная почта сотрудника - частичное совпадение
        phone=phone,                         # str - Телефон сотрудника - частичное совпадение
        notes=notes,                         # str - Заметки о сотруднике - частичное совпадение
        post=post,
        deleted=deleted,                     # bool - Статус удален сотрудника
        role_id=role_id,                     # str - Роль сотрудника - частичное совпадение
        login=login,                         # str - Логин
        page=page                            # int - Старница погинации

    )
    return result, 200

@app.route('/employee', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
def employee():
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

    first_name = request_body.get('first_name')
    if first_name:
        first_name = str(first_name)

    last_name = request_body.get('last_name')
    if last_name:
        last_name = str(last_name)

    email = request_body.get('email')
    if email:
        email = str(email)

    login = request_body.get('login')
    if login:
        login = str(login)

    phone = request_body.get('phone')
    if phone:
        phone = str(phone)

    notes = request_body.get('notes')
    if notes:
        notes = str(notes)

    inn = request_body.get('inn')
    if inn:
        inn = str(inn)

    doc_name = request_body.get('doc_name')
    if doc_name:
        doc_name = str(doc_name)

    post = request_body.get('post')
    if post:
        post = str(post)

    deleted = request_body.get('deleted', False)
    if deleted:
        deleted = bool(deleted)

    permissions = request_body.get('permissions')
    if permissions and type(permissions) != list:
        return {'success': False, 'message': "permissions is not list"}, 400
    if permissions:
        if not all([type(permission) == str for permission in permissions]):
            return {'success': False, 'message': "permissions has not string"}, 400

    role_id = request_body.get('role_id')
    if role_id and type(role_id) != int:
        return {'success': False, 'message': "role_id is not integer"}, 400

    password = request_body.get('password')
    if password:
        password = str(password)

    if request.method == 'POST':

        if not email:
            return {'success': False, 'message': 'email required'}, 400
        if db_iteraction.get_employee(email=email)['data']:
            return {'success': False, 'message': 'there is the same email'}, 400

        if not login:
            return {'success': False, 'message': 'login required'}, 400
        if db_iteraction.get_employee(login=login)['data']:
            return {'success': False, 'message': 'there is the same login'}, 400

        if not password:
            return {'success': False, 'message': 'Password required'}, 400

        if len(password) < 4:
            return {'success': False, 'message': 'password is short'}, 400


        db_iteraction.add_employee(
            first_name=first_name,                              # str - Имя сотрудника
            last_name=last_name,                                # str - Фамилия сотрудника
            email=email,                                        # str - Электронная почта сотрудника - уникальное значение
            phone=phone,                                        # str - Телфон сотрудника
            notes=notes,                                        # str - Заметки
            deleted=deleted,                                    # bool - Статус удален
            inn=inn,
            doc_name=doc_name,
            post=post,
            permissions=permissions,
            role_id=role_id,                                    # str - Роль сотрудника
            login=login,                                        # str - Логин сотрудника - уникальное значение
            password=generate_password_hash(password)           # str - Пароль сотрудника - обязательное поле,
        )
        return {'success': True, 'message': f'{first_name} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_employee(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':

        # if not email:
        #     return {'success': False, 'message': 'email required'}, 400
        if email and db_iteraction.get_employee(id=id)['data'][0]['email'] != email:
            if db_iteraction.get_employee(email=email)['data']:
                return {'success': False, 'message': 'there is the same email'}, 400

        # if not login:
        #     return {'success': False, 'message': 'login required'}, 400
        if login and db_iteraction.get_employee(id=id)['data'][0]['login'] != login:
            if db_iteraction.get_employee(login=login)['data']:
                return {'success': False, 'message': 'there is the same login'}, 400


        db_iteraction.edit_employee(
            id=id,                                      # int - ID сотрудника -  полное совпадение
            first_name=first_name,                      # str - Новое имя сотрудника
            last_name=last_name,                        # str - Новая фамилия сотрудника
            email=email,                                # str - Новый email сотрудника
            phone=phone,                                # str - Новый телефон сотрудника
            notes=notes,                                # str - Новый коментарий к сотруднику
            deleted=deleted,                            # str - Статус удален сотрудника
            inn=inn,
            doc_name=doc_name,
            post=post,
            login=login,                                # str - Новый логин
            role_id=role_id,                            # str - Новая роль сотрудника
            permissions=permissions
            # password=generate_password_hash(password)   # str - Пароль сотрудника - обязательное поле,
        )
        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_employee(id=id)                         # int - id сотрудника - полное совпадение
        return {'success': True, 'message': f'{id} deleted'}, 202

@app.route('/change_userpassword', methods=['PUT'])
@jwt_required()
def change_userpassword():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    # Проверим является ли id числом
    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_employee(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    password = request_body.get('password')
    if not password:
        return {'success': False, 'message': 'password required'}, 400

    password = str(password)

    if len(password) < 6:
        return {'success': False, 'message': 'password is short'}, 400

    if request.method == 'PUT':

        db_iteraction.cange_userpassword(
            id=id,
            password=generate_password_hash(password)
        )
        return {'success': True, 'message': f'{request_body.get("id")} changed'}, 202

@app.route('/get_table_headers', methods=['POST'])
@jwt_required()
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
        id=id,                            # int - id поля - полное совпадение
        title=title,                        # [str, ...str] - текст поля - полное совпадение
        field=field,                         # [str, ...str] - имя поля - полное совпадение
        employee_id=employee_id,            # int - id инженера, которому пренадлежит поле - полное совпадение
        visible=visible                     # bool - статус отображения - - полное совпадение
    )
    return result, 200

@app.route('/table_headers', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
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
            title=title,                # str - Текст поля - обязательное поле
            field=field,                # str - Имя поля - обязательное поле
            width=width,                # str - Ширина поля - обязательное поле
            employee_id=employee_id,    # int - id сотрудника - обязательное поле
            visible=visible             # bool - Статус отображения
        )
        return {'success': True, 'message': f'{title} added'}, 201

    if request.method == 'PUT':
        db_iteraction.edit_table_headers(
            id=id,                          # int - id записи - полное совпаден
            title=title,                    # str - Текст поля
            field=field,                    # str - Имя поля
            width=width,                    # str - Ширина поля
            employee_id=employee_id,        # int - id сотрудника
            visible=visible                 # bool - Статус отображения
        )
        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_table_headers(
            id=id)           # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202

@app.route('/get_attachments', methods=['POST'])
@jwt_required()
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
        id=id,                                  # int - ID записи о вложении -  полное совпадение
        created_by_id=created_by_id,            # int - ID сотрудника - полное совпадение
        created_at=created_at,                  # array - Из двах дат в timestamp - диапазон выбоки по времени
        filename=filename,                      # str - Имя файла - частичное совподение
        page=page                               # Номер страницы для вывода пагинацией
    )
    return result, 200

@app.route('/attachments', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
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
            created_by_id=created_by_id,            # int - ID сотрудника
            created_at=created_at,                  # int (timestamp) - Дата создания, по дефолту now
            filename=filename,                      # str - Имя файла
            url=url,                                # str - Путь к файлу
        )
        return {'success': True, 'message': f"{request_body.get('filename')} added"}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_attachments(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':

        db_iteraction.edit_attachments(
            id=id,                                  # int - id записи - полное совпадение
            created_by_id=created_by_id,            # int - Новый id инженера
            created_at=created_at,                  # int - Ноывая дата создания
            filename=filename,                      # str - Новое имя файла
            url=url,                                # str - Новый путь к файлу
        )
        return {'success': True, 'message': f"{id} changed"}, 202

    if request.method == 'DELETE':
        db_iteraction.del_attachments(id=id)                    # int - id записи - полное совпадение
        return {'success': True, 'message': f"{id} deleted"}, 202

@app.route('/get_branch', methods=['POST'])
@jwt_required()
def get_branch():
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

    deleted = request_body.get('deleted')

    result = db_iteraction.get_branch(
        id=id,                            # int - id филиала - полное совпадение
        name=name,                        # str - Имя филиала - частичное совпадение
        deleted=deleted,
        page=page                         # int - Старница погинации
    )
    return result, 200

@app.route('/branch', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
def branch():
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

    color = request_body.get('color')
    if color:
        color = str(color)

    address = request_body.get('address')
    if address:
        address = str(address)

    phone = request_body.get('phone')
    if phone:
        phone = str(phone)

    icon = request_body.get('icon')
    if icon:
        icon = str(icon)

    orders_type_id = request_body.get('orders_type_id')
    if orders_type_id and type(orders_type_id) != int:
        return {'success': False, 'message': "orders_type_id is not integer"}, 400

    orders_type_strategy = request_body.get('orders_type_strategy')
    if orders_type_strategy:
        orders_type_strategy = str(orders_type_strategy)

    orders_prefix = request_body.get('orders_prefix')
    if orders_prefix:
        orders_prefix = str(orders_prefix)

    documents_prefix = request_body.get('documents_prefix')
    if documents_prefix:
        documents_prefix = str(documents_prefix)

    employees = request_body.get('employees')
    if employees and type(employees) != list:
        return {'success': False, 'message': "employees is not list"}, 400
    if employees:
        if not all([type(employee) == int for employee in employees]):
            return {'success': False, 'message': "employees has not integer"}, 400

    deleted = request_body.get('deleted')

    schedule = request_body.get('schedule')

    if request.method == 'POST':

        if not name:
            return {'success': False, 'message': 'name required'}, 400

        branch_id = db_iteraction.add_branch(
            name=name,                          # str - Название филиала - обязательное поле
            color=color,
            address=address,
            phone=phone,
            icon=icon,
            orders_type_id=orders_type_id,
            orders_type_strategy=orders_type_strategy,
            orders_prefix=orders_prefix,
            documents_prefix=documents_prefix,
            employees=employees,
            deleted=deleted
            )
        for day in schedule:
            db_iteraction.add_schedule(
                start_time=day['start_time'],
                end_time=day['end_time'],
                work_day=day['work_day'],
                week_day=day['week_day'],
                branch_id=branch_id
            )
        return {'success': True, 'message': f'{name} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_branch(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_branch(
            id=id,                    # int - id записи - полное совпаден
            name=name,                # str - Новое название филиала
            color=color,
            address=address,
            phone=phone,
            icon=icon,
            orders_type_id=orders_type_id,
            orders_type_strategy=orders_type_strategy,
            orders_prefix=orders_prefix,
            documents_prefix=documents_prefix,
            employees=employees,
            deleted=deleted
        )
        if schedule:
            for day in schedule:
                db_iteraction.edit_schedule(
                    id=day['id'],
                    start_time=day['start_time'],
                    end_time=day['end_time'],
                    work_day=day['work_day'],
                    week_day=day['week_day'],
                    branch_id=day['branch_id']
                )
        return {'success': True, 'message': f'{name} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_branch(
            id=id)           # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202

@app.route('/get_discount_margin', methods=['POST'])
@jwt_required()
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
        id=id,                                  # int - id наценки - полное совпадение
        title=title,                            # str - Имя наценки - частичное совпадение
        margin_type=margin_type,
        deleted=deleted,
        page=page                               # int - Старница погинации
    )
    return result, 200

@app.route('/discount_margin', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
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
            title=title,                            # str - Название наценки - обязательное поле
            margin=margin,                           # float - Значение наценки - обязательное полу
            margin_type=margin_type,
            deleted=deleted
        )
        return {'success': True, 'message': f'{title} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_discount_margin(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':

        db_iteraction.edit_discount_margin(
            id=id,                                              # int - id записи - полное совпаден
            title=title,            # str - Новое название наценки
            margin=margin,                               # str - Новое значение наценки
            margin_type=margin_type,
            deleted=deleted
        )
        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_discount_margin(
            id=id)                          # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202

@app.route('/get_order_type', methods=['POST'])
@jwt_required()
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
        id=id,                              # int - id типа - полное совпадение
        name=name,                          # str - Имя типа - частичное совпадение
        page=page                           # int - Старница погинации
    )
    return result, 200

@app.route('/order_type', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
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
            name=name                    # str - Название типа - обязательное поле
        )
        return {'success': True, 'message': f'{name} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_order_type(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_order_type(
            id=id,                                              # int - id записи - полное совпаден
            name=name,              # str - Новое название типа
        )
        return {'success': True, 'message': f'{name} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_order_type(
            id=id)                          # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202

@app.route('/get_status_group', methods=['POST'])
@jwt_required()
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
        id=id,                              # int - id группы статусов - полное совпадение
        name=name,                          # str - Имя группы статуов - частичное совпадение
        type_group=type_group,              # int - Номер группы - полное совпадение
        page=page                           # int - Старница погинации
    )
    return result, 200

@app.route('/status_group', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
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
            name=name,                                     # str - Имя группы статуов - обязательное поле
            type_group=type_group,                         # int - Номер группы - обязательное поле
            color=color                                    # str - цвет группы
        )
        return {'success': True, 'message': f'{name} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_status_group(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':

        db_iteraction.edit_status_group(
            id=id,                                      # int - id записи - полное совпаден
            name=name,                                  # str - Новое название группы статусов
            type_group=type_group,                      # int - Новый номер группы
            color=color                                 # str - Новый цвет группы
        )
        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_status_group(
            id=id)                              # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202

@app.route('/get_status', methods=['POST'])
@jwt_required()
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
        id=id,                              # int - id статуса - полное совпадение
        name=name,                          # str - Имя статуса - частичное совпадение
        color=color,                        # str - Цвет статуса - полное совпадение
        group=group,                        # int - Номер группы - полное совпадение
        page=page                           # int - Старница погинации
    )
    return result

@app.route('/status', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
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
            name=name,                                      # str - Имя группы статуов - обязательное поле
            color=color,                                    # str - Цвет статуса - обязательное поле
            group=group,                                    # int - Номер группы - обязательное поле
            deadline=deadline,                              # int - Дедлайн статуса
            comment_required=comment_required,              # bool - Требуется ли коментарий
            payment_required=payment_required,              # bool - Требуется ли платеж
            available_to=available_to                       # [int, ...int] - Список статусов доступных для прехода
        )
        return {'success': True, 'message': f'{name} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_status(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':

        db_iteraction.edit_status(
            id=id,                                  # int - id записи - полное совпаден
            name=name,                              # str - Новое название статуса
            color=color,                            # str - Новый цвет статуса
            group=group,                            # int - Новый номер группы
            deadline=deadline,                      # int - Новый дедлайн статуса
            comment_required=comment_required,      # bool - Требуется коментарий
            payment_required=payment_required,      # bool - Требуется платеж
            available_to=available_to               # [int, ...int] - Новый список статусов для перехода
        )
        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_status(
            id=id)                              # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202



@app.route('/get_order_parts', methods=['POST'])
@jwt_required()
def get_order_parts():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    # Проверка соответствию типов данных
    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    amount = request_body.get('amount', 1)
    if amount and type(amount) != int:
        return {'success': False, 'message': "amount is not integer"}, 400

    cost = request_body.get('cost', 0)
    if cost:
        try:
            cost = float(cost)
        except:
            return {'success': False, 'message': 'Cost is not number'}, 400

    discount_value = request_body.get('discount_value', 0)
    if discount_value:
        try:
            discount_value = float(discount_value)
        except:
            return {'success': False, 'message': 'Discount_value is not number'}, 400

    engineer_id = request_body.get('engineer_id')
    if engineer_id and type(engineer_id) != int:
        return {'success': False, 'message': "Engineer_id is not integer"}, 400
    if engineer_id:
        if db_iteraction.get_employee(id=engineer_id)['count'] == 0:
            return {'success': False, 'message': 'engineer_id is not defined'}, 400

    order_id = request_body.get('order_id')
    if order_id and type(order_id) != int:
        return {'success': False, 'message': "order_id is not integer"}, 400
    if order_id:
        if db_iteraction.get_orders(id=order_id)['count'] == 0:
            return {'success': False, 'message': 'order_id is not defined'}, 400

    price = request_body.get('price', 0)
    if price:
        try:
            price = float(price)
        except:
            return {'success': False, 'message': 'price is not number'}, 400

    total = request_body.get('total', 0)
    if total:
        try:
            total = float(total)
        except:
            return {'success': False, 'message': 'total is not number'}, 400

    title = request_body.get('title')
    if title:
        title = str(title)

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    warranty_period = request_body.get('warranty_period', 0)
    if warranty_period and type(warranty_period) != int:
        return {'success': False, 'message': "warranty_period is not integer"}, 400

    created_at = request_body.get('created_at')

    if created_at:
        if type(created_at) != list:
            return {'success': False, 'message': "Created_at is not list"}, 400
        if len(created_at) != 2:
            return {'success': False, 'message': "Created_at is not correct"}, 400
        if (type(created_at[0]) != int) or (type(created_at[1]) != int):
            return {'success': False, 'message': "Created_at has not integers"}, 400

    result = db_iteraction.get_oder_parts(
        id=id,                              # int - id статуса - полное совпадение
        cost=cost,                          # int - себестоимость - полное совпадение
        discount_value=discount_value,      # float - сумма скидки - подное совпадение
        engineer_id=engineer_id,            # int - id инженера - полное сопвпадение
        price=price,                        # float - цена услуги - полное совпадение
        total=total,
        title=title,                        # str - наименование услуги - частичное совпадение
        deleted=deleted,
        warranty_period=warranty_period,    # int - гарантийный период - полное совпадение
        created_at=created_at,              # [int, int] - дата создания - промежуток дат
        order_id=order_id,                  # int - id заказа
        page=page                           # int - Старница погинации
    )
    return result, 200

@app.route('/order_parts', methods=['POST', 'GET', 'PUT', 'DELETE'])
@jwt_required()
def order_parts():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    # Проверка соответствию типов данных
    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    amount = request_body.get('amount', 1)
    if amount and type(amount) != int:
        return {'success': False, 'message': "amount is not integer"}, 400

    cost = request_body.get('cost', 0)
    if cost:
        try:
            cost = float(cost)
        except:
            return {'success': False, 'message': 'Cost is not number'}, 400

    discount_value = request_body.get('discount_value', 0)
    if discount_value:
        try:
            discount_value = float(discount_value)
        except:
            return {'success': False, 'message': 'Discount_value is not number'}, 400

    discount = request_body.get('discount', 0)
    if discount:
        try:
            discount = float(discount)
        except:
            return {'success': False, 'message': 'discount is not number'}, 400

    engineer_id = request_body.get('engineer_id')
    if engineer_id and type(engineer_id) != int:
        return {'success': False, 'message': "Engineer_id is not integer"}, 400
    if engineer_id:
        if db_iteraction.get_employee(id=engineer_id)['count'] == 0:
            return {'success': False, 'message': 'engineer_id is not defined'}, 400

    order_id = request_body.get('order_id')
    if order_id and type(order_id) != int:
        return {'success': False, 'message': "order_id is not integer"}, 400
    if order_id:
        if db_iteraction.get_orders(id=order_id)['count'] == 0:
            return {'success': False, 'message': 'order_id is not defined'}, 400

    price = request_body.get('price', 0)
    if price:
        try:
            price = float(price)
        except:
            return {'success': False, 'message': 'price is not number'}, 400

    total = request_body.get('total', 0)
    if total:
        try:
            total = float(total)
        except:
            return {'success': False, 'message': 'total is not number'}, 400

    title = request_body.get('title')
    if title:
        title = str(title)

    comment = request_body.get('comment')
    if comment:
        comment = str(comment)

    percent = request_body.get('percent')
    if percent and type(percent) != bool:
        return {'success': False, 'message': 'percent is not boolean'}, 400

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    warranty_period = request_body.get('warranty_period', 0)
    if warranty_period and type(warranty_period) != int:
        return {'success': False, 'message': "warranty_period is not integer"}, 400

    created_at = request_body.get('created_at')

    if request.method == 'POST':

        if created_at and type(created_at) != int:
            return {'success': False, 'message': "created_at is not integer"}, 400

        if not engineer_id:
            return {'success': False, 'message': 'engineer_id required'}, 400

        if not title:
            return {'success': False, 'message': 'title required'}, 400

        db_iteraction.add_oder_parts(
            amount=amount,                          # int - количество - по дефолту 1
            cost=cost,                              # int - себестоимость - по дефолту 0
            discount_value=discount_value,          # float - сумма скидки - по дефолту 0
            engineer_id=engineer_id,                # int - id инженера - обязательное поле
            price=price,                            # float - цена услуги - по дефолту 0
            total=total,
            title=title,                            # str - наименование услуги - обязательное поле
            comment=comment,
            percent=percent,
            discount=discount,
            deleted=deleted,
            warranty_period=warranty_period,        # int - гарантийный период - по дефолту 0
            created_at=created_at,                  # int - дата создания - по дефоту now
            order_id=order_id                       # int - id заказа
        )
        return {'success': True, 'message': f'{title} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_oder_parts(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':

        created_at = request_body.get('created_at', 0)
        if created_at and type(created_at) != int:
            return {'success': False, 'message': "created_at is not integer"}, 400


        db_iteraction.edit_oder_parts(
            id=id,                                      # int - id записи - полное совпаден
            amount=amount,                              # int - Новое количество
            cost=cost,                                  # float - Новая себестоимость
            discount_value=discount_value,              # float - Новая сумма скидки
            engineer_id=engineer_id,                    # int - Новый id инженера
            price=price,                                # int - Новая стоимость услуги
            total=total,
            title=title,                                # str - Новое наименование услуги
            comment=comment,
            percent=percent,
            discount=discount,
            deleted=deleted,
            warranty_period=warranty_period,            # int - Новый срок гаранти
            created_at=created_at,                      # int - Новая дата создания
            order_id=order_id,                          # int - id заказа
        )
        return {'success': True, 'message': f'{request_body.get("id")} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_oder_parts(id=id)                  # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202

@app.route('/get_clients', methods=['POST'])
@jwt_required()
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

    ad_campaign_id = request_body.get('ad_campaign_id')
    if ad_campaign_id and type(ad_campaign_id) != int:
        return {'success': False, 'message': "ad_campaign_id is not integer"}, 400

    if ad_campaign_id and db_iteraction.get_adCampaign(id=ad_campaign_id)['count'] == 0:
        return {'success': False, 'message': 'ad_campaign_id is not defined'}, 400

    address = request_body.get('address')
    if address:
        address = str(address)

    conflicted = request_body.get('conflicted')
    if conflicted:
        conflicted = bool(conflicted)

    deleted = request_body.get('deleted')
    if deleted:
        deleted = bool(deleted)

    name_doc = request_body.get('name_doc')
    if name_doc:
        name_doc = str(name_doc)

    discount_code = request_body.get('discount_code')
    if discount_code:
        discount_code = str(discount_code)

    discount_goods = request_body.get('discount_goods', 0)
    if discount_goods:
        try:
            discount_goods = float(discount_goods)
        except:
            return {'success': False, 'message': 'discount_goods is not number'}, 400

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

    if discount_materials_margin_id and db_iteraction.get_discount_margin(id=discount_materials_margin_id)['count'] == 0:
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
        id=id,                                                      # int - id клиента - полное совпадение
        conflicted=conflicted,                                      # bool - Конфликтный - полное совпадение
        email=email,                                                # str - Электронная почта - частичное совпадение
        juridical=juridical,                                        # bool - Юридическое лицо - полное совпадение
        deleted=deleted,
        name=name,                                                  # str - ФИО клиета - частично совпадение
        supplier=supplier,                                          # bool - Поставщик - полное совпадение
        phone=phone,
        page=page                                                   # int - Старница погинации
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
@jwt_required()
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
            juridical=juridical,                                        # bool - Юридическое лицо
            supplier=supplier,                                          # bool - Поставщик - полное совпадение
            conflicted=conflicted,                                      # bool - Конфликтный
            should_send_email=should_send_email,                        # bool - Согласен получать email
            deleted=deleted,
            discount_good_type=discount_good_type,
            discount_materials_type=discount_materials_type,
            discount_service_type=discount_service_type,

            name=name,                                                  # str - ФИО клиета - обязательное поле
            name_doc=name_doc,                                          # str - Имя в печатных документах
            email=email,                                                # str - Электронная почта
            address=address,                                            # str - Адрес клиента
            discount_code=discount_code,                                # str - Скидочная карта
            notes=notes,                                                # str - Заметки
            ogrn=ogrn,                                                  # str - ОГРН
            inn=inn,                                                    # str - ИНН
            kpp=kpp,                                                    # str - КПП
            juridical_address=juridical_address,                        # str - Юредический адресс
            director=director,                                          # str - Директор
            bank_name=bank_name,                                        # str - Наименование банка
            settlement_account=settlement_account,                      # str - Расчетный счет
            corr_account=corr_account,                                  # str - Кор. счет
            bic=bic,                                                    # str - БИК

            discount_goods=discount_goods,                              # float - Скидка на товары
            discount_materials=discount_materials,                      # float - Скидка на материалы
            discount_services=discount_services,                        # float - скидка на услуги

            ad_campaign_id=ad_campaign_id,                              # int - id рекламной компании
            discount_goods_margin_id=discount_goods_margin_id,          # int - id типа наценки
            discount_materials_margin_id=discount_materials_margin_id,  # int - id типа наценки
            discount_service_margin_id=discount_service_margin_id,

            tags=tags,                                                  # [str, ...str] - теги
            created_at=created_at,                                      # int - дата создания
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
            id=id,                                                      # int - id записи - полное совпаден
            juridical=juridical,                                        # bool - Юридическое лицо
            supplier=supplier,                                          # bool - Поставщик - полное совпадение
            conflicted=conflicted,                                      # bool - Конфликтный
            should_send_email=should_send_email,                        # bool - Согласен получать email
            deleted=deleted,
            discount_good_type=discount_good_type,
            discount_materials_type=discount_materials_type,
            discount_service_type=discount_service_type,

            name=name,                                                  # str - ФИО клиета - обязательное поле
            name_doc=name_doc,                                          # str - Имя в печатных документах
            email=email,                                                # str - Электронная почта
            address=address,                                            # str - Адрес клиента
            discount_code=discount_code,                                # str - Скидочная карта
            notes=notes,                                                # str - Заметки
            ogrn=ogrn,                                                  # str - ОГРН
            inn=inn,                                                    # str - ИНН
            kpp=kpp,                                                    # str - КПП
            juridical_address=juridical_address,                        # str - Юредический адресс
            director=director,                                          # str - Директор
            bank_name=bank_name,                                        # str - Наименование банка
            settlement_account=settlement_account,                      # str - Расчетный счет
            corr_account=corr_account,                                  # str - Кор. счет
            bic=bic,                                                    # str - БИК

            discount_goods=discount_goods,                              # float - Скидка на товары
            discount_materials=discount_materials,                      # float - Скидка на материалы
            discount_services=discount_services,                        # float - скидка на услуги

            ad_campaign_id=ad_campaign_id,                              # int - id рекламной компании
            discount_goods_margin_id=discount_goods_margin_id,          # int - id типа наценки
            discount_materials_margin_id=discount_materials_margin_id,  # int - id типа наценки
            discount_service_margin_id=discount_service_margin_id,

            tags=tags,                                                  # [str, ...str] - теги
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
            id=id)           # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202

@app.route('/get_orders', methods=['POST'])
@jwt_required()
def get_orders():
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

    created_at = request_body.get('created_at')
    if created_at:
        if type(created_at) != list:
            return {'success': False, 'message': "created_at is not list"}, 400
        if len(created_at) != 2:
            return {'success': False, 'message': "created_at is not correct"}, 400
        if type(created_at[0]) != int:
            return {'success': False, 'message': "created_at has not integers"}, 400
        if type(created_at[1]) and type(created_at[1]) != int:
            return {'success': False, 'message': "created_at has not integers"}, 400

    done_at = request_body.get('done_at')
    if done_at:
        if type(done_at) != list:
            return {'success': False, 'message': "done_at is not list"}, 400
        if len(done_at) != 2:
            return {'success': False, 'message': "done_at is not correct"}, 400
        if type(done_at[0]) != int:
            return {'success': False, 'message': "done_at has not integers"}, 400
        if type(done_at[1]) and type(done_at[1]) != int:
            return {'success': False, 'message': "done_at has not integers"}, 400

    closed_at = request_body.get('closed_at')
    if closed_at:
        if type(closed_at) != list:
            return {'success': False, 'message': "closed_at is not list"}, 400
        if len(closed_at) != 2:
            return {'success': False, 'message': "closed_at is not correct"}, 400
        if type(closed_at[0]) != int:
            return {'success': False, 'message': "closed_at has not integers"}, 400
        if type(closed_at[1]) and type(closed_at[1]) != int:
            return {'success': False, 'message': "closed_at has not integers"}, 400

    assigned_at = request_body.get('assigned_at')
    if assigned_at:
        if type(assigned_at) != list:
            return {'success': False, 'message': "assigned_at is not list"}, 400
        if len(assigned_at) != 2:
            return {'success': False, 'message': "assigned_at is not correct"}, 400
        if type(assigned_at[0]) != int:
            return {'success': False, 'message': "assigned_at has not integers"}, 400
        if type(assigned_at[1]) and type(assigned_at[1]) != int:
            return {'success': False, 'message': "assigned_at has not integers"}, 400

    estimated_done_at = request_body.get('estimated_done_at')
    if estimated_done_at:
        if type(estimated_done_at) != list:
            return {'success': False, 'message': "estimated_done_at is not list"}, 400
        if len(estimated_done_at) != 2:
            return {'success': False, 'message': "estimated_done_at is not correct"}, 400
        if type(estimated_done_at[0]) != int:
            return {'success': False, 'message': "estimated_done_at has not integers"}, 400
        if type(estimated_done_at[1]) and type(estimated_done_at[1]) != int:
            return {'success': False, 'message': "estimated_done_at has not integers"}, 400

    scheduled_for = request_body.get('scheduled_for')
    if scheduled_for:
        if type(scheduled_for) != list:
            return {'success': False, 'message': "scheduled_for is not list"}, 400
        if len(scheduled_for) != 2:
            return {'success': False, 'message': "scheduled_for is not correct"}, 400
        if type(scheduled_for[0]) != int:
            return {'success': False, 'message': "scheduled_for has not integers"}, 400
        if type(scheduled_for[1]) and type(scheduled_for[1]) != int:
            return {'success': False, 'message': "scheduled_for has not integers"}, 400

    warranty_date = request_body.get('warranty_date')
    if warranty_date:
        if type(warranty_date) != list:
            return {'success': False, 'message': "warranty_date is not list"}, 400
        if len(warranty_date) != 2:
            return {'success': False, 'message': "warranty_date is not correct"}, 400
        if type(warranty_date[0]) != int:
            return {'success': False, 'message': "warranty_date has not integers"}, 400
        if type(warranty_date[1]) and type(warranty_date[1]) != int:
            return {'success': False, 'message': "warranty_date has not integers"}, 400

    ad_campaign_id = request_body.get('ad_campaign_id')
    if ad_campaign_id and type(ad_campaign_id) != list:
        return {'success': False, 'message': "ad_campaign_id is not list"}, 400
    if ad_campaign_id:
        if not all([type(ad_cam) == int for ad_cam in ad_campaign_id]):
            return {'success': False, 'message': "ad_campaign_id has not integer"}, 400

    branch_id = request_body.get('branch_id')
    if branch_id and type(branch_id) != list:
        return {'success': False, 'message': "branch_id is not list"}, 400
    if branch_id:
        if not all([type(branch) == int for branch in branch_id]):
            return {'success': False, 'message': "branch_id has not integer"}, 400

    status_id = request_body.get('status_id')
    if status_id and type(status_id) != list:
        return {'success': False, 'message': "status_id is not list"}, 400
    if status_id:
        if not all([type(status) == int for status in status_id]):
            return {'success': False, 'message': "status_id has not integer"}, 400

    client_id = request_body.get('client_id')
    if client_id and type(client_id) != list:
        return {'success': False, 'message': "client_id is not list"}, 400
    if client_id:
        if not all([type(client) == int for client in client_id]):
            return {'success': False, 'message': "client_id has not integer"}, 400

    order_type_id = request_body.get('order_type_id')
    if order_type_id and type(order_type_id) != list:
        return {'success': False, 'message': "order_type_id is not list"}, 400
    if order_type_id:
        if not all([type(ot) == int for ot in order_type_id]):
            return {'success': False, 'message': "order_type_id has not integer"}, 400

    closed_by_id = request_body.get('closed_by_id')
    if closed_by_id and type(closed_by_id) != list:
        return {'success': False, 'message': "closed_by_id is not list"}, 400
    if closed_by_id:
        if not all([type(closed_by) == int for closed_by in closed_by_id]):
            return {'success': False, 'message': "closed_by_id has not integer"}, 400

    created_by_id = request_body.get('created_by_id')
    if created_by_id and type(created_by_id) != list:
        return {'success': False, 'message': "created_by_id is not list"}, 400
    if created_by_id:
        if not all([type(created_by) == int for created_by in created_by_id]):
            return {'success': False, 'message': "created_by_id has not integer"}, 400

    engineer_id = request_body.get('engineer_id')
    if engineer_id and type(engineer_id) != list:
        return {'success': False, 'message': "engineer_id is not list"}, 400
    if engineer_id:
        if not all([type(engineer) == int for engineer in engineer_id]):
            return {'success': False, 'message': "engineer_id has not integer"}, 400

    manager_id = request_body.get('manager_id')
    if manager_id and type(manager_id) != list:
        return {'success': False, 'message': "manager_id is not list"}, 400
    if manager_id:
        if not all([type(manager) == int for manager in manager_id]):
            return {'success': False, 'message': "manager_id has not integer"}, 400

    id_label = request_body.get('id_label')
    if id_label:
        id_label = str(id_label)

    kindof_good = request_body.get('kindof_good')
    if kindof_good:
        kindof_good = str(kindof_good)

    brand = request_body.get('brand')
    if brand:
        brand = str(brand)

    model = request_body.get('model')
    if model:
        model = str(model)

    subtype = request_body.get('subtype')
    if subtype:
        subtype = str(subtype)

    serial = request_body.get('serial')
    if serial:
        serial = str(serial)

    cell = request_body.get('cell')
    if cell:
        cell = str(cell)

    client_name = request_body.get('client_name')
    if client_name:
        client_name = str(client_name)

    client_phone = request_body.get('client_phone')
    if client_phone:
        client_phone = str(client_phone)

    field_sort = request_body.get('field_sort', 'id')
    if field_sort:
        field_sort = str(field_sort)

    sort = request_body.get('sort', 'asc')
    if sort:
        sort = str(sort)

    search = request_body.get('search')
    if search:
        search = str(search)

    estimated_cost = request_body.get('estimated_cost')
    if estimated_cost:
        try:
            estimated_cost = float(estimated_cost)
        except:
            return {'success': False, 'message': 'estimated_cost is not number'}, 400

    missed_payments = request_body.get('missed_payments')
    if missed_payments:
        try:
            missed_payments = float(missed_payments)
        except:
            return {'success': False, 'message': 'missed_payments is not number'}, 400

    discount_sum = request_body.get('discount_sum')
    if discount_sum:
        try:
            discount_sum = float(discount_sum)
        except:
            return {'success': False, 'message': 'estimated_cost is not number'}, 400

    payed = request_body.get('payed')
    if payed:
        try:
            payed = float(payed)
        except:
            return {'success': False, 'message': 'payed is not number'}, 400

    price = request_body.get('price')
    if price:
        try:
            price = float(price)
        except:
            return {'success': False, 'message': 'price is not number'}, 400

    urgent = request_body.get('urgent')
    if urgent and type(urgent) != bool:
        return {'success': False, 'message': 'urgent is not boolean'}, 400

    overdue = request_body.get('overdue')
    if overdue and type(overdue) != bool:
        return {'success': False, 'message': 'overdue is not boolean'}, 400

    status_overdue = request_body.get('status_overdue')
    if status_overdue and type(status_overdue) != bool:
        return {'success': False, 'message': 'status_overdue is not boolean'}, 400

    result = db_iteraction.get_orders(
        id=id,                                  # int - id филиала - полное совпадение
        created_at=created_at,                  # [int - int] - даты создания - промежуток
        done_at=done_at,                        # [int - int] - даты готовности - промежуток
        closed_at=closed_at,                    # [int - int] - даты закрытия - промежуток
        assigned_at=assigned_at,                # [int - int] - даты назначен на - промежуток
        estimated_done_at=estimated_done_at,    # [int - int] - запланированные даты готовности - промежуток
        scheduled_for=scheduled_for,            # [int - int] - даты запланирован на - промежуток
        warranty_date=warranty_date,            # [int - int] - даты горании до - промежуток

        ad_campaign_id=ad_campaign_id,          # list - id рекламной копании - полное совпадение одного из списка
        branch_id=branch_id,                    # list - id филиала - полное совпадение одного из списка
        status_id=status_id,                    # list - id статуса - полное совпадение одного из списка
        client_id=client_id,                    # list - id клиента - полное совпадение одного из списка
        order_type_id=order_type_id,            # list - id типа заказа - полное совпадение одного из списка
        engineer_id=engineer_id,                # list - id сотрудника - полное совпадение одного из списка
        manager_id=manager_id,                  # list - id сотрудника - полное совпадение одного из списка

        id_label=id_label,
        kindof_good=kindof_good,
        brand=brand,
        model=model,
        subtype=subtype,
        serial=serial,
        client_name=client_name,
        client_phone=client_phone,
        search=search,
        cell=cell,

        overdue=overdue,
        status_overdue=status_overdue,
        urgent=urgent,
        page=page,                         # int - Старница погинации
        field_sort=field_sort,
        sort=sort
    )

    return result, 200

@app.route('/orders', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
def orders():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 290

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    created_at = request_body.get('created_at')
    if created_at and type(created_at) != int:
        return {'success': False, 'message': 'created_at is not integer'}, 400

    done_at = request_body.get('done_at')
    if done_at and type(done_at) != int:
        return {'success': False, 'message': 'done_at is not integer'}, 400

    closed_at = request_body.get('closed_at')
    if closed_at and type(closed_at) != int:
        return {'success': False, 'message': 'closed_at is not integer'}, 400

    assigned_at = request_body.get('assigned_at')
    if assigned_at and type(assigned_at) != int:
        return {'success': False, 'message': 'assigned_at is not integer'}, 400

    duration = request_body.get('duration')
    if duration and type(duration) != int:
        return {'success': False, 'message': 'duration is not integer'}, 400

    estimated_done_at = request_body.get('estimated_done_at')
    if estimated_done_at and type(estimated_done_at) != int:
        return {'success': False, 'message': 'estimated_done_at is not integer'}, 400

    scheduled_for = request_body.get('scheduled_for')
    if scheduled_for and type(scheduled_for) != int:
        return {'success': False, 'message': 'scheduled_for is not integer'}, 400

    warranty_date = request_body.get('warranty_date')
    if warranty_date and type(warranty_date) != int:
        return {'success': False, 'message': 'warranty_date is not integer'}, 400

    status_deadline = request_body.get('status_deadline')
    if status_deadline and type(status_deadline) != int:
        return {'success': False, 'message': 'status_deadline is not integer'}, 400

    ad_campaign_id = request_body.get('ad_campaign_id')
    if ad_campaign_id and type(ad_campaign_id) != int:
        return {'success': False, 'message': "ad_campaign_id is not integer"}, 400
    if ad_campaign_id and db_iteraction.get_adCampaign(id=ad_campaign_id)['count'] == 0:
        return {'success': False, 'message': 'ad_campaign_id is not defined'}, 400

    branch_id = request_body.get('branch_id')
    if branch_id and type(branch_id) != int:
        return {'success': False, 'message': "branch_id is not integer"}, 400
    if branch_id and db_iteraction.get_branch(id=branch_id)['count'] == 0:
        return {'success': False, 'message': 'branch_id is not defined'}, 400

    status_id = request_body.get('status_id')
    if status_id and type(status_id) != int:
        return {'success': False, 'message': "status_id is not integer"}, 400
    if status_id and db_iteraction.get_status(id=status_id)['count'] == 0:
        return {'success': False, 'message': 'status_id is not defined'}, 400

    client_id = request_body.get('client_id')
    if client_id and type(client_id) != int:
        return {'success': False, 'message': "client_id is not integer"}, 400
    if client_id and db_iteraction.get_clients(id=client_id)['count'] == 0:
        return {'success': False, 'message': 'client_id is not defined'}, 400

    order_type_id = request_body.get('order_type_id')
    if order_type_id and type(order_type_id) != int:
        return {'success': False, 'message': "order_type_id is not integer"}, 400
    if order_type_id and db_iteraction.get_order_type(id=order_type_id)['count'] == 0:
        return {'success': False, 'message': 'order_type_id is not defined'}, 400

    closed_by_id = request_body.get('closed_by_id')
    if closed_by_id and type(closed_by_id) != int:
        return {'success': False, 'message': "closed_by_id is not integer"}, 400
    if closed_by_id and db_iteraction.get_employee(id=closed_by_id)['count'] == 0:
        return {'success': False, 'message': 'closed_by_id is not defined'}, 400

    created_by_id = request_body.get('created_by_id')
    if created_by_id and type(created_by_id) != int:
        return {'success': False, 'message': "created_by_id is not integer"}, 400
    if created_by_id and db_iteraction.get_employee(id=created_by_id)['count'] == 0:
        return {'success': False, 'message': 'created_by_id is not defined'}, 400

    engineer_id = request_body.get('engineer_id')
    if engineer_id and type(engineer_id) != int:
        return {'success': False, 'message': "engineer_id is not integer"}, 400
    if engineer_id and db_iteraction.get_employee(id=engineer_id)['count'] == 0:
        return {'success': False, 'message': 'engineer_id is not defined'}, 400

    manager_id = request_body.get('manager_id')
    if manager_id and type(manager_id) != int:
        return {'success': False, 'message': "manager_id is not integer"}, 400
    if manager_id and db_iteraction.get_employee(id=manager_id)['count'] == 0:
        return {'success': False, 'message': 'manager_id is not defined'}, 400

    id_label = request_body.get('id_label')
    if id_label:
        id_label = str(id_label)

    prefix = request_body.get('prefix')
    if prefix:
        prefix = str(prefix)

    kindof_good = request_body.get('kindof_good')
    if kindof_good:
        kindof_good = str(kindof_good)

    brand = request_body.get('brand')
    if brand:
        brand = str(brand)

    subtype = request_body.get('subtype')
    if subtype:
        subtype = str(subtype)

    model = request_body.get('model')
    if model:
        model = str(model)

    serial = request_body.get('serial')
    if serial:
        serial = str(serial)

    malfunction = request_body.get('malfunction')
    if malfunction:
        malfunction = str(malfunction)

    packagelist = request_body.get('packagelist')
    if packagelist:
        packagelist = str(packagelist)

    appearance = request_body.get('appearance')
    if appearance:
        appearance = str(appearance)

    manager_notes = request_body.get('manager_notes')
    if manager_notes:
        manager_notes = str(manager_notes)

    engineer_notes = request_body.get('engineer_notes')
    if engineer_notes:
        engineer_notes = str(engineer_notes)

    resume = request_body.get('resume')
    if resume:
        resume = str(resume)

    cell = request_body.get('cell')
    if cell:
        cell = str(cell)

    estimated_cost = request_body.get('estimated_cost')
    if estimated_cost:
        try:
            estimated_cost = float(estimated_cost)
        except:
            return {'success': False, 'message': 'estimated_cost is not number'}, 400

    missed_payments = request_body.get('missed_payments')
    if missed_payments:
        try:
            missed_payments = float(missed_payments)
        except:
            return {'success': False, 'message': 'missed_payments is not number'}, 400

    discount_sum = request_body.get('discount_sum')
    if discount_sum:
        try:
            discount_sum = float(discount_sum)
        except:
            return {'success': False, 'message': 'estimated_cost is not number'}, 400

    payed = request_body.get('payed')
    if payed:
        try:
            payed = float(payed)
        except:
            return {'success': False, 'message': 'payed is not number'}, 400

    price = request_body.get('price')
    if price:
        try:
            price = float(price)
        except:
            return {'success': False, 'message': 'price is not number'}, 400

    urgent = request_body.get('urgent')
    if urgent and type(urgent) != bool:
        return {'success': False, 'message': 'urgent is not boolean'}, 400

    if request.method == 'POST':
        if not status_id:
            return {'success': False, 'message': 'status_id required'}, 400

        equipments = request_body.get('equipments')
        for equipment in equipments:

            counter = db_iteraction.get_counts(id=1)['data'][0]
            id_label = f'{counter["prefix"]}-{counter["count"]}'
            db_iteraction.inc_count(id=1)

            order = db_iteraction.add_orders(
                created_at=created_at,                      # int - дата создания
                done_at=done_at,                            # int - дата готовность
                closed_at=closed_at,                        # int - дата закрытия
                assigned_at=assigned_at,                    # int - назначен на время
                duration=duration,                          # int - длительность
                estimated_done_at=estimated_done_at,        # int - запланированная дата готовности
                scheduled_for=scheduled_for,                # int - запланирован на
                warranty_date=warranty_date,                # int - дата гарантии до
                status_deadline=status_deadline,            # int - срок статуса до

                ad_campaign_id=ad_campaign_id,              # int - id рекламной компании
                branch_id=branch_id,                        # int - id филиала
                status_id=status_id,                        # int - id статуса
                client_id=client_id,                        # int - id клиента
                order_type_id=order_type_id,                # int - id заказа
                closed_by_id=closed_by_id,                  # int - id сотрдника который закрыл заказ
                created_by_id=created_by_id,                # int - id сотрудника который созда заказ
                engineer_id=engineer_id,                    # int - id сотрудника
                manager_id=manager_id,                      # int - id сотрудника

                id_label=id_label,                                                                          # str - номер заказа
                prefix=counter["prefix"],                                                                              # str - префикс
                kindof_good=equipment.get('kindof_good')['id'] if equipment.get('kindof_good') else None,   # str - тип техники
                brand=equipment.get('brand')['id'] if equipment.get('brand') else None,                     # str - бренд
                model=equipment.get('model')['id'] if equipment.get('model') else None,                     # str - модель
                subtype=equipment.get('subtype')['id'] if equipment.get('subtype') else None,               # str - модификация
                serial=equipment.get('serial'),                                                             # str - сирийный номер
                malfunction=equipment.get('malfunction'),                                                   # str - неисправность
                packagelist=equipment.get('packagelist'),                                                   # str - комплектация
                appearance=equipment.get('appearance'),                                                     # str - внешний вид
                manager_notes=manager_notes,                                                                # str - заметки менеджера
                engineer_notes=engineer_notes,                                                              # str - заметки инженера
                resume=resume,                                                                              # str - вердикт
                cell=cell,

                estimated_cost=estimated_cost,              # float - ориентировочная стоимость
                missed_payments=missed_payments,            # float - пропущеный платеж
                discount_sum=discount_sum,                  # float - сумма скидки
                payed=payed,                                # float - оплачено
                price=price,                                # float - стоимость

                urgent=urgent                               # boll - срочный
            )
            event_create_order(db_iteraction, order)
        return {'success': True, 'data': order, 'message': f'{id_label} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_orders(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':

        db_iteraction.edit_orders(
            id=id,                                  # int - id записи - полное совпаден
            created_at=created_at,                  # int - дата создания
            done_at=done_at,                        # int - дата готовность
            closed_at=closed_at,                    # int - дата закрытия
            assigned_at=assigned_at,                # int - назначен на время
            duration=duration,                      # int - длительность
            estimated_done_at=estimated_done_at,    # int - запланированная дата готовности
            scheduled_for=scheduled_for,            # int - запланирован на
            warranty_date=warranty_date,            # int - дата гарантии до
            status_deadline=status_deadline,        # int - срок статуса до

            ad_campaign_id=ad_campaign_id,          # int - id рекламной компании
            branch_id=branch_id,                    # int - id филиала
            status_id=status_id,                    # int - id статуса
            client_id=client_id,                    # int - id клиента
            order_type_id=order_type_id,            # int - id заказа
            closed_by_id=closed_by_id,              # int - id сотрдника который закрыл заказ
            created_by_id=created_by_id,            # int - id сотрудника который созда заказ
            engineer_id=engineer_id,                # int - id сотрудника
            manager_id=manager_id,                  # int - id сотрудника

            id_label=id_label,                      # str - номер заказа
            prefix=prefix,                          # str - префикс
            kindof_good=kindof_good,                # str - тип техники
            brand=brand,                            # str - бренд
            model=model,                            # str - модель
            subtype=subtype,                        # str - модификация
            serial=serial,                          # str - сирийный номер
            malfunction=malfunction,                # str - неисправность
            packagelist=packagelist,                # str - комплектация
            appearance=appearance,                  # str - внешний вид
            manager_notes=manager_notes,            # str - заметки менеджера
            engineer_notes=engineer_notes,          # str - заметки инженера
            resume=resume,                          # str - вердикт
            cell=cell,

            estimated_cost=estimated_cost,          # float - ориентировочная стоимость
            missed_payments=missed_payments,        # float - пропущеный платеж
            discount_sum=discount_sum,              # float - сумма скидки
            payed=payed,                            # float - оплачено
            price=price,                            # float - стоимость

            urgent=urgent                           # boll - срочный
        )
        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_orders(
            id=id)           # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202

@app.route('/change_order_status', methods=['POST'])
@jwt_required()
def change_order_status():

    # Достанем токен
    token = request.headers['Authorization'][7:]
    # Извлечем id пользователя из токена
    user_id = decode_token(token)['sub']

    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 290

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400
    order = db_iteraction.get_orders(id=id)
    # Проверим сущестует ли запись по данному id
    if order['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400
    order = order['data'][0]

    status_id = request_body.get('status_id')
    if not status_id:
        return {'success': False, 'message': 'status_id required'}, 400
    if type(status_id) != int:
        return {'success': False, 'message': "status_id is not integer"}, 400
    new_status = db_iteraction.get_status(id=status_id)
    if new_status['count'] == 0:
        return {'success': False, 'message': 'status_id is not defined'}, 400
    new_status = new_status['data'][0]

    current_status = order['status']
    # print('Текущий статус: ', current_status['name'])
    # print('Новый статус: ', new_status['name'])

    db_iteraction.edit_orders(
        id=id,
        status_id=status_id
    )

# Запишим сотрудника, который закрыл заказ =============================================================================

    if current_status['group'] == 6:
        db_iteraction.edit_orders(
            id=id,
            closed_by_id=user_id
        )

# Расчет Начислений по статусу Готов ===================================================================================

    # Если переход в группу Готов с груп ниже или групп Закрыт не успешно
    if new_status['group'] == 4 and (not current_status['group'] in [4, 5, 6]):
        # Проверим существую ли операции по данном заказу
        if order['operations']:
            # Пройдем циклом по всем операциям
            for operation in order['operations']:
                # проверим не удалена ли опарация
                if not operation['deleted']:
                    # Проверим есть ли у данного инженера правило с коэффициентом для данной операции
                    rules = db_iteraction.get_payrules(
                        type_rule=4,  # Инженуру за работу/услугу
                        employee_id=operation['engineer_id'],
                        order_type=order['order_type']['id'],
                        check_status=4  # По группе статусов Готов
                    )
                    # Проверим есть ли в самой операции особое правило начисления
                    if operation['dict_service'] and (operation['dict_service']['earnings_percent'] or operation['dict_service']['earnings_summ']):
                        # Проверим существуют ли правила начисления процента за данную работу
                        if operation['dict_service']['earnings_percent']:
                            if rules['count'] > 0:
                                rule = rules['data'][0]
                                # Определяем сумму вознаграждения
                                income = operation['dict_service']['earnings_percent'] * operation['total'] / 100 * rule['coefficient']
                            else:
                                income = operation['dict_service']['earnings_percent'] * operation['total'] / 100
                            # Добавим начисление
                            db_iteraction.add_payroll(
                                relation_type=5,  # 5 - за работу по статусу Готов
                                relation_id=operation['id'],
                                employee_id=operation['engineer_id'],
                                order_id=order['id'],
                                direction=2,  # 2 - приход
                                description=f'''Начисление за работу "{operation['title']}" в заказе {order['id_label']}''',
                                income=income
                            )
                        # Проверим существуют ли правила начисления суммы за данную работу
                        if operation['dict_service']['earnings_summ']:
                            if rules['count'] > 0:
                                rule = rules['data'][0]
                                # Определяем сумму вознаграждения
                                income = operation['dict_service']['earnings_summ'] * rule['coefficient']
                            else:
                                income = operation['dict_service']['earnings_summ']
                            # Добавим начисление
                            db_iteraction.add_payroll(
                                relation_type=5,  # 5 - за работу по статусу Готов
                                relation_id=operation['id'],
                                employee_id=operation['engineer_id'],
                                order_id=order['id'],
                                direction=2,  # 2 - приход
                                description=f'''Начисление за работу "{operation['title']}" в заказе {order['id_label']}''',
                                income=income
                            )
                    # Если в самой операции нет особых правил начисления
                    else:
                        # Пройдем циклом по всем правилам начисления если таковые есть
                        if rules['count'] > 0:
                            for rule in rules['data']:
                                # Если мы начисляем процент
                                if rule['method'] == 0:
                                    # Пройдем по списку коэфициентов и цен и определим сумму начисления
                                    for row in rule['count_coeff']:
                                        if row['cost'] <= operation['total']:
                                            income = row['coef'] * operation['total'] / 100
                                    # Добавим начисление
                                    db_iteraction.add_payroll(
                                        relation_type=5,  # 5 - за работу по статусу Готов
                                        relation_id=operation['id'],
                                        employee_id=operation['engineer_id'],
                                        order_id=order['id'],
                                        direction=2,  # 2 - приход
                                        description=f'''Начисление за работу "{operation['title']}" в заказе {order['id_label']}''',
                                        income=income
                                    )
                                else:
                                    # Пройдем по списку коэфициентов и цен и определим сумму начисления
                                    income = 0
                                    for row in rule['count_coeff']:
                                        if row['cost'] <= operation['total']:
                                            income = row['coef']
                                    # Добавим начисление
                                    db_iteraction.add_payroll(
                                        relation_type=5,  # 5 - за работу по статусу Готов
                                        relation_id=operation['id'],
                                        employee_id=operation['engineer_id'],
                                        order_id=order['id'],
                                        direction=2,  # 2 - приход
                                        description=f'''Начисление за работу "{operation['title']}" в заказе {order['id_label']}''',
                                        income=income
                                    )
    #  =====================================================================================================================

    # Списания при возврате статуса с Готов ===============================================================================

    # Если переход с группу Готов в любой другой групу кроме Доставка и Закрыт
    if (not new_status['group'] in [4, 5, 6]) and current_status['group'] in [4, 5, 6]:
        # Проверим существую ли операции по данном заказу
        if order['operations']:
            # Пройдем циклом по всем операциям
            for operation in order['operations']:
                # проверим не удалена ли опарация
                if not operation['deleted']:
                    # Найдем все начисления по данной операции
                    payrolls = db_iteraction.get_payrolls(
                        direction=2,  # все которые с приходом
                        deleted=False,  # Не удаленные
                        reimburse=False,  # Не возмещенные
                        relation_type=5,  # Начисленные за работу по статусу Готов
                        relation_id=operation['id']  # Принадлежащие данной операции
                    )
                    # Если начисления имеются
                    if payrolls['count'] > 0:
                        for payroll in payrolls['data']:
                            db_iteraction.add_payroll(
                                relation_type=11,  # Возврат заказа
                                relation_id=payroll['id'],  # id начисления за которое делается возмещение
                                employee_id=operation['engineer_id'],
                                order_id=order['id'],
                                direction=1,
                                description=f'''Возврат за операцию "{operation['title']}" в заказе {order['id_label']}''',
                                outcome=-payroll['income'],
                            )
                            # Отметим операцию как возмещенную
                            db_iteraction.edit_payroll(id=payroll['id'], reimburse=True)

    # ======================================================================================================================



# Расчет Начислений по статусу Успешно закрыт ========================================================================

    # Если переход в группу Закрыт успешно с любой другой групы
    if new_status['group'] == 6 and current_status['group'] != 6:
        # Проверим существую ли операции по данном заказу
        if order['operations']:
            # Пройдем циклом по всем операциям
            for operation in order['operations']:
                # проверим не удалена ли опарация
                if not operation['deleted']:
                    # Проверим есть ли у данного инженера правило с коэффициентом для данной операции
                    rules = db_iteraction.get_payrules(
                        type_rule=4,  # Инженуру за работу/услугу
                        employee_id=operation['engineer_id'],
                        order_type=order['order_type']['id'],
                        check_status=6  # По группе статусов Успешно закрыт
                    )
                    # Проверим есть ли в самой операции особое правило начисления
                    if operation['dict_service'] and (operation['dict_service']['earnings_percent'] or operation['dict_service']['earnings_summ']):
                        # print('Особые правила начиления')
                        # Проверим существуют ли правила начисления процента за данную работу
                        if operation['dict_service']['earnings_percent']:
                            if rules['count'] > 0:
                                rule = rules['data'][0]
                                # Определяем сумму вознаграждения
                                income = operation['dict_service']['earnings_percent'] * operation['total'] / 100 * rule['coefficient']
                            else:
                                income = operation['dict_service']['earnings_percent'] * operation['total'] / 100
                            # Добавим начисление
                            db_iteraction.add_payroll(
                                relation_type=4,  # 4 - за работу по статусу Закрыт
                                relation_id=operation['id'],
                                employee_id=operation['engineer_id'],
                                order_id=order['id'],
                                direction=2,  # 2 - приход
                                description=f'''Начисление за работу "{operation['title']}" в заказе {order['id_label']}''',
                                income=income,
                            )
                        # Проверим существуют ли правила начисления суммы за данную работу
                        if operation['dict_service']['earnings_summ']:
                            if rules['count'] > 0:
                                rule = rules['data'][0]
                                # Определяем сумму вознаграждения
                                income = operation['dict_service']['earnings_summ'] * rule['coefficient']
                            else:
                                income = operation['dict_service']['earnings_summ']
                            # Добавим начисление
                            db_iteraction.add_payroll(
                                relation_type=4,  # 4 - за работу по статусу Закрыт
                                relation_id=operation['id'],
                                employee_id=operation['engineer_id'],
                                order_id=order['id'],
                                direction=2,  # 2 - приход
                                description=f'''Начисление за работу "{operation['title']}" в заказе {order['id_label']}''',
                                income=income
                            )
                    # Если в самой операции нет особых правил начисления
                    else:
                        # print('Обычные правила начиления')
                        # Пройдем циклом по всем правилам начисления если таковые есть
                        if rules['count'] > 0:
                            for rule in rules['data']:
                                # Если мы начисляем процент
                                if rule['method'] == 0:
                                    # Пройдем по списку коэфициентов и цен и определим сумму начисления
                                    for row in rule['count_coeff']:
                                        if row['cost'] <= operation['total']:
                                            income = row['coef'] * operation['total'] / 100
                                    # Добавим начисление
                                    db_iteraction.add_payroll(
                                        relation_type=4,  # 4 - за работу по статусу закрыт
                                        relation_id=operation['id'],
                                        employee_id=operation['engineer_id'],
                                        order_id=order['id'],
                                        direction=2,  # 2 - приход
                                        description=f'''Начисление за работу "{operation['title']}" в заказе {order['id_label']}''',
                                        income=income
                                    )
                                else:
                                    # Пройдем по списку коэфициентов и цен и определим сумму начисления
                                    income = 0
                                    for row in rule['count_coeff']:
                                        if row['cost'] <= operation['total']:
                                            income = row['coef']
                                    # Добавим начисление
                                    db_iteraction.add_payroll(
                                        relation_type=4,  # 4 - за работу по статусу закрыт
                                        relation_id=operation['id'],
                                        employee_id=operation['engineer_id'],
                                        order_id=order['id'],
                                        direction=2,  # 2 - приход
                                        description=f'''Начисление за работу "{operation['title']}" в заказе {order['id_label']}''',
                                        income=income
                                    )
#  =====================================================================================================================

# Списания при возврате статуса с Закрыт ===============================================================================

    # Если переход в группу Закрыт успешно с любой другой групы
    if new_status['group'] != 6 and current_status['group'] == 6:
        # Проверим существую ли операции по данном заказу
        if order['operations']:
            # Пройдем циклом по всем операциям
            for operation in order['operations']:
                # проверим не удалена ли опарация
                if not operation['deleted']:
                    # Найдем все начисления по данной операции
                    payrolls = db_iteraction.get_payrolls(
                        direction=2,                # все которые с приходом
                        deleted=False,              # Не удаленные
                        reimburse=False,            # Не возмещенные
                        relation_type=4,            # Начисленные за работу по статусу закрыт
                        relation_id=operation['id'] # Принадлежащие данной операции
                    )
                    # Если начисления имеются
                    if payrolls['count'] > 0:
                        for payroll in payrolls['data']:
                            db_iteraction.add_payroll(
                                relation_type=11,               # Возврат заказа
                                relation_id=payroll['id'],      # id начисления за которое делается возмещение
                                employee_id=operation['engineer_id'],
                                order_id=order['id'],
                                direction=1,
                                description=f'''Возврат за операцию "{operation['title']}" в заказе {order['id_label']}''',
                                outcome=-payroll['income'],
                            )
                            # Отметим операцию как возмещенную
                            db_iteraction.edit_payroll(id=payroll['id'], reimburse=True)

# ======================================================================================================================

    # 3 Проверяем Если новый статус Готов, а текущий меньше
    # 4 Добавляем начисления по текущим правилам начисления ЗП

    # 7 Проверяем Если теущий статус Готов, а новый ниже
    # 8 Добавляем списания по имеющимся зачислениям
    # 9 Проверямем Если текущий статус Закрыт, а новый друго
    # 10 Добавляем списания по имеющимся зачислениям

# Отправка уведомлений =================================================================================================

    # Отправляем SMS при событиях сменты статуса
    event_change_status_to(db_iteraction, order, new_status)


    return {'success': True, 'message': f'{id} changed'}, 202

@app.route('/get_menu_rows', methods=['POST'])
@jwt_required()
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
        id=id,                              # int - id строчки - полное совпадение
        title=title,                        # [str, ...str] - Список имен строчек
        group_name=group_name               # [str, ...str] - Список имен групп
    )
    return result, 200

@app.route('/bagges', methods=['POST'])
@jwt_required()
def get_babges():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    employee_id = request_body.get('employee_id')
    if employee_id and type(employee_id) != int:
        return {'success': False, 'message': "employee_id is not integer"}, 400
    if not employee_id:
        return {'success': False, 'message': 'employee_id required'}, 400

    result = db_iteraction.get_badges(
        employee_id=employee_id            # int - id сотрудника - обязательное поле
    )
    return result, 200

@app.route('/get_custom_filters', methods=['POST'])
@jwt_required()
def get_custom_filters():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    employee_id = request_body.get('employee_id')
    if not employee_id:
        return {'success': False, 'message': 'employee_id required'}, 400
    if type(employee_id) != int:
        return {'success': False, 'message': "employee_id is not integer"}, 400
    if db_iteraction.get_employee(id=employee_id)['count'] == 0:
        return {'success': False, 'message': 'employee_id is not defined'}, 400

    result = db_iteraction.get_custom_filters(
        employee_id=employee_id                        # int - id сотрудника - полное совпадение
    )
    return result, 200

@app.route('/custom_filters', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
def custom_filters():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    employee_id = request_body.get('employee_id')
    if employee_id and type(employee_id) != int:
        return {'success': False, 'message': "employee_id is not integer"}, 400
    if employee_id and db_iteraction.get_employee(id=employee_id)['count'] == 0:
        return {'success': False, 'message': 'employee_id is not defined'}, 400

    filters = request_body.get('filters')

    title = request_body.get('title')
    if title:
        title = str(title)

    general = request_body.get('general')
    if general:
        general = bool(general)

    if request.method == 'POST':

        if not title:
            return {'success': False, 'message': 'title required'}, 400

        if not employee_id:
            return {'success': False, 'message': 'employee_id required'}, 400

        if not filters:
            return {'success': False, 'message': 'filters required'}, 400

        db_iteraction.add_custom_filters(
            title=title,                    # str - Название фильтра - обязательное поле
            filters=filters,                # json - фильтр - обязательное поле
            employee_id=employee_id,        # int - id сотрудника - обязательное поле
            general=general                 # bool - Общий - обязательное поле
        )
        return {'success': True, 'message': f'{title} added'}, 201

    # Проверим сущестует ли запись по данному id
    # if db_iteraction.get_custom_filters(id=id)['count'] == 0:
    #     return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_custom_filters(
            id=id,                    # int - id записи - полное совпаден
            title=title,              # str - Новое название филиала
            filters=filters,          # json - фильтр
            general=general           # bool - общпй
        )
        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_custom_filters(
            id=id)           # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202

@app.route('/get_equipment_type', methods=['POST'])
@jwt_required()
def get_equipment_type():
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

    result = db_iteraction.get_equipment_type(
        id=id,                            # int - id типа изделия - полное совпадение
        title=title,                      # str - Тип изделия - частичное совпадение
        deleted=deleted,
        page=page                         # int - Старница погинации
    )
    return result, 200

@app.route('/equipment_type', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
def equipment_type():
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

    icon = request_body.get('icon')
    if icon:
        icon = str(icon)

    url = request_body.get('url')
    if url:
        url = str(url)

    branches = request_body.get('branches')
    if branches and type(branches) != list:
        return {'success': False, 'message': "branches is not list"}, 400
    if branches:
        if not all([type(branch) == int for branch in branches]):
            return {'success': False, 'message': "branches has not integer"}, 400

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    list_for_join = request_body.get('list_for_join')
    if list_for_join and type(list_for_join) != list:
        return {'success': False, 'message': "list_for_join is not list"}, 400
    if list_for_join:
        if not all([type(join) == int for join in list_for_join]):
            return {'success': False, 'message': "list_for_join has not integer"}, 400

    if request.method == 'POST':

        if not title:
            return {'success': False, 'message': 'title required'}, 400

        db_iteraction.add_equipment_type(
            title=title,            # str - Тип изделия - обязательное поле
            icon=icon,              # str - Иконка типа изделия
            url=url,                # str - Ссылка на изображение типа изделия
            branches=branches,
            deleted=deleted
        )
        return {'success': True, 'message': f'{title} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_equipment_type(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_equipment_type(
            id=id,                    # int - id записи - полное совпаден
            title=title,              # str - Новое название типа изделия
            icon=icon,                # str - Новоя иконка изделия
            url=url,                  # str - Новоя ссылка на изображение изделия
            branches=branches,
            deleted=deleted
        )
        if list_for_join:
            for equipment_type in list_for_join:
                db_iteraction.edit_equipment_type(
                    id=equipment_type,
                    deleted=True
                )
                list_brands = db_iteraction.get_equipment_brand(equipment_type_id=equipment_type)['data']
                for equipment_brand in list_brands:
                    db_iteraction.edit_equipment_brand(
                        id=equipment_brand['id'],
                        equipment_type_id=id
                    )
        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_equipment_type(
            id=id)           # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202

@app.route('/get_equipment_brand', methods=['POST'])
@jwt_required()
def get_equipment_brand():
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

    equipment_type_id = request_body.get('equipment_type_id')
    if equipment_type_id and type(equipment_type_id) != int:
        return {'success': False, 'message': "equipment_type_id is not integer"}, 400
    if equipment_type_id and db_iteraction.get_equipment_type(id=equipment_type_id)['count'] == 0:
        return {'success': False, 'message': 'equipment_type_id is not defined'}, 400


    result = db_iteraction.get_equipment_brand(
        id=id,                                  # int - id бренда изделия - полное совпадение
        title=title,                            # str - Бренд - частичное совпадение
        equipment_type_id=equipment_type_id,    # int - id типа изделия
        deleted=deleted,
        page=page                               # int - Старница погинации
    )
    return result, 200

@app.route('/equipment_brand', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
def equipment_brand():
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

    icon = request_body.get('icon')
    if icon:
        icon = str(icon)

    url = request_body.get('url')
    if url:
        url = str(url)

    branches = request_body.get('branches')
    if branches and type(branches) != list:
        return {'success': False, 'message': "branches is not list"}, 400
    if branches:
        if not all([type(branch) == int for branch in branches]):
            return {'success': False, 'message': "branches has not integer"}, 400

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    equipment_type_id = request_body.get('equipment_type_id')
    if equipment_type_id and type(equipment_type_id) != int:
        return {'success': False, 'message': "equipment_type_id is not integer"}, 400
    if equipment_type_id and db_iteraction.get_equipment_type(id=equipment_type_id)['count'] == 0:
        return {'success': False, 'message': 'equipment_type_id is not defined'}, 400

    list_for_join = request_body.get('list_for_join')
    if list_for_join and type(list_for_join) != list:
        return {'success': False, 'message': "list_for_join is not list"}, 400
    if list_for_join:
        if not all([type(join) == int for join in list_for_join]):
            return {'success': False, 'message': "list_for_join has not integer"}, 400

    if request.method == 'POST':

        if not equipment_type_id:
            return {'success': False, 'message': 'equipment_type_id required'}, 400

        if not title:
            return {'success': False, 'message': 'title required'}, 400

        db_iteraction.add_equipment_brand(
            title=title,                            # str - Бренд - обязательное поле
            icon=icon,                              # str - Иконка бренда изделия
            url=url,                                # str - Ссылка на изображение бренда изделия
            branches=branches,
            deleted=deleted,
            equipment_type_id=equipment_type_id     # int - id типа изделия
        )
        return {'success': True, 'message': f'{title} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_equipment_brand(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_equipment_brand(
            id=id,                                  # int - id записи - полное совпаден
            title=title,                            # str - Новое название бренда изделия
            icon=icon,                              # str - Новоя бренда изделия
            url=url,                                # str - Новоя ссылка на изображение бренда изделия
            branches=branches,
            deleted=deleted,
            equipment_type_id=equipment_type_id     # int - id типа изделия
        )
        if list_for_join:
            for equipment_brand in list_for_join:
                db_iteraction.edit_equipment_brand(
                    id=equipment_brand,
                    deleted=True
                )
                list_subtypes = db_iteraction.get_equipment_subtype(equipment_brand_id=equipment_brand)['data']
                for equipment_subtype in list_subtypes:
                    db_iteraction.edit_equipment_subtype(
                        id=equipment_subtype['id'],
                        equipment_brand_id=id
                    )
        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_equipment_brand(
            id=id)           # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202

@app.route('/get_equipment_subtype', methods=['POST'])
@jwt_required()
def get_equipment_subtype():
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

    equipment_brand_id = request_body.get('equipment_brand_id')
    if equipment_brand_id and type(equipment_brand_id) != int:
        return {'success': False, 'message': "equipment_brand_id is not integer"}, 400
    if equipment_brand_id and db_iteraction.get_equipment_brand(id=equipment_brand_id)['count'] == 0:
        return {'success': False, 'message': 'equipment_brand_id is not defined'}, 400

    result = db_iteraction.get_equipment_subtype(
        id=id,                                  # int - id модификации изделия - полное совпадение
        title=title,                            # str - Модификация изделия - частичное совпадение
        equipment_brand_id=equipment_brand_id,  # int - id бренда изделия
        deleted=deleted,
        page=page                               # int - Старница погинации
    )
    return result, 200

@app.route('/equipment_subtype', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
def equipment_subtype():
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

    icon = request_body.get('icon')
    if icon:
        icon = str(icon)

    url = request_body.get('url')
    if url:
        url = str(url)

    branches = request_body.get('branches')
    if branches and type(branches) != list:
        return {'success': False, 'message': "branches is not list"}, 400
    if branches:
        if not all([type(branch) == int for branch in branches]):
            return {'success': False, 'message': "branches has not integer"}, 400

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    equipment_brand_id = request_body.get('equipment_brand_id')
    if equipment_brand_id and type(equipment_brand_id) != int:
        return {'success': False, 'message': "equipment_brand_id is not integer"}, 400
    if equipment_brand_id and db_iteraction.get_equipment_brand(id=equipment_brand_id)['count'] == 0:
        return {'success': False, 'message': 'equipment_brand_id is not defined'}, 400

    list_for_join = request_body.get('list_for_join')
    if list_for_join and type(list_for_join) != list:
        return {'success': False, 'message': "list_for_join is not list"}, 400
    if list_for_join:
        if not all([type(join) == int for join in list_for_join]):
            return {'success': False, 'message': "list_for_join has not integer"}, 400




    if request.method == 'POST':

        if not title:
            return {'success': False, 'message': 'title required'}, 400

        if not equipment_brand_id:
            return {'success': False, 'message': 'equipment_brand_id required'}, 400

        id_subtype = db_iteraction.add_equipment_subtype(
            title=title,                            # str - Модификация изделия - обязательное поле
            icon=icon,                              # str - Иконка модификации изделия
            url=url,                                # str - Ссылка на изображение модификации изделия
            branches=branches,
            deleted=deleted,
            equipment_brand_id=equipment_brand_id   # int - id бренда изделия
        )

        # загрузка изображения
        img_uri = request_body.get('img')
        if img_uri:
            with urlopen(img_uri) as response:
                data = response.read()
            url = f'build/static/data/PCB/subtype{id_subtype}.jpeg'
            with open(url, 'wb') as f:
                f.write(data)
            url = f'data/PCB/subtype{id_subtype}.jpeg'
            db_iteraction.edit_equipment_subtype(
                id=id_subtype,
                url=url
            )
        return {'success': True, 'message': f'{title} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_equipment_subtype(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':

        # загрузка/замена изображения
        img_uri = request_body.get('img')
        if img_uri:
            with urlopen(img_uri) as response:
                data = response.read()
            url = f'build/static/data/PCB/subtype{id}.jpeg'
            with open(url, 'wb') as f:
                f.write(data)
            url = f'data/PCB/subtype{id}.jpeg'

        db_iteraction.edit_equipment_subtype(
            id=id,                                  # int - id записи - полное совпаден
            title=title,                            # str - Новое название бренда изделия
            icon=icon,                              # str - Новоя бренда изделия
            url=url,                                # str - Новоя ссылка на изображение бренда изделия
            branches=branches,
            deleted=deleted,
            equipment_brand_id=equipment_brand_id   # int - id типа изделия
        )
        if list_for_join:
            for equipment_subtype in list_for_join:
                db_iteraction.edit_equipment_subtype(
                    id=equipment_subtype,
                    deleted=True
                )
                list_models = db_iteraction.get_equipment_model(equipment_subtype_id=equipment_subtype)['data']
                for equipment_model in list_models:
                    db_iteraction.edit_equipment_model(
                        id=equipment_model['id'],
                        equipment_subtype_id=id
                    )


        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_equipment_subtype(
            id=id)                              # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202

@app.route('/get_equipment_model', methods=['POST'])
@jwt_required()
def get_equipment_model():
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

    equipment_subtype_id = request_body.get('equipment_subtype_id')
    if equipment_subtype_id and type(equipment_subtype_id) != int:
        return {'success': False, 'message': "equipment_subtype_id is not integer"}, 400
    if equipment_subtype_id and db_iteraction.get_equipment_subtype(id=equipment_subtype_id)['count'] == 0:
        return {'success': False, 'message': 'equipment_subtype_id is not defined'}, 400

    result = db_iteraction.get_equipment_model(
        id=id,                                      # int - id модели изделия - полное совпадение
        title=title,                                # str - Модель изделия - частичное совпадение
        equipment_subtype_id=equipment_subtype_id,  # int - id модификации изделия
        deleted=deleted,
        page=page                                   # int - Старница погинации
    )
    return result, 200

@app.route('/equipment_model', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
def equipment_model():
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

    icon = request_body.get('icon')
    if icon:
        icon = str(icon)

    url = request_body.get('url')
    if url:
        url = str(url)

    branches = request_body.get('branches')
    if branches and type(branches) != list:
        return {'success': False, 'message': "branches is not list"}, 400
    if branches:
        if not all([type(branch) == int for branch in branches]):
            return {'success': False, 'message': "branches has not integer"}, 400

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    equipment_subtype_id = request_body.get('equipment_subtype_id')
    if equipment_subtype_id and type(equipment_subtype_id) != int:
        return {'success': False, 'message': "equipment_subtype_id is not integer"}, 400
    if equipment_subtype_id and db_iteraction.get_equipment_subtype(id=equipment_subtype_id)['count'] == 0:
        return {'success': False, 'message': 'equipment_subtype_id is not defined'}, 400

    if request.method == 'POST':

        if not equipment_subtype_id:
            return {'success': False, 'message': 'equipment_subtype_id required'}, 400

        if not title:
            return {'success': False, 'message': 'title required'}, 400

        db_iteraction.add_equipment_model(
            title=title,                                # str - Модель изделия - обязательное поле
            icon=icon,                                  # str - Иконка модели изделия
            url=url,                                    # str - Ссылка на изображение модели изделия
            branches=branches,
            deleted=deleted,
            equipment_subtype_id=equipment_subtype_id   # int - id модификации изделия
        )
        return {'success': True, 'message': f'{title} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_equipment_model(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_equipment_model(
            id=id,                                      # int - id записи - полное совпаден
            title=title,                                # str - Новое название модели изделия
            icon=icon,                                  # str - Новоя иконика модели изделия
            url=url,                                    # str - Новоя ссылка на изображение модели изделия
            branches=branches,
            deleted=deleted,
            equipment_subtype_id=equipment_subtype_id   # int - id типа изделия
        )
        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_equipment_model(
            id=id)                              # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202

@app.route('/get_setting_menu', methods=['POST'])
@jwt_required()
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
        id=id,                              # int - id строчки - полное совпадение
        title=title,                        # [str, ...str] - Список имен строчек
        group_name=group_name               # [str, ...str] - Список имен групп
    )
    return result, 200

@app.route('/get_roles', methods=['POST'])
@jwt_required()
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
        id=id,                              # int - id роли - полное совпадение
        title=title,                        # str - Роль - частичное совпадение
        page=page                           # int - Старница погинации
    )
    return result, 200

@app.route('/roles', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
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
            title=title,                                        # str - Роль - обязательное поле
            earnings_visibility=earnings_visibility,            # bool - Видит только свою ЗП
            leads_visibility=leads_visibility,                  # bool - Видит только свои обращения
            orders_visibility=orders_visibility,                # bool - Видит тольк свои заказы
            permissions=permissions,                            # [str, ...str] - Список разрешений
            settable_statuses=settable_statuses,                # [int, ...int] - Может устанавливать статусы
            visible_statuses=visible_statuses,                  # [int, ...int] - Может видеть статусы
            settable_discount_margin=settable_discount_margin   # [int, ...int] - Может использовать цены
        )
        return {'success': True, 'message': f'{title} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_role(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_role(
            id=id,                                                  # int - id записи - полное совпаден
            title=title,                                            # str - Новое название роли
            earnings_visibility=earnings_visibility,                # bool - Видит только свою ЗП
            leads_visibility=leads_visibility,                      # bool - Видит только свои обращения
            orders_visibility=orders_visibility,                    # bool - Видит тольк свои заказы
            permissions=permissions,                                # [str, ...str] - Новый список разрешений
            settable_statuses=settable_statuses,                    # [int, ...int] - Новый список статуов, которые может устанавливать
            visible_statuses=visible_statuses,                      # [int, ...int] - Новый список статуов, которые может видеть
            settable_discount_margin = settable_discount_margin     # [int, ...int] - Может использовать цены
        )
        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_roles(
            id=id)                                  # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202

@app.route('/get_generally_info', methods=['POST'])
@jwt_required()
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
        id=id,                            # int - id филиала - полное совпадение
    )
    return result, 200

@app.route('/generally_info', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
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
            id=id,                    # int - id записи - полное совпаден
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
            id=id)           # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202

@app.route('/get_main_data', methods=['POST'])
@jwt_required()
def get_main_data():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    result = {}

    generally_info = db_iteraction.get_generally_info(id=1)
    result['generally_info'] = generally_info['data']

    branches = db_iteraction.get_branch()
    result['branch'] = branches['data']

    order_type = db_iteraction.get_order_type()
    result['order_type'] = order_type['data']

    counts = db_iteraction.get_counts()
    result['counts'] = counts['data']

    ad_campaign = db_iteraction.get_adCampaign()
    result['ad_campaign'] = ad_campaign['data']

    item_payments = db_iteraction.get_item_payments()
    result['item_payments'] = item_payments['data']

    status_group = db_iteraction.get_status_group()
    result['status_group'] = status_group['data']

    cashboxes = db_iteraction.get_cashbox()
    result['cashboxes'] = cashboxes['data']

    item_payments = db_iteraction.get_item_payments()
    result['item_payments'] = item_payments['data']

    service_prices = db_iteraction.get_service_prices()
    result['service_prices'] = service_prices['data']

    result['success'] = True
    return result, 200

@app.route('/get_counts', methods=['POST'])
@jwt_required()
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
        id=id                            # int - id  - полное совпадение
    )
    return result, 200

@app.route('/counts', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
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
            id=id,                    # int - id записи - полное совпаден
            prefix=prefix,
            count=count,
            description=description
        )
        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_counts(
            id=id)           # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202

@app.route('/get_malfunction', methods=['POST'])
@jwt_required()
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
        id=id,                            # int - id  - полное совпадение
        page=page,
        title=title
    )
    return result, 200

@app.route('/malfunction', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
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
                id=malfunction[0]['id'],        # int - id записи - полное совпаден
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
            id=id,              # int - id записи - полное совпаден
            title=title,
            count=count
        )
        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':

        if del_ids:
            for ids in del_ids:
                db_iteraction.del_malfunction(
                    id=ids               # int - id записи - полное совпаден
                )
        else:
            db_iteraction.del_malfunction(
                id=id  # int - id записи - полное совпаден
            )
        return {'success': True, 'message': f'{id} deleted'}, 202

@app.route('/get_packagelist', methods=['POST'])
@jwt_required()
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
        id=id,                            # int - id  - полное совпадение
        page=page,
        title=title
    )
    return result, 200

@app.route('/packagelist', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
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
            id=id,              # int - id записи - полное совпаден
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
@jwt_required()
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
        id=id,                            # int - id  - полное совпадение
        page=page,
        direction=direction
    )
    return result, 200

@app.route('/item_payments', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
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
            id=id,              # int - id записи - полное совпаден
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

@app.route('/get_cashbox', methods=['POST'])
@jwt_required()
def get_cashbox():
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

    isGlobal = request_body.get('isGlobal')
    if isGlobal and type(isGlobal) != bool:
        return {'success': False, 'message': 'isGlobal is not boolean'}, 400

    isVirtual = request_body.get('isVirtual')
    if isVirtual and type(isVirtual) != bool:
        return {'success': False, 'message': 'isVirtual is not boolean'}, 400

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    branch_id = request_body.get('branch_id')
    if branch_id and type(branch_id) != int:
        return {'success': False, 'message': "branch_id is not integer"}, 400
    if branch_id and db_iteraction.get_branch(id=branch_id)['count'] == 0:
        return {'success': False, 'message': 'branch_id is not defined'}, 400



    result = db_iteraction.get_cashbox(
        id=id,                            # int - id  - полное совпадение
        title=title,
        isGlobal=isGlobal,
        isVirtual=isVirtual,
        deleted=deleted,
        branch_id=branch_id
    )
    return result, 200

@app.route('/cashbox', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
def cashbox():
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

    balance = request_body.get('balance')
    if balance:
        try:
            balance = float(balance)
        except:
            return {'success': False, 'message': 'balance is not number'}, 400

    types = request_body.get('type')
    if types and type(types) != int:
        return {'success': False, 'message': "types is not integer"}, 400

    isGlobal = request_body.get('isGlobal')
    if isGlobal and type(isGlobal) != bool:
        return {'success': False, 'message': 'isGlobal is not boolean'}, 400

    isVirtual = request_body.get('isVirtual')
    if isVirtual and type(isVirtual) != bool:
        return {'success': False, 'message': 'isVirtual is not boolean'}, 400

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    permissions = request_body.get('permissions')
    if permissions and type(permissions) != list:
        return {'success': False, 'message': "permissions is not list"}, 400
    if permissions:
        if not all([type(permission) == str for permission in permissions]):
            return {'success': False, 'message': "permissions has not string"}, 400

    employees = request_body.get('employees')
    # if employees and type(employees) != list:
    #     return {'success': False, 'message': "employees is not list"}, 400
    # if employees:
    #     if not all([type(employee) == int for employee in employees]):
    #         return {'success': False, 'message': "employees has not integer"}, 400

    branch_id = request_body.get('branch_id')
    if branch_id and type(branch_id) != int:
        return {'success': False, 'message': "branch_id is not integer"}, 400
    if branch_id and db_iteraction.get_branch(id=branch_id)['count'] == 0:
        return {'success': False, 'message': 'branch_id is not defined'}, 400


    if request.method == 'POST':
        db_iteraction.add_cashbox(
            title=title,
            balance=balance,
            type=types,
            isGlobal=isGlobal,
            isVirtual=isVirtual,
            deleted=deleted,
            permissions=permissions,
            employees=employees,
            branch_id=branch_id
        )

        return {'success': True, 'message': f'{title} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_cashbox(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        db_iteraction.edit_cashbox(
            id=id,              # int - id записи - полное совпаден
            title=title,
            balance=balance,
            type=types,
            isGlobal=isGlobal,
            isVirtual=isVirtual,
            deleted=deleted,
            permissions=permissions,
            employees=employees,
            branch_id=branch_id
        )
        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':
        db_iteraction.del_cashbox(
            id=id)                      # int - id записи - полное совпаден
        return {'success': True, 'message': f'{id} deleted'}, 202

@app.route('/get_payments', methods=['POST'])
@jwt_required()
def get_payments():
    if print_logs:
        start_time = time.time()
        print(f'Начало выполнение запроса {start_time}')
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    cashflow_category = request_body.get('cashflow_category')
    if cashflow_category:
        cashflow_category = str(cashflow_category)

    direction = request_body.get('direction')
    if direction and type(direction) != int:
        return {'success': False, 'message': "direction is not integer"}, 400

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    custom_created_at = request_body.get('custom_created_at')
    if custom_created_at:
        if type(custom_created_at) != list:
            return {'success': False, 'message': "custom_created_at is not list"}, 400
        if len(custom_created_at) != 2:
            return {'success': False, 'message': "custom_created_at is not correct"}, 400
        if type(custom_created_at[0]) != int:
            return {'success': False, 'message': "custom_created_at has not integers"}, 400
        if type(custom_created_at[1]) and type(custom_created_at[1]) != int:
            return {'success': False, 'message': "custom_created_at has not integers"}, 400

    tags = request_body.get('tags')
    if tags:
        tags = str(tags)

    cashbox_id = request_body.get('cashbox_id')
    if cashbox_id and type(cashbox_id) != int:
        return {'success': False, 'message': "cashbox_id is not integer"}, 400
    if cashbox_id and db_iteraction.get_cashbox(id=cashbox_id)['count'] == 0:
        return {'success': False, 'message': 'cashbox_id is not defined'}, 400

    client_id = request_body.get('client_id')
    if client_id and type(client_id) != int:
        return {'success': False, 'message': "client_id is not integer"}, 400
    if client_id and db_iteraction.get_clients(id=client_id)['count'] == 0:
        return {'success': False, 'message': 'client_id is not defined'}, 400

    employee_id = request_body.get('employee_id')
    if employee_id and type(employee_id) != int:
        return {'success': False, 'message': "employee_id is not integer"}, 400
    if employee_id and db_iteraction.get_employee(id=employee_id)['count'] == 0:
        return {'success': False, 'message': 'employee_id is not defined'}, 400

    order_id = request_body.get('order_id')
    if order_id and type(order_id) != int:
        return {'success': False, 'message': "order_id is not integer"}, 400
    if order_id and db_iteraction.get_orders(id=order_id)['count'] == 0:
            return {'success': False, 'message': 'order_id is not defined'}, 400

    if print_logs:
        print(f'Верефикации данных: {time.time() - start_time} сек.')

    result = db_iteraction.get_payments(
        id=id,                                      # int - id  - полное совпадение
        cashflow_category=cashflow_category,
        direction=direction,
        deleted=deleted,
        custom_created_at=custom_created_at,
        tags=tags,
        cashbox_id=cashbox_id,
        client_id=client_id,
        employee_id=employee_id,
        order_id=order_id
    )
    if print_logs:
        print(f'Данные найдены и отправлены: {time.time() - start_time} сек.')
    return result, 200

@app.route('/payments', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
def payments():
    if print_logs:
        start_time = time.time()
        print(f'Начало выполнение запроса {start_time}')
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    cashflow_category = request_body.get('cashflow_category')
    if cashflow_category:
        cashflow_category = str(cashflow_category)

    description = request_body.get('description')
    if description:
        description = str(description)

    deposit = request_body.get('deposit')
    if deposit:
        try:
            deposit = float(deposit)
        except:
            return {'success': False, 'message': 'deposit is not number'}, 400

    income = request_body.get('income')
    if income:
        try:
            income = float(income)
        except:
            return {'success': False, 'message': 'income is not number'}, 400

    outcome = request_body.get('outcome')
    if outcome:
        try:
            outcome = float(outcome)
        except:
            return {'success': False, 'message': 'balance is not number'}, 400

    direction = request_body.get('direction')
    if direction and type(direction) != int:
        return {'success': False, 'message': "direction is not integer"}, 400

    can_print_fiscal = request_body.get('can_print_fiscal')
    if can_print_fiscal and type(can_print_fiscal) != bool:
        return {'success': False, 'message': 'can_print_fiscal is not boolean'}, 400

    is_fiscal = request_body.get('is_fiscal')
    if is_fiscal and type(is_fiscal) != bool:
        return {'success': False, 'message': 'is_fiscal is not boolean'}, 400

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    created_at = request_body.get('created_at')
    if created_at and type(created_at) != int:
        return {'success': False, 'message': "created_at is not integer"}, 400

    custom_created_at = request_body.get('custom_created_at')
    if custom_created_at and type(custom_created_at) != int:
        return {'success': False, 'message': "custom_created_at is not integer"}, 400

    tags = request_body.get('tags')
    if tags and type(tags) != list:
        return {'success': False, 'message': "tags is not list"}, 400
    if tags:
        if not all([type(tag) == str for tag in tags]):
            return {'success': False, 'message': "tags has not string"}, 400

    relation_id = request_body.get('relation_id')
    if relation_id and type(relation_id) != int:
        return {'success': False, 'message': "relation_id is not integer"}, 400

    cashbox_id = request_body.get('cashbox_id')
    if cashbox_id and type(cashbox_id) != int:
        return {'success': False, 'message': "cashbox_id is not integer"}, 400
    if cashbox_id and db_iteraction.get_cashbox(id=cashbox_id)['count'] == 0:
        return {'success': False, 'message': 'cashbox_id is not defined'}, 400

    target_cashbox_id = request_body.get('target_cashbox_id')
    if target_cashbox_id and type(target_cashbox_id) != int:
        return {'success': False, 'message': "target_cashbox_id is not integer"}, 400
    if target_cashbox_id and db_iteraction.get_cashbox(id=target_cashbox_id)['count'] == 0:
        return {'success': False, 'message': 'target_cashbox_id is not defined'}, 400

    client_id = request_body.get('client_id')
    if client_id and type(client_id) != int:
        return {'success': False, 'message': "client_id is not integer"}, 400
    if client_id and db_iteraction.get_clients(id=client_id)['count'] == 0:
        return {'success': False, 'message': 'client_id is not defined'}, 400

    employee_id = request_body.get('employee_id')
    if employee_id and type(employee_id) != int:
        return {'success': False, 'message': "employee_id is not integer"}, 400
    if employee_id and db_iteraction.get_employee(id=employee_id)['count'] == 0:
        return {'success': False, 'message': 'employee_id is not defined'}, 400

    order_id = request_body.get('order_id')
    if order_id and type(order_id) != int:
        return {'success': False, 'message': "order_id is not integer"}, 400
    if order_id and db_iteraction.get_orders(id=order_id)['count'] == 0:
        return {'success': False, 'message': 'order_id is not defined'}, 400


    if request.method == 'POST':
        payment1_id = db_iteraction.add_payments(
            cashflow_category=cashflow_category,
            description=description,
            deposit=deposit,
            income=income,
            outcome=outcome,
            direction=direction,
            can_print_fiscal=can_print_fiscal,
            deleted=deleted,
            is_fiscal=is_fiscal,
            created_at=created_at,
            custom_created_at=custom_created_at,
            tags=tags,
            relation_id=None,
            cashbox_id=cashbox_id,
            client_id=client_id,
            employee_id=employee_id,
            order_id=order_id
        )

        # db_iteraction.edit_cashbox(
        #     id=cashbox_id,
        #     title=None,
        #     balance=deposit,
        #     type=None,
        #     isGlobal=None,
        #     isVirtual=None,
        #     deleted=None,
        #     permissions=None,
        #     employees=None,
        #     branch_id=None
        # )

        if target_cashbox_id:
            # deposit=db_iteraction.get_cashbox(id=target_cashbox_id)['data'][0]['balance'] + abs(outcome)
            payment2_id = db_iteraction.add_payments(
                cashflow_category=cashflow_category,
                description=description,
                deposit=None,
                income=abs(outcome),
                outcome=income,
                direction=direction,
                can_print_fiscal=can_print_fiscal,
                deleted=deleted,
                is_fiscal=is_fiscal,
                created_at=created_at,
                custom_created_at=custom_created_at,
                tags=tags,
                relation_id=payment1_id,
                cashbox_id=target_cashbox_id,
                client_id=client_id,
                employee_id=employee_id,
                order_id=order_id
            )

            db_iteraction.edit_payments(
                id=payment1_id,
                cashflow_category=None,
                description=None,
                deposit=None,
                income=None,
                outcome=None,
                direction=None,
                can_print_fiscal=None,
                deleted=None,
                is_fiscal=None,
                created_at=None,
                custom_created_at=None,
                tags=None,
                relation_id=payment2_id,
                cashbox_id=None,
                client_id=None,
                employee_id=None,
                order_id=None
            )

            # db_iteraction.edit_cashbox(
            #     id=target_cashbox_id,
            #     title=None,
            #     balance=deposit,
            #     type=None,
            #     isGlobal=None,
            #     isVirtual=None,
            #     deleted=None,
            #     permissions=None,
            #     employees=None,
            #     branch_id=None
            # )

        # if custom_created_at != created_at:
            # db_iteraction.change_payment_deposit(
            #     cashbox_id=cashbox_id,
            #     start_date=custom_created_at
            # )
            # if target_cashbox_id:
                # db_iteraction.change_payment_deposit(
                #     cashbox_id=target_cashbox_id,
                #     start_date=custom_created_at
                # )


        return {'success': True, 'message': f'{cashflow_category} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_payments(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400


    if request.method == 'PUT':
        db_iteraction.edit_payments(
            id=id,                          # int - id записи - полное совпаден
            cashflow_category=cashflow_category,
            description=description,
            deposit=deposit,
            income=income,
            outcome=outcome,
            direction=direction,
            can_print_fiscal=can_print_fiscal,
            deleted=deleted,
            is_fiscal=is_fiscal,
            created_at=created_at,
            custom_created_at=custom_created_at,
            tags=tags,
            relation_id=relation_id,
            cashbox_id=cashbox_id,
            client_id=client_id,
            employee_id=employee_id,
            order_id=order_id
        )

        payment = db_iteraction.get_payments(id=id)['data'][0]
        # db_iteraction.change_payment_deposit(
        #     cashbox_id=payment['cashbox']['id'],
        #     start_date=payment['custom_created_at']
        # )

        if payment['relation_id']:
            db_iteraction.edit_payments(
                id=payment['relation_id'],  # int - id записи - полное совпаден
                cashflow_category=None,
                description=None,
                deposit=None,
                income=None,
                outcome=None,
                direction=None,
                can_print_fiscal=None,
                deleted=deleted,
                is_fiscal=None,
                created_at=None,
                custom_created_at=None,
                tags=None,
                relation_id=None,
                cashbox_id=None,
                client_id=None,
                employee_id=None,
                order_id=None
            )
        #     if print_logs:
        #         print(f'Второй платеж изменен: {time.time() - start_time} сек.')
        #
        #     payment = db_iteraction.get_payments(id=payment['relation_id'])['data'][0]
        #     db_iteraction.change_payment_deposit(
        #         cashbox_id=payment['cashbox']['id'],
        #         start_date=payment['custom_created_at']
        #     )
        #     if print_logs:
        #         print(f'Балансы последующих платежей обновлены: {time.time() - start_time} сек.')

        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':

        db_iteraction.del_payments(
            id=id)  # int - id записи - полное совпаден

        # db_iteraction.change_payment_deposit(
        #     cashbox_id=payment['cashbox']['id'],
        #     start_date=payment['custom_created_at']
        # )

        if relation_id:

            db_iteraction.del_payments(
                id=relation_id)

            # db_iteraction.change_payment_deposit(
            #     cashbox_id=payment['cashbox']['id'],
            #     start_date=payment['custom_created_at']
            # )

        return {'success': True, 'message': f'{id} deleted'}, 202

@app.route('/get_payrolls', methods=['POST'])
@jwt_required()
def get_payrolls():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    direction = request_body.get('direction')
    if direction and type(direction) != int:
        return {'success': False, 'message': "direction is not integer"}, 400

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    reimburse = request_body.get('reimburse')
    if reimburse and type(reimburse) != bool:
        return {'success': False, 'message': 'reimburse is not boolean'}, 400

    custom_created_at = request_body.get('custom_created_at')
    if custom_created_at:
        if type(custom_created_at) != list:
            return {'success': False, 'message': "custom_created_at is not list"}, 400
        if len(custom_created_at) != 2:
            return {'success': False, 'message': "custom_created_at is not correct"}, 400
        if type(custom_created_at[0]) != int:
            return {'success': False, 'message': "custom_created_at has not integers"}, 400
        if type(custom_created_at[1]) and type(custom_created_at[1]) != int:
            return {'success': False, 'message': "custom_created_at has not integers"}, 400

    relation_type = request_body.get('relation_type')
    if relation_type and type(relation_type) != int:
        return {'success': False, 'message': "relation_type is not integer"}, 400

    relation_id = request_body.get('relation_id')
    if relation_id and type(relation_id) != int:
        return {'success': False, 'message': "relation_id is not integer"}, 400

    employee_id = request_body.get('employee_id')
    if employee_id and type(employee_id) != int:
        return {'success': False, 'message': "employee_id is not integer"}, 400
    if employee_id and db_iteraction.get_employee(id=employee_id)['count'] == 0:
        return {'success': False, 'message': 'employee_id is not defined'}, 400

    order_id = request_body.get('order_id')
    if order_id and type(order_id) != int:
        return {'success': False, 'message': "order_id is not integer"}, 400
    if order_id and db_iteraction.get_orders(id=order_id)['count'] == 0:
            return {'success': False, 'message': 'order_id is not defined'}, 400


    result = db_iteraction.get_payrolls(
        id=id,                                      # int - id  - полное совпадение
        direction=direction,
        deleted=deleted,
        reimburse=reimburse,
        custom_created_at=custom_created_at,
        relation_type=relation_type,
        relation_id=relation_id,
        employee_id=employee_id,
        order_id=order_id
    )
    return result, 200

@app.route('/get_payroll_sum', methods=['POST'])
@jwt_required()
def get_payroll_sum():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    custom_created_at = request_body.get('custom_created_at')
    if custom_created_at:
        if type(custom_created_at) != list:
            return {'success': False, 'message': "custom_created_at is not list"}, 400
        if len(custom_created_at) != 2:
            return {'success': False, 'message': "custom_created_at is not correct"}, 400
        if type(custom_created_at[0]) != int:
            return {'success': False, 'message': "custom_created_at has not integers"}, 400
        if type(custom_created_at[1]) and type(custom_created_at[1]) != int:
            return {'success': False, 'message': "custom_created_at has not integers"}, 400

    employee_id = request_body.get('employee_id')
    if employee_id and type(employee_id) != int:
        return {'success': False, 'message': "employee_id is not integer"}, 400
    if employee_id and db_iteraction.get_employee(id=employee_id)['count'] == 0:
        return {'success': False, 'message': 'employee_id is not defined'}, 400

    result = db_iteraction.get_payroll_sum(
        custom_created_at=custom_created_at,
        employee_id=employee_id
    )
    return {'success': True, 'sum': result}, 200

@app.route('/payroll', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
def payroll():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    description = request_body.get('description')
    if description:
        description = str(description)

    income = request_body.get('income')
    if income:
        try:
            income = float(income)
        except:
            return {'success': False, 'message': 'income is not number'}, 400

    outcome = request_body.get('outcome')
    if outcome:
        try:
            outcome = float(outcome)
        except:
            return {'success': False, 'message': 'balance is not number'}, 400

    direction = request_body.get('direction')
    if direction and type(direction) != int:
        return {'success': False, 'message': "direction is not integer"}, 400

    deleted = request_body.get('deleted')
    if deleted and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    reimburse = request_body.get('reimburse')
    if reimburse and type(reimburse) != bool:
        return {'success': False, 'message': 'reimburse is not boolean'}, 400

    created_at = request_body.get('created_at')
    if created_at and type(created_at) != int:
        return {'success': False, 'message': "created_at is not integer"}, 400

    custom_created_at = request_body.get('custom_created_at')
    if custom_created_at and type(custom_created_at) != int:
        return {'success': False, 'message': "custom_created_at is not integer"}, 400

    relation_type = request_body.get('relation_type')
    if relation_type and type(relation_type) != int:
        return {'success': False, 'message': "relation_type is not integer"}, 400

    relation_id = request_body.get('relation_id')
    if relation_id and type(relation_id) != int:
        return {'success': False, 'message': "relation_id is not integer"}, 400

    employee_id = request_body.get('employee_id')
    if employee_id and type(employee_id) != int:
        return {'success': False, 'message': "employee_id is not integer"}, 400
    if employee_id and db_iteraction.get_employee(id=employee_id)['count'] == 0:
        return {'success': False, 'message': 'employee_id is not defined'}, 400

    order_id = request_body.get('order_id')
    if order_id and type(order_id) != int:
        return {'success': False, 'message': "order_id is not integer"}, 400
    if order_id and db_iteraction.get_orders(id=order_id)['count'] == 0:
        return {'success': False, 'message': 'order_id is not defined'}, 400


    if request.method == 'POST':
        id = db_iteraction.add_payroll(
            description=description,
            income=income,
            outcome=outcome,
            direction=direction,
            deleted=deleted,
            reimburse=reimburse,
            created_at=created_at,
            custom_created_at=custom_created_at,
            relation_type=relation_type,
            relation_id=relation_id,
            employee_id=employee_id,
            order_id=order_id
        )

        return {'success': True, 'message': f'{id} added'}, 201

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_payrolls(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400


    if request.method == 'PUT':
        db_iteraction.edit_payroll(
            id=id,                          # int - id записи - полное совпаден
            description=description,
            income=income,
            outcome=outcome,
            direction=direction,
            deleted=deleted,
            reimburse=reimburse,
            custom_created_at=custom_created_at,
            relation_id=relation_id,
            relation_type=relation_type,
            employee_id=employee_id,
            order_id=order_id
        )

        return {'success': True, 'message': f'{id} changed'}, 202

    if request.method == 'DELETE':

        db_iteraction.del_payroll(
            id=id)  # int - id записи - полное совпаден

        return {'success': True, 'message': f'{id} deleted'}, 202

@app.route('/get_payrules', methods=['POST'])
@jwt_required()
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
        id=id,                                      # int - id  - полное совпадение
        title=title,
        type_rule=type_rule,
        deleted=deleted,
        employee_id=employee_id
    )
    return result, 200

@app.route('/payrule', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
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
            id=id,                          # int - id записи - полное совпаден
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
@jwt_required()
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
        id=id,                                      # int - id  - полное совпадение
        title=title,
        deleted=deleted
    )
    return result, 200

@app.route('/group_dict_service', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
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
            id=id,                          # int - id записи - полное совпаден
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
@jwt_required()
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
        id=id,                                      # int - id  - полное совпадение
        title=title,
        warranty=warranty,
        code=code,
        deleted=deleted,
        category_id=category_id
    )
    return result, 200

@app.route('/dict_service', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
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
            id=id,                          # int - id записи - полное совпаден
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
@jwt_required()
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
        id=id,                                      # int - id  - полное совпадение
        discount_margin_id=discount_margin_id,
        service_id=service_id,
        deleted=deleted
    )
    return result, 200

@app.route('/service_prices', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
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
@jwt_required()
def get_parts():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page',  0)
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
        id=id,                                      # int - id  - полное совпадение
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
@jwt_required()
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
            id=id,                          # int - id записи - полное совпаден
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
@jwt_required()
def get_warehouse():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page',  0)
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
        id=id,                                      # int - id  - полное совпадение
        title=title,
        branch_id=branch_id,
        isGlobal=isGlobal,
        deleted=deleted,
        page=page
    )
    return result, 200

@app.route('/warehouse', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
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
            id=id,                          # int - id записи - полное совпаден
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
@jwt_required()
def get_warehouse_category():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page',  0)
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
@jwt_required()
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
@jwt_required()
def get_warehouse_parts():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page',  0)
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
@jwt_required()
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
@jwt_required()
def get_notification_template():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page',  0)
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
@jwt_required()
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
@jwt_required()
def get_notification_events():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page',  0)
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
@jwt_required()
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

app.add_url_rule('/login', view_func=login, methods=['POST'])




class UserLogin:

    def __init__(self):
        self.db_iteraction = db_iteraction

    def fromDB(self, user_id):
        self.__user = self.db_iteraction.get_employee(id=user_id)['data'][0]
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
        return str(self.__user['id'])



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