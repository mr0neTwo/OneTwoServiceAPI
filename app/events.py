from datetime import datetime
import json
import requests
from num2words import num2words

def timestamp_to_string(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%d.%m.%y %H:%M')

def replace_template(db, order, template):

    company = db.get_generally_info()['data']
    client = order['client']
    data_employees = db.get_employee()['data']
    employees = {}
    for employee in data_employees:
        employees[employee['id']] = [f'{employee.get("first_name")} {employee.get("last_name")}', employee.get("phone")]

    requisites = f''' 
    ИНН {company.get('inn', '')}
    КПП {company.get('kpp', '')}
    БАНК {company.get('bank_name', '')}
    БИК {company.get('bic', '')}
    Р/С {company.get('settlement_account', '')}
    К/С {company.get('corr_account', '')}
    '''

    template = template.replace('#КОМПАНИЯ-НАЗВАНИЕ', company['name'] if company.get('name') else '')
    template = template.replace('#КОМПАНИЯ-АДРЕС', company['address'] if company.get('address') else '')
    template = template.replace('#КОМПАНИЯ-EMAIL', company['email'] if company.get('email') else '')
    template = template.replace('#КОМПАНИЯ-РЕКВИЗИТЫ', requisites)

    template = template.replace('#КЛИЕНТ-ИМЯ', client['name'] if client.get('name') else '')
    template = template.replace('#КЛИЕНТ-ТЕЛЕФОН', client['phone'][0]['number'] if client.get('phone') else None)
    template = template.replace('#КЛИЕНТ-АДРЕС', client['address'] if client.get('address') else '')
    template = template.replace('#КЛИЕНТ-EMAIL', client['email'] if client.get('email') else '')
    template = template.replace('#КЛИЕНТ-К/С', client['corr_account'] if client.get('corr_account') else '')
    template = template.replace('#КЛИЕНТ-Р/С', client['settlement_account'] if client.get('settlement_account') else '')
    template = template.replace('#КЛИЕНТ-ДИРЕКТОР', client['director'] if client.get('director') else '')
    template = template.replace('#КЛИЕНТ-БИК', client['bic'] if client.get('bic') else '')
    template = template.replace('#КЛИЕНТ-НАЗВАНИЕ-БАНКА', client['bank_name'] if client.get('bank_name') else '')
    template = template.replace('#КЛИЕНТ-ЮРИДИЧЕСКИЙ-АДРЕС', client['juridical_address'] if client.get('juridical_address') else '')
    template = template.replace('#КЛИЕНТ-КПП', client['kpp'] if client.get('kpp') else '')
    template = template.replace('#КЛИЕНТ-ИНН', client['inn'] if client.get('inn') else '')
    template = template.replace('#КЛИЕНТ-ОГРН', client['ogrn'] if client.get('ogrn') else '')
    template = template.replace('#КЛИЕНТ-ОБРАЩЕНИЕ', client['name_doc'] if client.get('name_doc') else '')

    template = template.replace('#ЗАКАЗ-НОМЕР', order['id_label'] if order.get('id_label') else '')
    template = template.replace('#ЦЕНА', str(order['price']) if order.get('price') else '')
    template = template.replace('#ЗАМЕТКИ-МЕНЕДЖЕРА', order['manager_notes'] if order.get('manager_notes') else '')
    template = template.replace('#ЗАМЕТКИ-ИСПОЛНИТЕЛЯ', order['engineer_notes'] if order.get('engineer_notes') else '')
    template = template.replace('#СРОЧНО', 'срочно' if order.get('urgent') else 'не срочно')
    template = template.replace('#ЗАКАЗ-НЕИСПРАВНОСТЬ', order['malfunction'] if order.get('malfunction') else '')
    template = template.replace('#ДАТА-ЗАКАЗ-БУДЕТ-ГОТОВ', timestamp_to_string(order['estimated_done_at']) if order.get('estimated_done_at') else '')
    template = template.replace('#ДАТА-ЗАКАЗ-ЗАПЛАНИРОВАН-НА', timestamp_to_string(order['scheduled_for']) if order.get('scheduled_for') else '')
    # template = template.replace('#ДАТА-ЗАКАЗ-ДЛИТЕЛЬНОСТЬ', timestamp_to_string(order['estimated_done_at']) if order.get('estimated_done_at') else ''))
    template = template.replace('#РЕКЛАМНАЯ-КАМПАНИЯ', order['ad_campaign']['name'] if order.get('ad_campaign') else '')
    template = template.replace('#ЗАКАЗ-ТИП-ИЗДЕЛИЯ', order['kindof_good']['title'] if order.get('kindof_good') else '')
    template = template.replace('#ЗАКАЗ-БРЕНД', order['brand']['title'] if order.get('brand') else '')
    template = template.replace('#ЗАКАЗ-МОДУЛЬ', order['subtype']['title'] if order.get('subtype') else '')
    template = template.replace('#ЗАКАЗ-МОДЕЛЬ', order['model']['title'] if order.get('model') else '')
    template = template.replace('#ЗАКАЗ-ВНЕШНИЙ-ВИД', order['appearance'] if order.get('appearance') else '')
    template = template.replace('#ЗАКАЗ-СЕРИЙНЫЙ-НОМЕР', order['serial'] if order.get('serial') else '')
    template = template.replace('#ЗАКАЗ-КОМПЛЕКТАЦИЯ', order['packagelist'] if order.get('packagelist') else '')

    template = template.replace('#ЗАКАЗ-СОЗДАЛ', employees[order['created_by_id']][0] if order.get('created_by_id') else '')
    # template = template.replace('#СЧЕТ-СОЗДАЛ', )
    template = template.replace('#ИСПОЛНИТЕЛЬ-ИМЯ', employees[order['engineer_id']][0] if order.get('engineer_id') else '')
    template = template.replace('#ИСПОЛНИТЕЛЬ-ТЕЛЕФОН', employees[order['engineer_id']][1] if order.get('engineer_id') else '')
    template = template.replace('#МЕНЕДЖЕР-ИМЯ', employees[order['manager_id']][0] if order.get('manager_id') else '')
    template = template.replace('#МЕНЕДЖЕР-ТЕЛЕФОН', employees[order['manager_id']][1] if order.get('manager_id') else '')
    template = template.replace('#ЗАКАЗ-ЗАКРЫЛ', employees[order['closed_by_id']][0] if order.get('closed_by_id') else '')

    # template = template.replace('#ВСЕГО-СУММА', order.get('price'))
    # template = template.replace('#СУММА-ПРОПИСЬЮ', order.get(''))
    # template = template.replace('#ВАЛЮТА', order.get(''))
    estimated_cost_word = num2words(int(order['estimated_cost']), lang='ru')
    template = template.replace('#ОРИЕНТИР-ЦЕНА', str(order['estimated_cost']) if order.get('estimated_cost') else '0')
    # template = template.replace('#ОРИЕНТИР-ЦЕНА-ПРОПИСЬЮ', estimated_cost_word if order.get('estimated_cost') else '0')
    template = template.replace('#К-ОПЛАТЕ', str(order['missed_payments']) if order.get('missed_payments') else '0')
    # template = template.replace('#К-ОПЛАТЕ-ПРОПИСЬЮ', num2words(int(order['missed_payments']), lang='ru') if order.get('missed_payments') else '0')
    template = template.replace('#ОПЛАЧЕНО', str(order['payed']) if order.get('payed') else '0')
    # template = template.replace('#ОПЛАЧЕНО-ПРОПИСЬЮ', num2words(int(order['payed']), lang='ru') if order.get('payed') else '0')
    template = template.replace('#ЗАКАЗ-СУММА', str(order['price']) if order.get('price') else '0')
    # template = template.replace('#ЗАКАЗ-СУММА-ПРОПИСЬЮ', num2words(int(order['price']), lang='ru') if order.get('price') else '0')

    template = template.replace('#ДАТА-СЕГОДНЯ', datetime.now().strftime('%d.%m.%y'))
    template = template.replace('#ДАТА-ВРЕМЯ-СЕГОДНЯ', datetime.now().strftime('%H:%M:%S'))
    # template = template.replace('#ДАТА-ПРОДАЖИ', order.get(''))
    # template = template.replace('#ДАТА-ВЫСТАВЛЕНИЯ-СЧЕТА', order.get(''))
    template = template.replace('#ДАТА-ЗАКАЗ-СОЗДАН', timestamp_to_string(order['created_at']) if order.get('created_at') else '')
    template = template.replace('#ДАТА-ЗАКАЗ-ГОТОВ', timestamp_to_string(order['done_at']) if order.get('done_at') else '')
    template = template.replace('#ДАТА-ЗАКАЗ-БУДЕТ-ГОТОВ', timestamp_to_string(order['estimated_done_at']) if order.get('estimated_done_at') else '')
    template = template.replace('#ДАТА-ЗАКАЗ-ЗАКРЫТ', timestamp_to_string(order['closed_at']) if order.get('closed_at') else '')
    template = template.replace('#ДАТА-ЗАКАЗ-ЗАПЛАНИРОВАН-НА', timestamp_to_string(order['scheduled_for']) if order.get('scheduled_for') else '')
    template = template.replace('#ДАТА-ГАРАНТИЯ', timestamp_to_string(order['warranty_date']) if order.get('warranty_date') else '')

    template = template.replace('#ЗАКАЗ-ТИП', order['order_type']['name'] if order.get('order_type') else '')
    # template = template.replace('#ЗАКАЗ-URL-ДЛЯ-ИСПОЛНИТЕЛЯ', order.get(''))
    # template = template.replace('#ЗАКАЗ-URL-ДЛЯ-КЛИЕНТА', order.get(''))
    # template = template.replace('#ЗАКАЗ-URL-ОТЗЫВ-КЛИЕНТА', order.get(''))
    # template = template.replace('#ЗАКАЗ-URL-ДЛЯ-ИСПОЛНИТЕЛЯ-SMS', order.get(''))
    # template = template.replace('#ЗАКАЗ-URL-ДЛЯ-КЛИЕНТА-SMS', order.get(''))
    # template = template.replace('#ПРОДАЖА-НОМЕР', order.get(''))
    # template = template.replace('#ФОРМА-ОПЛАТЫ', order.get(''))
    # template = template.replace('#СЧЕТ-НОМЕР', order.get(''))
    template = template.replace('#ВЕРДИКТ', order['resume'] if order.get('resume') else '')
    # template = template.replace('#КОММЕНТАРИЙ', order.get(''))
    # template = template.replace('#ШТРИХ-КОД', order.get(''))
    # template = template.replace('#КОММЕНТАРИЙ-АВТОР', order.get(''))
    template = template.replace('#ЛОКАЦИЯ', order['branch']['name'] if order.get('branch') else '')
    template = template.replace('#СТАТУС', order['status']['name'] if order.get('status') else '')

    return template

def send_sms(number, text):

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

    result = requests.post(url, data=json.dumps(body), headers=headers)

    print(f'send SMS to: {number} text: {text} status: {result.status_code}')
    # print(f'send SMS to: {number} text: {text} status: ок')


def event_change_status_to(db, order, new_status):

    # Достанем данные клиента
    client = order.get('client')
    # Отфильтруем телефоны на которые можно отправлять SMS
    phones = filter(lambda phone: phone['notify'], client['phone'])
    if phones:

        # Находим все события смены статуса на для уведомления клиентов
        events_change_to = db.get_notification_events(event='ORDER_STATUS_CHANGED_TO', target_audience=1)['data']

        # Пройдем цыклом по всем событиям данного типа
        for event in events_change_to:
            if new_status['id'] in event['statuses']:
                # Пройдем списком по телефонам
                for phone in phones:
                    # Извлекаем номер
                    number = phone['number']
                    # Создаем текст на основе шаблона
                    text = replace_template(db, order, event['template'])
                    # Отправляем СМС
                    send_sms(number, text)

        # Находим все события смены статуса для уведомления клиентов
        events_change_to = db.get_notification_events(event='ORDER_STATUS_CHANGED', target_audience=1)['data']

        # Пройдем цыклом по всем событиям данного типа
        for event in events_change_to:
                # Пройдем списком по телефонам
                for phone in phones:
                    # Извлекаем номер
                    number = phone['number']
                    # Создаем текст на основе шаблона
                    text = replace_template(db, order, event['template'])
                    # Отправляем СМС
                    send_sms(number, text)


def event_create_order(db, order):

    # Достанем данные клиента
    client = order.get('client')
    # Отфильтруем телефоны на которые можно отправлять SMS
    phones = filter(lambda phone: phone['notify'], client['phone'])
    if phones:

        # Находим все события смены статуса на для уведомления клиентов
        events_change_to = db.get_notification_events(event='ORDER_CREATED', target_audience=1)['data']

        # Пройдем цыклом по всем событиям данного типа
        for event in events_change_to:
            # Пройдем списком по телефонам
            for phone in phones:
                # Извлекаем номер
                number = phone['number']
                # Создаем текст на основе шаблона
                text = replace_template(db, order, event['template'])
                # Отправляем СМС
                send_sms(number, text)
