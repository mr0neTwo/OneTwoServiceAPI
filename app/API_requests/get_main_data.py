from flask import Blueprint
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, decode_token
from flask import request
from flask_login import current_user, login_required
from sqlalchemy import func

from app.db.interaction.db_iteraction import db_iteraction
from app.db.models.models import Branch, GenerallyInfo, OrderType, Counts, AdCampaign, ItemPayments, \
    StatusGroup, Cashboxs, Payments, ServicePrices, Employees

main_data = Blueprint('main_data', __name__)


@main_data.route('/get_main_data', methods=['POST'])
@login_required
def get_main_data():
    user = current_user.get_user()

    # Проверим содежит ли запрос тело json
    try:
        request_body = dict(request.json)
    except:
        return {'success': False, 'message': "Request don't has json body"}, 400

    id = request_body.get('id')
    if id and type(id) != int:
        return {'success': False, 'message': "id is not integer"}, 400

    result = {}

    result['user'] = {
        'id': user.id,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'phone': user.phone,
        'notes': user.notes,
        'deleted': user.deleted,
        'inn': user.inn,
        'doc_name': user.doc_name,
        'post': user.post,
        'permissions': user.permissions,
        'login': user.login,
        'avatar': user.avatar,
        'role': {
            'id': user.role.id,
            'title': user.role.title,
            'earnings_visibility': user.role.earnings_visibility,
            'leads_visibility': user.role.leads_visibility,
            'orders_visibility': user.role.orders_visibility,
            'permissions': user.role.permissions,
            'settable_statuses': user.role.settable_statuses,
            'visible_statuses': user.role.visible_statuses,
            'settable_discount_margin': user.role.settable_discount_margin
        }
    }


    generally_info = db_iteraction.pgsql_connetction.session.query(GenerallyInfo).first()
    result['generally_info'] = {
        'id': generally_info.id,
        'name': generally_info.name,
        'address': generally_info.address,
        'email': generally_info.email,

        'ogrn': generally_info.ogrn,
        'inn': generally_info.inn,
        'kpp': generally_info.kpp,
        'juridical_address': generally_info.juridical_address,
        'director': generally_info.director,
        'bank_name': generally_info.bank_name,
        'settlement_account': generally_info.settlement_account,
        'corr_account': generally_info.corr_account,
        'bic': generally_info.bic,

        'description': generally_info.description,
        'phone': generally_info.phone,
        'logo': generally_info.logo
    }

    query = db_iteraction.pgsql_connetction.session.query(Branch)
    query = query.filter(Branch.deleted.is_(False))
    branches = query.all()
    branches = list(filter(lambda branch: user.id in branch.employees, branches))
    data = []
    for row in branches:
        data.append({
            'id': row.id,
            'name': row.name,
            'address': row.address,
            'phone': row.phone,
            'color': row.color,
            'icon': row.icon,
            'orders_type_id': row.orders_type_id,
            'orders_type_strategy': row.orders_type_strategy,
            'orders_prefix': row.orders_prefix,
            'documents_prefix': row.documents_prefix,
            'employees': row.employees,
            'deleted': row.deleted,
            'schedule': [{
                'id': shed.id,
                'start_time': shed.start_time,
                'end_time': shed.end_time,
                'work_day': shed.work_day,
                'week_day': shed.week_day,
                'branch_id': shed.branch_id
            } for shed in row.schedule] if row.schedule else []
        })
    result['branch'] = data

    order_type = db_iteraction.pgsql_connetction.session.query(OrderType).all()
    data = []
    for row in order_type:
        data.append({
            'id': row.id,
            'name': row.name
        })
    result['order_type'] = data

    counts = db_iteraction.pgsql_connetction.session.query(Counts).all()
    data = []
    for count in counts:
        data.append({
            'id': count.id,
            'prefix': count.prefix,
            'count': count.count,
            'description': count.description
        })
    result['counts'] = data

    ad_campaign = db_iteraction.pgsql_connetction.session.query(AdCampaign).all()
    data = []
    for row in ad_campaign:
        data.append({
            'id': row.id,
            'name': row.name
        })
    result['ad_campaign'] = data

    item_payments = db_iteraction.pgsql_connetction.session.query(ItemPayments).all()
    data = []
    for row in item_payments:
        data.append({
            'id': row.id,
            'title': row.title,
            'direction': row.direction
        })
    result['item_payments'] = data

    status_group = db_iteraction.pgsql_connetction.session.query(StatusGroup).all()
    data = []
    for row in status_group:
        data.append({
            'id': row.id,
            'name': row.name,
            'type_group': row.type_group,
            'color': row.color,
            'status': [{
                'id': stat.id,
                'name': stat.name,
                'color': stat.color,
                'group': stat.group,
                'deadline': stat.deadline,
                'comment_required': stat.comment_required,
                'payment_required': stat.payment_required,
                'available_to': stat.available_to
            } for stat in row.status] if row.status else []
        })
    result['status_group'] = data

    query = db_iteraction.pgsql_connetction.session.query(Cashboxs)
    query = query.filter(Cashboxs.deleted.is_(False))
    cashboxes = query.all()
    data = []
    for row in cashboxes:
        query = db_iteraction.pgsql_connetction.session.query(func.sum(Payments.income + Payments.outcome))
        query = query.filter(Payments.cashbox_id == row.id)
        query = query.filter(Payments.deleted.is_(False))
        balance = query.scalar()

        data.append({
            'id': row.id,
            'title': row.title,
            'balance': balance,
            'type': row.type,
            'isGlobal': row.isGlobal,
            'isVirtual': row.isVirtual,
            'deleted': row.deleted,
            'permissions': row.permissions,
            'employees': row.employees,
            'branch_id': row.branch_id
        })
    # Отфильтруем доступные для пользователя кассы
    data = list(filter(lambda cashbox: cashbox['employees'][f'{user.id}']['available'], data))
    result['cashboxes'] = data

    service_prices = db_iteraction.pgsql_connetction.session.query(ServicePrices).all()
    data = []
    for row in service_prices:
        data.append({
            'id': row.id,
            'cost': row.cost,
            'discount_margin_id': row.discount_margin_id,
            'service_id': row.service_id,
            'deleted': row.deleted
        })
    result['service_prices'] = data

    employees = db_iteraction.pgsql_connetction.session.query(Employees).all()
    data = []
    for row in employees:
        data.append({
            'id': row.id,
            'first_name': row.first_name,
            'last_name': row.last_name,
            'email': row.email,
            'phone': row.phone,
            'notes': row.notes,
            'deleted': row.deleted,
            'inn': row.inn,
            'doc_name': row.doc_name,
            'post': row.post,
            'permissions': row.permissions,
            'login': row.login,
            'avatar': row.avatar,
            'role': {
                'id': row.role.id,
                'title': row.role.title,
                'earnings_visibility': row.role.earnings_visibility,
                'leads_visibility': row.role.leads_visibility,
                'orders_visibility': row.role.orders_visibility,
                'permissions': row.role.permissions,
                'settable_statuses': row.role.settable_statuses,
                'visible_statuses': row.role.visible_statuses,
                'settable_discount_margin': row.role.settable_discount_margin
            }
        })
    result['employees'] = data

    result['success'] = True
    return result, 200