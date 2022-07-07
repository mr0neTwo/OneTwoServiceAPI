from flask import Blueprint
from flask import request
from flask_login import login_required
from werkzeug.security import generate_password_hash

from app.db.interaction.db_iteraction import db_iteraction
from app.db.models.models import Branch, Employees, Roles

employees_api = Blueprint('employees_api', __name__)

@employees_api.route('/get_employee', methods=['POST'])
@login_required
def get_employee():

    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id is not None and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page is not None and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    deleted = request_body.get('deleted', False)
    if deleted is not None and type(deleted) != bool:
        return {'success': False, 'message': "deleted is not boolean"}, 400


    result = db_iteraction.get_employee(
        id=id,  # int - id сотрудника - полное совпадение
        deleted=deleted,  # bool - Статус удален сотрудника
        page=page  # int - Старница погинации
    )
    return result


@employees_api.route('/employee', methods=['POST', 'PUT', 'DELETE'])
@login_required
def employee():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id is not None and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page is not None and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    first_name = request_body.get('first_name')
    if first_name is not None:
        first_name = str(first_name)

    last_name = request_body.get('last_name')
    if last_name is not None:
        last_name = str(last_name)

    email = request_body.get('email')
    if email is not None:
        email = str(email)

    login = request_body.get('login')
    if login is not None:
        login = str(login)

    phone = request_body.get('phone')
    if phone is not None:
        phone = str(phone)

    notes = request_body.get('notes')
    if notes is not None:
        notes = str(notes)

    inn = request_body.get('inn')
    if inn is not None:
        inn = str(inn)

    doc_name = request_body.get('doc_name')
    if doc_name is not None:
        doc_name = str(doc_name)

    post = request_body.get('post')
    if post is not None:
        post = str(post)

    avatar = request_body.get('avatar')
    if avatar is not None:
        avatar = str(avatar)

    deleted = request_body.get('deleted', False)
    if deleted is not None and type(deleted) != bool:
        return {'success': False, 'message': "deleted is not boolean"}, 400

    permissions = request_body.get('permissions')
    if permissions is not None and type(permissions) != list:
        return {'success': False, 'message': "permissions is not list"}, 400
    if permissions is not None:
        if not all([type(permission) == str for permission in permissions]):
            return {'success': False, 'message': "permissions has not string"}, 400

    role_id = request_body.get('role_id')
    if role_id is not None:
        if type(role_id) != int:
            return {'success': False, 'message': "role_id is not integer"}, 400
        if not db_iteraction.pgsql_connetction.session.query(Roles).get(role_id):
            return {'success': False, 'message': "employee_id is not defined"}, 400

    password = request_body.get('password')
    if password is not None:
        password = str(password)

    img = request_body.get('img')
    filter_employees = request_body.get('filter')

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

        result = db_iteraction.add_employee(
            first_name=first_name,  # str - Имя сотрудника
            last_name=last_name,  # str - Фамилия сотрудника
            email=email,  # str - Электронная почта сотрудника - уникальное значение
            phone=phone,  # str - Телфон сотрудника
            notes=notes,  # str - Заметки
            deleted=deleted,  # bool - Статус удален
            inn=inn,
            doc_name=doc_name,
            post=post,
            permissions=permissions,
            role_id=role_id,  # str - Роль сотрудника
            login=login,  # str - Логин сотрудника - уникальное значение
            password=generate_password_hash(password),  # str - Пароль сотрудника - обязательное поле,
            filter_employees=filter_employees
        )
        return result

    # Проверим сущестует ли запись по данному id
    employee = db_iteraction.pgsql_connetction.session.query(Employees).get(id)
    if not employee:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':

        if email is not None and employee.email != email:
            if db_iteraction.pgsql_connetction.session.query(Employees).filter_by(email=email).first():
                return {'success': False, 'message': 'there is the same email'}, 400

        if login and employee.login != login:
            if db_iteraction.pgsql_connetction.session.query(Employees).filter_by(login=login).first():
                return {'success': False, 'message': 'there is the same login'}, 400

        result = db_iteraction.edit_employee(
            id=id,  # int - ID сотрудника -  полное совпадение
            first_name=first_name,  # str - Новое имя сотрудника
            last_name=last_name,  # str - Новая фамилия сотрудника
            email=email,  # str - Новый email сотрудника
            phone=phone,  # str - Новый телефон сотрудника
            notes=notes,  # str - Новый коментарий к сотруднику
            deleted=deleted,  # str - Статус удален сотрудника
            inn=inn,
            doc_name=doc_name,
            post=post,
            login=login,  # str - Новый логин
            role_id=role_id,  # str - Новая роль сотрудника
            permissions=permissions,
            # password=generate_password_hash(password)   # str - Пароль сотрудника - обязательное поле,
            filter_employees=filter_employees
        )
        return result

    if request.method == 'DELETE':
        return db_iteraction.del_employee(id=id)  # int - id сотрудника - полное совпадение


@employees_api.route('/change_userpassword', methods=['PUT'])
@login_required
def change_userpassword():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    # Проверим является ли id числом
    id = request_body.get('id')
    if id is not None and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    if not db_iteraction.pgsql_connetction.session.query(Employees).get(id):
        return {'success': False, 'message': 'id is not defined'}, 400

    password = request_body.get('password')
    if not password:
        return {'success': False, 'message': 'password required'}, 400

    password = str(password)

    if len(password) < 6:
        return {'success': False, 'message': 'password is short'}, 400

    if request.method == 'PUT':
        result = db_iteraction.cange_userpassword(
            id=id,
            password=password
        )
        return result

@employees_api.route('/change_avatar', methods=['POST'])
@login_required
def change_avatar():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400


    employee_id = request_body.get('employee_id')
    if employee_id is not None and type(employee_id) != int:
        return {'success': False, 'message': "employee_id is not integer"}, 400

    if not db_iteraction.pgsql_connetction.session.query(Employees).get(employee_id):
        return {'success': False, 'message': 'employee_id is not defined'}, 400

    left = request_body.get('left')
    if left is not None and type(left) != int:
        return {'success': False, 'message': "left is not integer"}, 400

    top = request_body.get('top')
    if top is not None and type(top) != int:
        return {'success': False, 'message': "top is not integer"}, 400

    size = request_body.get('size')
    if size is not None:
        if type(size) != list:
            return {'success': False, 'message': "size is not size"}, 400
        if type(size[0]) != int and type(size[1]) != int:
            return {'success': False, 'message': "size has not integer"}, 400

    img = request_body.get('img')

    if request.method == 'POST':
        result = db_iteraction.change_avatar(
            employee_id=employee_id,
            left=left,
            top=top,
            size=size,
            img=img
        )
        return result