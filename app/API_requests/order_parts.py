from flask import Blueprint
from flask_jwt_extended import jwt_required, decode_token
from flask import request
from flask_login import login_required, current_user

from app.db.interaction.db_iteraction import db_iteraction
from app.db.models.models import Employees, Orders, OrderParts

order_parts_api = Blueprint('order_parts_api', __name__)

@order_parts_api.route('/get_order_parts', methods=['POST'])
@login_required
def get_order_parts():
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

    engineer_id = request_body.get('engineer_id')
    if engineer_id is not None and type(engineer_id) != int:
        return {'success': False, 'message': "Engineer_id is not integer"}, 400
    if engineer_id is not None and not db_iteraction.pgsql_connetction.session.query(Employees).get(engineer_id):
        return {'success': False, 'message': 'employee_id is not defined'}, 400

    order_id = request_body.get('order_id')
    if order_id is not None and type(order_id) != int:
        return {'success': False, 'message': "order_id is not integer"}, 400
    if order_id is not None and not db_iteraction.pgsql_connetction.session.query(Orders).get(order_id):
        return {'success': False, 'message': 'order_id is not defined'}, 400

    title = request_body.get('title')
    if title is not None:
        title = str(title)

    deleted = request_body.get('deleted')
    if deleted is not None and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    created_at = request_body.get('created_at')

    if created_at is not None:
        if type(created_at) != list:
            return {'success': False, 'message': "Created_at is not list"}, 400
        if len(created_at) != 2:
            return {'success': False, 'message': "Created_at is not correct"}, 400
        if (type(created_at[0]) != int) or (type(created_at[1]) != int):
            return {'success': False, 'message': "Created_at has not integers"}, 400

    result = db_iteraction.get_oder_parts(
        id=id,                              # int - id статуса - полное совпадение
        title=title,                        # str - наименование услуги - частичное совпадение
        deleted=deleted,
        created_at=created_at,              # [int, int] - дата создания - промежуток дат
        order_id=order_id,                  # int - id заказа
        page=page                           # int - Старница погинации
    )
    return result

@order_parts_api.route('/order_parts', methods=['POST', 'GET', 'PUT', 'DELETE'])
@login_required
def order_parts():
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

    cost = request_body.get('cost', 0)
    if cost is not None:
        try:
            cost = float(cost)
        except:
            return {'success': False, 'message': 'Cost is not number'}, 400

    discount_value = request_body.get('discount_value', 0)
    if discount_value is not None:
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
    if engineer_id is not None and type(engineer_id) != int:
        return {'success': False, 'message': "Engineer_id is not integer"}, 400
    if engineer_id is not None and not db_iteraction.pgsql_connetction.session.query(Employees).get(engineer_id):
        return {'success': False, 'message': 'employee_id is not defined'}, 400

    order_id = request_body.get('order_id')
    if order_id is not None and type(order_id) != int:
        return {'success': False, 'message': "order_id is not integer"}, 400
    if order_id is not None and not db_iteraction.pgsql_connetction.session.query(Orders).get(order_id):
        return {'success': False, 'message': 'order_id is not defined'}, 400

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

    if request.method == 'POST':

        if created_at is not None and type(created_at) != int:
            return {'success': False, 'message': "created_at is not integer"}, 400

        if not engineer_id:
            return {'success': False, 'message': 'engineer_id required'}, 400

        if not title:
            return {'success': False, 'message': 'title required'}, 400

        result = db_iteraction.add_oder_parts(
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
            order_id=order_id,                      # int - id заказа
            user_id=user_id,
            filter_order=filter_order
        )
        return result

    # Проверим сущестует ли запись по данному id
    if not db_iteraction.pgsql_connetction.session.query(OrderParts).get(id):
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':

        created_at = request_body.get('created_at', 0)
        if created_at is not None and type(created_at) != int:
            return {'success': False, 'message': "created_at is not integer"}, 400


        result = db_iteraction.edit_oder_parts(
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
            user_id=user_id,
            filter_order=filter_order
            )
        return result

    if request.method == 'DELETE':
        return db_iteraction.del_oder_parts(id=id)                  # int - id записи - полное совпаден
