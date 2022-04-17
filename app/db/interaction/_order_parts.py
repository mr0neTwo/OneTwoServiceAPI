import inspect
import traceback

from sqlalchemy import desc, func

from app.db.models.models import OrderParts, time_now, Orders, Events, Employees


def add_oder_parts(
        self,
        amount,
        cost,
        discount_value,
        engineer_id,
        price,
        total,
        title,
        comment,
        percent,
        discount,
        deleted,
        warranty_period,
        created_at,
        order_id,
        user_id,
        filter_order=None
    ):
    try:
        oder_part = OrderParts(
            amount=amount,
            cost=cost,
            discount_value=discount_value,
            engineer_id=engineer_id,
            price=price,
            total=total,
            title=title,
            comment=comment,
            percent=percent,
            discount=discount,
            deleted=deleted,
            warranty_period=warranty_period,
            created_at=created_at,
            order_id=order_id
        )
        self.pgsql_connetction.session.add(oder_part)
        self.pgsql_connetction.session.flush()

        order = self.pgsql_connetction.session.query(Orders).filter(Orders.id == order_id).first()
        result = {'success': True}

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
        self.pgsql_connetction.session.refresh(order)

        # Добавим событие добавление запчасти
        order_event = Events(
            object_type=1,  # Заказ
            object_id=order.id,
            event_type='ADD_ORDER_PART',
            current_status_id=order.status_id,
            branch_id=order.branch_id,
            employee_id=user_id,
            changed=[{
                'title': 'Добавлена запчасть',
                'new': {
                    'id': oder_part.id,
                    'title': oder_part.title
                }
            }]
        )
        operation_event = Events(
            object_type=7,  # Работа в заказе
            object_id=oder_part.id,
            event_type='ADD_ORDER_PART',
            current_status_id=None,
            branch_id=None,
            employee_id=user_id,
            changed=[{
                'title': 'Добавлена запчасть',
                'new': {
                    'id': oder_part.id,
                    'title': title or oder_part.title
                }
            }]
        )
        self.pgsql_connetction.session.add_all([order_event, operation_event])
        self.pgsql_connetction.session.flush()

        result['order'], result['events'] = self.get_order_by_id(order_id)

        if filter_order:
            result['orders'] = self.get_orders_by_filter(filter_order)

        self.pgsql_connetction.session.commit()
        return result, 201
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550

def get_oder_parts(
        self,
        id=None,
        engineer_id=None,
        deleted=None,
        created_at=None,
        order_id=None,
        page=0
    ):
    try:
        query = self.pgsql_connetction.session.query(OrderParts)
        if id is not None: query = query.filter(OrderParts.id == id)
        if engineer_id is not None: query = query.filter(OrderParts.engineer_id == engineer_id)
        if deleted is not None: query = query.filter((deleted or OrderParts.deleted.is_(False)))
        if order_id is not None: query = query.filter(OrderParts.order_id == order_id)
        if created_at is not None:
            query = query.filter(OrderParts.created_at > created_at[0])
            query = query.filter(OrderParts.created_at < created_at[1])
        result = {'success': True}
        result['count'] = query.count()

        query = query.limit(50)
        if page: query = query.offset(page * 50)

        oder_parts = query.all()

        data = []
        for row in oder_parts:
            data.append({
                'id': row.id,
                'amount': row.amount,
                'cost': row.cost,
                'discount_value': row.discount_value,
                'engineer_id': row.engineer_id,
                'price': row.price,
                'total': row.total,
                'title': row.title,
                'comment': row.comment,
                'percent': row.percent,
                'discount': row.discount,
                'deleted': row.deleted,
                'warranty': (row.created_at + row.warranty_period) > time_now(),
                'warranty_period': row.warranty_period,
                'created_at': row.created_at,
                'updated_at': row.updated_at,
                'order_id': row.order_id
            })

        result['data'] = data
        result['page'] = page
        return result, 200
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550

