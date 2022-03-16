from sqlalchemy import or_
from app.db.models.models import CustomFilters

# Таблица БЕДЖЕЙ ===============================================================================

def get_badges(self, employee_access):
    statuses = self.get_status()['data']

    badge1 = {
        'id': 1,
        'title': 'В работе',
        'icon': 'M31.342 25.559l-14.392-12.336c0.67-1.259 1.051-2.696 1.051-4.222 0-4.971-4.029-9-9-9-0.909 0-1.787 0.135-2.614 0.386l5.2 5.2c0.778 0.778 0.778 2.051 0 2.828l-3.172 3.172c-0.778 0.778-2.051 0.778-2.828 0l-5.2-5.2c-0.251 0.827-0.386 1.705-0.386 2.614 0 4.971 4.029 9 9 9 1.526 0 2.963-0.38 4.222-1.051l12.336 14.392c0.716 0.835 1.938 0.882 2.716 0.104l3.172-3.172c0.778-0.778 0.731-2-0.104-2.716z',
        'color': '#5cb85c',
        'filter': {
            'status_id': [stat['id'] for stat in filter(lambda status: status['group'] in [1, 2], statuses)],
            'page': 0,
            'urgent': None,
            'overdue': None,
            'status_overdue': None,
            'engineer_id': [employee_access] if employee_access else None,
            'order_type_id': None,
            'manager_id': None,
            'created_at': None,
            'kindof_good': None,
            'brand': None,
            'subtype': None,
            'client_id': None
        }
    }

    badge1['count'] = self.get_orders(
        status_id=badge1['filter']['status_id'],
        page=badge1['filter']['page'],
        urgent=badge1['filter']['urgent'],
        overdue=badge1['filter']['overdue'],
        status_overdue=badge1['filter']['status_overdue'],
        engineer_id=badge1['filter']['engineer_id'],
        order_type_id=badge1['filter']['order_type_id'],
        manager_id=badge1['filter']['manager_id'],
        created_at=badge1['filter']['created_at'],
        kindof_good=badge1['filter']['kindof_good'],
        brand=badge1['filter']['brand'],
        subtype=badge1['filter']['subtype'],
        client_id=badge1['filter']['client_id']
    )['count']

    badge2 = {
        'id': 2,
        'title': 'Срочные',
        'icon': 'M10.031 32c-2.133-4.438-0.997-6.981 0.642-9.376 1.795-2.624 2.258-5.221 2.258-5.221s1.411 1.834 0.847 4.703c2.493-2.775 2.963-7.196 2.587-8.889 5.635 3.938 8.043 12.464 4.798 18.783 17.262-9.767 4.294-24.38 2.036-26.027 0.753 1.646 0.895 4.433-0.625 5.785-2.573-9.759-8.937-11.759-8.937-11.759 0.753 5.033-2.728 10.536-6.084 14.648-0.118-2.007-0.243-3.392-1.298-5.312-0.237 3.646-3.023 6.617-3.777 10.27-1.022 4.946 0.765 8.568 7.555 12.394z',
        'color': '#f74e4d',
        'filter': {
            'status_id': [stat['id'] for stat in filter(lambda status: status['group'] in [1, 2, 3], statuses)],
            'page': 0,
            'urgent': True,
            'overdue': None,
            'status_overdue': None,
            'engineer_id': [employee_access] if employee_access else None,
            'order_type_id': None,
            'manager_id': None,
            'created_at': None,
            'kindof_good': None,
            'brand': None,
            'subtype': None,
            'client_id': None
        }
    }

    badge2['count'] = self.get_orders(
        status_id=badge2['filter']['status_id'],
        page=badge2['filter']['page'],
        urgent=badge2['filter']['urgent'],
        overdue=badge2['filter']['overdue'],
        status_overdue=badge2['filter']['status_overdue'],
        engineer_id=badge2['filter']['engineer_id'],
        order_type_id=badge2['filter']['order_type_id'],
        manager_id=badge2['filter']['manager_id'],
        created_at=badge2['filter']['created_at'],
        kindof_good=badge2['filter']['kindof_good'],
        brand=badge2['filter']['brand'],
        subtype=badge2['filter']['subtype'],
        client_id=badge2['filter']['client_id']
    )['count']

    badge3 = {
        'id': 3,
        'title': 'Ожидают',
        'icon': 'M22.781 16c4.305-2.729 7.219-7.975 7.219-14 0-0.677-0.037-1.345-0.109-2h-27.783c-0.072 0.655-0.109 1.323-0.109 2 0 6.025 2.914 11.271 7.219 14-4.305 2.729-7.219 7.975-7.219 14 0 0.677 0.037 1.345 0.109 2h27.783c0.072-0.655 0.109-1.323 0.109-2 0-6.025-2.914-11.271-7.219-14zM5 30c0-5.841 2.505-10.794 7-12.428v-3.143c-4.495-1.634-7-6.587-7-12.428v0h22c0 5.841-2.505 10.794-7 12.428v3.143c4.495 1.634 7 6.587 7 12.428h-22zM19.363 20.925c-2.239-1.27-2.363-2.918-2.363-3.918v-2.007c0-1 0.119-2.654 2.367-3.927 1.203-0.699 2.244-1.761 3.033-3.073h-12.799c0.79 1.313 1.832 2.376 3.036 3.075 2.239 1.27 2.363 2.918 2.363 3.918v2.007c0 1-0.119 2.654-2.367 3.927-2.269 1.318-3.961 3.928-4.472 7.073h15.677c-0.511-3.147-2.204-5.758-4.475-7.075z',
        'color': '#f0ad4e',
        'filter': {
            'status_id': [stat['id'] for stat in filter(lambda status: status['group'] in [3], statuses)],
            'page': 0,
            'urgent': None,
            'overdue': None,
            'status_overdue': None,
            'engineer_id': [employee_access] if employee_access else None,
            'order_type_id': None,
            'manager_id': None,
            'created_at': None,
            'kindof_good': None,
            'brand': None,
            'subtype': None,
            'client_id': None
        }
    }

    badge3['count'] = self.get_orders(
        status_id=badge3['filter']['status_id'],
        page=badge3['filter']['page'],
        urgent=badge3['filter']['urgent'],
        overdue=badge3['filter']['overdue'],
        status_overdue=badge3['filter']['status_overdue'],
        engineer_id=badge3['filter']['engineer_id'],
        order_type_id=badge3['filter']['order_type_id'],
        manager_id=badge3['filter']['manager_id'],
        created_at=badge3['filter']['created_at'],
        kindof_good=badge3['filter']['kindof_good'],
        brand=badge3['filter']['brand'],
        subtype=badge3['filter']['subtype'],
        client_id=badge3['filter']['client_id']
    )['count']

    badge4 = {
        'id': 4,
        'title': 'Просроченные',
        'icon': 'M16 0c-8.837 0-16 7.163-16 16s7.163 16 16 16 16-7.163 16-16-7.163-16-16-16zM9.707 10.332c-0.39 0.391-1.024 0.391-1.414 0s-0.391-1.024 0-1.414c1.392-1.392 4.023-1.392 5.414 0 0.391 0.39 0.391 1.024 0 1.414-0.195 0.195-0.451 0.293-0.707 0.293s-0.512-0.098-0.707-0.293c-0.604-0.604-1.982-0.604-2.586 0zM16 26c-2.209 0-4-2.239-4-5s1.791-5 4-5 4 2.239 4 5-1.791 5-4 5zM23.707 10.332c-0.195 0.195-0.451 0.293-0.707 0.293s-0.512-0.098-0.707-0.293c-0.604-0.604-1.982-0.604-2.586 0-0.39 0.391-1.024 0.391-1.414 0s-0.391-1.024 0-1.414c1.392-1.392 4.023-1.392 5.414 0 0.391 0.391 0.391 1.024 0 1.414z',
        'color': '#f0ad4e',
        'filter': {
            'status_id': [stat['id'] for stat in filter(lambda status: status['group'] in [1, 2, 3], statuses)],
            'page': 0,
            'urgent': None,
            'overdue': True,
            'status_overdue': None,
            'engineer_id': [employee_access] if employee_access else None,
            'order_type_id': None,
            'manager_id': None,
            'created_at': None,
            'kindof_good': None,
            'brand': None,
            'subtype': None,
            'client_id': None
        }
    }

    badge4['count'] = self.get_orders(
        status_id=badge4['filter']['status_id'],
        page=badge4['filter']['page'],
        urgent=badge4['filter']['urgent'],
        overdue=badge4['filter']['overdue'],
        status_overdue=badge4['filter']['status_overdue'],
        engineer_id=badge4['filter']['engineer_id'],
        order_type_id=badge4['filter']['order_type_id'],
        manager_id=badge4['filter']['manager_id'],
        created_at=badge4['filter']['created_at'],
        kindof_good=badge4['filter']['kindof_good'],
        brand=badge4['filter']['brand'],
        subtype=badge4['filter']['subtype'],
        client_id=badge4['filter']['client_id']
    )['count']

    badge5 = {
        'id': 5,
        'title': 'Просрочен статус',
        'icon': 'M20.586 23.414l-6.586-6.586v-8.828h4v7.172l5.414 5.414zM16 0c-8.837 0-16 7.163-16 16s7.163 16 16 16 16-7.163 16-16-7.163-16-16-16zM16 28c-6.627 0-12-5.373-12-12s5.373-12 12-12c6.627 0 12 5.373 12 12s-5.373 12-12 12z',
        'color': '#f0ad4e',
        'filter': {
            'status_id': [stat['id'] for stat in filter(lambda status: status['group'] in [1, 2, 3, 4], statuses)],
            'page': 0,
            'urgent': None,
            'overdue': None,
            'status_overdue': True,
            'engineer_id': [employee_access] if employee_access else None,
            'order_type_id': None,
            'manager_id': None,
            'created_at': None,
            'kindof_good': None,
            'brand': None,
            'subtype': None,
            'client_id': None
        }
    }

    badge5['count'] = self.get_orders(
        status_id=badge5['filter']['status_id'],
        page=badge5['filter']['page'],
        urgent=badge5['filter']['urgent'],
        overdue=badge5['filter']['overdue'],
        status_overdue=badge5['filter']['status_overdue'],
        engineer_id=badge5['filter']['engineer_id'],
        order_type_id=badge5['filter']['order_type_id'],
        manager_id=badge5['filter']['manager_id'],
        created_at=badge5['filter']['created_at'],
        kindof_good=badge5['filter']['kindof_good'],
        brand=badge5['filter']['brand'],
        subtype=badge5['filter']['subtype'],
        client_id=badge5['filter']['client_id']
    )['count']

    badge6 = {
        'id': 6,
        'title': 'Ждут оплаты',
        'icon': 'M12.42 28.678l-12.433-12.238 6.168-6.071 6.265 6.167 13.426-13.214 6.168 6.071-19.594 19.285zM3.372 16.441l9.048 8.905 16.208-15.953-2.782-2.739-13.426 13.214-6.265-6.167-2.782 2.739z',
        'color': '#434343',
        'filter': {
            'status_id': [stat['id'] for stat in filter(lambda status: status['group'] in [4], statuses)],
            'page': 0,
            'urgent': None,
            'overdue': None,
            'status_overdue': None,
            'engineer_id': [employee_access] if employee_access else None,
            'order_type_id': None,
            'manager_id': None,
            'created_at': None,
            'kindof_good': None,
            'brand': None,
            'subtype': None,
            'client_id': None
        }
    }

    badge6['count'] = self.get_orders(
        status_id=badge6['filter']['status_id'],
        page=badge6['filter']['page'],
        urgent=badge6['filter']['urgent'],
        overdue=badge6['filter']['overdue'],
        status_overdue=badge6['filter']['status_overdue'],
        engineer_id=badge6['filter']['engineer_id'],
        order_type_id=badge6['filter']['order_type_id'],
        manager_id=badge6['filter']['manager_id'],
        created_at=badge6['filter']['created_at'],
        kindof_good=badge6['filter']['kindof_good'],
        brand=badge6['filter']['brand'],
        subtype=badge6['filter']['subtype'],
        client_id=badge6['filter']['client_id']
    )['count']

    result = {'success': True}
    result['data'] = [badge1, badge2, badge3, badge4, badge5, badge6]

    return result

