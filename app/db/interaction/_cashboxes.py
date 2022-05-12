import inspect
import traceback

from sqlalchemy import func, or_

from app.db.models.models import Cashboxs, Payments


def add_cashbox(
    self,
    title,
    balance,
    type,
    isGlobal,
    isVirtual,
    deleted,
    permissions,
    employees,
    branch_id,
    user_id,
    cashbox_filter=None
    ):
    try:
        cashbox = Cashboxs(
            title=title,
            balance=balance,
            type=type,
            isGlobal=isGlobal,
            isVirtual=isVirtual,
            deleted=deleted,
            permissions=permissions,
            employees=employees,
            branch_id=branch_id
        )
        self.pgsql_connetction.session.add(cashbox)
        self.pgsql_connetction.session.flush()

        result = {'success': True}
        if cashbox_filter:
            query = self.pgsql_connetction.session.query(Cashboxs)

            if cashbox_filter.get('deleted') is not None:
                query = query.filter(cashbox_filter['deleted'] or Cashboxs.deleted.is_(False))
            if cashbox_filter.get('branch_id') is not None:
                query = query.filter(or_(Cashboxs.branch_id == cashbox_filter['branch_id'], Cashboxs.isGlobal))

            query = query.order_by(Cashboxs.id)

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
            # Отфильтруем доступные для пользователя кассы
            data = list(filter(lambda cashbox: cashbox['employees'][f'{user_id}']['available'], data))

            result['cashboxes'] = data
            result['count'] = len(data)

        self.pgsql_connetction.session.commit()
        return result, 201
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550

def get_cashbox(self, id=None, deleted=None, branch_id=None, user_id=None):
    try:
        query = self.pgsql_connetction.session.query(Cashboxs)

        if id is not None:
            query = query.filter(Cashboxs.id == id)
        if deleted is not None:
            query = query.filter(deleted or Cashboxs.deleted.is_(False))
        if branch_id is not None:
            query = query.filter(or_(Cashboxs.branch_id == branch_id, Cashboxs.isGlobal))

        query = query.order_by(Cashboxs.id)

        cashboxes = query.all()

        result = {'success': True}

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
        # Отфильтруем доступные для пользователя кассы
        data = list(filter(lambda cashbox: cashbox['employees'][f'{user_id}']['available'], data))

        result['data'] = data
        result['count'] = len(data)
        return result, 200
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550

def edit_cashbox(
    self,
    id,
    title=None,
    balance=None,
    type=None,
    isGlobal=None,
    isVirtual=None,
    deleted=None,
    permissions=None,
    employees=None,
    branch_id=None,
    user_id=None,
    cashbox_filter=None
    ):
    try:
        cashbox = self.pgsql_connetction.session.query(Cashboxs).get(id)
        fields = inspect.getfullargspec(edit_cashbox).args[:-2]  # список имен всех аргументов текущей фнкции
        for field in fields:
            war = locals()[field]  # Находим переменную от имени и присваеваем war
            if war is not None:
                setattr(cashbox, field, war)

        self.pgsql_connetction.session.add(cashbox)
        self.pgsql_connetction.session.flush()

        result = {'success': True}

        if cashbox_filter:
            query = self.pgsql_connetction.session.query(Cashboxs)

            if cashbox_filter.get('deleted') is not None:
                query = query.filter(cashbox_filter['deleted'] or Cashboxs.deleted.is_(False))
            if cashbox_filter.get('branch_id') is not None:
                query = query.filter(or_(Cashboxs.branch_id == cashbox_filter['branch_id'], Cashboxs.isGlobal))

            query = query.order_by(Cashboxs.id)

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
            # Отфильтруем доступные для пользователя кассы
            data = list(filter(lambda cashbox: cashbox['employees'][f'{user_id}']['available'], data))

            result['cashboxes'] = data
            result['count'] = len(data)

        self.pgsql_connetction.session.commit()
        return result, 202
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550

def del_cashbox(self, id):
    try:
        cashbox = self.pgsql_connetction.session.query(Cashboxs).get(id)
        if cashbox:
            self.pgsql_connetction.session.delete(cashbox)
            self.pgsql_connetction.session.commit()
            return {'success': True, 'message': f'{id} deleted'}, 202

    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550