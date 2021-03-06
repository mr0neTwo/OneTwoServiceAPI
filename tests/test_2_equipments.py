import base64
import os
import random

import pytest
import requests

from data.data import equipment_type, equipment_brand, equipment_subtype, equipment_model
from data.test_images import img1, img2

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
etype_for_join = [
    {
        'id': 1,
        'title': 'join1',
        'list_for_join': [2, 3],
        'filter': {
            'title': '',
            'deleted': False
        }
    }, {
        'id': 4,
        'title': 'join2',
        'list_for_join': [5, 6, 7],
        'filter': {
            'title': '',
            'deleted': False
        }
    }
]
ebrand_for_join = [
    {
        'id': 1,
        'title': 'Brand(join1)',
        'list_for_join': [2, 3],
        'filter': {
            'title': '',
            'deleted': False
        }
    }, {
        'id': 4,
        'title': 'Brand(join2)',
        'list_for_join': [5, 6, 7],
        'filter': {
            'title': '',
            'deleted': False
        }
    }
]
esubtype_for_join = [
    {
        'id': 1,
        'title': 'Subtype(join1)',
        'list_for_join': [2, 3],
        'filter': {
            'title': '',
            'deleted': False
        }
    }, {
        'id': 4,
        'title': 'Subtype(join2)',
        'list_for_join': [5, 6, 7],
        'filter': {
            'title': '',
            'deleted': False
        }
    }
]


# ?????????????? ?????? ???????????????????? ???????????????? ????????????
def filter_equipment(list_equipments, title=None, deleted=None, parents_id=None, field_parents=None):
    if title:
        list_equipments = list(filter(lambda e: title.lower() in e['title'].lower(), list_equipments))
    if deleted is not None:
        list_equipments = list(filter(lambda e: deleted or e['deleted'] is deleted, list_equipments))
    if parents_id:
        list_equipments = list(filter(lambda e: e[field_parents] == parents_id, list_equipments))
    return sorted(list_equipments, key=lambda e: e['id'])


@pytest.mark.parametrize('equipment_type', equipment_types)
def test_create_equipment_types(server_url, headers, equipment_type):
    # ???????????????? ?????????????????? ????????????
    r_filter = random.choice(type_filters)

    # ?????????????????? ???????????? ?? ????????????
    equipment_type['filter'] = r_filter

    # ???????????? ???????????????? ???????????? ???? ???????????????? ???????? ?????????????? ?? ????
    result = requests.post(server_url + 'equipment_type', json=equipment_type, headers=headers).json()

    #  ?????????????? ?????????????? ???? ???????????? ?????? ???????????????????????? ??????????????????
    del equipment_type['filter']

    # ???????? ???????????? ???????? ????????
    if r_filter:

        # ?????????????????????? ???????????? ?????????????????? (?????????? ?????????? ??????????????)
        result['data'] = filter_equipment(result['data'])

        # ?????????????????? ???????????????? ????????????, ?????? ???? ???????????????????????? ???????????????????? ?????????????? ?? ????
        e_types = filter_equipment(
            equipment_types[:equipment_type['id']],
            title=r_filter.get('title'),
            deleted=r_filter.get('deleted')
        )
        # ???????????????????? ??????????
        assert result == {
            'success': True,
            'count': len(e_types),
            'page': 0,
            'data': e_types
        }
    # ???????? ???????????? ?????? ????????
    else:
        # ???????????????????? ??????????
        assert result == {
            'success': True,
            'data': equipment_type,
            'message': f'{equipment_type["id"]} added'
        }


