import operator
import random
from pprint import pprint

import pytest
import requests

from data import equipment_type, equipment_brand, equipment_subtype, equipment_model

equipment_types = [{
    'id': x + 1,
    'title': random.choice(equipment_type),
    'icon': f'{random.choice(equipment_type)}.jpeg',
    'url': f'data/IMG_TYPE/type{x + 1}.jpeg',
    'branches': [x for x in range(1, random.randint(1, 4))],
    'deleted': False
} for x in range(10)]
equipment_brands = [{
    'id': x + 1,
    'title': random.choice(equipment_brand),
    'icon': f'{random.choice(equipment_brand)}.jpeg',
    'url': f'data/IMG_TYPE/brand{x + 1}.jpeg',
    'branches': [x for x in range(1, random.randint(1, 4))],
    'deleted': False,
    'equipment_type_id': random.randint(1, 10)
} for x in range(20)]
equipment_subtypes = [{
    'id': x + 1,
    'title': random.choice(equipment_subtype),
    'icon': f'{random.choice(equipment_subtype)}.jpeg',
    'url': f'data/IMG_TYPE/brand{x + 1}.jpeg',
    'branches': [x for x in range(1, random.randint(1, 4))],
    'deleted': False,
    'equipment_brand_id': random.randint(1, 20)
} for x in range(30)]
equipment_models = [{
    'id': x + 1,
    'title': random.choice(equipment_model),
    'icon': f'{random.choice(equipment_model)}.jpeg',
    'url': f'data/IMG_TYPE/brand{x + 1}.jpeg',
    'branches': [x for x in range(1, random.randint(1, 4))],
    'deleted': False,
    'equipment_subtype_id': random.randint(1, 30)
} for x in range(40)]
type_filters = [{
    'title': random.choice(equipment_type)[:random.randint(0, 4)].lower(),
    'deleted': bool(random.randint(0, 1))
} for x in range(10)] + [False, False, False, False]
brand_filters = [{
    'title': random.choice(equipment_brand)[:random.randint(0, 4)].lower(),
    'deleted': bool(random.randint(0, 1)),
    'equipment_type_id': random.randint(1, 10)
} for x in range(10)] + [False, False, False, False]
subtype_filters = [{
    'title': random.choice(equipment_subtype)[:random.randint(0, 4)].lower(),
    'deleted': bool(random.randint(0, 1)),
    'equipment_brand_id': random.randint(1, 10)
} for x in range(10)] + [False, False, False, False]
model_filters = [{
    'title': random.choice(equipment_model)[:random.randint(0, 4)].lower(),
    'deleted': bool(random.randint(0, 1)),
    'equipment_subtype_id': random.randint(1, 10)
} for x in range(10)] + [False, False, False, False]
etype_for_edit = [
    {
        'id': random.randint(1, 10),
        'title': random.choice(equipment_type)
    }, {
        'id': random.randint(1, 10),
        'title': random.choice(equipment_type)
    }, {
        'id': random.randint(1, 10),
        'branches': [x for x in range(1, random.randint(1, 4))],
    }, {
        'id': random.randint(1, 10),
        'branches': [x for x in range(1, random.randint(1, 4))],
    }, {
        'id': random.randint(1, 10),
        'icon': 'new_icon.svg',
        'url': 'data/PCB/new_img.jpeg'
    }, {
        'id': 5,
        'deleted': True
    }, {
        'id': random.randint(1, 10),
        'deleted': True
    }, {
        'id': 5,
        'deleted': False
    }
]
ebrand_for_edit = [
    {
        'id': random.randint(1, 20),
        'title': random.choice(equipment_brand)
    }, {
        'id': random.randint(1, 20),
        'title': random.choice(equipment_brand)
    }, {
        'id': random.randint(1, 20),
        'branches': [x for x in range(1, random.randint(1, 4))],
    }, {
        'id': random.randint(1, 20),
        'branches': [x for x in range(1, random.randint(1, 4))],
    }, {
        'id': random.randint(1, 20),
        'icon': 'new_icon.svg',
        'url': 'data/PCB/new_img.jpeg'
    }, {
        'id': 5,
        'deleted': True
    }, {
        'id': random.randint(1, 20),
        'deleted': True
    }, {
        'id': 5,
        'deleted': False
    }, {
        'id': random.randint(1, 20),
        'equipment_type_id': random.randint(1, 10)
    }, {
        'id': random.randint(1, 20),
        'equipment_type_id': random.randint(1, 10)
    }
]
esubtype_for_edit = [
    {
        'id': random.randint(1, 30),
        'title': random.choice(equipment_subtype)
    }, {
        'id': random.randint(1, 30),
        'title': random.choice(equipment_subtype)
    }, {
        'id': random.randint(1, 30),
        'branches': [x for x in range(1, random.randint(1, 4))],
    }, {
        'id': random.randint(1, 30),
        'branches': [x for x in range(1, random.randint(1, 4))],
    }, {
        'id': random.randint(1, 30),
        'icon': 'new_icon.svg',
        'url': 'data/PCB/new_img.jpeg'
    }, {
        'id': 5,
        'deleted': True
    }, {
        'id': random.randint(1, 30),
        'deleted': True
    }, {
        'id': 5,
        'deleted': False
    }, {
        'id': random.randint(1, 30),
        'equipment_brand_id': random.randint(1, 20)
    }, {
        'id': random.randint(1, 30),
        'equipment_brand_id': random.randint(1, 20)
    }
]
emodel_for_edit = [
    {
        'id': random.randint(1, 40),
        'title': random.choice(equipment_model)
    }, {
        'id': random.randint(1, 40),
        'title': random.choice(equipment_model)
    }, {
        'id': random.randint(1, 40),
        'branches': [x for x in range(1, random.randint(1, 4))],
    }, {
        'id': random.randint(1, 40),
        'branches': [x for x in range(1, random.randint(1, 4))],
    }, {
        'id': random.randint(1, 30),
        'icon': 'new_icon.svg',
        'url': 'data/PCB/new_img.jpeg'
    }, {
        'id': 5,
        'deleted': True
    }, {
        'id': random.randint(1, 40),
        'deleted': True
    }, {
        'id': 5,
        'deleted': False
    }, {
        'id': random.randint(1, 40),
        'equipment_subtype_id': random.randint(1, 30)
    }, {
        'id': random.randint(1, 40),
        'equipment_subtype_id': random.randint(1, 30)
    }
]


