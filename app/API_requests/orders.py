from flask import Blueprint
from flask_jwt_extended import jwt_required, decode_token
from flask import request
from flask_login import login_required, current_user

from app.db.interaction.db_iteraction import db_iteraction
from app.db.models.models import Orders, Status, Branch

orders_api = Blueprint('orders_api', __name__)

@orders_api.route('/get_order', methods=['POST'])
@login_required
def get_order():
    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id is not None and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400


    result = db_iteraction.get_order(id=id)
    return result

@orders_api.route('/order_comment', methods=['POST'])
@login_required
def order_comment():
    user_id = current_user.get_id()

    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    order_id = request_body.get('order_id')
    if order_id is not None and type(order_id) != int:
        return {'success': False, 'message': "order_id is not integer"}, 400
    if order_id is not None and not db_iteraction.pgsql_connetction.session.query(Orders).get(order_id):
        return {'success': False, 'message': 'order_id is not defined'}, 400

    current_status_id = request_body.get('current_status_id')
    if current_status_id is not None and type(current_status_id) != int:
        return {'success': False, 'message': "current_status_id is not integer"}, 400
    if current_status_id is not None and not db_iteraction.pgsql_connetction.session.query(Status).get(current_status_id):
        return {'success': False, 'message': 'current_status_id is not defined'}, 400

    branch_id = request_body.get('branch_id')
    if branch_id is not None and type(branch_id) != int:
        return {'success': False, 'message': "branch_id is not integer"}, 400
    if branch_id is not None and not db_iteraction.pgsql_connetction.session.query(Branch).get(branch_id):
        return {'success': False, 'message': 'branch_id is not defined'}, 400

    comment = request_body.get('comment')
    if comment is not None:
        comment = str(comment)

    result = db_iteraction.add_order_comment(
        order_id=order_id,
        current_status_id=current_status_id,
        branch_id=branch_id,
        comment=comment,
        user_id=user_id
    )

    return result

