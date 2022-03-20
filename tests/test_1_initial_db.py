import pytest


list_tables = [
    'ad_campaign',
    'roles',
    'employees',
    'table_headers',
    'branch',
    'schedule',
    'discount_margin',
    'order_type',
    'status_group',
    'status',
    'clients',
    'phones',
    'equipment_type',
    'equipment_brand',
    'equipment_subtype',
    'equipment_model',
    'orders',
    'group_dict_service',
    'dict_service',
    'service_prices',
    'operations',
    'oder_parts',
    'attachments',
    'menu_rows',
    'badges',
    'custom_filters',
    'setting_menu',
    'generally_info',
    'counts',
    'malfunction',
    'packagelist',
    'item_payments',
    'cashboxs',
    'payments',
    'payrolls',
    'payrules',
    'warehouse',
    'warehouse_category',
    'parts',
    'warehouse_parts',
    'notification_template',
    'notification_events'
]

def test_drop_all_tables(db, insp):
    db.drop_all_tables()
    assert len(insp.get_table_names(schema='public')) == 0, 'Таблицы не удалены'

def test_create_db(db, insp):
    db.create_all_tables()
    assert len(insp.get_table_names(schema='public')) == 42, 'Не совпадает количество таблиц в базе данных'

@pytest.mark.parametrize('table_name', list_tables)
def test_has_table(table_name, insp):
    assert insp.has_table(table_name, schema='public'), f'Таблица {table_name} не создана'

def test_create_role(db):
    db.add_role(
        title='Полный доступ',
        earnings_visibility=True,
        leads_visibility=True,
        orders_visibility=True,
        permissions=['Может', 'практичеси', 'все'],
        settable_statuses=[n for n in range(1, 33)],
        visible_statuses=[n for n in range(1, 33)],
        settable_discount_margin=[n for n in range(1, 4)]
    )
    roles = db.get_role()
    data = {
        'success': True,
        'count': 1,
        'page': 0,
        'data': [{
            'id': 1,
            'title': 'Полный доступ',
            'earnings_visibility': True,
            'leads_visibility': True,
            'orders_visibility': True,
            'permissions': ['Может', 'практичеси', 'все'],
            'settable_statuses': [n for n in range(1, 33)],
            'visible_statuses': [n for n in range(1, 33)],
            'settable_discount_margin': [n for n in range(1, 4)]
        }]
    }
    assert roles == data

def test_create_employee(db):
    db.add_employee(
        first_name='Тайвин',
        last_name='Ланистер',
        email='tywin_lannister@gmail.com',
        notes='',
        phone='79997774477',
        password='power_and_money',
        deleted=False,
        inn=None,
        doc_name='Лев',
        post=None,
        permissions=[],
        role_id=1,
        login=None
    )
    employees = db.get_employee()
    del employees['data'][0]['password']
    assert employees == {
        'success': True,
        'count': 1,
        'page': 0,
        'data': [{
            'id': 1,
            'first_name': 'Тайвин',
            'last_name': 'Ланистер',
            'email': 'tywin_lannister@gmail.com',
            'phone': '79997774477',
            'notes': '',
            'deleted': False,
            'inn': None,
            'doc_name': 'Лев',
            'post': None,
            'permissions': [],
            'role': {
                'id': 1,
                'title': 'Полный доступ',
                'earnings_visibility': True,
                'leads_visibility': True,
                'orders_visibility': True,
                'permissions': ['Может', 'практичеси', 'все'],
                'settable_statuses': [n for n in range(1, 33)],
                'visible_statuses': [n for n in range(1, 33)],
                'settable_discount_margin': [n for n in range(1, 4)]
            },
            'login': None,
            'table_headers': [],
            'payrules': [],
            'balance': None
        }]
    }

