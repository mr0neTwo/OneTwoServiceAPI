import time
import re

from sqlalchemy import and_, desc, func
from werkzeug.security import generate_password_hash

from app.db.client.client import PGSQL_connetction
from app.db.models.models import Base, AdCampaign, Employees, Attachments, Branch, DiscountMargin, OrderType, \
    StatusGroup, Status, OrderParts, Clients, time_now, MenuRows, TableHeaders, EquipmentType, EquipmentBrand, \
    EquipmentSubtype, EquipmentModel, SettingMenu, Roles, Phones, \
    GenerallyInfo, Counts, Schedule, DictMalfunction, DictPackagelist, Cashboxs, Payments, ItemPayments, Payrolls, \
    Payrules, GroupDictService, DictService, ServicePrices, Parts, Warehouse, WarehouseCategory, WarehouseParts, \
    NotificationTemplate, NotificationEvents, Events

from tqdm import tqdm

from data.data import data_menu_rows, dataTableHeader, bages, data_setting_menu, data_group_statuses, data_statuses, data_roles, data_branches, data_counts, \
    data_cashboxes, data_item_payments, data_group_service, data_service, data_margin

from payments.alfa import alfa
from payments.tinkoff import tinkoff
from payments.fedreserv import fedreserv
from payments.kassa import kassa
from payments.obus import obus
from payments.sber import sber
from payments.seyf import seyf
from payments.yura import yura
from payments.anton import anton
from payments.alba import alba

from utils import GetListRO, GetCustomer, GetOders

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
print_logs = False


