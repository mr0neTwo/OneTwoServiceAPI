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
            result['order'], result['events'] = self.get_order_by_id(order.id)

        if r_filter:
            result['data'] = self.get_orders_by_filter(r_filter)
            result['page'] = r_filter.get('page', 0)

        if r_filter.get('update_badges'):
            result['badges'] = self.get_badges()['data']

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
