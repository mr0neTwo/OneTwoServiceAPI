from sqlalchemy import and_, or_, desc
from sqlalchemy.orm import contains_eager

from app.db.models.models import Orders, time_now


def add_orders(self,
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
               kindof_good,
               brand,
               subtype,
               model,
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
               price,

               urgent,
               ):
    orders = Orders(
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
        kindof_good_id=kindof_good,
        brand_id=brand,
        subtype_id=subtype,
        model_id=model,
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
        price=price,

        urgent=urgent
    )
    self.pgsql_connetction.session.add(orders)
    self.pgsql_connetction.session.commit()
    self.pgsql_connetction.session.refresh(orders)
    order = {
        'id': orders.id,
        'created_at': orders.created_at,
        'estimated_done_at': orders.estimated_done_at,
        'scheduled_for': orders.scheduled_for,
        'warranty_date': orders.warranty_date,
        'status_deadline': orders.status_deadline,

        'id_label': orders.id_label,
        'serial': orders.serial,
        'malfunction': orders.malfunction,
        'packagelist': orders.packagelist,
        'appearance': orders.appearance,
        'manager_notes': orders.manager_notes,

        'estimated_cost': orders.estimated_cost,

        'urgent': orders.urgent,
        'ad_campaign': {
            'id': orders.ad_campaign.id,
            'name': orders.ad_campaign.name
        } if orders.ad_campaign else {},
        'branch': {
            'id': orders.branch.id,
            'name': orders.branch.name
        } if orders.branch else {},
        'status': {
            'id': orders.status.id,
            'name': orders.status.name,
            'color': orders.status.color,
            'group': orders.status.group
        } if orders.status else {},
        'client': {
            'id': orders.client.id,
            'conflicted': orders.client.conflicted,
            'email': orders.client.email,
            'name': orders.client.name,
            'name_doc': orders.client.name_doc,
            'discount_good_type': orders.client.discount_good_type,
            'discount_materials_type': orders.client.discount_materials_type,
            'discount_service_type': orders.client.discount_service_type,
            'notes': orders.client.notes,
            'phone': [{
                'id': ph.id,
                'number': ph.number,
                'notify': ph.notify,
                'title': ph.title
            } for ph in orders.client.phone] if orders.client.phone else []
        } if orders.client else {},
        'order_type': {
            'id': orders.order_type.id,
            'name': orders.order_type.name
        } if orders.order_type else {},
        'kindof_good': {
            'id': orders.kindof_good.id,
            'title': orders.kindof_good.title,
            'icon': orders.kindof_good.icon,
        } if orders.kindof_good else {},
        'brand': {
            'id': orders.brand.id,
            'title': orders.brand.title,
        } if orders.brand else {},
        'subtype': {
            'id': orders.subtype.id,
            'title': orders.subtype.title,
        } if orders.subtype else {},
        'model': {
            'id': orders.model.id,
            'title': orders.model.title,
        } if orders.model else {},
        'engineer_id': orders.engineer_id,
        'manager_id': orders.manager_id,
    }
    return order