@orders_api.route('/get_orders', methods=['POST'])
@login_required
def get_orders():
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

    created_at = request_body.get('created_at')
    if created_at is not None:
        if type(created_at) != list:
            return {'success': False, 'message': "created_at is not list"}, 400
        if len(created_at) != 2:
            return {'success': False, 'message': "created_at is not correct"}, 400
        if type(created_at[0]) != int:
            return {'success': False, 'message': "created_at has not integers"}, 400
        if type(created_at[1]) and type(created_at[1]) != int:
            return {'success': False, 'message': "created_at has not integers"}, 400

    # done_at = request_body.get('done_at')
    # if done_at is not None:
    #     if type(done_at) != list:
    #         return {'success': False, 'message': "done_at is not list"}, 400
    #     if len(done_at) != 2:
    #         return {'success': False, 'message': "done_at is not correct"}, 400
    #     if type(done_at[0]) != int:
    #         return {'success': False, 'message': "done_at has not integers"}, 400
    #     if type(done_at[1]) and type(done_at[1]) != int:
    #         return {'success': False, 'message': "done_at has not integers"}, 400

    # closed_at = request_body.get('closed_at')
    # if closed_at is not None:
    #     if type(closed_at) != list:
    #         return {'success': False, 'message': "closed_at is not list"}, 400
    #     if len(closed_at) != 2:
    #         return {'success': False, 'message': "closed_at is not correct"}, 400
    #     if type(closed_at[0]) != int:
    #         return {'success': False, 'message': "closed_at has not integers"}, 400
    #     if type(closed_at[1]) and type(closed_at[1]) != int:
    #         return {'success': False, 'message': "closed_at has not integers"}, 400

    # assigned_at = request_body.get('assigned_at')
    # if assigned_at is not None:
    #     if type(assigned_at) != list:
    #         return {'success': False, 'message': "assigned_at is not list"}, 400
    #     if len(assigned_at) != 2:
    #         return {'success': False, 'message': "assigned_at is not correct"}, 400
    #     if type(assigned_at[0]) != int:
    #         return {'success': False, 'message': "assigned_at has not integers"}, 400
    #     if type(assigned_at[1]) and type(assigned_at[1]) != int:
    #         return {'success': False, 'message': "assigned_at has not integers"}, 400

    # estimated_done_at = request_body.get('estimated_done_at')
    # if estimated_done_at is not None:
    #     if type(estimated_done_at) != list:
    #         return {'success': False, 'message': "estimated_done_at is not list"}, 400
    #     if len(estimated_done_at) != 2:
    #         return {'success': False, 'message': "estimated_done_at is not correct"}, 400
    #     if type(estimated_done_at[0]) != int:
    #         return {'success': False, 'message': "estimated_done_at has not integers"}, 400
    #     if type(estimated_done_at[1]) and type(estimated_done_at[1]) != int:
    #         return {'success': False, 'message': "estimated_done_at has not integers"}, 400

    # scheduled_for = request_body.get('scheduled_for')
    # if scheduled_for is not None:
    #     if type(scheduled_for) != list:
    #         return {'success': False, 'message': "scheduled_for is not list"}, 400
    #     if len(scheduled_for) != 2:
    #         return {'success': False, 'message': "scheduled_for is not correct"}, 400
    #     if type(scheduled_for[0]) != int:
    #         return {'success': False, 'message': "scheduled_for has not integers"}, 400
    #     if type(scheduled_for[1]) and type(scheduled_for[1]) != int:
    #         return {'success': False, 'message': "scheduled_for has not integers"}, 400

    # warranty_date = request_body.get('warranty_date')
    # if warranty_date is not None:
    #     if type(warranty_date) != list:
    #         return {'success': False, 'message': "warranty_date is not list"}, 400
    #     if len(warranty_date) != 2:
    #         return {'success': False, 'message': "warranty_date is not correct"}, 400
    #     if type(warranty_date[0]) != int:
    #         return {'success': False, 'message': "warranty_date has not integers"}, 400
    #     if type(warranty_date[1]) and type(warranty_date[1]) != int:
    #         return {'success': False, 'message': "warranty_date has not integers"}, 400

    # ad_campaign_id = request_body.get('ad_campaign_id')
    # if ad_campaign_id is not None and type(ad_campaign_id) != list:
    #     return {'success': False, 'message': "ad_campaign_id is not list"}, 400
    # if ad_campaign_id is not None:
    #     if not all([type(ad_cam) == int for ad_cam in ad_campaign_id]):
    #         return {'success': False, 'message': "ad_campaign_id has not integer"}, 400

    branch_id = request_body.get('branch_id')
    if branch_id is not None and type(branch_id) != int:
        return {'success': False, 'message': "branch_id is not integer"}, 400
    if branch_id is not None and not db_iteraction.pgsql_connetction.session.query(Branch).get(branch_id):
        return {'success': False, 'message': 'branch_id is not defined'}, 400

    status_id = request_body.get('status_id')
    if status_id is not None and type(status_id) != list:
        return {'success': False, 'message': "status_id is not list"}, 400
    if status_id is not None:
        if not all([type(status) == int for status in status_id]):
            return {'success': False, 'message': "status_id has not integer"}, 400

    client_id = request_body.get('client_id')
    if client_id is not None and type(client_id) != list:
        return {'success': False, 'message': "client_id is not list"}, 400
    if client_id is not None:
        if not all([type(client) == int for client in client_id]):
            return {'success': False, 'message': "client_id has not integer"}, 400

    order_type_id = request_body.get('order_type_id')
    if order_type_id is not None and type(order_type_id) != list:
        return {'success': False, 'message': "order_type_id is not list"}, 400
    if order_type_id is not None:
        if not all([type(ot) == int for ot in order_type_id]):
            return {'success': False, 'message': "order_type_id has not integer"}, 400

    # closed_by_id = request_body.get('closed_by_id')
    # if closed_by_id is not None and type(closed_by_id) != list:
    #     return {'success': False, 'message': "closed_by_id is not list"}, 400
    # if closed_by_id is not None:
    #     if not all([type(closed_by) == int for closed_by in closed_by_id]):
    #         return {'success': False, 'message': "closed_by_id has not integer"}, 400

    # created_by_id = request_body.get('created_by_id')
    # if created_by_id is not None and type(created_by_id) != list:
    #     return {'success': False, 'message': "created_by_id is not list"}, 400
    # if created_by_id is not None:
    #     if not all([type(created_by) == int for created_by in created_by_id]):
    #         return {'success': False, 'message': "created_by_id has not integer"}, 400

    engineer_id = request_body.get('engineer_id')
    if engineer_id is not None and type(engineer_id) != list:
        return {'success': False, 'message': "engineer_id is not list"}, 400
    if engineer_id is not None:
        if not all([type(engineer) == int for engineer in engineer_id]):
            return {'success': False, 'message': "engineer_id has not integer"}, 400

    manager_id = request_body.get('manager_id')
    if manager_id is not None and type(manager_id) != list:
        return {'success': False, 'message': "manager_id is not list"}, 400
    if manager_id is not None:
        if not all([type(manager) == int for manager in manager_id]):
            return {'success': False, 'message': "manager_id has not integer"}, 400

    # id_label = request_body.get('id_label')
    # if id_label:
    #     id_label = str(id_label)

    kindof_good_id = request_body.get('kindof_good_id')
    if kindof_good_id is not None and type(kindof_good_id) != int:
        return {'success': False, 'message': "kindof_good_id is not integer"}, 400
    if kindof_good_id is not None and db_iteraction.get_equipment_type(id=kindof_good_id)[0]['count'] == 0:
        return {'success': False, 'message': 'kindof_good_id is not defined'}, 400

    brand_id = request_body.get('brand_id')
    if brand_id is not None and type(brand_id) != int:
        return {'success': False, 'message': "brand_id is not integer"}, 400
    if brand_id is not None and db_iteraction.get_equipment_brand(id=brand_id)[0]['count'] == 0:
        return {'success': False, 'message': 'brand_id is not defined'}, 400

    # model = request_body.get('model')
    # if model:
    #     model = str(model)

    subtype_id = request_body.get('subtype_id')
    if subtype_id is not None and type(subtype_id) != int:
        return {'success': False, 'message': "subtype_id is not integer"}, 400
    if subtype_id is not None and db_iteraction.get_equipment_subtype(id=subtype_id)[0]['count'] == 0:
        return {'success': False, 'message': 'subtype_id is not defined'}, 400

    # serial = request_body.get('serial')
    # if serial is not None:
    #     serial = str(serial)

    # cell = request_body.get('cell')
    # if cell is not None:
    #     cell = str(cell)

    # client_name = request_body.get('client_name')
    # if client_name is not None:
    #     client_name = str(client_name)

    # client_phone = request_body.get('client_phone')
    # if client_phone is not None:
    #     client_phone = str(client_phone)

    field_sort = request_body.get('field_sort', 'id')
    if field_sort is not None:
        field_sort = str(field_sort)

    sort = request_body.get('sort', 'asc')
    if sort is not None:
        sort = str(sort)

    search = request_body.get('search')
    if search is not None:
        search = str(search)

    urgent = request_body.get('urgent')
    if urgent  is not None and type(urgent) != bool:
        return {'success': False, 'message': 'urgent is not boolean'}, 400

    overdue = request_body.get('overdue')
    if overdue  is not None and type(overdue) != bool:
        return {'success': False, 'message': 'overdue is not boolean'}, 400

    status_overdue = request_body.get('status_overdue')
    if status_overdue  is not None and type(status_overdue) != bool:
        return {'success': False, 'message': 'status_overdue is not boolean'}, 400


    result = db_iteraction.get_orders(
        # id=id,                                  # int - id филиала - полное совпадение
        created_at=created_at,                  # [int - int] - даты создания - промежуток
        # done_at=done_at,                        # [int - int] - даты готовности - промежуток
        # closed_at=closed_at,                    # [int - int] - даты закрытия - промежуток
        # assigned_at=assigned_at,                # [int - int] - даты назначен на - промежуток
        # estimated_done_at=estimated_done_at,    # [int - int] - запланированные даты готовности - промежуток
        # scheduled_for=scheduled_for,            # [int - int] - даты запланирован на - промежуток
        # warranty_date=warranty_date,            # [int - int] - даты горании до - промежуток

        # ad_campaign_id=ad_campaign_id,          # list - id рекламной копании - полное совпадение одного из списка
        branch_id=branch_id,                    # int - id филиала - полное совпадение
        status_id=status_id,                    # list - id статуса - полное совпадение одного из списка
        client_id=client_id,                    # list - id клиента - полное совпадение одного из списка
        order_type_id=order_type_id,            # list - id типа заказа - полное совпадение одного из списка
        engineer_id=engineer_id,                # list - id сотрудника - полное совпадение одного из списка
        manager_id=manager_id,                  # list - id сотрудника - полное совпадение одного из списка

        # id_label=id_label,
        kindof_good_id=kindof_good_id,
        brand_id=brand_id,
        # model=model,
        subtype_id=subtype_id,
        # serial=serial,
        # client_name=client_name,
        # client_phone=client_phone,
        search=search,
        # cell=cell,

        overdue=overdue,
        status_overdue=status_overdue,
        urgent=urgent,
        page=page,                         # int - Старница погинации
        field_sort=field_sort,
        sort=sort
    )
    return result


