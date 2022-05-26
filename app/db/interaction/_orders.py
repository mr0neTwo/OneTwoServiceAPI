import inspect
import time
import traceback
from datetime import datetime, timedelta
from pprint import pprint

from sqlalchemy import or_, desc, func

from app.db.models.models import Orders, time_now, Clients, Phones, Events, Employees, Branch, AdCampaign, OrderType, \
    Schedule
from app.db.models.models import Status, EquipmentType, EquipmentBrand, EquipmentSubtype, EquipmentModel
from app.events import event_create_order


def get_estimate_work_time(estimated_done_at, schedule):
    # Расчитаем дедлайн
    now = datetime.now()
    done_at = datetime.fromtimestamp(estimated_done_at)

    # Если статус не просрочен
    if estimated_done_at - now.timestamp() > 0:
        # Количество дней
        days = done_at.toordinal() - now.toordinal()
        # Найдем количество рабочих дней
        work_days = 0
        current_day = datetime.now()
        for day in range(days):
            week_day = current_day.isoweekday()
            if schedule[week_day]['work_day']:
                work_days += 1
            current_day += timedelta(days=1)
        if work_days >= 3:
            return timedelta(days=work_days).total_seconds()
        # Если день окончания - текущий день
        if days == 0:
            # Если сегодня не рабочий день
            week_day = done_at.isoweekday()
            if not schedule[week_day]['work_day']:
                return 0
            # Если сегодня рабочий день - рассчитаем
            else:
                start = schedule[week_day]['start_time'].split(':')
                end = schedule[week_day]['end_time'].split(':')
                start_time = datetime.now().replace(hour=int(start[0]), minute=int(start[1]))
                end_time = datetime.now().replace(hour=int(end[0]), minute=int(end[1]))
                # Если рабочее время не настало и дата оканчания находится в пределах рабочего времени
                if now < start_time and done_at >= start_time and done_at <= end_time:
                    return (done_at - start_time).total_seconds()
                # Если рабочие време не настало и дата окончания за предалими рабочего времени
                if now < start_time and done_at > end_time:
                    return (end_time - start_time).total_seconds()
                # Если сейчас рабочее время и дата окончания в предалах рабочего времени
                if now >= start_time and now <= end_time and done_at <= end_time:
                    return (done_at - now).total_seconds()
                # Если сейчас рабочее время и дата окончания за пределами рабочего времени
                if now >= start_time and now <= end_time and done_at > end_time:
                    return (end_time - now).total_seconds()
                # Если сейчас за пределами рабочего времени и дата окончания за пределами рабочего времени
                if now > end_time and done_at > end_time:
                    return 0
        # Если день окончания ранее одного дня
        else:
            estimate_work_time = 0

            for n in range(days + 1):
                week_day = now.isoweekday()
                if schedule[week_day]['work_day']:
                    start = schedule[week_day]['start_time'].split(':')
                    end = schedule[week_day]['end_time'].split(':')
                    start_time = now.replace(hour=int(start[0]), minute=int(start[1]))
                    end_time = now.replace(hour=int(end[0]), minute=int(end[1]))
                    # Считаем первый день
                    if n == 0:
                        # Если текущее время до рабочего дня
                        if now < start_time:
                            estimate_work_time += (end_time - start_time).total_seconds()
                        # Если текущее время это рабочее время
                        if now >= start_time and now <= end_time:
                            estimate_work_time += (end_time - now).total_seconds()
                    # Считаем последний день
                    if n == days:
                        # Если срок заканчивается во время рабочего дня рабочего дня
                        if done_at >= start_time and done_at <= end_time:
                            estimate_work_time += (done_at - start_time).total_seconds()
                        # Если срок заканчивается после рабочего дня
                        if done_at > end_time:
                            estimate_work_time += (end_time - start_time).total_seconds()
                    # Считаем промежуточные дни
                    if n > 0 and n < days:
                        estimate_work_time += (end_time - start_time).total_seconds()

                now += timedelta(days=1)

            return estimate_work_time
    # Если статус просрочен
    else:
        # Количество дней
        days = now.toordinal() - done_at.toordinal()
        # Найдем количество рабочих дней
        work_days = 0
        current_day = datetime.fromtimestamp(estimated_done_at)
        for day in range(days):
            week_day = current_day.isoweekday()
            if schedule[week_day]['work_day']:
                work_days += 1
            current_day += timedelta(days=1)
        if work_days >= 3:
            return -timedelta(days=work_days).total_seconds()
        # Если день окончания - текущий день
        if days == 0:
            # Если сегодня не рабочий день
            week_day = done_at.isoweekday()
            if not schedule[week_day]['work_day']:
                return 0
            # Если сегодня рабочий день - рассчитаем
            else:
                start = schedule[week_day]['start_time'].split(':')
                end = schedule[week_day]['end_time'].split(':')
                start_time = datetime.now().replace(hour=int(start[0]), minute=int(start[1]))
                end_time = datetime.now().replace(hour=int(end[0]), minute=int(end[1]))
                # Если рабочее время не настало и дата окончания до рабочего времени
                if now < start_time and done_at < start_time:
                    return 0
                # Если сейчас рабочее время и дата окончания находится в предалах рабочего времени
                if now > start_time and now < end_time and done_at > start_time and done_at < end_time:
                    return -(now - done_at).total_seconds()
                # Если уже за пределами рабочего времени и дата окончания в рабочем времени
                if now > end_time and done_at > start_time and done_at < end_time:
                    return -(end_time - done_at).total_seconds()
                # Если уже за предалими рабочего времени и дата окончания до начала рабочего времени
                if now > end_time and done_at < start_time:
                    return -(end_time - start_time).total_seconds()
                # Если уже за пределами рабочего времени и дата окончания за пределами рабочего времени
                if now > end_time and done_at > end_time:
                    return 0
        # Если день позже ранее одного дня
        else:
            estimate_work_time = 0

            for n in range(days + 1):
                week_day = done_at.isoweekday()
                if schedule[week_day]['work_day']:
                    start = schedule[week_day]['start_time'].split(':')
                    end = schedule[week_day]['end_time'].split(':')
                    start_time = done_at.replace(hour=int(start[0]), minute=int(start[1]))
                    end_time = done_at.replace(hour=int(end[0]), minute=int(end[1]))
                    # Считаем первый день
                    if n == 0:
                        # Если срок заканчивается до рабочего дня
                        if done_at < start_time:
                            estimate_work_time += (end_time - start_time).total_seconds()
                        # Если срок заканчивается во время рабочего дня
                        if done_at >= start_time and done_at <= end_time:
                            estimate_work_time += (end_time - done_at).total_seconds()
                    # Считаем последний день
                    if n == days:
                        # Если сейчас рабочее время
                        if now >= start_time and now <= end_time:
                            estimate_work_time += (now - start_time).total_seconds()
                        # Если сейчас уже после рабочего времени
                        if now > end_time:
                            estimate_work_time += (end_time - start_time).total_seconds()
                    # Считаем промежуточные дни
                    if n > 0 and n < days:
                        estimate_work_time += (end_time - start_time).total_seconds()

                done_at += timedelta(days=1)

            return -estimate_work_time



