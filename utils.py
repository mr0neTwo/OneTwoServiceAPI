import traceback
from datetime import datetime
from pprint import pprint

import requests
from telebot import TeleBot
from tqdm import tqdm

def config_parser(config_path):
    with open(config_path, 'r') as config_file:
        config = dict()
        lines = config_file.readlines()
        for line in lines:
            key, value = line.split(' = ')
            config[key] = value.split('\n')[0]
        return config



# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++



# list_name = ['Стас', 'Антон', 'Юра', 'Альбиночка']
# list_telegram_id = [442971377, 633363605, 857858976, 315479668]

def bot_send_message(employee_id, text):
    # Создаем токен для бота
    token = "1729021750:AAHObATFNa1uO0cyFrWZezNSG8YMBugNhjE"
    dict_id = {
        1: 442971377,
        2: 633363605,
        4: 857858976,
        7: 315479668
    }
    # Подключаемся к боту
    bot = TeleBot(token)
    bot.send_message(dict_id[employee_id], text)




my_api_key = "94ee4e09d9e247edaeab77e7ac63f368"

def GetListRO(value_request):
    '''
    API запрос на сервер РемонтОнлайн
        :param value_request: параметр запроса
        :return: list dictionares
        status - Запрос списка статусов заказа
        empoyees - Запрос списка сотрудниов
        oder_custom_fields -  Запрос списка пользовательских полей заказа
        client_custom_fields' - Запрос списка пользовательских полей клиента
        margins - Запрос списка наценок
        branches - Запрос списка филиалов
        service-operations - Запрос списка улуг
        dictionaries -  Запрос списка словарей
        arehouse_categories - Запрос списка категорий склада
        warehouse - Запрос списка складов
        cashbox - Запрос списка касс
    '''
    # Мой ключ для доступо к API
    api_key = my_api_key

    # Запрос и формирование token
    data_key = {'api_key': api_key}
    result = requests.post('https://api.remonline.ru/token/new', data = data_key).json()
    token = result['token']

    # Параметры запроса
    param = {'token': token}

    patchesRO = {
        'status': 'https://api.remonline.ru/statuses/',                                 # Запрос списка статусов заказа
        'empoyees': 'https://api.remonline.ru/employees/',                              # Запрос списка сотрудниов
        'oder_custom_fields': 'https://api.remonline.ru/order/custom-fields/',          # Запрос списка пользовательских полей заказа
        'client_custom_fields': 'https://api.remonline.ru/clients/custom-fields/',      # Запрос списка пользовательских полей клиента
        'margins': 'https://api.remonline.ru/margins/',                                 # Запрос списка наценок
        'branches': 'https://api.remonline.ru/branches/',                               # Запрос списка филиалов
        'service-operations': 'https://api.remonline.ru/books/service-operations/',     # Запрос списка улуг
        'dictionaries': 'https://api.remonline.ru/book/list/',                          # Запрос списка словарей
        'arehouse_categories': 'https://api.remonline.ru/warehouse/categories/',        # Запрос списка категорий склада
        'warehouse': 'https://api.remonline.ru/warehouse/',                             # Запрос списка складов
        'cashbox': 'https://api.remonline.ru/cashbox/',                                 # Запрос списка касс
        'type_oders': 'https://api.remonline.ru/order/types/',                          # Запрос списка типов заказов
    }

    # Делаем запрос
    result_service = requests.get(patchesRO[value_request], params=param).json()

    # Возвращаем результат
    return result_service['data']



# Список клиентов
def GetCustomer(page = 'all',
                names = None,
                phones = None,
                emails = None,
                addresses = None,
                discount_codes = None,
                modified_at = None,
                created_at = None,
                ad_campaigns = None,
                juridical = None,
                conflicted = None,
                supplier = None):
    '''
    Возвращает словарь с данными клиенов с сврвера РемОнлайн
        :param page: int - Количесто страниц
        :param names: array - Фильтр по имени клиента. Учитывать клиентов у которых переданный параметр содержится в значении name клиента
        :param phones: array - Фильтр по телефону клиента. Учитывать клиентов у которы переданный параметр содержится в значении phone клиента
        :param emails: array - Фильтр по email клиента. Учитывать клиентов у которых переданный параметр содержится в значении email клиента
        :param addresses: array - Фильтр по адресу клиента. Учитывать клиентов у которых переданный параметр содержится в значении adress клиента;
        :param discount_codes: array - Фильтр по скидочным картам;
        :param modified_at: array - Фильтр по дате изменения сущности клиента. Массив из одного либо двух значений, которые содержат в себе timestamp. В случае, если массив состоит из одного значения, то оно является левой границей. Примеры: [1454277600000, 1456783200000], [1454277500000];
        :param created_at: array - Фильтр по дате создания клиента. Массив из одного либо двух значений, которые содержат в себе timestamp.В случае, если массив состоит из одного значения, то оно является левой границей. Примеры: [1454277600000, 1456783200000], [1454277500000];
        :param ad_campaigns: array - Массив идентификаторов источников откуда клиент узнал о нас;
        :param juridical: bool -  Вернуть только юридические лица, если правда, и только физические лица, если ложь;
        :param conflicted: bool - Вернуть конфликтных клиентов, если правда, и только не конфликтных, если ложь;
        :param supplier: bool - Вернуть клиентов являющихся поставщиками, если правда, и только обычных, если ложь;
        :return: Список словарей с данными клиентов
    '''
    # Мой ключ для доступо к API
    api_key = '94ee4e09d9e247edaeab77e7ac63f368'

    # Запрос и формирование token
    data_key = {'api_key': api_key}
    result = requests.post('https://api.remonline.ru/token/new', data = data_key).json()
    token = result['token']
    # print('Connection success: {}'.format(result['success']))

    # Параметры запроса
    param = {'token': token,
             'page': page,
             'names[]': names,
             'phones[]': phones,
             'emails[]': emails,
             'addresses[]': addresses,
             'discount_codes[]': discount_codes,
             'modified_at[]': modified_at,
             'created_at[]': created_at,
             'ad_campaigns[]': ad_campaigns,
             'juridical': juridical,
             'conflicted': conflicted,
             'supplier': supplier}

    # Делаем первый запрос, чтобы узнать количество страниц ответа
    if page == 'all':
        param['page'] = 1
        result_customer = requests.get('https://api.remonline.ru/clients/', params = param).json()
        page = result_customer['count'] // 50 + 1 if result_customer['count'] % 50 > 0 else result_customer['count'] // 50
        # print('Найдено {} клиентов на {} страницах'.format(result_customer['count'], page))

        # Создадим список для словарей клиентов
        list_dict = []

        # Перебираем циклом страницы
        for N in tqdm(range(1, page + 1), position = 0, desc = f"Найдено {result_customer['count']} клиентов. Загрузка"):
            # Задаем количество страниц
            param['page'] = N

            # Отправляем запрос на сервер
            result_customer = requests.get('https://api.remonline.ru/clients/', params = param).json()

            # Занесем каждое значение в список
            for dict_custom in result_customer['data']:
                list_dict.append(dict_custom)

        # Возвращаем список
        return list_dict
    else:
        # Создадим список для словарей клиентов
        list_dict = []

        # Отправляем запрос на сервер
        result_customer = requests.get('https://api.remonline.ru/clients/', params=param).json()

        # Занесем каждое значение в список
        for dict_custom in result_customer['data']:
            list_dict.append(dict_custom)

        # Возвращаем список
        return list_dict


