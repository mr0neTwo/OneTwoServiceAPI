import traceback

from flask import Blueprint
from flask_jwt_extended import jwt_required
from flask import request

from app.db.interaction.db_iteraction import db_iteraction
from app.events import event_create_order

orders_api = Blueprint('orders_api', __name__)

@orders_api.route('/get_orders', methods=['POST'])
@jwt_required()
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

    done_at = request_body.get('done_at')
    if done_at is not None:
        if type(done_at) != list:
            return {'success': False, 'message': "done_at is not list"}, 400
        if len(done_at) != 2:
            return {'success': False, 'message': "done_at is not correct"}, 400
        if type(done_at[0]) != int:
            return {'success': False, 'message': "done_at has not integers"}, 400
        if type(done_at[1]) and type(done_at[1]) != int:
            return {'success': False, 'message': "done_at has not integers"}, 400

    closed_at = request_body.get('closed_at')
    if closed_at is not None:
        if type(closed_at) != list:
            return {'success': False, 'message': "closed_at is not list"}, 400
        if len(closed_at) != 2:
            return {'success': False, 'message': "closed_at is not correct"}, 400
        if type(closed_at[0]) != int:
            return {'success': False, 'message': "closed_at has not integers"}, 400
        if type(closed_at[1]) and type(closed_at[1]) != int:
            return {'success': False, 'message': "closed_at has not integers"}, 400

    assigned_at = request_body.get('assigned_at')
    if assigned_at is not None:
        if type(assigned_at) != list:
            return {'success': False, 'message': "assigned_at is not list"}, 400
        if len(assigned_at) != 2:
            return {'success': False, 'message': "assigned_at is not correct"}, 400
        if type(assigned_at[0]) != int:
            return {'success': False, 'message': "assigned_at has not integers"}, 400
        if type(assigned_at[1]) and type(assigned_at[1]) != int:
            return {'success': False, 'message': "assigned_at has not integers"}, 400

    estimated_done_at = request_body.get('estimated_done_at')
    if estimated_done_at is not None:
        if type(estimated_done_at) != list:
            return {'success': False, 'message': "estimated_done_at is not list"}, 400
        if len(estimated_done_at) != 2:
            return {'success': False, 'message': "estimated_done_at is not correct"}, 400
        if type(estimated_done_at[0]) != int:
            return {'success': False, 'message': "estimated_done_at has not integers"}, 400
        if type(estimated_done_at[1]) and type(estimated_done_at[1]) != int:
            return {'success': False, 'message': "estimated_done_at has not integers"}, 400

    scheduled_for = request_body.get('scheduled_for')
    if scheduled_for is not None:
        if type(scheduled_for) != list:
            return {'success': False, 'message': "scheduled_for is not list"}, 400
        if len(scheduled_for) != 2:
            return {'success': False, 'message': "scheduled_for is not correct"}, 400
        if type(scheduled_for[0]) != int:
            return {'success': False, 'message': "scheduled_for has not integers"}, 400
        if type(scheduled_for[1]) and type(scheduled_for[1]) != int:
            return {'success': False, 'message': "scheduled_for has not integers"}, 400

    warranty_date = request_body.get('warranty_date')
    if warranty_date is not None:
        if type(warranty_date) != list:
            return {'success': False, 'message': "warranty_date is not list"}, 400
        if len(warranty_date) != 2:
            return {'success': False, 'message': "warranty_date is not correct"}, 400
        if type(warranty_date[0]) != int:
            return {'success': False, 'message': "warranty_date has not integers"}, 400
        if type(warranty_date[1]) and type(warranty_date[1]) != int:
            return {'success': False, 'message': "warranty_date has not integers"}, 400

    ad_campaign_id = request_body.get('ad_campaign_id')
    if ad_campaign_id is not None and type(ad_campaign_id) != list:
        return {'success': False, 'message': "ad_campaign_id is not list"}, 400
    if ad_campaign_id is not None:
        if not all([type(ad_cam) == int for ad_cam in ad_campaign_id]):
            return {'success': False, 'message': "ad_campaign_id has not integer"}, 400

    branch_id = request_body.get('branch_id')
    if branch_id is not None and type(branch_id) != list:
        return {'success': False, 'message': "branch_id is not list"}, 400
    if branch_id  is not None:
        if not all([type(branch) == int for branch in branch_id]):
            return {'success': False, 'message': "branch_id has not integer"}, 400

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

    closed_by_id = request_body.get('closed_by_id')
    if closed_by_id is not None and type(closed_by_id) != list:
        return {'success': False, 'message': "closed_by_id is not list"}, 400
    if closed_by_id is not None:
        if not all([type(closed_by) == int for closed_by in closed_by_id]):
            return {'success': False, 'message': "closed_by_id has not integer"}, 400

    created_by_id = request_body.get('created_by_id')
    if created_by_id is not None and type(created_by_id) != list:
        return {'success': False, 'message': "created_by_id is not list"}, 400
    if created_by_id is not None:
        if not all([type(created_by) == int for created_by in created_by_id]):
            return {'success': False, 'message': "created_by_id has not integer"}, 400

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

    id_label = request_body.get('id_label')
    if id_label:
        id_label = str(id_label)

    kindof_good = request_body.get('kindof_good')
    if kindof_good is not None and type(kindof_good) != int:
        return {'success': False, 'message': "kindof_good is not integer"}, 400
    if kindof_good is not None and db_iteraction.get_equipment_type(id=kindof_good)[0]['count'] == 0:
        return {'success': False, 'message': 'kindof_good is not defined'}, 400

    brand = request_body.get('brand')
    if brand is not None and type(brand) != int:
        return {'success': False, 'message': "brand is not integer"}, 400
    if brand is not None and db_iteraction.get_equipment_brand(id=brand)[0]['count'] == 0:
        return {'success': False, 'message': 'brand is not defined'}, 400

    # model = request_body.get('model')
    # if model:
    #     model = str(model)

    subtype = request_body.get('subtype')
    if subtype is not None and type(subtype) != int:
        return {'success': False, 'message': "subtype is not integer"}, 400
    if subtype is not None and db_iteraction.get_equipment_subtype(id=subtype)[0]['count'] == 0:
        return {'success': False, 'message': 'subtype is not defined'}, 400

    serial = request_body.get('serial')
    if serial is not None:
        serial = str(serial)

    cell = request_body.get('cell')
    if cell is not None:
        cell = str(cell)

    client_name = request_body.get('client_name')
    if client_name is not None:
        client_name = str(client_name)

    client_phone = request_body.get('client_phone')
    if client_phone is not None:
        client_phone = str(client_phone)

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

    try:
        result = db_iteraction.get_orders(
            id=id,                                  # int - id филиала - полное совпадение
            created_at=created_at,                  # [int - int] - даты создания - промежуток
            done_at=done_at,                        # [int - int] - даты готовности - промежуток
            closed_at=closed_at,                    # [int - int] - даты закрытия - промежуток
            assigned_at=assigned_at,                # [int - int] - даты назначен на - промежуток
            estimated_done_at=estimated_done_at,    # [int - int] - запланированные даты готовности - промежуток
            scheduled_for=scheduled_for,            # [int - int] - даты запланирован на - промежуток
            warranty_date=warranty_date,            # [int - int] - даты горании до - промежуток

            ad_campaign_id=ad_campaign_id,          # list - id рекламной копании - полное совпадение одного из списка
            branch_id=branch_id,                    # list - id филиала - полное совпадение одного из списка
            status_id=status_id,                    # list - id статуса - полное совпадение одного из списка
            client_id=client_id,                    # list - id клиента - полное совпадение одного из списка
            order_type_id=order_type_id,            # list - id типа заказа - полное совпадение одного из списка
            engineer_id=engineer_id,                # list - id сотрудника - полное совпадение одного из списка
            manager_id=manager_id,                  # list - id сотрудника - полное совпадение одного из списка

            id_label=id_label,
            kindof_good=kindof_good,
            brand=brand,
            # model=model,
            subtype=subtype,
            serial=serial,
            client_name=client_name,
            client_phone=client_phone,
            search=search,
            cell=cell,

            overdue=overdue,
            status_overdue=status_overdue,
            urgent=urgent,
            page=page,                         # int - Старница погинации
            field_sort=field_sort,
            sort=sort
        )
        return result, 200
    except:
        print(traceback.format_exc())
        return {'success': False, 'message': 'server error'}, 550

