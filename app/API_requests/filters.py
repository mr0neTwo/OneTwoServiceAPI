import traceback

from flask import Blueprint
from flask_jwt_extended import jwt_required
from flask import request
from flask_login import login_required

from app.db.interaction.db_iteraction import db_iteraction
from app.db.models.models import Employees

filters_api = Blueprint('filters_api', __name__)


@filters_api.route('/bagges', methods=['POST'])
@login_required
def get_babges():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    employee_access = request_body.get('employee_access')
    if employee_access is not None and type(employee_access) != int:
        return {'success': False, 'message': "employee_access is not integer"}, 400

    try:
        result = db_iteraction.get_badges(
            employee_access=employee_access            # int - id сотрудника - обязательное поле
        )
        return result, 200
    except:
        print(traceback.format_exc())
        return {'success': False, 'message': 'server error'}, 550


@filters_api.route('/get_custom_filters', methods=['POST'])
@login_required
def get_custom_filters():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id is not None and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    employee_id = request_body.get('employee_id')
    if not employee_id:
        return {'success': False, 'message': 'employee_id required'}, 400
    if type(employee_id) != int:
        return {'success': False, 'message': "employee_id is not integer"}, 400
    if not db_iteraction.pgsql_connetction.session.query(Employees).get(employee_id):
        return {'success': False, 'message': 'employee_id is not defined'}, 400

    result = db_iteraction.get_custom_filters(
        employee_id=employee_id                        # int - id сотрудника - полное совпадение
    )
    return result



@filters_api.route('/custom_filters', methods=['POST', 'PUT', 'DELETE'])
@login_required
def custom_filters():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id is not None and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    employee_id = request_body.get('employee_id')
    if employee_id is not None and type(employee_id) != int:
        return {'success': False, 'message': "employee_id is not integer"}, 400
    if employee_id is not None and not db_iteraction.pgsql_connetction.session.query(Employees).get(employee_id):
        return {'success': False, 'message': 'employee_id is not defined'}, 400

    filters = request_body.get('filters')

    title = request_body.get('title')
    if title is not None:
        title = str(title)

    general = request_body.get('general')
    if general is not None:
        general = bool(general)

    if request.method == 'POST':

        if not title:
            return {'success': False, 'message': 'title required'}, 400

        if not employee_id:
            return {'success': False, 'message': 'employee_id required'}, 400

        if not filters:
            return {'success': False, 'message': 'filters required'}, 400

        result = db_iteraction.add_custom_filters(
            title=title,                    # str - Название фильтра - обязательное поле
            filters=filters,                # json - фильтр - обязательное поле
            employee_id=employee_id,        # int - id сотрудника - обязательное поле
            general=general                 # bool - Общий - обязательное поле
        )
        return result

    if request.method == 'DELETE':
        return db_iteraction.del_custom_filters(
            id=id,                      # int - id записи - полное совпаден
            employee_id=employee_id
        )