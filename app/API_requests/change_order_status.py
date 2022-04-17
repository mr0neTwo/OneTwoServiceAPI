from flask import Blueprint
from flask_jwt_extended import jwt_required, decode_token
from flask import request

from app.db.interaction.db_iteraction import db_iteraction

change_status_api = Blueprint('change_status_api', __name__)

@change_status_api.route('/change_order_status', methods=['POST'])
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
        return {'success': False, 'message': "Request don't has json body"}, 400

    order_id = request_body.get('order_id')
    if not order_id:
        return {'success': False, 'message': 'order_id required'}, 400
    if order_id and type(order_id) != int:
        return {'success': False, 'message': "order_id is not integer"}, 400

    status_id = request_body.get('status_id')
    if not status_id:
        return {'success': False, 'message': 'status_id required'}, 400
    if type(status_id) != int:
        return {'success': False, 'message': "status_id is not integer"}, 400

    r_filter = request_body.get('filter')
    if r_filter:

        if r_filter.get('sort'):
            r_filter['sort'] = str(r_filter['sort'])

        if r_filter.get('field_sort'):
            r_filter['field_sort'] = str(r_filter['field_sort'])

        if r_filter.get('search'):
            r_filter['search'] = str(r_filter['search'])

        if r_filter.get('page') is not None and type(r_filter['page']) != int:
            return {'success': False, 'message': "page is not integer"}, 400

        if r_filter.get('kindof_good_id') is not None and type(r_filter['kindof_good_id']) != int:
            return {'success': False, 'message': "kindof_good_id is not integer"}, 400

        if r_filter.get('brand_id') is not None and type(r_filter['brand_id']) != int:
            return {'success': False, 'message': "brand_id is not integer"}, 400

        if r_filter.get('subtype_id') is not None and type(r_filter['subtype_id']) != int:
            return {'success': False, 'message': "subtype_id is not integer"}, 400

        if r_filter.get('client_id') is not None and type(r_filter['client_id']) != int:
            return {'success': False, 'message': "client_id is not integer"}, 400

        if r_filter.get('update_order') is not None and type(r_filter['update_order']) != int:
            return {'success': False, 'message': "update_order is not integer"}, 400

        if r_filter.get('created_at') is not None:
            if type(r_filter['created_at']) != list:
                return {'success': False, 'message': "created_at is not list"}, 400
            if len(r_filter['created_at']) != 2:
                return {'success': False, 'message': "created_at is not correct"}, 400
            if (type(r_filter['created_at'][0]) != int) or (type(r_filter['created_at'][1]) != int):
                return {'success': False, 'message': "created_at has not integers"}, 400

        if r_filter.get('engineer_id') is not None:
            if type(r_filter['engineer_id']) != list:
                return {'success': False, 'message': "engineer_id is not list"}, 400
            if not all([type(engineer) == int for engineer in r_filter['engineer_id']]):
                return {'success': False, 'message': "engineer_id has not integer"}, 400

        if r_filter.get('status_id') is not None:
            if type(r_filter['status_id']) != list:
                return {'success': False, 'message': "status_id is not list"}, 400
            if not all([type(status) == int for status in r_filter['status_id']]):
                return {'success': False, 'message': "status_id has not integer"}, 400

        if r_filter.get('order_type_id') is not None:
            if type(r_filter['order_type_id']) != list:
                return {'success': False, 'message': "order_type_id is not list"}, 400
            if not all([type(order_type) == int for order_type in r_filter['order_type_id']]):
                return {'success': False, 'message': "order_type_id has not integer"}, 400

        if r_filter.get('manager_id') is not None:
            if type(r_filter['manager_id']) != list:
                return {'success': False, 'message': "manager_id is not list"}, 400
            if not all([type(manager) == int for manager in r_filter['manager_id']]):
                return {'success': False, 'message': "manager_id has not integer"}, 400

        if r_filter.get('overdue') is not None and type(r_filter['overdue']) != bool:
            return {'success': False, 'message': "overdue is not boolean"}, 400

        if r_filter.get('status_overdue') is not None and type(r_filter['status_overdue']) != bool:
            return {'success': False, 'message': "status_overdue is not boolean"}, 400

        if r_filter.get('urgent') is not None and type(r_filter['urgent']) != bool:
            return {'success': False, 'message': "urgent is not boolean"}, 400

        if r_filter.get('update_badges') is not None and type(r_filter['update_badges']) != bool:
            return {'success': False, 'message': "update_badges is not boolean"}, 400

    return db_iteraction.change_order_status(
        status_id=status_id,
        order_id=order_id,
        user_id=user_id,
        r_filter=r_filter
    )