# Список заказов
def GetOders():

    # Запрос и формирование token
    data_key = {'api_key': "94ee4e09d9e247edaeab77e7ac63f368"}
    result = requests.post('https://api.remonline.ru/token/new', data = data_key).json()
    token = result['token']

    # Параметры запроса
    param = {'token': token,
             'page': 1}


    # Делаем первый запрос, чтобы узнать количество страниц ответа
    param['page'] = 1
    result_oders = requests.get('https://api.remonline.ru/order/', params = param).json()
    page = result_oders['count'] // 50 + 1 if result_oders['count'] % 50 > 0 else result_oders['count'] // 50

    # Создадим список для словарей заказов
    list_dict = []

    # Перебираем циклом страницы
    for N in tqdm(range(1, page + 1), position = 0, desc = f"Найдено {result_oders['count']} заказов. Загрузка"):
        # Задаем номер страницы
        param['page'] = N

        # Отправляем запрос на сервер
        result_oders = requests.get('https://api.remonline.ru/order/', params = param).json()

        # Занесем каждое значение в список
        for dict_oders in result_oders['data']:
            list_dict.append(dict_oders)

    # Возвращаем список
    return list_dict

# Список операций по кассе
def GetCashTransaction(cashName,
                       page = 'all',
                       sort_dir = 'asc',
                       created_at = None):
    '''
    Возвращает список операций по кассе
    :param cashName: - str - Имя кассы()
    :param page: - int - Количество страниц
    :param sort_dir: asc|desc - Направление сортировки заказов
    :param created_at: array - Фильтр по дате создания. Массив из одного либо двух значений, которые содержат в себе timestamp. В случае, если массив состоит из одного значения, то оно является левой границей. Примеры: [0, 1454277600000], [1454277500000];
    :return: Список словарей касс
    '''
    # Мой ключ для доступо к API
    api_key = "94ee4e09d9e247edaeab77e7ac63f368"

    # Запрос и формирование token
    data_key = {'api_key': api_key}
    result = requests.post('https://api.remonline.ru/token/new', data = data_key).json()
    token = result['token']
    # print('Connection success: {}'.format(result['success']))

    # Параметры запроса
    param = {'token': token,
             'sort_dir': sort_dir,
             'created_at[]': created_at}

    # Создаем словарь id касс
    cashNames = {'Сбербанк': 83913,
                'Альфа Банк': 48530,
                'Сейф': 53830,
                'Касса': 48492,
                'Федеральный резерв': 48531,
                'Обустройство': 48555}

    # Делаем первый запрос, чтобы узнать количество страниц ответа
    if page == 'all':
        param['page'] = 1
        result_cash = requests.get('https://api.remonline.ru/cashbox/report/{}'.format(cashNames[cashName]),
                                   params=param).json()

        page = result_cash['count'] // 50 + 1 if result_cash['count'] % 50 > 0 else result_cash['count'] // 50
        # print('Найдено {} транзакций на {} страницах'.format(result_cash['count'], page))

    # Создадим список для словарей транзакций
    list_dict = []

    # Перебираем циклом страницы
    for N in tqdm(range(1, page + 1), position = 0, desc = f" Найдено {0} транзакций. Закгрузка"):
        # Задаем номер страницы
        param['page'] = N

        # Создаем запрос на сервер
        result_cash = requests.get('https://api.remonline.ru/cashbox/report/{}'.format(cashNames[cashName]),
                                   params = param).json()

        # Занесем каждое значение в список
        for dict_cash in result_cash['data']:
            list_dict.append(dict_cash)

    # Возвращаем список
    return list_dict


def error550(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            print(traceback.format_exc())
            return {'success': False, 'message': 'server error'}, 550
    return wrapper



# payments = GetCashTransaction('Альфа Банк', page=1)
# pprint(payments)
#
# clients = GetCustomer(page='all')
# pprint(clients)


# send_sms("79002888475", "Братюня!")