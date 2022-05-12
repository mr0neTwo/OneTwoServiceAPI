import inspect
import traceback

from sqlalchemy import desc, func

from app.db.models.models import Payrolls, Payments, Employees


def add_payroll(
        self,
        relation_type,
        relation_id,
        employee_id,
        order_id,
        direction,
        description='',
        income=0,
        outcome=0,
        deleted=False,
        reimburse=False,
        created_at=None,
        custom_created_at=None,
        payroll_filter=None,
        payment=None
    ):
    try:
        payroll = Payrolls(
            description=description,
            income=income,
            outcome=outcome,
            direction=direction,
            deleted=deleted,
            reimburse=reimburse,
            created_at=created_at,
            custom_created_at=custom_created_at,
            relation_type=relation_type,
            relation_id=relation_id,
            employee_id=employee_id,
            order_id=order_id
        )
        self.pgsql_connetction.session.add(payroll)
        self.pgsql_connetction.session.flush()
        if payment:
            self.pgsql_connetction.session.refresh(payroll)
            payment = Payments(
                cashflow_category=payment['cashflow_category'],
                description=f'Выплата заработной платы {self.pgsql_connetction.session.query(func.concat(Employees.last_name, " ", Employees.first_name)).filter_by(id=employee_id).scalar()}',
                income=income,
                outcome=outcome,
                direction=direction,
                deleted=False,
                custom_created_at=custom_created_at,
                relation_type=1,    # Связь с начислением ЗП
                relation_id=payroll.id,
                cashbox_id=payment['cashbox_id'],
                employee_id=employee_id
            )
            self.pgsql_connetction.session.add(payment)
            self.pgsql_connetction.session.flush()

            self.pgsql_connetction.session.refresh(payment)
            payroll.relation_id = payment.id
            self.pgsql_connetction.session.add(payroll)
            self.pgsql_connetction.session.flush()
            # print(f'Платеж добавлен, id: {payment.id}')


        result = {'success': True}

        if payroll_filter:
            query = self.pgsql_connetction.session.query(Payrolls)
            if payroll_filter.get('deleted') is not None:
                query = query.filter(payroll_filter['deleted'] or Payrolls.deleted.is_(False))
            if payroll_filter.get('employee_id') is not None:
                query = query.filter(Payrolls.employee_id == payroll_filter['employee_id'])
            if payroll_filter.get('custom_created_at') is not None:
                query = query.filter(Payrolls.custom_created_at >= payroll_filter['custom_created_at'][0])
                query = query.filter(Payrolls.custom_created_at <= payroll_filter['custom_created_at'][1])

            query = query.order_by(desc(Payrolls.custom_created_at))

            payrolls = query.all()

            data = []
            for row in payrolls:
                query = self.pgsql_connetction.session.query(func.sum(Payrolls.income + Payrolls.outcome))
                query = query.filter(Payrolls.employee_id == row.employee_id)
                query = query.filter(Payrolls.deleted.is_(False))
                query = query.filter(Payrolls.custom_created_at <= row.custom_created_at)
                deposit = query.scalar()

                data.append({
                    'id': row.id,
                    'description': row.description,
                    'deposit': deposit,
                    'income': row.income,
                    'outcome': row.outcome,
                    'direction': row.direction,
                    'deleted': row.deleted,
                    'reimburse': row.reimburse,
                    'created_at': row.created_at,
                    'updated_at': row.updated_at,
                    'custom_created_at': row.custom_created_at,
                    'relation_type': row.relation_type,
                    'relation_id': row.relation_id,
                    'employee_id': row.employee_id,
                    'order_id': row.order_id,
                    'order': {
                        'id': row.order.id,
                        'id_label': row.order.id_label,
                    } if row.order else {}
                })

            result['payrolls'] = data
            result['count'] = len(data)

        self.pgsql_connetction.session.commit()
        return result, 201
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def get_payrolls(self, id=None, deleted=None, employee_id=None, custom_created_at=None):

    try:
        query = self.pgsql_connetction.session.query(Payrolls)
        if id is not None:
            query = query.filter(Payrolls.id == id)
        if deleted is not None:
            query = query.filter(deleted or Payrolls.deleted.is_(False))
        if employee_id is not None:
            query = query.filter(Payrolls.employee_id == employee_id)
        if custom_created_at is not None:
            query = query.filter(Payrolls.custom_created_at >= custom_created_at[0])
            query = query.filter(Payrolls.custom_created_at <= custom_created_at[1])

        query = query.order_by(desc(Payrolls.custom_created_at))

        result = {'success': True}

        payroll = query.all()

        data = []
        for row in payroll:
            query = self.pgsql_connetction.session.query(func.sum(Payrolls.income + Payrolls.outcome))
            query = query.filter(Payrolls.employee_id == row.employee_id)
            query = query.filter(Payrolls.deleted.is_(False))
            query = query.filter(Payrolls.custom_created_at <= row.custom_created_at)
            deposit = query.scalar()

            data.append({
                'id': row.id,
                'description': row.description,
                'deposit': deposit,
                'income': row.income,
                'outcome': row.outcome,
                'direction': row.direction,
                'deleted': row.deleted,
                'reimburse': row.reimburse,
                'created_at': row.created_at,
                'updated_at': row.updated_at,
                'custom_created_at': row.custom_created_at,
                'relation_type': row.relation_type,
                'relation_id': row.relation_id,
                'employee_id': row.employee_id,
                'order_id': row.order_id,
                'order': {
                    'id': row.order.id,
                    'id_label': row.order.id_label,
                } if row.order else {}
            })

        result['data'] = data
        result['count'] = len(data)

        return result, 200
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def get_payroll_sum(self, custom_created_at, employee_id):
    try:
        query = self.pgsql_connetction.session.query(func.sum(Payrolls.income + Payrolls.outcome))
        query = query.filter(Payrolls.employee_id == employee_id)
        query = query.filter(Payrolls.relation_type != 12)  # Выплаты ЗП
        query = query.filter(Payrolls.deleted.is_(False))
        query = query.filter(Payrolls.custom_created_at >= custom_created_at[0])
        query = query.filter(Payrolls.custom_created_at <= custom_created_at[1])
        sum = query.scalar()

        result = {'success': True}
        result['sum'] = sum

        return result, 200
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def edit_payroll(
        self,
        id,
        description=None,
        income=None,
        outcome=None,
        direction=None,
        deleted=None,
        reimburse=None,
        custom_created_at=None,
        relation_type=None,
        relation_id=None,
        employee_id=None,
        order_id=None,
        payroll_filter=None
    ):
    try:
        payroll = self.pgsql_connetction.session.query(Payrolls).get(id)
        fields = inspect.getfullargspec(edit_payroll).args[:-1]
        # Идем циклоа по списку имен
        for field in fields:
            # преобразовываем имя функции в переменную
            war = locals()[field]
            # Если значение переменной присутсвует, присваееваем его соответсвующему атрибуту обекта
            if war is not None:
                setattr(payroll, field, war)

        self.pgsql_connetction.session.add(payroll)

        if payroll.relation_type == 12 and deleted is not None:
            payment = self.pgsql_connetction.session.query(Payments).get(payroll.relation_id)
            payment.deleted = deleted
            self.pgsql_connetction.session.add(payment)

        self.pgsql_connetction.session.flush()

        result = {'success': True}

        if payroll_filter:
            query = self.pgsql_connetction.session.query(Payrolls)
            if payroll_filter.get('deleted') is not None:
                query = query.filter(payroll_filter['deleted'] or Payrolls.deleted.is_(False))
            if payroll_filter.get('employee_id') is not None:
                query = query.filter(Payrolls.employee_id == payroll_filter['employee_id'])
            if payroll_filter.get('custom_created_at') is not None:
                query = query.filter(Payrolls.custom_created_at >= payroll_filter['custom_created_at'][0])
                query = query.filter(Payrolls.custom_created_at <= payroll_filter['custom_created_at'][1])

            query = query.order_by(desc(Payrolls.custom_created_at))

            payrolls = query.all()

            data = []
            for row in payrolls:
                query = self.pgsql_connetction.session.query(func.sum(Payrolls.income + Payrolls.outcome))
                query = query.filter(Payrolls.employee_id == row.employee_id)
                query = query.filter(Payrolls.deleted.is_(False))
                query = query.filter(Payrolls.custom_created_at <= row.custom_created_at)
                deposit = query.scalar()

                data.append({
                    'id': row.id,
                    'description': row.description,
                    'deposit': deposit,
                    'income': row.income,
                    'outcome': row.outcome,
                    'direction': row.direction,
                    'deleted': row.deleted,
                    'reimburse': row.reimburse,
                    'created_at': row.created_at,
                    'updated_at': row.updated_at,
                    'custom_created_at': row.custom_created_at,
                    'relation_type': row.relation_type,
                    'relation_id': row.relation_id,
                    'employee_id': row.employee_id,
                    'order_id': row.order_id,
                    'order': {
                        'id': row.order.id,
                        'id_label': row.order.id_label,
                    } if row.order else {}
                })

            result['payrolls'] = data
            result['count'] = len(data)

        self.pgsql_connetction.session.commit()
        return result, 202
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def del_payroll(self, id):
    payroll = self.pgsql_connetction.session.query(Payrolls).get(id)
    if payroll:
        self.pgsql_connetction.session.delete(payroll)
        self.pgsql_connetction.session.commit()
        return id