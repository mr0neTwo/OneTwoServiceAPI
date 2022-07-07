from flask import Blueprint
from flask_jwt_extended import jwt_required, decode_token
from flask import request
from flask_login import login_required, current_user

from app.db.interaction.db_iteraction import db_iteraction
from app.db.models.models import Branch, Cashboxs

cashboxes_api = Blueprint('cashboxes_api', __name__)

@cashboxes_api.route('/get_cashbox', methods=['POST'])
@login_required
def get_cashbox():
    user_id = current_user.get_id()

    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id is not None and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    deleted = request_body.get('deleted')
    if deleted is not None and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    branch_id = request_body.get('branch_id')
    if branch_id is not None and type(branch_id) != int:
        return {'success': False, 'message': "branch_id is not integer"}, 400
    if branch_id is not None and not db_iteraction.pgsql_connetction.session.query(Branch).get(branch_id):
        return {'success': False, 'message': 'branch_id is not defined'}, 400

    result = db_iteraction.get_cashbox(
        id=id,                            # int - id  - полное совпадение
        deleted=deleted,
        branch_id=branch_id,
        user_id=user_id
    )
    return result


@cashboxes_api.route('/cashbox', methods=['POST', 'PUT', 'DELETE'])
@login_required
def cashbox():
    user_id = current_user.get_id()

    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id is not None and type(id) != int:
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
    if types is not None and type(types) != int:
        return {'success': False, 'message': "types is not integer"}, 400

    isGlobal = request_body.get('isGlobal')
    if isGlobal is not None and type(isGlobal) != bool:
        return {'success': False, 'message': 'isGlobal is not boolean'}, 400

    isVirtual = request_body.get('isVirtual')
    if isVirtual is not None and type(isVirtual) != bool:
        return {'success': False, 'message': 'isVirtual is not boolean'}, 400

    deleted = request_body.get('deleted')
    if deleted is not None and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    permissions = request_body.get('permissions')
    if permissions is not None and type(permissions) != list:
        return {'success': False, 'message': "permissions is not list"}, 400
    if permissions is not None:
        if not all([type(permission) == str for permission in permissions]):
            return {'success': False, 'message': "permissions has not string"}, 400

    employees = request_body.get('employees')
    # if employees and type(employees) != list:
    #     return {'success': False, 'message': "employees is not list"}, 400
    # if employees:
    #     if not all([type(employee) == int for employee in employees]):
    #         return {'success': False, 'message': "employees has not integer"}, 400

    branch_id = request_body.get('branch_id')
    if branch_id is not None and type(branch_id) != int:
        return {'success': False, 'message': "branch_id is not integer"}, 400
    if branch_id is not None and not db_iteraction.pgsql_connetction.session.query(Branch).get(branch_id):
        return {'success': False, 'message': 'branch_id is not defined'}, 400

    cashbox_filter = request_body.get('filter')
    if cashbox_filter:

        if cashbox_filter.get('deleted') is not None and type(cashbox_filter['deleted']) != bool:
            return {'success': False, 'message': 'deleted in cashbox_filter is not boolean'}, 400

        if cashbox_filter.get('branch_id') is not None:
            if type(cashbox_filter['branch_id']) != int:
                return {'success': False, 'message': 'branch_id is not integer in cashbox_filter'}, 400
            if not db_iteraction.pgsql_connetction.session.query(Branch).get(cashbox_filter['branch_id']):
                return {'success': False, 'message': 'branch_id is not defined in cashbox_filter'}, 400


    if request.method == 'POST':
        result = db_iteraction.add_cashbox(
            title=title,
            balance=balance,
            type=types,
            isGlobal=isGlobal,
            isVirtual=isVirtual,
            deleted=deleted,
            permissions=permissions,
            employees=employees,
            branch_id=branch_id,
            user_id=user_id,
            cashbox_filter=cashbox_filter
        )

        return result

    # Проверим сущестует ли запись по данному id
    if not db_iteraction.pgsql_connetction.session.query(Cashboxs).get(id):
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        result = db_iteraction.edit_cashbox(
            id=id,              # int - id записи - полное совпаден
            title=title,
            balance=balance,
            type=types,
            isGlobal=isGlobal,
            isVirtual=isVirtual,
            deleted=deleted,
            permissions=permissions,
            employees=employees,
            branch_id=branch_id,
            user_id=user_id,
            cashbox_filter=cashbox_filter
        )
        return result

    if request.method == 'DELETE':
        return db_iteraction.del_cashbox(id=id)       # int - id записи - полное совпаден