def get_order_by_id(self, id):
    try:
        order = self.pgsql_connetction.session.query(Orders).get(id)

        branch_id = order.branch_id
        query = self.pgsql_connetction.session.query(Schedule)
        query = query.filter(Schedule.branch_id == branch_id)
        data_schedule = query.all()
        schedule = {}
        for day in data_schedule:
            schedule[day.week_day] = {
                'work_day': day.work_day,
                'start_time': day.start_time,
                'end_time': day.end_time
            }

        data_order = {
            'id': order.id,
            'created_at': order.created_at,
            'updated_at': order.updated_at,
            'done_at': order.done_at,
            'closed_at': order.closed_at,
            'assigned_at': order.assigned_at,
            'duration': order.duration,
            'estimated_done_at': order.estimated_done_at,
            'scheduled_for': order.scheduled_for,
            'warranty_date': order.warranty_date,
            'status_deadline': order.status_deadline,

            'id_label': order.id_label,
            'prefix': order.prefix,
            'serial': order.serial,
            'malfunction': order.malfunction,
            'packagelist': order.packagelist,
            'appearance': order.appearance,
            'engineer_notes': order.engineer_notes,
            'manager_notes': order.manager_notes,
            'resume': order.resume,
            'cell': order.cell,

            'estimated_cost': order.estimated_cost,
            'missed_payments': order.missed_payments,
            'discount_sum': order.discount_sum,
            'payed': order.payed,
            'price': order.price,
            'remaining': get_estimate_work_time(order.estimated_done_at, schedule),
            'remaining_status': order.status_deadline - time_now() if order.status_deadline else None,
            'remaining_warranty': order.warranty_date - time_now() if order.warranty_date else None,

            'overdue': order.estimated_done_at > time_now() if order.estimated_done_at else False,
            'status_overdue': order.status_deadline > time_now() if order.status_deadline else False,
            'urgent': order.urgent,
            'warranty_measures': order.warranty_date < time_now() if order.warranty_date else False,

            'ad_campaign': {
                'id': order.ad_campaign.id,
                'name': order.ad_campaign.name
            } if order.ad_campaign else {},
            'branch': {
                'id': order.branch.id,
                'name': order.branch.name
            } if order.branch else {},
            'status': {
                'id': order.status.id,
                'name': order.status.name,
                'color': order.status.color,
                'group': order.status.group
            } if order.status else {},
            'client': {
                'id': order.client.id,
                'ad_campaign': {
                    'id': order.client.ad_campaign.id,
                    'name': order.client.ad_campaign.name
                },
                'address': order.client.address,
                'conflicted': order.client.conflicted,
                'name_doc': order.client.name_doc,

                'discount_good_type': order.client.discount_good_type,
                'discount_materials_type': order.client.discount_materials_type,
                'discount_service_type': order.client.discount_service_type,

                'discount_code': order.client.discount_code,

                'discount_goods': order.client.discount_goods,
                'discount_goods_margin_id': order.client.discount_goods_margin_id,

                'discount_materials': order.client.discount_materials,
                'discount_materials_margin_id': order.client.discount_materials_margin_id,

                'discount_services': order.client.discount_services,
                'discount_service_margin_id': order.client.discount_service_margin_id,

                'email': order.client.email,
                'juridical': order.client.juridical,
                'ogrn': order.client.ogrn,
                'inn': order.client.inn,
                'kpp': order.client.kpp,
                'juridical_address': order.client.juridical_address,
                'director': order.client.director,
                'bank_name': order.client.bank_name,
                'settlement_account': order.client.settlement_account,
                'corr_account': order.client.corr_account,
                'bic': order.client.bic,
                'created_at': order.client.created_at,
                'updated_at': order.client.updated_at,
                'name': order.client.name,
                'notes': order.client.notes,
                'supplier': order.client.supplier,
                'phone': [{
                    'id': ph.id,
                    'number': ph.number,
                    'title': ph.title,
                    'notify': ph.notify
                } for ph in order.client.phone] if order.client.phone else []
            } if order.client else {},
            'order_type': {
                'id': order.order_type.id,
                'name': order.order_type.name
            } if order.order_type else {},
            'kindof_good': {
                'id': order.kindof_good.id,
                'title': order.kindof_good.title,
                'icon': order.kindof_good.icon,
            } if order.kindof_good else {},
            'brand': {
                'id': order.brand.id,
                'title': order.brand.title,
            } if order.brand else {},
            'subtype': {
                'id': order.subtype.id,
                'title': order.subtype.title,
            } if order.subtype else {},
            'model': {
                'id': order.model.id,
                'title': order.model.title,
            } if order.model else {},
            'closed_by_id': order.closed_by_id,
            'created_by_id': order.created_by_id,
            'engineer_id': order.engineer_id,
            'manager_id': order.manager_id,
            'operations': [{
                'id': operat.id,
                'amount': operat.amount,
                'cost': operat.cost,
                'discount_value': operat.discount_value,
                'engineer_id': operat.engineer_id,
                'price': operat.price,
                'total': operat.total,
                'warranty': (operat.created_at + operat.warranty_period) > time_now(),
                'title': operat.title,
                'comment': operat.comment,
                'percent': operat.percent,
                'discount': operat.discount,
                'deleted': operat.deleted,
                'warranty_period': operat.warranty_period,
                'created_at': operat.created_at,
                'dict_service': {
                    'id': operat.dict_service.id,
                    'title': operat.dict_service.title,
                    'earnings_percent': operat.dict_service.earnings_percent,
                    'earnings_summ': operat.dict_service.earnings_summ
                } if operat.dict_service else {},
            } for operat in order.operations] if order.operations else [],
            'parts': [{
                'id': part.id,
                'amount': part.amount,
                'cost': part.cost,
                'discount_value': part.discount_value,
                'engineer_id': part.engineer_id,
                'price': part.price,
                'total': part.total,
                'warranty': (part.created_at + part.warranty_period) > time_now(),
                'title': part.title,
                'comment': part.comment,
                'percent': part.percent,
                'discount': part.discount,
                'deleted': part.deleted,
                'warranty_period': part.warranty_period,
                'created_at': part.created_at
            } for part in order.parts] if order.parts else [],
            # 'attachments': [{
            #     'id': attachment.id,
            #     'amount': attachment.amount,
            #     'cost': attachment.cost,
            #     'discount_value': attachment.discount_value,
            #     'engineer_id': attachment.engineer_id,
            #     'price': attachment.price,
            #     'warranty': attachment.warranty,
            #     'title': attachment.title,
            #     'warranty_period': attachment.warranty_period,
            #     'created_at': attachment.created_at
            # } for attachment in row.attachments] if row.attachments else [],
            'payments': [
                {
                    'id': payment.id,
                    'cashflow_category': payment.cashflow_category,
                    'description': payment.description,
                    'income': payment.income,
                    'outcome': payment.outcome,
                    'direction': payment.direction,
                    'can_print_fiscal': payment.can_print_fiscal,
                    'deleted': payment.deleted,
                    'is_fiscal': payment.is_fiscal,
                    'created_at': payment.created_at,
                    'custom_created_at': payment.custom_created_at,
                    'tags': payment.tags,
                    'relation_id': payment.relation_id,
                    'cashbox': {
                        'id': payment.cashbox.id,
                        'title': payment.cashbox.title,
                        'type': payment.cashbox.type
                    } if payment.cashbox else {},
                    'client': {
                        'id': payment.client.id,
                        'name': payment.client.name,
                        'phone': [ph.number for ph in order.client.phone] if payment.client.phone else []
                    } if payment.client else {},
                    'employee': {
                        'id': payment.employee.id,
                        'name': f'{payment.employee.last_name} {payment.employee.first_name}'
                    } if payment.employee else {},
                    'order': {
                        'id': payment.order.id,
                        'id_label': payment.order.id_label
                    } if payment.order else {}
                } for payment in order.payments
            ] if order.payments else []
        }
        query = self.pgsql_connetction.session.query(Events)
        query = query.filter(Events.object_type == 1)
        query = query.filter(Events.object_id == id)
        query = query.order_by(Events.id)
        events = query.all()

        data_events = []
        for event in events:
            data_events.append({
                'created_at': event.created_at,
                'event_type': event.event_type,
                'current_status': {
                    'id': event.current_status.id,
                    'color': event.current_status.color
                },
                'employee_id': event.employee_id,
                'changed': event.changed
            })

        return data_order, data_events
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def add_order_comment(
        self,
        order_id,
        current_status_id,
        branch_id,
        comment,
        user_id
    ):
    try:
        order_event = Events(
            object_type=1,  # Заказ
            object_id=order_id,
            event_type='ADD_COMMENT',
            current_status_id=current_status_id,
            branch_id=branch_id,
            employee_id=user_id,
            changed=[{
                'title': self.pgsql_connetction.session.query(
                            func.concat(Employees.last_name, ' ', Employees.first_name)).filter_by(id=user_id).scalar(),
                'new': {'title': comment}
            }]
        )
        self.pgsql_connetction.session.add(order_event)
        self.pgsql_connetction.session.flush()

        result = {'success': True}

        query = self.pgsql_connetction.session.query(Events)
        query = query.filter(Events.object_type == 1)
        query = query.filter(Events.object_id == order_id)
        query = query.order_by(Events.id)
        events = query.all()

        data_events = []
        for event in events:
            data_events.append({
                'created_at': event.created_at,
                'event_type': event.event_type,
                'current_status': {
                    'id': event.current_status.id,
                    'color': event.current_status.color
                },
                'employee_id': event.employee_id,
                'changed': event.changed
            })

        print(order_id, current_status_id)

        result['events'] = data_events

        self.pgsql_connetction.session.commit()
        return result, 201
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def get_orders_by_filter(self, filter_order):

    try:
        query = self.pgsql_connetction.session.query(Orders)

        if filter_order.get('created_at') is not None:
            query = query.filter(Orders.created_at >= filter_order['created_at'][0])
            query = query.filter(Orders.created_at <= filter_order['created_at'][1])
        if filter_order.get('status_id') is not None:
            query = query.filter(Orders.status_id.in_(filter_order['status_id']))
        if filter_order.get('order_type_id') is not None:
            query = query.filter(Orders.order_type_id.in_(filter_order['order_type_id']))
        if filter_order.get('engineer_id') is not None:
            query = query.filter(Orders.engineer_id.in_(filter_order['engineer_id']))
        if filter_order.get('manager_id') is not None:
            query = query.filter(Orders.manager_id.in_(filter_order['manager_id']))
        if filter_order.get('kindof_good_id') is not None:
            query = query.filter(Orders.kindof_good_id == filter_order['kindof_good_id'])
        if filter_order.get('brand_id') is not None:
            query = query.filter(Orders.brand_id == filter_order['brand_id'])
        if filter_order.get('subtype_id') is not None:
            query = query.filter(Orders.subtype_id == filter_order['subtype_id'])
        if filter_order.get('client_id') is not None:
            query = query.filter(Orders.client_id == filter_order['client_id'])
        if filter_order.get('overdue') is not None:
            query = query.filter(Orders.estimated_done_at < time_now())
        if filter_order.get('status_overdue') is not None:
            query = query.filter(Orders.status_deadline < time_now())
        if filter_order.get('urgent') is not None:
            query = query.filter(Orders.urgent.is_(filter_order['urgent']))

        if filter_order.get('field_sort') == 'status.name':
            query = query.outerjoin(Status, Status.id == Orders.status_id)
            query = query.order_by(Status.group if filter_order.get('sort') == 'asc' else desc(Status.group))
            query = query.order_by(Status.id if filter_order.get('sort') == 'asc' else desc(Status.id))
        elif filter_order.get('field_sort') == 'kindof_good':
            query = query.outerjoin(EquipmentType, EquipmentType.id == Orders.kindof_good_id)
            query = query.order_by(EquipmentType.title if filter_order.get('sort') == 'asc' else desc(EquipmentType.title))
        elif filter_order.get('field_sort') == 'brand':
            query = query.outerjoin(EquipmentBrand, EquipmentBrand.id == Orders.brand_id)
            query = query.order_by(EquipmentBrand.title if filter_order.get('sort') == 'asc' else desc(EquipmentBrand.title))
        elif filter_order.get('field_sort') == 'subtype':
            query = query.outerjoin(EquipmentSubtype, EquipmentSubtype.id == Orders.subtype_id)
            query = query.order_by(EquipmentSubtype.title if filter_order.get('sort') == 'asc' else desc(EquipmentSubtype.title))
        elif filter_order.get('field_sort') == 'engineer_id':
            query = query.outerjoin(Employees, Employees.id == Orders.engineer_id)
            query = query.order_by(Employees.last_name if filter_order.get('sort') == 'asc' else desc(Employees.last_name))
            query = query.order_by(Employees.first_name if filter_order.get('sort') == 'asc' else desc(Employees.first_name))
        elif filter_order.get('field_sort') == 'manager_id':
            query = query.outerjoin(Employees, Employees.id == Orders.manager_id)
            query = query.order_by(Employees.last_name if filter_order.get('sort') == 'asc' else desc(Employees.last_name))
            query = query.order_by(Employees.first_name if filter_order.get('sort') == 'asc' else desc(Employees.first_name))
        elif filter_order.get('field_sort') == 'client.name':
            query = query.outerjoin(Clients, Clients.id == Orders.client_id)
            query = query.order_by(Clients.name if filter_order.get('sort') == 'asc' else desc(Clients.name))
            query = query.order_by(Clients.id if filter_order.get('sort') == 'asc' else desc(Clients.id))
        elif filter_order.get('field_sort') == 'ad_campaign_id':
            query = query.outerjoin(AdCampaign, AdCampaign.id == Orders.ad_campaign_id)
            query = query.order_by(AdCampaign.name if filter_order.get('sort') == 'asc' else desc(AdCampaign.name))
        else:
            query = query.order_by(
                getattr(Orders, filter_order.get('field_sort'), 'id') if filter_order.get('sort') == 'asc' else desc(
                    getattr(Orders, filter_order.get('field_sort'), 'id'))
            )

        query = query.limit(50)
        if filter_order.get('page', 0): query = query.offset(filter_order['page'] * 50)

        orders = query.all()

        branch_id = 1   # todo: прописать маршрут
        query = self.pgsql_connetction.session.query(Schedule)
        query = query.filter(Schedule.branch_id == branch_id)
        data_schedule = query.all()
        schedule = {}
        for day in data_schedule:
            schedule[day.week_day] = {
                'work_day': day.work_day,
                'start_time': day.start_time,
                'end_time': day.end_time
            }

        data = []
        for row in orders:
            data.append({
                'id': row.id,
                'created_at': row.created_at,
                'done_at': row.done_at,
                'closed_at': row.closed_at,
                'assigned_at': row.assigned_at,
                'duration': row.duration,
                'estimated_done_at': row.estimated_done_at,
                'scheduled_for': row.scheduled_for,
                'warranty_date': row.warranty_date,
                'status_deadline': row.status_deadline,

                'id_label': row.id_label,
                'prefix': row.prefix,
                'serial': row.serial,
                'malfunction': row.malfunction,
                'packagelist': row.packagelist,
                'appearance': row.appearance,
                'engineer_notes': row.engineer_notes,
                'manager_notes': row.manager_notes,
                'resume': row.resume,
                'cell': row.cell,

                'estimated_cost': row.estimated_cost,
                'missed_payments': row.missed_payments,
                'discount_sum': row.discount_sum,
                'payed': row.payed,
                'price': row.price,
                'remaining': get_estimate_work_time(row.estimated_done_at, schedule),
                'remaining_status': row.status_deadline - time_now() if row.status_deadline else None,
                'remaining_warranty': row.warranty_date - time_now() if row.warranty_date else None,

                'overdue': row.estimated_done_at > time_now() if row.estimated_done_at else False,
                'status_overdue': row.status_deadline > time_now() if row.status_deadline else False,
                'urgent': row.urgent,
                'warranty_measures': row.warranty_date < time_now() if row.warranty_date else False,
                'ad_campaign': {
                    'id': row.ad_campaign.id,
                    'name': row.ad_campaign.name
                } if row.ad_campaign else {},
                'branch': {
                    'id': row.branch.id,
                    'name': row.branch.name
                } if row.branch else {},
                'status': {
                    'id': row.status.id,
                    'name': row.status.name,
                    'color': row.status.color,
                    'group': row.status.group
                } if row.status else {},
                'client': {
                    'id': row.client.id,

                    'conflicted': row.client.conflicted,
                    'name': row.client.name,
                    'phone': [{
                        'id': ph.id,
                        'number': ph.number,
                        'title': ph.title,
                        'notify': ph.notify
                    } for ph in row.client.phone] if row.client.phone else []
                } if row.client else {},
                'kindof_good': {
                    'id': row.kindof_good.id,
                    'title': row.kindof_good.title,
                    'icon': row.kindof_good.icon,
                } if row.kindof_good else {},
                'brand': {
                    'id': row.brand.id,
                    'title': row.brand.title,
                } if row.brand else {},
                'subtype': {
                    'id': row.subtype.id,
                    'title': row.subtype.title,
                } if row.subtype else {},
                'model': {
                    'id': row.model.id,
                    'title': row.model.title,
                } if row.model else {},

                'engineer_id': row.engineer_id,
                'manager_id': row.manager_id,
                'created_by_id': row.created_by_id
            })
        return data
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def get_order(self, id):
    try:
        result = {'success': True}

        result['data'], result['events'] = self.get_order_by_id(id)

        return result, 200
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def add_orders(
    self,
    created_at,
    done_at,
    closed_at,
    assigned_at,
    duration,
    estimated_done_at,
    scheduled_for,
    warranty_date,
    status_deadline,

    ad_campaign_id,
    branch_id,
    status_id,
    client_id,
    order_type_id,
    kindof_good_id,
    brand_id,
    subtype_id,
    model_id,
    closed_by_id,
    created_by_id,
    engineer_id,
    manager_id,

    id_label,
    prefix,
    serial,
    malfunction,
    packagelist,
    appearance,
    manager_notes,
    engineer_notes,
    resume,
    cell,

    estimated_cost,

    urgent,

    user_id,
    r_filter
    ):
    try:
        # Создание заказа ==============================================================================================
        order = Orders(
            created_at=created_at,
            done_at=done_at,
            closed_at=closed_at,
            assigned_at=assigned_at,
            duration=duration,
            estimated_done_at=estimated_done_at,
            scheduled_for=scheduled_for,
            warranty_date=warranty_date,
            status_deadline=status_deadline,

            ad_campaign_id=ad_campaign_id,
            branch_id=branch_id,
            status_id=status_id,
            client_id=client_id,
            order_type_id=order_type_id,
            kindof_good_id=kindof_good_id,
            brand_id=brand_id,
            subtype_id=subtype_id,
            model_id=model_id,
            closed_by_id=closed_by_id,
            created_by_id=created_by_id,
            engineer_id=engineer_id,
            manager_id=manager_id,

            id_label=id_label,
            prefix=prefix,
            serial=serial,
            malfunction=malfunction,
            packagelist=packagelist,
            appearance=appearance,
            manager_notes=manager_notes,
            engineer_notes=engineer_notes,
            resume=resume,
            cell=cell,

            estimated_cost=estimated_cost,

            urgent=urgent
        )
        self.pgsql_connetction.session.add(order)
        self.pgsql_connetction.session.flush()
        self.pgsql_connetction.session.refresh(order)

        # Формираование данных текащего заказа для ответа ==============================================================
        result = {'success': True}
        dict_order = {
            'id': order.id,
            'created_at': order.created_at,
            'estimated_done_at': order.estimated_done_at,
            'scheduled_for': order.scheduled_for,
            'warranty_date': order.warranty_date,
            'status_deadline': order.status_deadline,

            'id_label': order.id_label,
            'serial': order.serial,
            'malfunction': order.malfunction,
            'packagelist': order.packagelist,
            'appearance': order.appearance,
            'manager_notes': order.manager_notes,

            'estimated_cost': order.estimated_cost,

            'urgent': order.urgent,
            'ad_campaign': {
                'id': order.ad_campaign.id,
                'name': order.ad_campaign.name
            } if order.ad_campaign else {},
            'branch': {
                'id': order.branch.id,
                'name': order.branch.name
            } if order.branch else {},
            'status': {
                'id': order.status.id,
                'name': order.status.name,
                'color': order.status.color,
                'group': order.status.group
            } if order.status else {},
            'client': {
                'id': order.client.id,
                'conflicted': order.client.conflicted,
                'email': order.client.email,
                'name': order.client.name,
                'name_doc': order.client.name_doc,
                'discount_good_type': order.client.discount_good_type,
                'discount_materials_type': order.client.discount_materials_type,
                'discount_service_type': order.client.discount_service_type,
                'notes': order.client.notes,
                'phone': [{
                    'id': ph.id,
                    'number': ph.number,
                    'notify': ph.notify,
                    'title': ph.title
                } for ph in order.client.phone] if order.client.phone else []
            } if order.client else {},
            'order_type': {
                'id': order.order_type.id,
                'name': order.order_type.name
            } if order.order_type else {},
            'kindof_good': {
                'id': order.kindof_good.id,
                'title': order.kindof_good.title,
                'icon': order.kindof_good.icon
            } if order.kindof_good else {},
            'brand': {
                'id': order.brand.id,
                'title': order.brand.title
            } if order.brand else {},
            'subtype': {
                'id': order.subtype.id,
                'title': order.subtype.title
            } if order.subtype else {},
            'model': {
                'id': order.model.id,
                'title': order.model.title
            } if order.model else {},
            'engineer_id': order.engineer_id,
            'manager_id': order.manager_id
        }
        # Создание событий =============================================================================================
        order_events = []
        order_event = Events(
            object_type=1,          # Заказ
            object_id=order.id,
            event_type='CREATE_ORDER',
            current_status_id=order.status_id,
            branch_id=branch_id,
            employee_id=user_id,
            changed=[{
                'title': 'Создан заказ',
                'new': {
                    'id': order.id,
                    'title': order.status.name,
                    'data': dict_order
                }
            }]
        )
        order_events.append(order_event)
        if order.engineer_id:
            order_event = Events(
                object_type=1,  # Заказ
                object_id=order.id,
                event_type='ASSIGN_ENGINEER',
                current_status_id=order.status_id,
                branch_id=branch_id,
                employee_id=user_id,
                changed=[{
                    'title': 'Назанчен инженер',
                    'new': {
                        'id': order.engineer.id,
                        'title': f'{order.engineer.last_name} {order.engineer.first_name}'
                    }
                }]
            )
            order_events.append(order_event)
        if order.manager_id:
            order_event = Events(
                object_type=1,  # Заказ
                object_id=order.id,
                event_type='ASSIGN_MANAGER',
                current_status_id=order.status_id,
                branch_id=branch_id,
                employee_id=user_id,
                changed=[{
                    'title': 'Назанчен менеджер',
                    'new': {
                        'id': order.manager.id,
                        'title': f'{order.manager.last_name} {order.manager.first_name}'
                    }
                }]
            )
            order_events.append(order_event)
        if order.client_id:
            order_event = Events(
                object_type=1,  # Заказ
                object_id=order.id,
                event_type='ADD_CLIENT',
                current_status_id=order.status_id,
                branch_id=branch_id,
                employee_id=user_id,
                changed=[{
                    'title': 'Добавлен клиент',
                    'new': {
                        'id': order.client.id,
                        'title': order.client.name
                    }
                }]
            )
            order_events.append(order_event)

        self.pgsql_connetction.session.add_all(order_events)
        self.pgsql_connetction.session.flush()

        # Формирование заказов в соответсвии с фильтром запроса для ответа =============================================
        result['order'] = dict_order
        query = self.pgsql_connetction.session.query(Events)
        query = query.filter(Events.object_type == 1)
        query = query.filter(Events.object_id == order.id)
        query = query.order_by(Events.id)
        events = query.all()

        data_events = []
        for event in events:
            data_events.append({
                'created_at': event.created_at,
                'event_type': event.event_type,
                'current_status': {
                    'id': event.current_status.id,
                    'color': event.current_status.color
                },
                'employee_id': event.employee_id,
                'changed': event.changed
            })

        result['events'] = data_events

        if r_filter:
            result['data'] = self.get_orders_by_filter(r_filter)
            result['count'] = len(result['data'])
            result['page'] = r_filter.get('page', 0)

        if r_filter.get('update_badges'):
            result['badges'] = self.get_badges()['data']

        # Отправляем SMS при событиях создания заказа
        event_create_order(self.pgsql_connetction.session, order, user_id)

        self.pgsql_connetction.session.commit()
        return result, 201
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def get_orders(
    self,
    id=None,
    created_at=None,
    status_id=None,
    order_type_id=None,
    engineer_id=None,
    manager_id=None,
    kindof_good_id=None,
    brand_id=None,
    subtype_id=None,
    client_id=None,

    overdue=None,
    status_overdue=None,
    urgent=None,

    search=None,

    sort=None,
    field_sort='desc',
    page=0
    ):
    try:
        query = self.pgsql_connetction.session.query(Orders)

        if id is not None: query = query.filter(Orders.id == id)
        if created_at is not None:
            query = query.filter(created_at[0] <= Orders.created_at)
            query = query.filter(Orders.created_at <= created_at[1])
        if status_id is not None: query = query.filter(Orders.status_id.in_(status_id))
        if order_type_id is not None: query = query.filter(Orders.order_type_id.in_(order_type_id))
        if engineer_id is not None: query = query.filter(Orders.engineer_id.in_(engineer_id))
        if manager_id is not None: query = query.filter(Orders.manager_id.in_(manager_id))
        if kindof_good_id is not None: query = query.filter(Orders.kindof_good_id == kindof_good_id)
        if brand_id is not None: query = query.filter(Orders.brand_id == brand_id)
        if subtype_id is not None: query = query.filter(Orders.subtype_id == subtype_id)
        if client_id is not None: query = query.filter(Orders.client_id == client_id)
        if overdue is not None: query = query.filter(Orders.estimated_done_at < time_now())
        if status_overdue is not None: query = query.filter(Orders.status_deadline < time_now())
        if urgent is not None: query = query.filter(Orders.urgent.is_(urgent))

        if search:
            query = query.outerjoin(Clients, Clients.id == Orders.client_id)
            query = query.outerjoin(Phones, Phones.client_id == Clients.id)
            query = query.outerjoin(EquipmentType, EquipmentType.id == Orders.kindof_good_id)
            query = query.outerjoin(EquipmentBrand, EquipmentBrand.id == Orders.brand_id)
            query = query.outerjoin(EquipmentSubtype, EquipmentSubtype.id == Orders.subtype_id)
            query = query.outerjoin(EquipmentModel, EquipmentModel.id == Orders.model_id)
            query = query.filter(or_(
                        Orders.id_label.ilike(f'%{search}%'),
                        Orders.serial.ilike(f'%{search}%'),
                        Clients.name.ilike(f'%{search}%'),
                        Phones.number.ilike(f'%{search}%'),
                        EquipmentType.title.ilike(f'%{search}%'),
                        EquipmentBrand.title.ilike(f'%{search}%'),
                        EquipmentSubtype.title.ilike(f'%{search}%'),
                        EquipmentModel.title.ilike(f'%{search}%')
                    ))

        if field_sort == 'status.name':
            query = query.outerjoin(Status, Status.id == Orders.status_id)
            query = query.order_by(Status.group if sort == 'asc' else desc(Status.group))
            query = query.order_by(Status.id if sort == 'asc' else desc(Status.id))
        elif field_sort == 'kindof_good':
            query = query.outerjoin(EquipmentType, EquipmentType.id == Orders.kindof_good_id)
            query = query.order_by(EquipmentType.title if sort == 'asc' else desc(EquipmentType.title))
        elif field_sort == 'brand':
            query = query.outerjoin(EquipmentBrand, EquipmentBrand.id == Orders.brand_id)
            query = query.order_by(EquipmentBrand.title if sort == 'asc' else desc(EquipmentBrand.title))
        elif field_sort == 'subtype':
            query = query.outerjoin(EquipmentSubtype, EquipmentSubtype.id == Orders.subtype_id)
            query = query.order_by(EquipmentSubtype.title if sort == 'asc' else desc(EquipmentSubtype.title))
        elif field_sort == 'engineer_id':
            query = query.outerjoin(Employees, Employees.id == Orders.engineer_id)
            query = query.order_by(Employees.last_name if sort == 'asc' else desc(Employees.last_name))
            query = query.order_by(Employees.first_name if sort == 'asc' else desc(Employees.first_name))
        elif field_sort == 'manager_id':
            query = query.outerjoin(Employees, Employees.id == Orders.manager_id)
            query = query.order_by(Employees.last_name if sort == 'asc' else desc(Employees.last_name))
            query = query.order_by(Employees.first_name if sort == 'asc' else desc(Employees.first_name))
        elif field_sort == 'client.name':
            query = query.outerjoin(Clients, Clients.id == Orders.client_id)
            query = query.order_by(Clients.name if sort == 'asc' else desc(Clients.name))
            query = query.order_by(Clients.id if sort == 'asc' else desc(Clients.id))
        elif field_sort == 'ad_campaign_id':
            query = query.outerjoin(AdCampaign, AdCampaign.id == Orders.ad_campaign_id)
            query = query.order_by(AdCampaign.name if sort == 'asc' else desc(AdCampaign.name))
        else:
            query = query.order_by(getattr(Orders, field_sort, 'id') if sort == 'asc' else desc(getattr(Orders, field_sort, 'id')))

        result = {'success': True}
        result['count'] = query.count()

        query = query.limit(50)
        if page: query = query.offset(page*50)

        orders = query.all()

        branch_id = 1 # todo: прописать маршрут
        query = self.pgsql_connetction.session.query(Schedule)
        query = query.filter(Schedule.branch_id == branch_id)
        data_schedule = query.all()
        schedule = {}
        for day in data_schedule:
            schedule[day.week_day] = {
                'work_day': day.work_day,
                'start_time': day.start_time,
                'end_time': day.end_time
            }

        data = []
        for row in orders:


            data.append({
                'id': row.id,
                'created_at': row.created_at,
                'done_at': row.done_at,
                'closed_at': row.closed_at,
                'assigned_at': row.assigned_at,
                'duration': row.duration,
                'estimated_done_at': row.estimated_done_at,
                'scheduled_for': row.scheduled_for,
                'warranty_date': row.warranty_date,
                'status_deadline': row.status_deadline,

                'id_label': row.id_label,
                'prefix': row.prefix,
                'serial': row.serial,
                'malfunction': row.malfunction,
                'packagelist': row.packagelist,
                'appearance': row.appearance,
                'engineer_notes': row.engineer_notes,
                'manager_notes': row.manager_notes,
                'resume': row.resume,
                'cell': row.cell,

                'estimated_cost': row.estimated_cost,
                'missed_payments': row.missed_payments,
                'discount_sum': row.discount_sum,
                'payed': row.payed,
                'price': row.price,
                # 'remaining': row.estimated_done_at - time_now() if row.estimated_done_at else None,
                'remaining': get_estimate_work_time(row.estimated_done_at, schedule),
                'remaining_status': row.status_deadline - time_now() if row.status_deadline else None,
                'remaining_warranty': row.warranty_date - time_now() if row.warranty_date else None,

                'overdue': row.estimated_done_at > time_now() if row.estimated_done_at else False,
                'status_overdue': row.status_deadline > time_now() if row.status_deadline else False,
                'urgent': row.urgent,
                'warranty_measures': row.warranty_date < time_now() if row.warranty_date else False,
                'ad_campaign': {
                    'id': row.ad_campaign.id,
                    'name': row.ad_campaign.name
                } if row.ad_campaign else {},
                'branch': {
                    'id': row.branch.id,
                    'name': row.branch.name
                } if row.branch else {},
                'status': {
                    'id': row.status.id,
                    'name': row.status.name,
                    'color': row.status.color,
                    'group': row.status.group
                } if row.status else {},
                'client': {
                    'id': row.client.id,
                    'conflicted': row.client.conflicted,
                    'name': row.client.name,
                    'phone': [{
                        'id': ph.id,
                        'number': ph.number,
                        'title': ph.title,
                        'notify': ph.notify
                    } for ph in row.client.phone] if row.client.phone else []
                } if row.client else {},
                'kindof_good': {
                    'id': row.kindof_good.id,
                    'title': row.kindof_good.title,
                    'icon': row.kindof_good.icon,
                } if row.kindof_good else {},
                'brand': {
                    'id': row.brand.id,
                    'title': row.brand.title,
                } if row.brand else {},
                'subtype': {
                    'id': row.subtype.id,
                    'title': row.subtype.title,
                } if row.subtype else {},
                'model': {
                    'id': row.model.id,
                    'title': row.model.title,
                } if row.model else {},

                'engineer_id': row.engineer_id,
                'manager_id': row.manager_id,
                'created_by_id': row.created_by_id
            })

        result['data'] = data
        result['page'] = page
        return result, 200
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def edit_orders(
        self,
        id,
        created_at=None,
        done_at=None,
        closed_at=None,
        assigned_at=None,
        duration=None,
        estimated_done_at=None,
        scheduled_for=None,
        warranty_date=None,
        status_deadline=None,
        ad_campaign_id=None,
        branch_id=None,
        status_id=None,
        client_id=None,
        order_type_id=None,
        closed_by_id=None,
        created_by_id=None,
        engineer_id=None,
        manager_id=None,
        id_label=None,
        prefix=None,
        kindof_good_id=None,
        brand_id=None,
        model_id=None,
        subtype_id=None,
        serial=None,
        malfunction=None,
        packagelist=None,
        appearance=None,
        engineer_notes=None,
        manager_notes=None,
        resume=None,
        cell=None,
        estimated_cost=None,
        price=None,
        urgent=None,
        user_id=None,
        r_filter=None
        ):
    try:
        order = self.pgsql_connetction.session.query(Orders).get(id)
        # Добавим события ==============================================================================================
        order_events = []
        if engineer_id is not None and order.engineer_id != engineer_id:
            order_event = Events(
                object_type=1,  # Заказ
                object_id=order.id,
                event_type='CHANGE_ENGINEER',
                current_status_id=order.status_id,
                branch_id=branch_id,
                employee_id=user_id,
                changed=[{
                    'title': 'Инженер изменен' if order.engineer_id else 'Назанчен инженер',
                    'current': {
                        'id': order.engineer.id,
                        'title': f'{order.engineer.last_name} {order.engineer.first_name}'
                    } if order.engineer_id else {},
                    'new': {
                        'id': engineer_id,
                        'title': self.pgsql_connetction.session.query(
                            func.concat(Employees.last_name, ' ', Employees.first_name)).filter_by(id=engineer_id).scalar()
                    }
                }]
            )
            order_events.append(order_event)
        if manager_id is not None and order.manager_id != manager_id:
            order_event = Events(
                object_type=1,  # Заказ
                object_id=order.id,
                event_type='CHANGE_MANAGER',
                current_status_id=order.status_id,
                branch_id=branch_id,
                employee_id=user_id,
                changed=[{
                    'title': 'Менеджер изменен' if order.manager_id else 'Назначен менеджер',
                    'current': {
                        'id': order.manager.id,
                        'title': f'{order.manager.last_name} {order.manager.first_name}'
                    } if order.manager_id else {},
                    'new': {
                        'id': manager_id,
                        'title': self.pgsql_connetction.session.query(
                            func.concat(Employees.last_name, ' ', Employees.first_name)).filter_by(id=manager_id).scalar()
                    }
                }]
            )
            order_events.append(order_event)
        if client_id is not None and order.client_id != client_id:
            order_event = Events(
                object_type=1,  # Заказ
                object_id=order.id,
                event_type='CHANGE_CLIENT',
                current_status_id=order.status_id,
                branch_id=branch_id,
                employee_id=user_id,
                changed=[{
                    'title': 'Клиент изменен' if order.client_id else 'Добавлен клиент',
                    'current': {
                        'id': order.client.id,
                        'title': order.client.name
                    } if order.client_id else {},
                    'new': {
                        'id': client_id,
                        'title': self.pgsql_connetction.session.query(Clients.name).filter_by(id=client_id).scalar()
                    }
                }]
            )
            order_events.append(order_event)
        if estimated_done_at is not None and order.estimated_done_at != estimated_done_at:
            order_event = Events(
                object_type=1,  # Заказ
                object_id=order.id,
                event_type='CHANGE_ESTIMATED_DONE_AT',
                current_status_id=order.status_id,
                branch_id=branch_id,
                employee_id=user_id,
                changed=[{
                    'title': 'Изменен срок выполнения заказ',
                    'current': {'title': datetime.fromtimestamp(order.estimated_done_at).strftime("%d.%m.%Y %H:%M")},
                    'new': {'title': datetime.fromtimestamp(estimated_done_at).strftime("%d.%m.%Y %H:%M")}
                }]
            )
            order_events.append(order_event)
        if branch_id is not None and order.branch_id != branch_id:
            order_event = Events(
                object_type=1,  # Заказ
                object_id=order.id,
                event_type='MOVE_TO',
                current_status_id=order.status_id,
                branch_id=branch_id,
                employee_id=user_id,
                changed=[{
                    'title': 'Заказ перемещен',
                    'current': {
                        'id': order.branch.id,
                        'title': order.branch.name
                    },
                    'new': {
                        'id': branch_id,
                        'title': self.pgsql_connetction.session.query(Branch.name).filter_by(id=branch_id).scalar()
                    }
                }]
            )
            order_events.append(order_event)

        changed_list = []
        if assigned_at is not None and order.assigned_at != assigned_at:
            changed_list.append({
                'title': 'Заказ перенесен' if order.assigned_at else 'Заказ назначен на',
                'current': {'title': order.assigned_at},
                'new': {'title': assigned_at}
            })
        if duration is not None and order.duration != duration:
            changed_list.append({
                'title': 'Длительность изменена' if order.duration else 'Установлена длительность',
                'current': {'title': order.duration},
                'new': {'title': duration}
            })
        if warranty_date is not None and order.warranty_date != warranty_date:
            changed_list.append({
                'title': 'Дата гарантии изменена' if order.warranty_date else 'Установлена дата гарантии',
                'current': {'title': order.warranty_date},
                'new': {'title': warranty_date}
            })
        if ad_campaign_id is not None and order.ad_campaign_id != ad_campaign_id:
            changed_list.append({
                'title': 'Рекламная компания изменена' if order.ad_campaign_id else 'Установлена рекламная компания',
                'current': {
                    'id': order.ad_campaign_id,
                    'title': order.ad_campaign.name
                } if order.ad_campaign_id else {},
                'new': {
                    'id': ad_campaign_id,
                    'title': self.pgsql_connetction.session.query(AdCampaign.name).filter_by(id=ad_campaign_id).scalar()
                }
            })
        if order_type_id is not None and order.order_type_id != order_type_id:
            changed_list.append({
                'title': 'Тип заказа изменен' if order.order_type_id else 'Установлен тип заказа',
                 'current': {
                    'id': order.order_type.id,
                    'title': order.order_type.name
                } if order.order_type_id else {},
                'new': {
                    'id': order_type_id,
                    'title': self.pgsql_connetction.session.query(OrderType.name).filter_by(id=order_type_id).scalar()
                }
            })
        if kindof_good_id is not None and order.kindof_good_id != kindof_good_id:
            changed_list.append({
                'title': 'Тип устройства изменен' if order.kindof_good_id else 'Установлен тип устройства',
                'current': {
                    'id': order.kindof_good.id,
                    'title': order.kindof_good.title
                } if order.kindof_good_id else {},
                'new': {
                    'id': kindof_good_id,
                    'title': self.pgsql_connetction.session.query(EquipmentType.title).filter_by(id=kindof_good_id).scalar()
                }
            })
        if brand_id is not None and order.brand_id != brand_id:
            changed_list.append({
                'title': 'Бренд изменен' if order.brand_id else 'Установлен бренд',
                'current': {
                    'id': order.brand.id,
                    'title': order.brand.title
                } if order.brand_id else {},
                'new': {
                    'id': brand_id,
                    'title': self.pgsql_connetction.session.query(EquipmentBrand.title).filter_by(id=brand_id).scalar()
                }
            })
        if subtype_id is not None and order.subtype_id != subtype_id:
            changed_list.append({
                'title': 'Модуль/серия изменен(а)' if order.subtype_id else 'Установлен(а) модуль/серия',
                'current': {
                    'id': order.subtype.id,
                    'title': order.subtype.title
                } if order.subtype_id else {},
                'new': {
                    'id': kindof_good_id,
                    'title': self.pgsql_connetction.session.query(EquipmentSubtype.title).filter_by(id=subtype_id).scalar()
                }
            })
        if model_id is not None and order.model_id != model_id:
            changed_list.append({
                'title': 'Модель изменена' if order.model_id else 'Установлена модель',
                'current': {
                    'id': order.model.id,
                    'title': order.model.title
                } if order.model_id else {},
                'new': {
                    'id': model_id,
                    'title': self.pgsql_connetction.session.query(EquipmentModel.title).filter_by(id=model_id).scalar()
                }
            })
        if serial is not None and order.serial != serial:
            changed_list.append({
                'title': 'Серийный номер изменен' if order.serial else 'Добавлен серийный номер',
                'current': {'title': order.serial},
                'new': {'title': serial}
            })
        if malfunction is not None and order.malfunction != malfunction:
            changed_list.append({
                'title': 'Неисправность изменена' if order.malfunction else 'Добавлена неисправность',
                'current': {'title': order.malfunction},
                'new': {'title': malfunction}
            })
        if packagelist is not None and order.packagelist != packagelist:
            changed_list.append({
                'title': 'Комплектация изменена' if order.packagelist else 'Добавлена комплектация',
                'current': {'title': order.packagelist},
                'new': {'title': packagelist}
            })
        if appearance is not None and order.appearance != appearance:
            changed_list.append({
                'title': 'Внешний вид изменен' if order.appearance else 'Внешинй вид добавлен',
                'current': {'title': order.appearance},
                'new': {'title': appearance}
            })
        if engineer_notes is not None and order.engineer_notes != engineer_notes:
            changed_list.append({
                'title': 'Заметки инженера изменены' if order.engineer_notes else 'Добавлены заметки инженера',
                'current': {'title': order.engineer_notes},
                'new': {'title': engineer_notes}
            })
        if manager_notes is not None and order.manager_notes != manager_notes:
            changed_list.append({
                'title': 'Заметки менеджера изменены' if order.manager_notes else 'Добавлены заметки менеджера',
                'current': {'title': order.manager_notes},
                'new': {'title': manager_notes}
            })
        if resume is not None and order.resume != resume:
            changed_list.append({
                'title': 'Вердикт изменен' if order.resume else 'Добален вердикт',
                'current': {'title': order.resume},
                'new': {'title': resume}
            })
        if cell is not None and order.cell != cell:
            changed_list.append({
                'title': 'Ячейка изменена' if order.cell else 'Установлена ячейка',
                'current': {'title': order.cell},
                'new': {'title': cell}
            })
        if estimated_cost is not None and order.estimated_cost != estimated_cost:
            changed_list.append({
                'title': 'Ориентировочная стоимость изменена' if order.estimated_cost else 'Установлена ориентировочная стоимость',
                'current': {'title': order.estimated_cost},
                'new': {'title': estimated_cost}
            })
        if urgent is not None and order.urgent != urgent:
            changed_list.append({
                'title': 'Срочность изменена',
                'current': {'title': 'срочно' if order.urgent else 'не срочно'},
                'new': {'title': 'срочно' if urgent else 'не срочно'}
            })

        if changed_list:
            order_event = Events(
                object_type=1,  # Заказ
                object_id=order.id,
                event_type='CHANGE_DATA',
                current_status_id=order.status_id,
                branch_id=branch_id,
                employee_id=user_id,
                changed=changed_list
            )
            order_events.append(order_event)

        # Изменение данных заказа ======================================================================================
        fields = inspect.getfullargspec(edit_orders).args[:-2]  # список имен всех аргументов текущей фнкции
        for field in fields:
            war = locals()[field]  # Находим переменную от имени и присваеваем war
            if war is not None:
                setattr(order, field, war)

        result = {'success': True}

        self.pgsql_connetction.session.add_all([order] + order_events)
        self.pgsql_connetction.session.flush()
        self.pgsql_connetction.session.refresh(order)

        # Формирования данных заказа для ответа ========================================================================
        result['order'], result['events'] = self.get_order_by_id(id)


        # Формироваиня списка заказов в соответсвии с фильтром запроса =================================================
        if r_filter:
            result['data'] = self.get_orders_by_filter(r_filter)
            result['count'] = len(result['data'])
            result['page'] = r_filter.get('page', 0)

        if r_filter.get('update_badges'):
            result['badges'] = self.get_badges()['data']

        self.pgsql_connetction.session.commit()
        return result, 202
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def del_orders(self, id):
    orders = self.pgsql_connetction.session.query(Orders).get(id)
    if orders:
        self.pgsql_connetction.session.delete(orders)
        self.pgsql_connetction.session.commit()
        return self.get_orders()