@pytest.mark.parametrize('data', etype_for_edit)
def test_edit_equipment_types(server_url, headers, data):
    # ???????????????? ?????????????????? ????????????
    r_filter = random.choice(type_filters)

    # ?????????????????? ???????????? ?? ????????????
    data['filter'] = r_filter

    # ???????????? ???????????? ???? ?????????????????? ???????? ?????????????? ?? ????
    result = requests.put(server_url + 'equipment_type', json=data, headers=headers).json()

    #  ?????????????? ?????????????? ???? ???????????? ?????? ???????????????????????? ??????????????????
    del data['filter']

    # ?????????????????? ???????????????? ????????????, ?????? ???? ?????? ???????????? ???????????????????? ?????????????? ?? ????
    equipment_types[data['id'] - 1].update(data)

    # ???????? ???????????? ???????????????? ????????
    if r_filter:

        # ?????????????????????? ???????????? ?????????????????? (?????????? ?????????? ??????????????)
        result['data'] = filter_equipment(result['data'])

        # ?????????????????? ???????????????? ????????????, ?????? ???? ???????????????????????? ???????????????????? ?????????????? ?? ????
        equipment_type = filter_equipment(
            equipment_types,
            title=r_filter.get('title'),
            deleted=r_filter.get('deleted')
        )
        # ???????????????????? ????????????
        assert result == {
            'success': True,
            'count': len(equipment_type),
            'page': 0,
            'data': equipment_type
        }
    # ???????? ???????????? ???? ???????????????? ????????
    else:
        # ???????????????????? ????????????
        assert result == {'success': True, 'message': f'{data["id"]} changed'}


@pytest.mark.parametrize('r_filter', type_filters)
def test_get_equipment_types(server_url, headers, r_filter):
    # ???????? ???????????? ???????????????? ????????, ???????????????????? ??????, ???????? ?????? ???????????????????? ???????????? ????????????
    r_filter = r_filter if r_filter else {}

    # ???????????? ???????????? ???? ?????????????????? ???????? ?????????????? ?? ????
    result = requests.post(server_url + 'get_equipment_type', json=r_filter, headers=headers).json()

    # ?????????????????????? ???????????? ?????????????????? (?????????? ?????????? ??????????????)
    result['data'] = filter_equipment(result['data'])

    # ?????????????????? ???????????????? ????????????, ?????? ???? ???????????????????????? ???????????????????? ?????????????? ?? ????
    equipment_type = filter_equipment(
        equipment_types,
        title=r_filter.get('title'),
        deleted=r_filter.get('deleted')
    )

    # ???????????????????? ????????????
    assert result == {
        'success': True,
        'count': len(equipment_type),
        'page': 0,
        'data': equipment_type
    }


@pytest.mark.parametrize('brand', equipment_brands)
def test_create_equipment_brand(server_url, headers, brand):
    # ???????????????? ?????????????????? ????????????
    r_filter = random.choice(brand_filters)

    # ?????????????????? ???????????? ?? ????????????
    brand['filter'] = r_filter

    # ???????????? ???????????????? ???????????? ???? ???????????????? ???????????? ?? ????
    result = requests.post(server_url + 'equipment_brand', json=brand, headers=headers).json()

    #  ?????????????? ?????????????? ???? ???????????? ?????? ???????????????????????? ??????????????????
    del brand['filter']

    # ???????? ???????????? ???????? ????????
    if r_filter:

        # ?????????????????????? ???????????? ?????????????????? (?????????? ?????????? ??????????????)
        result['data'] = filter_equipment(result['data'])

        # ?????????????????? ???????????????? ????????????, ?????? ???? ???????????????????????? ???????????????????? ?????????????? ?? ????
        brands = filter_equipment(
            equipment_brands[:brand['id']],  # ?????????? ????????????????, ?????????????? ?????? ??????????????
            title=r_filter.get('title'),
            deleted=r_filter.get('deleted'),
            parents_id=r_filter.get('equipment_type_id'),
            field_parents='equipment_type_id'
        )
        # ???????????????????? ??????????
        assert result == {
            'success': True,
            'count': len(brands),
            'page': 0,
            'data': brands
        }
    # ???????? ???????????? ?????? ????????
    else:
        # ???????????????????? ??????????
        assert result == {
            'success': True,
            'data': brand,
            'message': f'{brand["id"]} added'
        }


