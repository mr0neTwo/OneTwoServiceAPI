import re
from operator import and_

from tqdm import tqdm

from app.db.interaction.interaction import DbInteraction
from app.db.models.models import EquipmentType, EquipmentBrand, EquipmentSubtype, EquipmentModel

from payments.alba import alba
from payments.alba2022 import alba2022
from payments.alfa import alfa
from payments.anton import anton
from payments.anton2022 import anton2022
from payments.fedreserv import fedreserv
from payments.fedreserv2022 import fedreserv2022
from payments.kassa import kassa
from payments.kassa2022 import kassa2022
from payments.obus import obus
from payments.obus2022 import obus2022
from payments.sber import sber
from payments.sber2022 import sber2022
from payments.seyf import seyf
from payments.seyf2022 import seyf2022
from payments.tinkoff import tinkoff
from payments.tinkoff2022 import tinkoff2022
from payments.yura import yura
from payments.yura2022 import yura2022
from utils import GetCustomer, GetOders

db = DbInteraction(
        host='5.53.124.252',
        port='5432',
        user='postgres',
        password='225567',
        db_name='one_two',
        rebuild_db=False
    )

dict_emploeey_ids = {
    '68021': 1,
    '68023': 2,
    '68024': 3,
    '68025': 4,
    '68026': 5,
    '68027': 6,
    '79236': 7,
    '90657': 8,
    '141624': 9
}

def updeteClienst():
    print('Обнавление клиентов...')
    list_client = GetCustomer(page='all')
    for client in tqdm(list_client, desc='Добавление в базу данных', position=0):
        id_create_client = db.add_clients(
            juridical=client.get('juridical'),
            supplier=client.get('supplier'),
            conflicted=client.get('conflicted'),
            should_send_email=False,
            deleted=False,
            discount_good_type=False,
            discount_materials_type=False,
            discount_service_type=False,

            name=client.get('name'),
            name_doc=client.get('custom_fields').get('f1022889'),
            email=client.get('email'),
            address=client.get('address'),
            discount_code=client.get('discount_code'),
            notes=client.get('notes'),
            ogrn='',
            inn='',
            kpp='',
            juridical_address='',
            director='',
            bank_name='',
            settlement_account='',
            corr_account='',
            bic='',

            discount_goods=client.get('discount_goods'),
            discount_materials=client.get('discount_materials'),
            discount_services=client.get('discount_services'),

            ad_campaign_id=1,
            discount_goods_margin_id=1,
            discount_materials_margin_id=1,
            discount_service_margin_id=1,

            tags=[],
            created_at=client.get('created_at') / 1000
        )

        for phone in client.get('phone'):
            db.add_phone(
                number=phone,
                title='Мобильный',
                client_id=id_create_client
            )
    print('Клиенты синхронизированы')