@orders_api.route('/orders', methods=['POST', 'PUT', 'DELETE'])
@login_required
def orders():
    user_id = current_user.get_id()

    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 290

    id = request_body.get('id')
    if id is not None and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    page = request_body.get('page', 0)
    if page is not None and type(page) != int:
        return {'success': False, 'message': "page is not integer"}, 400

    created_at = request_body.get('created_at')
    if created_at is not None and type(created_at) != int:
        return {'success': False, 'message': 'created_at is not integer'}, 400

    done_at = request_body.get('done_at')
    if done_at is not None and type(done_at) != int:
        return {'success': False, 'message': 'done_at is not integer'}, 400

    closed_at = request_body.get('closed_at')
    if closed_at is not None and type(closed_at) != int:
        return {'success': False, 'message': 'closed_at is not integer'}, 400

    assigned_at = request_body.get('assigned_at')
    if assigned_at is not None and type(assigned_at) != int:
        return {'success': False, 'message': 'assigned_at is not integer'}, 400

    duration = request_body.get('duration')
    if duration is not None and type(duration) != int:
        return {'success': False, 'message': 'duration is not integer'}, 400

    estimated_done_at = request_body.get('estimated_done_at')
    if estimated_done_at is not None and type(estimated_done_at) != int:
        return {'success': False, 'message': 'estimated_done_at is not integer'}, 400

    scheduled_for = request_body.get('scheduled_for')
    if scheduled_for is not None and type(scheduled_for) != int:
        return {'success': False, 'message': 'scheduled_for is not integer'}, 400

    warranty_date = request_body.get('warranty_date')
    if warranty_date is not None and type(warranty_date) != int:
        return {'success': False, 'message': 'warranty_date is not integer'}, 400

    status_deadline = request_body.get('status_deadline')
    if status_deadline is not None and type(status_deadline) != int:
        return {'success': False, 'message': 'status_deadline is not integer'}, 400

    ad_campaign_id = request_body.get('ad_campaign_id')
    if ad_campaign_id is not None and type(ad_campaign_id) != int:
        return {'success': False, 'message': "ad_campaign_id is not integer"}, 400
    # if ad_campaign_id is not None and db_iteraction.get_adCampaign(id=ad_campaign_id)['count'] == 0:
    #     return {'success': False, 'message': 'ad_campaign_id is not defined'}, 400

    branch_id = request_body.get('branch_id')
    if branch_id is not None and type(branch_id) != int:
        return {'success': False, 'message': "branch_id is not integer"}, 400
    if branch_id is not None and not db_iteraction.pgsql_connetction.session.query(Branch).get(branch_id):
        return {'success': False, 'message': 'branch_id is not defined'}, 400

    status_id = request_body.get('status_id')
    if status_id is not None and type(status_id) != int:
        return {'success': False, 'message': "status_id is not integer"}, 400
    # if status_id is not None and db_iteraction.get_status(id=status_id)['count'] == 0:
    #     return {'success': False, 'message': 'status_id is not defined'}, 400

    client_id = request_body.get('client_id')
    if client_id is not None and type(client_id) != int:
        return {'success': False, 'message': "client_id is not integer"}, 400
    # if client_id is not None and db_iteraction.get_clients(id=client_id)['count'] == 0:
    #     return {'success': False, 'message': 'client_id is not defined'}, 400

    order_type_id = request_body.get('order_type_id')
    if order_type_id is not None and type(order_type_id) != int:
        return {'success': False, 'message': "order_type_id is not integer"}, 400
    # if order_type_id is not None and db_iteraction.get_order_type(id=order_type_id)['count'] == 0:
    #     return {'success': False, 'message': 'order_type_id is not defined'}, 400

    closed_by_id = request_body.get('closed_by_id')
    if closed_by_id is not None and type(closed_by_id) != int:
        return {'success': False, 'message': "closed_by_id is not integer"}, 400
    # if closed_by_id is not None and db_iteraction.get_employee(id=closed_by_id)['count'] == 0:
    #     return {'success': False, 'message': 'closed_by_id is not defined'}, 400

    created_by_id = request_body.get('created_by_id')
    if created_by_id is not None and type(created_by_id) != int:
        return {'success': False, 'message': "created_by_id is not integer"}, 400
    # if created_by_id is not None and db_iteraction.get_employee(id=created_by_id)['count'] == 0:
    #     return {'success': False, 'message': 'created_by_id is not defined'}, 400

    engineer_id = request_body.get('engineer_id')
    if engineer_id is not None and type(engineer_id) != int:
        return {'success': False, 'message': "engineer_id is not integer"}, 400
    # if engineer_id is not None and db_iteraction.get_employee(id=engineer_id)['count'] == 0:
    #     return {'success': False, 'message': 'engineer_id is not defined'}, 400

    manager_id = request_body.get('manager_id')
    if manager_id is not None and type(manager_id) != int:
        return {'success': False, 'message': "manager_id is not integer"}, 400
    # if manager_id is not None and db_iteraction.get_employee(id=manager_id)['count'] == 0:
    #     return {'success': False, 'message': 'manager_id is not defined'}, 400

    kindof_good_id = request_body.get('kindof_good_id')
    if kindof_good_id is not None and type(kindof_good_id) != int:
        return {'success': False, 'message': "kindof_good_id is not integer"}, 400
    # if kindof_good_id is not None and db_iteraction.get_equipment_type(id=kindof_good_id)[0]['count'] == 0:
    #     return {'success': False, 'message': 'kindof_good_id is not defined'}, 400

    brand_id = request_body.get('brand_id')
    if brand_id is not None and type(brand_id) != int:
        return {'success': False, 'message': "brand_id is not integer"}, 400
    # if brand_id is not None and db_iteraction.get_equipment_brand(id=brand_id)[0]['count'] == 0:
    #     return {'success': False, 'message': 'brand_id is not defined'}, 400

    subtype_id = request_body.get('subtype_id')
    if subtype_id is not None and type(subtype_id) != int:
        return {'success': False, 'message': "subtype_id is not integer"}, 400
    # if subtype_id is not None and db_iteraction.get_equipment_subtype(id=subtype_id)[0]['count'] == 0:
    #     return {'success': False, 'message': 'subtype_id is not defined'}, 400

    model_id = request_body.get('model_id')
    if model_id is not None and type(model_id) != int:
        return {'success': False, 'message': "model_id is not integer"}, 400
    # if model is not None and db_iteraction.get_equipment_model(id=model_id)[0]['count'] == 0:
    #     return {'success': False, 'message': 'model_id is not defined'}, 400

    id_label = request_body.get('id_label')
    if id_label is not None:
        id_label = str(id_label)

    prefix = request_body.get('prefix')
    if prefix is not None:
        prefix = str(prefix)

    serial = request_body.get('serial')
    if serial is not None:
        serial = str(serial)

    malfunction = request_body.get('malfunction')
    if malfunction is not None:
        malfunction = str(malfunction)

    packagelist = request_body.get('packagelist')
    if packagelist is not None:
        packagelist = str(packagelist)

    appearance = request_body.get('appearance')
    if appearance is not None:
        appearance = str(appearance)

    manager_notes = request_body.get('manager_notes')
    if manager_notes is not None:
        manager_notes = str(manager_notes)

    engineer_notes = request_body.get('engineer_notes')
    if engineer_notes is not None:
        engineer_notes = str(engineer_notes)

    resume = request_body.get('resume')
    if resume is not None:
        resume = str(resume)

    cell = request_body.get('cell')
    if cell is not None:
        cell = str(cell)

    estimated_cost = request_body.get('estimated_cost')
    if estimated_cost is not None:
        try:
            estimated_cost = float(estimated_cost)
        except:
            return {'success': False, 'message': 'estimated_cost is not number'}, 400

    urgent = request_body.get('urgent')
    if urgent is not None and type(urgent) != bool:
        return {'success': False, 'message': 'urgent is not boolean'}, 400

    r_filter = request_body.get('filter')
    if r_filter:

        if r_filter.get('sort'):
            r_filter['sort'] = str(r_filter['sort'])

        if r_filter.get('field_sort'):
            r_filter['field_sort'] = str(r_filter['field_sort'])

        if r_filter.get('search'):
            r_filter['search'] = str(r_filter['search'])

        if r_filter.get('page') is not None and type(r_filter['page']) != int:
            return {'success': False, 'message': "page is not integer in order filter"}, 400

        if r_filter.get('kindof_good_id') is not None and type(r_filter['kindof_good_id']) != int:
            return {'success': False, 'message': "kindof_good_id is not integer in order filter"}, 400

        if r_filter.get('brand_id') is not None and type(r_filter['brand_id']) != int:
            return {'success': False, 'message': "brand_id is not integer in order filter"}, 400

        if r_filter.get('subtype_id') is not None and type(r_filter['subtype_id']) != int:
            return {'success': False, 'message': "subtype_id is not integer in order filter"}, 400

        if r_filter.get('client_id') is not None and type(r_filter['client_id']) != int:
            return {'success': False, 'message': "client_id is not integer in order filter"}, 400

        if r_filter.get('update_order') is not None and type(r_filter['update_order']) != int:
            return {'success': False, 'message': "update_order is not integer in order filter"}, 400

        if r_filter.get('created_at') is not None:
            if type(r_filter['created_at']) != list:
                return {'success': False, 'message': "created_at is not list in order filter"}, 400
            if len(r_filter['created_at']) != 2:
                return {'success': False, 'message': "created_at is not correct in order filter"}, 400
            if (type(r_filter['created_at'][0]) != int) or (type(r_filter['created_at'][1]) != int):
                return {'success': False, 'message': "created_at has not integers in order filter"}, 400

        if r_filter.get('engineer_id') is not None:
            if type(r_filter['engineer_id']) != list:
                return {'success': False, 'message': "engineer_id is not list in order filter"}, 400
            if not all([type(engineer) == int for engineer in r_filter['engineer_id']]):
                return {'success': False, 'message': "engineer_id has not integer in order filter"}, 400

        if r_filter.get('status_id') is not None:
            if type(r_filter['status_id']) != list:
                return {'success': False, 'message': "status_id is not list in order filter"}, 400
            if not all([type(status) == int for status in r_filter['status_id']]):
                return {'success': False, 'message': "status_id has not integer in order filter"}, 400

        if r_filter.get('order_type_id') is not None:
            if type(r_filter['order_type_id']) != list:
                return {'success': False, 'message': "order_type_id is not list"}, 400
            if not all([type(order_type) == int for order_type in r_filter['order_type_id']]):
                return {'success': False, 'message': "order_type_id has not integer in order filter"}, 400

        if r_filter.get('manager_id') is not None:
            if type(r_filter['manager_id']) != list:
                return {'success': False, 'message': "manager_id is not list in order filter"}, 400
            if not all([type(manager) == int for manager in r_filter['manager_id']]):
                return {'success': False, 'message': "manager_id has not integer in order filter"}, 400

        if r_filter.get('overdue') is not None and type(r_filter['overdue']) != bool:
            return {'success': False, 'message': "overdue is not boolean in order filter"}, 400

        if r_filter.get('status_overdue') is not None and type(r_filter['status_overdue']) != bool:
            return {'success': False, 'message': "status_overdue is not boolean in order filter"}, 400

        if r_filter.get('branch_id') is not None and type(r_filter['branch_id']) != int:
            return {'success': False, 'message': "branch_id is not integer in order filter"}, 400
        if r_filter.get('branch_id') is not None and not db_iteraction.pgsql_connetction.session.query(Branch).get(r_filter['branch_id']):
            return {'success': False, 'message': 'branch_id is not defined in order filter'}, 400

        if r_filter.get('urgent') is not None and type(r_filter['urgent']) != bool:
            return {'success': False, 'message': "urgent is not boolean in order filter"}, 400

        if r_filter.get('update_badges') is not None and type(r_filter['update_badges']) != bool:
            return {'success': False, 'message': "update_badges is not boolean in order filter"}, 400


    if request.method == 'POST':
        if not status_id:
            return {'success': False, 'message': 'status_id required'}, 400

        # Достаем значение счетчика и инкременируем его
        counter = db_iteraction.get_counts(id=1)['data'][0]
        id_label = f'{counter["prefix"]}-{counter["count"]}'
        db_iteraction.inc_count(id=1)

        result = db_iteraction.add_orders(
            created_at=created_at,                      # int - дата создания
            done_at=done_at,                            # int - дата готовность
            closed_at=closed_at,                        # int - дата закрытия
            assigned_at=assigned_at,                    # int - назначен на время
            duration=duration,                          # int - длительность
            estimated_done_at=estimated_done_at,        # int - запланированная дата готовности
            scheduled_for=scheduled_for,                # int - запланирован на
            warranty_date=warranty_date,                # int - дата гарантии до
            status_deadline=status_deadline,            # int - срок статуса до

            ad_campaign_id=ad_campaign_id,              # int - id рекламной компании
            branch_id=branch_id,                        # int - id филиала
            status_id=status_id,                        # int - id статуса
            client_id=client_id,                        # int - id клиента
            order_type_id=order_type_id,                # int - id заказа
            closed_by_id=closed_by_id,                  # int - id сотрдника который закрыл заказ
            created_by_id=created_by_id,                # int - id сотрудника который созда заказ
            engineer_id=engineer_id,                    # int - id сотрудника
            manager_id=manager_id,                      # int - id сотрудника

            id_label=id_label,                          # str - номер заказа
            prefix=counter["prefix"],                   # str - префикс
            kindof_good_id=kindof_good_id,              # str - тип техники
            brand_id=brand_id,                          # str - бренд
            model_id=model_id,                          # str - модель
            subtype_id=subtype_id,                      # str - модификация
            serial=serial,                              # str - сирийный номер
            malfunction=malfunction,                    # str - неисправность
            packagelist=packagelist,                    # str - комплектация
            appearance=appearance,                      # str - внешний вид
            manager_notes=manager_notes,                # str - заметки менеджера
            engineer_notes=engineer_notes,              # str - заметки инженера
            resume=resume,                              # str - вердикт
            cell=cell,

            estimated_cost=estimated_cost,              # float - ориентировочная стоимость

            urgent=urgent,                              # boll - срочный

            user_id=user_id,
            r_filter=r_filter
        )

        return result


    # Проверим сущестует ли запись по данному id
    if not db_iteraction.pgsql_connetction.session.query(Orders).get(id):
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':

        result = db_iteraction.edit_orders(
            id=id,                                  # int - id записи - полное совпаден
            created_at=created_at,                  # int - дата создания
            done_at=done_at,                        # int - дата готовность
            closed_at=closed_at,                    # int - дата закрытия
            assigned_at=assigned_at,                # int - назначен на время
            duration=duration,                      # int - длительность
            estimated_done_at=estimated_done_at,    # int - запланированная дата готовности
            scheduled_for=scheduled_for,            # int - запланирован на
            warranty_date=warranty_date,            # int - дата гарантии до
            status_deadline=status_deadline,        # int - срок статуса до

            ad_campaign_id=ad_campaign_id,          # int - id рекламной компании
            branch_id=branch_id,                    # int - id филиала
            status_id=status_id,                    # int - id статуса
            client_id=client_id,                    # int - id клиента
            order_type_id=order_type_id,            # int - id заказа
            closed_by_id=closed_by_id,              # int - id сотрдника который закрыл заказ
            created_by_id=created_by_id,            # int - id сотрудника который созда заказ
            engineer_id=engineer_id,                # int - id сотрудника
            manager_id=manager_id,                  # int - id сотрудника

            id_label=id_label,                      # str - номер заказа
            prefix=prefix,                          # str - префикс
            kindof_good_id=kindof_good_id,          # str - тип техники
            brand_id=brand_id,                      # str - бренд
            model_id=model_id,                      # str - модель
            subtype_id=subtype_id,                  # str - модификация
            serial=serial,                          # str - сирийный номер
            malfunction=malfunction,                # str - неисправность
            packagelist=packagelist,                # str - комплектация
            appearance=appearance,                  # str - внешний вид
            manager_notes=manager_notes,            # str - заметки менеджера
            engineer_notes=engineer_notes,          # str - заметки инженера
            resume=resume,                          # str - вердикт
            cell=cell,

            estimated_cost=estimated_cost,          # float - ориентировочная стоимость
            urgent=urgent,                          # boll - срочный
            user_id=user_id,
            r_filter=r_filter
        )
        return result


    if request.method == 'DELETE':

        return db_iteraction.del_orders(id=id)           # int - id записи - полное совпаден

