from urllib.request import urlopen
from flask import Blueprint
from flask_jwt_extended import jwt_required
from flask import request

from app.db.interaction.db_iteraction import db_iteraction

equipments_api = Blueprint('equipments_api', __name__)


@equipments_api.route('/get_equipment_type', methods=['POST'])
@jwt_required()
def get_equipment_type():
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

    title = request_body.get('title')
    if title is not None:
        title = str(title)

    deleted = request_body.get('deleted')
    if deleted is not None and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    result = db_iteraction.get_equipment_type(
        id=id,              # int - id типа изделия - полное совпадение
        title=title,        # str - Тип изделия - частичное совпадение
        deleted=deleted,    # bool - Удален
        page=page           # int - Старница погинации
    )
    return result


@equipments_api.route('/equipment_type', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
def equipment_type():
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

    title = request_body.get('title')
    if title is not None:
        title = str(title)

    icon = request_body.get('icon')
    if icon is not None:
        icon = str(icon)

    url = request_body.get('url')
    if url is not None:
        url = str(url)

    branches = request_body.get('branches')
    if branches is not None and type(branches) != list:
        return {'success': False, 'message': "branches is not list"}, 400
    if branches is not None:
        if not all([type(branch) == int for branch in branches]):
            return {'success': False, 'message': "branches has not integer"}, 400

    deleted = request_body.get('deleted')
    if deleted is not None and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    list_for_join = request_body.get('list_for_join')
    if list_for_join is not None and type(list_for_join) != list:
        return {'success': False, 'message': "list_for_join is not list"}, 400
    if list_for_join is not None:
        if not all([type(join) == int for join in list_for_join]):
            return {'success': False, 'message': "list_for_join has not integer"}, 400

    r_filter = request_body.get('filter')

    if request.method == 'POST':

        if not title:
            return {'success': False, 'message': 'title required'}, 400

        result = db_iteraction.add_equipment_type(
            title=title,            # str - Тип изделия - обязательное поле
            icon=icon,              # str - Иконка типа изделия
            url=url,                # str - Ссылка на изображение типа изделия
            branches=branches,      # [int, ..int] - Список id филиалов
            deleted=deleted,        # bool - Удален
            r_filter=r_filter       # dict - фильтр ответных данных
        )
        return result

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_equipment_type(id=id)[0]['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        result = db_iteraction.edit_equipment_type(
            id=id,                          # int - id записи - полное совпаден
            title=title,                    # str - Новое название типа изделия
            icon=icon,                      # str - Новоя иконка изделия
            url=url,                        # str - Новоя ссылка на изображение изделия
            branches=branches,              # [int, ..int] - Список id филиалов
            deleted=deleted,                # bool - Удален
            list_for_join=list_for_join,    # [int, ..int] - Список id элементов для объединение
            r_filter=r_filter               # dict - фильтр ответных данных
        )
        return result

    if request.method == 'DELETE':

        return db_iteraction.del_equipment_type(id=id)  # int - id записи - полное совпаден


@equipments_api.route('/get_equipment_brand', methods=['POST'])
@jwt_required()
def get_equipment_brand():
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

    title = request_body.get('title')
    if title is not None:
        title = str(title)

    deleted = request_body.get('deleted')
    if deleted is not None and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    equipment_type_id = request_body.get('equipment_type_id')
    if equipment_type_id is not None and type(equipment_type_id) != int:
        return {'success': False, 'message': "equipment_type_id is not integer"}, 400
    if equipment_type_id is not None and db_iteraction.get_equipment_type(id=equipment_type_id)[0]['count'] == 0:
        return {'success': False, 'message': 'equipment_type_id is not defined'}, 400

    result = db_iteraction.get_equipment_brand(
        id=id,                                  # int - id бренда изделия - полное совпадение
        title=title,                            # str - Бренд - частичное совпадение
        equipment_type_id=equipment_type_id,    # int - id типа изделия
        deleted=deleted,                        # bool - Удален
        page=page                               # int - Старница погинации
    )
    return result


@equipments_api.route('/equipment_brand', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
def equipment_brand():
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

    title = request_body.get('title')
    if title is not None:
        title = str(title)

    icon = request_body.get('icon')
    if icon is not None:
        icon = str(icon)

    url = request_body.get('url')
    if url is not None:
        url = str(url)

    branches = request_body.get('branches')
    if branches is not None and type(branches) != list:
        return {'success': False, 'message': "branches is not list"}, 400
    if branches is not None:
        if not all([type(branch) == int for branch in branches]):
            return {'success': False, 'message': "branches has not integer"}, 400

    deleted = request_body.get('deleted')
    if deleted is not None and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    equipment_type_id = request_body.get('equipment_type_id')
    if equipment_type_id is not None and type(equipment_type_id) != int:
        return {'success': False, 'message': "equipment_type_id is not integer"}, 400
    if equipment_type_id is not None and db_iteraction.get_equipment_type(id=equipment_type_id)[0]['count'] == 0:
        return {'success': False, 'message': 'equipment_type_id is not defined'}, 400

    list_for_join = request_body.get('list_for_join')
    if list_for_join is not None and type(list_for_join) != list:
        return {'success': False, 'message': "list_for_join is not list"}, 400
    if list_for_join is not None:
        if not all([type(join) == int for join in list_for_join]):
            return {'success': False, 'message': "list_for_join has not integer"}, 400

    r_filter = request_body.get('filter')

    if request.method == 'POST':

        if not equipment_type_id:
            return {'success': False, 'message': 'equipment_type_id required'}, 400

        if not title:
            return {'success': False, 'message': 'title required'}, 400

        result = db_iteraction.add_equipment_brand(
            title=title,                            # str - Бренд - обязательное поле
            icon=icon,                              # str - Иконка бренда изделия
            url=url,                                # str - Ссылка на изображение бренда изделия
            branches=branches,                      # [int, ..int] - Список id филиалов
            deleted=deleted,                        # bool - Удален
            equipment_type_id=equipment_type_id,    # int - id типа изделия
            r_filter=r_filter                       # dict - фильтр ответных данных
        )
        return result

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_equipment_brand(id=id)[0]['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        result = db_iteraction.edit_equipment_brand(
            id=id,                                  # int - id записи - полное совпаден
            title=title,                            # str - Новое название бренда изделия
            icon=icon,                              # str - Новоя бренда изделия
            url=url,                                # str - Новоя ссылка на изображение бренда изделия
            branches=branches,                      # [int, ..int] - Список id филиалов
            deleted=deleted,                        # bool - Удален
            equipment_type_id=equipment_type_id,    # int - id типа изделия
            list_for_join=list_for_join,            # [int, ..int] - Список id элементов для объединение
            r_filter=r_filter                       # dict - фильтр ответных данных
        )
        return result

    if request.method == 'DELETE':
        return db_iteraction.del_equipment_brand(id=id)  # int - id записи - полное совпаден


@equipments_api.route('/get_equipment_subtype', methods=['POST'])
@jwt_required()
def get_equipment_subtype():
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

    title = request_body.get('title')
    if title is not None:
        title = str(title)

    deleted = request_body.get('deleted')
    if deleted is not None and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    equipment_brand_id = request_body.get('equipment_brand_id')
    if equipment_brand_id is not None and type(equipment_brand_id) != int:
        return {'success': False, 'message': "equipment_brand_id is not integer"}, 400
    if equipment_brand_id is not None and db_iteraction.get_equipment_brand(id=equipment_brand_id)[0]['count'] == 0:
        return {'success': False, 'message': 'equipment_brand_id is not defined'}, 400

    result = db_iteraction.get_equipment_subtype(
        id=id,                                      # int - id модификации изделия - полное совпадение
        title=title,                                # str - Модификация изделия - частичное совпадение
        equipment_brand_id=equipment_brand_id,      # int - id бренда изделия
        deleted=deleted,                            # bool - удален
        page=page                                   # int - Старница погинации
    )
    return result


@equipments_api.route('/equipment_subtype', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
def equipment_subtype():
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

    title = request_body.get('title')
    if title is not None:
        title = str(title)

    icon = request_body.get('icon')
    if icon is not None:
        icon = str(icon)

    url = request_body.get('url')
    if url is not None:
        url = str(url)

    branches = request_body.get('branches')
    if branches is not None and type(branches) != list:
        return {'success': False, 'message': "branches is not list"}, 400
    if branches is not None:
        if not all([type(branch) == int for branch in branches]):
            return {'success': False, 'message': "branches has not integer"}, 400

    deleted = request_body.get('deleted')
    if deleted is not None and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    equipment_brand_id = request_body.get('equipment_brand_id')
    if equipment_brand_id is not None and type(equipment_brand_id) != int:
        return {'success': False, 'message': "equipment_brand_id is not integer"}, 400
    if equipment_brand_id is not None and db_iteraction.get_equipment_brand(id=equipment_brand_id)[0]['count'] == 0:
        return {'success': False, 'message': 'equipment_brand_id is not defined'}, 400

    list_for_join = request_body.get('list_for_join')
    if list_for_join is not None and type(list_for_join) != list:
        return {'success': False, 'message': "list_for_join is not list"}, 400
    if list_for_join is not None:
        if not all([type(join) == int for join in list_for_join]):
            return {'success': False, 'message': "list_for_join has not integer"}, 400

    r_filter = request_body.get('filter')
    img = request_body.get('img')

    if request.method == 'POST':

        if not title:
            return {'success': False, 'message': 'title required'}, 400

        if not equipment_brand_id:
            return {'success': False, 'message': 'equipment_brand_id required'}, 400

        result = db_iteraction.add_equipment_subtype(
            title=title,                            # str - Модификация изделия - обязательное поле
            icon=icon,                              # str - Иконка модификации изделия
            url=url,                                # str - Ссылка на изображение модификации изделия
            branches=branches,                      # [int, ...int] - Список филиалов
            deleted=deleted,                        # bool - Удален
            equipment_brand_id=equipment_brand_id,  # int - id бренда изделия
            r_filter=r_filter,                      # dict - фильтр ответных данных
            img=img
        )


        return result

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_equipment_subtype(id=id)[0]['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':

        result = db_iteraction.edit_equipment_subtype(
            id=id,                                  # int - id записи - полное совпаден
            title=title,                            # str - Новое название бренда изделия
            icon=icon,                              # str - Новоя бренда изделия
            url=url,                                # str - Новоя ссылка на изображение бренда изделия
            branches=branches,                      # [int, ...int] - Список филиалов
            deleted=deleted,                        # bool - Удален
            equipment_brand_id=equipment_brand_id,  # int - id типа изделия
            list_for_join=list_for_join,            # [int, ..int] - Список id элементов для объединение
            r_filter=r_filter,                      # dict - фильтр ответных данных
            img=img
        )

        return result

    if request.method == 'DELETE':
        return db_iteraction.del_equipment_subtype(id=id)  # int - id записи - полное совпаден


@equipments_api.route('/get_equipment_model', methods=['POST'])
@jwt_required()
def get_equipment_model():
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

    title = request_body.get('title')
    if title is not None:
        title = str(title)

    deleted = request_body.get('deleted')
    if deleted is not None and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    equipment_subtype_id = request_body.get('equipment_subtype_id')
    if equipment_subtype_id is not None and type(equipment_subtype_id) != int:
        return {'success': False, 'message': "equipment_subtype_id is not integer"}, 400
    if equipment_subtype_id is not None and db_iteraction.get_equipment_subtype(id=equipment_subtype_id)[0]['count'] == 0:
        return {'success': False, 'message': 'equipment_subtype_id is not defined'}, 400

    result = db_iteraction.get_equipment_model(
        id=id,                                      # int - id модели изделия - полное совпадение
        title=title,                                # str - Модель изделия - частичное совпадение
        equipment_subtype_id=equipment_subtype_id,  # int - id модификации изделия
        deleted=deleted,                            # bool - Удален
        page=page                                   # int - Старница погинации
    )
    return result


@equipments_api.route('/equipment_model', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
def equipment_model():
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

    title = request_body.get('title')
    if title is not None:
        title = str(title)

    icon = request_body.get('icon')
    if icon is not None:
        icon = str(icon)

    url = request_body.get('url')
    if url is not None:
        url = str(url)

    branches = request_body.get('branches')
    if branches is not None and type(branches) != list:
        return {'success': False, 'message': "branches is not list"}, 400
    if branches is not None:
        if not all([type(branch) == int for branch in branches]):
            return {'success': False, 'message': "branches has not integer"}, 400

    deleted = request_body.get('deleted')
    if deleted is not None and type(deleted) != bool:
        return {'success': False, 'message': 'deleted is not boolean'}, 400

    equipment_subtype_id = request_body.get('equipment_subtype_id')
    if equipment_subtype_id is not None and type(equipment_subtype_id) != int:
        return {'success': False, 'message': "equipment_subtype_id is not integer"}, 400
    if equipment_subtype_id is not None and db_iteraction.get_equipment_subtype(id=equipment_subtype_id)[0]['count'] == 0:
        return {'success': False, 'message': 'equipment_subtype_id is not defined'}, 400

    r_filter = request_body.get('filter')

    if request.method == 'POST':

        if not equipment_subtype_id:
            return {'success': False, 'message': 'equipment_subtype_id required'}, 400

        if not title:
            return {'success': False, 'message': 'title required'}, 400

        result = db_iteraction.add_equipment_model(
            title=title,                                # str - Модель изделия - обязательное поле
            icon=icon,                                  # str - Иконка модели изделия
            url=url,                                    # str - Ссылка на изображение модели изделия
            branches=branches,                          # [int, ...int] - Список филиалов
            deleted=deleted,                            # bool - Удален
            equipment_subtype_id=equipment_subtype_id,  # int - id модификации изделия
            r_filter=r_filter                           # dict - фильтр ответных данных
        )
        return result

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_equipment_model(id=id)[0]['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':
        result = db_iteraction.edit_equipment_model(
            id=id,                                      # int - id записи - полное совпаден
            title=title,                                # str - Новое название модели изделия
            icon=icon,                                  # str - Новоя иконика модели изделия
            url=url,                                    # str - Новоя ссылка на изображение модели изделия
            branches=branches,                          # [int, ...int] - Список филиалов
            deleted=deleted,                            # bool - Удален
            equipment_subtype_id=equipment_subtype_id,  # int - id типа изделия
            r_filter=r_filter                           # dict - фильтр ответных данных
        )
        return result

    if request.method == 'DELETE':
        return db_iteraction.del_equipment_model(id=id)  # int - id записи - полное совпаден

