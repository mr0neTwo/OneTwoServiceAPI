from flask import Blueprint
from flask_jwt_extended import jwt_required, decode_token
from flask import request
from flask_login import login_required, current_user

from app.db.interaction.db_iteraction import db_iteraction
from app.db.models.models import Cashboxs, Clients, Employees, Orders, Payments, Status

payment_api = Blueprint('payment_api', __name__)

@payment_api.route('/get_payments', methods=['POST'])
@login_required
def get_payments():

    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id is not None and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    direction = request_body.get('direction')
    if direction is not None and type(direction) != int:
        return {'success': False, 'message': "direction is not integer"}, 400

    deleted = request_body.get('deleted')
    if deleted is not None and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

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

    tags = request_body.get('tags')
    if tags is not None:
        tags = str(tags)

    cashbox_id = request_body.get('cashbox_id')
    if cashbox_id is not None and type(cashbox_id) != int:
        return {'success': False, 'message': "cashbox_id is not integer"}, 400
    if cashbox_id is not None and not db_iteraction.pgsql_connetction.session.query(Cashboxs).get(cashbox_id):
        return {'success': False, 'message': 'cashbox_id is not defined'}, 400

    client_id = request_body.get('client_id')
    if client_id is not None and type(client_id) != int:
        return {'success': False, 'message': "client_id is not integer"}, 400
    if client_id is not None and not db_iteraction.pgsql_connetction.session.query(Clients).get(client_id):
        return {'success': False, 'message': 'client_id is not defined'}, 400

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

    result = db_iteraction.get_payments(
        id=id,                                      # int - id  - полное совпадение
        direction=direction,
        deleted=deleted,
        custom_created_at=custom_created_at,
        tags=tags,
        cashbox_id=cashbox_id,
        client_id=client_id,
        employee_id=employee_id,
        order_id=order_id
    )

    return result