# Таблица ПОЛЬЗОВАТЕЛЬСКИХ ФИЛЬТРОВ ======================================================================

def add_custom_filters(self, title, filters, employee_id, general=False):
    custom_filters = CustomFilters(
        title=title,
        filters=filters,
        employee_id=employee_id,
        general=general
    )
    self.pgsql_connetction.session.add(custom_filters)
    self.pgsql_connetction.session.commit()
    self.pgsql_connetction.session.refresh(custom_filters)
    return custom_filters.id

def get_custom_filters(self, employee_id):
    custom_filters = self.pgsql_connetction.session.query(CustomFilters).filter(
        or_(
            CustomFilters.employee_id == employee_id,
            CustomFilters.general == True,
        ))

    self.pgsql_connetction.session.expire_all()
    result = {'success': True}
    count = custom_filters.count()
    result['count'] = count

    data = []
    for row in custom_filters:
        data.append({
            'id': row.id,
            'title': row.title,
            'filters': row.filters,
            'employee_id': row.employee_id,
            'general': row.general,
            'active': False
        })

    result['data'] = data
    return result

def edit_custom_filters(self, id, title=None, filters=None, general=None):
    self.pgsql_connetction.session.query(CustomFilters).filter_by(id=id).update({
        'title': title if title is not None else CustomFilters.title,
        'filters': filters if filters is not None else CustomFilters.filters,
        'general': general if general is not None else CustomFilters.general
    })
    self.pgsql_connetction.session.commit()
    return id

def del_custom_filters(self, id):
    custom_filters = self.pgsql_connetction.session.query(CustomFilters).get(id)
    if custom_filters:
        self.pgsql_connetction.session.delete(custom_filters)
        self.pgsql_connetction.session.commit()
        return self.get_custom_filters(1)