def get_orders(self,
               id=None,
               created_at=None,
               done_at=None,
               closed_at=None,
               assigned_at=None,
               estimated_done_at=None,
               scheduled_for=None,
               warranty_date=None,

               ad_campaign_id=None,
               branch_id=None,
               status_id=None,
               client_id=None,
               order_type_id=None,
               kindof_good=None,
               brand=None,
               subtype=None,
               model=None,
               cell=None,
               engineer_id=None,
               manager_id=None,

               id_label=None,
               serial=None,
               client_name=None,
               client_phone=None,
               search=None,

               urgent=None,
               overdue=None,
               status_overdue=None,

               field_sort='id',
               sort='desc',
               page=0):
    if any([id, created_at, done_at, closed_at, assigned_at, estimated_done_at, scheduled_for, warranty_date,
            ad_campaign_id, branch_id, status_id, client_id, order_type_id, engineer_id, manager_id, id_label,
            kindof_good, brand, model, subtype, serial, client_name, client_phone, urgent, overdue, status_overdue,
            search, cell]):

        if search:
            orders = self.pgsql_connetction.session.query(Orders) \
                .join(Orders.client) \
                .options(contains_eager(Orders.client)) \
                .filter(or_(
                    Orders.id_label.ilike(f'%{search}%'),
                    Orders.serial.ilike(f'%{search}%'),
                    Orders.client.property.mapper.class_.name.ilike(f'%{search}%')
                ))\
                .filter(and_(
                    Orders.urgent == urgent if urgent is not None else True,
                    Orders.engineer_id.in_(engineer_id) if engineer_id else True,
                    Orders.status_id.in_(status_id) if status_id else True,
                    (Orders.estimated_done_at < time_now()) if overdue else True,
                    (Orders.status_deadline < time_now()) if status_overdue else True
                ))\
                .order_by(
                getattr(Orders, field_sort, 'id') if sort == 'asc' else desc(getattr(Orders, field_sort, 'id')))
        else:
            orders = self.pgsql_connetction.session.query(Orders).join(Orders.client).filter(
                and_(
                    Orders.id == id if id else True,
                    (Orders.created_at >= created_at[0] if created_at[0] else True) if created_at else True,
                    (Orders.created_at <= created_at[1] if created_at[1] else True) if created_at else True,
                    (Orders.done_at >= done_at[0] if done_at[0] else True) if done_at else True,
                    (Orders.done_at <= done_at[1] if done_at[1] else True) if done_at else True,
                    (Orders.closed_at >= closed_at[0] if closed_at[0] else True) if closed_at else True,
                    (Orders.closed_at <= closed_at[1] if closed_at[1] else True) if closed_at else True,
                    (Orders.assigned_at >= assigned_at[0] if assigned_at[0] else True) if assigned_at else True,
                    (Orders.assigned_at <= assigned_at[1] if assigned_at[1] else True) if assigned_at else True,
                    (Orders.estimated_done_at >= estimated_done_at[0] if estimated_done_at[
                        0] else True) if estimated_done_at else True,
                    (Orders.estimated_done_at <= estimated_done_at[1] if estimated_done_at[
                        1] else True) if estimated_done_at else True,
                    (Orders.scheduled_for >= scheduled_for[0] if scheduled_for[0] else True) if scheduled_for else True,
                    (Orders.scheduled_for <= scheduled_for[1] if scheduled_for[1] else True) if scheduled_for else True,
                    (Orders.warranty_date >= warranty_date[0] if warranty_date[0] else True) if warranty_date else True,
                    (Orders.warranty_date <= warranty_date[1] if warranty_date[1] else True) if warranty_date else True,

                    Orders.ad_campaign_id.in_(ad_campaign_id) if ad_campaign_id else True,
                    Orders.branch_id.in_(branch_id) if branch_id else True,
                    Orders.status_id.in_(status_id) if status_id else True,
                    Orders.client_id.in_(client_id) if client_id else True,
                    Orders.order_type_id.in_(order_type_id) if order_type_id else True,
                    Orders.engineer_id.in_(engineer_id) if engineer_id else True,
                    Orders.manager_id.in_(manager_id) if manager_id else True,

                    Orders.cell == cell if cell else True,
                    Orders.id_label.ilike(f'%{id_label}%') if id_label else True,
                    # Orders.kindof_good == kindof_good if kindof_good else True,
                    # Orders.brand == brand if brand else True,
                    # Orders.model == model if model else True,
                    # Orders.subtype == subtype if subtype else True,
                    # Orders.serial.ilike(f'%{serial}%') if serial else True,
                    Orders.client.property.mapper.class_.name.ilike(f'%{client_name}%') if client_name else True,
                    # Orders.client.property.mapper.class_.phone[0].ilike(f'%{client_name}%') if client_phone else True,

                    Orders.urgent == urgent if urgent != None else True,
                    (Orders.estimated_done_at < time_now()) if overdue else True,
                    (Orders.status_deadline < time_now()) if status_overdue else True
                )
            ).order_by(
                getattr(Orders, field_sort, 'id') if sort == 'asc' else desc(getattr(Orders, field_sort, 'id')))
    else:
        orders = self.pgsql_connetction.session.query(Orders) \
            .order_by(
            getattr(Orders, field_sort, 'id') if sort == 'asc' else desc(getattr(Orders, field_sort, 'id')))

    self.pgsql_connetction.session.expire_all()
    result = {'success': True}
    count = orders.count()
    result['count'] = count

    max_page = count // 50 if count % 50 > 0 else count // 50 - 1

    if page > max_page and max_page != -1:
        return {'success': False, 'message': 'page is not defined'}, 400

    data = []
    for row in orders[50 * page: 50 * (page + 1)]:
        discount_sum = 0
        price = 0
        payed = 0
        if row.operations:
            for operation in row.operations:
                if not operation.deleted:
                    discount_sum += operation.discount_value
                    price += operation.total
        if row.parts:
            for parts in row.parts:
                if not parts.deleted:
                    discount_sum += parts.discount_value
                    price += parts.total
        if row.payments:
            for payment in row.payments:
                if not payment.deleted:
                    payed += payment.income
                    payed += payment.outcome
        data.append({
            'id': row.id,
            'created_at': row.created_at,
            'updated_at': row.updated_at,
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
            'missed_payments': price - payed,
            'discount_sum': discount_sum,
            'payed': payed,
            'price': price,
            'remaining': row.estimated_done_at - time_now() if row.estimated_done_at else None,
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
                'ad_campaign': {
                    'id': row.client.ad_campaign.id,
                    'name': row.client.ad_campaign.name
                },
                'address': row.client.address,
                'conflicted': row.client.conflicted,
                'name_doc': row.client.name_doc,

                'discount_good_type': row.client.discount_good_type,
                'discount_materials_type': row.client.discount_materials_type,
                'discount_service_type': row.client.discount_service_type,

                'discount_code': row.client.discount_code,

                'discount_goods': row.client.discount_goods,
                'discount_goods_margin_id': row.client.discount_goods_margin_id,

                'discount_materials': row.client.discount_materials,
                'discount_materials_margin_id': row.client.discount_materials_margin_id,

                'discount_services': row.client.discount_services,
                'discount_service_margin_id': row.client.discount_service_margin_id,

                'email': row.client.email,
                'juridical': row.client.juridical,
                'ogrn': row.client.ogrn,
                'inn': row.client.inn,
                'kpp': row.client.kpp,
                'juridical_address': row.client.juridical_address,
                'director': row.client.director,
                'bank_name': row.client.bank_name,
                'settlement_account': row.client.settlement_account,
                'corr_account': row.client.corr_account,
                'bic': row.client.bic,
                'created_at': row.client.created_at,
                'updated_at': row.client.updated_at,
                'name': row.client.name,
                'notes': row.client.notes,
                'supplier': row.client.supplier,
                'phone': [{
                    'id': ph.id,
                    'number': ph.number,
                    'title': ph.title,
                    'notify': ph.notify
                } for ph in row.client.phone] if row.client.phone else []
            } if row.client else {},
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
                'id': row.order_type.id,
                'name': row.order_type.name
            } if row.order_type else {},
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
            'closed_by_id': row.closed_by_id,
            'created_by_id': row.created_by_id,
            'engineer_id': row.engineer_id,
            'manager_id': row.manager_id,
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
            } for operat in row.operations] if row.operations else [],
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
            } for part in row.parts] if row.parts else [],
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
                        'phone': [ph.number for ph in row.client.phone] if payment.client.phone else []
                    } if payment.client else {},
                    'employee': {
                        'id': payment.employee.id,
                        'name': f'{payment.employee.last_name} {payment.employee.first_name}'
                    } if payment.employee else {},
                    'order': {
                        'id': payment.order.id,
                        'id_label': payment.order.id_label
                    } if payment.order else {}
                } for payment in row.payments
            ] if row.payments else []
        })

    result['data'] = data
    result['page'] = page
    return result


