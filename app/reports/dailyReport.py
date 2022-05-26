from datetime import datetime, timedelta, timezone
from flask import Blueprint
from sqlalchemy import func

from app.db.interaction.db_iteraction import db_iteraction, scheduler
from app.db.models.models import Orders, Payments, Operations, Payrolls, Employees
from config import config
from utils import bot_send_message

daily_report = Blueprint('daily_report', __name__)

start_date = datetime(day=1, month=3, year=2022, hour=20, minute=0, tzinfo=timezone(timedelta(hours=3)))
@scheduler.task('interval', id='do_job_1', days=1, start_date=start_date)
def job1():

    employee_ids = [1, 2, 4, 7]

    # Определим интервал времени для поиска
    now = datetime.now(timezone.utc) + timedelta(hours=3, minutes=0)
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
    income_sum = query.scalar() or 0

    # Найдем сумму выполненых работ
    query = db_iteraction.pgsql_connetction.session.query(func.sum(Operations.total))
    query = query.filter(Operations.deleted.is_(False))
    query = query.filter(Operations.created_at >= start)
    query = query.filter(Operations.created_at <= end)
    operation_sum = query.scalar() or 0

    # Найдем сумму возвратов
    query = db_iteraction.pgsql_connetction.session.query(func.sum(Payments.outcome))
    query = query.filter(Payments.deleted.is_(False))
    query = query.filter(Payments.custom_created_at >= start)
    query = query.filter(Payments.custom_created_at <= end)
    query = query.filter(Payments.cashflow_category == 'Возврат денег покупателю')
    refund_sum = query.scalar() or 0

    # Найдем количество заркытых заказов
    query = db_iteraction.pgsql_connetction.session.query(Orders)
    query = query.filter(Orders.closed_at >= start)
    query = query.filter(Orders.closed_at <= end)
    order_closed = query.count() or 0

    # Посчитаем прибыль
    query = db_iteraction.pgsql_connetction.session.query(func.sum(Payrolls.income + Payrolls.outcome))
    query = query.filter(Payrolls.deleted.is_(False))
    query = query.filter(Payrolls.relation_type != 12)
    query = query.filter(Payrolls.created_at >= start)
    query = query.filter(Payrolls.created_at <= end)
    payroll_sum = query.scalar() or 0
    total = income_sum - refund_sum - payroll_sum - 2500

    # Посчитаем выполненные работы по инженерам
    list_employees = []
    list_for_employee = []
    for employee_id in employee_ids:
        query = db_iteraction.pgsql_connetction.session.query(func.sum(Operations.total))
        query = query.filter(Operations.deleted.is_(False))
        query = query.filter(Operations.created_at >= start)
        query = query.filter(Operations.created_at <= end)
        query = query.filter(Operations.engineer_id == employee_id)
        operation_employee_sum = query.scalar() or 0

        query = db_iteraction.pgsql_connetction.session.query(Operations)
        query = query.filter(Operations.deleted.is_(False))
        query = query.filter(Operations.created_at >= start)
        query = query.filter(Operations.created_at <= end)
        query = query.filter(Operations.engineer_id == employee_id)
        operation_employee_count = query.count() or 0

        query = db_iteraction.pgsql_connetction.session.query(Orders)
        query = query.filter(Orders.created_at >= start)
        query = query.filter(Orders.created_at <= end)
        query = query.filter(Orders.created_by_id == employee_id)
        employee_created = query.count() or 0

        query = db_iteraction.pgsql_connetction.session.query(Orders)
        query = query.filter(Orders.closed_at >= start)
        query = query.filter(Orders.closed_at <= end)
        query = query.filter(Orders.closed_by_id == employee_id)
        employee_closed = query.count() or 0

        query = db_iteraction.pgsql_connetction.session.query(func.sum(Payrolls.income + Payrolls.outcome))
        query = query.filter(Payrolls.deleted.is_(False))
        query = query.filter(Payrolls.relation_type != 12)
        query = query.filter(Payrolls.custom_created_at >= start)
        query = query.filter(Payrolls.custom_created_at <= end)
        query = query.filter(Payrolls.employee_id == employee_id)
        employee_payroll_sum = query.scalar() or 0

        query = db_iteraction.pgsql_connetction.session.query(func.concat(Employees.last_name, ' ', Employees.first_name))
        name = query.filter_by(id=employee_id).scalar()

        if operation_employee_count:
            list_employees.append({
                'name': name,
                'count': operation_employee_count,
                'operation_sum': operation_employee_sum
            })

        list_for_employee.append({
            'id': employee_id,
            'name': name,
            'count': operation_employee_count,
            'operation_sum': operation_employee_sum * 0.38 if employee_id != 7 else operation_employee_sum * 0.30,
            'created': employee_created,
            'closed': employee_closed,
            'payroll_sum': employee_payroll_sum
        })

    list_employees = sorted(list_employees, key=lambda employee: employee['operation_sum'], reverse=True)
    rows = []
    for employee in list_employees:
        rows.append(f'{employee["name"]} выполнил {employee["count"]} работ на сумму {int(employee["operation_sum"])} руб.\n\n')


    if any([order_created, income_sum, operation_sum, refund_sum, order_closed]):
        text = f"Отчет на {now.strftime('%d.%m.%y')}\n"
        if order_created: text += f'Создано заказов: {order_created}\n'
        if order_closed: text += f'Закрыто заказов: {order_closed}\n'
        if income_sum: text += f'Выручка: {int(income_sum)} руб.\n'
        if operation_sum: text += f'Выполнили работ на: {int(operation_sum)} руб.\n'
        if refund_sum: text += f'Сделано возвратов: {int(refund_sum)} руб.\n'
        if payroll_sum: text += f'Расходы на ЗП: {int(payroll_sum)} руб.\n'
        text += 'Прочий расход: 1500 руб.\n'
        text += f'Прибыль: {total} руб.\n'
        text += 'Сотрудники:\n'
        for row in rows:
            text += row

        # посчитаем денежный поток по кассам

        # Оценим результат
        if config['SEND_SMS']:
            bot_send_message(1, text)
        else:
            print(text)

    for employee in list_for_employee:
        if any([employee['count'], employee['operation_sum'], employee['created'], employee['closed'], employee['payroll_sum']]):
            text = f"Отчет на {now.strftime('%d.%m.%y')}\n"
            if employee['count']:
                text += f"Выполнил работ: {employee['count']}\n"
                text += f"На сумму: {int(employee['operation_sum'])} руб.\n"
            if employee['created']:
                text += f"Создал заказов: {employee['created']}\n"
            if employee['closed']:
                text += f"Закрыл заказов: {employee['closed']}\n"
            if employee['payroll_sum']:
                text += f"Начислено ЗП: {int(employee['payroll_sum'])} руб.\n"
            if config['SEND_SMS']:
                bot_send_message(employee['id'], text)
                # bot_send_message(1, employee['name'])
                # bot_send_message(1, text)
            else:
                print(employee['name'])
                print(text)
