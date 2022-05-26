from flask import Blueprint
from flask_jwt_extended import jwt_required, decode_token
from flask import request

from app.db.interaction.db_iteraction import db_iteraction
from app.db.models.models import Branch, Cashboxs, Employees

branches_api = Blueprint('branches_api', __name__)

@branches_api.route('/get_branch', methods=['POST'])
@jwt_required()
def get_branch():
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

    deleted = request_body.get('deleted')
    if deleted is not None and type(deleted) != bool:
        return {'success': False, 'message': "deleted is not boolean"}, 400

    employee_id = request_body.get('employee_id')
    if employee_id is not None:
        if type(employee_id) != int:
            return {'success': False, 'message': "employee_id is not integer"}, 400
        if not db_iteraction.pgsql_connetction.session.query(Employees).get(employee_id):
            return {'success': False, 'message': "employee_id is not defined"}, 400

    result = db_iteraction.get_branch(
        id=id,  # int - id филиала - полное совпадение
        deleted=deleted,
        employee_id=employee_id,
        page=page  # int - Старница погинации
    )
    return result


@branches_api.route('/branch', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
def branch():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id is not None and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    name = request_body.get('name')
    if name is not None:
        name = str(name)

    color = request_body.get('color')
    if color is not None:
        color = str(color)

    address = request_body.get('address')
    if address is not None:
        address = str(address)

    phone = request_body.get('phone')
    if phone is not None:
        phone = str(phone)

    icon = request_body.get('icon')
    if icon is not None:
        icon = str(icon)

    orders_type_id = request_body.get('orders_type_id')
    if orders_type_id is not None and type(orders_type_id) != int:
        return {'success': False, 'message': "orders_type_id is not integer"}, 400

    orders_type_strategy = request_body.get('orders_type_strategy')
    if orders_type_strategy is not None:
        orders_type_strategy = str(orders_type_strategy)

    orders_prefix = request_body.get('orders_prefix')
    if orders_prefix is not None:
        orders_prefix = str(orders_prefix)

    documents_prefix = request_body.get('documents_prefix')
    if documents_prefix is not None:
        documents_prefix = str(documents_prefix)

    employees = request_body.get('employees')
    if employees is not None and type(employees) != list:
        return {'success': False, 'message': "employees is not list"}, 400
    if employees is not None:
        if not all([type(employee) == int for employee in employees]):
            return {'success': False, 'message': "employees has not integer"}, 400

    deleted = request_body.get('deleted')
    if deleted is not None and type(deleted) != bool:
        return {'success': False, 'message': "deleted is not boolean"}, 400

    schedule = request_body.get('schedule')

    branch_filter = request_body.get('filter')
    if branch_filter:

        if branch_filter.get('employee_id') is not None:
            if type(branch_filter['employee_id']) != int:
                return {'success': False, 'message': "employee_id is not integer in branch_filter"}, 400
            if not db_iteraction.pgsql_connetction.session.query(Employees).get(branch_filter['employee_id']):
                return {'success': False, 'message': "employee_id is not defined in branch_filter"}, 400

        if branch_filter.get('deleted') is not None and type(branch_filter['deleted']) != bool:
            return {'success': False, 'message': "deleted is not boolean in branch_filter"}, 400

    if request.method == 'POST':

        if not name:
            return {'success': False, 'message': 'name required'}, 400

        result = db_iteraction.add_branch(
            name=name,  # str - Название филиала - обязательное поле
            color=color,
            address=address,
            phone=phone,
            icon=icon,
            orders_type_id=orders_type_id,
            orders_type_strategy=orders_type_strategy,
            orders_prefix=orders_prefix,
            documents_prefix=documents_prefix,
            employees=employees,
            deleted=deleted,
            schedule=schedule,
            branch_filter=branch_filter
        )

        return result

    # Проверим сущестует ли запись по данному id
    if not db_iteraction.pgsql_connetction.session.query(Branch).get(id):
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        result = db_iteraction.edit_branch(
            id=id,  # int - id записи - полное совпаден
            name=name,  # str - Новое название филиала
            color=color,
            address=address,
            phone=phone,
            icon=icon,
            orders_type_id=orders_type_id,
            orders_type_strategy=orders_type_strategy,
            orders_prefix=orders_prefix,
            documents_prefix=documents_prefix,
            employees=employees,
            deleted=deleted,
            schedule=schedule,
            branch_filter=branch_filter
        )

        return result

    if request.method == 'DELETE':

        return db_iteraction.del_branch(id=id)  # int - id записи - полное совпаден