@pytest.mark.parametrize('brand', ebrand_for_edit)
def test_edit_equipment_brands(server_url, headers, brand):
    # ???????????????? ?????????????????? ????????????
    r_filter = random.choice(brand_filters)

    # ?????????????????? ???????????? ?? ????????????
    brand['filter'] = r_filter

    # ???????????? ???????????? ???? ?????????????????? ???????????? ?? ????
    result = requests.put(server_url + 'equipment_brand', json=brand, headers=headers).json()

    #  ?????????????? ?????????????? ???? ???????????? ?????? ???????????????????????? ??????????????????
    del brand['filter']

    # ?????????????????? ???????????????? ????????????, ?????? ???? ?????? ???????????? ???????????????????? ?????????????? ?? ????
    equipment_brands[brand['id'] - 1].update(brand)

    # ???????? ???????????? ???????????????? ????????
    if r_filter:

        # ?????????????????????? ???????????? ?????????????????? (?????????? ?????????? ??????????????)
        result['data'] = filter_equipment(result['data'])

        # ?????????????????? ???????????????? ????????????, ?????? ???? ???????????????????????? ???????????????????? ?????????????? ?? ????
        brands = filter_equipment(
            equipment_brands,
            title=r_filter.get('title'),
            deleted=r_filter.get('deleted'),
            parents_id=r_filter.get('equipment_type_id'),
            field_parents='equipment_type_id'
        )
        # ???????????????????? ????????????
        assert result == {
            'success': True,
            'count': len(brands),
            'page': 0,
            'data': brands
        }
    # ???????? ???????????? ???? ???????????????? ????????
    else:
        # ???????????????????? ????????????
        assert result == {'success': True, 'message': f'{brand["id"]} changed'}


@pytest.mark.parametrize('r_filter', brand_filters)
def test_get_equipment_brands(server_url, headers, r_filter):
    # ???????? ???????????? ???????????????? ????????, ???????????????????? ??????, ???????? ?????? ???????????????????? ???????????? ????????????
    r_filter = r_filter if r_filter else {}

    # ???????????? ???????????? ?????????????? ?? ????
    result = requests.post(server_url + 'get_equipment_brand', json=r_filter, headers=headers).json()

    # ?????????????????????? ???????????? ?????????????????? (?????????? ?????????? ??????????????)
    result['data'] = filter_equipment(result['data'])

    # ?????????????????? ???????????????? ????????????, ?????? ???? ???????????????????????? ???????????????????? ?????????????? ?? ????
    brands = filter_equipment(
        equipment_brands,
        title=r_filter.get('title'),
        deleted=r_filter.get('deleted'),
        parents_id=r_filter.get('equipment_type_id'),
        field_parents='equipment_type_id'
    )
    # ???????????????????? ????????????
    assert result == {
        'success': True,
        'count': len(brands),
        'page': 0,
        'data': brands
    }


@pytest.mark.parametrize('subtype', equipment_subtypes)
def test_create_equipment_subtype(server_url, headers, subtype):
    # ???????????????? ?????????????????? ????????????
    r_filter = random.choice(subtype_filters)

    # ?????????????????? ???????????? ?? ????????????
    subtype['filter'] = r_filter

    # ???????????? ???????????????? ???????????? ???? ???????????????? ????????????/?????????? ?? ????
    result = requests.post(server_url + 'equipment_subtype', json=subtype, headers=headers).json()

    #  ?????????????? ?????????????? ???? ???????????? ?????? ???????????????????????? ??????????????????
    del subtype['filter']

    # ???????? ???????????? ???????? ????????
    if r_filter:

        # ?????????????????????? ???????????? ?????????????????? (?????????? ?????????? ??????????????)
        result['data'] = filter_equipment(result['data'])

        # ?????????????????? ???????????????? ????????????, ?????? ???? ???????????????????????? ???????????????????? ?????????????? ?? ????
        subtypes = filter_equipment(
            equipment_subtypes[:subtype['id']],  # ?????????? ????????????????, ?????????????? ?????? ??????????????
            title=r_filter.get('title'),
            deleted=r_filter.get('deleted'),
            parents_id=r_filter.get('equipment_brand_id'),
            field_parents='equipment_brand_id'
        )
        # ???????????????????? ??????????
        assert result == {
            'success': True,
            'count': len(subtypes),
            'page': 0,
            'data': subtypes
        }
    # ???????? ???????????? ?????? ????????
    else:
        # ???????????????????? ??????????
        assert result == {
            'success': True,
            'data': subtype,
            'message': f'{subtype["id"]} added'
        }