class DbInteraction():

    def __init__(self, host, port, user, password, db_name, rebuild_db=False):
        self.pgsql_connetction = PGSQL_connetction(
            host=host,
            port=port,
            user=user,
            password=password,
            db_name=db_name,
            rebuild_db=rebuild_db
        )

        self.rebuild_db = rebuild_db
        self.engine = self.pgsql_connetction.connection

    # Imported methods
    from ._orders import add_orders, get_orders, edit_orders, del_orders, get_order, get_orders_by_filter, get_order_by_id, add_order_comment
    from ._operations import add_operations, get_operations, edit_operations, del_operations
    from ._filters import get_badges, add_custom_filters, get_custom_filters, del_custom_filters
    from ._equipments import add_equipment_type, get_equipment_type, edit_equipment_type, del_equipment_type
    from ._equipments import add_equipment_brand, get_equipment_brand, edit_equipment_brand, del_equipment_brand
    from ._equipments import add_equipment_subtype, get_equipment_subtype, edit_equipment_subtype, del_equipment_subtype
    from ._equipments import add_equipment_model, get_equipment_model, edit_equipment_model, del_equipment_model
    from ._change_order_status import change_order_status
    from ._payments import add_payments, get_payments, edit_payments, del_payments
    from ._order_parts import add_oder_parts, get_oder_parts, edit_oder_parts, del_oder_parts
    from ._cashboxes import add_cashbox, get_cashbox, edit_cashbox, del_cashbox
    from ._payrolls import add_payroll, get_payrolls, get_payroll_sum, edit_payroll, del_payroll
    from ._branches import add_branch, get_branch, edit_branch, del_branch
    from ._employees import add_employee, get_employee, edit_employee, del_employee, cange_userpassword, change_avatar


    def create_all_tables(self):
        '''
        ?????????????? ?????????????? ?????? ?????????????? ???????????????? ?????????????? ??????????
        '''

        # if self.rebuild_db:
        # Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        # else:
        #     Base.metadata.create_all(self.engine)

    def create_tables(self, list_tables):
        Base.metadata.create_all(self.engine, tables=list_tables)

    def add_column(self, table_name, column):
        column_name = column.compile(dialect=self.engine.dialect)
        column_type = column.type.compile(self.engine.dialect)
        self.engine.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}')

    def cleanTable(self, Table):
        self.pgsql_connetction.session.query(Table).delete()
        self.pgsql_connetction.session.commit()

    def drop_all_tables(self):
        '''
        ?????????????? ?????????????? ?????? ??????????????
        '''
        # self.pgsql_connetction.execute_query(
        #     '''DROP DATABASE one_two;'''
        # )
        Base.metadata.drop_all(self.engine)

    def initial_data(self):
        # ???????????? ?????? ?????????????? ???? ????????
        self.drop_all_tables()
        print('?????? ?????????????? ??????????????')

        # ???????????????? ?????? ?????????????? ????????????
        self.create_all_tables()
        print('?????? ?????????????? ??????????????')

        # # ???????????????? ???????????????? ???????????? ????????????????
        self.add_generally_info(
            name='OneTwoService',
            address='??????????????????, ?????????????????? 179/1',
            email='onetwoservice@yandex.ru',

            ogrn='',
            inn='230815804505',
            kpp='',
            juridical_address='350049, ??. ??????????????????, ?????????? ???????????????????? ??????????????, ??. 9, ????. 17',
            director='???????????????????? ?????????????????? ??????????????????',
            bank_name='???????????? "????????????????????" ???? "??????????-????????"',
            settlement_account='40802810126240001808',
            corr_account='30101810500000000207',
            bic='046015207',

            description='???????????? ?????????????? ??????????????',
            phone='79528556886',
            logo=''
        )
        print('???????????????? ???????????? ???????????????? ??????????????')

        # ?????????????? ????????????????
        for count in data_counts:
            self.add_counts(
                prefix=count['prefix'],
                count=count['count'],
                description=count['description']
            )
        print('???????????????? ??????????????')

        # ???????????????? ?????????????????? ????????????????
        list_ad_campaign = ['???? ??????????????', '????????????????', '????????????????', '???????????????? ??????????????']
        for ad_campaign in list_ad_campaign:
            self.add_adCampaign(
                name=ad_campaign
            )
        print('?????????????????? ???????????????? ??????????????????')

        # ???????????????? ??????????????
        for branch in data_branches:
            branch_id = self.add_branch(
                name=branch['name'],
                color=branch['color'],
                address=branch['address'],
                phone=branch['phone'],
                icon=branch['icon'],
                orders_type_id=branch['orders_type_id'],
                orders_type_strategy=branch['orders_type_strategy'],
                orders_prefix=branch['orders_prefix'],
                documents_prefix=branch['documents_prefix'],
                employees=branch['employees'],
                deleted=branch['deleted']
            )
            for day in range(1, 8):
                self.add_schedule(
                    start_time='9:00',
                    end_time='18:00',
                    work_day=True if day != 7 else False,
                    week_day=day,
                    branch_id=branch_id
                )
        print('?????????????? ??????????????????')

        # ???????????????? ???????? ??????????????
        list_order_type = ['?? ????????????????????', '???? ????????????']
        for order_type in list_order_type:
            self.add_order_type(
                name=order_type
            )
        print('???????? ?????????????? ??????????????????')

        # ???????????????? ???????????? ????????????????
        for group in data_group_statuses:
            self.add_status_group(
                name=group['name'],
                type_group=group['type_group'],
                color=group['color']
            )
        print('???????????? ???????????????? ??????????????????')

        # ???????????????????????????? ??????????????
        for status in data_statuses:
            self.add_status(
                name=status.get('name'),
                color=status.get('color'),
                group=status.get('group'),
                deadline=status.get('deadline'),
                comment_required=status.get('comment_required'),
                payment_required=status.get('payment_required'),
                available_to=status.get('available_to')
            )
        print('?????????????? ????????????????????????????????')

        # ???????????????? ?????????????? ????????
        for row in data_menu_rows:
            self.add_menu_row(
                title=row['title'],
                img=row['image'],
                url=row['url'],
                group_name=row['group_name']
            )
        print('???????????? ???????? ??????????????????')

        # ???????????????? ?????????????? ???????? ????????????????
        for row in data_setting_menu:
            self.add_setting_menu(
                title=row['title'],
                url=row['url'],
                group_name=row['group_name']
            )
        print('???????????? ???????? ???????????????? ??????????????????')

        # ???????????????? ???????????? ?? ???????????????????? ??????????????
        self.add_equipment_type(
            title='-',
            icon=None,
            url=None,
            deleted=False,
            branches=[1, 2]
        )

        self.add_equipment_brand(
            title='-',
            equipment_type_id=1,
            icon=None,
            url=None,
            deleted=False,
            branches=[1, 2]
        )

        self.add_equipment_subtype(
            title='-',
            equipment_brand_id=1,
            icon=None,
            url=None,
            deleted=False,
            branches=[1, 2]
        )
        self.add_equipment_model(
            title='-',
            equipment_subtype_id=1,
            icon=None,
            url=None,
            deleted=False,
            branches=[1, 2]
        )

        # ???????????????? ????????
        for role in data_roles:
            self.add_role(
                title=role.get('title'),
                earnings_visibility=role.get('earnings_visibility'),
                leads_visibility=role.get('leads_visibility'),
                orders_visibility=role.get('orders_visibility'),
                permissions=role.get('permissions'),
                settable_statuses=role.get('settable_statuses'),
                visible_statuses=role.get('visible_statuses'),
                settable_discount_margin=role.get('settable_discount_margin')
            )

        # ?????????????? ??????????
        for cashbox in data_cashboxes:
            self.add_cashbox(
                title=cashbox.get('title'),
                balance=cashbox.get('balance'),
                type=cashbox.get('type'),
                isGlobal=cashbox.get('isGlobal'),
                isVirtual=cashbox.get('isVirtual'),
                deleted=cashbox.get('deleted'),
                permissions=cashbox.get('permissions'),
                employees=cashbox.get('employees'),
                branch_id=cashbox.get('branch_id')
            )
        print('?????????? ??????????????')

        # ?????????????? ???????????? ??????
        for item_payment in data_item_payments:
            self.add_item_payments(
                title=item_payment.get('title'),
                direction=item_payment.get('direction')
            )
        print('???????????????? ?????? ??????????????????')

        # ?????????????? ??????????????
        for margin in data_margin:
            self.add_discount_margin(
                title=margin.get('title'),
                margin=margin.get('margin'),
                margin_type=margin.get('margin_type'),
                deleted=margin.get('deleted')
            )
        print('?????????????? ????????????????????????????????')

        # ?????????????? ?????????????????? ??????????
        for group in data_group_service:
            self.add_group_dict_service(
                title=group.get('title'),
                icon=group.get('icon'),
                deleted=group.get('deleted')
            )
        print('?????????????????? ?????????? ??????????????????')

        # ?????????????? ????????????
        for service in data_service:
            self.add_dict_service(
                title=service.get('title'),
                price=service.get('price'),
                cost=service.get('cost'),
                warranty=service.get('warranty'),
                code=service.get('code'),
                earnings_percent=service.get('earnings_percent'),
                earnings_summ=service.get('earnings_summ'),
                deleted=service.get('deleted'),
                category_id=service.get('category_id')
            )
        print('???????????? ??????????????????')

    def update_date_from_remonline(self):
        # ???????????????????????????? ???????????? ?? ??????????????????????
        list_employee = GetListRO('empoyees')
        for employee in list_employee:
            self.add_employee(
                first_name=employee.get('first_name'),
                last_name=employee.get('last_name'),
                email=employee.get('email'),
                notes=employee.get('notes'),
                phone=employee.get('phone'),
                password=generate_password_hash('225567') if employee.get(
                    'email') == 'stasmen@mail.ru' else generate_password_hash('12345'),
                deleted=not employee.get('email') in ['stasmen@mail.ru', 'p.s.respekt@mail.ru',
                                                      'potato316bless@gmail.com', 'Stepanenkoyura353@mail.ru'],
                inn=None,
                doc_name=None,
                post=None,
                permissions=[],
                role_id=1 if employee.get('email') == 'stasmen@mail.ru' else 2,
                login=None
            )
            imployee_id = self.get_employee(email=employee.get('email'))['data'][0]['id']
            for head in dataTableHeader:
                self.add_table_headers(
                    title=head['title'],
                    field=head['field'],
                    width=head['width'],
                    employee_id=imployee_id
                )
        print('???????????? ?? ?????????????????????? ????????????????????????????????')

        # ???????????????? ??????????
        for row in bages:
            self.add_badges(
                title=row['title'],
                color=row['color'],
                img=row['image']
            )
        print('?????????? ??????????????????')

        list_client = GetCustomer(page='all')
        for client in tqdm(list_client, desc='???????????????????? ?? ???????? ????????????', position=0):
            id_create_client = self.add_clients(
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
                self.add_phone(
                    number=phone,
                    title='??????????????????',
                    client_id=id_create_client
                )
        print('?????????????? ????????????????????????????????')

        # ?????????????? ????????????
        n = 0
        list_orders = GetOders()
        for order in tqdm(list_orders, desc='???????????????????? ?? ???????? ????????????', position=0):

            equipment_type = self.pgsql_connetction.session.query(EquipmentType).filter(
                EquipmentType.title == order.get('kindof_good').strip()
            ).first()
            # equipment_type_id = equipment_type.id if equipment_type else 1,
            if equipment_type:
                equipment_type_id = equipment_type.id
            else:
                equipment_type_id = self.add_equipment_type(
                    title=order.get('kindof_good').strip(),
                    icon=None,
                    url=None,
                    branches=[1, 2],
                    deleted=False
                )

            equipment_brand = self.pgsql_connetction.session.query(EquipmentBrand).filter(
                and_(
                    EquipmentBrand.title == order['custom_fields'].get('f718512').strip(),
                    EquipmentBrand.equipment_type_id == equipment_type_id
                )
            ).first()
            if equipment_brand:
                equipment_brand_id = equipment_brand.id
            else:
                equipment_brand_id = self.add_equipment_brand(
                    title=order['custom_fields'].get('f718512').strip(),
                    icon=None,
                    url=None,
                    branches=[1, 2],
                    deleted=False,
                    equipment_type_id=equipment_type_id
                )

            equipment_subtype = self.pgsql_connetction.session.query(EquipmentSubtype).filter(
                and_(
                    EquipmentSubtype.title == '-',
                    EquipmentSubtype.equipment_brand_id == equipment_brand_id
                )
            ).first()
            if equipment_subtype:
                equipment_subtype_id = equipment_subtype.id
            else:
                equipment_subtype_id = self.add_equipment_subtype(
                    title='-',
                    icon=None,
                    url=None,
                    branches=[1, 2],
                    deleted=False,
                    equipment_brand_id=equipment_brand_id
                )

            equipment_model = self.pgsql_connetction.session.query(EquipmentModel).filter(
                and_(
                    EquipmentModel.title == order.get('model').strip(),
                    EquipmentModel.equipment_subtype_id == equipment_subtype_id
                )
            ).first()
            if equipment_model:
                equipment_model_id = equipment_model.id
            else:
                equipment_model_id = self.add_equipment_model(
                    title=order.get('model').strip(),
                    icon=None,
                    url=None,
                    branches=[1, 2],
                    deleted=False,
                    equipment_subtype_id=equipment_subtype_id
                )

            id_order = self.add_orders(
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
                status_id=self.get_status(name=order['status']['name'])['data'][0]['id'] if
                self.get_status(name=order['status']['name'])['data'] else None,
                client_id=self.get_clients(name=order['client']['name'])['data'][0]['id'] if order.get('client') and
                                                                                             self.get_clients(
                                                                                                 name=order['client'][
                                                                                                     'name'])[
                                                                                                 'data'] else None,
                order_type_id=self.get_order_type(name=order['order_type']['name'])['data'][0]['id'] if order.get(
                    'order_type') else None,
                closed_by_id=dict_emploeey_ids[str(order.get('closed_by_id'))] if order.get('closed_by_id') else None,
                created_by_id=dict_emploeey_ids[str(order.get('created_by_id'))] if order.get(
                    'created_by_id') else None,
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
                packagelist=order.get('packagelist') if order.get('packagelist') else order['custom_fields'].get(
                    'f718508'),
                appearance=order.get('appearance'),
                manager_notes=order.get('manager_notes'),
                engineer_notes=order.get('engineer_notes'),
                resume=order.get('resume'),
                cell=None,

                estimated_cost=order.get('estimated_cost', 0) if (type(order.get('estimated_cost', 0)) == int or type(
                    order.get('estimated_cost', 0)) == float) else 0,
                missed_payments=order.get('missed_payments', 0),
                discount_sum=order.get('discount_sum', 0),
                payed=order.get('payed', 0),
                price=order.get('price', 0),

                urgent=order.get('urgent')
            )

            # id_order = self.get_orders(id_label=order['id_label'])['data'][0]['id'] if \
            # self.get_orders(id_label=order['id_label'])['data'] else print(f'???? ????????????: {order["id_label"]}')
            if order.get('operations'):
                for operation in order.get('operations'):
                    self.add_operations(
                        amount=operation.get('amount'),
                        cost=operation.get('cost'),
                        discount_value=operation.get('discount_value'),
                        engineer_id=dict_emploeey_ids[str(operation.get('engineer_id'))] if operation.get(
                            'engineer_id') else None,
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
                    self.add_oder_parts(
                        amount=part.get('amount'),
                        cost=part.get('cost'),
                        discount_value=part.get('discount_value'),
                        engineer_id=dict_emploeey_ids[str(part.get('engineer_id'))] if part.get(
                            'engineer_id') else None,
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
                    self.add_attachments(
                        created_by_id=dict_emploeey_ids[str(attachment.get('created_by_id'))] if attachment.get(
                            'created_by_id') else None,
                        created_at=attachment.get('created_at') / 1000 if attachment.get('created_at') else None,
                        filename=attachment.get('filename'),
                        url=attachment.get('url'),
                        order_id=id_order
                    )
            n += 1
            if n == len(list_orders):
                index = int(order['id_label'][4:])
                self.edit_counts(id=1, count=index + 1, prefix=None, description=None)

        print('???????????? ??????????????????')

        # ?????????????? ??????????????
        regex_lable = re.compile('OTS-\d+')
        data_payments = [
            {
                'data': alfa,
                'title': '???????????????????? ?????????? ???????? 2018',
                'cashbox_id': 4
                # }, {
                #     'data': alfa2019,
                #     'title': '???????????????????? ?????????? ???????? 2019',
                #     'cashbox_id': 4
                # }, {
                #     'data': alfa2020,
                #     'title': '???????????????????? ?????????? ???????? 2020',
                #     'cashbox_id': 4
                # }, {
                #     'data': alfa2021,
                #     'title': '???????????????????? ?????????? ???????? 2021',
                #     'cashbox_id': 4
            }, {
                'data': fedreserv,
                'title': '???????????????????? ?????????????????????? ????????????',
                'cashbox_id': 7
            }, {
                'data': kassa,
                'title': '???????????????????? ?????????? 2018',
                'cashbox_id': 1
                # }, {
                #     'data': kassa2019_1,
                #     'title': '???????????????????? ?????????? 2019_1',
                #     'cashbox_id': 1
                # }, {
                #     'data': kassa2019_2,
                #     'title': '???????????????????? ?????????? 2019_2',
                #     'cashbox_id': 1
                # }, {
                #     'data': kassa2019_3,
                #     'title': '???????????????????? ?????????? 2019_3',
                #     'cashbox_id': 1
                # }, {
                #     'data': kassa2020,
                #     'title': '???????????????????? ?????????? 2020',
                #     'cashbox_id': 1
                # }, {
                #     'data': kassa2021,
                #     'title': '???????????????????? ?????????? 2021',
                #     'cashbox_id': 1
            }, {
                'data': obus,
                'title': '???????????????????? ????????????????????????',
                'cashbox_id': 6
            }, {
                'data': sber,
                'title': '???????????????????? ????????????????',
                'cashbox_id': 3
            }, {
                'data': seyf,
                'title': '???????????????????? ????????',
                'cashbox_id': 5
            }, {
                'data': tinkoff,
                'title': '???????????????????? ????????????????',
                'cashbox_id': 2
            }, {
                'data': anton,
                'title': '???????????????????? ?????????? ??????????',
                'cashbox_id': 8
            }, {
                'data': yura,
                'title': '???????????????????? ?????????? ??????',
                'cashbox_id': 9
            }, {
                'data': alba,
                'title': '???????????????????? ?????????? ??????????????',
                'cashbox_id': 10
            }
        ]
        for data in data_payments:
            for payment in tqdm(data['data'], position=0, desc=data['title']):
                self.add_payments(
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
                    client_id=self.get_clients(name=payment['client']['name'])['data'][0]['id'] if payment.get(
                        'client') and self.get_clients(name=payment['client']['name'])['data'] else None,
                    employee_id=dict_emploeey_ids[str(payment['employee'].get('id'))],
                    order_id=self.get_orders(id_label=regex_lable.findall(payment['description'])[0])['data'][0][
                        'id'] if regex_lable.findall(payment['description']) and
                                 self.get_orders(id_label=regex_lable.findall(payment['description'])[0])[
                                     'data'] else None
                )
        # for cashbox_id in range(1, 7):
        #     self.change_payment_deposit(
        #         start_date=0,
        #         cashbox_id=cashbox_id
        #     )

    def reset_dict(self):
        list_malfunction = []
        list_packege = []
        for page in tqdm(range(260), desc='???????????????? ???????????????? ???? ???????? ??????????????', position=0):
            orders = self.get_orders(page=page)
            for order in orders['data']:
                malfunction = order.get('malfunction')
                packagelist = order.get('packagelist')
                if malfunction:
                    list_malfunction.append(malfunction)
                if packagelist:
                    list_packege.append(packagelist)

        count_malfunction = dict((x, list_malfunction.count(x)) for x in set(list_malfunction))
        count_packege = dict((x, list_packege.count(x)) for x in set(list_packege))

        for key, val in tqdm(count_malfunction.items(), desc='?????????????????? ?????????????? ????????????????????????????', position=0):
            self.add_malfunction(
                title=key,
                count=val
            )

        for key, val in tqdm(count_packege.items(), desc='?????????????????? ?????????????? ????????????????????????', position=0):
            self.add_packagelist(
                title=key,
                count=val
            )
        print('?????? ?????????????? ??????????????')

    # ?????????????? ?????????????????? ???????????????? ===========================================================================

    def add_adCampaign(self, name):
        '''
        ?????????????????? ???????????? ?? ?????????????????? ????????????????
        :param name: ?????? ?????????????????? ????????????????
        '''
        adCampaign = AdCampaign(
            name=name
        )
        self.pgsql_connetction.session.add(adCampaign)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(adCampaign)
        return adCampaign.id

    def get_adCampaign(self, id=None, name=None, page=0):
        '''
        ???????????????????? ???????????? ?? ?????????????????????? ???????????????????? ???????????? ???? ???????? ???????????? ?????????????????? ????????????????
        :param id: ID ?????????????????? ???????????????? ?????? ?????????? ?? ???????? ????????????
        :param name: ?????? ?????????????????? ???????????????? ?????? ???????????? ?? ???????? ????????????
        :return: ?????????? ?? ??????????????:
                    count - ???????????????????? ???????????????? ??????????????
                    data: - ???????????? ?????????????? json (???????????? ??????????????)
        '''
        if id or name:
            adCampaign = self.pgsql_connetction.session.query(AdCampaign).filter(
                and_(
                    AdCampaign.id == id if id else True,
                    AdCampaign.name.like(f'%{name}%') if name else True,
                )
            )
        else:
            adCampaign = self.pgsql_connetction.session.query(AdCampaign)

        # self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = adCampaign.count()
        result['count'] = count

        max_page = count // 50 if count % 50 > 0 else count // 50 - 1

        if page > max_page and max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []
        for row in adCampaign[50 * page: 50 * (page + 1)]:
            data.append({
                'id': row.id,
                'name': row.name
            })

        result['data'] = data
        result['page'] = page
        return result

    def edit_adCampaign(self, id, name=None):
        '''
        ???????????? ???????????????????? ?? ?????????????? ?????????????????? ???????????????? ???????? ????????????
        :param id: ID ????????????
        :param name: ?????????? ???????? ?????? ?????????? ?? ????????????
        '''
        self.pgsql_connetction.session.query(AdCampaign).filter_by(id=id).update({
            'name': name if name is not None else AdCampaign.name
        })
        self.pgsql_connetction.session.commit()
        return self.get_adCampaign()

    def del_adCampaign(self, id):
        '''
        ?????????????? ???????????? ?? ?????????????????? ID ???? ?????????????? ?????????????????? ????????????????
        :param id: ID ????????????
        '''
        adCampaign = self.pgsql_connetction.session.query(AdCampaign).get(id)
        if adCampaign:
            self.pgsql_connetction.session.delete(adCampaign)
            self.pgsql_connetction.session.commit()
            return self.get_adCampaign()

    #  ?????????????? ???????????????????? ==================================================================================


    # ?????????????? ???????????????? ==================================================================================

    def add_attachments(self, created_by_id, created_at, filename, url, order_id):
        attachments = Attachments(
            created_by_id=created_by_id,
            created_at=created_at,
            filename=filename,
            url=url,
            order_id=order_id
        )
        self.pgsql_connetction.session.add(attachments)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(attachments)
        return attachments.id

    def get_attachments(self,
                        id=None,
                        created_by_id=None,
                        created_at=None,
                        updated_at=None,
                        filename=None,
                        url=None,
                        order_id=None,
                        page=0):

        if any([id, created_by_id, created_at, updated_at, filename, url, order_id]):
            attachments = self.pgsql_connetction.session.query(Attachments).filter(

                Attachments.id == id if id else True,
                Attachments.filename.like(f'%{filename}%') if filename else True,
                (Attachments.created_at >= created_at[0] if created_at[0] else True) if created_at else True,
                (Attachments.created_at <= created_at[1] if created_at[1] else True) if created_at else True,
                Attachments.order_id == order_id if order_id else True,
            )
        else:
            attachments = self.pgsql_connetction.session.query(Attachments)

        self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = attachments.count()
        result['count'] = count

        max_page = count // 50 if count % 50 > 0 else count // 50 - 1

        if page > max_page and max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []
        for row in attachments[50 * page: 50 * (page + 1)]:
            data.append({
                'id': row.id,
                'created_by_id': row.created_by_id,
                'created_at': row.created_at,
                'updated_at': row.updated_at,
                'filename': row.filename,
                'url': row.url,
                'order_id': row.order_id
            })

        result['data'] = data
        result['page'] = page
        return result

    def edit_attachments(self, id, created_by_id, created_at, filename, url, order_id):
        self.pgsql_connetction.session.query(Attachments).filter_by(id=id if type(id) == int else None).update({
            'created_by_id': created_by_id if created_by_id is not None else Attachments.created_by_id,
            'created_at': created_at if created_at is not None else Attachments.created_at,
            'filename': filename if filename is not None else Attachments.filename,
            'url': url if url is not None else Attachments.url,
            'order_id': order_id if order_id is not None else Attachments.order_id
        })
        return self.get_attachments()

    def del_attachments(self, id):
        attachments = self.pgsql_connetction.session.query(Attachments).get(id if type(id) == int else 0)
        if attachments:
            self.pgsql_connetction.session.delete(attachments)
            self.pgsql_connetction.session.commit()
            return self.get_attachments()

    # ?????????????? ???????? ???????????????????? =========================================================================

    def add_schedule(self, start_time, end_time, work_day, week_day, branch_id):

        schedule = Schedule(
            start_time=start_time,
            end_time=end_time,
            work_day=work_day,
            week_day=week_day,
            branch_id=branch_id
        )
        self.pgsql_connetction.session.add(schedule)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(schedule)
        return schedule.id

    def get_schedule(self, id=None, branch_id=None):

        if any([id, branch_id]):
            schedule = self.pgsql_connetction.session.query(Schedule).filter(
                and_(
                    Schedule.id == id if id else True,
                    Schedule.branch_id == branch_id if branch_id else True
                )
            )
        else:
            schedule = self.pgsql_connetction.session.query(Schedule)

        self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = schedule.count()
        result['count'] = count

        data = []
        for row in schedule:
            data.append({
                'id': row.id,
                'start_time': row.start_time,
                'end_time': row.end_time,
                'work_day': row.work_day,
                'week_day': row.week_day,
                'branch_id': row.branch_id
            })

        result['data'] = data
        return result

    def edit_schedule(self, id, start_time, end_time, work_day, week_day, branch_id):

        self.pgsql_connetction.session.query(Schedule).filter_by(id=id).update({
            'start_time': start_time if start_time is not None else Schedule.start_time,
            'end_time': end_time if end_time is not None else Schedule.end_time,
            'work_day': work_day if work_day is not None else Schedule.work_day,
            'week_day': week_day if week_day is not None else Schedule.week_day,
            'branch_id': branch_id if branch_id is not None else Schedule.branch_id
        })
        self.pgsql_connetction.session.commit()
        return self.get_schedule(id=id)

    def del_schedule(self, id):

        schedule = self.pgsql_connetction.session.query(Schedule).get(id)
        if schedule:
            self.pgsql_connetction.session.delete(schedule)
            self.pgsql_connetction.session.commit()
            return self.get_schedule()

    # ?????????????? ?????????????? ==================================================================================

    def add_discount_margin(self, title, margin, deleted, margin_type):

        discount_margin = DiscountMargin(
            title=title,
            margin=margin,
            margin_type=margin_type,
            deleted=deleted
        )
        self.pgsql_connetction.session.add(discount_margin)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(discount_margin)
        return discount_margin.id

    def get_discount_margin(self, id=None, title=None, margin_type=None, deleted=None, page=0):

        if any([id, title, margin_type, deleted]):
            discount_margin = self.pgsql_connetction.session.query(DiscountMargin).filter(
                and_(
                    DiscountMargin.id == id if id else True,
                    DiscountMargin.margin_type == margin_type if margin_type else True,
                    DiscountMargin.title.like(f'%{title}%') if title else True,
                    (deleted or DiscountMargin.deleted.is_(False)) if deleted != None else True
                )
            )
        else:
            discount_margin = self.pgsql_connetction.session.query(DiscountMargin)

        self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = discount_margin.count()
        result['count'] = count

        max_page = count // 50 if count % 50 > 0 else count // 50 - 1

        if page > max_page and max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []
        for row in discount_margin[50 * page: 50 * (page + 1)]:
            data.append({
                'id': row.id,
                'title': row.title,
                'margin': row.margin,
                'margin_type': row.margin_type,
                'deleted': row.deleted
            })

        result['data'] = data
        result['page'] = page
        return result

    def edit_discount_margin(self, id, title, margin, deleted, margin_type):

        self.pgsql_connetction.session.query(DiscountMargin).filter_by(id=id).update({
            'title': title if title is not None else DiscountMargin.title,
            'margin': margin if margin is not None else DiscountMargin.margin,
            'margin_type': margin_type if margin_type is not None else DiscountMargin.margin_type,
            'deleted': deleted if deleted is not None else DiscountMargin.deleted
        })
        self.pgsql_connetction.session.commit()
        return self.get_discount_margin()

    def del_discount_margin(self, id):

        discount_margin = self.pgsql_connetction.session.query(DiscountMargin).get(id)
        if discount_margin:
            self.pgsql_connetction.session.delete(discount_margin)
            self.pgsql_connetction.session.commit()
            return self.get_discount_margin()

    # ?????????????? ?????????? ???????????? ==================================================================================

    def add_order_type(self, name):

        order_type = OrderType(
            name=name
        )
        self.pgsql_connetction.session.add(order_type)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(order_type)
        return order_type.id

    def get_order_type(self, id=None, name=None, page=0):

        if id or name:
            order_type = self.pgsql_connetction.session.query(OrderType).filter(
                and_(
                    OrderType.id == id if id else True,
                    OrderType.name.like(f'%{name}%') if name else True,
                )
            )
        else:
            order_type = self.pgsql_connetction.session.query(OrderType)

        self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = order_type.count()
        result['count'] = count

        max_page = count // 50 if count % 50 > 0 else count // 50 - 1

        if page > max_page and max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []
        for row in order_type[50 * page: 50 * (page + 1)]:
            data.append({
                'id': row.id,
                'name': row.name
            })

        result['data'] = data
        result['page'] = page
        return result

    def edit_order_type(self, id, name):

        self.pgsql_connetction.session.query(OrderType).filter_by(id=id).update({
            'name': name if name is not None else OrderType.name
        })
        self.pgsql_connetction.session.commit()
        return self.get_order_type()

    def del_order_type(self, id):

        order_type = self.pgsql_connetction.session.query(OrderType).get(id)
        if order_type:
            self.pgsql_connetction.session.delete(order_type)
            self.pgsql_connetction.session.commit()
            return self.get_order_type()

    # ?????????????? ???????????? ???????????????? ==================================================================================

    def add_status_group(self, name, type_group, color):

        status_group = StatusGroup(
            name=name,
            type_group=type_group,
            color=color
        )
        self.pgsql_connetction.session.add(status_group)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(status_group)
        return status_group.id

    def get_status_group(self, id=None, name=None, type_group=None, page=0):
        if id or name or type_group:
            status_group = self.pgsql_connetction.session.query(StatusGroup).filter(
                and_(
                    StatusGroup.id == id if id else True,
                    StatusGroup.name.like(f'%{name}%') if name else True,
                    StatusGroup.type_group == type_group if type_group else True
                )
            )
        else:
            status_group = self.pgsql_connetction.session.query(StatusGroup)

        self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = status_group.count()
        result['count'] = count

        max_page = count // 50 if count % 50 > 0 else count // 50 - 1

        if page > max_page and max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []
        for row in status_group[50 * page: 50 * (page + 1)]:
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
        result['data'] = data
        result['page'] = page
        return result

    def edit_status_group(self, id, name, type_group, color):

        self.pgsql_connetction.session.query(StatusGroup).filter_by(id=id).update({
            'name': name if name is not None else StatusGroup.name,
            'type_group': type_group if type_group is not None else StatusGroup.type_group,
            'color': color if color is not None else StatusGroup.color,
        })
        self.pgsql_connetction.session.commit()
        return self.get_status_group()

    def del_status_group(self, id):

        status_group = self.pgsql_connetction.session.query(StatusGroup).get(id)
        if status_group:
            self.pgsql_connetction.session.delete(status_group)
            self.pgsql_connetction.session.commit()
            return self.get_status_group()

    # ?????????????? ???????????????? ==================================================================================

    def add_status(self, name, color, group, deadline, comment_required, payment_required, available_to):

        status = Status(
            name=name,
            color=color,
            group=group,
            deadline=deadline,
            comment_required=comment_required,
            payment_required=payment_required,
            available_to=available_to
        )
        self.pgsql_connetction.session.add(status)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(status)
        return status.id

    def get_status(self, id=None, name=None, color=None, group=None, page=0):
        if any([id, name, color, group]):
            status = self.pgsql_connetction.session.query(Status).filter(
                and_(
                    Status.id == id if id else True,
                    Status.name.like(f'%{name}%') if name else True,
                    Status.color == color if color else True,
                    Status.group == group if group else True,
                )
            )
        else:
            status = self.pgsql_connetction.session.query(Status)

        self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = status.count()
        result['count'] = count

        max_page = count // 50 if count % 50 > 0 else count // 50 - 1

        if page > max_page and max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []
        for row in status[50 * page: 50 * (page + 1)]:
            data.append({
                'id': row.id,
                'name': row.name,
                'color': row.color,
                'group': row.group,
                'deadline': row.deadline,
                'comment_required': row.comment_required,
                'payment_required': row.payment_required,
                'available_to': row.available_to
            })
        result['data'] = data
        result['page'] = page
        return result

    def edit_status(self, id, name, color, group, deadline, comment_required, payment_required, available_to):

        self.pgsql_connetction.session.query(Status).filter_by(id=id).update({
            'name': name if name is not None else Status.name,
            'color': color if color is not None else Status.color,
            'group': group if group is not None else Status.group,
            'deadline': deadline if deadline is not None else Status.deadline,
            'comment_required': comment_required if comment_required is not None else Status.comment_required,
            'payment_required': payment_required if payment_required is not None else Status.payment_required,
            'available_to': available_to if available_to is not None else Status.available_to
        })
        self.pgsql_connetction.session.commit()
        return self.get_status()

    def del_status(self, id):

        status = self.pgsql_connetction.session.query(Status).get(id)
        if status:
            self.pgsql_connetction.session.delete(status)
            self.pgsql_connetction.session.commit()
            return id




    # ?????????????? ?????????????????? ==================================================================================

    def add_phone(self, number, title, notify, client_id):

        phones = Phones(
            number=number,
            title=title,
            notify=notify,
            client_id=client_id
        )
        self.pgsql_connetction.session.add(phones)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(phones)
        return phones.id

    def get_phones(self, id=None, number=None, title=None, client_id=None, page=0):

        if any([id, number, title, client_id]):
            phones = self.pgsql_connetction.session.query(Phones).filter(
                and_(
                    Phones.id == id if id else True,
                    Phones.number.like(f'%{number}%') if number else True,
                    Phones.title.like(f'%{title}%') if title else True,
                    Phones.client_id == client_id if client_id else True,
                )
            )
        else:
            phones = self.pgsql_connetction.session.query(Phones)

        self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = phones.count()
        result['count'] = count

        max_page = count // 50 if count % 50 > 0 else count // 50 - 1

        if page > max_page and max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []
        for row in phones[50 * page: 50 * (page + 1)]:
            data.append({
                'id': row.id,
                'number': row.number,
                'title': row.title,
                'notify': row.notify,
                'client_id': row.client_id
            })

        result['data'] = data
        result['page'] = page
        return result

    def edit_phones(self, id, number=None, title=None, notify=None, client_id=None):

        self.pgsql_connetction.session.query(Phones).filter_by(id=id).update({
            'number': number if number is not None else Phones.number,
            'title': title if title is not None else Phones.title,
            'notify': notify if notify is not None else Phones.notify,
            'client_id': client_id if client_id is not None else Phones.client_id
        })
        self.pgsql_connetction.session.commit()
        return id

    def del_phones(self, id):

        phones = self.pgsql_connetction.session.query(Phones).get(id)
        if phones:
            self.pgsql_connetction.session.delete(phones)
            self.pgsql_connetction.session.commit()
            return self.get_phones()

    # ?????????????? ???????????????? ==================================================================================

    def add_clients(self,
                    juridical,
                    supplier,
                    conflicted,
                    should_send_email,
                    deleted,
                    discount_good_type,
                    discount_materials_type,
                    discount_service_type,

                    name,
                    name_doc,
                    email,
                    address,
                    discount_code,
                    notes,
                    ogrn,
                    inn,
                    kpp,
                    juridical_address,
                    director,
                    bank_name,
                    settlement_account,
                    corr_account,
                    bic,

                    discount_goods,
                    discount_materials,
                    discount_services,

                    ad_campaign_id,
                    discount_goods_margin_id,
                    discount_materials_margin_id,
                    discount_service_margin_id,

                    tags,
                    created_at
                    ):

        clients = Clients(
            juridical=juridical,
            supplier=supplier,
            conflicted=conflicted,
            should_send_email=should_send_email,
            deleted=deleted,
            discount_good_type=discount_good_type,
            discount_materials_type=discount_materials_type,
            discount_service_type=discount_service_type,

            name=name,
            name_doc=name_doc,
            email=email,
            address=address,
            discount_code=discount_code,
            notes=notes,
            ogrn=ogrn,
            inn=inn,
            kpp=kpp,
            juridical_address=juridical_address,
            director=director,
            bank_name=bank_name,
            settlement_account=settlement_account,
            corr_account=corr_account,
            bic=bic,

            discount_goods=discount_goods,
            discount_materials=discount_materials,
            discount_services=discount_services,

            ad_campaign_id=ad_campaign_id,
            discount_goods_margin_id=discount_goods_margin_id,
            discount_materials_margin_id=discount_materials_margin_id,
            discount_service_margin_id=discount_service_margin_id,

            tags=tags,
            created_at=created_at
        )
        self.pgsql_connetction.session.add(clients)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(clients)
        return clients.id

    def get_clients(self,
                    id=None,
                    # ad_campaign_id=None,
                    # address=None,
                    conflicted=None,
                    deleted=None,
                    # name_doc=None,
                    # discount_code=None,
                    # discount_goods=None,
                    # discount_goods_margin_id=None,
                    # discount_materials=None,
                    # discount_materials_margin_id=None,
                    # discount_services=None,
                    email=None,
                    juridical=None,
                    # created_at=None,
                    name=None,
                    # notes=None,
                    supplier=None,
                    phone=None,
                    page=0):

        if any([id, name, conflicted != None, email, juridical != None, supplier != None, deleted != None, phone]):
            clients = self.pgsql_connetction.session.query(Clients).join(Clients.phone).filter(
                and_(
                    Clients.id == id if id else True,
                    Clients.name.ilike(f'%{name}%') if name else True,
                    # Clients.ad_campaign_id == ad_campaign_id if ad_campaign_id else True,
                    # Clients.address.like(f'%{address}%') if address else True,
                    Clients.conflicted == conflicted if conflicted != None else True,
                    # Clients.name_doc.like(f'%{name_doc}%') if name_doc else True,
                    # Clients.discount_code.like(f'%{discount_code}%') if discount_code else True,
                    # Clients.discount_goods == discount_goods if discount_goods else True,
                    # Clients.discount_goods_margin_id == discount_goods_margin_id if discount_goods_margin_id else True,
                    # Clients.discount_materials == discount_materials if discount_materials else True,
                    # Clients.discount_materials_margin_id == discount_materials_margin_id if discount_materials_margin_id else True,
                    # Clients.discount_services == discount_services if discount_services else True,
                    Clients.email.ilike(f'%{email}%') if email else True,
                    # (Clients.created_at >= created_at[0] if created_at[0] else True) if created_at else True,
                    # (Clients.created_at <= created_at[1] if created_at[1] else True) if created_at else True,
                    Clients.juridical == juridical if juridical != None else True,
                    (deleted or Clients.deleted.is_(False)) if deleted != None else True,
                    # Clients.notes.like(f'%{notes}%') if notes else True,
                    Clients.supplier == supplier if supplier != None else True,
                    Clients.phone.property.mapper.class_.number.ilike(f'%{phone}%') if phone else True,
                )
            )
        else:
            clients = self.pgsql_connetction.session.query(Clients)

        # self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = clients.count()
        result['count'] = count

        max_page = count // 50 if count % 50 > 0 else count // 50 - 1

        if page > max_page and max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []
        for row in clients[50 * page: 50 * (page + 1)]:
            data.append({
                'id': row.id,
                'juridical': row.juridical,
                'supplier': row.supplier,
                'conflicted': row.conflicted,
                'should_send_email': row.should_send_email,
                'deleted': row.deleted,
                'discount_good_type': row.discount_good_type,
                'discount_materials_type': row.discount_materials_type,
                'discount_service_type': row.discount_service_type,

                'name': row.name,
                'name_doc': row.name_doc,
                'email': row.email,
                'address': row.address,
                'discount_code': row.discount_code,
                'notes': row.notes,
                'ogrn': row.ogrn,
                'inn': row.inn,
                'kpp': row.kpp,
                'juridical_address': row.juridical_address,
                'director': row.director,
                'bank_name': row.bank_name,
                'settlement_account': row.settlement_account,
                'corr_account': row.corr_account,
                'bic': row.bic,

                'discount_goods': row.discount_goods,
                'discount_materials': row.discount_materials,
                'discount_services': row.discount_services,

                'discount_goods_margin_id': row.discount_goods_margin_id,
                'discount_materials_margin_id': row.discount_materials_margin_id,
                'discount_service_margin_id': row.discount_service_margin_id,

                'tags': row.tags,
                'created_at': row.created_at,
                'phone': [{
                    'id': ph.id,
                    'number': ph.number,
                    'title': ph.title,
                    'notify': ph.notify
                } for ph in row.phone] if row.phone else [],
                'ad_campaign': {
                    'id': row.ad_campaign.id,
                    'name': row.ad_campaign.name
                }
            })

        result['data'] = data
        result['page'] = page
        # self.pgsql_connetction.session.close()
        return result

    def edit_clients(self,
                     id,
                     juridical=None,
                     supplier=None,
                     conflicted=None,
                     should_send_email=None,
                     deleted=None,
                     discount_good_type=None,
                     discount_materials_type=None,
                     discount_service_type=None,

                     name=None,
                     name_doc=None,
                     email=None,
                     address=None,
                     discount_code=None,
                     notes=None,
                     ogrn=None,
                     inn=None,
                     kpp=None,
                     juridical_address=None,
                     director=None,
                     bank_name=None,
                     settlement_account=None,
                     corr_account=None,
                     bic=None,

                     discount_goods=None,
                     discount_materials=None,
                     discount_services=None,

                     ad_campaign_id=None,
                     discount_goods_margin_id=None,
                     discount_materials_margin_id=None,
                     discount_service_margin_id=None,

                     tags=None
                     ):

        self.pgsql_connetction.session.query(Clients).filter_by(id=id).update({
            'juridical': juridical if juridical is not None else Clients.juridical,
            'supplier': supplier if supplier is not None else Clients.supplier,
            'conflicted': conflicted if conflicted is not None else Clients.conflicted,
            'should_send_email': should_send_email if should_send_email is not None else Clients.should_send_email,
            'deleted': deleted if deleted is not None else Clients.deleted,
            'discount_good_type': discount_good_type if discount_good_type is not None else Clients.discount_good_type,
            'discount_materials_type': discount_materials_type if discount_materials_type is not None else Clients.discount_materials_type,
            'discount_service_type': discount_service_type if discount_service_type is not None else Clients.discount_service_type,

            'name': name if name is not None else Clients.name,
            'name_doc': name_doc if name_doc is not None else Clients.name_doc,
            'email': email if email is not None else Clients.email,
            'address': address if address is not None else Clients.address,
            'discount_code': discount_code if discount_code is not None else Clients.discount_code,
            'notes': notes if notes is not None else Clients.notes,
            'ogrn': ogrn if ogrn is not None else Clients.ogrn,
            'inn': inn if inn is not None else Clients.inn,
            'kpp': kpp if kpp is not None else Clients.kpp,
            'juridical_address': juridical_address if juridical_address is not None else Clients.juridical_address,
            'director': director if director is not None else Clients.director,
            'bank_name': bank_name if bank_name is not None else Clients.bank_name,
            'settlement_account': settlement_account if settlement_account is not None else Clients.settlement_account,
            'corr_account': corr_account if corr_account is not None else Clients.corr_account,
            'bic': bic if bic is not None else Clients.bic,

            'discount_goods': discount_goods if discount_goods is not None else Clients.discount_goods,
            'discount_materials': discount_materials if discount_materials is not None else Clients.discount_materials,
            'discount_services': discount_services if discount_services is not None else Clients.discount_services,
            'discount_service_margin_id': discount_service_margin_id if discount_service_margin_id is not None else Clients.discount_service_margin_id,

            'ad_campaign_id': ad_campaign_id if ad_campaign_id is not None else Clients.ad_campaign_id,
            'discount_goods_margin_id': discount_goods_margin_id if discount_goods_margin_id is not None else Clients.discount_goods_margin_id,
            'discount_materials_margin_id': discount_materials_margin_id if discount_materials_margin_id is not None else Clients.discount_materials_margin_id,

            'tags': tags if tags is not None else Clients.tags
        })
        self.pgsql_connetction.session.commit()
        return id

    def del_clients(self, id):

        clients = self.pgsql_connetction.session.query(Clients).get(id)
        if clients:
            self.pgsql_connetction.session.delete(clients)
            self.pgsql_connetction.session.commit()
            return self.get_clients()


    # ?????????????? ?????????? ???????? ===============================================================================

    def add_menu_row(self, title, img, url, group_name):

        menu_row = MenuRows(
            title=title,
            img=img,
            url=url,
            group_name=group_name
        )
        self.pgsql_connetction.session.add(menu_row)
        self.pgsql_connetction.session.commit()
        return self.get_menu_row()

    def get_menu_row(self, id=None, title=None, group_name=None):

        if any([id, title, group_name]):
            menu_row = self.pgsql_connetction.session.query(MenuRows).filter(
                and_(
                    MenuRows.id == id if id else True,
                    MenuRows.name in title if title else True,
                    MenuRows.group_name in group_name if group_name else True
                )
            )
        else:
            menu_row = self.pgsql_connetction.session.query(MenuRows)

        self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = menu_row.count()
        result['count'] = count

        data = []
        for row in menu_row:
            data.append({
                'id': row.id,
                'title': row.title,
                'img': row.img,
                'url': row.url,
                'group_name': row.group_name,
                'active': False
            })

        result['data'] = data
        return result

    def edit_menu_row(self, id=None, title=None, img=None, url=None, group_name=None):

        self.pgsql_connetction.session.query(MenuRows).filter_by(id=id).update({
            'title': title if title is not None else MenuRows.title,
            'img': img if img is not None else MenuRows.img,
            'url': url if url is not None else MenuRows.url,
            'group_name': group_name if group_name is not None else MenuRows.group_name

        })
        self.pgsql_connetction.session.commit()
        return id

    def del_menu_row(self, id):

        menu_row = self.pgsql_connetction.session.query(MenuRows).get(id)
        if menu_row:
            self.pgsql_connetction.session.delete(MenuRows)
            self.pgsql_connetction.session.commit()
            return self.get_menu_row()




    # ?????????????? ?????????? ???????? ===============================================================================

    def add_setting_menu(self, title, url, group_name):

        setting_menu = SettingMenu(
            title=title,
            url=url,
            group_name=group_name
        )
        self.pgsql_connetction.session.add(setting_menu)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(setting_menu)
        return setting_menu.id

    def get_setting_menu(self, id=None, title=None, group_name=None):

        if any([id, title, group_name]):
            setting_menu = self.pgsql_connetction.session.query(SettingMenu).filter(
                and_(
                    SettingMenu.id == id if id else True,
                    SettingMenu.name in title if title else True,
                    SettingMenu.group_name in group_name if group_name else True
                )
            )
        else:
            setting_menu = self.pgsql_connetction.session.query(SettingMenu)

        self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = setting_menu.count()
        result['count'] = count

        data = []
        for row in setting_menu:
            data.append({
                'id': row.id,
                'title': row.title,
                'url': row.url,
                'group_name': row.group_name,
                'active': False
            })

        result['data'] = data
        return result

    def edit_setting_menu(self, id, title=None, url=None, group_name=None):

        self.pgsql_connetction.session.query(SettingMenu).filter_by(id=id).update({
            'title': title if title is not None else SettingMenu.title,
            'url': url if url is not None else SettingMenu.url,
            'group_name': group_name if group_name is not None else SettingMenu.group_name

        })
        self.pgsql_connetction.session.commit()
        return id

    def del_setting_menuw(self, id):

        setting_menu = self.pgsql_connetction.session.query(SettingMenu).get(id)
        if setting_menu:
            self.pgsql_connetction.session.delete(SettingMenu)
            self.pgsql_connetction.session.commit()
            return self.get_setting_menu()

    # ?????????????? ?????????? ==================================================================================

    def add_role(self,
                 title,
                 earnings_visibility,
                 leads_visibility,
                 orders_visibility,
                 permissions,
                 settable_statuses,
                 visible_statuses,
                 settable_discount_margin):

        roles = Roles(
            title=title,
            earnings_visibility=earnings_visibility,
            leads_visibility=leads_visibility,
            orders_visibility=orders_visibility,
            permissions=permissions,
            settable_statuses=settable_statuses,
            visible_statuses=visible_statuses,
            settable_discount_margin=settable_discount_margin
        )
        self.pgsql_connetction.session.add(roles)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(roles)
        return roles.id

    def get_role(self,
                 id=None,
                 title=None,
                 page=0):

        if id or title:
            roles = self.pgsql_connetction.session.query(Roles).filter(
                and_(
                    Roles.id == id if id else True,
                    Roles.title.like(f'%{title}%') if title else True,
                )
            )
        else:
            roles = self.pgsql_connetction.session.query(Roles)

        self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = roles.count()
        result['count'] = count

        max_page = count // 50 if count % 50 > 0 else count // 50 - 1

        if page > max_page and max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []
        for row in roles[50 * page: 50 * (page + 1)]:
            data.append({
                'id': row.id,
                'title': row.title,
                'earnings_visibility': row.earnings_visibility,
                'leads_visibility': row.leads_visibility,
                'orders_visibility': row.orders_visibility,
                'permissions': row.permissions,
                'settable_statuses': row.settable_statuses,
                'visible_statuses': row.visible_statuses,
                'settable_discount_margin': row.settable_discount_margin
            })

        result['data'] = data
        result['page'] = page
        return result

    def edit_role(self,
                  id,
                  title=None,
                  earnings_visibility=None,
                  leads_visibility=None,
                  orders_visibility=None,
                  permissions=None,
                  settable_statuses=None,
                  visible_statuses=None,
                  settable_discount_margin=None):

        self.pgsql_connetction.session.query(Roles).filter_by(id=id).update({
            'title': title if title is not None else Roles.title,
            'earnings_visibility': earnings_visibility if earnings_visibility is not None else Roles.earnings_visibility,
            'leads_visibility': leads_visibility if leads_visibility is not None else Roles.leads_visibility,
            'orders_visibility': orders_visibility if orders_visibility is not None else Roles.orders_visibility,
            'permissions': permissions if permissions is not None else Roles.permissions,
            'settable_statuses': settable_statuses if settable_statuses is not None else Roles.settable_statuses,
            'visible_statuses': visible_statuses if visible_statuses is not None else Roles.visible_statuses,
            'settable_discount_margin': settable_discount_margin if settable_discount_margin is not None else Roles.settable_discount_margin
        })
        self.pgsql_connetction.session.commit()
        return id

    def del_roles(self, id):

        roles = self.pgsql_connetction.session.query(Roles).get(id)
        if roles:
            self.pgsql_connetction.session.delete(roles)
            self.pgsql_connetction.session.commit()
            return self.get_role()

    # ?????????????? ???????????????? ???????????????????? ?? ???????????????? ==================================================================

    def add_generally_info(self,
                           name,
                           address,
                           email,

                           ogrn,
                           inn,
                           kpp,
                           juridical_address,
                           director,
                           bank_name,
                           settlement_account,
                           corr_account,
                           bic,

                           description,
                           phone,
                           logo
                           ):

        generally_info = GenerallyInfo(
            name=name,
            address=address,
            email=email,

            ogrn=ogrn,
            inn=inn,
            kpp=kpp,
            juridical_address=juridical_address,
            director=director,
            bank_name=bank_name,
            settlement_account=settlement_account,
            corr_account=corr_account,
            bic=bic,

            description=description,
            phone=phone,
            logo=logo
        )
        self.pgsql_connetction.session.add(generally_info)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(generally_info)
        return generally_info.id

    def get_generally_info(self, id=1):

        generally_info = self.pgsql_connetction.session.query(GenerallyInfo).filter(
            GenerallyInfo.id == id if id else True
        ).first()

        self.pgsql_connetction.session.expire_all()
        result = {'success': True}

        data = {
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

        result['data'] = data
        return result

    def edit_generally_info(self,
                            id,
                            name=None,
                            address=None,
                            email=None,

                            ogrn=None,
                            inn=None,
                            kpp=None,
                            juridical_address=None,
                            director=None,
                            bank_name=None,
                            settlement_account=None,
                            corr_account=None,
                            bic=None,

                            description=None,
                            phone=None,
                            logo=None):

        self.pgsql_connetction.session.query(GenerallyInfo).filter_by(id=id).update({
            'name': name if name is not None else GenerallyInfo.name,
            'address': address if address is not None else GenerallyInfo.address,
            'email': email if email is not None else GenerallyInfo.email,

            'ogrn': ogrn if ogrn is not None else GenerallyInfo.ogrn,
            'inn': inn if inn is not None else GenerallyInfo.inn,
            'kpp': kpp if kpp is not None else GenerallyInfo.kpp,
            'juridical_address': juridical_address if juridical_address is not None else GenerallyInfo.juridical_address,
            'director': director if director is not None else GenerallyInfo.director,
            'bank_name': bank_name if bank_name is not None else GenerallyInfo.bank_name,
            'settlement_account': settlement_account if settlement_account is not None else GenerallyInfo.settlement_account,
            'corr_account': corr_account if corr_account is not None else GenerallyInfo.corr_account,
            'bic': bic if bic is not None else GenerallyInfo.bic,

            'description': description if description is not None else GenerallyInfo.description,
            'phone': phone if phone is not None else GenerallyInfo.phone,
            'logo': logo if logo is not None else GenerallyInfo.logo,
        })
        self.pgsql_connetction.session.commit()
        return id

    def del_generally_info(self, id):

        generally_info = self.pgsql_connetction.session.query(GenerallyInfo).get(id)
        if generally_info:
            self.pgsql_connetction.session.delete(generally_info)
            self.pgsql_connetction.session.commit()
            return id

    # ?????????????? ?????????????????? ==================================================================================

    def add_counts(self, prefix, count, description):

        counts = Counts(
            prefix=prefix,
            count=count,
            description=description
        )
        self.pgsql_connetction.session.add(counts)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(counts)
        return counts.id

    def get_counts(self, id=None):

        if id:
            counts = self.pgsql_connetction.session.query(Counts).filter(
                Counts.id == id if id else True,
            )
        else:
            counts = self.pgsql_connetction.session.query(Counts)

        self.pgsql_connetction.session.expire_all()
        result = {'success': True}

        data = []
        for count in counts:
            data.append({
                'id': count.id,
                'prefix': count.prefix,
                'count': count.count,
                'description': count.description
            })

        result['data'] = data

        return result

    def edit_counts(self, id, prefix=None, count=None, description=None):

        self.pgsql_connetction.session.query(Counts).filter_by(id=id).update({
            'prefix': prefix if prefix is not None else Counts.prefix,
            'count': count if count is not None else Counts.count,
            'description': description if description is not None else Counts.description
        })
        self.pgsql_connetction.session.commit()
        return id

    def inc_count(self, id):

        counter = self.pgsql_connetction.session.query(Counts).filter_by(id=id).first().count
        self.pgsql_connetction.session.query(Counts).filter_by(id=id).update({
            'count': counter + 1
        })

        self.pgsql_connetction.session.commit()
        return id

    def del_counts(self, id):

        counts = self.pgsql_connetction.session.query(Counts).get(id)
        if counts:
            self.pgsql_connetction.session.delete(counts)
            self.pgsql_connetction.session.commit()
            return self.get_counts()

    # ?????????????? ?????????????? ???????????????????????????? =========================================================================

    def add_malfunction(self, title, count):

        malfunction = DictMalfunction(
            title=title,
            count=count
        )
        self.pgsql_connetction.session.add(malfunction)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(malfunction)
        return malfunction.id

    def get_malfunction(self, id=None, title=None, page=0):

        if any([id, title]):
            malfunction = self.pgsql_connetction.session.query(DictMalfunction).filter(
                and_(
                    DictMalfunction.id == id if id else True,
                    DictMalfunction.title.like(f'%{title}%') if title else True
                )
            ).order_by(desc(DictMalfunction.count))
        else:
            malfunction = self.pgsql_connetction.session.query(DictMalfunction).order_by(desc(DictMalfunction.count))

        self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = malfunction.count()
        result['count'] = count

        intem_of_page = 20

        max_page = count // intem_of_page if count % intem_of_page > 0 else count // intem_of_page - 1

        if page > max_page and max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []
        for row in malfunction[intem_of_page * page: intem_of_page * (page + 1)]:
            data.append({
                'id': row.id,
                'title': row.title,
                'count': row.count
            })

        result['data'] = data
        result['page'] = page
        return result

    def edit_malfunction(self, id, title=None, count=None):

        self.pgsql_connetction.session.query(DictMalfunction).filter_by(id=id).update({
            'title': title if title is not None else DictMalfunction.title,
            'count': count if count is not None else DictMalfunction.count
        })
        self.pgsql_connetction.session.commit()
        return id

    def del_malfunction(self, id):

        malfunction = self.pgsql_connetction.session.query(DictMalfunction).get(id)
        if malfunction:
            self.pgsql_connetction.session.delete(malfunction)
            self.pgsql_connetction.session.commit()
            return id

    # ?????????????? ?????????????? ???????????????????????? =========================================================================

    def add_packagelist(self, title, count):

        packagelist = DictPackagelist(
            title=title,
            count=count
        )
        self.pgsql_connetction.session.add(packagelist)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(packagelist)
        return packagelist.id

    def get_packagelist(self, id=None, title=None, page=0):

        if any([id, title]):
            packagelist = self.pgsql_connetction.session.query(DictPackagelist).filter(
                and_(
                    DictPackagelist.id == id if id else True,
                    DictPackagelist.title.like(f'%{title}%') if title else True
                )
            ).order_by(desc(DictPackagelist.count))
        else:
            packagelist = self.pgsql_connetction.session.query(DictPackagelist).order_by(desc(DictPackagelist.count))

        self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = packagelist.count()
        result['count'] = count

        intem_of_page = 20

        max_page = count // intem_of_page if count % intem_of_page > 0 else count // intem_of_page - 1

        if page > max_page and max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []
        for row in packagelist[intem_of_page * page: intem_of_page * (page + 1)]:
            data.append({
                'id': row.id,
                'title': row.title,
                'count': row.count
            })

        result['data'] = data
        result['page'] = page
        return result

    def edit_packagelist(self, id, title=None, count=None):

        self.pgsql_connetction.session.query(DictPackagelist).filter_by(id=id).update({
            'title': title if title is not None else DictPackagelist.title,
            'count': count if count is not None else DictPackagelist.count
        })
        self.pgsql_connetction.session.commit()
        return id

    def del_packagelist(self, id):

        packagelist = self.pgsql_connetction.session.query(DictPackagelist).get(id)
        if packagelist:
            self.pgsql_connetction.session.delete(packagelist)
            self.pgsql_connetction.session.commit()
            return self.get_packagelist()


    # ?????????????? ?????????????? ???????????????????????? =========================================================================

    def add_item_payments(self, title, direction):

        item_payments = ItemPayments(
            title=title,
            direction=direction
        )
        self.pgsql_connetction.session.add(item_payments)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(item_payments)
        return item_payments.id

    def get_item_payments(self, id=None, title=None, direction=None, page=0):

        if any([id, title, direction]):
            item_payments = self.pgsql_connetction.session.query(ItemPayments).filter(
                and_(
                    ItemPayments.id == id if id else True,
                    ItemPayments.title.like(f'%{title}%') if title else True,
                    ItemPayments.direction == direction if direction else True,
                )
            ).order_by(desc(ItemPayments.direction))
        else:
            item_payments = self.pgsql_connetction.session.query(ItemPayments).order_by(desc(ItemPayments.direction))

        self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = item_payments.count()
        result['count'] = count

        intem_of_page = 20

        max_page = count // intem_of_page if count % intem_of_page > 0 else count // intem_of_page - 1

        if page > max_page and max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []
        for row in item_payments[intem_of_page * page: intem_of_page * (page + 1)]:
            data.append({
                'id': row.id,
                'title': row.title,
                'direction': row.direction
            })

        result['data'] = data
        result['page'] = page
        return result

    def edit_item_payments(self, id, title=None, direction=None):

        self.pgsql_connetction.session.query(ItemPayments).filter_by(id=id).update({
            'title': title if title is not None else ItemPayments.title,
            'direction': direction if direction is not None else ItemPayments.direction
        })
        self.pgsql_connetction.session.commit()
        return id

    def del_item_payments(self, id):

        item_payments = self.pgsql_connetction.session.query(ItemPayments).get(id)
        if item_payments:
            self.pgsql_connetction.session.delete(item_payments)
            self.pgsql_connetction.session.commit()
            return id



    # ?????????????? ???????????? ???????????????????? ???????????????????? ?????????? ===============================================================

    def add_payrule(self,
                    title,
                    type_rule,
                    order_type,
                    method,
                    coefficient,
                    count_coeff,
                    fix_salary,
                    deleted,
                    employee_id,
                    check_status
                    ):

        payrule = Payrules(
            title=title,
            type_rule=type_rule,
            order_type=order_type,
            method=method,
            coefficient=coefficient,
            count_coeff=count_coeff,
            fix_salary=fix_salary,
            deleted=deleted,
            employee_id=employee_id,
            check_status=check_status
        )
        self.pgsql_connetction.session.add(payrule)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(payrule)
        return payrule.id

    def get_payrules(self,
                     id=None,
                     title=None,
                     type_rule=None,
                     deleted=None,
                     employee_id=None,
                     order_type=None,
                     check_status=None
                     ):

        if any([id, title, type_rule, deleted != None, employee_id, order_type, check_status]):
            payrule = self.pgsql_connetction.session.query(Payrules).filter(
                and_(
                    Payrules.id == id if id else True,
                    Payrules.title.like(f'%{title}%') if title else True,
                    Payrules.type_rule == type_rule if type_rule else True,
                    Payrules.order_type == order_type if order_type else True,
                    Payrules.check_status == check_status if check_status else True,
                    (deleted or Payrules.deleted.is_(False)) if deleted != None else True,
                    Payrules.employee_id == employee_id if employee_id else True,
                )
            ).order_by(desc(Payrules.created_at))
        else:
            payrule = self.pgsql_connetction.session.query(Payrules).order_by(desc(Payrules.created_at))

        result = {'success': True}
        count = payrule.count()
        result['count'] = count

        data = []
        for row in payrule:
            data.append({
                'id': row.id,
                'title': row.title,
                'type_rule': row.type_rule,
                'order_type': row.order_type,
                'method': row.method,
                'coefficient': row.coefficient,
                'count_coeff': row.count_coeff,
                'fix_salary': row.fix_salary,
                'deleted': row.deleted,
                'created_at': row.created_at,
                'employee_id': row.employee_id,
                'check_status': row.check_status
            })

        result['data'] = data
        return result

    def edit_payrule(self,
                     id,
                     title=None,
                     type_rule=None,
                     order_type=None,
                     method=None,
                     coefficient=None,
                     count_coeff=None,
                     fix_salary=None,
                     deleted=None,
                     employee_id=None,
                     check_status=None):

        self.pgsql_connetction.session.query(Payrules).filter_by(id=id).update({
            'title': title if title is not None else Payrules.title,
            'type_rule': type_rule if type_rule is not None else Payrules.type_rule,
            'order_type': order_type if order_type is not None else Payrules.order_type,
            'method': method if method is not None else Payrules.method,
            'coefficient': coefficient if coefficient is not None else Payrules.coefficient,
            'count_coeff': count_coeff if count_coeff is not None else Payrules.count_coeff,
            'fix_salary': fix_salary if fix_salary is not None else Payrules.fix_salary,
            'deleted': deleted if deleted is not None else Payrules.deleted,
            'employee_id': employee_id if employee_id is not None else Payrules.employee_id,
            'check_status': check_status if check_status is not None else Payrules.check_status
        })
        self.pgsql_connetction.session.commit()
        return id

    def del_payrule(self, id):

        payrule = self.pgsql_connetction.session.query(Payrules).get(id)
        if payrule:
            self.pgsql_connetction.session.delete(payrule)
            self.pgsql_connetction.session.commit()
            return id

    # ?????????????? ?????????????????? ???????????? ???????? ===============================================================

    def add_group_dict_service(self, title, icon, deleted):

        group_dict_service = GroupDictService(
            title=title,
            icon=icon,
            deleted=deleted
        )
        self.pgsql_connetction.session.add(group_dict_service)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(group_dict_service)
        return group_dict_service.id

    def get_group_dict_service(self, id=None, title=None, deleted=None):

        if any([id, title, deleted != None]):
            group_dict_service = self.pgsql_connetction.session.query(GroupDictService).filter(
                and_(
                    GroupDictService.id == id if id else True,
                    GroupDictService.title.like(f'%{title}%') if title else True,
                    (deleted or GroupDictService.deleted.is_(False)) if deleted != None else True,
                )
            ).order_by(GroupDictService.title)
        else:
            group_dict_service = self.pgsql_connetction.session.query(GroupDictService).order_by(GroupDictService.title)

        result = {'success': True}
        count = group_dict_service.count()
        result['count'] = count

        data = []
        for row in group_dict_service:
            data.append({
                'id': row.id,
                'title': row.title,
                'icon': row.icon,
                'deleted': row.deleted,
                'count': len(row.dict_service)
            })

        result['data'] = data
        return result

    def edit_group_dict_service(self, id, title=None, icon=None, deleted=None):

        self.pgsql_connetction.session.query(GroupDictService).filter_by(id=id).update({
            'title': title if title is not None else GroupDictService.title,
            'icon': icon if icon is not None else GroupDictService.icon,
            'deleted': deleted if deleted is not None else GroupDictService.deleted
        })
        self.pgsql_connetction.session.commit()
        return id

    def del_group_dict_service(self, id):

        group_dict_service = self.pgsql_connetction.session.query(GroupDictService).get(id)
        if group_dict_service:
            self.pgsql_connetction.session.delete(group_dict_service)
            self.pgsql_connetction.session.commit()
            return id

    # ?????????????? ???????????? ???????????????????? ???????????????????? ?????????? ===============================================================

    def add_dict_service(self,
                         title,
                         price,
                         cost,
                         warranty,
                         code,
                         earnings_percent,
                         earnings_summ,
                         deleted,
                         category_id
                         ):

        dict_service = DictService(
            title=title,
            price=price,
            cost=cost,
            warranty=warranty,
            code=code,
            earnings_percent=earnings_percent,
            earnings_summ=earnings_summ,
            deleted=deleted,
            category_id=category_id
        )
        self.pgsql_connetction.session.add(dict_service)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(dict_service)
        return dict_service.id

    def get_dict_service(self,
                         id=None,
                         title=None,
                         warranty=None,
                         code=None,
                         deleted=None,
                         category_id=None
                         ):

        if any([id, title, warranty, code, deleted != None, category_id]):
            dict_service = self.pgsql_connetction.session.query(DictService).filter(
                and_(
                    DictService.id == id if id else True,
                    DictService.title.like(f'%{title}%') if title else True,
                    DictService.warranty == warranty if warranty else True,
                    DictService.code == code if code else True,
                    (deleted or DictService.deleted.is_(False)) if deleted != None else True,
                    DictService.category_id == category_id if category_id else True,
                )
            ).order_by(desc(DictService.title))
        else:
            dict_service = self.pgsql_connetction.session.query(DictService).order_by(desc(DictService.title))

        result = {'success': True}
        count = dict_service.count()
        result['count'] = count

        data = []
        for row in dict_service:
            data.append({
                'id': row.id,
                'title': row.title,
                'price': row.price,
                'cost': row.cost,
                'warranty': row.warranty,
                'code': row.code,
                'earnings_percent': row.earnings_percent,
                'earnings_summ': row.earnings_summ,
                'deleted': row.deleted,
                'category_id': row.category_id
            })

        result['data'] = data
        return result

    def edit_dict_service(self,
                          id,
                          title=None,
                          price=None,
                          cost=None,
                          warranty=None,
                          code=None,
                          earnings_percent=None,
                          earnings_summ=None,
                          deleted=None,
                          category_id=None
                          ):

        self.pgsql_connetction.session.query(DictService).filter_by(id=id).update({
            'title': title if title is not None else DictService.title,
            'price': price if price is not None else DictService.price,
            'cost': cost if cost is not None else DictService.cost,
            'warranty': warranty if warranty is not None else DictService.warranty,
            'code': code if code is not None else DictService.code,
            'earnings_percent': earnings_percent if earnings_percent is not None else DictService.earnings_percent,
            'earnings_summ': earnings_summ if earnings_summ is not None else DictService.earnings_summ,
            'deleted': deleted if deleted is not None else DictService.deleted,
            'category_id': category_id if category_id is not None else DictService.category_id
        })
        self.pgsql_connetction.session.commit()
        return id

    def del_dict_service(self, id):

        dict_service = self.pgsql_connetction.session.query(DictService).get(id)
        if dict_service:
            self.pgsql_connetction.session.delete(dict_service)
            self.pgsql_connetction.session.commit()
            return id

    # ?????????????? ?????? ???????? ===============================================================

    def add_service_prices(self, cost, discount_margin_id, service_id, deleted):

        service_prices = ServicePrices(
            cost=cost,
            discount_margin_id=discount_margin_id,
            service_id=service_id,
            deleted=deleted
        )
        self.pgsql_connetction.session.add(service_prices)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(service_prices)
        return service_prices.id

    def get_service_prices(self, id=None, discount_margin_id=None, service_id=None, deleted=None):

        if any([id, discount_margin_id, service_id, deleted != None]):
            service_prices = self.pgsql_connetction.session.query(ServicePrices).filter(
                and_(
                    ServicePrices.id == id if id else True,
                    ServicePrices.discount_margin_id == discount_margin_id if discount_margin_id else True,
                    ServicePrices.service_id == service_id if service_id else True,
                    (deleted or ServicePrices.deleted.is_(False)) if deleted != None else True
                )
            )
        else:
            service_prices = self.pgsql_connetction.session.query(ServicePrices)

        result = {'success': True}
        count = service_prices.count()
        result['count'] = count

        data = []
        for row in service_prices:
            data.append({
                'id': row.id,
                'cost': row.cost,
                'discount_margin_id': row.discount_margin_id,
                'service_id': row.service_id,
                'deleted': row.deleted
            })

        result['data'] = data
        return result

    def edit_service_prices(self, id, cost=None, discount_margin_id=None, service_id=None, deleted=None):

        self.pgsql_connetction.session.query(ServicePrices).filter_by(id=id).update({
            'cost': cost if cost is not None else ServicePrices.cost,
            'discount_margin_id': discount_margin_id if discount_margin_id is not None else ServicePrices.discount_margin_id,
            'service_id': service_id if service_id is not None else ServicePrices.service_id,
            'deleted': deleted if deleted is not None else ServicePrices.deleted
        })
        self.pgsql_connetction.session.commit()
        return id

    def del_service_prices(self, id):

        service_prices = self.pgsql_connetction.session.query(ServicePrices).get(id)
        if service_prices:
            self.pgsql_connetction.session.delete(service_prices)
            self.pgsql_connetction.session.commit()
            return id

    # ?????????????? ??????????????/?????????????????? ===============================================================

    def add_parts(self,
                  title,
                  description,
                  marking,
                  article,
                  barcode,
                  code,
                  image_url,
                  doc_url,
                  specifications,
                  deleted,
                  warehouse_category_id):

        parts = Parts(
            title=title,
            description=description,
            marking=marking,
            article=article,
            barcode=barcode,
            code=code,
            image_url=image_url,
            doc_url=doc_url,
            specifications=specifications,
            deleted=deleted,
            warehouse_category_id=warehouse_category_id
        )
        self.pgsql_connetction.session.add(parts)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(parts)
        return parts.id

    def get_parts(self,
                  id=None,
                  title=None,
                  marking=None,
                  article=None,
                  barcode=None,
                  code=None,
                  page=0,
                  deleted=None,
                  warehouse_category_id=None):

        if any([id, title, marking, article, barcode, code, deleted != None]):
            parts = self.pgsql_connetction.session.query(Parts).filter(
                and_(
                    Parts.id == id if id else True,
                    Parts.title.ilike(f'%{title}%') if title else True,
                    Parts.marking.ilike(f'%{marking}%') if marking else True,
                    Parts.article == article if article else True,
                    Parts.barcode == barcode if barcode else True,
                    Parts.code == code if code else True,
                    (deleted or Parts.deleted.is_(False)) if deleted != None else True,
                    Parts.warehouse_category_id == warehouse_category_id if warehouse_category_id else True
                )
            ).order_by(Parts.title)
        else:
            parts = self.pgsql_connetction.session.query(Parts).order_by(Parts.title)

        result = {'success': True}
        count = parts.count()
        result['count'] = count

        item_of_page = 50

        max_page = count // item_of_page if count % item_of_page > 0 else count // item_of_page - 1

        if page > max_page and max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []
        for row in parts[item_of_page * page: item_of_page * (page + 1)]:
            data.append({
                'id': row.id,
                'title': row.title,
                'description': row.description,
                'marking': row.marking,
                'article': row.article,
                'barcode': row.barcode,
                'code': row.code,
                'image_url': row.image_url,
                'doc_url': row.doc_url,
                'specifications': row.specifications,
                'deleted': row.deleted,
                'warehouse_category': {
                    'id': row.warehouse_category.id,
                    'title': row.warehouse_category.title,
                    'deleted': row.warehouse_category.deleted
                } if row.warehouse_category else {}
            })

        result['data'] = data
        return result

    def edit_parts(self,
                   id,
                   title=None,
                   description=None,
                   marking=None,
                   article=None,
                   barcode=None,
                   code=None,
                   image_url=None,
                   doc_url=None,
                   specifications=None,
                   deleted=None,
                   warehouse_category_id=None):

        self.pgsql_connetction.session.query(Parts).filter_by(id=id).update({
            'title': title if title is not None else Parts.title,
            'description': description if description is not None else Parts.description,
            'marking': marking if marking is not None else Parts.marking,
            'article': article if article is not None else Parts.article,
            'barcode': barcode if barcode is not None else Parts.barcode,
            'code': code if code is not None else Parts.code,
            'image_url': image_url if image_url is not None else Parts.image_url,
            'doc_url': doc_url if doc_url is not None else Parts.doc_url,
            'specifications': specifications if specifications is not None else Parts.specifications,
            'deleted': deleted if deleted is not None else Parts.deleted,
            'warehouse_category_id': warehouse_category_id if warehouse_category_id is not None else Parts.warehouse_category_id
        })
        self.pgsql_connetction.session.commit()
        return id

    def del_parts(self, id):

        parts = self.pgsql_connetction.session.query(Parts).get(id)
        if parts:
            self.pgsql_connetction.session.delete(parts)
            self.pgsql_connetction.session.commit()
            return id

    # ?????????????? ?????????????? ===============================================================

    def add_warehouse(self, title, description, isGlobal, permissions, employees, branch_id, deleted):

        warehouse = Warehouse(
            title=title,
            description=description,
            isGlobal=isGlobal,
            permissions=permissions,
            employees=employees,
            branch_id=branch_id,
            deleted=deleted
        )
        self.pgsql_connetction.session.add(warehouse)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(warehouse)
        return warehouse.id

    def get_warehouse(self,
                      id=None,
                      title=None,
                      branch_id=None,
                      isGlobal=None,
                      deleted=None,
                      page=0):

        if any([id, title, branch_id, isGlobal != None, deleted != None]):
            warehouse = self.pgsql_connetction.session.query(Warehouse).filter(
                and_(
                    Warehouse.id == id if id else True,
                    Warehouse.title.ilike(f'%{title}%') if title else True,
                    Warehouse.branch_id == branch_id if branch_id else True,
                    Warehouse.isGlobal == isGlobal if isGlobal != None else True,
                    (deleted or Warehouse.deleted.is_(False)) if deleted != None else True
                )
            ).order_by(Warehouse.title)
        else:
            warehouse = self.pgsql_connetction.session.query(Warehouse).order_by(Warehouse.title)

        result = {'success': True}
        count = warehouse.count()
        result['count'] = count

        item_of_page = 50

        max_page = count // item_of_page if count % item_of_page > 0 else count // item_of_page - 1

        if page > max_page and max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []
        for row in warehouse[item_of_page * page: item_of_page * (page + 1)]:
            data.append({
                'id': row.id,
                'title': row.title,
                'description': row.description,
                'isGlobal': row.isGlobal,
                'permissions': row.permissions,
                'employees': row.employees,
                'deleted': row.deleted,
                'branch': {
                    'id': row.branch.id,
                    'name': row.branch.name,
                    'color': row.branch.color,
                    'icon': row.branch.icon
                } if row.branch else {}
            })

        result['data'] = data
        return result

    def edit_warehouse(self,
                       id,
                       title=None,
                       description=None,
                       isGlobal=None,
                       permissions=None,
                       employees=None,
                       branch_id=None,
                       deleted=None):

        self.pgsql_connetction.session.query(Warehouse).filter_by(id=id).update({
            'title': title if title is not None else Warehouse.title,
            'description': description if description is not None else Warehouse.description,
            'branch_id': branch_id if branch_id is not None else Warehouse.branch_id,
            'permissions': permissions if permissions is not None else Warehouse.permissions,
            'employees': employees if employees is not None else Warehouse.employees,
            'isGlobal': isGlobal if isGlobal is not None else Warehouse.isGlobal,
            'deleted': deleted if deleted is not None else Warehouse.deleted
        })
        self.pgsql_connetction.session.commit()
        return id

    def del_warehouse(self, id):

        warehouse = self.pgsql_connetction.session.query(Warehouse).get(id)
        if warehouse:
            self.pgsql_connetction.session.delete(warehouse)
            self.pgsql_connetction.session.commit()
            return id

    # ?????????????? ?????????????????? ?????????????? ===============================================================

    def add_warehouse_category(self, title, parent_category_id, warehouse_id, deleted):

        warehouse_category = WarehouseCategory(
            title=title,
            parent_category_id=parent_category_id,
            warehouse_id=warehouse_id,
            deleted=deleted
        )
        self.pgsql_connetction.session.add(warehouse_category)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(warehouse_category)
        return warehouse_category.id

    def get_warehouse_category(self,
                               id=None,
                               title=None,
                               parent_category_id=None,
                               warehouse_id=None,
                               deleted=None,
                               page=0):

        if any([id, title, parent_category_id, warehouse_id, deleted != None]):
            warehouse_category = self.pgsql_connetction.session.query(WarehouseCategory).filter(
                and_(
                    WarehouseCategory.id == id if id else True,
                    # WarehouseCategory.title.ilike(f'%{title}%') if title else True,
                    # WarehouseCategory.parent_category_id == parent_category_id if parent_category_id else True,
                    # WarehouseCategory.warehouse_id == warehouse_id if warehouse_id else True,
                    (deleted or WarehouseCategory.deleted.is_(False)) if deleted != None else True
                )
            ).order_by(WarehouseCategory.title)
        else:
            warehouse_category = self.pgsql_connetction.session.query(WarehouseCategory).order_by(
                WarehouseCategory.title)

        result = {'success': True}
        count = warehouse_category.count()
        result['count'] = count

        data = []
        for row in warehouse_category:
            data.append({
                'id': row.id,
                'title': row.title,
                'parent_category_id': row.parent_category_id,
                'warehouse_id': row.warehouse_id,
                'deleted': row.deleted,
            })

        result['data'] = data
        return result

    def edit_warehouse_category(self,
                                id,
                                title=None,
                                parent_category_id=None,
                                warehouse_id=None,
                                deleted=None):

        self.pgsql_connetction.session.query(WarehouseCategory).filter_by(id=id).update({
            'title': title if title is not None else WarehouseCategory.title,
            'parent_category_id': parent_category_id if parent_category_id is not None else WarehouseCategory.parent_category_id,
            'warehouse_id': warehouse_id if warehouse_id is not None else WarehouseCategory.warehouse_id,
            'deleted': deleted if deleted is not None else WarehouseCategory.deleted
        })
        self.pgsql_connetction.session.commit()
        return id

    def del_warehouse_category(self, id):

        warehouse_category = self.pgsql_connetction.session.query(WarehouseCategory).get(id)
        if warehouse_category:
            self.pgsql_connetction.session.delete(warehouse_category)
            self.pgsql_connetction.session.commit()
            return id

    # ?????????????? ?????????????????? ???? ???????????? ==========================================================================================

    def add_warehouse_parts(self,
                            where_to_buy,
                            cell,
                            count,
                            min_residue,
                            warranty_period,
                            necessary_amount,
                            part_id,
                            category_id,
                            warehouse_id,
                            deleted):

        warehouse_parts = WarehouseParts(
            where_to_buy=where_to_buy,
            cell=cell,
            count=count,
            min_residue=min_residue,
            warranty_period=warranty_period,
            necessary_amount=necessary_amount,
            part_id=part_id,
            category_id=category_id,
            warehouse_id=warehouse_id,
            deleted=deleted
        )
        self.pgsql_connetction.session.add(warehouse_parts)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(warehouse_parts)
        return warehouse_parts.id

    def get_warehouse_parts(self,
                            id=None,
                            title=None,
                            cell=None,
                            marking=None,
                            count=None,
                            min_residue=None,
                            part_id=None,
                            category_id=None,
                            warehouse_id=None,
                            page=0,
                            deleted=None):

        if any([id, cell, title, marking, count, min_residue, part_id, category_id, warehouse_id, deleted != None]):
            warehouse_parts = self.pgsql_connetction.session.query(WarehouseParts).join(WarehouseParts.part).filter(
                and_(
                    WarehouseParts.id == id if id else True,
                    WarehouseParts.cell == cell if cell else True,
                    WarehouseParts.part.property.mapper.class_.title.ilike(f'%{title}%'),
                    WarehouseParts.part.property.mapper.class_.marking.ilike(f'%{marking}%'),
                    WarehouseParts.count == count if count else True,
                    WarehouseParts.min_residue == min_residue if min_residue else True,
                    WarehouseParts.part_id == part_id if part_id else True,
                    WarehouseParts.category_id == category_id if category_id else True,
                    WarehouseParts.warehouse_id == warehouse_id if warehouse_id else True,
                    (deleted or WarehouseParts.deleted.is_(False)) if deleted != None else True
                )
            ).order_by(WarehouseParts.title)
        else:
            warehouse_parts = self.pgsql_connetction.session.query(WarehouseParts).order_by(WarehouseParts.title)

        result = {'success': True}
        count = warehouse_parts.count()
        result['count'] = count

        item_of_page = 50

        max_page = count // item_of_page if count % item_of_page > 0 else count // item_of_page - 1

        if page > max_page and max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []
        for row in warehouse_parts[item_of_page * page: item_of_page * (page + 1)]:
            data.append({
                'id': row.id,
                'where_to_buy': row.where_to_buy,
                'cell': row.cell,
                'count': row.count,
                'min_residue': row.min_residue,
                'warranty_period': row.warranty_period,
                'necessary_amount': row.necessary_amount,
                'part_id': row.part_id,
                'category_id': row.category_id,
                'warehouse_id': row.warehouse_id,
                'deleted': row.deleted,
                'title': row.part.title,
                'description': row.part.description,
                'marking': row.part.marking,
                'article': row.part.article,
                'barcode': row.part.barcode,
                'code': row.part.code,
                'image_url': row.part.image_url,
                'doc_url': row.part.doc_url
            })

        result['data'] = data
        return result

    def edit_warehouse_parts(self,
                             id,
                             where_to_buy=None,
                             cell=None,
                             count=None,
                             min_residue=None,
                             warranty_period=None,
                             necessary_amount=None,
                             part_id=None,
                             category_id=None,
                             warehouse_id=None,
                             specifications=None,
                             deleted=None):

        self.pgsql_connetction.session.query(WarehouseParts).filter_by(id=id).update({
            'where_to_buy': where_to_buy if where_to_buy is not None else WarehouseParts.where_to_buy,
            'cell': cell if cell is not None else WarehouseParts.cell,
            'count': count if count is not None else WarehouseParts.count,
            'min_residue': min_residue if min_residue is not None else WarehouseParts.min_residue,
            'warranty_period': warranty_period if warranty_period is not None else WarehouseParts.warranty_period,
            'necessary_amount': necessary_amount if necessary_amount is not None else WarehouseParts.necessary_amount,
            'part_id': part_id if part_id is not None else WarehouseParts.part_id,
            'category_id': category_id if category_id is not None else WarehouseParts.category_id,
            'warehouse_id': warehouse_id if warehouse_id is not None else WarehouseParts.warehouse_id,
            'deleted': deleted if deleted is not None else WarehouseParts.deleted
        })
        self.pgsql_connetction.session.commit()
        return id

    def del_warehouse_parts(self, id):

        warehouse_parts = self.pgsql_connetction.session.query(WarehouseParts).get(id)
        if warehouse_parts:
            self.pgsql_connetction.session.delete(warehouse_parts)
            self.pgsql_connetction.session.commit()
            return id

    # ?????????????? ???????????????? ?????????????????????? =========================================================================================

    def add_notification_template(self, title, template, deleted):

        notification_template = NotificationTemplate(
            title=title,
            template=template,
            deleted=deleted
        )
        self.pgsql_connetction.session.add(notification_template)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(notification_template)
        return notification_template.id

    def get_notification_template(self, id=None, title=None, page=0, deleted=None):

        if any([id, title, deleted != None]):
            notification_template = self.pgsql_connetction.session.query(NotificationTemplate).filter(
                and_(
                    NotificationTemplate.id == id if id else True,
                    NotificationTemplate.title.ilike(f'%{title}%') if title else True,
                    (deleted or NotificationTemplate.deleted.is_(False)) if deleted != None else True
                )
            ).order_by(NotificationTemplate.title)
        else:
            notification_template = self.pgsql_connetction.session.query(NotificationTemplate).order_by(
                NotificationTemplate.title)

        result = {'success': True}
        count = notification_template.count()
        result['count'] = count

        item_of_page = 50

        max_page = count // item_of_page if count % item_of_page > 0 else count // item_of_page - 1

        if page > max_page and max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []
        for row in notification_template[item_of_page * page: item_of_page * (page + 1)]:
            data.append({
                'id': row.id,
                'title': row.title,
                'template': row.template,
                'deleted': row.deleted
            })

        result['data'] = data
        return result

    def edit_notification_template(self, id, title=None, template=None, deleted=None):

        self.pgsql_connetction.session.query(NotificationTemplate).filter_by(id=id).update({
            'title': title if title is not None else NotificationTemplate.title,
            'template': template if template is not None else NotificationTemplate.template,
            'deleted': deleted if deleted is not None else NotificationTemplate.deleted
        })
        self.pgsql_connetction.session.commit()
        return id

    def del_notification_template(self, id):

        notification_template = self.pgsql_connetction.session.query(NotificationTemplate).get(id)
        if notification_template:
            self.pgsql_connetction.session.delete(notification_template)
            self.pgsql_connetction.session.commit()
            return id

    # ?????????????? ?????????????? ?????? ?????????????????????? ======================================================================================

    def add_notification_events(self, event, target_audience, statuses, notification_type, notification_template_id,
                                deleted):

        notification_events = NotificationEvents(
            event=event,
            target_audience=target_audience,
            statuses=statuses,
            notification_type=notification_type,
            notification_template_id=notification_template_id,
            deleted=deleted
        )
        self.pgsql_connetction.session.add(notification_events)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(notification_events)
        return notification_events.id

    def get_notification_events(self,
                                id=None,
                                event=None,
                                target_audience=None,
                                notification_template_id=None,
                                notification_type=None,
                                page=0,
                                deleted=None
                                ):

        if any([id, event, target_audience, notification_template_id, notification_type, deleted != None]):
            notification_events = self.pgsql_connetction.session.query(NotificationEvents).filter(
                and_(
                    NotificationEvents.id == id if id else True,
                    NotificationEvents.event == event if event else True,
                    NotificationEvents.target_audience == target_audience if target_audience else True,
                    NotificationEvents.notification_type == notification_type if notification_type else True,
                    NotificationEvents.notification_template_id == notification_template_id if notification_template_id else True,
                    (deleted or NotificationEvents.deleted.is_(False)) if deleted != None else True
                )
            ).order_by(NotificationEvents.id)
        else:
            notification_events = self.pgsql_connetction.session.query(NotificationEvents).order_by(
                NotificationEvents.id)

        result = {'success': True}
        count = notification_events.count()
        result['count'] = count

        item_of_page = 50

        max_page = count // item_of_page if count % item_of_page > 0 else count // item_of_page - 1

        if page > max_page and max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []
        for row in notification_events[item_of_page * page: item_of_page * (page + 1)]:
            data.append({
                'id': row.id,
                'event': row.event,
                'target_audience': row.target_audience,
                'statuses': row.statuses,
                'notification_type': row.notification_type,
                'template_id': row.template.id,
                'template_title': row.template.title,
                'template': row.template.template,
                'deleted': row.deleted
            })

        result['data'] = data
        return result

    def edit_notification_events(self,
                                 id,
                                 event=None,
                                 target_audience=None,
                                 statuses=None,
                                 notification_type=None,
                                 notification_template_id=None,
                                 deleted=None
                                 ):

        self.pgsql_connetction.session.query(NotificationEvents).filter_by(id=id).update({
            'event': event if event is not None else NotificationEvents.event,
            'target_audience': target_audience if target_audience is not None else NotificationEvents.target_audience,
            'statuses': statuses if statuses is not None else NotificationEvents.statuses,
            'notification_type': notification_type if notification_type is not None else NotificationEvents.notification_type,
            'notification_template_id': notification_template_id if notification_template_id is not None else NotificationEvents.notification_template_id,
            'deleted': deleted if deleted is not None else NotificationEvents.deleted
        })
        self.pgsql_connetction.session.commit()
        return id

    def del_notification_events(self, id):

        notification_events = self.pgsql_connetction.session.query(NotificationEvents).get(id)
        if notification_events:
            self.pgsql_connetction.session.delete(notification_events)
            self.pgsql_connetction.session.commit()
            return id


if __name__ == '__main__':
    start_time = time.time()
    db = DbInteraction(
        host='localhost',
        port='5432',
        user='postgres',
        password='225567',
        db_name='one_two',
        rebuild_db=False
    )

    # ???????????????? ?????????? ????????????
    # db.create_tables([Events.__table__])

    # # ???????????????????? ??????????????
    # column = Column('percent', BOOLEAN)
    # db.add_column(Operations.__table__, column)
    # column = Column('discount', FLOAT)
    # db.add_column(Operations.__table__, column)
    # column = Column('percent', BOOLEAN)
    # db.add_column(OrderParts.__table__, column)
    # column = Column('discount', FLOAT)
    # db.add_column(OrderParts.__table__, column)

    # db.create_all_tables()
    # db.initial_data()
    # db.update_date_from_remonline()
    # db.reset_dict()
    #
    # dtime = time.time() - start_time
    # hours = int(dtime // 3600)
    # minutes = int((dtime % 3600) // 60)
    # seconds = int((dtime % 3600) % 60)
    # print(f'???????????????????? ?????????????????? ???? {hours}:{minutes:02}:{seconds:02}')

    # pages = db.get_orders()['count']/50
    # types = []
    # for page in tqdm(range(int(pages)+1), desc='??????????????????...', position=0):
    #     orders = db.get_orders(page=page)['data']
    #     for order in orders:
    #         types.append(order.get('kindof_good').strip().lower())
    # types = set(types)
    # print('count:', len(types))
    # pprint(types)