def edit_oder_parts(
        self,
        id,
        amount=None,
        cost=None,
        discount_value=None,
        engineer_id=None,
        price=None,
        total=None,
        title=None,
        comment=None,
        percent=None,
        discount=None,
        deleted=None,
        warranty_period=None,
        created_at=None,
        order_id=None,
        user_id=None,
        filter_order=None
    ):
    try:
        order_part = self.pgsql_connetction.session.query(OrderParts).filter_by(id=id).first()
        # Добавим события
        list_events = []
        if deleted is not True and ((order_part.total != total) or (title is not None and order_part.title != title)):
            order_event = Events(
                object_type=1,  # Заказ
                object_id=order_part.order_id,
                event_type='CHANGE_ORDER_PART',
                current_status_id=self.pgsql_connetction.session.query(Orders.status_id).filter_by(id=order_part.order_id).scalar(),
                branch_id=None,
                employee_id=user_id,
                changed=[{
                    'title': 'Изменена запчасть',
                    'current': {'title': f'{order_part.title}  {order_part.total} руб.'},
                    'new': {'title': f'{title} {total} руб.'}
                }]
            )
            list_events.append(order_event)

        if deleted is True:
            order_event = Events(
                object_type=1,  # Заказ
                object_id=order_part.order_id,
                event_type='DELETE_ORDER_PART',
                current_status_id=self.pgsql_connetction.session.query(Orders.status_id).filter_by(id=order_part.order_id).scalar(),
                branch_id=None,
                employee_id=user_id,
                changed=[{
                    'title': 'Запчать удалена',
                    'new': {
                        'id': order_part.id,
                        'title': title or order_part.title
                    }
                }]
            )
            list_events.append(order_event)
            operation_event = Events(
                object_type=7,  # Запчасть в заказе
                object_id=order_part.id,
                event_type='DELETE_ORDER_PART',
                current_status_id=None,
                branch_id=None,
                employee_id=user_id,
                changed=[{
                    'title': 'Запчать удалена',
                    'new': {
                        'id': order_part.id,
                        'title': title or order_part.title
                    }
                }]
            )
            list_events.append(operation_event)

        changed_list = []
        if amount is not None and order_part.amount != amount:
            changed_list.append({
                'title': 'Изменено количество',
                'current': {'title': order_part.amount},
                'new': {'title': amount}
            })
        if cost is not None and order_part.cost != cost:
            changed_list.append({
                'title': 'Изменена себестоимость',
                'current': {'title': order_part.cost},
                'new': {'title': cost}
            })
        if price is not None and order_part.price != price:
            changed_list.append({
                'title': 'Изменена цена',
                'current': {'title': order_part.price},
                'new': {'title': price}
            })
        if total is not None and order_part.total != total:
            changed_list.append({
                'title': 'Изменена итогавая стоимость',
                'current': {'title': order_part.total},
                'new': {'title': total}
            })
        if comment is not None and order_part.comment != comment:
            changed_list.append({
                'title': 'Изменен коментарий' if order_part.comment else 'Добавлен коментарий',
                'current': {'title': order_part.comment},
                'new': {'title': comment}
            })
        if discount_value is not None and order_part.discount_value != discount_value:
            changed_list.append({
                'title': 'Изменена скидка',
                'current': {'title': order_part.discount_value},
                'new': {'title': discount_value}
            })
        if warranty_period is not None and order_part.warranty_period != warranty_period:
            changed_list.append({
                'title': 'Изменен срок гарантии',
                'current': {'title': order_part.warranty_period},
                'new': {'title': warranty_period}
            })
        if engineer_id is not None and order_part.engineer_id != engineer_id:
            changed_list.append({
                'title': 'Изменен иженер',
                'current': {
                    'id': order_part.engineer_id,
                    'title': self.pgsql_connetction.session.query(
                        func.concat(Employees.first_name, ' ', Employees.last_name)).filter_by(id=order_part.engineer_id).scalar()
                },
                'new': {
                    'id': engineer_id,
                    'title': self.pgsql_connetction.session.query(
                        func.concat(Employees.first_name, ' ', Employees.last_name)).filter_by(id=engineer_id).scalar()
                }
            })
        if changed_list:
            order_event = Events(
                object_type=7,  # Работа в заказе
                object_id=order_part.id,
                event_type='CHANGE_ORDER_PART',
                current_status_id=None,
                branch_id=None,
                employee_id=user_id,
                changed=changed_list
            )
            list_events.append(order_event)

        self.pgsql_connetction.session.add_all(list_events)
        self.pgsql_connetction.session.flush()

        fields = inspect.getfullargspec(edit_oder_parts).args[:-2]  # список имен всех аргументов текущей фнкции
        for field in fields:
            war = locals()[field]  # Находим переменную от имени и присваеваем war
            if war is not None:
                setattr(order_part, field, war)

        self.pgsql_connetction.session.add(order_part)
        self.pgsql_connetction.session.flush()

        order = self.pgsql_connetction.session.query(Orders).get(order_id)
        result = {'success': True}

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

        result = {'success': True}

        result['order'], result['events'] = self.get_order_by_id(order_id)

        if filter_order:
            result['orders'] = self.get_orders_by_filter(filter_order)

        self.pgsql_connetction.session.commit()
        return result, 202
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550

def del_oder_parts(self, id):

    oder_parts = self.pgsql_connetction.session.query(OrderParts).get(id)
    if oder_parts:
        self.pgsql_connetction.session.delete(oder_parts)
        self.pgsql_connetction.session.commit()
        return id