@pytest.mark.parametrize('subtype', esubtype_for_edit)
def test_edit_equipment_subtypes(server_url, headers, subtype):
    # ???????????????? ?????????????????? ????????????
    r_filter = random.choice(subtype_filters)

    # ?????????????????? ???????????? ?? ????????????
    subtype['filter'] = r_filter

    # ???????????? ???????????? ???? ?????????????????? ????????????/?????????? ?? ????
    result = requests.put(server_url + 'equipment_subtype', json=subtype, headers=headers).json()

    #  ?????????????? ?????????????? ???? ???????????? ?????? ???????????????????????? ??????????????????
    del subtype['filter']

    # ?????????????????? ???????????????? ????????????, ?????? ???? ?????? ???????????? ???????????????????? ?????????????? ?? ????
    equipment_subtypes[subtype['id'] - 1].update(subtype)

    # ???????? ???????????? ???????????????? ????????
    if r_filter:

        # ?????????????????????? ???????????? ?????????????????? (?????????? ?????????? ??????????????)
        result['data'] = filter_equipment(result['data'])

        # ?????????????????? ???????????????? ????????????, ?????? ???? ???????????????????????? ???????????????????? ?????????????? ?? ????
        subtypes = filter_equipment(
            equipment_subtypes,
            title=r_filter.get('title'),
            deleted=r_filter.get('deleted'),
            parents_id=r_filter.get('equipment_brand_id'),
            field_parents='equipment_brand_id'
        )
        # ???????????????????? ????????????
        assert result == {
            'success': True,
            'count': len(subtypes),
            'page': 0,
            'data': subtypes
        }
    # ???????? ???????????? ???? ???????????????? ????????
    else:
        # ???????????????????? ????????????
        assert result == {'success': True, 'message': f'{subtype["id"]} changed'}


@pytest.mark.parametrize('r_filter', subtype_filters)
def test_get_equipment_subtypes(server_url, headers, r_filter):
    # ???????? ???????????? ???????????????? ????????, ???????????????????? ??????, ???????? ?????? ???????????????????? ???????????? ????????????
    r_filter = r_filter if r_filter else {}

    # ???????????? ???????????? ??????????????/?????????? ?? ????
    result = requests.post(server_url + 'get_equipment_subtype', json=r_filter, headers=headers).json()

    # ?????????????????????? ???????????? ?????????????????? (?????????? ?????????? ??????????????)
    result['data'] = filter_equipment(result['data'])

    # ?????????????????? ???????????????? ????????????, ?????? ???? ???????????????????????? ???????????????????? ?????????????? ?? ????
    subtypes = filter_equipment(
        equipment_subtypes,
        title=r_filter.get('title'),
        deleted=r_filter.get('deleted'),
        parents_id=r_filter.get('equipment_brand_id'),
        field_parents='equipment_brand_id'
    )
    # ???????????????????? ????????????
    assert result == {
        'success': True,
        'count': len(subtypes),
        'page': 0,
        'data': subtypes
    }