@orders_api.route('/orders', methods=['POST', 'PUT', 'DELETE'])
@jwt_required()
def orders():
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
    if ad_campaign_id is not None and db_iteraction.get_adCampaign(id=ad_campaign_id)['count'] == 0:
        return {'success': False, 'message': 'ad_campaign_id is not defined'}, 400

    branch_id = request_body.get('branch_id')
    if branch_id is not None and type(branch_id) != int:
        return {'success': False, 'message': "branch_id is not integer"}, 400
    if branch_id is not None and db_iteraction.get_branch(id=branch_id)['count'] == 0:
        return {'success': False, 'message': 'branch_id is not defined'}, 400

    status_id = request_body.get('status_id')
    if status_id is not None and type(status_id) != int:
        return {'success': False, 'message': "status_id is not integer"}, 400
    if status_id is not None and db_iteraction.get_status(id=status_id)['count'] == 0:
        return {'success': False, 'message': 'status_id is not defined'}, 400

    client_id = request_body.get('client_id')
    if client_id is not None and type(client_id) != int:
        return {'success': False, 'message': "client_id is not integer"}, 400
    if client_id is not None and db_iteraction.get_clients(id=client_id)['count'] == 0:
        return {'success': False, 'message': 'client_id is not defined'}, 400

    order_type_id = request_body.get('order_type_id')
    if order_type_id is not None and type(order_type_id) != int:
        return {'success': False, 'message': "order_type_id is not integer"}, 400
    if order_type_id is not None and db_iteraction.get_order_type(id=order_type_id)['count'] == 0:
        return {'success': False, 'message': 'order_type_id is not defined'}, 400

    closed_by_id = request_body.get('closed_by_id')
    if closed_by_id is not None and type(closed_by_id) != int:
        return {'success': False, 'message': "closed_by_id is not integer"}, 400
    if closed_by_id is not None and db_iteraction.get_employee(id=closed_by_id)['count'] == 0:
        return {'success': False, 'message': 'closed_by_id is not defined'}, 400

    created_by_id = request_body.get('created_by_id')
    if created_by_id is not None and type(created_by_id) != int:
        return {'success': False, 'message': "created_by_id is not integer"}, 400
    if created_by_id is not None and db_iteraction.get_employee(id=created_by_id)['count'] == 0:
        return {'success': False, 'message': 'created_by_id is not defined'}, 400

    engineer_id = request_body.get('engineer_id')
    if engineer_id is not None and type(engineer_id) != int:
        return {'success': False, 'message': "engineer_id is not integer"}, 400
    if engineer_id is not None and db_iteraction.get_employee(id=engineer_id)['count'] == 0:
        return {'success': False, 'message': 'engineer_id is not defined'}, 400

    manager_id = request_body.get('manager_id')
    if manager_id is not None and type(manager_id) != int:
        return {'success': False, 'message': "manager_id is not integer"}, 400
    if manager_id is not None and db_iteraction.get_employee(id=manager_id)['count'] == 0:
        return {'success': False, 'message': 'manager_id is not defined'}, 400

    kindof_good = request_body.get('kindof_good')
    if kindof_good is not None and type(kindof_good) != int:
        return {'success': False, 'message': "kindof_good is not integer"}, 400
    if kindof_good is not None and db_iteraction.get_equipment_type(id=kindof_good)[0]['count'] == 0:
        return {'success': False, 'message': 'kindof_good is not defined'}, 400

    brand = request_body.get('brand')
    if brand is not None and type(brand) != int:
        return {'success': False, 'message': "brand is not integer"}, 400
    if brand is not None and db_iteraction.get_equipment_brand(id=brand)[0]['count'] == 0:
        return {'success': False, 'message': 'brand is not defined'}, 400

    subtype = request_body.get('subtype')
    if subtype is not None and type(subtype) != int:
        return {'success': False, 'message': "subtype is not integer"}, 400
    if subtype is not None and db_iteraction.get_equipment_subtype(id=subtype)[0]['count'] == 0:
        return {'success': False, 'message': 'subtype is not defined'}, 400

    model = request_body.get('model')
    if model is not None and type(model) != int:
        return {'success': False, 'message': "model is not integer"}, 400
    if model is not None and db_iteraction.get_equipment_model(id=model)[0]['count'] == 0:
        return {'success': False, 'message': 'model is not defined'}, 400

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

    # missed_payments = request_body.get('missed_payments')
    # if missed_payments is not None:
    #     try:
    #         missed_payments = float(missed_payments)
    #     except:
    #         return {'success': False, 'message': 'missed_payments is not number'}, 400
    #
    # discount_sum = request_body.get('discount_sum')
    # if discount_sum is not None:
    #     try:
    #         discount_sum = float(discount_sum)
    #     except:
    #         return {'success': False, 'message': 'estimated_cost is not number'}, 400
    #
    # payed = request_body.get('payed')
    # if payed:
    #     try:
    #         payed = float(payed)
    #     except:
    #         return {'success': False, 'message': 'payed is not number'}, 400

    price = request_body.get('price')
    if price is not None:
        try:
            price = float(price)
        except:
            return {'success': False, 'message': 'price is not number'}, 400

    urgent = request_body.get('urgent')
    if urgent is not None and type(urgent) != bool:
        return {'success': False, 'message': 'urgent is not boolean'}, 400

    if request.method == 'POST':
        if not status_id:
            return {'success': False, 'message': 'status_id required'}, 400

        equipments = request_body.get('equipments')
        try:
            for equipment in equipments:

                # Достаем значение счетчика и инкременируем его
                counter = db_iteraction.get_counts(id=1)['data'][0]
                id_label = f'{counter["prefix"]}-{counter["count"]}'
                db_iteraction.inc_count(id=1)

                order = db_iteraction.add_orders(
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

                    id_label=id_label,                                                                          # str - номер заказа
                    prefix=counter["prefix"],                                                                              # str - префикс
                    kindof_good=equipment.get('kindof_good')['id'] if equipment.get('kindof_good') else None,   # str - тип техники
                    brand=equipment.get('brand')['id'] if equipment.get('brand') else None,                     # str - бренд
                    model=equipment.get('model')['id'] if equipment.get('model') else None,                     # str - модель
                    subtype=equipment.get('subtype')['id'] if equipment.get('subtype') else None,               # str - модификация
                    serial=equipment.get('serial'),                                                             # str - сирийный номер
                    malfunction=equipment.get('malfunction'),                                                   # str - неисправность
                    packagelist=equipment.get('packagelist'),                                                   # str - комплектация
                    appearance=equipment.get('appearance'),                                                     # str - внешний вид
                    manager_notes=manager_notes,                                                                # str - заметки менеджера
                    engineer_notes=engineer_notes,                                                              # str - заметки инженера
                    resume=resume,                                                                              # str - вердикт
                    cell=cell,

                    estimated_cost=estimated_cost,              # float - ориентировочная стоимость
                    price=price,                                # float - стоимость

                    urgent=urgent                               # boll - срочный
                )
                event_create_order(db_iteraction, order)
            return {'success': True, 'data': order, 'message': f'{id_label} added'}, 201
        except:
            print(traceback.format_exc())
            return {'success': False, 'message': 'server error'}, 550

    # Проверим сущестует ли запись по данному id
    if db_iteraction.get_orders(id=id)['count'] == 0:
        return {'success': False, 'message': 'id is not defined'}, 400

    if request.method == 'PUT':

        try:
            db_iteraction.edit_orders(
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
                kindof_good=kindof_good,                # str - тип техники
                brand=brand,                            # str - бренд
                model=model,                            # str - модель
                subtype=subtype,                        # str - модификация
                serial=serial,                          # str - сирийный номер
                malfunction=malfunction,                # str - неисправность
                packagelist=packagelist,                # str - комплектация
                appearance=appearance,                  # str - внешний вид
                manager_notes=manager_notes,            # str - заметки менеджера
                engineer_notes=engineer_notes,          # str - заметки инженера
                resume=resume,                          # str - вердикт
                cell=cell,

                estimated_cost=estimated_cost,          # float - ориентировочная стоимость
                price=price,                            # float - стоимость

                urgent=urgent                           # boll - срочный
            )
            return {'success': True, 'message': f'{id} changed'}, 202
        except:
            print(traceback.format_exc())
            return {'success': False, 'message': 'server error'}, 550

    if request.method == 'DELETE':
        try:
            db_iteraction.del_orders(
                id=id)           # int - id записи - полное совпаден
            return {'success': True, 'message': f'{id} deleted'}, 202
        except:
            print(traceback.format_exc())
            return {'success': False, 'message': 'server error'}, 550