# Функция для фильтрации тестовых данных
def filter_equipment(list_equipments, title=None, deleted=None, parents_id=None, field_parents=None):
    if title:
        list_equipments = list(filter(lambda e: title.lower() in e['title'].lower(), list_equipments))
    if deleted is not None:
        list_equipments = list(filter(lambda e: deleted or e['deleted'] is deleted, list_equipments))
    if parents_id:
        list_equipments = list(filter(lambda e: e[field_parents] == parents_id, list_equipments))
    return sorted(list_equipments, key=lambda e: e['title'].lower())


@pytest.mark.parametrize('equipment_type', equipment_types)
def test_create_equipment_types(server_url, headers, equipment_type):
    # Выбираем случайный фильтр
    r_filter = random.choice(type_filters)

    # Добавляем фильтр в запрос
    equipment_type['filter'] = r_filter

    # Делаем тестовый запрос на создание Типа техники в БД
    result = requests.post(server_url + 'equipment_type', json=equipment_type, headers=headers).json()

    #  Удаляем фильтер из данных для последующего сравнения
    del equipment_type['filter']

    # Если фильтр имел тело
    if r_filter:

        # Отсортируем данные одинаково (иначе тесты сыпятся)
        result['data'] = filter_equipment(result['data'])

        # Фильтруем тестовые данные, как бы отфильтровал обработчик запроса к БД
        e_types = filter_equipment(
            equipment_types[:equipment_type['id']],
            title=r_filter.get('title'),
            deleted=r_filter.get('deleted')
        )
        # Сравниваем ответ
        assert result == {
            'success': True,
            'count': len(e_types),
            'page': 0,
            'data': e_types
        }
    # Если фильтр без тела
    else:
        # Сравниваем ответ
        assert result == {
            'success': True,
            'data': equipment_type,
            'message': f'{equipment_type["id"]} added'
        }