@pytest.mark.parametrize('model', equipment_models)
def test_create_equipment_model(server_url, headers, model):
    # ???????????????? ?????????????????? ????????????
    r_filter = random.choice(model_filters)

    # ?????????????????? ???????????? ?? ????????????
    model['filter'] = r_filter

    # ???????????? ???????????????? ???????????? ???? ???????????????? ???????????? ?? ????
    result = requests.post(server_url + 'equipment_model', json=model, headers=headers).json()

    #  ?????????????? ?????????????? ???? ???????????? ?????? ???????????????????????? ??????????????????
    del model['filter']

    # ???????? ???????????? ???????? ????????
    if r_filter:

        # ?????????????????????? ???????????? ?????????????????? (?????????? ?????????? ??????????????)
        result['data'] = filter_equipment(result['data'])

        # ?????????????????? ???????????????? ????????????, ?????? ???? ???????????????????????? ???????????????????? ?????????????? ?? ????
        models = filter_equipment(
            equipment_models[:model['id']],  # ?????????? ????????????????, ?????????????? ?????? ??????????????
            title=r_filter.get('title'),
            deleted=r_filter.get('deleted'),
            parents_id=r_filter.get('equipment_subtype_id'),
            field_parents='equipment_subtype_id'
        )
        # ???????????????????? ??????????
        assert result == {
            'success': True,
            'count': len(models),
            'page': 0,
            'data': models
        }
    # ???????? ???????????? ?????? ????????
    else:
        # ???????????????????? ??????????
        assert result == {
            'success': True,
            'data': model,
            'message': f'{model["id"]} added'
        }


@pytest.mark.parametrize('model', emodel_for_edit)
def test_edit_equipment_models(server_url, headers, model):
    # ???????????????? ?????????????????? ????????????
    r_filter = random.choice(model_filters)

    # ?????????????????? ???????????? ?? ????????????
    model['filter'] = r_filter

    # ???????????? ???????????? ???? ?????????????????? ???????????? ?? ????
    result = requests.put(server_url + 'equipment_model', json=model, headers=headers).json()

    #  ?????????????? ?????????????? ???? ???????????? ?????? ???????????????????????? ??????????????????
    del model['filter']

    # ?????????????????? ???????????????? ????????????, ?????? ???? ?????? ???????????? ???????????????????? ?????????????? ?? ????
    equipment_models[model['id'] - 1].update(model)

    # ???????? ???????????? ???????????????? ????????
    if r_filter:

        # ?????????????????????? ???????????? ?????????????????? (?????????? ?????????? ??????????????)
        result['data'] = filter_equipment(result['data'])

        # ?????????????????? ???????????????? ????????????, ?????? ???? ???????????????????????? ???????????????????? ?????????????? ?? ????
        models = filter_equipment(
            equipment_models,
            title=r_filter.get('title'),
            deleted=r_filter.get('deleted'),
            parents_id=r_filter.get('equipment_subtype_id'),
            field_parents='equipment_subtype_id'
        )
        # ???????????????????? ????????????
        assert result == {
            'success': True,
            'count': len(models),
            'page': 0,
            'data': models
        }
    # ???????? ???????????? ???? ???????????????? ????????
    else:
        # ???????????????????? ????????????
        assert result == {'success': True, 'message': f'{model["id"]} changed'}


@pytest.mark.parametrize('r_filter', model_filters)
def test_get_equipment_models(server_url, headers, r_filter):
    # ???????? ???????????? ???????????????? ????????, ???????????????????? ??????, ???????? ?????? ???????????????????? ???????????? ????????????
    r_filter = r_filter if r_filter else {}

    # ???????????? ???????????? ?????????????? ?? ????
    result = requests.post(server_url + 'get_equipment_model', json=r_filter, headers=headers).json()

    # ?????????????????????? ???????????? ?????????????????? (?????????? ?????????? ??????????????)
    result['data'] = filter_equipment(result['data'])

    # ?????????????????? ???????????????? ????????????, ?????? ???? ???????????????????????? ???????????????????? ?????????????? ?? ????
    models = filter_equipment(
        equipment_models,
        title=r_filter.get('title'),
        deleted=r_filter.get('deleted'),
        parents_id=r_filter.get('equipment_subtype_id'),
        field_parents='equipment_subtype_id'
    )
    # ???????????????????? ????????????
    assert result == {
        'success': True,
        'count': len(models),
        'page': 0,
        'data': models
    }


