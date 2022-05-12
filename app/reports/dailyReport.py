from datetime import datetime
from flask import Blueprint
from sqlalchemy import func

from app.db.interaction.db_iteraction import db_iteraction, scheduler
from app.db.models.models import Orders, Payments, Operations, Payrolls, Employees
from utils import bot_send_message

daily_report = Blueprint('daily_report', __name__)

# interval example
@scheduler.task('interval', id='do_job_1', days=1, start_date='2022-05-11 21:00:00')
def job1():

    # Определим интервал времени для поиска
    now = datetime.now()
    # now = datetime(year=2022, month=4, day=27)
    start = int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
    end = int(now.replace(hour=23, minute=59, second=59, microsecond=999999).timestamp())

    # Найдем количиство принятых заказов
    query = db_iteraction.pgsql_connetction.session.query(Orders)
    query = query.filter(Orders.created_at >= start)
    query = query.filter(Orders.created_at <= end)
    order_created = query.count() or 0

    # Найдем сумму поступивших платежей
    query = db_iteraction.pgsql_connetction.session.query(func.sum(Payments.income))
    query = query.filter(Payments.deleted.is_(False))
    query = query.filter(Payments.created_at >= start)
    query = query.filter(Payments.created_at <= end)
    query = query.filter(Payments.cashflow_category == 'Оплата покупателя за услугу, товар')
    income_sum = int(query.scalar()) or 0

    # Найдем сумму выполненых работ
    query = db_iteraction.pgsql_connetction.session.query(func.sum(Operations.total))
    query = query.filter(Operations.deleted.is_(False))
    query = query.filter(Operations.created_at >= start)
    query = query.filter(Operations.created_at <= end)
    operation_sum = int(query.scalar()) or 0

    # Найдем сумму возвратов
    query = db_iteraction.pgsql_connetction.session.query(func.sum(Payments.outcome))
    query = query.filter(Payments.deleted.is_(False))
    query = query.filter(Payments.created_at >= start)
    query = query.filter(Payments.created_at <= end)
    query = query.filter(Payments.cashflow_category == 'Возврат денег покупателю')
    refund_sum = int(query.scalar()) or 0

    # Найдем количество заркытых заказов
    query = db_iteraction.pgsql_connetction.session.query(Orders)
    query = query.filter(Orders.closed_at >= start)
    query = query.filter(Orders.closed_at <= end)
    order_closed = query.count() or 0

    # Посчитаем прибыль
    query = db_iteraction.pgsql_connetction.session.query(func.sum(Payrolls.income + Payrolls.outcome))
    query = query.filter(Payrolls.deleted.is_(False))
    query = query.filter(Payrolls.created_at >= start)
    query = query.filter(Payrolls.created_at <= end)
    payroll_sum = int(query.scalar()) or 0
    total = income_sum - refund_sum - payroll_sum - 2500

    # Посчитаем выполненные работы по инженерам
    list_employees = []
    for emoloyee_id in [1, 2, 4, 7]:
        query = db_iteraction.pgsql_connetction.session.query(func.sum(Operations.total))
        query = query.filter(Operations.deleted.is_(False))
        query = query.filter(Operations.created_at >= start)
        query = query.filter(Operations.created_at <= end)
        query = query.filter(Operations.engineer_id == emoloyee_id)
        operation_employee_sum = int(query.scalar()) or 0

        query = db_iteraction.pgsql_connetction.session.query(Operations)
        query = query.filter(Operations.deleted.is_(False))
        query = query.filter(Operations.created_at >= start)
        query = query.filter(Operations.created_at <= end)
        query = query.filter(Operations.engineer_id == emoloyee_id)
        operation_employee_count = query.count() or 0
        if operation_employee_count:

            list_employees.append({
                'name': db_iteraction.pgsql_connetction.session.query(func.concat(Employees.last_name, ' ', Employees.first_name)).filter_by(id=emoloyee_id).scalar(),
                'count': query.count(),
                'operation_sum': operation_employee_sum
            })
    list_employees = sorted(list_employees, key=lambda employee: employee['operation_sum'], reverse=True)
    rows = []
    for employee in list_employees:
        rows.append(f'{employee["name"]} выполнил {employee["count"]} работ на сумму {employee["operation_sum"]} руб.\n\n')


    if any([order_created, income_sum, operation_sum, refund_sum, order_closed]):
        text = now.strftime('%d.%m.%y') + '\n'
        if order_created: text += f'Создано заказов: {order_created}\n'
        if income_sum: text += f'Выручка: {income_sum} руб.\n' if income_sum else ''
        if operation_sum: text += f'Выполнили работ на: {operation_sum} руб.\n'
        if refund_sum: text += f'Сделано возвратов: {refund_sum} руб.\n'
        if order_closed: text += f'Закрыто заказов: {order_closed}\n'
        text += f'Прибыль: {total} руб.\n'
        text += f'Сотрудники:\n'
        for row in rows:
            text += row

        # посчитаем денежный поток по кассам

        # Оценим результат

        bot_send_message(1, text)
