from flask import Blueprint
from flask_jwt_extended import jwt_required, decode_token
from flask import request

from app.db.interaction.db_iteraction import db_iteraction
from app.db.models.models import Employees, Orders, Payrolls

payrolls_api = Blueprint('payrolls_api', __name__)

@payrolls_api.route('/get_payrolls', methods=['POST'])
@jwt_required()
def get_payrolls():
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
    if employee_id is not None and type(employee_id) != int:
        return {'success': False, 'message': "employee_id is not integer"}, 400
    if employee_id is not None and not db_iteraction.pgsql_connetction.session.query(Employees).get(employee_id):
        return {'success': False, 'message': 'employee_id is not defined'}, 400

    result = db_iteraction.get_payrolls(
        id=id,  # int - id  - полное совпадение
        deleted=deleted,
        custom_created_at=custom_created_at,
        employee_id=employee_id,
    )
    return result


@payrolls_api.route('/get_payroll_sum', methods=['POST'])
@jwt_required()
def get_payroll_sum():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    custom_created_at = request_body.get('custom_created_at')
    if custom_created_at is not None:
        if type(custom_created_at) != list:
            return {'success': False, 'message': "custom_created_at is not list"}, 400
        if len(custom_created_at) != 2:
            return {'success': False, 'message': "custom_created_at is not correct"}, 400
        if type(custom_created_at[0]) != int:
            return {'success': False, 'message': "custom_created_at has not integers"}, 400
        if type(custom_created_at[1]) and type(custom_created_at[1]) != int:
            return {'success': False, 'message': "custom_created_at has not integers"}, 400

    employee_id = request_body.get('employee_id')
    if employee_id is not None and type(employee_id) != int:
        return {'success': False, 'message': "employee_id is not integer"}, 400
    if employee_id is not None and not db_iteraction.pgsql_connetction.session.query(Employees).get(employee_id):
        return {'success': False, 'message': 'employee_id is not defined'}, 400

    result = db_iteraction.get_payroll_sum(
        custom_created_at=custom_created_at,
        employee_id=employee_id
    )
    return result


@payrolls_api.route('/payroll', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
def payroll():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id is not None and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    description = request_body.get('description')
    if description is not None:
        description = str(description)

    income = request_body.get('income')
    if income is not None:
        try:
            income = float(income)
        except:
            return {'success': False, 'message': 'income is not number'}, 400

    outcome = request_body.get('outcome')
    if outcome is not None:
        try:
            outcome = float(outcome)
        except:
            return {'success': False, 'message': 'balance is not number'}, 400

    direction = request_body.get('direction')
    if direction is not None and type(direction) != int:
        return {'success': False, 'message': "direction is not integer"}, 400

    deleted = request_body.get('deleted')
    if deleted is not None and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    reimburse = request_body.get('reimburse')
    if reimburse is not None and type(reimburse) != bool:
        return {'success': False, 'message': 'reimburse is not boolean'}, 400

    created_at = request_body.get('created_at')
    if created_at is not None and type(created_at) != int:
        return {'success': False, 'message': "created_at is not integer"}, 400

    custom_created_at = request_body.get('custom_created_at')
    if custom_created_at is not None and type(custom_created_at) != int:
        return {'success': False, 'message': "custom_created_at is not integer"}, 400

    relation_type = request_body.get('relation_type')
    if relation_type is not None and type(relation_type) != int:
        return {'success': False, 'message': "relation_type is not integer"}, 400

    relation_id = request_body.get('relation_id')
    if relation_id is not None and type(relation_id) != int:
        return {'success': False, 'message': "relation_id is not integer"}, 400

    employee_id = request_body.get('employee_id')
    if employee_id is not None and type(employee_id) != int:
        return {'success': False, 'message': "employee_id is not integer"}, 400
    if employee_id is not None and not db_iteraction.pgsql_connetction.session.query(Employees).get(employee_id):
        return {'success': False, 'message': 'employee_id is not defined'}, 400

    order_id = request_body.get('order_id')
    if order_id is not None and type(order_id) != int:
        return {'success': False, 'message': "order_id is not integer"}, 400
    if order_id is not None and not db_iteraction.pgsql_connetction.session.query(Orders).get(order_id):
        return {'success': False, 'message': 'order_id is not defined'}, 400

    payroll_filter = request_body.get('filter')
    if payroll_filter:

        if payroll_filter.get('deleted') is not None and type(payroll_filter['deleted']) != bool:
            return {'success': False, 'message': 'deleted is not boolean in payroll_filter'}, 400

        if payroll_filter.get('employee_id') is not None:
            if type(payroll_filter['employee_id']) != int:
                return {'success': False, 'message': "employee_id is not integer in payroll_filter"}, 400
            if not db_iteraction.pgsql_connetction.session.query(Employees).get(payroll_filter['employee_id']):
                return {'success': False, 'message': 'employee_id is not defined in payroll_filter'}, 400

        if payroll_filter.get('custom_created_at') is not None:
            if type(payroll_filter['custom_created_at']) != list:
                return {'success': False, 'message': "custom_created_at is not list in payroll_filter"}, 400
            if len(payroll_filter['custom_created_at']) != 2:
                return {'success': False, 'message': "custom_created_at is not correct in payroll_filter"}, 400
            if type(payroll_filter['custom_created_at'][0]) != int:
                return {'success': False, 'message': "custom_created_at has not integers in payroll_filter"}, 400
            if type(payroll_filter['custom_created_at'][1]) and type(payroll_filter['custom_created_at'][1]) != int:
                return {'success': False, 'message': "custom_created_at has not integers in payroll_filter"}, 400

    payment = request_body.get('payment')


    if request.method == 'POST':
        result = db_iteraction.add_payroll(
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
            order_id=order_id,
            payroll_filter=payroll_filter,
            payment=payment
        )

        return result

    # Проверим сущестует ли запись по данному id
    if not db_iteraction.pgsql_connetction.session.query(Payrolls).get(id):
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        result = db_iteraction.edit_payroll(
            id=id,  # int - id записи - полное совпаден
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
            order_id=order_id,
            payroll_filter=payroll_filter
        )

        return result

    if request.method == 'DELETE':
        return db_iteraction.del_payroll(id=id)  # int - id записи - полное совпаден