@pytest.mark.parametrize('data', etype_for_join)
def test_join_equipment_types(server_url, headers, data):

    # ???????????????? ???????????? id ?????? ??????????????????????
    list_for_join = data['list_for_join']

    # ???????????????? ????????????
    r_filter = data.get('filter')

    # ???????????? ???????????? ???? ?????????????????? ???????? ?????????????? ?? ????
    result = requests.put(server_url + 'equipment_type', json=data, headers=headers).json()

    #  ?????????????? ?????????????? ???? ???????????? ?????? ???????????????????????? ??????????????????
    del data['filter']
    del data['list_for_join']

    # ?????????????????? ???????????????? ????????????, ?????? ???? ?????? ???????????? ???????????????????? ?????????????? ?? ????
    equipment_types[data['id'] - 1].update(data)

    # ?????????????? ???????????? ???? ???????????? id
    for etype_id in list_for_join:

        # ?????????????? ???????????? ?????? ??????????????????
        equipment_types[etype_id-1]['deleted'] = True

        # ?????????????? ???????????? ???????????????? ??????????????
        list_brands = filter(lambda brand: brand['equipment_type_id'] == etype_id, equipment_brands)

        # ?????????????? ???????????? ???? ???????????? ???????????????? ??????????????
        for ebrand in list_brands:

            # ?????????????? ???????????????????????? ??????????????
            equipment_brands[ebrand['id'] - 1]['equipment_type_id'] = data['id']



    # ???????? ???????????? ???????????????? ????????
    if r_filter:

        # ?????????????????????? ???????????? ?????????????????? (?????????? ?????????? ??????????????)
        result['data'] = filter_equipment(result['data'])

        # ?????????????????? ???????????????? ????????????, ?????? ???? ???????????????????????? ???????????????????? ?????????????? ?? ????
        equipment_type = filter_equipment(
            equipment_types,
            title=r_filter.get('title'),
            deleted=r_filter.get('deleted')
        )
        # ???????????????????? ????????????
        assert result == {
            'success': True,
            'count': len(equipment_type),
            'page': 0,
            'data': equipment_type
        }
    # ???????? ???????????? ???? ???????????????? ????????
    else:
        # ???????????????????? ????????????
        assert result == {'success': True, 'message': f'{data["id"]} changed'}

    # ???????????????? ?????????? ?????????????????? ?? ??????????????
    # ???????????? ???????????? ?????????????? ?? ????
    result = requests.post(server_url + 'get_equipment_brand', json={}, headers=headers).json()

    # ?????????????????????? ???????????? ?????????????????? (?????????? ?????????? ??????????????)
    result['data'] = filter_equipment(result['data'])

    # ?????????????????? ???????????????? ????????????, ?????? ???? ???????????????????????? ???????????????????? ?????????????? ?? ????
    brands = filter_equipment(equipment_brands)

    # ???????????????????? ????????????
    assert result == {
        'success': True,
        'count': len(brands),
        'page': 0,
        'data': brands
    }