@payment_api.route('/payments', methods=['POST', 'PUT', 'DELETE'])
@login_required
def payments():
    user_id = current_user.get_id()

    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id is not None and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    cashflow_category = request_body.get('cashflow_category')
    if cashflow_category is not None:
        cashflow_category = str(cashflow_category)

    description = request_body.get('description')
    if description is not None:
        description = str(description)

    deposit = request_body.get('deposit')
    if deposit is not None:
        try:
            deposit = float(deposit)
        except:
            return {'success': False, 'message': 'deposit is not number'}, 400

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

    can_print_fiscal = request_body.get('can_print_fiscal')
    if can_print_fiscal is not None and type(can_print_fiscal) != bool:
        return {'success': False, 'message': 'can_print_fiscal is not boolean'}, 400

    is_fiscal = request_body.get('is_fiscal')
    if is_fiscal is not None and type(is_fiscal) != bool:
        return {'success': False, 'message': 'is_fiscal is not boolean'}, 400

    deleted = request_body.get('deleted')
    if deleted is not None and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    created_at = request_body.get('created_at')
    if created_at is not None and type(created_at) != int:
        return {'success': False, 'message': "created_at is not integer"}, 400

    custom_created_at = request_body.get('custom_created_at')
    if custom_created_at is not None and type(custom_created_at) != int:
        return {'success': False, 'message': "custom_created_at is not integer"}, 400

    tags = request_body.get('tags')
    if tags is not None and type(tags) != list:
        return {'success': False, 'message': "tags is not list"}, 400
    if tags is not None:
        if not all([type(tag) == str for tag in tags]):
            return {'success': False, 'message': "tags has not string"}, 400

    relation_type = request_body.get('relation_type')
    if relation_type is not None and type(relation_type) != int:
        return {'success': False, 'message': "relation_type is not integer"}, 400

    relation_id = request_body.get('relation_id')
    if relation_id is not None and type(relation_id) != int:
        return {'success': False, 'message': "relation_id is not integer"}, 400

    cashbox_id = request_body.get('cashbox_id')
    if cashbox_id is not None and type(cashbox_id) != int:
        return {'success': False, 'message': "cashbox_id is not integer"}, 400
    if cashbox_id is not None and not db_iteraction.pgsql_connetction.session.query(Cashboxs).get(cashbox_id):
        return {'success': False, 'message': 'cashbox_id is not defined'}, 400

    target_cashbox_id = request_body.get('target_cashbox_id')
    if target_cashbox_id is not None and type(target_cashbox_id) != int:
        return {'success': False, 'message': "target_cashbox_id is not integer"}, 400
    if target_cashbox_id is not None and not db_iteraction.pgsql_connetction.session.query(Cashboxs).get(target_cashbox_id):
        return {'success': False, 'message': 'target_cashbox_id is not defined'}, 400

    client_id = request_body.get('client_id')
    if client_id is not None and type(client_id) != int:
        return {'success': False, 'message': "client_id is not integer"}, 400
    if client_id is not None and not db_iteraction.pgsql_connetction.session.query(Clients).get(client_id):
        return {'success': False, 'message': 'client_id is not defined'}, 400

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

    filter_payments = request_body.get('filter_payments')
    if filter_payments:
        if filter_payments.get('custom_created_at'):
            if type(filter_payments['custom_created_at']) != list:
                return {'success': False, 'message': "custom_created_at is not list"}, 400
            if len(filter_payments['custom_created_at']) != 2:
                return {'success': False, 'message': "custom_created_at is not correct"}, 400
            if type(filter_payments['custom_created_at'][0]) != int:
                return {'success': False, 'message': "custom_created_at has not integers"}, 400
            if type(filter_payments['custom_created_at'][1]) != int:
                return {'success': False, 'message': "custom_created_at has not integers"}, 400

        if filter_payments.get('cashbox_id') is not None:
            if type(filter_payments['cashbox_id']) != int:
                return {'success': False, 'message': "cashbox_id is not integer"}, 400
            if not db_iteraction.pgsql_connetction.session.query(Cashboxs).get(filter_payments['cashbox_id']):
                return {'success': False, 'message': 'cashbox_id is not defined'}, 400

        if filter_payments.get('tags') is not None:
            if type(filter_payments['tags']) != str:
                filter_payments['tags'] = str(filter_payments['tags'])

        if filter_payments.get('deleted') is not None:
            if type(filter_payments['deleted']) != bool:
                return {'success': False, 'message': 'deleted is not boolean'}, 400

    filter_cashboxes = request_body.get('filter_cashboxes')
    if filter_cashboxes:
        if filter_cashboxes.get('deleted') is not None:
            if type(filter_cashboxes['deleted']) != bool:
                return {'success': False, 'message': 'deleted is not boolean'}, 400

    closed_order = request_body.get('closed_order')
    if closed_order:
        if closed_order.get('order_id') is not None:
            if type(closed_order['order_id']) != int:
                return {'success': False, 'message': "order_id is not integer"}, 400
            if not db_iteraction.pgsql_connetction.session.query(Orders).get(closed_order['order_id']):
                return {'success': False, 'message': 'order_id is not defined'}, 400

        if closed_order.get('status_id') is not None:
            if type(closed_order['status_id']) != int:
                return {'success': False, 'message': "status_id is not integer"}, 400
            if not db_iteraction.pgsql_connetction.session.query(Status).get(closed_order['status_id']):
                return {'success': False, 'message': 'status_id is not defined'}, 400

    filter_order = request_body.get('filter_order') or (closed_order.get('filter') if closed_order else None)
    if filter_order:

        if filter_order.get('sort'):
            filter_order['sort'] = str(filter_order['sort'])

        if filter_order.get('field_sort'):
            filter_order['field_sort'] = str(filter_order['field_sort'])

        if filter_order.get('search'):
            filter_order['search'] = str(filter_order['search'])

        if filter_order.get('page') is not None and type(filter_order['page']) != int:
            return {'success': False, 'message': "page is not integer"}, 400

        if filter_order.get('kindof_good_id') is not None and type(filter_order['kindof_good_id']) != int:
            return {'success': False, 'message': "kindof_good_id is not integer"}, 400

        if filter_order.get('brand_id') is not None and type(filter_order['brand_id']) != int:
            return {'success': False, 'message': "brand_id is not integer"}, 400

        if filter_order.get('subtype_id') is not None and type(filter_order['subtype_id']) != int:
            return {'success': False, 'message': "subtype_id is not integer"}, 400

        if filter_order.get('client_id') is not None and type(filter_order['client_id']) != int:
            return {'success': False, 'message': "client_id is not integer"}, 400

        if filter_order.get('update_order') is not None and type(filter_order['update_order']) != int:
            return {'success': False, 'message': "update_order is not integer"}, 400

        if filter_order.get('created_at') is not None:
            if type(filter_order['created_at']) != list:
                return {'success': False, 'message': "created_at is not list"}, 400
            if len(filter_order['created_at']) != 2:
                return {'success': False, 'message': "created_at is not correct"}, 400
            if (type(filter_order['created_at'][0]) != int) or (type(filter_order['created_at'][1]) != int):
                return {'success': False, 'message': "created_at has not integers"}, 400

        if filter_order.get('engineer_id') is not None:
            if type(filter_order['engineer_id']) != list:
                return {'success': False, 'message': "engineer_id is not list"}, 400
            if not all([type(engineer) == int for engineer in filter_order['engineer_id']]):
                return {'success': False, 'message': "engineer_id has not integer"}, 400

        if filter_order.get('status_id') is not None:
            if type(filter_order['status_id']) != list:
                return {'success': False, 'message': "status_id is not list"}, 400
            if not all([type(status) == int for status in filter_order['status_id']]):
                return {'success': False, 'message': "status_id has not integer"}, 400

        if filter_order.get('order_type_id') is not None:
            if type(filter_order['order_type_id']) != list:
                return {'success': False, 'message': "order_type_id is not list"}, 400
            if not all([type(order_type) == int for order_type in filter_order['order_type_id']]):
                return {'success': False, 'message': "order_type_id has not integer"}, 400

        if filter_order.get('manager_id') is not None:
            if type(filter_order['manager_id']) != list:
                return {'success': False, 'message': "manager_id is not list"}, 400
            if not all([type(manager) == int for manager in filter_order['manager_id']]):
                return {'success': False, 'message': "manager_id has not integer"}, 400

        if filter_order.get('overdue') is not None and type(filter_order['overdue']) != bool:
            return {'success': False, 'message': "overdue is not boolean"}, 400

        if filter_order.get('status_overdue') is not None and type(filter_order['status_overdue']) != bool:
            return {'success': False, 'message': "status_overdue is not boolean"}, 400

        if filter_order.get('urgent') is not None and type(filter_order['urgent']) != bool:
            return {'success': False, 'message': "urgent is not boolean"}, 400

        if filter_order.get('update_badges') is not None and type(filter_order['update_badges']) != bool:
            return {'success': False, 'message': "update_badges is not boolean"}, 400


    if request.method == 'POST':
        result = db_iteraction.add_payments(
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
            relation_type=relation_type,
            relation_id=None,
            cashbox_id=cashbox_id,
            client_id=client_id,
            employee_id=employee_id,
            order_id=order_id,
            target_cashbox_id=target_cashbox_id,
            user_id=user_id,
            filter_payments=filter_payments,
            filter_cashboxes=filter_cashboxes,
            filter_order=filter_order,
            closed_order=closed_order
        )

        return result

    # Проверим сущестует ли запись по данному id
    if not db_iteraction.pgsql_connetction.session.query(Payments).get(id):
        return {'success': False, 'message': 'id is not defined'}, 400


    if request.method == 'PUT':
        result = db_iteraction.edit_payments(
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
            relation_type=relation_type,
            relation_id=relation_id,
            cashbox_id=cashbox_id,
            client_id=client_id,
            employee_id=employee_id,
            order_id=order_id,
            filter_payments=filter_payments,
            filter_cashboxes=filter_cashboxes,
            filter_order=filter_order
        )

        return result

    if request.method == 'DELETE':

        return db_iteraction.del_payments(id=id)  # int - id записи - полное совпаден

