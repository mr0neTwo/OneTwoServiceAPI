import os
from datetime import datetime
import json
import requests
from num2words import num2words

from app.db.models.models import NotificationEvents, GenerallyInfo, Employees, Events


def timestamp_to_string(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%d.%m.%y %H:%M')

def replace_template(session, order, template):

    company = session.query(GenerallyInfo).first()
    client = order.client
    data_employees = session.query(Employees).all()
    employees = {}
    for employee in data_employees:
        employees[employee.id] = [f'{employee.last_name} {employee.first_name}', employee.phone]

    requisites = f''' 
    ИНН {company.inn or ''}
    КПП {company.kpp or ''}
    БАНК {company.bank_name or ''}
    БИК {company.bic or ''}
    Р/С {company.settlement_account or ''}
    К/С {company.corr_account or ''}
    '''
    template = template.replace('#КОМПАНИЯ-НАЗВАНИЕ', company.name or '')
    template = template.replace('#КОМПАНИЯ-АДРЕС', company.address or '')
    template = template.replace('#КОМПАНИЯ-EMAIL', company.email or '')
    template = template.replace('#КОМПАНИЯ-РЕКВИЗИТЫ', requisites)

    template = template.replace('#КЛИЕНТ-ИМЯ', client.name or '')
    template = template.replace('#КЛИЕНТ-ТЕЛЕФОН', client.phone[0].number or '')
    template = template.replace('#КЛИЕНТ-АДРЕС', client.address or '')
    template = template.replace('#КЛИЕНТ-EMAIL', client.email or '')
    template = template.replace('#КЛИЕНТ-К/С', client.corr_account or '')
    template = template.replace('#КЛИЕНТ-Р/С', client.settlement_account or '')
    template = template.replace('#КЛИЕНТ-ДИРЕКТОР', client.director or '')
    template = template.replace('#КЛИЕНТ-БИК', client.bic or '')
    template = template.replace('#КЛИЕНТ-НАЗВАНИЕ-БАНКА', client.bank_name or '')
    template = template.replace('#КЛИЕНТ-ЮРИДИЧЕСКИЙ-АДРЕС', client.juridical_address or '')
    template = template.replace('#КЛИЕНТ-КПП', client.kpp or '')
    template = template.replace('#КЛИЕНТ-ИНН', client.inn or '')
    template = template.replace('#КЛИЕНТ-ОГРН', client.ogrn or '')
    template = template.replace('#КЛИЕНТ-ОБРАЩЕНИЕ', client.name_doc or '')

    template = template.replace('#ЗАКАЗ-НОМЕР', str(order.id_label) or '')
    template = template.replace('#ЦЕНА', str(order.price) or '')
    template = template.replace('#ЗАМЕТКИ-МЕНЕДЖЕРА', order.manager_notes or '')
    template = template.replace('#ЗАМЕТКИ-ИСПОЛНИТЕЛЯ', order.engineer_notes or '')
    template = template.replace('#СРОЧНО', 'срочно' if order.urgent else 'не срочно')
    template = template.replace('#ЗАКАЗ-НЕИСПРАВНОСТЬ', order.malfunction or '')
    template = template.replace('#ДАТА-ЗАКАЗ-БУДЕТ-ГОТОВ', timestamp_to_string(order.estimated_done_at) if order.estimated_done_at else '')
    template = template.replace('#ДАТА-ЗАКАЗ-ЗАПЛАНИРОВАН-НА', timestamp_to_string(order.scheduled_for) if order.scheduled_for else '')
    # template = template.replace('#ДАТА-ЗАКАЗ-ДЛИТЕЛЬНОСТЬ', timestamp_to_string(order['estimated_done_at']) if order.get('estimated_done_at') else ''))
    template = template.replace('#РЕКЛАМНАЯ-КАМПАНИЯ', order.ad_campaign.name  if order.ad_campaign else '')
    template = template.replace('#ЗАКАЗ-ТИП-ИЗДЕЛИЯ', order.kindof_good.title if order.kindof_good else '')
    template = template.replace('#ЗАКАЗ-БРЕНД', order.brand.title if order.brand else '')
    template = template.replace('#ЗАКАЗ-МОДУЛЬ', order.subtype.title if order.subtype else '')
    template = template.replace('#ЗАКАЗ-МОДЕЛЬ', order.model.title if order.model else '')
    template = template.replace('#ЗАКАЗ-ВНЕШНИЙ-ВИД', order.appearance or '')
    template = template.replace('#ЗАКАЗ-СЕРИЙНЫЙ-НОМЕР', order.serial or '')
    template = template.replace('#ЗАКАЗ-КОМПЛЕКТАЦИЯ', order.packagelist or '')

    template = template.replace('#ЗАКАЗ-СОЗДАЛ', employees[order.created_by_id][0] if order.created_by_id else '')
    # template = template.replace('#СЧЕТ-СОЗДАЛ', )
    template = template.replace('#ИСПОЛНИТЕЛЬ-ИМЯ', employees[order.engineer_id][0] if order.engineer_id else '')
    template = template.replace('#ИСПОЛНИТЕЛЬ-ТЕЛЕФОН', employees[order.engineer_id][1] if order.engineer_id else '')
    template = template.replace('#МЕНЕДЖЕР-ИМЯ', employees[order.manager_id][0] if order.manager_id else '')
    template = template.replace('#МЕНЕДЖЕР-ТЕЛЕФОН', employees[order.manager_id][1] if order.manager_id else '')
    template = template.replace('#ЗАКАЗ-ЗАКРЫЛ', employees[order.closed_by_id][0] if order.closed_by_id else '')

    # template = template.replace('#ВСЕГО-СУММА', order.get('price'))
    # template = template.replace('#СУММА-ПРОПИСЬЮ', order.get(''))
    # template = template.replace('#ВАЛЮТА', order.get(''))
    # estimated_cost_word = num2words(int(order['estimated_cost']), lang='ru')
    template = template.replace('#ОРИЕНТИР-ЦЕНА', str(order.estimated_cost) if order.estimated_cost else '0')
    # template = template.replace('#ОРИЕНТИР-ЦЕНА-ПРОПИСЬЮ', estimated_cost_word if order.get('estimated_cost') else '0')
    template = template.replace('#К-ОПЛАТЕ', str(order.missed_payments) if order.missed_payments else '0')
    # template = template.replace('#К-ОПЛАТЕ-ПРОПИСЬЮ', num2words(int(order['missed_payments']), lang='ru') if order.get('missed_payments') else '0')
    template = template.replace('#ОПЛАЧЕНО', str(order.payed) if order.payed else '0')
    # template = template.replace('#ОПЛАЧЕНО-ПРОПИСЬЮ', num2words(int(order['payed']), lang='ru') if order.get('payed') else '0')
    template = template.replace('#ЗАКАЗ-СУММА', str(order.price) if order.price else '0')
    # template = template.replace('#ЗАКАЗ-СУММА-ПРОПИСЬЮ', num2words(int(order['price']), lang='ru') if order.get('price') else '0')

    template = template.replace('#ДАТА-СЕГОДНЯ', datetime.now().strftime('%d.%m.%y'))
    template = template.replace('#ДАТА-ВРЕМЯ-СЕГОДНЯ', datetime.now().strftime('%H:%M:%S'))
    # template = template.replace('#ДАТА-ПРОДАЖИ', order.get(''))
    # template = template.replace('#ДАТА-ВЫСТАВЛЕНИЯ-СЧЕТА', order.get(''))
    template = template.replace('#ДАТА-ЗАКАЗ-СОЗДАН', timestamp_to_string(order.created_at) if order.created_at else '')
    template = template.replace('#ДАТА-ЗАКАЗ-ГОТОВ', timestamp_to_string(order.done_at) if order.done_at else '')
    template = template.replace('#ДАТА-ЗАКАЗ-БУДЕТ-ГОТОВ', timestamp_to_string(order.estimated_done_at) if order.estimated_done_at else '')
    template = template.replace('#ДАТА-ЗАКАЗ-ЗАКРЫТ', timestamp_to_string(order.closed_at) if order.closed_at else '')
    template = template.replace('#ДАТА-ЗАКАЗ-ЗАПЛАНИРОВАН-НА', timestamp_to_string(order.scheduled_for) if order.scheduled_for else '')
    template = template.replace('#ДАТА-ГАРАНТИЯ', timestamp_to_string(order.warranty_date) if order.warranty_date else '')

    template = template.replace('#ЗАКАЗ-ТИП', order.order_type.name if order.order_type else '')
    # template = template.replace('#ЗАКАЗ-URL-ДЛЯ-ИСПОЛНИТЕЛЯ', order.get(''))
    # template = template.replace('#ЗАКАЗ-URL-ДЛЯ-КЛИЕНТА', order.get(''))
    # template = template.replace('#ЗАКАЗ-URL-ОТЗЫВ-КЛИЕНТА', order.get(''))
    # template = template.replace('#ЗАКАЗ-URL-ДЛЯ-ИСПОЛНИТЕЛЯ-SMS', order.get(''))
    # template = template.replace('#ЗАКАЗ-URL-ДЛЯ-КЛИЕНТА-SMS', order.get(''))
    # template = template.replace('#ПРОДАЖА-НОМЕР', order.get(''))
    # template = template.replace('#ФОРМА-ОПЛАТЫ', order.get(''))
    # template = template.replace('#СЧЕТ-НОМЕР', order.get(''))
    template = template.replace('#ВЕРДИКТ', order.resume or '')
    # template = template.replace('#КОММЕНТАРИЙ', order.get(''))
    # template = template.replace('#ШТРИХ-КОД', order.get(''))
    # template = template.replace('#КОММЕНТАРИЙ-АВТОР', order.get(''))
    template = template.replace('#ЛОКАЦИЯ', order.branch.name if order.branch else '')
    template = template.replace('#СТАТУС', order.status.name if order.status else '')

    return template

def send_sms(session, number, text, order, user_id):

    url = 'https://onetwoonline.moizvonki.ru/api/v1'
    headers = {
        "Content-Type": "application/json"
    }
    body = {
        "user_name": "stasmen66@gmail.com",
        "api_key": "1zww7we8zoq53rm32cmewjnjx683asms",
        "action": "calls.send_sms",
        "to": str(number),
        "text": text
    }
    # Добавим событие отправки сообщения
    order_event = Events(
        object_type=1,  # Заказ
        object_id=order.id,
        event_type='SEND_SMS',
        current_status_id=order.status_id,
        branch_id=order.branch_id,
        employee_id=user_id,
        changed=[{
            'title': 'Отправлено SMS',
            'new': {'title': text}
        }]
    )
    session.add(order_event)
    session.flush()

    if os.environ['SEND_SMS']:
        result = requests.post(url, data=json.dumps(body), headers=headers)
        print(f'send SMS to: {number} text: {text} status: {result.status_code}')
    else:
        print(f'send SMS to: {number} text: {text} status: ок')


def event_change_status_to(session, order, new_status, user_id):

    # Достанем данные клиента
    client = order.client
    # Отфильтруем телефоны на которые можно отправлять SMS
    phones = filter(lambda phone: phone.notify, client.phone)
    if phones:

        # Находим все события смены статуса на для уведомления клиентов
        query = session.query(NotificationEvents)
        query = query.filter_by(event='ORDER_STATUS_CHANGED_TO', target_audience=1)
        events_change_to = query.all()

        # Пройдем цыклом по всем событиям данного типа
        for event in events_change_to:
            if new_status.id in event.statuses:
                # Пройдем списком по телефонам
                for phone in phones:
                    # Извлекаем номер
                    number = phone.number
                    # Создаем текст на основе шаблона
                    text = replace_template(session, order, event.template.template)
                    # Отправляем СМС
                    send_sms(session, number, text, order, user_id)

        # Находим все события смены статуса для уведомления клиентов
        query = session.query(NotificationEvents)
        query = query.filter_by(event='ORDER_STATUS_CHANGED', target_audience=1)
        events_change_to = query.all()

        # Пройдем цыклом по всем событиям данного типа
        for event in events_change_to:
                # Пройдем списком по телефонам
                for phone in phones:
                    # Извлекаем номер
                    number = phone.number
                    # Создаем текст на основе шаблона
                    text = replace_template(session, order, event.template)
                    # Отправляем СМС
                    send_sms(session, number, text, order, user_id)


def event_create_order(session, order, user_id):
    # Достанем данные клиента
    client = order.client
    # Отфильтруем телефоны на которые можно отправлять SMS
    phones = filter(lambda phone: phone.notify, client.phone)
    if phones:

        # Находим все события смены статуса на для уведомления клиентов
        query = session.query(NotificationEvents)
        query = query.filter_by(event='ORDER_CREATED', target_audience=1)
        events_change_to = query.all()

        # Пройдем цыклом по всем событиям данного типа
        for event in events_change_to:
            # Пройдем списком по телефонам
            for phone in phones:
                # Извлекаем номер
                number = phone.number
                # Создаем текст на основе шаблона
                text = replace_template(session, order, event.template.template)
                # Отправляем СМС
                send_sms(session, number, text, order, user_id)
