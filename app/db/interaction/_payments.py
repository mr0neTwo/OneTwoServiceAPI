import inspect
import traceback

from sqlalchemy import desc, func

from app.db.models.models import Payments, Cashboxs, time_now, Orders, Events


def add_payments(
        self,
        cashflow_category,
        description,
        deposit,
        income,
        outcome,
        direction,
        can_print_fiscal,
        deleted,
        is_fiscal,
        created_at,
        custom_created_at,
        tags,
        relation_id,
        cashbox_id,
        client_id,
        employee_id,
        order_id,
        user_id,
        target_cashbox_id=None,
        filter_payments=None,
        filter_cashboxes=None,
        filter_order=None,
        closed_order=None
    ):
    try:
        payment = Payments(
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
            relation_id=relation_id,
            cashbox_id=cashbox_id,
            client_id=client_id,
            employee_id=employee_id,
            order_id=order_id
        )
        self.pgsql_connetction.session.add(payment)
        self.pgsql_connetction.session.flush()
        self.pgsql_connetction.session.refresh(payment)

        # Если есть целевая касса, то есть делаем пермещение
        if target_cashbox_id is not None:
            payment2 = Payments(
                cashflow_category=cashflow_category,
                description=description,
                deposit=None,
                income=abs(outcome),
                outcome=income,
                direction=direction,
                can_print_fiscal=can_print_fiscal,
                deleted=deleted,
                is_fiscal=is_fiscal,
                created_at=created_at,
                custom_created_at=custom_created_at,
                tags=tags,
                relation_id=payment.id,
                cashbox_id=target_cashbox_id,
                client_id=client_id,
                employee_id=employee_id,
                order_id=order_id
            )

            self.pgsql_connetction.session.add(payment2)
            self.pgsql_connetction.session.flush()
            self.pgsql_connetction.session.refresh(payment2)

            payment.relation_id = payment2.id
            self.pgsql_connetction.session.add(payment)
            self.pgsql_connetction.session.flush()

        # Добавим событие добавление операции

        payment_event = Events(
            object_type=6,  # Работа в заказе
            object_id=payment.id,
            event_type='ADD_PAYMENT',
            current_status_id=None,
            branch_id=None,
            employee_id=user_id,
            changed=[{
                'title': 'Добавлен платеж' if payment.direction == 2 else 'Сделана выплата',
                'new': {
                    'id': payment.id,
                    'title': f'{payment.description}  {payment.income or payment.outcome} руб.'
                }
            }]
        )
        self.pgsql_connetction.session.add(payment_event)
        self.pgsql_connetction.session.flush()

        if order_id:
            order = self.pgsql_connetction.session.query(Orders).get(order_id)

            discount_sum = 0
            price = 0
            payed = 0
            if order.operations:
                for operation in order.operations:
                    if not operation.deleted:
                        discount_sum += operation.discount_value
                        price += operation.total
            if order.parts:
                for parts in order.parts:
                    if not parts.deleted:
                        discount_sum += parts.discount_value
                        price += parts.total
            if order.payments:
                for payment in order.payments:
                    if not payment.deleted:
                        payed += payment.income
                        payed += payment.outcome

            order.discount_sum = discount_sum
            order.price = price
            order.payed = payed
            order.missed_payments = price - payed

            order_event = Events(
                object_type=1,  # Заказ
                object_id=order_id,
                event_type='ADD_PAYMENT',
                current_status_id=order.status_id,
                branch_id=order.branch_id,
                employee_id=user_id,
                changed=[{
                    'title': 'Добавлен платеж' if payment.direction == 2 else 'Сделан возврат',
                    'new': {
                        'id': payment.id,
                        'title': f'{payment.income or payment.outcome} руб.'
                    }
                }]
            )
            self.pgsql_connetction.session.add_all([order, order_event])
            self.pgsql_connetction.session.flush()

        result = {'success': True}

        if filter_payments:
            query = self.pgsql_connetction.session.query(Payments)
            if filter_payments.get('custom_created_at'):
                query = query.filter(filter_payments['custom_created_at'][0] <= Payments.custom_created_at)
                query = query.filter(Payments.custom_created_at <= filter_payments['custom_created_at'][1])
            if filter_payments.get('cashbox_id'):
                query = query.filter(Payments.cashbox_id == filter_payments['cashbox_id'])
            if filter_payments.get('tags'):
                query = query.filter(tags in Payments.tags)
            if filter_payments.get('deleted') is not None:
                query = query.filter(filter_payments['deleted'] or Payments.deleted.is_(False))

            query = query.order_by(desc(Payments.custom_created_at))

            result['payments_count'] = query.count()

            payments = query.all()

            data = []
            for row in payments:
                query = self.pgsql_connetction.session.query(func.sum(Payments.income + Payments.outcome))
                query = query.filter(Payments.cashbox_id == row.cashbox.id)
                query = query.filter(Payments.deleted != True)
                query = query.filter(Payments.custom_created_at <= row.custom_created_at)
                deposit = query.scalar()

                data.append({
                    'id': row.id,
                    'cashflow_category': row.cashflow_category,
                    'description': row.description,
                    'deposit': deposit,
                    'income': row.income,
                    'outcome': row.outcome,
                    'direction': row.direction,
                    'can_print_fiscal': row.can_print_fiscal,
                    'deleted': row.deleted,
                    'is_fiscal': row.is_fiscal,
                    'created_at': row.created_at,
                    'custom_created_at': row.custom_created_at,
                    'tags': row.tags,
                    'relation_id': row.relation_id,
                    'cashbox': {
                        'id': row.cashbox.id,
                        'title': row.cashbox.title,
                        'type': row.cashbox.type
                    } if row.cashbox else {},
                    'client': {
                        'id': row.client.id,
                        'name': row.client.name,
                        'phone': [ph.number for ph in row.client.phone] if row.client.phone else []
                    } if row.client else {},
                    'employee': {
                        'id': row.employee.id,
                        'name': f'{row.employee.last_name} {row.employee.first_name}'
                    } if row.employee else {},
                    'order': {
                        'id': row.order.id,
                        'id_label': row.order.id_label
                    } if row.order else {}
                })

            result['payments'] = data

        if filter_cashboxes:
            query = self.pgsql_connetction.session.query(Cashboxs)
            if filter_cashboxes.get('deleted'):
                query = query.filter(filter_cashboxes['deleted'] or Cashboxs.deleted.is_(False))

            cashboxes = query.all()

            data = []
            for row in cashboxes:
                query = self.pgsql_connetction.session.query(func.sum(Payments.income + Payments.outcome))
                query = query.filter(Payments.cashbox_id == row.id)
                query = query.filter(Payments.deleted.is_(False))
                balance = query.scalar()

                data.append({
                    'id': row.id,
                    'title': row.title,
                    'balance': balance,
                    'type': row.type,
                    'isGlobal': row.isGlobal,
                    'isVirtual': row.isVirtual,
                    'deleted': row.deleted,
                    'permissions': row.permissions,
                    'employees': row.employees,
                    'branch_id': row.branch_id
                })

            result['cashboxes'] = data

        if filter_order:
            if filter_order.get('update_order'):
                order = self.pgsql_connetction.session.query(Orders).get(filter_order['update_order'])
                result['order'] = {
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
                    'remaining': order.estimated_done_at - time_now() if order.estimated_done_at else None,
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
                    # 'engineer': {
                    #     'id': row.engineer.id,
                    #     'first_name': row.engineer.first_name,
                    #     'last_name': row.engineer.last_name,
                    #     'email': row.engineer.email,
                    #     'phone': row.engineer.phone,
                    # } if row.engineer else {},
                    # 'manager': {
                    #     'id': row.manager.id,
                    #     'first_name': row.manager.first_name,
                    #     'last_name': row.manager.last_name,
                    #     'email': row.manager.email,
                    #     'phone': row.manager.phone,
                    # } if row.manager else {},
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


            query = self.pgsql_connetction.session.query(Orders)

            if filter_order.get('created_at') is not None:
                query = query.filter(filter_order['created_at'][0] <= Orders.created_at)
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


            query = query.order_by(
                getattr(Orders, filter_order.get('field_sort'), 'id') if filter_order.get('sort') == 'asc' else desc(getattr(Orders, filter_order.get('field_sort'), 'id')))

            count = query.count()
            result['count'] = count

            query = query.limit(50)
            if filter_order.get('page', 0): query = query.offset(filter_order['page'] * 50)

            orders = query.all()

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
                    'remaining': row.estimated_done_at - time_now() if row.estimated_done_at else None,
                    'remaining_status': row.status_deadline - time_now() if row.status_deadline else None,
                    'remaining_warranty': row.warranty_date - time_now() if row.warranty_date else None,

                    'overdue': row.estimated_done_at > time_now() if row.estimated_done_at else False,
                    'status_overdue': row.status_deadline > time_now() if row.status_deadline else False,
                    'urgent': row.urgent,
                    'warranty_measures': row.warranty_date < time_now() if row.warranty_date else False,

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
                result['orders'] = data

        if closed_order:
            cos_result = self.change_order_status(
                status_id=closed_order['status_id'],
                order_id=closed_order['order_id'],
                user_id=user_id,
                r_filter=closed_order.get('filter')
            )
            if cos_result[0].get('order'):
                result['order'] = cos_result[0]['order']
                result['events'] = cos_result[0]['events']
            result['orders'] = cos_result[0]['data']
            result['orders_count'] = cos_result[0]['count']
            result['badges'] = cos_result[0]['badges']

        self.pgsql_connetction.session.commit()
        return result
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550

def get_payments(
        self,
        id=None,
        direction=None,
        deleted=None,
        custom_created_at=None,
        tags=None,
        cashbox_id=None,
        client_id=None,
        employee_id=None,
        order_id=None,
        relation_id=None
    ):
    try:
        query = self.pgsql_connetction.session.query(Payments)
        if id is not None: query = query.filter(Payments.id == id)
        if direction is not None: query = query.filter(Payments.direction == direction)
        if deleted is not None: query = query.filter(deleted or Payments.deleted.is_(False))
        if tags is not None: query = query.filter(tags in Payments.tags)
        if cashbox_id is not None: query = query.filter(Payments.cashbox_id == cashbox_id)
        if employee_id is not None: query = query.filter(Payments.employee_id == employee_id)
        if order_id is not None: query = query.filter(Payments.order_id == order_id)
        if relation_id is not None: query = query.filter(Payments.relation_id == relation_id)
        if custom_created_at is not None: 
            query = query.filter(Payments.custom_created_at >= custom_created_at[0])
            query = query.filter(Payments.custom_created_at <= custom_created_at[1])
    
        query = query.order_by(desc(Payments.custom_created_at))

        result = {'success': True}
    
        result['count'] = query.count()

        payments = query.all()

        data = []
        for row in payments:
            deposit = self.pgsql_connetction.session.query(func.sum(Payments.income + Payments.outcome)) \
                .filter(Payments.cashbox_id == row.cashbox.id) \
                .filter(Payments.deleted.is_(False)) \
                .filter(Payments.custom_created_at <= row.custom_created_at) \
                .scalar()
    
            data.append({
                'id': row.id,
                'cashflow_category': row.cashflow_category,
                'description': row.description,
                'deposit': deposit,
                'income': row.income,
                'outcome': row.outcome,
                'direction': row.direction,
                'can_print_fiscal': row.can_print_fiscal,
                'deleted': row.deleted,
                'is_fiscal': row.is_fiscal,
                'created_at': row.created_at,
                'custom_created_at': row.custom_created_at,
                'tags': row.tags,
                'relation_id': row.relation_id,
                'cashbox': {
                    'id': row.cashbox.id,
                    'title': row.cashbox.title,
                    'type': row.cashbox.type
                } if row.cashbox else {},
                'client': {
                    'id': row.client.id,
                    'name': row.client.name,
                    'phone': [ph.number for ph in row.client.phone] if row.client.phone else []
                } if row.client else {},
                'employee': {
                    'id': row.employee.id,
                    'name': f'{row.employee.last_name} {row.employee.first_name}'
                } if row.employee else {},
                'order': {
                    'id': row.order.id,
                    'id_label': row.order.id_label
                } if row.order else {}
            })
    
        result['data'] = data
        
        return result, 200
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def edit_payments(
        self,
        id,
        cashflow_category=None,
        description=None,
        deposit=None,
        income=None,
        outcome=None,
        direction=None,
        can_print_fiscal=None,
        deleted=None,
        is_fiscal=None,
        created_at=None,
        custom_created_at=None,
        tags=None,
        relation_id=None,
        cashbox_id=None,
        client_id=None,
        employee_id=None,
        order_id=None,
        user_id=None,
        filter_payments=None,
        filter_cashboxes=None,
        filter_order=None
    ):
    try:
        # Достаем платеж из базы данных в виде объекта
        payment = self.pgsql_connetction.session.query(Payments).get(id)
        # создаем список имен всех аргументов текущей фнкции
        fields = inspect.getfullargspec(edit_payments).args[:-4]
        # Идем циклоа по списку имен
        for field in fields:
            # преобразовываем имя функции в переменную
            war = locals()[field]
            # Если значение переменной присутсвует, присваееваем его соответсвующему атрибуту обекта
            if war is not None:
                setattr(payment, field, war)

        self.pgsql_connetction.session.add(payment)

        if payment.relation_id and deleted is not None:
            payment2 = self.pgsql_connetction.session.query(Payments).get(payment.relation_id)
            payment2.deleted = deleted

            self.pgsql_connetction.session.add(payment2)

        if deleted is True:
            payment_event = Events(
                object_type=6,  # Платеж
                object_id=id,
                event_type='DELETE_OPERATION',
                current_status_id=None,
                branch_id=None,
                employee_id=user_id,
                changed=[{
                    'title': 'Платеж удален',
                    'new': {
                        'id': payment.id,
                        'title': f'{payment.description}   {payment.income or payment.outcome} руб.'
                    }
                }]
            )
            self.pgsql_connetction.session.add(payment_event)

        self.pgsql_connetction.session.flush()

        if payment.order_id:
            order = self.pgsql_connetction.session.query(Orders).get(payment.order_id)

            discount_sum = 0
            price = 0
            payed = 0
            if order.operations:
                for operation in order.operations:
                    if not operation.deleted:
                        discount_sum += operation.discount_value
                        price += operation.total
            if order.parts:
                for parts in order.parts:
                    if not parts.deleted:
                        discount_sum += parts.discount_value
                        price += parts.total
            if order.payments:
                for payment in order.payments:
                    if not payment.deleted:
                        payed += payment.income
                        payed += payment.outcome

            order.discount_sum = discount_sum
            order.price = price
            order.payed = payed
            order.missed_payments = price - payed

            self.pgsql_connetction.session.add(order)
            self.pgsql_connetction.session.flush()

            if deleted is True:
                order_event = Events(
                    object_type=1,  # Заказ
                    object_id=payment.order_id,
                    event_type='DELETE_PAYMENT',
                    current_status_id=self.pgsql_connetction.session.query(Orders.status_id).filter_by(id=payment.order_id).scalar(),
                    branch_id=None,
                    employee_id=user_id,
                    changed=[{
                        'title': 'Удален платеж/выплата',
                        'new': {
                            'id': payment.id,
                            'title': payment.income or payment.outcome
                        }
                    }]
                )
                self.pgsql_connetction.session.add(order_event)
                self.pgsql_connetction.session.flush()

        result = {'success': True}

        if filter_payments:
            query = self.pgsql_connetction.session.query(Payments)
            if filter_payments.get('custom_created_at'):
                query = query.filter(filter_payments['custom_created_at'][0] <= Payments.custom_created_at)
                query = query.filter(Payments.custom_created_at <= filter_payments['custom_created_at'][1])
            if filter_payments.get('cashbox_id'):
                query = query.filter(Payments.cashbox_id == filter_payments['cashbox_id'])
            if filter_payments.get('tags'):
                query = query.filter(tags in Payments.tags)
            if filter_payments.get('deleted') is not None:
                query = query.filter(filter_payments['deleted'] or Payments.deleted.is_(False))

            query = query.order_by(desc(Payments.custom_created_at))

            result['payments_count'] = query.count()

            payments = query.all()

            data = []
            for row in payments:
                query = self.pgsql_connetction.session.query(func.sum(Payments.income + Payments.outcome))
                query = query.filter(Payments.cashbox_id == row.cashbox.id)
                query = query.filter(Payments.deleted != True)
                query = query.filter(Payments.custom_created_at <= row.custom_created_at)
                deposit = query.scalar()

                data.append({
                    'id': row.id,
                    'cashflow_category': row.cashflow_category,
                    'description': row.description,
                    'deposit': deposit,
                    'income': row.income,
                    'outcome': row.outcome,
                    'direction': row.direction,
                    'can_print_fiscal': row.can_print_fiscal,
                    'deleted': row.deleted,
                    'is_fiscal': row.is_fiscal,
                    'created_at': row.created_at,
                    'custom_created_at': row.custom_created_at,
                    'tags': row.tags,
                    'relation_id': row.relation_id,
                    'cashbox': {
                        'id': row.cashbox.id,
                        'title': row.cashbox.title,
                        'type': row.cashbox.type
                    } if row.cashbox else {},
                    'client': {
                        'id': row.client.id,
                        'name': row.client.name,
                        'phone': [ph.number for ph in row.client.phone] if row.client.phone else []
                    } if row.client else {},
                    'employee': {
                        'id': row.employee.id,
                        'name': f'{row.employee.last_name} {row.employee.first_name}'
                    } if row.employee else {},
                    'order': {
                        'id': row.order.id,
                        'id_label': row.order.id_label
                    } if row.order else {}
                })

            result['payments'] = data

        if filter_cashboxes:
            query = self.pgsql_connetction.session.query(Cashboxs)
            if filter_cashboxes.get('deleted'):
                query = query.filter(filter_cashboxes['deleted'] or Cashboxs.deleted.is_(False))

            cashboxes = query.all()

            data = []
            for row in cashboxes:
                query = self.pgsql_connetction.session.query(func.sum(Payments.income + Payments.outcome))
                query = query.filter(Payments.cashbox_id == row.id)
                query = query.filter(Payments.deleted.is_(False))
                balance = query.scalar()

                data.append({
                    'id': row.id,
                    'title': row.title,
                    'balance': balance,
                    'type': row.type,
                    'isGlobal': row.isGlobal,
                    'isVirtual': row.isVirtual,
                    'deleted': row.deleted,
                    'permissions': row.permissions,
                    'employees': row.employees,
                    'branch_id': row.branch_id
                })

            result['cashboxes'] = data

        if filter_order:
            order = self.pgsql_connetction.session.query(Orders).get(filter_order['update_order'])
            result['order'] = {
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
                'remaining': order.estimated_done_at - time_now() if order.estimated_done_at else None,
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
                # 'engineer': {
                #     'id': row.engineer.id,
                #     'first_name': row.engineer.first_name,
                #     'last_name': row.engineer.last_name,
                #     'email': row.engineer.email,
                #     'phone': row.engineer.phone,
                # } if row.engineer else {},
                # 'manager': {
                #     'id': row.manager.id,
                #     'first_name': row.manager.first_name,
                #     'last_name': row.manager.last_name,
                #     'email': row.manager.email,
                #     'phone': row.manager.phone,
                # } if row.manager else {},
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

            query = self.pgsql_connetction.session.query(Orders)

            if filter_order.get('created_at') is not None:
                query = query.filter(filter_order['created_at'][0] <= Orders.created_at)
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

            query = query.order_by(
                getattr(Orders, filter_order.get('field_sort'), 'id') if filter_order.get('sort') == 'asc' else desc(
                    getattr(Orders, filter_order.get('field_sort'), 'id')))

            count = query.count()
            result['count'] = count

            query = query.limit(50)
            if filter_order.get('page', 0): query = query.offset(filter_order['page'] * 50)

            orders = query.all()

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
                    'remaining': row.estimated_done_at - time_now() if row.estimated_done_at else None,
                    'remaining_status': row.status_deadline - time_now() if row.status_deadline else None,
                    'remaining_warranty': row.warranty_date - time_now() if row.warranty_date else None,

                    'overdue': row.estimated_done_at > time_now() if row.estimated_done_at else False,
                    'status_overdue': row.status_deadline > time_now() if row.status_deadline else False,
                    'urgent': row.urgent,
                    'warranty_measures': row.warranty_date < time_now() if row.warranty_date else False,

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
                result['orders'] = data

        self.pgsql_connetction.session.commit()
        return result, 202
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550

def del_payments(self, id):
    try:
        payment = self.pgsql_connetction.session.query(Payments).get(id)
        if payment:
            if payment.relation_id:
                payment2 = self.pgsql_connetction.session.query(Payments).get(payment.relation_id)
                self.pgsql_connetction.session.delete(payment2)
            self.pgsql_connetction.session.delete(payment)
            self.pgsql_connetction.session.commit()
            return {'success': True, 'message': f'{id} deleted'}, 202
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550