@pytest.mark.parametrize('data', ebrand_for_join)
def test_join_equipment_brands(server_url, headers, data):

    # ???????????????? ???????????? id ?????? ??????????????????????
    list_for_join = data['list_for_join']

    # ???????????????? ????????????
    r_filter = data.get('filter')

    # ???????????? ???????????? ???? ?????????????????? ???????????? ?????????????? ?? ????
    result = requests.put(server_url + 'equipment_brand', json=data, headers=headers).json()

    #  ?????????????? ?????????????? ???? ???????????? ?????? ???????????????????????? ??????????????????
    del data['filter']
    del data['list_for_join']

    # ?????????????????? ???????????????? ????????????, ?????? ???? ?????? ???????????? ???????????????????? ?????????????? ?? ????
    equipment_brands[data['id'] - 1].update(data)

    # ?????????????? ???????????? ???? ???????????? id
    for ebrand_id in list_for_join:

        # ?????????????? ???????????? ?????? ??????????????????
        equipment_brands[ebrand_id-1]['deleted'] = True

        # ?????????????? ???????????? ???????????????? ??????????????
        list_subtypes = filter(lambda subtype: subtype['equipment_brand_id'] == ebrand_id, equipment_subtypes)

        # ?????????????? ???????????? ???? ???????????? ???????????????? ??????????????
        for esubtype in list_subtypes:

            # ?????????????? ???????????????????????? ??????????????
            equipment_subtypes[esubtype['id'] - 1]['equipment_brand_id'] = data['id']

    # ???????? ???????????? ???????????????? ????????
    if r_filter:

        # ?????????????????????? ???????????? ?????????????????? (?????????? ?????????? ??????????????)
        result['data'] = filter_equipment(result['data'])

        # ?????????????????? ???????????????? ????????????, ?????? ???? ???????????????????????? ???????????????????? ?????????????? ?? ????
        brands = filter_equipment(
            equipment_brands,
            title=r_filter.get('title'),
            deleted=r_filter.get('deleted'),
            parents_id=r_filter.get('equipment_type_id'),
            field_parents='equipment_type_id'
        )
        # ???????????????????? ????????????
        assert result == {
            'success': True,
            'count': len(brands),
            'page': 0,
            'data': brands
        }
    # ???????? ???????????? ???? ???????????????? ????????
    else:
        # ???????????????????? ????????????
        assert result == {'success': True, 'message': f'{data["id"]} changed'}

    # ???????????????? ?????????? ?????????????????? ?? ??????????????
    # ???????????? ???????????? ?????????????? ?? ????
    result = requests.post(server_url + 'get_equipment_subtype', json={}, headers=headers).json()

    # ?????????????????????? ???????????? ?????????????????? (?????????? ?????????? ??????????????)
    result['data'] = filter_equipment(result['data'])

    # ?????????????????? ???????????????? ????????????, ?????? ???? ???????????????????????? ???????????????????? ?????????????? ?? ????
    subtypes = filter_equipment(equipment_subtypes)

    # ???????????????????? ????????????
    assert result == {
        'success': True,
        'count': len(subtypes),
        'page': 0,
        'data': subtypes
    }


@pytest.mark.parametrize('data', esubtype_for_join)
def test_join_equipment_subtypes(server_url, headers, data):

    # ???????????????? ???????????? id ?????? ??????????????????????
    list_for_join = data['list_for_join']

    # ???????????????? ????????????
    r_filter = data.get('filter')

    # ???????????? ???????????? ???? ?????????????????? ???????????? ?????????????? ?? ????
    result = requests.put(server_url + 'equipment_subtype', json=data, headers=headers).json()

    #  ?????????????? ?????????????? ???? ???????????? ?????? ???????????????????????? ??????????????????
    del data['filter']
    del data['list_for_join']

    # ?????????????????? ???????????????? ????????????, ?????? ???? ?????? ???????????? ???????????????????? ?????????????? ?? ????
    equipment_subtypes[data['id'] - 1].update(data)

    # ?????????????? ???????????? ???? ???????????? id
    for esubtype_id in list_for_join:

        # ?????????????? ???????????? ?????? ??????????????????
        equipment_subtypes[esubtype_id-1]['deleted'] = True

        # ?????????????? ???????????? ???????????????? ??????????????
        list_models = filter(lambda model: model['equipment_subtype_id'] == esubtype_id, equipment_models)

        # ?????????????? ???????????? ???? ???????????? ???????????????? ??????????????
        for emodel in list_models:

            # ?????????????? ???????????????????????? ??????????????
            equipment_models[emodel['id'] - 1]['equipment_subtype_id'] = data['id']

    # ???????? ???????????? ???????????????? ????????
    if r_filter:

        # ?????????????????????? ???????????? ?????????????????? (?????????? ?????????? ??????????????)
        result['data'] = filter_equipment(result['data'])

        # ?????????????????? ???????????????? ????????????, ?????? ???? ???????????????????????? ???????????????????? ?????????????? ?? ????
        subtypes = filter_equipment(
            equipment_subtypes,
            title=r_filter.get('title'),
            deleted=r_filter.get('deleted'),
            parents_id=r_filter.get('equipment_brand_id'),
            field_parents='equipment_brand_id'
        )
        # ???????????????????? ????????????
        assert result == {
            'success': True,
            'count': len(subtypes),
            'page': 0,
            'data': subtypes
        }
    # ???????? ???????????? ???? ???????????????? ????????
    else:
        # ???????????????????? ????????????
        assert result == {'success': True, 'message': f'{data["id"]} changed'}

    # ???????????????? ?????????? ?????????????????? ?? ??????????????
    # ???????????? ???????????? ?????????????? ?? ????
    result = requests.post(server_url + 'get_equipment_model', json={}, headers=headers).json()

    # ?????????????????????? ???????????? ?????????????????? (?????????? ?????????? ??????????????)
    result['data'] = filter_equipment(result['data'])

    # ?????????????????? ???????????????? ????????????, ?????? ???? ???????????????????????? ???????????????????? ?????????????? ?? ????
    models = filter_equipment(equipment_models)

    # ???????????????????? ????????????
    assert result == {
        'success': True,
        'count': len(models),
        'page': 0,
        'data': models
    }


