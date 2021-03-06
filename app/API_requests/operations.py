from flask import Blueprint
from flask_jwt_extended import jwt_required, decode_token
from flask import request
from flask_login import login_required, current_user

from app.db.interaction.db_iteraction import db_iteraction
from app.db.models.models import Employees, Orders, DictService, Operations

operation_api = Blueprint('operation_api', __name__)


@operation_api.route('/get_operations', methods=['POST'])
@login_required
def get_operations():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    # Проверка соответствию типов данных
    id = request_body.get('id')
    if id is not None and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page is not None and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    amount = request_body.get('amount', 1)
    if amount is not None and type(amount) != int:
        return {'success': False, 'message': "amount is not integer"}, 400

    cost = request_body.get('cost', 0)
    if cost is not None:
        try:
            cost = float(cost)
        except:
            return {'success': False, 'message': 'cost is not number'}, 400

    discount_value = request_body.get('discount_value', 0)
    if discount_value is not None:
        try:
            discount_value = float(discount_value)
        except:
            return {'success': False, 'message': 'discount_value is not number'}, 400

    engineer_id = request_body.get('engineer_id')
    if engineer_id is not None and type(engineer_id) != int:
        return {'success': False, 'message': "engineer_id is not integer"}, 400
    if engineer_id is not None and not db_iteraction.pgsql_connetction.session.query(Employees).get(engineer_id):
        return {'success': False, 'message': 'employee_id is not defined'}, 400

    order_id = request_body.get('order_id')
    if order_id is not None and type(order_id) != int:
        return {'success': False, 'message': "order_id is not integer"}, 400
    if order_id is not None and not db_iteraction.pgsql_connetction.session.query(Orders).get(order_id):
        return {'success': False, 'message': 'order_id is not defined'}, 400

    dict_id = request_body.get('dict_id')
    if dict_id is not None and type(dict_id) != int:
        return {'success': False, 'message': "dict_id is not integer"}, 400
    if dict_id is not None and not db_iteraction.pgsql_connetction.session.query(DictService).get(dict_id):
        return {'success': False, 'message': 'dict_id is not defined'}, 400

    price = request_body.get('price', 0)
    if price is not None:
        try:
            price = float(price)
        except:
            return {'success': False, 'message': 'price is not number'}, 400

    total = request_body.get('total', 0)
    if total is not None:
        try:
            total = float(total)
        except:
            return {'success': False, 'message': 'total is not number'}, 400

    title = request_body.get('title')
    if title is not None:
        title = str(title)

    warranty = request_body.get('warranty')
    if warranty is not None and type(warranty) != bool:
        return {'success': False, 'message': 'warranty is not boolean'}, 400

    deleted = request_body.get('deleted')
    if deleted is not None and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    warranty_period = request_body.get('warranty_period', 0)
    if warranty_period is not None and type(warranty_period) != int:
        return {'success': False, 'message': "warranty_period is not integer"}, 400

    created_at = request_body.get('created_at')
    if created_at is not None:
        if type(created_at) != list:
            return {'success': False, 'message': "Created_at is not list"}, 400
        if len(created_at) != 2:
            return {'success': False, 'message': "Created_at is not correct"}, 400
        if (type(created_at[0]) != int) or (type(created_at[1]) != int):
            return {'success': False, 'message': "Created_at has not integers"}, 400

    filter_order = request_body.get('filter_order')


    result = db_iteraction.get_operations(
        id=id,                              # int - id статуса - полное совпадение
        cost=cost,                          # int - себестоимость - полное совпадение
        discount_value=discount_value,      # float - сумма скидки - подное совпадение
        engineer_id=engineer_id,            # int - id инженера - полное сопвпадение
        price=price,                        # float - цена услуги - полное совпадение
        title=title,                        # str - наименование услуги - частичное совпадение
        total=total,                        # float - сумма к оплате
        warranty=warranty,                  # bool - гарантия - полное совпадение
        deleted=deleted,                    # bool - удален
        warranty_period=warranty_period,    # int - гарантийный период - полное совпадение
        created_at=created_at,              # [int, int] - дата создания - промежуток дат
        page=page,                          # int - Старница погинации
        order_id=order_id,                  # int - Новый id заказа
        dict_id=dict_id,
        filter_order=filter_order
    )
    return result



