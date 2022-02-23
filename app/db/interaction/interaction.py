import time
from pprint import pprint
import re

from sqlalchemy import or_, and_, desc, func, Column, TEXT, JSON
from sqlalchemy.orm import contains_eager
from werkzeug.security import generate_password_hash

from app.db.client.client import PGSQL_connetction
from app.db.models.models import Base, AdCampaign, Employees, Attachments, Branch, DiscountMargin, OrderType, \
    StatusGroup, Status, Operations, OderParts, Clients, Orders, time_now, MenuRows, TableHeaders, Badges, \
    CustomFilters, EquipmentType, EquipmentBrand, EquipmentSubtype, EquipmentModel, SettingMenu, Roles, Phones, \
    GenerallyInfo, Counts, Schedule, DictMalfunction, DictPackagelist, Cashboxs, Payments, ItemPayments, Payrolls, \
    Payrules, GroupDictService, DictService, ServicePrices, Parts, Warehouse, WarehouseCategory, WarehouseParts

from tqdm import tqdm

from data import data_menu_rows, dataTableHeader, bages, equipment_type, equipment_brand, equipment_subtype, \
    equipment_model, data_setting_menu, data_group_statuses, data_statuses, data_roles, data_branches, data_counts, \
    data_cashboxes, data_item_payments, data_group_service, data_service, data_margin