@pytest.mark.parametrize('data', etype_for_edit)
def test_edit_equipment_types(server_url, headers, data):
    # Выбираем случайный фильтр
    r_filter = random.choice(type_filters)

    # Добавляем фильтр в запрос
    data['filter'] = r_filter

    # Делаем запрос на изменение Типа техники в БД
    result = requests.put(server_url + 'equipment_type', json=data, headers=headers).json()

    #  Удаляем фильтер из данных для последующего сравнения
    del data['filter']

    # Обновляем тестовые данные, как бы это сделал обработчик запроса в БД
    equipment_types[data['id'] - 1].update(data)

    # Если фильтр содержит тело
    if r_filter:

        # Отсортируем данные одинаково (иначе тесты сыпятся)
        result['data'] = filter_equipment(result['data'])

        # Фильтруем тестовые данные, как бы отфильтровал обработчик запроса к БД
        equipment_type = filter_equipment(
            equipment_types,
            title=r_filter.get('title'),
            deleted=r_filter.get('deleted')
        )
        # Сравниваем данные
        assert result == {
            'success': True,
            'count': len(equipment_type),
            'page': 0,
            'data': equipment_type
        }
    # Если фильтр не содержит тело
    else:
        # Сравниваем данные
        assert result == {'success': True, 'message': f'{data["id"]} changed'}


@pytest.mark.parametrize('r_filter', type_filters)
def test_get_equipment_types(server_url, headers, r_filter):
    # Если фильтр содержит тело, истользуем его, если нет отправляем пустой объект
    r_filter = r_filter if r_filter else {}

    # Делаем запрос на изменение Типа техники в БД
    result = requests.post(server_url + 'get_equipment_type', json=r_filter, headers=headers).json()

    # Отсортируем данные одинаково (иначе тесты сыпятся)
    result['data'] = filter_equipment(result['data'])

    # Фильтруем тестовые данные, как бы отфильтровал обработчик запроса к БД
    equipment_type = filter_equipment(
        equipment_types,
        title=r_filter.get('title'),
        deleted=r_filter.get('deleted')
    )

    # Сравниваем данные
    assert result == {
        'success': True,
        'count': len(equipment_type),
        'page': 0,
        'data': equipment_type
    }


@pytest.mark.parametrize('brand', equipment_brands)
def test_create_equipment_brand(server_url, headers, brand):
    # Выбираем случайный фильтр
    r_filter = random.choice(brand_filters)

    # Добавляем фильтр в запрос
    brand['filter'] = r_filter

    # Делаем тестовый запрос на создание Бренда в БД
    result = requests.post(server_url + 'equipment_brand', json=brand, headers=headers).json()

    #  Удаляем фильтер из данных для последующего сравнения
    del brand['filter']

    # Если фильтр имел тело
    if r_filter:

        # Отсортируем данные одинаково (иначе тесты сыпятся)
        result['data'] = filter_equipment(result['data'])

        # Фильтруем тестовые данные, как бы отфильтровал обработчик запроса к БД
        brands = filter_equipment(
            equipment_brands[:brand['id']],  # Берем элементы, которые уже созданы
            title=r_filter.get('title'),
            deleted=r_filter.get('deleted'),
            parents_id=r_filter.get('equipment_type_id'),
            field_parents='equipment_type_id'
        )
        # Сравниваем ответ
        assert result == {
            'success': True,
            'count': len(brands),
            'page': 0,
            'data': brands
        }
    # Если фильтр без тела
    else:
        # Сравниваем ответ
        assert result == {
            'success': True,
            'data': brand,
            'message': f'{brand["id"]} added'
        }


@pytest.mark.parametrize('brand', ebrand_for_edit)
def test_edit_equipment_brands(server_url, headers, brand):
    # Выбираем случайный фильтр
    r_filter = random.choice(brand_filters)

    # Добавляем фильтр в запрос
    brand['filter'] = r_filter

    # Делаем запрос на изменение Бренда в БД
    result = requests.put(server_url + 'equipment_brand', json=brand, headers=headers).json()

    #  Удаляем фильтер из данных для последующего сравнения
    del brand['filter']

    # Обновляем тестовые данные, как бы это сделал обработчик запроса в БД
    equipment_brands[brand['id'] - 1].update(brand)

    # Если фильтр содержит тело
    if r_filter:

        # Отсортируем данные одинаково (иначе тесты сыпятся)
        result['data'] = filter_equipment(result['data'])

        # Фильтруем тестовые данные, как бы отфильтровал обработчик запроса к БД
        brands = filter_equipment(
            equipment_brands,
            title=r_filter.get('title'),
            deleted=r_filter.get('deleted'),
            parents_id=r_filter.get('equipment_type_id'),
            field_parents='equipment_type_id'
        )
        # Сравниваем данные
        assert result == {
            'success': True,
            'count': len(brands),
            'page': 0,
            'data': brands
        }
    # Если фильтр не содержит тело
    else:
        # Сравниваем данные
        assert result == {'success': True, 'message': f'{brand["id"]} changed'}