@operation_api.route('/operations', methods=['POST', 'PUT', 'DELETE'])
@login_required
def operations():
    user_id = current_user.get_id()

    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    # Проверка соответствию типов данных
    id = request_body.get('id')
    if id is not None and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page is not None and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    amount = request_body.get('amount', 1)
    if amount is not None and type(amount) != int:
        return {'success': False, 'message': "amount is not integer"}, 400

    order_type_id = request_body.get('order_type_id')
    if order_type_id is not None and type(order_type_id) != int:
        return {'success': False, 'message': "order_type_id is not integer"}, 400

    cost = request_body.get('cost', 0)
    if cost is not None:
        try:
            cost = float(cost)
        except:
            return {'success': False, 'message': 'cost is not number'}, 400

    earnings_percent = request_body.get('earnings_percent', 0)
    if earnings_percent is not None:
        try:
            earnings_percent = float(earnings_percent)
        except:
            return {'success': False, 'message': 'earnings_percent is not number'}, 400

    earnings_summ = request_body.get('earnings_summ', 0)
    if earnings_summ is not None:
        try:
            earnings_summ = float(earnings_summ)
        except:
            return {'success': False, 'message': 'earnings_summ is not number'}, 400

    discount_value = request_body.get('discount_value', 0)
    if discount_value is not None:
        try:
            discount_value = float(discount_value)
        except:
            return {'success': False, 'message': 'discount_value is not number'}, 400

    discount = request_body.get('discount', 0)
    if discount is not None:
        try:
            discount = float(discount)
        except:
            return {'success': False, 'message': 'discount is not number'}, 400

    engineer_id = request_body.get('engineer_id')
    if engineer_id is not None and type(engineer_id) != int:
        return {'success': False, 'message': "engineer_id is not integer"}, 400
    if engineer_id is not None and not db_iteraction.pgsql_connetction.session.query(Employees).get(engineer_id):
        return {'success': False, 'message': 'employee_id is not defined'}, 400

    order_id = request_body.get('order_id')
    if order_id is not None and type(order_id) != int:
        return {'success': False, 'message': "order_id is not integer"}, 400
    if order_id is not None and not db_iteraction.pgsql_connetction.session.query(Orders).get(order_id):
        return {'success': False, 'message': 'order_id is not defined'}, 400

    dict_id = request_body.get('dict_id')
    if dict_id is not None and type(dict_id) != int:
        return {'success': False, 'message': "dict_id is not integer"}, 400
    if dict_id is not None and not db_iteraction.pgsql_connetction.session.query(DictService).get(dict_id):
        return {'success': False, 'message': 'dict_id is not defined'}, 400

    price = request_body.get('price', 0)
    if price is not None:
        try:
            price = float(price)
        except:
            return {'success': False, 'message': 'price is not number'}, 400

    total = request_body.get('total', 0)
    if total is not None:
        try:
            total = float(total)
        except:
            return {'success': False, 'message': 'total is not number'}, 400

    title = request_body.get('title')
    if title is not None:
        title = str(title)

    comment = request_body.get('comment')
    if comment is not None:
        comment = str(comment)

    percent = request_body.get('percent')
    if percent is not None and type(percent) != bool:
        return {'success': False, 'message': 'percent is not boolean'}, 400

    deleted = request_body.get('deleted')
    if deleted is not None and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    warranty_period = request_body.get('warranty_period', 0)
    if warranty_period is not None and type(warranty_period) != int:
        return {'success': False, 'message': "warranty_period is not integer"}, 400

    created_at = request_body.get('created_at')
    
    filter_order = request_body.get('filter_order')
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
            return {'success': False, 'message': "kindof_good is not integer"}, 400
    
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

        if created_at and type(created_at) != int:
            return {'success': False, 'message': "created_at is not integer"}, 400

        if not engineer_id:
            return {'success': False, 'message': 'engineer_id required'}, 400

        if not title:
            return {'success': False, 'message': 'title required'}, 400


        result = db_iteraction.add_operations(
            amount=amount,                      # int - количество - по дефолту 1
            cost=cost,                          # int - себестоимость - по дефолту 0
            discount_value=discount_value,      # float - сумма скидки - по дефолту 0
            engineer_id=engineer_id,            # int - id инженера - обязательное поле
            price=price,                        # float - цена услуги - по дефолту 0
            total=total,                        # float - сумма к оплате
            title=title,                        # str - наименование услуги - обязательное поле
            comment=comment,                    # str - коментарий
            percent=percent,                    # bool - процент или сумма (True - процент)
            discount=discount,                  # float - значение скидки
            deleted=deleted,                    # bool - уделен
            warranty_period=warranty_period,    # int - гарантийный период - по дефолту 0
            created_at=created_at,              # int - дата создания - по дефоту now
            order_id=order_id,                  # int - id заказа
            dict_id=dict_id,                    # int - id услуги
            filter_order=filter_order,
            user_id=user_id

        )
        return result


    # Проверим сущестует ли запись по данному id
    if not db_iteraction.pgsql_connetction.session.query(Operations).get(id):
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':

        created_at = request_body.get('created_at', 0)
        if created_at is not None and type(created_at) != int:
            return {'success': False, 'message': "created_at is not integer"}, 400


        result = db_iteraction.edit_operations(
            id=id,                              # int - id записи - полное совпаден
            amount=amount,                      # int - Новое количество
            cost=cost,                          # float - Новая себестоимость
            discount_value=discount_value,      # float - Новая сумма скидки
            engineer_id=engineer_id,            # int - Новый id инженера
            price=price,                        # int - Новая стоимость услуги
            total=total,                        # float - Новая сумма к оплате
            title=title,                        # str - Новое наименование услуги
            comment=comment,                    # str - Новый коментарий
            percent=percent,                    # bool - Новое значение процент или сумма (True - процент)
            discount=discount,                  # float - Новое значение скидки
            deleted=deleted,                    # bool - Новое значение уделен
            warranty_period=warranty_period,    # int - Новый срок гаранти
            created_at=created_at,              # int - Новая дата создания
            order_id=order_id,                  # int - Новый id заказа
            dict_id=dict_id,                    # int - Новый id услуги
            filter_order=filter_order,
            user_id=user_id
        )
        return result


    if request.method == 'DELETE':

        return db_iteraction.del_operations(id=id)        # int - id записи - полное совпаден