from payments.alfa import alfa
from payments.tinkoff import tinkoff2021
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

    def __init__(self, host, port,  user, password, db_name, rebuild_db=False):
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

    def create_all_tables(self):
        '''
        Функция создает все таблицы согласно моделям схемы
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

    def drop_all_tables(self):
        '''
        Функция удаляет все таблицы
        '''
        # self.pgsql_connetction.execute_query(
        #     '''DROP DATABASE one_two;'''
        # )
        Base.metadata.drop_all(self.engine)

    def initial_data(self):
        # Удалим все таблицы из базы
        self.drop_all_tables()
        print('Все таблицы удалены')

        # Создадим все таблицы заново
        self.create_all_tables()
        print('Все таблицы созданы')

        # # Загрузим основные данные компании
        self.add_generally_info(
                name='OneTwoService',
                address='Краснодар, Бабушкина 179/1',
                email='onetwoservice@yandex.ru',

                ogrn='',
                inn='230815804505',
                kpp='',
                juridical_address='350049, г. Краснодар, улица Платановый Бульвар, д. 9, кв. 17',
                director='КАЙГОРОДОВ СТАНИСЛАВ СЕРГЕЕВИЧ',
                bank_name='ФИЛИАЛ "РОСТОВСКИЙ" АО "АЛЬФА-БАНК"',
                settlement_account='40802810126240001808',
                corr_account='30101810500000000207',
                bic='046015207',

                description='Ремонт бытовой техники',
                phone='79528556886',
                logo=''
            )
        print('Основные данные компании созданы')

        # Добавим счетчики
        for count in data_counts:
            self.add_counts(
                prefix=count['prefix'],
                count=count['count'],
                description=count['description']
            )
        print('Счетчики созданы')

        # Загрузим рекламные компании
        list_ad_campaign = ['Не указана', 'Знакомые', 'Интернет', 'Наружняя реклама']
        for ad_campaign in list_ad_campaign:
            self.add_adCampaign(
                name=ad_campaign
            )
        print('Рекламные компании загружены')

        # Загрузим филиалы
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
        print('Филиалы загружены')

        # Загрузим типы заказов
        list_order_type = ['В мастерской', 'На выезде']
        for order_type in list_order_type:
            self.add_order_type(
                name=order_type
            )
        print('Типы заказов загружены')

        # Загрузим группы статусов
        for group in data_group_statuses:
            self.add_status_group(
                name=group['name'],
                type_group=group['type_group'],
                color=group['color']
            )
        print('Группы статусов загружены')

        # Синхронизируем статусы
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
        print('Статусы синхронизированы')

        # Загрузим строчки меню
        for row in data_menu_rows:
            self.add_menu_row(
                title=row['title'],
                img=row['image'],
                url=row['url'],
                group_name=row['group_name']
            )
        print('Строки меню загружены')

        # Загрузим строчки меню настроек
        for row in data_setting_menu:
            self.add_setting_menu(
                title=row['title'],
                url=row['url'],
                group_name=row['group_name']
            )
        print('Строки меню настроек загружены')

        # Загрузим данные в справочник изделий
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

        # Загрузим роли
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

        # Добавим кассы
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
        print('Кассы созданы')

        # Добавим статьи ДДС
        for item_payment in data_item_payments:
            self.add_item_payments(
                title=item_payment.get('title'),
                direction=item_payment.get('direction')
            )
        print('Стадитьи ДДС добавлены')

        # Добавим наценки
        for margin in data_margin:
            self.add_discount_margin(
                title=margin.get('title'),
                margin=margin.get('margin'),
                margin_type=margin.get('margin_type'),
                deleted=margin.get('deleted')
            )
        print('Наценки синхронизированы')

        # Добавим категории услуг
        for group in data_group_service:
            self.add_group_dict_service(
                title=group.get('title'),
                icon=group.get('icon'),
                deleted=group.get('deleted')
            )
        print('Категории услуг добавлены')

        # Добавим услуги
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
        print('Услуги добавлены')

    def update_date_from_remonline(self):
        # Синхронизируем данные о сотрудниках
        list_employee = GetListRO('empoyees')
        for employee in list_employee:
            self.add_employee(
                first_name=employee.get('first_name'),
                last_name=employee.get('last_name'),
                email=employee.get('email'),
                notes=employee.get('notes'),
                phone=employee.get('phone'),
                password=generate_password_hash('225567') if employee.get('email') == 'stasmen@mail.ru' else generate_password_hash('12345'),
                deleted=not employee.get('email') in ['stasmen@mail.ru', 'p.s.respekt@mail.ru', 'potato316bless@gmail.com', 'Stepanenkoyura353@mail.ru'],
                inn=None,
                doc_name=None,
                post=None,
                permissions=[],
                role_id=1 if employee.get('email') == 'stasmen@mail.ru' else 2,
                login=None
            )
            imployee_id=self.get_employee(email=employee.get('email'))['data'][0]['id']
            for head in dataTableHeader:
                self.add_table_headers(
                    title=head['title'],
                    field=head['field'],
                    width=head['width'],
                    employee_id=imployee_id
                )
        print('Данные о сотрудниках синхронизированы')

        # Загрузим беджи
        for row in bages:
            self.add_badges(
                title=row['title'],
                color=row['color'],
                img=row['image']
            )
        print('Беджи загружены')

        list_client = GetCustomer(page='all')
        for client in tqdm(list_client, desc='Добавление в базу данных', position=0):
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
                    title='Мобильный',
                    client_id=id_create_client
                )
        print('Клиенты синхронизированы')


        # Обновим заказы
        n = 0
        list_orders = GetOders()
        for order in tqdm(list_orders, desc='Добавление в базу данных', position=0):

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

            id_order =self.add_orders(
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
                status_id=self.get_status(name=order['status']['name'])['data'][0]['id'] if self.get_status(name=order['status']['name'])['data'] else None,
                client_id=self.get_clients(name=order['client']['name'])['data'][0]['id'] if order.get('client') and self.get_clients(name=order['client']['name'])['data'] else None,
                order_type_id=self.get_order_type(name=order['order_type']['name'])['data'][0]['id'] if order.get('order_type') else None,
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

            # id_order = self.get_orders(id_label=order['id_label'])['data'][0]['id'] if \
            # self.get_orders(id_label=order['id_label'])['data'] else print(f'Не найден: {order["id_label"]}')
            if order.get('operations'):
                for operation in order.get('operations'):
                    self.add_operations(
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
                    self.add_oder_parts(
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
                    self.add_attachments(
                        created_by_id=dict_emploeey_ids[str(attachment.get('created_by_id'))] if attachment.get('created_by_id') else None,
                        created_at=attachment.get('created_at') / 1000 if attachment.get('created_at') else None,
                        filename=attachment.get('filename'),
                        url=attachment.get('url'),
                        order_id=id_order
                    )
            n += 1
            if n == len(list_orders):
                index = int(order['id_label'][4:])
                self.edit_counts(id=1, count=index+1, prefix=None, description=None)

        print('Заказы обнавлены')

        # Добавим платежи
        regex_lable = re.compile('OTS-\d+')
        data_payments = [
            {
                'data': alfa,
                'title': 'Транзакции Альфа Банк 2018',
                'cashbox_id': 4
            # }, {
            #     'data': alfa2019,
            #     'title': 'Транзакции Альфа Банк 2019',
            #     'cashbox_id': 4
            # }, {
            #     'data': alfa2020,
            #     'title': 'Транзакции Альфа Банк 2020',
            #     'cashbox_id': 4
            # }, {
            #     'data': alfa2021,
            #     'title': 'Транзакции Альфа Банк 2021',
            #     'cashbox_id': 4
            }, {
                'data': fedreserv,
                'title': 'Транзакции Федеральный резерв',
                'cashbox_id': 7
            }, {
                'data': kassa,
                'title': 'Транзакции Касса 2018',
                'cashbox_id': 1
            # }, {
            #     'data': kassa2019_1,
            #     'title': 'Транзакции Касса 2019_1',
            #     'cashbox_id': 1
            # }, {
            #     'data': kassa2019_2,
            #     'title': 'Транзакции Касса 2019_2',
            #     'cashbox_id': 1
            # }, {
            #     'data': kassa2019_3,
            #     'title': 'Транзакции Касса 2019_3',
            #     'cashbox_id': 1
            # }, {
            #     'data': kassa2020,
            #     'title': 'Транзакции Касса 2020',
            #     'cashbox_id': 1
            # }, {
            #     'data': kassa2021,
            #     'title': 'Транзакции Касса 2021',
            #     'cashbox_id': 1
            }, {
                'data': obus,
                'title': 'Транзакции Обустройство',
                'cashbox_id': 6
            }, {
                'data': sber,
                'title': 'Транзакции Сбербанк',
                'cashbox_id': 3
            }, {
                'data': seyf,
                'title': 'Транзакции Сейф',
                'cashbox_id': 5
            }, {
                'data': tinkoff2021,
                'title': 'Транзакции Тинькофф',
                'cashbox_id': 2
            }, {
                'data': anton,
                'title': 'Транзакции кассы Антон',
                'cashbox_id': 8
            }, {
                'data': yura,
                'title': 'Транзакции кассы Юра',
                'cashbox_id': 9
            }, {
                'data': alba,
                'title': 'Транзакции кассы Альбина',
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
        for page in tqdm(range(260), desc='Создание словарей из бызы заказов', position=0):
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

        for key, val in tqdm(count_malfunction.items(), desc='Добаления словаря неисправностей', position=0):
            self.add_malfunction(
                title=key,
                count=val
            )

        for key, val in tqdm(count_packege.items(), desc='Добаления словаря комплектаций', position=0):
            self.add_packagelist(
                title=key,
                count=val
            )
        print('Все словари созданы')

    # Таблица РЕКЛАМНЫЕ КОМПАНИИ ===========================================================================

    def add_adCampaign(self, name):
        '''
        Добавляет данные о рекламной компании
        :param name: Имя рекламной компании
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
        Возвращает объект с параметрами резултьата поиска по базе данных рекламных компаний
        :param id: ID рекламной компании для поска в базе данных
        :param name: Имя рекламной компании для поиска в базе данных
        :return: Съект с ключами:
                    count - количество найденых записей
                    data: - список оъектов json (строки таблицы)
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

        self.pgsql_connetction.session.expire_all()
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
        Меняет информацию в таблице рекламных компаний бызы данных
        :param id: ID записи
        :param name: новое поле для имени в записи
        '''
        self.pgsql_connetction.session.query(AdCampaign).filter_by(id=id).update({
            'name': name if name else AdCampaign.name
        })
        self.pgsql_connetction.session.commit()
        return self.get_adCampaign()

    def del_adCampaign(self, id):
        '''
        Удаляет запись с указанным ID из таблицы рекламных компаний
        :param id: ID записи
        '''
        adCampaign = self.pgsql_connetction.session.query(AdCampaign).get(id)
        if adCampaign:
            self.pgsql_connetction.session.delete(adCampaign)
            self.pgsql_connetction.session.commit()
            return self.get_adCampaign()

    #  Таблица СОТРУДНИКИ ==================================================================================

    def add_employee(self,
                    first_name,
                    last_name,
                    email,
                    phone,
                    notes,
                    deleted,
                    inn,
                    doc_name,
                    post,
                    permissions,
                    role_id,
                    login,
                    password):
        '''
        Функция добавляет запись о новом сотруднике в таблицу данных сотрудников
        :param first_name: Имя
        :param last_name: Фамилия
        :param email: Электронная почта
        :param phone: Телефон
        :param notes: Заметки
        :param deleted: Удален
        :param role: Роль
        :return:
        '''
        employees = Employees(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            notes=notes,
            deleted=deleted,
            inn=inn,
            doc_name=doc_name,
            post=post,
            permissions=permissions,
            role_id=role_id,
            login=login,
            password=password
        )
        self.pgsql_connetction.session.add(employees)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(employees)
        return employees.id

    def get_employee(self, id=None,
                     first_name=None,
                     last_name=None,
                     email=None,
                     phone=None,
                     notes=None,
                     post=None,
                     deleted=False,
                     role_id=None,
                     login=None,
                     page=0):

        if any([id, first_name, last_name, email, phone, notes, post, deleted, role_id, login]):
            employees = self.pgsql_connetction.session.query(Employees).filter(

                    Employees.id == id if id else True,
                    Employees.first_name.like(f'%{first_name}%') if first_name else True,
                    Employees.last_name.like(f'%{last_name}%') if last_name else True,
                    Employees.email == email if email else True,
                    Employees.phone.like(f'%{phone}%') if phone else True,
                    Employees.notes.like(f'%{notes}%') if notes else True,
                    Employees.post.like(f'%{post}%') if post else True,
                    Employees.deleted == bool(deleted) if deleted else True,
                    Employees.role_id == role_id if role_id else True,
                    Employees.login == login if login else True

            )
        else:
            employees = self.pgsql_connetction.session.query(Employees)

        self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = employees.count()
        result['count'] = count

        max_page = count // 50 if count % 50 > 0 else count // 50 - 1

        if page > max_page and max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []
        for row in employees[50 * page: 50 * (page + 1)]:
            balance = self.pgsql_connetction.session.query(func.sum(Payrolls.income + Payrolls.outcome)) \
                .filter(Payrolls.employee_id == row.id) \
                .filter(Payrolls.deleted != True).scalar()
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
                },
                'login': row.login,
                'password': row.password,
                'table_headers': [{
                    'id': head.id,
                    'title': head.title,
                    'field': head.field,
                    'width': head.width,
                    'employee_id': head.employee_id,
                    'visible': head.visible
                } for head in row.table_headers] if row.table_headers else [],
                'payrules': [{
                    'id': pr.id,
                    'type_rule': pr.type_rule,
                    'order_type': pr.order_type,
                    'method': pr.method,
                    'coefficient': pr.coefficient,
                    'count_coeff': pr.count_coeff,
                    'fix_salary': pr.fix_salary
                } for pr in row.payrules] if row.payrules else [],
                'balance': balance
            })

        result['data'] = data
        result['page'] = page
        return result

    def edit_employee(self, id, first_name, last_name, email, phone, notes, post, deleted, inn, doc_name,
                     permissions, role_id, login, password=None):
        self.pgsql_connetction.session.query(Employees).filter_by(id=id if type(id) == int else None).update({
                'first_name': first_name if first_name else Employees.first_name,
                'last_name': last_name if last_name else Employees.last_name,
                'email': email if email else Employees.email,
                'phone': phone if phone else Employees.phone,
                'notes': notes if notes else Employees.notes,
                'deleted': deleted if deleted != None else Employees.deleted,
                'inn': inn if inn else Employees.inn,
                'doc_name': doc_name if doc_name else Employees.doc_name,
                'post': post if post else Employees.post,
                'role_id': role_id if role_id else Employees.role_id,
                'permissions': permissions if permissions else Employees.permissions,
                'login': login if login else Employees.login,
                'password': password if password else Employees.password
        })
        self.pgsql_connetction.session.commit()
        return self.get_employee()

    def del_employee(self, id):
        employees = self.pgsql_connetction.session.query(Employees).get(id if type(id) == int else 0)
        if employees:
            self.pgsql_connetction.session.delete(employees)
            self.pgsql_connetction.session.commit()
            return self.get_employee()

    def cange_userpassword(self, id, password):
        self.pgsql_connetction.session.query(Employees).filter_by(id=id if type(id) == int else None).update({
            'password': password
        })
        return self.get_employee()

    # Таблица ПОЛЕЙ ТАБЛИЦЫ ЗАКАЗОВ =======================================================================

    def add_table_headers(self, title, field, width, employee_id, visible=True):

        table_headers = TableHeaders(
            title=title,
            field=field,
            width=width,
            employee_id=employee_id,
            visible=visible
        )
        self.pgsql_connetction.session.add(table_headers)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(table_headers)
        return table_headers.id

    def get_table_headers(self, id=None, title=None, field=None, employee_id=None, visible=None ):

        if any([id, title, field, employee_id, visible]):
            table_headers = self.pgsql_connetction.session.query(TableHeaders).filter(
                and_(
                    TableHeaders.id == id if id else True,
                    TableHeaders.title in title if title else True,
                    TableHeaders.field in field if field else True,
                    TableHeaders.employee_id == employee_id if employee_id else True,
                    TableHeaders.visible == visible if visible else True
                )
            )
        else:
            table_headers = self.pgsql_connetction.session.query(TableHeaders)

        self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = table_headers.count()
        result['count'] = count

        data = []
        for row in table_headers:
            data.append({
                'id': row.id,
                'title': row.title,
                'field': row.field,
                'width': row.width,
                'employee_id': row.employee_id,
                'visible': row.visible
            })

        result['data'] = data
        return result

    def edit_table_headers(self, id, title, field, width, employee_id, visible):

        self.pgsql_connetction.session.query(TableHeaders).filter_by(id=id).update({
            'title': title if title else TableHeaders.title,
            'field': field if field else TableHeaders.field,
            'width': width if width else TableHeaders.width,
            'employee_id': employee_id if employee_id else TableHeaders.employee_id,
            'visible': visible if visible != None else TableHeaders.visible
        })
        self.pgsql_connetction.session.commit()
        return self.get_table_headers()

    def del_table_headers(self, id):

        table_headers = self.pgsql_connetction.session.query(TableHeaders).get(id)
        if table_headers:
            self.pgsql_connetction.session.delete(table_headers)
            self.pgsql_connetction.session.commit()
            return self.get_table_headers()

    # Таблица ВЛОЖЕНИЯ ==================================================================================

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
                'created_by_id': created_by_id if created_by_id else Attachments.created_by_id,
                'created_at': created_at if created_at else Attachments.created_at,
                'filename': filename if filename else Attachments.filename,
                'url': url if url else Attachments.url,
                'order_id': order_id if order_id else Attachments.order_id
        })
        return self.get_attachments()

    def del_attachments(self, id):
        attachments = self.pgsql_connetction.session.query(Attachments).get(id if type(id) == int else 0)
        if attachments:
            self.pgsql_connetction.session.delete(attachments)
            self.pgsql_connetction.session.commit()
            return self.get_attachments()

    # Таблица ФИЛИФЛОВ ==================================================================================

    def add_branch(self,
                   name,
                   color,
                   address,
                   phone,
                   icon,
                   orders_type_id,
                   orders_type_strategy,
                   orders_prefix,
                   documents_prefix,
                   employees,
                   deleted):

        branch = Branch(
            name=name,
            color=color,
            address=address,
            phone=phone,
            icon=icon,
            orders_type_id=orders_type_id,
            orders_type_strategy=orders_type_strategy,
            orders_prefix=orders_prefix,
            documents_prefix=documents_prefix,
            employees=employees,
            deleted=deleted
        )
        self.pgsql_connetction.session.add(branch)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(branch)
        return branch.id

    def get_branch(self, id=None, name=None, deleted=None, page=0):

        if any([id, name, deleted != None]):
            branch = self.pgsql_connetction.session.query(Branch).filter(
                and_(
                    Branch.id == id if id else True,
                    Branch.name.like(f'%{name}%') if name else True,
                    (Branch.deleted if deleted else not Branch.deleted) if deleted != None else True
                )
            )
        else:
            branch = self.pgsql_connetction.session.query(Branch)

        self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = branch.count()
        result['count'] = count

        max_page = count // 50 if count % 50 > 0 else count // 50 - 1

        if page > max_page and max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []
        for row in branch[50 * page: 50 * (page + 1)]:
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

        result['data'] = data
        result['page'] = page
        return result

    def edit_branch(self,
                    id,
                    name,
                    address,
                    phone,
                    color,
                    icon,
                    orders_type_id,
                    orders_type_strategy,
                    orders_prefix,
                    documents_prefix,
                    employees,
                    deleted):

        self.pgsql_connetction.session.query(Branch).filter_by(id=id).update({
            'name': name if name else Branch.name,
            'address': address if address else Branch.address,
            'phone': phone if phone else Branch.phone,
            'color': color if color else Branch.color,
            'icon': icon if icon else Branch.icon,
            'orders_type_id': orders_type_id if orders_type_id else Branch.orders_type_id,
            'orders_type_strategy': orders_type_strategy if orders_type_strategy else Branch.orders_type_strategy,
            'orders_prefix': orders_prefix if orders_prefix else Branch.orders_prefix,
            'documents_prefix': documents_prefix if documents_prefix else Branch.documents_prefix,
            'employees': employees if employees else Branch.employees,
            'deleted': deleted if deleted != None else Branch.deleted
        })
        self.pgsql_connetction.session.commit()
        return self.get_branch(id=id)

    def del_branch(self, id):

        branch = self.pgsql_connetction.session.query(Branch).get(id)
        if branch:
            self.pgsql_connetction.session.delete(branch)
            self.pgsql_connetction.session.commit()
            return self.get_branch(id=id)

    # Таблица ДНЕЙ РАСПИСАНИЯ =========================================================================

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
            'start_time': start_time if start_time else Schedule.start_time,
            'end_time': end_time if end_time else Schedule.end_time,
            'work_day': work_day if work_day else Schedule.work_day,
            'week_day': week_day if week_day else Schedule.week_day,
            'branch_id': branch_id if branch_id else Schedule.branch_id
        })
        self.pgsql_connetction.session.commit()
        return self.get_schedule(id=id)

    def del_schedule(self, id):

        schedule = self.pgsql_connetction.session.query(Schedule).get(id)
        if schedule:
            self.pgsql_connetction.session.delete(schedule)
            self.pgsql_connetction.session.commit()
            return self.get_schedule()

    # Таблица НАЦЕНОК ==================================================================================

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
                    DiscountMargin.deleted == deleted if deleted != None else True,
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
            'title': title if title else DiscountMargin.title,
            'margin': margin if margin else DiscountMargin.margin,
            'margin_type': margin_type if margin_type else DiscountMargin.margin_type,
            'deleted': deleted if deleted != None else DiscountMargin.deleted
        })
        self.pgsql_connetction.session.commit()
        return self.get_discount_margin()

    def del_discount_margin(self, id):

        discount_margin = self.pgsql_connetction.session.query(DiscountMargin).get(id)
        if discount_margin:
            self.pgsql_connetction.session.delete(discount_margin)
            self.pgsql_connetction.session.commit()
            return self.get_discount_margin()


    # Таблица ТИПОВ ЗАКАЗА ==================================================================================

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
            'name': name if name else OrderType.name
        })
        self.pgsql_connetction.session.commit()
        return self.get_order_type()

    def del_order_type(self, id):

        order_type = self.pgsql_connetction.session.query(OrderType).get(id)
        if order_type:
            self.pgsql_connetction.session.delete(order_type)
            self.pgsql_connetction.session.commit()
            return self.get_order_type()

    # Таблица ГРУППЫ СТАТУСОВ ==================================================================================

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
            'name': name if name else StatusGroup.name,
            'type_group': type_group if type_group else StatusGroup.type_group,
            'color': color if color else StatusGroup.color,
        })
        self.pgsql_connetction.session.commit()
        return self.get_status_group()

    def del_status_group(self, id):

        status_group = self.pgsql_connetction.session.query(StatusGroup).get(id)
        if status_group:
            self.pgsql_connetction.session.delete(status_group)
            self.pgsql_connetction.session.commit()
            return self.get_status_group()

 # Таблица СТАТУСОВ ==================================================================================

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

    def get_status(self, id=None, name=None, color=None, group=None,page=0):
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
            'name': name if name else Status.name,
            'color': color if color else Status.color,
            'group': group if group else Status.group,
            'deadline': deadline if deadline else Status.deadline,
            'comment_required': comment_required if comment_required else Status.comment_required,
            'payment_required': payment_required if payment_required else Status.payment_required,
            'available_to': available_to if available_to else Status.available_to
        })
        self.pgsql_connetction.session.commit()
        return self.get_status()

    def del_status(self, id):

        status = self.pgsql_connetction.session.query(Status).get(id)
        if status:
            self.pgsql_connetction.session.delete(status)
            self.pgsql_connetction.session.commit()
            return self.get_status()

 # Таблица ОПЕРАЦИЙ ==================================================================================

    def add_operations(self,
                       amount,
                       cost,
                       discount_value,
                       engineer_id,
                       price,
                       total,
                       title,
                       comment,
                       deleted,
                       warranty_period,
                       created_at,
                       order_id,
                       dict_id
                       ):

        operations = Operations(
            amount=amount,
            cost=cost,
            discount_value=discount_value,
            engineer_id=engineer_id,
            price=price,
            total=total,
            title=title,
            comment=comment,
            deleted=deleted,
            warranty_period=warranty_period,
            created_at=created_at,
            order_id=order_id,
            dict_id=dict_id
        )
        self.pgsql_connetction.session.add(operations)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(operations)
        return operations.id

    def get_operations(self,
                       id=None,
                       cost=None,
                       discount_value=None,
                       engineer_id=None,
                       price=None,
                       total=None,
                       title=None,
                       warranty=None,
                       deleted=None,
                       warranty_period=None,
                       created_at=None,
                       updated_at=None,
                       order_id=None,
                       dict_id=None,
                       page=0):

        if any([id, cost, discount_value, engineer_id, price, total, title, warranty != None,
                deleted != None, warranty_period, created_at, updated_at, order_id, dict_id]):
            operations = self.pgsql_connetction.session.query(Operations).filter(
                and_(
                    Operations.id == id if id else True,
                    Operations.title.like(f'%{title}%') if title else True,
                    Operations.cost == cost if cost else True,
                    Operations.discount_value == discount_value if discount_value else True,
                    Operations.price == price if price else True,
                    Operations.total == total if total else True,
                    Operations.discount_value == discount_value if discount_value else True,
                    Operations.warranty == warranty if warranty != None else True,
                    Operations.deleted == deleted if deleted != None else True,
                    Operations.order_id == order_id if order_id else True,
                    Operations.dict_id == dict_id if dict_id else True,
                    Operations.warranty_period == warranty_period if warranty_period else True,
                    (Operations.created_at >= created_at[0] if created_at[0] else True) if created_at else True,
                    (Operations.created_at <= created_at[1] if created_at[1] else True) if created_at else True,
                )
            )
        else:
            operations = self.pgsql_connetction.session.query(Operations)

        self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = operations.count()
        result['count'] = count

        max_page = count // 50 if count % 50 > 0 else count // 50 - 1

        if page > max_page and max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []
        for row in operations[50 * page: 50 * (page + 1)]:
            data.append({
                'id': row.id,
                'amount': row.amount,
                'cost': row.cost,
                'discount_value': row.discount_value,
                'engineer_id': row.engineer_id,
                'price': row.price,
                'total': row.total,
                'title': row.title,
                'comment': row.comment,
                'warranty': (row.created_at + row.warranty_period) > time_now(),
                'deleted': row.deleted,
                'warranty_period': row.warranty_period,
                'created_at': row.created_at,
                'updated_at': row.updated_at,
                'order_id': row.order_id,
                'dict_id': row.dict_id
            })

        result['data'] = data
        result['page'] = page
        return result

    def edit_operations(self,
                       id,
                       amount,
                       cost,
                       discount_value,
                       engineer_id,
                       price,
                       total,
                       title,
                       comment,
                       deleted,
                       warranty_period,
                       created_at,
                       order_id,
                       dict_id):

        self.pgsql_connetction.session.query(Operations).filter_by(id=id).update({
            'amount': amount if amount else Operations.amount,
            'cost': cost if cost else Operations.cost,
            'discount_value': discount_value if discount_value else Operations.discount_value,
            'engineer_id': engineer_id if engineer_id else Operations.engineer_id,
            'price': price if price else Operations.price,
            'total': total if total else Operations.total,
            'title': title if title else Operations.title,
            'comment': comment if comment else Operations.comment,
            'deleted': deleted if deleted != None else Operations.deleted,
            'warranty_period': warranty_period if warranty_period else Operations.warranty_period,
            'created_at': created_at if created_at else Operations.created_at,
            'order_id': order_id if order_id else Operations.order_id,
            'dict_id': dict_id if dict_id else Operations.dict_id
        })
        self.pgsql_connetction.session.commit()
        return self.get_operations()

    def del_operations(self, id):

        operations = self.pgsql_connetction.session.query(Operations).get(id)
        if operations:
            self.pgsql_connetction.session.delete(operations)
            self.pgsql_connetction.session.commit()
            return self.get_operations()

 # Таблица ЗАПЧАСТЕЙ ==================================================================================

    def add_oder_parts(self,
                       amount,
                       cost,
                       discount_value,
                       engineer_id,
                       price,
                       total,
                       title,
                       comment,
                       deleted,
                       warranty_period,
                       created_at,
                       order_id):

        oder_parts = OderParts(
            amount=amount,
            cost=cost,
            discount_value=discount_value,
            engineer_id=engineer_id,
            price=price,
            total=total,
            title=title,
            comment=comment,
            deleted=deleted,
            warranty_period=warranty_period,
            created_at=created_at,
            order_id=order_id
        )
        self.pgsql_connetction.session.add(oder_parts)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(oder_parts)
        return oder_parts.id

    def get_oder_parts(self,
                       id=None,
                       cost=None,
                       discount_value=None,
                       engineer_id=None,
                       price=None,
                       total=None,
                       title=None,
                       deleted=None,
                       warranty_period=None,
                       created_at=None,
                       updated_at=None,
                       order_id=None,
                       page=0):

        if any([id, cost, discount_value, engineer_id, price, total, title, deleted != None,
                warranty_period, created_at, updated_at, order_id]):
            oder_parts = self.pgsql_connetction.session.query(OderParts).filter(
                and_(
                    OderParts.id == id if id else True,
                    OderParts.title.like(f'%{title}%') if title else True,
                    OderParts.cost == cost if cost else True,
                    OderParts.discount_value == discount_value if discount_value else True,
                    OderParts.price == price if price else True,
                    OderParts.discount_value == discount_value if discount_value else True,
                    OderParts.total == total if total else True,
                    OderParts.deleted == deleted if deleted != None else True,
                    OderParts.warranty_period == warranty_period if warranty_period else True,
                    OderParts.order_id == order_id if order_id else True,
                    (OderParts.created_at >= created_at[0] if created_at[0] else True) if created_at else True,
                    (OderParts.created_at <= created_at[1] if created_at[1] else True) if created_at else True,
                )
            )
        else:
            oder_parts = self.pgsql_connetction.session.query(OderParts)

        self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = oder_parts.count()
        result['count'] = count

        max_page = count // 50 if count % 50 > 0 else count // 50 - 1

        if page > max_page and max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []
        for row in oder_parts[50 * page: 50 * (page + 1)]:
            data.append({
                'id': row.id,
                'amount': row.amount,
                'cost': row.cost,
                'discount_value': row.discount_value,
                'engineer_id': row.engineer_id,
                'price': row.price,
                'total': row.total,
                'title': row.title,
                'comment': row.comment,
                'deleted': row.deleted,
                'warranty': (row.created_at + row.warranty_period) > time_now(),
                'warranty_period': row.warranty_period,
                'created_at': row.created_at,
                'updated_at': row.updated_at,
                'order_id': row.order_id
            })

        result['data'] = data
        result['page'] = page
        return result

    def edit_oder_parts(self,
                       id,
                       amount,
                       cost,
                       discount_value,
                       engineer_id,
                       price,
                       total,
                       title,
                       comment,
                       deleted,
                       warranty_period,
                       created_at,
                       order_id):

        self.pgsql_connetction.session.query(OderParts).filter_by(id=id).update({
            'amount': amount if amount else OderParts.amount,
            'cost': cost if cost else OderParts.cost,
            'discount_value': discount_value if discount_value else OderParts.discount_value,
            'engineer_id': engineer_id if engineer_id else OderParts.engineer_id,
            'price': price if price else OderParts.price,
            'total': total if total else OderParts.total,
            'title': title if title else OderParts.title,
            'comment': comment if comment else OderParts.comment,
            'deleted': deleted if deleted != None else OderParts.deleted,
            'warranty_period': warranty_period if warranty_period else OderParts.warranty_period,
            'created_at': created_at if created_at else OderParts.created_at,
            'order_id': order_id if order_id else OderParts.order_id,
        })
        self.pgsql_connetction.session.commit()
        return self.get_oder_parts()

    def del_oder_parts(self, id):

        oder_parts = self.pgsql_connetction.session.query(OderParts).get(id)
        if oder_parts:
            self.pgsql_connetction.session.delete(oder_parts)
            self.pgsql_connetction.session.commit()
            return self.get_oder_parts()

# Таблица ТЕЛЕФОНОВ ==================================================================================

    def add_phone(self, number, title, client_id):

        phones = Phones(
            number=number,
            title=title,
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
                'client_id': row.client_id
            })

        result['data'] = data
        result['page'] = page
        return result

    def edit_phones(self, id, number, title, client_id):

        self.pgsql_connetction.session.query(Phones).filter_by(id=id).update({
            'number': number if number else Phones.number,
            'title': title if title else Phones.title,
            'client_id': client_id if client_id else Phones.client_id
        })
        self.pgsql_connetction.session.commit()
        return self.get_phones()

    def del_phones(self, id):

        phones = self.pgsql_connetction.session.query(Phones).get(id)
        if phones:
            self.pgsql_connetction.session.delete(phones)
            self.pgsql_connetction.session.commit()
            return self.get_phones()

    # Таблица КЛИЕНТОВ ==================================================================================

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
                    Clients.name.like(f'%{name}%') if name else True,
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
                    Clients.email.like(f'%{email}%') if email else True,
                    # (Clients.created_at >= created_at[0] if created_at[0] else True) if created_at else True,
                    # (Clients.created_at <= created_at[1] if created_at[1] else True) if created_at else True,
                    Clients.juridical == juridical if juridical != None else True,
                    Clients.deleted == deleted if deleted != None else True,
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
                        'title': ph.title
                    } for ph in row.phone] if row.phone else [],
                'ad_campaign': {
                    'id': row.ad_campaign.id,
                    'name': row.ad_campaign.name
                }
            })

        result['data'] = data
        result['page'] = page
        return result

    def edit_clients(self,
                     id,
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

                     tags
                     ):

        self.pgsql_connetction.session.query(Clients).filter_by(id=id).update({
            'juridical': juridical if juridical != None else Clients.juridical,
            'supplier': supplier if supplier != None else Clients.supplier,
            'conflicted': conflicted if conflicted != None else Clients.conflicted,
            'should_send_email': should_send_email if should_send_email != None else Clients.should_send_email,
            'deleted': deleted if deleted != None else Clients.deleted,
            'discount_good_type': discount_good_type if discount_good_type != None else Clients.discount_good_type,
            'discount_materials_type': discount_materials_type if discount_materials_type != None else Clients.discount_materials_type,
            'discount_service_type': discount_service_type if discount_service_type != None else Clients.discount_service_type,

            'name': name if name else Clients.name,
            'name_doc': name_doc if name_doc else Clients.name_doc,
            'email': email if email else Clients.email,
            'address': address if address else Clients.address,
            'discount_code': discount_code if discount_code else Clients.discount_code,
            'notes': notes if notes else Clients.notes,
            'ogrn': ogrn if ogrn else Clients.ogrn,
            'inn': inn if inn else Clients.inn,
            'kpp': kpp if kpp else Clients.kpp,
            'juridical_address': juridical_address if juridical_address else Clients.juridical_address,
            'director': director if director else Clients.director,
            'bank_name': bank_name if bank_name else Clients.bank_name,
            'settlement_account': settlement_account if settlement_account else Clients.settlement_account,
            'corr_account': corr_account if corr_account else Clients.corr_account,
            'bic': bic if bic else Clients.bic,

            'discount_goods': discount_goods if discount_goods else Clients.discount_goods,
            'discount_materials': discount_materials if discount_materials else Clients.discount_materials,
            'discount_services': discount_services if discount_services else Clients.discount_services,
            'discount_service_margin_id': discount_service_margin_id if discount_service_margin_id else Clients.discount_service_margin_id,

            'ad_campaign_id': ad_campaign_id if ad_campaign_id else Clients.ad_campaign_id,
            'discount_goods_margin_id': discount_goods_margin_id if discount_goods_margin_id else Clients.discount_goods_margin_id,
            'discount_materials_margin_id': discount_materials_margin_id if discount_materials_margin_id else Clients.discount_materials_margin_id,

            'tags': tags if tags else Clients.tags
        })
        self.pgsql_connetction.session.commit()
        return self.get_clients()

    def del_clients(self, id):

        clients = self.pgsql_connetction.session.query(Clients).get(id)
        if clients:
            self.pgsql_connetction.session.delete(clients)
            self.pgsql_connetction.session.commit()
            return self.get_clients()

    # Таблица ЗАКАЗОВ ==================================================================================

    def add_orders(self,
                   created_at,
                   done_at,
                   closed_at,
                   assigned_at,
                   duration,
                   estimated_done_at,
                   scheduled_for,
                   warranty_date,
                   status_deadline,

                   ad_campaign_id,
                   branch_id,
                   status_id,
                   client_id,
                   order_type_id,
                   kindof_good,
                   brand,
                   subtype,
                   model,
                   closed_by_id,
                   created_by_id,
                   engineer_id,
                   manager_id,

                   id_label,
                   prefix,
                   serial,
                   malfunction,
                   packagelist,
                   appearance,
                   manager_notes,
                   engineer_notes,
                   resume,
                   cell,

                   estimated_cost,
                   missed_payments,
                   discount_sum,
                   payed,
                   price,

                   urgent,
                   ):

        orders = Orders(
            created_at=created_at,
            done_at=done_at,
            closed_at=closed_at,
            assigned_at=assigned_at,
            duration=duration,
            estimated_done_at=estimated_done_at,
            scheduled_for=scheduled_for,
            warranty_date=warranty_date,
            status_deadline=status_deadline,

            ad_campaign_id=ad_campaign_id,
            branch_id=branch_id,
            status_id=status_id,
            client_id=client_id,
            order_type_id=order_type_id,
            kindof_good_id=kindof_good,
            brand_id=brand,
            subtype_id=subtype,
            model_id=model,
            closed_by_id=closed_by_id,
            created_by_id=created_by_id,
            engineer_id=engineer_id,
            manager_id=manager_id,

            id_label=id_label,
            prefix=prefix,
            serial=serial,
            malfunction=malfunction,
            packagelist=packagelist,
            appearance=appearance,
            manager_notes=manager_notes,
            engineer_notes=engineer_notes,
            resume=resume,
            cell=cell,

            estimated_cost=estimated_cost,
            missed_payments=missed_payments,
            discount_sum=discount_sum,
            payed=payed,
            price=price,

            urgent=urgent
        )
        self.pgsql_connetction.session.add(orders)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(orders)
        return orders.id

    def get_orders(self,
            id=None,
            created_at=None,
            done_at=None,
            closed_at=None,
            assigned_at=None,
            estimated_done_at=None,
            scheduled_for=None,
            warranty_date=None,

            ad_campaign_id=None,
            branch_id=None,
            status_id=None,
            client_id=None,
            order_type_id=None,
            kindof_good=None,
            brand=None,
            subtype=None,
            model=None,
            cell=None,
            engineer_id=None,
            manager_id=None,

            id_label=None,
            serial=None,
            client_name=None,
            client_phone=None,
            search=None,

            urgent=None,
            overdue=None,
            status_overdue=None,

            field_sort='id',
            sort='asc',
            page=0):



        if any([id, created_at, done_at, closed_at, assigned_at, estimated_done_at, scheduled_for, warranty_date,
                ad_campaign_id, branch_id, status_id, client_id, order_type_id, engineer_id, manager_id, id_label,
                kindof_good, brand, model, subtype, serial, client_name, client_phone, urgent, overdue, status_overdue,
                search, cell]):

            if search:
                # search = search.lower()
                orders = self.pgsql_connetction.session.query(Orders)\
                    .join(Orders.client) \
                    .options(contains_eager(Orders.client)) \
                    .filter(
                    or_(
                        Orders.id_label.ilike(f'%{search}%'),
                        # func.lower(Orders.kindof_good).like(f'%{search}%'),
                        # Orders.brand.ilike(f'%{search}%'),
                        # Orders.model.ilike(f'%{search}%'),
                        # Orders.subtype.ilike(f'%{search}%'),
                        Orders.serial.ilike(f'%{search}%'),
                        Orders.client.property.mapper.class_.name.ilike(f'%{search}%'),
                        # Orders.client.property.mapper.class_.phone[0].ilike(f'%{search}%'),
                        Orders.id_label.ilike(f'%{search}%'),
                    )
                ).order_by(
                    getattr(Orders, field_sort, 'id') if sort == 'asc' else desc(getattr(Orders, field_sort, 'id')))
            else:
                orders = self.pgsql_connetction.session.query(Orders).join(Orders.client).filter(
                    and_(
                        Orders.id == id if id else True,
                        (Orders.created_at >= created_at[0] if created_at[0] else True) if created_at else True,
                        (Orders.created_at <= created_at[1] if created_at[1] else True) if created_at else True,
                        (Orders.done_at >= done_at[0] if done_at[0] else True) if done_at else True,
                        (Orders.done_at <= done_at[1] if done_at[1] else True) if done_at else True,
                        (Orders.closed_at >= closed_at[0] if closed_at[0] else True) if closed_at else True,
                        (Orders.closed_at <= closed_at[1] if closed_at[1] else True) if closed_at else True,
                        (Orders.assigned_at >= assigned_at[0] if assigned_at[0] else True) if assigned_at else True,
                        (Orders.assigned_at <= assigned_at[1] if assigned_at[1] else True) if assigned_at else True,
                        (Orders.estimated_done_at >= estimated_done_at[0] if estimated_done_at[0] else True) if estimated_done_at else True,
                        (Orders.estimated_done_at <= estimated_done_at[1] if estimated_done_at[1] else True) if estimated_done_at else True,
                        (Orders.scheduled_for >= scheduled_for[0] if scheduled_for[0] else True) if scheduled_for else True,
                        (Orders.scheduled_for <= scheduled_for[1] if scheduled_for[1] else True) if scheduled_for else True,
                        (Orders.warranty_date >= warranty_date[0] if warranty_date[0] else True) if warranty_date else True,
                        (Orders.warranty_date <= warranty_date[1] if warranty_date[1] else True) if warranty_date else True,

                        Orders.ad_campaign_id.in_(ad_campaign_id) if ad_campaign_id else True,
                        Orders.branch_id.in_(branch_id) if branch_id else True,
                        Orders.status_id.in_(status_id) if status_id else True,
                        Orders.client_id.in_(client_id) if client_id else True,
                        Orders.order_type_id.in_(order_type_id) if order_type_id else True,
                        Orders.engineer_id.in_(engineer_id) if engineer_id else True,
                        Orders.manager_id.in_(manager_id) if manager_id else True,

                        Orders.cell == cell if cell else True,
                        Orders.id_label.ilike(f'%{id_label}%') if id_label else True,
                        # Orders.kindof_good == kindof_good if kindof_good else True,
                        # Orders.brand == brand if brand else True,
                        # Orders.model == model if model else True,
                        # Orders.subtype == subtype if subtype else True,
                        # Orders.serial.ilike(f'%{serial}%') if serial else True,
                        Orders.client.property.mapper.class_.name.ilike(f'%{client_name}%') if client_name else True,
                        # Orders.client.property.mapper.class_.phone[0].ilike(f'%{client_name}%') if client_phone else True,


                        Orders.urgent == urgent if urgent != None else True,
                        (Orders.estimated_done_at < time_now()) if overdue else True,
                        (Orders.status_deadline < time_now()) if status_overdue else True
                    )
                ).order_by(getattr(Orders, field_sort, 'id') if sort == 'asc' else desc(getattr(Orders, field_sort, 'id')))
        else:
            orders = self.pgsql_connetction.session.query(Orders)\
                .order_by(getattr(Orders, field_sort, 'id') if sort == 'asc' else desc(getattr(Orders, field_sort, 'id')))

        self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = orders.count()
        result['count'] = count

        max_page = count // 50 if count % 50 > 0 else count // 50 - 1

        if page > max_page and max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []
        for row in orders[50 * page: 50 * (page + 1)]:
            data.append({
                'id': row.id,
                'created_at': row.created_at,
                'updated_at': row.updated_at,
                'done_at': row.done_at,
                'closed_at': row.closed_at,
                'assigned_at': row.assigned_at,
                'duration': row.duration,
                'estimated_done_at': row.estimated_done_at,
                'scheduled_for': row.scheduled_for,
                'warranty_date': row.warranty_date,
                'status_deadline': row.status_deadline,

                'id_label': row.id_label,
                'prefix': row.prefix,
                'serial': row.serial,
                'malfunction': row.malfunction,
                'packagelist': row.packagelist,
                'appearance': row.appearance,
                'engineer_notes': row.engineer_notes,
                'manager_notes': row.manager_notes,
                'resume': row.resume,
                'cell': row.cell,

                'estimated_cost': row.estimated_cost,
                'missed_payments': row.missed_payments,
                'discount_sum': row.discount_sum,
                'payed': row.payed,
                'price': row.price,
                'remaining': row.estimated_done_at - time_now() if row.estimated_done_at else None,
                'remaining_status': row.status_deadline - time_now() if row.status_deadline else None,
                'remaining_warranty': row.warranty_date - time_now() if row.warranty_date else None,

                'overdue': row.estimated_done_at > time_now() if row.estimated_done_at else False,
                'status_overdue': row.status_deadline > time_now() if row.status_deadline else False,
                'urgent': row.urgent,
                'warranty_measures': row.warranty_date < time_now() if row.warranty_date else False,

                'ad_campaign': {
                    'id': row.ad_campaign.id,
                    'name': row.ad_campaign.name
                } if row.ad_campaign else {},
                'branch': {
                    'id': row.branch.id,
                    'name': row.branch.name
                } if row.branch else {},
                'status': {
                    'id': row.status.id,
                    'name': row.status.name,
                    'color': row.status.color,
                    'group': row.status.group
                } if row.status else {},
                'client': {
                    'id': row.client.id,
                    'ad_campaign': {
                        'id': row.client.ad_campaign.id,
                        'name': row.client.ad_campaign.name
                    },
                    'address': row.client.address,
                    'conflicted': row.client.conflicted,
                    'name_doc': row.client.name_doc,
                    'discount_code': row.client.discount_code,
                    'discount_goods': row.client.discount_goods,
                    'discount_goods_margin_id': row.client.discount_goods_margin_id,
                    'discount_materials': row.client.discount_materials,
                    'discount_materials_margin_id': row.client.discount_materials_margin_id,
                    'discount_services': row.client.discount_services,
                    'email': row.client.email,
                    'juridical': row.client.juridical,
                    'created_at': row.client.created_at,
                    'updated_at': row.client.updated_at,
                    'name': row.client.name,
                    'notes': row.client.notes,
                    'supplier': row.client.supplier,
                    'phone': [{
                        'id': ph.id,
                        'number': ph.number,
                        'title': ph.title
                    } for ph in row.client.phone] if row.client.phone else []
                } if row.client else {},
                # 'engineer': {
                #     'id': row.engineer.id,
                #     'first_name': row.engineer.first_name,
                #     'last_name': row.engineer.last_name,
                #     'email': row.engineer.email,
                #     'phone': row.engineer.phone,
                # } if row.engineer else {},
                # 'manager': {
                #     'id': row.manager.id,
                #     'first_name': row.manager.first_name,
                #     'last_name': row.manager.last_name,
                #     'email': row.manager.email,
                #     'phone': row.manager.phone,
                # } if row.manager else {},
                'order_type': {
                    'id': row.order_type.id,
                    'name': row.order_type.name
                } if row.order_type else {},
                'kindof_good': {
                    'id': row.kindof_good.id,
                    'title': row.kindof_good.title,
                    'icon': row.kindof_good.icon,
                } if row.kindof_good else {},
                'brand': {
                    'id': row.brand.id,
                    'title': row.brand.title,
                } if row.brand else {},
                'subtype': {
                    'id': row.subtype.id,
                    'title': row.subtype.title,
                } if row.subtype else {},
                'model': {
                    'id': row.model.id,
                    'title': row.model.title,
                } if row.model else {},
                'closed_by_id': row.closed_by_id,
                'created_by_id': row.created_by_id,
                'engineer_id': row.engineer_id,
                'manager_id': row.manager_id,
                'operations': [{
                    'id': operat.id,
                    'amount': operat.amount,
                    'cost': operat.cost,
                    'discount_value': operat.discount_value,
                    'engineer_id': operat.engineer_id,
                    'price': operat.price,
                    'total': operat.total,
                    'warranty': (operat.created_at + operat.warranty_period) > time_now(),
                    'title': operat.title,
                    'comment': operat.comment,
                    'deleted': operat.deleted,
                    'warranty_period': operat.warranty_period,
                    'created_at': operat.created_at,
                    'dict_service': {
                        'id': operat.dict_service.id,
                        'title': operat.dict_service.title,
                        'earnings_percent': operat.dict_service.earnings_percent,
                        'earnings_summ': operat.dict_service.earnings_summ
                    } if operat.dict_service else {},
                } for operat in row.operations] if row.operations else [],
                'parts': [{
                    'id': part.id,
                    'amount': part.amount,
                    'cost': part.cost,
                    'discount_value': part.discount_value,
                    'engineer_id': part.engineer_id,
                    'price': part.price,
                    'total': part.total,
                    'warranty': (part.created_at + part.warranty_period) > time_now(),
                    'title': part.title,
                    'comment': part.comment,
                    'deleted': part.deleted,
                    'warranty_period': part.warranty_period,
                    'created_at': part.created_at
                } for part in row.parts] if row.parts else [],
                # 'attachments': [{
                #     'id': attachment.id,
                #     'amount': attachment.amount,
                #     'cost': attachment.cost,
                #     'discount_value': attachment.discount_value,
                #     'engineer_id': attachment.engineer_id,
                #     'price': attachment.price,
                #     'warranty': attachment.warranty,
                #     'title': attachment.title,
                #     'warranty_period': attachment.warranty_period,
                #     'created_at': attachment.created_at
                # } for attachment in row.attachments] if row.attachments else [],
                'payments': [
                    {
                        'id': payment.id,
                        'description': payment.description,
                        'income': payment.income,
                        'outcome': payment.outcome,
                        'direction': payment.direction,
                        'can_print_fiscal': payment.can_print_fiscal,
                        'deleted': payment.deleted,
                        'is_fiscal': payment.is_fiscal,
                        'created_at': payment.created_at,
                        'custom_created_at': payment.custom_created_at,
                        'tags': payment.tags,
                        'cashbox_id': payment.cashbox_id,
                        'client_id': payment.client_id,
                        'employee': {
                            'id': payment.employee.id,
                            'name': f'{payment.employee.last_name} {payment.employee.first_name}'
                        }
                    } for payment in row.payments
                ] if row.payments else []
            })

        result['data'] = data
        result['page'] = page
        return result

    def edit_orders(self,
                    id,
                    created_at=None,
                    done_at=None,
                    closed_at=None,
                    assigned_at=None,
                    duration=None,
                    estimated_done_at=None,
                    scheduled_for=None,
                    warranty_date=None,
                    status_deadline=None,
                    ad_campaign_id=None,
                    branch_id=None,
                    status_id=None,
                    client_id=None,
                    order_type_id=None,
                    closed_by_id=None,
                    created_by_id=None,
                    engineer_id=None,
                    manager_id=None,
                    id_label=None,
                    prefix=None,
                    kindof_good=None,
                    brand=None,
                    model=None,
                    subtype=None,
                    serial=None,
                    malfunction=None,
                    packagelist=None,
                    appearance=None,
                    engineer_notes=None,
                    manager_notes=None,
                    resume=None,
                    cell=None,
                    estimated_cost=None,
                    missed_payments=None,
                    discount_sum=None,
                    payed=None,
                    price=None,
                    urgent=None
                    ):

        self.pgsql_connetction.session.query(Orders).filter_by(id=id).update({
            'created_at': created_at if created_at else Orders.created_at,
            'done_at': done_at if done_at else Orders.done_at,
            'closed_at': closed_at if closed_at else Orders.closed_at,
            'assigned_at': assigned_at if assigned_at else Orders.assigned_at,
            'duration': duration if duration else Orders.duration,
            'estimated_done_at': estimated_done_at if estimated_done_at else Orders.estimated_done_at,
            'scheduled_for': scheduled_for if scheduled_for else Orders.scheduled_for,
            'warranty_date': warranty_date if warranty_date else Orders.warranty_date,
            'status_deadline': status_deadline if status_deadline else Orders.status_deadline,

            'ad_campaign_id': ad_campaign_id if ad_campaign_id else Orders.ad_campaign_id,
            'branch_id': branch_id if branch_id else Orders.branch_id,
            'status_id': status_id if status_id else Orders.status_id,
            'client_id': client_id if client_id else Orders.client_id,
            'order_type_id': order_type_id if order_type_id else Orders.order_type_id,
            'kindof_good_id': kindof_good if kindof_good else Orders.kindof_good_id,
            'brand_id': brand if brand else Orders.brand_id,
            'subtype_id': subtype if subtype else Orders.subtype_id,
            'model_id': model if model else Orders.model_id,
            'closed_by_id': closed_by_id if closed_by_id else Orders.closed_by_id,
            'created_by_id': created_by_id if created_by_id else Orders.created_by_id,
            'engineer_id': engineer_id if engineer_id else Orders.engineer_id,
            'manager_id': manager_id if manager_id else Orders.manager_id,

            'id_label': id_label if id_label else Orders.id_label,
            'prefix': prefix if prefix else Orders.prefix,
            'serial': serial if serial else Orders.serial,
            'malfunction': malfunction if malfunction else Orders.malfunction,
            'packagelist': packagelist if packagelist else Orders.packagelist,
            'appearance': appearance if appearance else Orders.appearance,
            'engineer_notes': engineer_notes if engineer_notes else Orders.engineer_notes,
            'manager_notes': manager_notes if manager_notes else Orders.manager_notes,
            'resume': resume if resume else Orders.resume,
            'cell': cell if cell else Orders.cell,

            'estimated_cost': estimated_cost if estimated_cost else Orders.estimated_cost,
            'missed_payments': missed_payments if missed_payments else Orders.missed_payments,
            'discount_sum': discount_sum if discount_sum else Orders.discount_sum,
            'payed': payed if payed else Orders.payed,
            'price': price if price else Orders.price,

            'urgent': urgent if urgent != None else Orders.urgent,

        })
        self.pgsql_connetction.session.commit()
        return self.get_orders()

    def del_orders(self, id):

        orders = self.pgsql_connetction.session.query(Orders).get(id)
        if orders:
            self.pgsql_connetction.session.delete(orders)
            self.pgsql_connetction.session.commit()
            return self.get_orders()

# Таблица СТРОК МЕНЮ ===============================================================================

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

    def edit_menu_row(self, id, title, img, url, group_name):

        self.pgsql_connetction.session.query(MenuRows).filter_by(id=id).update({
            'title': title if title else MenuRows.title,
            'img': img if img else MenuRows.img,
            'url': url if url else MenuRows.url,
            'group_name': group_name if group_name else MenuRows.group_name

        })
        self.pgsql_connetction.session.commit()
        return self.get_menu_row()

    def del_menu_row(self, id):

        menu_row = self.pgsql_connetction.session.query(MenuRows).get(id)
        if menu_row:
            self.pgsql_connetction.session.delete(MenuRows)
            self.pgsql_connetction.session.commit()
            return self.get_menu_row()

# Таблица БЕДЖЕЙ ===============================================================================

    def add_badges(self, title, img, color):

        badges = Badges(
            title=title,
            img=img,
            color=color
        )
        self.pgsql_connetction.session.add(badges)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(badges)
        return badges.id

    def get_badges(self, employee_id):


        badges = self.pgsql_connetction.session.query(Badges)

        self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = badges.count()
        result['count'] = count

        status = self.get_status()['data']

        status_not_ready = [stat['id'] for stat in status if stat['group'] < 3]
        status_ready = [stat['id'] for stat in status if stat['group'] == 4]

        data = []
        for row in badges:
            data.append({
                'id': row.id,
                'title': row.title,
                'img': row.img,
                'filters': {
                    'page': 0,
                    'sort': 'asc',
                    'sort_field': 'id',
                    'engineer_id': [employee_id],
                    'status_id': status_ready if row.id == 5 else status_not_ready,
                    'urgent': True if row.id == 2 else None,
                    'overdue': True if row.id == 3 else False,
                    'status_overdue': True if row.id == 4 else False
                },
                'count': self.get_orders(
                    engineer_id=[employee_id],
                    status_id=status_ready if row.id == 5 else status_not_ready,
                    urgent=True if row.id == 2 else None,
                    overdue=True if row.id == 3 else False,
                    status_overdue=True if row.id == 4 else False
                )['count'],
                'color': row.color,
                'active': False
            })
        result['data'] = data
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

    def edit_custom_filters(self, id, title, filters, general):

        self.pgsql_connetction.session.query(CustomFilters).filter_by(id=id).update({
            'title': title if title else CustomFilters.title,
            'filters': filters if filters else CustomFilters.filters,
            'general': general if general else CustomFilters.general
        })
        self.pgsql_connetction.session.commit()
        return self.get_custom_filters(1)

    def del_custom_filters(self, id):

        custom_filters = self.pgsql_connetction.session.query(CustomFilters).get(id)
        if custom_filters:
            self.pgsql_connetction.session.delete(custom_filters)
            self.pgsql_connetction.session.commit()
            return self.get_custom_filters(1)

# Таблица ТИПОВ ИЗДЕЛИЙ ==================================================================================

    def add_equipment_type(self, title, icon, url, branches, deleted):

        equipment_type = EquipmentType(
            title=title,
            icon=icon,
            url=url,
            branches=branches,
            deleted=deleted
        )
        self.pgsql_connetction.session.add(equipment_type)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(equipment_type)
        return equipment_type.id

    def get_equipment_type(self, id=None, title=None, deleted=None, page=0):

        if any([id, title, deleted != None]):
            equipment_type = self.pgsql_connetction.session.query(EquipmentType).filter(
                and_(
                    EquipmentType.id == id if id else True,
                    EquipmentType.title.ilike(f'%{title}%') if title else True,
                    (deleted or EquipmentType.deleted.is_(False)) if deleted!=None else True
                )
            ).order_by(EquipmentType.title)
        else:
            equipment_type = self.pgsql_connetction.session.query(EquipmentType).order_by(EquipmentType.title)

        self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = equipment_type.count()
        result['count'] = count

        num = 50

        max_page = count // num if count % num > 0 else count // num - 1

        if page > max_page and max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []
        for row in equipment_type[num * page: num * (page + 1)]:
            data.append({
                'id': row.id,
                'title': row.title,
                'icon': row.icon,
                'url': row.url,
                'branches': row.branches,
                'deleted': row.deleted
            })
                # 'equipment_brand': [{
                #     'id': brand.id,
                #     'title': brand.title,
                #     'icon': brand.icon,
                #     'url': brand.url,
                #     'branches': brand.branches,
                #     'deleted': brand.deleted,
                #     'equipment_subtype': [{
                #         'id': subtype.id,
                #         'title': subtype.title,
                #         'icon': subtype.icon,
                #         'url': subtype.url,
                #         'branches': subtype.branches,
                #         'deleted': subtype.deleted,
                #         'equipment_model': [{
                #             'id': model.id,
                #             'title': model.title,
                #             'icon': model.icon,
                #             'url': model.url,
                #             'branches': model.branches,
                #             'deleted': model.deleted
                #         } for model in subtype.equipment_model] if subtype.equipment_model else []
                #     } for subtype in brand.equipment_subtype] if brand.equipment_subtype else []
                # } for brand in row.equipment_brand] if row.equipment_brand else []


        result['data'] = data
        result['page'] = page
        return result

    def edit_equipment_type(self, id, title=None, icon=None, url=None, branches=None, deleted=None):

        self.pgsql_connetction.session.query(EquipmentType).filter_by(id=id).update({
            'title': title if title else EquipmentType.title,
            'icon': icon if icon else None,
            'url': url if url else EquipmentType.url,
            'branches': branches if branches else EquipmentType.branches,
            'deleted': deleted if deleted != None else EquipmentType.deleted
        })
        self.pgsql_connetction.session.commit()
        return self.get_equipment_type()

    def del_equipment_type(self, id):

        equipment_type = self.pgsql_connetction.session.query(EquipmentType).get(id)
        if equipment_type:
            self.pgsql_connetction.session.delete(equipment_type)
            self.pgsql_connetction.session.commit()
            return self.get_equipment_type()

# Таблица БРЕНДОВ ИЗДЕЛИЙ ==================================================================================

    def add_equipment_brand(self, title,  icon, url, branches, deleted, equipment_type_id):

        equipment_brand = EquipmentBrand(
            title=title,
            icon=icon,
            url=url,
            branches=branches,
            deleted=deleted,
            equipment_type_id=equipment_type_id
        )
        self.pgsql_connetction.session.add(equipment_brand)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(equipment_brand)
        return equipment_brand.id

    def get_equipment_brand(self, id=None, title=None, equipment_type_id=None, deleted=None, page=0):

        if any([id, title, equipment_type_id, deleted!=None]):
            equipment_brand = self.pgsql_connetction.session.query(EquipmentBrand).filter(
                and_(
                    EquipmentBrand.id == id if id else True,
                    EquipmentBrand.equipment_type_id == equipment_type_id if equipment_type_id else True,
                    EquipmentBrand.title.ilike(f'%{title}%') if title else True,
                    (deleted or EquipmentBrand.deleted.is_(False)) if deleted!=None else True
                )
            ).order_by(EquipmentBrand.title)
        else:
            equipment_brand = self.pgsql_connetction.session.query(EquipmentBrand).order_by(EquipmentBrand.title)

        self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = equipment_brand.count()
        result['count'] = count

        max_page = count // 50 if count % 50 > 0 else count // 50 - 1

        if page > max_page and max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []

        for row in equipment_brand[50 * page: 50 * (page + 1)]:
            data.append({
                'id': row.id,
                'title': row.title,
                'icon': row.icon,
                'url': row.url,
                'branches': row.branches,
                'deleted': row.deleted
            })
                # 'equipment_subtype': [{
                #     'id': subtype.id,
                #     'title': subtype.title,
                #     'icon': subtype.icon,
                #     'url': subtype.url,
                #     'branches': subtype.branches,
                #     'deleted': subtype.deleted,
                #     'equipment_model': [{
                #         'id': model.id,
                #         'title': model.title,
                #         'icon': model.icon,
                #         'url': model.url,
                #         'branches': model.branches,
                #         'deleted': model.deleted,
                #         } for model in subtype.equipment_model] if subtype.equipment_model else []
                #     } for subtype in row.equipment_subtype] if row.equipment_subtype else []


        result['data'] = data
        result['page'] = page
        return result

    def edit_equipment_brand(self, id, title=None, icon=None, url=None, branches=None, deleted=None, equipment_type_id=None):

        self.pgsql_connetction.session.query(EquipmentBrand).filter_by(id=id).update({
            'title': title if title else EquipmentBrand.title,
            'icon': icon if icon else EquipmentBrand.icon,
            'url': url if url else EquipmentBrand.url,
            'branches': branches if branches else EquipmentBrand.branches,
            'deleted': deleted if deleted != None else EquipmentBrand.deleted,
            'equipment_type_id': equipment_type_id if equipment_type_id else EquipmentBrand.equipment_type_id,
        })
        self.pgsql_connetction.session.commit()
        return self.get_equipment_brand()

    def del_equipment_brand(self, id):

        equipment_brand = self.pgsql_connetction.session.query(EquipmentBrand).get(id)
        if equipment_brand:
            self.pgsql_connetction.session.delete(equipment_brand)
            self.pgsql_connetction.session.commit()
            return self.get_equipment_brand()

# Таблица МОДИФИКАЦИЙ ИЗДЕЛИЙ ==================================================================================

    def add_equipment_subtype(self, title,  icon, url, branches, deleted,equipment_brand_id):

        equipment_subtype = EquipmentSubtype(
            title=title,
            icon=icon,
            url=url,
            branches=branches,
            deleted=deleted,
            equipment_brand_id=equipment_brand_id
        )
        self.pgsql_connetction.session.add(equipment_subtype)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(equipment_subtype)
        # return self.get_equipment_subtype()
        return equipment_subtype.id

    def get_equipment_subtype(self, id=None, title=None, equipment_brand_id=None, deleted=None, page=0):

        if any([id, title, equipment_brand_id, deleted!=None]):
            equipment_subtype = self.pgsql_connetction.session.query(EquipmentSubtype).filter(
                and_(
                    EquipmentSubtype.id == id if id else True,
                    EquipmentSubtype.equipment_brand_id == equipment_brand_id if equipment_brand_id else True,
                    EquipmentSubtype.title.ilike(f'%{title}%') if title else True,
                    (deleted or EquipmentSubtype.deleted.is_(False)) if deleted != None else True
                )
            ).order_by(EquipmentSubtype.title)
        else:
            equipment_subtype = self.pgsql_connetction.session.query(EquipmentSubtype).order_by(EquipmentSubtype.title)

        self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = equipment_subtype.count()
        result['count'] = count

        max_page = count // 50 if count % 50 > 0 else count // 50 - 1

        if page > max_page and max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []
        for row in equipment_subtype[50 * page: 50 * (page + 1)]:
            data.append({
                'id': row.id,
                'title': row.title,
                'icon': row.icon,
                'url': row.url,
                'branches': row.branches,
                'deleted': row.deleted
            })
                # 'equipment_model': [{
                #         'id': model.id,
                #         'title': model.title,
                #         'icon': model.icon,
                #         'url': model.url,
                #         'branches': row.branches,
                #         'deleted': row.deleted
                #     } for model in row.equipment_model] if row.equipment_model else []


        result['data'] = data
        result['page'] = page
        return result

    def edit_equipment_subtype(self, id, title=None, icon=None, url=None, branches=None, deleted=None, equipment_brand_id=None):

        self.pgsql_connetction.session.query(EquipmentSubtype).filter_by(id=id).update({
            'title': title if title else EquipmentSubtype.title,
            'icon': icon if icon else EquipmentSubtype.icon,
            'url': url if url else EquipmentSubtype.url,
            'branches': branches if branches else EquipmentSubtype.branches,
            'deleted': deleted if deleted != None else EquipmentSubtype.deleted,
            'equipment_brand_id': equipment_brand_id if equipment_brand_id else EquipmentSubtype.equipment_brand_id,
        })
        self.pgsql_connetction.session.commit()
        return self.get_equipment_subtype()

    def del_equipment_subtype(self, id):

        equipment_subtype = self.pgsql_connetction.session.query(EquipmentSubtype).get(id)
        if equipment_subtype:
            self.pgsql_connetction.session.delete(equipment_subtype)
            self.pgsql_connetction.session.commit()
            return self.get_equipment_subtype()

# Таблица МОДИФИКАЦИЙ ИЗДЕЛИЙ ==================================================================================

    def add_equipment_model(self, title,  icon, url, branches, deleted, equipment_subtype_id):

        equipment_model = EquipmentModel(
            title=title,
            icon=icon,
            url=url,
            branches=branches,
            deleted=deleted,
            equipment_subtype_id=equipment_subtype_id
        )
        self.pgsql_connetction.session.add(equipment_model)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(equipment_model)
        return equipment_model.id

    def get_equipment_model(self, id=None, title=None, equipment_subtype_id=None, deleted=None, page=0):

        if any([id, title, equipment_subtype_id, deleted!=None]):
            equipment_model = self.pgsql_connetction.session.query(EquipmentModel).filter(
                and_(
                    EquipmentModel.id == id if id else True,
                    EquipmentModel.equipment_subtype_id == equipment_subtype_id if equipment_subtype_id else True,
                    EquipmentModel.title.ilike(f'%{title}%') if title else True,
                    (deleted or EquipmentModel.deleted.is_(False)) if deleted != None else True
                )
            ).order_by(EquipmentModel.title)
        else:
            equipment_model = self.pgsql_connetction.session.query(EquipmentModel).order_by(EquipmentModel.title)

        self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = equipment_model.count()
        result['count'] = count

        max_page = count // 50 if count % 50 > 0 else count // 50 - 1

        if page > max_page and max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []
        for row in equipment_model[50 * page: 50 * (page + 1)]:
            data.append({
                'id': row.id,
                'title': row.title,
                'icon': row.icon,
                'url': row.url,
                'branches': row.branches,
                'deleted': row.deleted
            })

        result['data'] = data
        result['page'] = page
        return result

    def edit_equipment_model(self, id, title=None, icon=None, url=None, branches=None, deleted=None, equipment_subtype_id=None):

        self.pgsql_connetction.session.query(EquipmentModel).filter_by(id=id).update({
            'title': title if title else EquipmentModel.title,
            'icon': icon if icon else EquipmentModel.icon,
            'url': url if url else EquipmentModel.url,
            'branches': branches if branches else EquipmentModel.branches,
            'deleted': deleted if deleted != None else EquipmentModel.deleted,
            'equipment_subtype_id': equipment_subtype_id if equipment_subtype_id else EquipmentModel.equipment_subtype_id,
        })
        self.pgsql_connetction.session.commit()
        return self.get_equipment_model()

    def del_equipment_model(self, id):

        equipment_model = self.pgsql_connetction.session.query(EquipmentModel).get(id)
        if equipment_model:
            self.pgsql_connetction.session.delete(equipment_model)
            self.pgsql_connetction.session.commit()
            return self.get_equipment_model()

# Таблица СТРОК МЕНЮ ===============================================================================

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

    def edit_setting_menu(self, id, title, url, group_name):

        self.pgsql_connetction.session.query(SettingMenu).filter_by(id=id).update({
            'title': title if title else SettingMenu.title,
            'url': url if url else SettingMenu.url,
            'group_name': group_name if group_name else SettingMenu.group_name

        })
        self.pgsql_connetction.session.commit()
        return self.get_setting_menu()

    def del_setting_menuw(self, id):

        setting_menu = self.pgsql_connetction.session.query(SettingMenu).get(id)
        if setting_menu:
            self.pgsql_connetction.session.delete(SettingMenu)
            self.pgsql_connetction.session.commit()
            return self.get_setting_menu()

# Таблица РОЛЕЙ ==================================================================================

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
                  title,
                  earnings_visibility,
                  leads_visibility,
                  orders_visibility,
                  permissions,
                  settable_statuses,
                  visible_statuses,
                  settable_discount_margin):

        self.pgsql_connetction.session.query(Roles).filter_by(id=id).update({
            'title': title if title else Roles.title,
            'earnings_visibility': earnings_visibility if earnings_visibility != None else Roles.earnings_visibility,
            'leads_visibility': leads_visibility if leads_visibility != None else Roles.leads_visibility,
            'orders_visibility': orders_visibility if orders_visibility != None else Roles.orders_visibility,
            'permissions': permissions if permissions else Roles.permissions,
            'settable_statuses': settable_statuses if settable_statuses else Roles.settable_statuses,
            'visible_statuses': visible_statuses if visible_statuses else Roles.visible_statuses,
            'settable_discount_margin': settable_discount_margin if settable_discount_margin else Roles.settable_discount_margin
        })
        self.pgsql_connetction.session.commit()
        return self.get_role()

    def del_roles(self, id):

        roles = self.pgsql_connetction.session.query(Roles).get(id)
        if roles:
            self.pgsql_connetction.session.delete(roles)
            self.pgsql_connetction.session.commit()
            return self.get_role()

# Таблица ОСНОВНАЯ ИНФОРМАЦИЯ О КОМПАНИИ ==================================================================

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
                            logo):

        self.pgsql_connetction.session.query(GenerallyInfo).filter_by(id=id).update({
            'name': name if name else GenerallyInfo.name,
            'address': address if address else GenerallyInfo.address,
            'email': email if email != None else GenerallyInfo.email,

            'ogrn': ogrn if ogrn else GenerallyInfo.ogrn,
            'inn': inn if inn else GenerallyInfo.inn,
            'kpp': kpp if kpp else GenerallyInfo.kpp,
            'juridical_address': juridical_address if juridical_address else GenerallyInfo.juridical_address,
            'director': director if director else GenerallyInfo.director,
            'bank_name': bank_name if bank_name else GenerallyInfo.bank_name,
            'settlement_account': settlement_account if settlement_account else GenerallyInfo.settlement_account,
            'corr_account': corr_account if corr_account else GenerallyInfo.corr_account,
            'bic': bic if bic else GenerallyInfo.bic,

            'description': description if description else GenerallyInfo.description,
            'phone': phone if phone else GenerallyInfo.phone,
            'logo': logo if logo else GenerallyInfo.logo,
        })
        self.pgsql_connetction.session.commit()
        return self.get_generally_info()

    def del_generally_info(self, id):

        generally_info = self.pgsql_connetction.session.query(GenerallyInfo).get(id)
        if generally_info:
            self.pgsql_connetction.session.delete(generally_info)
            self.pgsql_connetction.session.commit()
            return self.get_generally_info()

# Таблица СЧЕТЧИКОВ ==================================================================================

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

    def edit_counts(self, id, prefix, count, description):

        self.pgsql_connetction.session.query(Counts).filter_by(id=id).update({
            'prefix': prefix if prefix else Counts.prefix,
            'count': count if count else Counts.count,
            'description': description if description else Counts.description
        })
        self.pgsql_connetction.session.commit()
        return self.get_counts()

    def inc_count(self, id):

        counter = self.pgsql_connetction.session.query(Counts).filter_by(id=id).first().count
        self.pgsql_connetction.session.query(Counts).filter_by(id=id).update({
            'count': counter + 1
        })

        self.pgsql_connetction.session.commit()
        return self.get_counts()

    def del_counts(self, id):

        counts = self.pgsql_connetction.session.query(Counts).get(id)
        if counts:
            self.pgsql_connetction.session.delete(counts)
            self.pgsql_connetction.session.commit()
            return self.get_counts()


# Таблица СЛОВАРЬ НЕИСПРАВНОСТЕЙ =========================================================================

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

    def edit_malfunction(self, id, title, count):

        self.pgsql_connetction.session.query(DictMalfunction).filter_by(id=id).update({
            'title': title if title else DictMalfunction.title,
            'count': count if count else DictMalfunction.count
        })
        self.pgsql_connetction.session.commit()
        return self.get_malfunction()

    def del_malfunction(self, id):

        malfunction = self.pgsql_connetction.session.query(DictMalfunction).get(id)
        if malfunction:
            self.pgsql_connetction.session.delete(malfunction)
            self.pgsql_connetction.session.commit()
            return self.get_malfunction()

# Таблица СЛОВАРЬ КОМПЛЕКТАЦИЙ =========================================================================

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

    def edit_packagelist(self, id, title, count):

        self.pgsql_connetction.session.query(DictPackagelist).filter_by(id=id).update({
            'title': title if title else DictPackagelist.title,
            'count': count if count else DictPackagelist.count
        })
        self.pgsql_connetction.session.commit()
        return self.get_packagelist()

    def del_packagelist(self, id):

        packagelist = self.pgsql_connetction.session.query(DictPackagelist).get(id)
        if packagelist:
            self.pgsql_connetction.session.delete(packagelist)
            self.pgsql_connetction.session.commit()
            return self.get_packagelist()

# Таблица КАССЫ =================================================================================

    def add_cashbox(self, title, balance, type, isGlobal, isVirtual, deleted,
                    permissions, employees, branch_id):

        cashbox = Cashboxs(
            title=title,
            balance=balance,
            type=type,
            isGlobal=isGlobal,
            isVirtual=isVirtual,
            deleted=deleted,
            permissions=permissions,
            employees=employees,
            branch_id=branch_id
        )
        self.pgsql_connetction.session.add(cashbox)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(cashbox)
        return cashbox.id

    def get_cashbox_balance(self, cashbox_id):

        sum_col = self.pgsql_connetction.session.query(func.sum(Payments.income + Payments.outcome))\
            .filter(Payments.cashbox_id == cashbox_id)\
            .filter(Payments.deleted != True).scalar()
        # self.pgsql_connetction.session.commit()
        # self.get_payments()
        # self.pgsql_connetction.session.expunge_all()
        return sum_col

    def get_cashbox(self, id=None, title=None, isGlobal=None, isVirtual=None, deleted=None, branch_id=None):

        if any([id, title, isGlobal!=None, isVirtual!=None, deleted != None, branch_id!=None ]):
            cashbox = self.pgsql_connetction.session.query(Cashboxs).filter(
                and_(
                    Cashboxs.id == id if id else True,
                    Cashboxs.title.like(f'%{title}%') if title else True,
                    Cashboxs.isGlobal == isGlobal if isGlobal != None else True,
                    Cashboxs.isVirtual == isVirtual if isVirtual != None else True,
                    Cashboxs.deleted == deleted if deleted != None else True,
                    Cashboxs.branch_id == branch_id if branch_id else True
                )
            ).order_by(Cashboxs.id)
        else:
            cashbox = self.pgsql_connetction.session.query(Cashboxs).order_by(Cashboxs.id)

        # self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = cashbox.count()
        result['count'] = count

        data = []
        for row in cashbox:
            balance = self.pgsql_connetction.session.query(func.sum(Payments.income + Payments.outcome))\
            .filter(Payments.cashbox_id == row.id)\
            .filter(Payments.deleted != True).scalar()
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

        result['data'] = data
        return result

    def edit_cashbox(self, id, title, balance, type, isGlobal, isVirtual, deleted, permissions, employees, branch_id):

        self.pgsql_connetction.session.query(Cashboxs).filter_by(id=id).update({
            'title': title if title else Cashboxs.title,
            'balance': balance if balance else Cashboxs.balance,
            'type': type if type else Cashboxs.type,
            'isGlobal': isGlobal if isGlobal != None else Cashboxs.isGlobal,
            'isVirtual': isVirtual if isVirtual != None else Cashboxs.isVirtual,
            'deleted': deleted if deleted != None else Cashboxs.deleted,
            'permissions': permissions if permissions else Cashboxs.permissions,
            'employees': employees if employees else Cashboxs.employees,
            'branch_id': branch_id if branch_id else Cashboxs.branch_id,
        })
        self.pgsql_connetction.session.commit()
        return self.get_cashbox()

    def del_cashbox(self, id):

        cashbox = self.pgsql_connetction.session.query(Cashboxs).get(id)
        if cashbox:
            self.pgsql_connetction.session.delete(cashbox)
            self.pgsql_connetction.session.commit()
            return self.get_cashbox()

# Таблица ТРАНЗАКЦИЙ =================================================================================

    def add_payments(self,
                     cashflow_category,
                     description,
                     deposit,
                     income,
                     outcome,
                     direction,
                     can_print_fiscal,
                     deleted,
                     is_fiscal,
                     created_at,
                     custom_created_at,
                     tags,
                     relation_id,
                     cashbox_id,
                     client_id,
                     employee_id,
                     order_id
                     ):

        payments = Payments(
            cashflow_category=cashflow_category,
            description=description,
            deposit=deposit,
            income=income,
            outcome=outcome,
            direction=direction,
            can_print_fiscal=can_print_fiscal,
            deleted=deleted,
            is_fiscal=is_fiscal,
            created_at=created_at,
            custom_created_at=custom_created_at,
            tags=tags,
            relation_id=relation_id,
            cashbox_id=cashbox_id,
            client_id=client_id,
            employee_id=employee_id,
            order_id=order_id
        )
        self.pgsql_connetction.session.add(payments)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(payments)
        return payments.id

    def get_payments(self,
                     id=None,
                     cashflow_category=None,
                     direction=None,
                     deleted=None,
                     custom_created_at=None,
                     tags=None,
                     cashbox_id=None,
                     client_id=None,
                     employee_id=None,
                     order_id=None,
                     relation_id=None
                     ):

        if any([id, cashflow_category, direction, deleted != None, custom_created_at, tags, cashbox_id,
                client_id, employee_id, order_id]):
            payments = self.pgsql_connetction.session.query(Payments).filter(
                and_(
                    Payments.id == id if id else True,
                    Payments.cashflow_category.like(f'%{cashflow_category}%') if cashflow_category else True,
                    Payments.direction == direction if direction else True,
                    Payments.deleted == deleted if deleted != None else True,
                    (Payments.custom_created_at >= custom_created_at[0] if custom_created_at[0] else True) if custom_created_at else True,
                    (Payments.custom_created_at <= custom_created_at[1] if custom_created_at[1] else True) if custom_created_at else True,
                    tags._in(Payments.tags) if tags else True,
                    Payments.relation_id == relation_id if relation_id else True,
                    Payments.cashbox_id == cashbox_id if cashbox_id else True,
                    Payments.client_id == client_id if client_id else True,
                    Payments.employee_id == employee_id if employee_id else True,
                    Payments.order_id == order_id if order_id else True
                )
            ).order_by(desc(Payments.custom_created_at))
        else:
            payments = self.pgsql_connetction.session.query(Payments).order_by(desc(Payments.custom_created_at))

        result = {'success': True}
        count = payments.count()
        result['count'] = count

        data = []
        for row in payments:

            deposit = self.pgsql_connetction.session.query(func.sum(Payments.income + Payments.outcome))\
            .filter(Payments.cashbox_id == row.cashbox.id)\
            .filter(Payments.deleted != True) \
            .filter(Payments.custom_created_at <= row.custom_created_at)\
            .scalar()


            data.append({
                'id': row.id,
                'cashflow_category': row.cashflow_category,
                'description': row.description,
                'deposit': deposit,
                'income': row.income,
                'outcome': row.outcome,
                'direction': row.direction,
                'can_print_fiscal': row.can_print_fiscal,
                'deleted': row.deleted,
                'is_fiscal': row.is_fiscal,
                'created_at': row.created_at,
                'updated_at': row.updated_at,
                'custom_created_at': row.custom_created_at,
                'tags': row.tags,
                'relation_id': row.relation_id,
                'cashbox': {
                    'id': row.cashbox.id,
                    'title': row.cashbox.title,
                    'type': row.cashbox.type
                } if row.cashbox else {},
                'client': {
                    'id': row.client.id,
                    'name': row.client.name,
                    'phone': [ph.number for ph in row.client.phone] if row.client.phone else []
                } if row.client else {},
                'employee': {
                    'id': row.employee.id,
                    'name': f'{row.employee.last_name} {row.employee.first_name}'
                } if row.employee else {},
                'order': {
                    'id': row.order.id,
                    'id_label': row.order.id_label
                } if row.order else {}
            })

        result['data'] = data
        # self.pgsql_connetction.session.commit()
        return result

    # def change_payment_deposit(self, start_date, cashbox_id):
    #     if print_logs:
    #         start_time=time.time()
    #         print('Начало оновления баланса платежей')
    #     payments = self.pgsql_connetction.session.query(Payments).filter(
    #         and_(
    #             Payments.deleted == False,
    #             Payments.custom_created_at >= start_date,
    #             Payments.cashbox_id == cashbox_id
    #         )
    #     ).order_by(Payments.custom_created_at)
    #     if print_logs:
    #         print(f'Список платежей определен: {time.time() - start_time} сек.')
    #
    #     payments2 = self.pgsql_connetction.session.query(Payments).filter(
    #         and_(
    #             Payments.deleted == False,
    #             Payments.custom_created_at < start_date,
    #             Payments.cashbox_id == cashbox_id
    #         )
    #     ).order_by(Payments.custom_created_at)
    #     if print_logs:
    #         print(f'Список оставшихся платежей определен: {time.time() - start_time} сек.')
    #
    #     if payments.count():
    #         deposit = payments2[-1].deposit if payments2.count() else 0
    #         if print_logs:
    #             print(f'Стартовый баланс определен: {time.time() - start_time} сек.')
    #
    #         for row in tqdm(payments, desc=f'Обнавление платежей {cashbox_id}', position=0, total=payments.count()):
    #             deposit = deposit + row.income + row.outcome
    #             self.pgsql_connetction.session.query(Payments).filter_by(id=row.id).update({'deposit': deposit})
    #             self.pgsql_connetction.session.commit()
    #         if print_logs:
    #             print(f'Балансы платежей изменены: {time.time() - start_time} сек.')
    #         payments = self.pgsql_connetction.session.query(Payments).filter(
    #             and_(
    #                 Payments.deleted == False,
    #                 Payments.custom_created_at >= start_date,
    #                 Payments.cashbox_id == cashbox_id
    #             )
    #         ).order_by(Payments.custom_created_at)
    #         if print_logs:
    #             print(f'Запрошены измененные платежи: {time.time() - start_time} сек.')
    #         self.edit_cashbox(id=cashbox_id,
    #                           balance=payments[-1].deposit,
    #                           title=None,
    #                           type=None,
    #                           isGlobal=None,
    #                           isVirtual=None,
    #                           deleted=None,
    #                           permissions=None,
    #                           employees=None,
    #                           branch_id=None
    #                           )
    #         if print_logs:
    #             print(f'Баланс кассы изменет: {time.time() - start_time} сек.')
    #     else:
    #         print('Платежи не найдены')
    #         self.edit_cashbox(id=cashbox_id,
    #                           balance=payments2[-1].deposit,
    #                           title=None,
    #                           type=None,
    #                           isGlobal=None,
    #                           isVirtual=None,
    #                           deleted=None,
    #                           permissions=None,
    #                           employees=None,
    #                           branch_id=None
    #                           )
    #         if print_logs:
    #             print(f'Баланс кассы изменет: {time.time() - start_time} сек.')
    #
    #     if print_logs:
    #         print(f'Конец изменения баланса платежей: {time.time() - start_time} сек.')
    #     return {'success': True}


    def edit_payments(self,
                      id,
                      cashflow_category,
                      description,
                      deposit,
                      income,
                      outcome,
                      direction,
                      can_print_fiscal,
                      deleted,
                      is_fiscal,
                      created_at,
                      custom_created_at,
                      tags,
                      relation_id,
                      cashbox_id,
                      client_id,
                      employee_id,
                      order_id):

        self.pgsql_connetction.session.query(Payments).filter_by(id=id).update({
            'cashflow_category': cashflow_category if cashflow_category else Payments.cashflow_category,
            'description': description if description else Payments.description,
            'deposit': deposit if deposit else Payments.deposit,
            'income': income if income else Payments.income,
            'outcome': outcome if outcome else Payments.outcome,
            'direction': direction if direction else Payments.direction,
            'can_print_fiscal': can_print_fiscal if can_print_fiscal != None else Payments.can_print_fiscal,
            'deleted': deleted if deleted != None else Payments.deleted,
            'is_fiscal': is_fiscal if is_fiscal != None else Payments.is_fiscal,
            'created_at': created_at if created_at else Payments.created_at,
            'custom_created_at': custom_created_at if custom_created_at else Payments.custom_created_at,
            'tags': tags if tags else Payments.tags,
            'relation_id': relation_id if relation_id else Payments.relation_id,
            'cashbox_id': cashbox_id if cashbox_id else Payments.cashbox_id,
            'client_id': client_id if client_id else Payments.client_id,
            'employee_id': employee_id if employee_id else Payments.employee_id,
            'order_id': order_id if order_id else Payments.order_id
        })
        self.pgsql_connetction.session.commit()
        return id

    def del_payments(self, id):

        payments = self.pgsql_connetction.session.query(Payments).get(id)
        if payments:
            self.pgsql_connetction.session.delete(payments)
            self.pgsql_connetction.session.commit()
            return self.get_payments()


# Таблица СЛОВАРЬ КОМПЛЕКТАЦИЙ =========================================================================

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

    def edit_item_payments(self, id, title, direction):

        self.pgsql_connetction.session.query(ItemPayments).filter_by(id=id).update({
            'title': title if title else ItemPayments.title,
            'direction': direction if direction else ItemPayments.direction
        })
        self.pgsql_connetction.session.commit()
        return self.get_item_payments()

    def del_item_payments(self, id):

        item_payments = self.pgsql_connetction.session.query(ItemPayments).get(id)
        if item_payments:
            self.pgsql_connetction.session.delete(item_payments)
            self.pgsql_connetction.session.commit()
            return self.get_item_payments()

# Таблица НАЧИСЛЕНИЙ ЗАРАБОТНОЙ ПЛАТЫ ===============================================================

    def add_payroll(self,
                    relation_type,
                    relation_id,
                    employee_id,
                    order_id,
                    direction,
                    description='',
                    income=0,
                    outcome=0,
                    deleted=False,
                    reimburse=False,
                    created_at=None,
                    custom_created_at=None,
                    ):

        payroll = Payrolls(
            description=description,
            income=income,
            outcome=outcome,
            direction=direction,
            deleted=deleted,
            reimburse=reimburse,
            created_at=created_at,
            custom_created_at=custom_created_at,
            relation_type=relation_type,
            relation_id=relation_id,
            employee_id=employee_id,
            order_id=order_id
        )
        self.pgsql_connetction.session.add(payroll)
        self.pgsql_connetction.session.commit()
        self.pgsql_connetction.session.refresh(payroll)
        return payroll.id

    def get_payrolls(self,
                     id=None,
                     direction=None,
                     deleted=None,
                     reimburse=None,
                     custom_created_at=None,
                     relation_type=None,
                     relation_id=None,
                     employee_id=None,
                     order_id=None
                     ):

        if any([id, direction, deleted != None, reimburse != None, custom_created_at, relation_type,
                employee_id, order_id]):
            payroll = self.pgsql_connetction.session.query(Payrolls).filter(
                and_(
                    Payrolls.id == id if id else True,
                    Payrolls.direction == direction if direction else True,
                    Payrolls.deleted == deleted if deleted != None else True,
                    Payrolls.reimburse == reimburse if reimburse != None else True,
                    (Payrolls.custom_created_at >= custom_created_at[0] if custom_created_at[0] else True) if custom_created_at else True,
                    (Payrolls.custom_created_at <= custom_created_at[1] if custom_created_at[1] else True) if custom_created_at else True,
                    Payrolls.relation_type == relation_type if relation_type else True,
                    Payrolls.relation_id == relation_id if relation_id else True,
                    Payrolls.employee_id == employee_id if employee_id else True,
                    Payrolls.order_id == order_id if order_id else True
                )
            ).order_by(desc(Payrolls.custom_created_at))
        else:
            payroll = self.pgsql_connetction.session.query(Payrolls).order_by(desc(Payrolls.custom_created_at))

        result = {'success': True}
        count = payroll.count()
        result['count'] = count

        data = []
        for row in payroll:

            deposit = self.pgsql_connetction.session.query(func.sum(Payrolls.income + Payrolls.outcome))\
            .filter(Payrolls.employee_id == row.employee_id)\
            .filter(Payrolls.deleted != True) \
            .filter(Payrolls.custom_created_at <= row.custom_created_at)\
            .scalar()

            data.append({
                'id': row.id,
                'description': row.description,
                'deposit': deposit,
                'income': row.income,
                'outcome': row.outcome,
                'direction': row.direction,
                'deleted': row.deleted,
                'reimburse': row.reimburse,
                'created_at': row.created_at,
                'updated_at': row.updated_at,
                'custom_created_at': row.custom_created_at,
                'relation_type': row.relation_type,
                'relation_id': row.relation_id,
                'employee_id': row.employee_id,
                'order_id': row.order_id,
                'order': {
                    'id': row.order.id,
                    'id_label': row.order.id_label,
                } if row.order else {}
            })

        result['data'] = data
        # self.pgsql_connetction.session.commit()
        return result

    def get_payroll_sum(self, custom_created_at, employee_id):
        sum = self.pgsql_connetction.session.query(func.sum(Payrolls.income + Payrolls.outcome)) \
            .filter(Payrolls.employee_id == employee_id) \
            .filter(Payrolls.deleted != True) \
            .filter(Payrolls.custom_created_at >= custom_created_at[0]) \
            .filter(Payrolls.custom_created_at <= custom_created_at[1]) \
            .scalar()

        return sum

    def edit_payroll(self,
                      id,
                      description=None,
                      income=None,
                      outcome=None,
                      direction=None,
                      deleted=None,
                      reimburse=None,
                      custom_created_at=None,
                      relation_type=None,
                      relation_id=None,
                      employee_id=None,
                      order_id=None):

        self.pgsql_connetction.session.query(Payrolls).filter_by(id=id).update({
            'description': description if description else Payrolls.description,
            'income': income if income else Payrolls.income,
            'outcome': outcome if outcome else Payrolls.outcome,
            'direction': direction if direction else Payrolls.direction,
            'deleted': deleted if deleted != None else Payrolls.deleted,
            'reimburse': reimburse if reimburse != None else Payrolls.reimburse,
            'custom_created_at': custom_created_at if custom_created_at else Payrolls.custom_created_at,
            'relation_type': relation_type if relation_type else Payrolls.relation_type,
            'relation_id': relation_id if relation_id else Payrolls.relation_id,
            'employee_id': employee_id if employee_id else Payrolls.employee_id,
            'order_id': order_id if order_id else Payrolls.order_id
        })
        self.pgsql_connetction.session.commit()
        return id

    def del_payroll(self, id):

        payroll = self.pgsql_connetction.session.query(Payrolls).get(id)
        if payroll:
            self.pgsql_connetction.session.delete(payroll)
            self.pgsql_connetction.session.commit()
            return id

# Таблица ПРАВИЛ НАЧИСЛЕНИЙ ЗАРАБОТНОЙ ПЛАТЫ ===============================================================

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
                    Payrules.deleted == deleted if deleted != None else True,
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
                     title,
                     type_rule,
                     order_type,
                     method,
                     coefficient,
                     count_coeff,
                     fix_salary,
                     deleted,
                     employee_id,
                     check_status):

        self.pgsql_connetction.session.query(Payrules).filter_by(id=id).update({
            'title': title if title else Payrules.title,
            'type_rule': type_rule if type_rule else Payrules.type_rule,
            'order_type': order_type if order_type else Payrules.order_type,
            'method': method if method != None else Payrules.method,
            'coefficient': coefficient if coefficient else Payrules.coefficient,
            'count_coeff': count_coeff if count_coeff else Payrules.count_coeff,
            'fix_salary': fix_salary if fix_salary else Payrules.fix_salary,
            'deleted': deleted if deleted != None else Payrules.deleted,
            'employee_id': employee_id if employee_id else Payrules.employee_id,
            'check_status': check_status if check_status else Payrules.check_status
        })
        self.pgsql_connetction.session.commit()
        return id

    def del_payrule(self, id):

        payrule = self.pgsql_connetction.session.query(Payrules).get(id)
        if payrule:
            self.pgsql_connetction.session.delete(payrule)
            self.pgsql_connetction.session.commit()
            return id

# Таблица КАТЕГОРИЙ ПРАЙСА УСЛГ ===============================================================

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
                    GroupDictService.deleted == deleted if deleted != None else True
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

    def edit_group_dict_service(self, id, title, icon, deleted):

        self.pgsql_connetction.session.query(GroupDictService).filter_by(id=id).update({
            'title': title if title else GroupDictService.title,
            'icon': icon if icon else GroupDictService.icon,
            'deleted': deleted if deleted != None else GroupDictService.deleted
        })
        self.pgsql_connetction.session.commit()
        return id

    def del_group_dict_service(self, id):

        group_dict_service = self.pgsql_connetction.session.query(GroupDictService).get(id)
        if group_dict_service:
            self.pgsql_connetction.session.delete(group_dict_service)
            self.pgsql_connetction.session.commit()
            return id

# Таблица ПРАВИЛ НАЧИСЛЕНИЙ ЗАРАБОТНОЙ ПЛАТЫ ===============================================================

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

            if any([id, title, warranty, code, deleted != None,  category_id]):
                dict_service = self.pgsql_connetction.session.query(DictService).filter(
                    and_(
                        DictService.id == id if id else True,
                        DictService.title.like(f'%{title}%') if title else True,
                        DictService.warranty == warranty if warranty else True,
                        DictService.code == code if code else True,
                        DictService.deleted == deleted if deleted != None else True,
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
                          title,
                          price,
                          cost,
                          warranty,
                          code,
                          earnings_percent,
                          earnings_summ,
                          deleted,
                          category_id):

            self.pgsql_connetction.session.query(DictService).filter_by(id=id).update({
                'title': title if title else DictService.title,
                'price': price if price else DictService.price,
                'cost': cost if cost else DictService.cost,
                'warranty': warranty if warranty else DictService.warranty,
                'code': code if code else DictService.code,
                'earnings_percent': earnings_percent if earnings_percent else DictService.earnings_percent,
                'earnings_summ': earnings_summ if earnings_summ else DictService.earnings_summ,
                'deleted': deleted if deleted != None else DictService.deleted,
                'category_id': category_id if category_id else DictService.category_id
            })
            self.pgsql_connetction.session.commit()
            return id

    def del_dict_service(self, id):

        dict_service = self.pgsql_connetction.session.query(DictService).get(id)
        if dict_service:
            self.pgsql_connetction.session.delete(dict_service)
            self.pgsql_connetction.session.commit()
            return id

# Таблица ЦЕН УСЛГ ===============================================================

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
                    ServicePrices.deleted == deleted if deleted != None else True
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

    def edit_service_prices(self, id, cost, discount_margin_id, service_id, deleted):

        self.pgsql_connetction.session.query(ServicePrices).filter_by(id=id).update({
            'cost': cost if cost else ServicePrices.cost,
            'discount_margin_id': discount_margin_id if discount_margin_id else ServicePrices.discount_margin_id,
            'service_id': service_id if service_id else ServicePrices.service_id,
            'deleted': deleted if deleted != None else ServicePrices.deleted
        })
        self.pgsql_connetction.session.commit()
        return id

    def del_service_prices(self, id):

        service_prices = self.pgsql_connetction.session.query(ServicePrices).get(id)
        if service_prices:
            self.pgsql_connetction.session.delete(service_prices)
            self.pgsql_connetction.session.commit()
            return id

# Таблица ТОВАРОВ/ЗАПЧАСТЕЙ ===============================================================

    def add_parts(self, title, description, marking, article, barcode, code, image_url, doc_url, specifications, deleted):

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
            deleted=deleted
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
                  deleted=None):

        if any([id, title, marking, article, barcode, code, deleted != None]):
            parts = self.pgsql_connetction.session.query(Parts).filter(
                and_(
                    Parts.id == id if id else True,
                    Parts.title.ilike(f'%{title}%') if title else True,
                    Parts.marking.ilike(f'%{marking}%') if marking else True,
                    Parts.article == article if article else True,
                    Parts.barcode == barcode if barcode else True,
                    Parts.code == code if code else True,
                    Parts.deleted == deleted if deleted != None else True
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
                'deleted': row.deleted
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
                   deleted=None):

        self.pgsql_connetction.session.query(Parts).filter_by(id=id).update({
            'title': title if title else Parts.title,
            'description': description if description else Parts.description,
            'marking': marking if marking else Parts.marking,
            'article': article if article else Parts.article,
            'barcode': barcode if barcode else Parts.barcode,
            'code': code if code else Parts.code,
            'image_url': image_url if image_url else Parts.image_url,
            'doc_url': doc_url if doc_url else Parts.doc_url,
            'specifications': specifications if specifications else Parts.specifications,
            'deleted': deleted if deleted != None else Parts.deleted
        })
        self.pgsql_connetction.session.commit()
        return id

    def del_parts(self, id):

        parts = self.pgsql_connetction.session.query(Parts).get(id)
        if parts:
            self.pgsql_connetction.session.delete(parts)
            self.pgsql_connetction.session.commit()
            return id

# Таблица СКЛАДОВ ===============================================================

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
                    Warehouse.deleted == deleted if deleted != None else True
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
            'title': title if title else Warehouse.title,
            'description': description if description else Warehouse.description,
            'branch_id': branch_id if branch_id else Warehouse.branch_id,
            'permissions': permissions if permissions else Warehouse.permissions,
            'employees': employees if employees else Warehouse.employees,
            'isGlobal': isGlobal if isGlobal != None else Warehouse.isGlobal,
            'deleted': deleted if deleted != None else Warehouse.deleted
        })
        self.pgsql_connetction.session.commit()
        return id

    def del_warehouse(self, id):

        warehouse = self.pgsql_connetction.session.query(Warehouse).get(id)
        if warehouse:
            self.pgsql_connetction.session.delete(warehouse)
            self.pgsql_connetction.session.commit()
            return id

# Таблица КАТЕГОРИЙ СКЛАДОВ ===============================================================

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
                    # WarehouseCategory.deleted == deleted if deleted != None else True
                )
            ).order_by(WarehouseCategory.title)
        else:
            warehouse_category = self.pgsql_connetction.session.query(WarehouseCategory).order_by(WarehouseCategory.title)

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
            'title': title if title else WarehouseCategory.title,
            'parent_category_id': parent_category_id if parent_category_id else WarehouseCategory.parent_category_id,
            'warehouse_id': warehouse_id if warehouse_id else WarehouseCategory.warehouse_id,
            'deleted': deleted if deleted != None else WarehouseCategory.deleted
        })
        self.pgsql_connetction.session.commit()
        return id

    def del_warehouse_category(self, id):

        warehouse_category = self.pgsql_connetction.session.query(WarehouseCategory).get(id)
        if warehouse_category:
            self.pgsql_connetction.session.delete(warehouse_category)
            self.pgsql_connetction.session.commit()
            return id

# Таблица ЗАПЧАСТЕЙ НА СКЛАДЕ ===============================================================

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
                    WarehouseParts.deleted == deleted if deleted != None else True
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
            'where_to_buy': where_to_buy if where_to_buy else WarehouseParts.where_to_buy,
            'cell': cell if cell else WarehouseParts.cell,
            'count': count if count else WarehouseParts.count,
            'min_residue': min_residue if min_residue else WarehouseParts.min_residue,
            'warranty_period': warranty_period if warranty_period else WarehouseParts.warranty_period,
            'necessary_amount': necessary_amount if necessary_amount else WarehouseParts.necessary_amount,
            'part_id': part_id if part_id else WarehouseParts.part_id,
            'category_id': category_id if category_id else WarehouseParts.category_id,
            'warehouse_id': warehouse_id if warehouse_id else WarehouseParts.warehouse_id,
            'deleted': deleted if deleted != None else WarehouseParts.deleted
        })
        self.pgsql_connetction.session.commit()
        return id

    def del_warehouse_parts(self, id):

        warehouse_parts = self.pgsql_connetction.session.query(WarehouseParts).get(id)
        if warehouse_parts:
            self.pgsql_connetction.session.delete(warehouse_parts)
            self.pgsql_connetction.session.commit()
            return id









if __name__ == '__main__':
    start_time = time.time()
    db = DbInteraction(
        host='5.53.124.252',
        port='5432',
        user='postgres',
        password='225567',
        db_name='one_two',
        rebuild_db=False
    )

    # Создание новых таблиц
    # db.create_tables([Parts.__table__, Warehouse.__table__, WarehouseCategory.__table__, WarehouseParts.__table__])

    # Добавление столбца
    column = Column('employees', JSON)
    db.add_column(Warehouse.__table__, column)

    # db.create_all_tables()
    # db.initial_data()
    # db.update_date_from_remonline()
    # db.reset_dict()
    #
    # dtime = time.time() - start_time
    # hours = int(dtime // 3600)
    # minutes = int((dtime % 3600) // 60)
    # seconds = int((dtime % 3600) % 60)
    # print(f'Обновление завершено за {hours}:{minutes:02}:{seconds:02}')


    # pages = db.get_orders()['count']/50
    # types = []
    # for page in tqdm(range(int(pages)+1), desc='Обработка...', position=0):
    #     orders = db.get_orders(page=page)['data']
    #     for order in orders:
    #         types.append(order.get('kindof_good').strip().lower())
    # types = set(types)
    # print('count:', len(types))
    # pprint(types)










