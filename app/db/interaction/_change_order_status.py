import traceback
from pprint import pprint

from sqlalchemy import or_, desc

from app.db.models.models import Orders, Status, time_now, Payrules, Payrolls, Clients, Phones, EquipmentType, \
    EquipmentBrand, EquipmentSubtype, EquipmentModel, Events
from app.events import event_change_status_to


def change_order_status(self, status_id, order_id, user_id, r_filter=None):

    try:
        # Подгузим текущий заказ
        order = self.pgsql_connetction.session.query(Orders).filter_by(id=order_id).first()

        # Вытащим текущий статус
        current_status = order.status

        # Подгрузим новый статус
        new_status = self.pgsql_connetction.session.query(Status).filter_by(id=status_id).first()

        # Создадим список для изменений
        list_to_add = []

        # Создаим событие смены статуса
        order_event = Events(
            object_type=1,  # Заказ
            object_id=order.id,
            event_type='CHANGE_STATUS',
            current_status_id=status_id,
            branch_id=order.branch_id,
            employee_id=user_id,
            changed=[{
                'title': 'Статус изменен',
                'current': {
                    'id': current_status.id,
                    'title': current_status.name
                },
                'new': {
                    'id': new_status.id,
                    'title': new_status.name
                }
            }]
        )
        list_to_add.append(order_event)

        # Обновим заказ
        order.status_id = status_id
        # Если заказ был закрыт сохраним сотрудника закрывшего заказ
        if new_status.group == 6: order.closed_by_id = user_id
        list_to_add.append(order)

        # Расчет Начислений по статусу Готов ===========================================================================

        # Если переход в группу Готов с груп ниже или групп Закрыт не успешно
        if new_status.group == 4 and (not current_status.group in [4, 5, 6]):
            # Проверим существую ли операции по данном заказу
            if order.operations:
                # Пройдем циклом по всем операциям
                for operation in order.operations:
                    # проверим не удалена ли опарация
                    if not operation.deleted:
                        # Проверим есть ли у данного инженера правило с коэффициентом для данной операции
                        query_rules = self.pgsql_connetction.session.query(Payrules)
                        query_rules = query_rules.filter_by(type_rule=4) # Инженуру за работу/услугу
                        query_rules = query_rules.filter_by(employee_id=operation.engineer_id)
                        query_rules = query_rules.filter_by(order_type=order.order_type.id)
                        query_rules = query_rules.filter_by(check_status=4) # По группе статусов Готов
                        rule = query_rules.first()
                        # Проверим есть ли в самой операции особое правило начисления
                        if operation.dict_service and (operation.dict_service.earnings_percent or operation.dict_service.earnings_summ):
                            # Проверим существуют ли правила начисления процента за данную работу
                            if operation.dict_service.earnings_percent:
                                if rule:
                                    # Определяем сумму вознаграждения
                                    income = operation.dict_service.earnings_percent * operation.total / 100 * rule.coefficient
                                else:
                                    income = operation.dict_service.earnings_percent * operation.total / 100
                                # Добавим начисление
                                if income != 0:
                                    payroll1 = Payrolls(
                                        relation_type=5,  # 5 - за работу по статусу Готов
                                        relation_id=operation.id,
                                        employee_id=operation.engineer_id,
                                        order_id=order.id,
                                        direction=2,  # 2 - приход
                                        description=f'''Начисление за работу "{operation.title}" в заказе {order.id_label}''',
                                        income=income
                                    )
                                    list_to_add.append(payroll1)
                                    del income
                            # Проверим существуют ли правила начисления суммы за данную работу
                            if operation.dict_service.earnings_summ:
                                if rule:
                                    # Определяем сумму вознаграждения
                                    income = operation.dict_service.earnings_summ * rule.coefficient
                                else:
                                    income = operation.dict_service.earnings_summ
                                # Добавим начисление
                                if income != 0:
                                    payroll2 = Payrolls(
                                        relation_type=5,    # 5 - за работу по статусу Готов
                                        relation_id=operation.id,
                                        employee_id=operation.engineer_id,
                                        order_id=order.id,
                                        direction=2,  # 2 - приход
                                        description=f'''Начисление за работу "{operation.title}" в заказе {order.id_label}''',
                                        income=income
                                    )
                                    list_to_add.append(payroll2)
                        # Если в самой операции нет особых правил начисления
                        else:
                            # Пройдем циклом по всем правилам начисления если таковые есть
                            if rule:
                                for rule in query_rules.all():
                                    # Если мы начисляем процент
                                    if rule.method == 0:
                                        # Пройдем по списку коэфициентов и цен и определим сумму начисления
                                        income = 0
                                        for row in rule.count_coeff:
                                            if row['cost'] <= operation.total:
                                                income = row['coef'] * operation.total / 100
                                        # Добавим начисление
                                        if income != 0:
                                            payroll3 = Payrolls(
                                                relation_type=5,  # 5 - за работу по статусу Готов
                                                relation_id=operation.id,
                                                employee_id=operation.engineer_id,
                                                order_id=order.id,
                                                direction=2,  # 2 - приход
                                                description=f'''Начисление за работу "{operation.title}" в заказе {order.id_label}''',
                                                income=income
                                            )
                                            list_to_add.append(payroll3)
                                            del income
                                    else:
                                        # Пройдем по списку коэфициентов и цен и определим сумму начисления
                                        income = 0
                                        for row in rule.count_coeff:
                                            if row['cost'] <= operation.total:
                                                income = row['coef']
                                        # Добавим начисление
                                        if income != 0:
                                            payroll4 = Payrolls(
                                                relation_type=5,  # 5 - за работу по статусу Готов
                                                relation_id=operation.id,
                                                employee_id=operation.engineer_id,
                                                order_id=order.id,
                                                direction=2,  # 2 - приход
                                                description=f'''Начисление за работу "{operation.title}" в заказе {order.id_label}''',
                                                income=income
                                            )
                                            list_to_add.append(payroll4)
                                            del income

        # Списания при возврате статуса с Готов ===============================================================================

        # Если переход с группу Готов в любой другой групу кроме Доставка и Закрыт
        if (not new_status.group in [4, 5, 6]) and current_status.group in [4, 5, 6]:
            # Проверим существую ли операции по данном заказу
            if order.operations:
                # Пройдем циклом по всем операциям
                for operation in order.operations:
                    # проверим не удалена ли опарация
                    if not operation.deleted:
                        # Найдем все начисления по данной операции
                        query_payrolls = self.pgsql_connetction.session.query(Payrolls)
                        query_payrolls = query_payrolls.filter_by(direction=2)  # все которые с приходом
                        query_payrolls = query_payrolls.filter_by(deleted=False)  # Не удаленные
                        query_payrolls = query_payrolls.filter_by(reimburse=False)  # Не возмещенные
                        query_payrolls = query_payrolls.filter_by(relation_type=5)  # Начисленные за работу по статусу Готов
                        query_payrolls =query_payrolls.filter_by(relation_id=operation.id)  # Принадлежащие данной операции
                        payrolls = query_payrolls.all()
                        # Если начисления имеются
                        if payrolls:
                            for payroll in payrolls:
                                if payroll.income != 0:
                                    payroll5 = Payrolls(
                                        relation_type=11,  # Возврат заказа
                                        relation_id=payroll.id,  # id начисления за которое делается возмещение
                                        employee_id=operation.engineer_id,
                                        order_id=order.id,
                                        direction=1,
                                        description=f'''Возврат за операцию "{operation.title}" в заказе {order.id_label}''',
                                        outcome=-payroll.income
                                    )
                                    # Отметим операцию как возмещенную
                                    payroll.reimburse = True
                                    list_to_add.append(payroll)
                                    list_to_add.append(payroll5)


        # Расчет Начислений по статусу Успешно закрыт ==================================================================

        # Если переход в группу Закрыт успешно с любой другой групы
        if new_status.group == 6 and current_status.group != 6:
            # Проверим существуют ли операции по данном заказу
            if order.operations:
                # Пройдем циклом по всем операциям
                for operation in order.operations:
                    # проверим не удалена ли опарация
                    if not operation.deleted:
                        # Проверим есть ли у данного инженера правило с коэффициентом для данной операции
                        query_rules = self.pgsql_connetction.session.query(Payrules)
                        query_rules = query_rules.filter_by(type_rule=4)  # Инженуру за работу/услугу
                        query_rules = query_rules.filter_by(employee_id=operation.engineer_id)
                        query_rules = query_rules.filter_by(order_type=order.order_type.id)
                        query_rules = query_rules.filter_by(check_status=6)  # По группе статусов Успешно закрыт
                        rules = query_rules.all()

                        # Проверим есть ли в самой операции особое правило начисления
                        if operation.dict_service and (operation.dict_service.earnings_percent or operation.dict_service.earnings_summ):
                            # Проверим существуют ли правила начисления процента за данную работу
                            if operation.dict_service.earnings_percent:
                                if rules:
                                    # Определяем сумму вознаграждения
                                    income = operation.dict_service.earnings_percent * operation.total / 100 * rules[0].coefficient
                                else:
                                    income = operation.dict_service.earnings_percent * operation.total / 100
                                # Добавим начисление
                                if income != 0:
                                    payroll6 = Payrolls(
                                        relation_type=4,  # 4 - за работу по статусу Закрыт
                                        relation_id=operation.id,
                                        employee_id=operation.engineer_id,
                                        order_id=order.id,
                                        direction=2,  # 2 - приход
                                        description=f'''Начисление за работу "{operation.title}" в заказе {order.id_label}''',
                                        income=income
                                    )
                                    list_to_add.append(payroll6)
                                    del income
                            # Проверим существуют ли правила начисления суммы за данную работу
                            if operation.dict_service.earnings_summ:
                                if rules:
                                    # Определяем сумму вознаграждения
                                    income = operation.dict_service.earnings_summ * rules[0].coefficient
                                else:
                                    income = operation.dict_service.earnings_summ
                                # Добавим начисление
                                if income != 0:
                                    payroll7 = Payrolls(
                                        relation_type=4,  # 4 - за работу по статусу Закрыт
                                        relation_id=operation.id,
                                        employee_id=operation.engineer_id,
                                        order_id=order['id'],
                                        direction=2,  # 2 - приход
                                        description=f'''Начисление за работу "{operation.title}" в заказе {order.id_label}''',
                                        income=income
                                    )
                                    list_to_add.append(payroll7)
                                    del income
                        # Если в самой операции нет особых правил начисления
                        else:
                            # print('Обычные правила начиления')
                            # Пройдем циклом по всем правилам начисления если таковые есть
                            if rules:
                                for rule in rules:
                                    # Если мы начисляем процент
                                    if rule.method == 0:
                                        # Пройдем по списку коэфициентов и цен и определим сумму начисления
                                        income = 0
                                        for row in rule.count_coeff:
                                            if row['cost'] <= operation.total:
                                                income = row['coef'] * operation.total / 100
                                        # Добавим начисление
                                        if income != 0:
                                            payroll8 = Payrolls(
                                                relation_type=4,  # 4 - за работу по статусу закрыт
                                                relation_id=operation.id,
                                                employee_id=operation.engineer_id,
                                                order_id=order.id,
                                                direction=2,  # 2 - приход
                                                description=f'''Начисление за работу "{operation.title}" в заказе {order.id_label}''',
                                                income=income
                                            )
                                            list_to_add.append(payroll8)
                                            del income
                                    else:
                                        # Пройдем по списку коэфициентов и цен и определим сумму начисления
                                        income = 0
                                        for row in rule.count_coeff:
                                            if row['cost'] <= operation.total:
                                                income = row['coef']
                                        # Добавим начисление
                                        if income != 0:
                                            payroll9 = Payrolls(
                                                relation_type=4,  # 4 - за работу по статусу закрыт
                                                relation_id=operation.id,
                                                employee_id=operation.engineer_id,
                                                order_id=order.id,
                                                direction=2,  # 2 - приход
                                                description=f'''Начисление за работу "{operation.title}" в заказе {order.id_label}''',
                                                income=income
                                            )
                                            list_to_add.append(payroll9)
                                            del income
        #  =====================================================================================================================

        # Списания при возврате статуса с Закрыт ===============================================================================

        # Если переход в группу Закрыт успешно с любой другой групы
        if new_status.group != 6 and current_status.group == 6:
            # Проверим существую ли операции по данном заказу
            if order.operations:
                # Пройдем циклом по всем операциям
                for operation in order.operations:
                    # проверим не удалена ли опарация
                    if not operation.deleted:
                        # Найдем все начисления по данной операции
                        query_payrolls = self.pgsql_connetction.session.query(Payrolls)
                        query_payrolls = query_payrolls.filter_by(direction=2)  # все которые с приходом
                        query_payrolls = query_payrolls.filter_by(deleted=False)  # Не удаленные
                        query_payrolls = query_payrolls.filter_by(reimburse=False)  # Не возмещенные
                        query_payrolls = query_payrolls.filter_by(relation_type=4)  # Начисленные за работу по статусу закрыт
                        query_payrolls = query_payrolls.filter_by(relation_id=operation.id)  # Принадлежащие данной операции
                        payrolls = query_payrolls.all()
                        # Если начисления имеются
                        if payrolls:
                            for payroll in payrolls:
                                if payroll.income != 0:
                                    payroll10 = Payrolls(
                                        relation_type=11,  # Возврат заказа
                                        relation_id=payroll.id,  # id начисления за которое делается возмещение
                                        employee_id=operation.engineer_id,
                                        order_id=order.id,
                                        direction=1,
                                        description=f'''Возврат за операцию "{operation.title}" в заказе {order.id_label}''',
                                        outcome=-payroll.income,
                                    )
                                    # Отметим операцию как возмещенную
                                    payroll.reimburse = True
                                    list_to_add.append(payroll)
                                    list_to_add.append(payroll10)

        # ======================================================================================================================

        # Предварительно сохраним результаты
        self.pgsql_connetction.session.add_all(list_to_add)
        self.pgsql_connetction.session.flush()

        self.pgsql_connetction.session.refresh(order)

        result = {'success': True}
        if r_filter and r_filter.get('update_order'):
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


        if r_filter:
            query = self.pgsql_connetction.session.query(Orders)

            if r_filter.get('created_at') is not None:
                query = query.filter(r_filter['created_at'][0] <= Orders.created_at)
                query = query.filter(Orders.created_at <= r_filter['created_at'][1])
            if r_filter.get('status_id') is not None:
                query = query.filter(Orders.status_id.in_(r_filter['status_id']))
            if r_filter.get('order_type_id') is not None:
                query = query.filter(Orders.order_type_id.in_(r_filter['order_type_id']))
            if r_filter.get('engineer_id') is not None:
                query = query.filter(Orders.engineer_id.in_(r_filter['engineer_id']))
            if r_filter.get('manager_id') is not None:
                query = query.filter(Orders.manager_id.in_(r_filter['manager_id']))
            if r_filter.get('kindof_good_id') is not None:
                query = query.filter(Orders.kindof_good_id == r_filter['kindof_good_id'])
            if r_filter.get('brand_id') is not None:
                query = query.filter(Orders.brand_id == r_filter['brand_id'])
            if r_filter.get('subtype_id') is not None:
                query = query.filter(Orders.subtype_id == r_filter['subtype_id'])
            if r_filter.get('client_id') is not None:
                query = query.filter(Orders.client_id == r_filter['client_id'])
            if r_filter.get('overdue') is not None:
                query = query.filter(Orders.estimated_done_at < time_now())
            if r_filter.get('status_overdue') is not None:
                query = query.filter(Orders.status_deadline < time_now())
            if r_filter.get('urgent') is not None:
                query = query.filter(Orders.urgent.is_(r_filter['urgent']))

            if r_filter.get('search'):
                query = query.join(Clients, Clients.id == Orders.client_id)
                query = query.join(Phones, Phones.client_id == Clients.id)
                query = query.join(EquipmentType, EquipmentType.id == Orders.kindof_good_id)
                query = query.join(EquipmentBrand, EquipmentBrand.id == Orders.brand_id)
                query = query.join(EquipmentSubtype, EquipmentSubtype.id == Orders.subtype_id)
                query = query.join(EquipmentModel, EquipmentModel.id == Orders.model_id)
                query = query.filter(or_(
                    Orders.id_label.ilike(f'%{r_filter["search"]}%'),
                    Orders.serial.ilike(f'%{r_filter["search"]}%'),
                    Clients.name.ilike(f'%{r_filter["search"]}%'),
                    Phones.number.ilike(f'%{r_filter["search"]}%'),
                    EquipmentType.title.ilike(f'%{r_filter["search"]}%'),
                    EquipmentBrand.title.ilike(f'%{r_filter["search"]}%'),
                    EquipmentSubtype.title.ilike(f'%{r_filter["search"]}%'),
                    EquipmentModel.title.ilike(f'%{r_filter["search"]}%')
                ))

            query = query.order_by(
                getattr(Orders, r_filter.get('field_sort'), 'id') if r_filter.get('sort') == 'asc' else desc(
                    getattr(Orders, r_filter.get('field_sort'), 'id')))

            count = query.count()
            result['count'] = count

            query = query.limit(50)
            if r_filter.get('page', 0): query = query.offset(r_filter['page'] * 50)

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

            result['data'] = data
            result['page'] = r_filter.get('field_sort', 0)

        if r_filter.get('update_badges'): result['badges'] = self.get_badges()['data']

        # Отправляем SMS при событиях сменты статуса
        event_change_status_to(self.pgsql_connetction.session, order, new_status, user_id)

        if r_filter and r_filter.get('update_order'):
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

            result['events'] = data_events

        self.pgsql_connetction.session.commit()
        return result, 202
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550