def updataOrders():
    # Обновим заказы
    n = 0
    list_orders = GetOders()
    for order in tqdm(list_orders, desc='Добавление в базу данных', position=0):

        equipment_type = db.pgsql_connetction.session.query(EquipmentType).filter(
            EquipmentType.title == order.get('kindof_good').strip()
        ).first()

        equipment_type_id = equipment_type.id if equipment_type else 1


        equipment_brand = db.pgsql_connetction.session.query(EquipmentBrand).filter(
            and_(
                EquipmentBrand.title == order['custom_fields'].get('f718512').strip(),
                EquipmentBrand.equipment_type_id == equipment_type_id
            )
        ).first()

        equipment_brand_id = equipment_brand.id if equipment_brand else 1

        equipment_subtype = db.pgsql_connetction.session.query(EquipmentSubtype).filter(
            and_(
                EquipmentSubtype.title == '-',
                EquipmentSubtype.equipment_brand_id == equipment_brand_id
            )
        ).first()

        equipment_subtype_id = equipment_subtype.id if equipment_subtype else 1

        equipment_model = db.pgsql_connetction.session.query(EquipmentModel).filter(
            and_(
                EquipmentModel.title == order.get('model').strip(),
                EquipmentModel.equipment_subtype_id == equipment_subtype_id
            )
        ).first()

        equipment_model_id = equipment_model.id if equipment_model else 1

        status = db.get_status(name=order['status']['name'])['data']
        client = db.get_clients(name=order['client']['name'])['data']

        id_order = db.add_orders(
            created_at=order.get('created_at') / 1000 if order.get('created_at') else None,
            done_at=order.get('done_at') / 1000 if order.get('done_at') else None,
            closed_at=order.get('closed_at') / 1000 if order.get('closed_at') else None,
            assigned_at=order.get('assigned_at') / 1000 if order.get('assigned_at') else None,
            duration=order.get('duration') / 1000 if order.get('duration') else None,
            estimated_done_at=order.get('estimated_done_at') / 1000 if order.get('estimated_done_at') else None,
            scheduled_for=order.get('scheduled_for') / 1000 if order.get('scheduled_for') else None,
            warranty_date=order.get('warranty_date') / 1000 if order.get('warranty_date') else None,
            status_deadline=order.get('status_deadline') / 1000 if order.get('status_deadline') else None,

            ad_campaign_id=1,
            branch_id=1,
            status_id=status[0]['id'] if status else None,
            client_id=client[0]['id'] if order.get('client') and client else None,
            order_type_id=db.get_order_type(name=order['order_type']['name'])['data'][0]['id'] if order.get('order_type') else None,
            closed_by_id=dict_emploeey_ids[str(order.get('closed_by_id'))] if order.get('closed_by_id') else None,
            created_by_id=dict_emploeey_ids[str(order.get('created_by_id'))] if order.get('created_by_id') else None,
            engineer_id=dict_emploeey_ids[str(order.get('engineer_id'))] if order.get('engineer_id') else None,
            manager_id=dict_emploeey_ids[str(order.get('manager_id'))] if order.get('manager_id') else None,

            id_label=order.get('id_label'),
            prefix=order.get('prefix'),
            kindof_good=equipment_type_id,
            brand=equipment_brand_id,
            model=equipment_model_id,
            serial=order.get('serial'),
            subtype=equipment_subtype_id,
            malfunction=order.get('malfunction'),
            packagelist=order.get('packagelist') if order.get('packagelist') else order['custom_fields'].get('f718508'),
            appearance=order.get('appearance'),
            manager_notes=order.get('manager_notes'),
            engineer_notes=order.get('engineer_notes'),
            resume=order.get('resume'),
            cell=None,

            estimated_cost=order.get('estimated_cost', 0) if (type(order.get('estimated_cost', 0)) == int or type(order.get('estimated_cost', 0)) == float) else 0,
            missed_payments=order.get('missed_payments', 0),
            discount_sum=order.get('discount_sum', 0),
            payed=order.get('payed', 0),
            price=order.get('price', 0),

            urgent=order.get('urgent')
        )


        if order.get('operations'):
            for operation in order.get('operations'):
                db.add_operations(
                    amount=operation.get('amount'),
                    cost=operation.get('cost'),
                    discount_value=operation.get('discount_value'),
                    engineer_id=dict_emploeey_ids[str(operation.get('engineer_id'))] if operation.get('engineer_id') else None,
                    price=operation.get('price') + operation.get('discount_value'),
                    total=operation.get('price'),
                    title=operation.get('title'),
                    comment='',
                    deleted=False,
                    warranty_period=operation.get('warranty_period'),
                    created_at=operation.get('created_at'),
                    order_id=id_order,
                    dict_id=None
                )
        if order.get('parts'):
            for part in order.get('parts'):
                db.add_oder_parts(
                    amount=part.get('amount'),
                    cost=part.get('cost'),
                    discount_value=part.get('discount_value'),
                    engineer_id=dict_emploeey_ids[str(part.get('engineer_id'))] if part.get('engineer_id') else None,
                    price=part.get('price') + part.get('discount_value'),
                    total=part.get('price'),
                    title=part.get('title'),
                    comment='',
                    deleted=False,
                    warranty_period=part.get('warranty_period'),
                    created_at=part.get('created_at'),
                    order_id=id_order
                )
        if order.get('attachments'):
            for attachment in order.get('attachments'):
                db.add_attachments(
                    created_by_id=dict_emploeey_ids[str(attachment.get('created_by_id'))] if attachment.get('created_by_id') else None,
                    created_at=attachment.get('created_at') / 1000 if attachment.get('created_at') else None,
                    filename=attachment.get('filename'),
                    url=attachment.get('url'),
                    order_id=id_order
                )
        n += 1
        if n == len(list_orders):
            index = int(order['id_label'][4:])
            db.edit_counts(id=1, count=index + 1, prefix=None, description=None)