@pytest.mark.parametrize('r_filter', brand_filters)
def test_get_equipment_brands(server_url, headers, r_filter):
    # Если фильтр содержит тело, истользуем его, если нет отправляем пустой объект
    r_filter = r_filter if r_filter else {}

    # Делаем запрос Брендов в БД
    result = requests.post(server_url + 'get_equipment_brand', json=r_filter, headers=headers).json()

    # Отсортируем данные одинаково (иначе тесты сыпятся)
    result['data'] = filter_equipment(result['data'])

    # Фильтруем тестовые данные, как бы отфильтровал обработчик запроса к БД
    brands = filter_equipment(
        equipment_brands,
        title=r_filter.get('title'),
        deleted=r_filter.get('deleted'),
        parents_id=r_filter.get('equipment_type_id'),
        field_parents='equipment_type_id'
    )
    # Сравниваем данные
    assert result == {
        'success': True,
        'count': len(brands),
        'page': 0,
        'data': brands
    }


@pytest.mark.parametrize('subtype', equipment_subtypes)
def test_create_equipment_subtype(server_url, headers, subtype):
    # Выбираем случайный фильтр
    r_filter = random.choice(subtype_filters)

    # Добавляем фильтр в запрос
    subtype['filter'] = r_filter

    # Делаем тестовый запрос на создание Модуля/Серии в БД
    result = requests.post(server_url + 'equipment_subtype', json=subtype, headers=headers).json()

    #  Удаляем фильтер из данных для последующего сравнения
    del subtype['filter']

    # Если фильтр имел тело
    if r_filter:

        # Отсортируем данные одинаково (иначе тесты сыпятся)
        result['data'] = filter_equipment(result['data'])

        # Фильтруем тестовые данные, как бы отфильтровал обработчик запроса к БД
        subtypes = filter_equipment(
            equipment_subtypes[:subtype['id']],  # Берем элементы, которые уже созданы
            title=r_filter.get('title'),
            deleted=r_filter.get('deleted'),
            parents_id=r_filter.get('equipment_brand_id'),
            field_parents='equipment_brand_id'
        )
        # Сравниваем ответ
        assert result == {
            'success': True,
            'count': len(subtypes),
            'page': 0,
            'data': subtypes
        }
    # Если фильтр без тела
    else:
        # Сравниваем ответ
        assert result == {
            'success': True,
            'data': subtype,
            'message': f'{subtype["id"]} added'
        }


@pytest.mark.parametrize('subtype', esubtype_for_edit)
def test_edit_equipment_subtypes(server_url, headers, subtype):
    # Выбираем случайный фильтр
    r_filter = random.choice(subtype_filters)

    # Добавляем фильтр в запрос
    subtype['filter'] = r_filter

    # Делаем запрос на изменение Модуля/Серии в БД
    result = requests.put(server_url + 'equipment_subtype', json=subtype, headers=headers).json()

    #  Удаляем фильтер из данных для последующего сравнения
    del subtype['filter']

    # Обновляем тестовые данные, как бы это сделал обработчик запроса в БД
    equipment_subtypes[subtype['id'] - 1].update(subtype)

    # Если фильтр содержит тело
    if r_filter:

        # Отсортируем данные одинаково (иначе тесты сыпятся)
        result['data'] = filter_equipment(result['data'])

        # Фильтруем тестовые данные, как бы отфильтровал обработчик запроса к БД
        subtypes = filter_equipment(
            equipment_subtypes,
            title=r_filter.get('title'),
            deleted=r_filter.get('deleted'),
            parents_id=r_filter.get('equipment_brand_id'),
            field_parents='equipment_brand_id'
        )
        # Сравниваем данные
        assert result == {
            'success': True,
            'count': len(subtypes),
            'page': 0,
            'data': subtypes
        }
    # Если фильтр не содержит тело
    else:
        # Сравниваем данные
        assert result == {'success': True, 'message': f'{subtype["id"]} changed'}


