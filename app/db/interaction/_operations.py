from sqlalchemy import and_
from app.db.models.models import Operations, time_now


def add_operations(self,
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
                   dict_id
                   ):

    operations = Operations(
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
        order_id=order_id,
        dict_id=dict_id
    )
    self.pgsql_connetction.session.add(operations)
    self.pgsql_connetction.session.commit()
    self.pgsql_connetction.session.refresh(operations)
    return operations.id

def get_operations(self,
                   id=None,
                   cost=None,
                   discount_value=None,
                   engineer_id=None,
                   price=None,
                   total=None,
                   title=None,
                   warranty=None,
                   deleted=None,
                   warranty_period=None,
                   created_at=None,
                   updated_at=None,
                   order_id=None,
                   dict_id=None,
                   page=0):

    if any([id, cost, discount_value, engineer_id, price, total, title, warranty != None,
            deleted != None, warranty_period, created_at, updated_at, order_id, dict_id]):
        operations = self.pgsql_connetction.session.query(Operations).filter(
            and_(
                Operations.id == id if id else True,
                Operations.title.like(f'%{title}%') if title else True,
                Operations.cost == cost if cost else True,
                Operations.discount_value == discount_value if discount_value else True,
                Operations.price == price if price else True,
                Operations.total == total if total else True,
                Operations.discount_value == discount_value if discount_value else True,
                Operations.warranty == warranty if warranty != None else True,
                (deleted or Operations.deleted.is_(False)) if deleted != None else True,
                Operations.order_id == order_id if order_id else True,
                Operations.dict_id == dict_id if dict_id else True,
                Operations.warranty_period == warranty_period if warranty_period else True,
                (Operations.created_at >= created_at[0] if created_at[0] else True) if created_at else True,
                (Operations.created_at <= created_at[1] if created_at[1] else True) if created_at else True,
            )
        )
    else:
        operations = self.pgsql_connetction.session.query(Operations)

    self.pgsql_connetction.session.expire_all()
    result = {'success': True}
    count = operations.count()
    result['count'] = count

    max_page = count // 50 if count % 50 > 0 else count // 50 - 1

    if page > max_page and max_page != -1:
        return {'success': False, 'message': 'page is not defined'}, 400

    data = []
    for row in operations[50 * page: 50 * (page + 1)]:
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
            'warranty': (row.created_at + row.warranty_period) > time_now(),
            'deleted': row.deleted,
            'warranty_period': row.warranty_period,
            'created_at': row.created_at,
            'updated_at': row.updated_at,
            'order_id': row.order_id,
            'dict_id': row.dict_id
        })

    result['data'] = data
    result['page'] = page
    return result

def edit_operations(self,
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
                    dict_id=None
                    ):

    self.pgsql_connetction.session.query(Operations).filter_by(id=id).update({
        'amount': amount if amount is not None else Operations.amount,
        'cost': cost if cost is not None else Operations.cost,
        'discount_value': discount_value if discount_value is not None else Operations.discount_value,
        'engineer_id': engineer_id if engineer_id is not None else Operations.engineer_id,
        'price': price if price is not None else Operations.price,
        'total': total if total is not None else Operations.total,
        'title': title if title is not None else Operations.title,
        'comment': comment if comment is not None else Operations.comment,
        'percent': percent if percent is not None else Operations.percent,
        'discount': discount if discount is not None else Operations.discount,
        'deleted': deleted if deleted is not None else Operations.deleted,
        'warranty_period': warranty_period if warranty_period is not None else Operations.warranty_period,
        'created_at': created_at if created_at is not None else Operations.created_at,
        'order_id': order_id if order_id is not None else Operations.order_id,
        'dict_id': dict_id if dict_id is not None else Operations.dict_id
    })
    self.pgsql_connetction.session.commit()
    return id

def del_operations(self, id):

    operations = self.pgsql_connetction.session.query(Operations).get(id)
    if operations:
        self.pgsql_connetction.session.delete(operations)
        self.pgsql_connetction.session.commit()
        return id