def test_create_subtype_with_img(server_url, headers):

    # ?????????????????? ????????????
    data = {
        'id': 31,
        'title': 'with_image',
        'branches': [1, 2],
        'deleted': False,
        'icon': None,
        'equipment_brand_id': 1,
        'img': img1
    }

    # ???????????? ???????????????? ???????????? ???? ???????????????? ???????? ?????????????? ?? ????
    result = requests.post(server_url + 'equipment_subtype', json=data, headers=headers).json()

    # ?????????????? ???????????????? ???? ??????????????
    del data['img']

    # ?????????????? url, ?????????????? ???????????? ????????????????
    data['url'] = f'data/PCB/subtype{data["id"]}.jpeg'

    # ???????????????????? ??????????
    assert result == {
        'success': True,
        'data': data,
        'message': f'{data["id"]} added'
    }

    # ???????????????? ???????????????????? ???? ???????? ?? ????????????????????????
    data_uri = base64.b64encode(open('build/static/' + data['url'], 'rb').read()).decode('utf-8')
    assert data_uri == img1[23:]

    # ???????????? ????????
    if os.path.isfile('build/static/' + data['url']):
        os.remove('build/static/' + data['url'])


def test_edit_subtype_with_img(server_url, headers):
    # ?????????????????? ????????????
    data = {
        'id': 1,
        'title': 'with_image_edit',
        'branches': [1, 2],
        'deleted': False,
        'icon': None,
        'equipment_brand_id': 1,
        'img': img2
    }

    # ???????????? ???????????????? ???????????? ???? ???????????????? ???????? ?????????????? ?? ????
    result = requests.put(server_url + 'equipment_subtype', json=data, headers=headers).json()

    # ?????????????? ???????????????? ???? ??????????????
    del data['img']

    # ?????????????? url, ?????????????? ???????????? ????????????????
    data['url'] = f'data/PCB/subtype{data["id"]}.jpeg'

    # ?????????????????? ???????????????? ????????????, ?????? ???? ?????? ???????????? ???????????????????? ?????????????? ?? ????
    equipment_subtypes[data['id'] - 1].update(data)

    # ???????????????????? ????????????
    assert result == {'success': True, 'message': f'{data["id"]} changed'}

    # ???????????????? ???????????????????? ???? ???????? ?? ????????????????????????
    data_uri = base64.b64encode(open('build/static/' + data['url'], 'rb').read()).decode('utf-8')
    assert data_uri == img2[23:]

    # ???????????? ????????
    if os.path.isfile('build/static/' + data['url']):
        os.remove('build/static/' + data['url'])


def test_data_valid(server_url, headers):

    # ???????????? ???????????? ?????? ???????? json
    result = requests.post(server_url + 'get_equipment_type', headers=headers).json()

    # ???????????????????? ??????????????????
    assert result == {'success': False, 'message': "Request don't has json body"}

# todo: ???????????????? ?????????? ?????? ???????????????????? ????????????