@pytest.mark.parametrize('r_filter', subtype_filters)
def test_get_equipment_subtypes(server_url, headers, r_filter):
    # Если фильтр содержит тело, истользуем его, если нет отправляем пустой объект
    r_filter = r_filter if r_filter else {}

    # Делаем запрос Моделей/Серий в БД
    result = requests.post(server_url + 'get_equipment_subtype', json=r_filter, headers=headers).json()

    # Отсортируем данные одинаково (иначе тесты сыпятся)
    result['data'] = filter_equipment(result['data'])

    # Фильтруем тестовые данные, как бы отфильтровал обработчик запроса к БД
    subtypes = filter_equipment(
        equipment_subtypes,
        title=r_filter.get('title'),
        deleted=r_filter.get('deleted'),
        parents_id=r_filter.get('equipment_brand_id'),
        field_parents='equipment_brand_id'
    )
    # Сравниваем данные
    assert result == {
        'success': True,
        'count': len(subtypes),
        'page': 0,
        'data': subtypes
    }


@pytest.mark.parametrize('model', equipment_models)
def test_create_equipment_model(server_url, headers, model):
    # Выбираем случайный фильтр
    r_filter = random.choice(model_filters)

    # Добавляем фильтр в запрос
    model['filter'] = r_filter

    # Делаем тестовый запрос на создание Модели в БД
    result = requests.post(server_url + 'equipment_model', json=model, headers=headers).json()

    #  Удаляем фильтер из данных для последующего сравнения
    del model['filter']

    # Если фильтр имел тело
    if r_filter:

        # Отсортируем данные одинаково (иначе тесты сыпятся)
        result['data'] = filter_equipment(result['data'])

        # Фильтруем тестовые данные, как бы отфильтровал обработчик запроса к БД
        models = filter_equipment(
            equipment_models[:model['id']],  # Берем элементы, которые уже созданы
            title=r_filter.get('title'),
            deleted=r_filter.get('deleted'),
            parents_id=r_filter.get('equipment_subtype_id'),
            field_parents='equipment_subtype_id'
        )
        # Сравниваем ответ
        assert result == {
            'success': True,
            'count': len(models),
            'page': 0,
            'data': models
        }
    # Если фильтр без тела
    else:
        # Сравниваем ответ
        assert result == {
            'success': True,
            'data': model,
            'message': f'{model["id"]} added'
        }


@pytest.mark.parametrize('model', emodel_for_edit)
def test_edit_equipment_models(server_url, headers, model):
    # Выбираем случайный фильтр
    r_filter = random.choice(model_filters)

    # Добавляем фильтр в запрос
    model['filter'] = r_filter

    # Делаем запрос на изменение Модели в БД
    result = requests.put(server_url + 'equipment_model', json=model, headers=headers).json()

    #  Удаляем фильтер из данных для последующего сравнения
    del model['filter']

    # Обновляем тестовые данные, как бы это сделал обработчик запроса в БД
    equipment_models[model['id'] - 1].update(model)

    # Если фильтр содержит тело
    if r_filter:

        # Отсортируем данные одинаково (иначе тесты сыпятся)
        result['data'] = filter_equipment(result['data'])

        # Фильтруем тестовые данные, как бы отфильтровал обработчик запроса к БД
        models = filter_equipment(
            equipment_models,
            title=r_filter.get('title'),
            deleted=r_filter.get('deleted'),
            parents_id=r_filter.get('equipment_subtype_id'),
            field_parents='equipment_subtype_id'
        )
        # Сравниваем данные
        assert result == {
            'success': True,
            'count': len(models),
            'page': 0,
            'data': models
        }
    # Если фильтр не содержит тело
    else:
        # Сравниваем данные
        assert result == {'success': True, 'message': f'{model["id"]} changed'}


@pytest.mark.parametrize('r_filter', model_filters)
def test_get_equipment_models(server_url, headers, r_filter):
    # Если фильтр содержит тело, истользуем его, если нет отправляем пустой объект
    r_filter = r_filter if r_filter else {}

    # Делаем запрос Моделей в БД
    result = requests.post(server_url + 'get_equipment_model', json=r_filter, headers=headers).json()

    # Отсортируем данные одинаково (иначе тесты сыпятся)
    result['data'] = filter_equipment(result['data'])

    # Фильтруем тестовые данные, как бы отфильтровал обработчик запроса к БД
    models = filter_equipment(
        equipment_models,
        title=r_filter.get('title'),
        deleted=r_filter.get('deleted'),
        parents_id=r_filter.get('equipment_subtype_id'),
        field_parents='equipment_subtype_id'
    )
    # Сравниваем данные
    assert result == {
        'success': True,
        'count': len(models),
        'page': 0,
        'data': models
    }

# todo: дописать тесты для join
# todo: дописать тесты для добавление картинок
# todo: дописать тесты для невалидных данных