def edit_orders(self,
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
                kindof_good=None,
                brand=None,
                model=None,
                subtype=None,
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
                urgent=None
                ):
    self.pgsql_connetction.session.query(Orders).filter_by(id=id).update({
        'created_at': created_at if created_at is not None else Orders.created_at,
        'done_at': done_at if done_at is not None else Orders.done_at,
        'closed_at': closed_at if closed_at is not None else Orders.closed_at,
        'assigned_at': assigned_at if assigned_at is not None else Orders.assigned_at,
        'duration': duration if duration is not None else Orders.duration,
        'estimated_done_at': estimated_done_at if estimated_done_at is not None else Orders.estimated_done_at,
        'scheduled_for': scheduled_for if scheduled_for is not None else Orders.scheduled_for,
        'warranty_date': warranty_date if warranty_date is not None else Orders.warranty_date,
        'status_deadline': status_deadline if status_deadline is not None else Orders.status_deadline,

        'ad_campaign_id': ad_campaign_id if ad_campaign_id is not None else Orders.ad_campaign_id,
        'branch_id': branch_id if branch_id is not None else Orders.branch_id,
        'status_id': status_id if status_id is not None else Orders.status_id,
        'client_id': client_id if client_id is not None else Orders.client_id,
        'order_type_id': order_type_id if order_type_id is not None else Orders.order_type_id,
        'kindof_good_id': kindof_good if kindof_good is not None else Orders.kindof_good_id,
        'brand_id': brand if brand is not None else Orders.brand_id,
        'subtype_id': subtype if subtype is not None else Orders.subtype_id,
        'model_id': model if model is not None else Orders.model_id,
        'closed_by_id': closed_by_id if closed_by_id is not None else Orders.closed_by_id,
        'created_by_id': created_by_id if created_by_id is not None else Orders.created_by_id,
        'engineer_id': engineer_id if engineer_id is not None else Orders.engineer_id,
        'manager_id': manager_id if manager_id is not None else Orders.manager_id,

        'id_label': id_label if id_label is not None else Orders.id_label,
        'prefix': prefix if prefix is not None else Orders.prefix,
        'serial': serial if serial is not None else Orders.serial,
        'malfunction': malfunction if malfunction is not None else Orders.malfunction,
        'packagelist': packagelist if packagelist is not None else Orders.packagelist,
        'appearance': appearance if appearance is not None else Orders.appearance,
        'engineer_notes': engineer_notes if engineer_notes is not None else Orders.engineer_notes,
        'manager_notes': manager_notes if manager_notes is not None else Orders.manager_notes,
        'resume': resume if resume is not None else Orders.resume,
        'cell': cell if cell is not None else Orders.cell,

        'estimated_cost': estimated_cost if estimated_cost is not None else Orders.estimated_cost,
        'price': price if price is not None else Orders.price,

        'urgent': urgent if urgent is not None else Orders.urgent,

    })
    self.pgsql_connetction.session.commit()
    return id


def del_orders(self, id):
    orders = self.pgsql_connetction.session.query(Orders).get(id)
    if orders:
        self.pgsql_connetction.session.delete(orders)
        self.pgsql_connetction.session.commit()
        return self.get_orders()


