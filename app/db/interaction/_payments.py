import inspect
import traceback

from sqlalchemy import desc, func

from app.db.models.models import Payments, Cashboxs, Orders, Events, Payrolls


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
        relation_type,
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
            relation_type=relation_type,
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
                relation_type=relation_type,
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
            self.pgsql_connetction.session.refresh(order)

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
                query = query.filter(Payments.deleted.is_(False))
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
                    'relation_type': row.relation_type,
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
            if filter_cashboxes.get('deleted') is not None:
                query = query.filter(filter_cashboxes['deleted'] or Cashboxs.deleted.is_(False))
            if filter_cashboxes.get('branch_id') is not None:
                query = query.filter(Cashboxs.branch_id == filter_cashboxes['branch_id'])


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
                result['order'], result['events'] = self.get_order_by_id(filter_order['update_order'])

            result['orders'] = self.get_orders_by_filter(filter_order)

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
            query = self.pgsql_connetction.session.query(func.sum(Payments.income + Payments.outcome))
            query = query.filter(Payments.cashbox_id == row.cashbox.id)
            query = query.filter(Payments.deleted.is_(False))
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
                'relation_type': row.relation_type,
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
        relation_type=None,
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

        if not payment.relation_type and payment.relation_id and deleted is not None:
            payment2 = self.pgsql_connetction.session.query(Payments).get(payment.relation_id)
            payment2.deleted = deleted

            self.pgsql_connetction.session.add(payment2)

        if payment.relation_type == 1 and deleted is not None:
            payroll = self.pgsql_connetction.session.query(Payrolls).get(payment.relation_id)
            payroll.deleted = deleted

            self.pgsql_connetction.session.add(payroll)

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
                    'relation_type': row.relation_type,
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
            if filter_cashboxes.get('branch_id') is not None:
                query = query.filter(Cashboxs.branch_id == filter_cashboxes['branch_id'])

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
            if filter_order:
                if filter_order.get('update_order'):
                    result['order'], result['events'] = self.get_order_by_id(filter_order['update_order'])

            result['orders'] = self.get_orders_by_filter(filter_order)

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
            if not payment.relation_type and payment.relation_id:
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