def updataPayments():
    # Добавим платежи
    regex_lable = re.compile('OTS-\d+')
    data_payments = [
        {
            'data': alfa,
            'title': 'Транзакции Альфа Банк',
            'cashbox_id': 4
        }, {
            'data': fedreserv,
            'title': 'Транзакции Федеральный резерв',
            'cashbox_id': 7
        }, {
            'data': fedreserv2022,
            'title': 'Транзакции Федеральный резерв 2022',
            'cashbox_id': 7
        }, {
            'data': kassa,
            'title': 'Транзакции Касса',
            'cashbox_id': 1
        }, {
            'data': kassa2022,
            'title': 'Транзакции Касса 2022',
            'cashbox_id': 1
        }, {
            'data': obus,
            'title': 'Транзакции Обустройство',
            'cashbox_id': 6
        }, {
            'data': obus2022,
            'title': 'Транзакции Обустройство 2022',
            'cashbox_id': 6
        }, {
            'data': sber,
            'title': 'Транзакции Сбербанк',
            'cashbox_id': 3
        }, {
            'data': sber2022,
            'title': 'Транзакции Сбербанк 2022',
            'cashbox_id': 3
        }, {
            'data': seyf,
            'title': 'Транзакции Сейф',
            'cashbox_id': 5
        }, {
            'data': seyf2022,
            'title': 'Транзакции Сейф 2022',
            'cashbox_id': 5
        }, {
            'data': tinkoff,
            'title': 'Транзакции Тинькофф',
            'cashbox_id': 2
        }, {
            'data': tinkoff2022,
            'title': 'Транзакции Тинькофф 2022',
            'cashbox_id': 2
        }, {
            'data': anton,
            'title': 'Транзакции кассы Антон',
            'cashbox_id': 8
        }, {
            'data': anton2022,
            'title': 'Транзакции кассы Антон 2022',
            'cashbox_id': 8
        }, {
            'data': yura,
            'title': 'Транзакции кассы Юра',
            'cashbox_id': 9
        }, {
            'data': yura2022,
            'title': 'Транзакции кассы Юра 2022',
            'cashbox_id': 9
        }, {
            'data': alba,
            'title': 'Транзакции кассы Альбина',
            'cashbox_id': 10
        }, {
            'data': alba2022,
            'title': 'Транзакции кассы Альбина 2022',
            'cashbox_id': 10
        }
    ]
    for data in data_payments:
        for payment in tqdm(data['data'], position=0, desc=data['title']):

            if payment.get('client'):
                client = db.get_clients(name=payment['client'].get('name'))['data']
                if client:
                    client = client[0]['id']
                else:
                    client = None
            else:
                client = None


            if regex_lable.findall(payment['description']):
                order = db.get_orders(id_label=regex_lable.findall(payment['description'])[0])['data']
                if order:
                    order = order[0]['id']
                else:
                    order = None
            else:
                order = None

            db.add_payments(
                cashflow_category=payment.get('cashflow_category'),
                description=payment.get('description'),
                deposit=payment.get('deposit'),
                income=payment.get('income'),
                outcome=payment.get('outcome'),
                direction=0 if not payment.get('cashflow_category') else (2 if payment.get('income') else 1),
                can_print_fiscal=payment.get('can_print_fiscal'),
                deleted=payment.get('is_deleted'),
                is_fiscal=payment.get('is_fiscal'),
                created_at=payment.get('created_at') / 1000,
                custom_created_at=payment.get('custom_created_at') / 1000,
                tags=payment.get('tags'),
                relation_id=0,
                cashbox_id=data['cashbox_id'],
                client_id=client,
                employee_id=dict_emploeey_ids[str(payment['employee'].get('id'))],
                order_id=order
            )

# updeteClienst()
# updataOrders()
updataPayments()