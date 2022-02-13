from datetime import datetime

from sqlalchemy import Column, Integer, ForeignKey, VARCHAR, UniqueConstraint, SMALLINT, DateTime, JSON
from sqlalchemy import ARRAY, TEXT, BOOLEAN, INTEGER, TIMESTAMP, FLOAT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
# from flask_jwt_extended import create_access_token

Base = declarative_base()

def time_now():
    return datetime.now().timestamp()

# таблица рекламных компаний
class AdCampaign(Base):

    __tablename__ = 'ad_campaign'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)  # ID рекламной компании
    name = Column(VARCHAR(50))                                   # Имя рекламной компании

# Таблица ролей
class Roles(Base):

    __tablename__ = 'roles'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)  # ID роли
    title = Column(TEXT)                                                        # Значение роли
    earnings_visibility = Column(BOOLEAN)                                       # Видит только свою ЗП
    leads_visibility = Column(BOOLEAN)                                          # Видит только свои заказы
    orders_visibility = Column(BOOLEAN)                                         # Видит только свои обращения
    permissions = Column(ARRAY(TEXT))                                           # Разрешения
    settable_statuses = Column(ARRAY(INTEGER))                                  # Может устанавливать статус
    visible_statuses = Column(ARRAY(INTEGER))                                   # Может видеть статус
    settable_discount_margin = Column(ARRAY(INTEGER))                           # Может использовать цены


# Таблица сотрудников
class Employees(Base):

    __tablename__ = 'employees'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)  # ID Сотрудника
    first_name = Column(TEXT)                                                   # Имя
    last_name = Column(TEXT)                                                    # Фамилия
    email = Column(TEXT, unique=True, nullable=False)                           # Электронная почта
    phone = Column(TEXT)                                                        # Телефон
    notes = Column(TEXT)                                                        # Заметки
    deleted = Column(BOOLEAN)                                                   # Сотрудник удален
    inn = Column(TEXT)
    doc_name = Column(TEXT)
    post = Column(TEXT)
    permissions = Column(ARRAY(TEXT))
    id_ref = f'{Roles.__tablename__}.{Roles.id.name}'
    role_id = Column(INTEGER, ForeignKey(id_ref), nullable=False)               # Роль
    login = Column(TEXT, unique=True)                                           # Логин
    password = Column(TEXT, nullable=False)                                     # Пароль

    role = relationship('Roles', foreign_keys=[role_id])
    table_headers = relationship('TableHeaders', backref='table_headers', passive_deletes=True)
    payrules = relationship('Payrules', backref='payrules', passive_deletes=True, cascade="all, delete, delete-orphan")

# Таблица полей таблицы заказо
class TableHeaders(Base):
    __tablename__ = 'table_headers'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)  # id поля
    title = Column(TEXT)                                                        # Текст поля
    field = Column(TEXT)                                                        # Имя поля
    width = Column(INTEGER)                                                     # Ширина поля
    visible = Column(BOOLEAN)                                                   # Статус отображения
    id_ref = f'{Employees.__tablename__}.{Employees.id.name}'
    employee_id = Column(INTEGER, ForeignKey(id_ref), nullable=False)           # id сотрудника



    # def get_token(self, expier_time=12):
    #     expire_delta = datetime(expier_time)
    #     token = create_access_token(identity=self.id, expires_delta=expire_delta)
    #     return token


# Таблица филиалов
class Branch(Base):

    __tablename__ = 'branch'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)  # ID Филиала
    name = Column(TEXT)                                                         # Имя филиала
    address = Column(TEXT)
    phone = Column(TEXT)
    color = Column(TEXT)
    icon = Column(TEXT)
    orders_type_id = Column(INTEGER)
    orders_type_strategy = Column(TEXT)
    orders_prefix = Column(TEXT)
    documents_prefix = Column(TEXT)
    employees = Column(ARRAY(INTEGER))
    deleted = Column(BOOLEAN)

    schedule = relationship('Schedule', backref='schedule', passive_deletes=True)

# Таблица филиалов

class Schedule(Base):
    __tablename__ = 'schedule'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)  # ID записи
    start_time = Column(TEXT)
    end_time = Column(TEXT)
    work_day = Column(BOOLEAN)
    week_day = Column(INTEGER)
    id_branch_ref = f'{Branch.__tablename__}.{Branch.id.name}'
    branch_id = Column(INTEGER, ForeignKey(id_branch_ref, ondelete='CASCADE'))                      # Филиал (id)



# Таблица наценок
class DiscountMargin(Base):

    __tablename__ = 'discount_margin'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)     # ID Филиала
    margin = Column(FLOAT)                                                         # Значение наценки
    title = Column(TEXT)                                                           # Имя наценки
    margin_type = Column(INTEGER)                                                  # Тип наценки (1 - работа, 2 - материал)
    deleted = Column(BOOLEAN)

# Таблица типов заказов
class OrderType(Base):

    __tablename__ = 'order_type'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)  # ID типа
    name = Column(TEXT)                                                         # Имя типа

# Таблица группы статусов
class StatusGroup(Base):

    __tablename__ = 'status_group'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)  # ID типа
    name = Column(TEXT)                                                         # Имя типа
    type_group = Column(INTEGER, unique=True)                                   # Номер группы
    color = Column(TEXT)                                                        # Цвет группы
    status = relationship('Status', backref='status', passive_deletes=True)


# Таблица статусов
class Status(Base):

    __tablename__ = 'status'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)  # ID статуса
    name = Column(TEXT)                                                         # Имя статуса
    color = Column(TEXT)                                                        # Цвет статуса
    id_ref = f'{StatusGroup.__tablename__}.{StatusGroup.type_group.name}'
    group = Column(INTEGER, ForeignKey(id_ref))                                 # Группа статуса
    deadline = Column(INTEGER)                                                  # Дедлайн статуса
    comment_required = Column(BOOLEAN)                                          # Необходим коментарий
    payment_required = Column(BOOLEAN)                                          # Необходим платеж
    available_to = Column(ARRAY(INTEGER))                                       # Список доступных статусов для перехода

# Таблица клиентов
class Clients(Base):

    __tablename__ = 'clients'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)      # ID Клиента

    juridical = Column(BOOLEAN)                                                     # Юридическое лицо
    supplier = Column(BOOLEAN)                                                      # Поставщик
    conflicted = Column(BOOLEAN)                                                    # Конфликтный
    should_send_email = Column(BOOLEAN)
    discount_good_type = Column(BOOLEAN)
    discount_materials_type = Column(BOOLEAN)
    discount_service_type = Column(BOOLEAN)
    deleted = Column(BOOLEAN)

    name = Column(TEXT)                                                             # Имя
    name_doc = Column(TEXT)                                                         # Имя в документах (обращение)
    email = Column(TEXT)                                                            # Электронная почта
    address = Column(TEXT)                                                          # Адрес
    discount_code = Column(TEXT)                                                    # Скидочная карта
    notes = Column(TEXT)                                                            # Примечание
    ogrn = Column(TEXT)
    inn = Column(TEXT)
    kpp = Column(TEXT)
    juridical_address = Column(TEXT)
    director = Column(TEXT)
    bank_name = Column(TEXT)
    settlement_account = Column(TEXT)
    corr_account = Column(TEXT)
    bic = Column(TEXT)

    discount_goods = Column(FLOAT)                                                  # Скидка на товары
    discount_materials = Column(FLOAT)                                              # Скидка для продаж
    discount_services = Column(FLOAT)                                               # Скидка на работы

    id_сompany_ref = f'{AdCampaign.__tablename__}.{AdCampaign.id.name}'
    ad_campaign_id = Column(INTEGER, ForeignKey(id_сompany_ref), nullable=False)    # Данные о рекламной компании
    id_margin_ref = f'{DiscountMargin.__tablename__}.{DiscountMargin.id.name}'
    discount_goods_margin_id = Column(INTEGER, ForeignKey(id_сompany_ref))          # Тип цены для продаж (id)
    discount_materials_margin_id = Column(INTEGER, ForeignKey(id_сompany_ref))      # Тип цены для мареиалов (id)
    discount_service_margin_id = Column(INTEGER, ForeignKey(id_сompany_ref))        # Тип цены для мареиалов (id)

    tags = Column(ARRAY(TEXT))

    created_at = Column(INTEGER, default=time_now)                                  # Дата создания
    updated_at = Column(INTEGER, default=time_now, onupdate=time_now)               # Дата обновления

    ad_campaign = relationship('AdCampaign', foreign_keys=[ad_campaign_id])
    phone = relationship('Phones', backref='phones', passive_deletes=True,  cascade="all, delete, delete-orphan")

# Таблица телефонов
class Phones(Base):

    __tablename__ = 'phones'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)  # ID телефона
    number = Column(TEXT)                                                       # Номер телефона
    title = Column(TEXT)                                                        # Тип номера
    id_ref = f'{Clients.__tablename__}.{Clients.id.name}'
    client_id = Column(INTEGER, ForeignKey(id_ref, ondelete='CASCADE'), nullable=False)             # Клиент


# Таблица типов изделий
class EquipmentType(Base):
    __tablename__ = 'equipment_type'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)  # ID поля
    title = Column(TEXT)                                                        # Значение поля
    icon = Column(TEXT)                                                         # иконка поля
    url = Column(TEXT)                                                          # ссылка на изображение
    branches = Column(ARRAY(INTEGER))
    deleted = Column(BOOLEAN)
    equipment_brand = relationship(
        'EquipmentBrand',
        backref='equipment_brand',
        passive_deletes=True,
        cascade="all, delete"
    )

# Таблица брендов изделий
class EquipmentBrand(Base):
    __tablename__ = 'equipment_brand'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)  # ID поля
    title = Column(TEXT)                                                        # Значение поля
    icon = Column(TEXT)                                                         # иконка поля
    url = Column(TEXT)                                                          # ссылка на изображение
    branches = Column(ARRAY(INTEGER))
    deleted = Column(BOOLEAN)
    id_ref = f'{EquipmentType.__tablename__}.{EquipmentType.id.name}'
    equipment_type_id = Column(INTEGER, ForeignKey(id_ref), nullable=True)     # id типа изделия
    equipment_subtype = relationship(
        'EquipmentSubtype',
        backref='equipment_subtype',
        passive_deletes=True,
        cascade="all, delete"
    )

# Таблица модификаций (модулей) изделий
class EquipmentSubtype(Base):
    __tablename__ = 'equipment_subtype'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)  # ID поля
    title = Column(TEXT)                                                        # Значение поля
    icon = Column(TEXT)                                                         # иконка поля
    url = Column(TEXT)                                                          # ссылка на изображение
    branches = Column(ARRAY(INTEGER))
    deleted = Column(BOOLEAN)
    id_ref = f'{EquipmentBrand.__tablename__}.{EquipmentBrand.id.name}'
    equipment_brand_id = Column(INTEGER, ForeignKey(id_ref), nullable=False)    # id бренда изделия
    equipment_model = relationship(
        'EquipmentModel',
        backref='equipment_model',
        passive_deletes=True,
        cascade="all, delete"
    )

# Таблица моделей изделий
class EquipmentModel(Base):
    __tablename__ = 'equipment_model'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)  # ID поля
    title = Column(TEXT)                                                        # Значение поля
    icon = Column(TEXT)                                                         # иконка поля
    url = Column(TEXT)                                                          # ссылка на изображение
    branches = Column(ARRAY(INTEGER))
    deleted = Column(BOOLEAN)
    id_ref = f'{EquipmentSubtype.__tablename__}.{EquipmentSubtype.id.name}'
    equipment_subtype_id = Column(INTEGER, ForeignKey(id_ref), nullable=False)  # id модификации изделия



# Таблица заказов
class Orders(Base):
    __tablename__ = 'orders'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)      # ID Заказа
    created_at = Column(INTEGER, default=time_now)                                  # Заказ создан (timestamp)
    updated_at = Column(INTEGER, default=time_now, onupdate=time_now)               # Заказ изменен (timestamp)
    done_at = Column(INTEGER)                                                       # Заказ готов (timestamp)
    closed_at = Column(INTEGER)                                                     # Заказ закрыт (timestamp)
    assigned_at = Column(INTEGER)                                                   # Назначен на время (timestamp)
    duration = Column(INTEGER)                                                      # Продолжительность  (timestamp)
    estimated_done_at = Column(INTEGER)                                             # Плановая дата готовности (timestamp)
    scheduled_for = Column(INTEGER)                                                 # Запланирован на
    warranty_date = Column(INTEGER)                                                 # Гарантия до
    status_deadline = Column(INTEGER)                                               # Срок статуса

    id_сompany_ref = f'{AdCampaign.__tablename__}.{AdCampaign.id.name}'
    ad_campaign_id = Column(INTEGER, ForeignKey(id_сompany_ref), nullable=True)     # Данные о рекламной компании
    id_branch_ref = f'{Branch.__tablename__}.{Branch.id.name}'
    branch_id = Column(INTEGER, ForeignKey(id_branch_ref))                          # Филиал (id)
    id_status_ref = f'{Status.__tablename__}.{Status.id.name}'
    status_id = Column(INTEGER, ForeignKey(id_status_ref))                          # Статус заказа (id)
    id_customers_ref = f'{Clients.__tablename__}.{Clients.id.name}'
    client_id = Column(INTEGER, ForeignKey(id_customers_ref), nullable=True)        # Клиент (id)
    id_type_ref = f'{OrderType.__tablename__}.{OrderType.id.name}'
    order_type_id = Column(INTEGER, ForeignKey(id_type_ref))                        # Тип заказа (id)
    id_emplooy_ref = f'{Employees.__tablename__}.{Employees.id.name}'
    closed_by_id = Column(INTEGER, ForeignKey(id_emplooy_ref), nullable=True)       # Закрыт сотрудником (id)
    created_by_id = Column(INTEGER, ForeignKey(id_emplooy_ref))                     # Создан сотрудником (id)
    engineer_id = Column(INTEGER, ForeignKey(id_emplooy_ref), nullable=True)        # Инженер (id)
    manager_id = Column(INTEGER, ForeignKey(id_emplooy_ref), nullable=True)         # Менеджнр (id)
    id_kindof_good_ref = f'{EquipmentType.__tablename__}.{EquipmentType.id.name}'
    kindof_good_id = Column(INTEGER, ForeignKey(id_kindof_good_ref), nullable=True)
    id_brand_ref = f'{EquipmentBrand.__tablename__}.{EquipmentBrand.id.name}'
    brand_id = Column(INTEGER, ForeignKey(id_brand_ref), nullable=True)
    id_subtype_ref = f'{EquipmentSubtype.__tablename__}.{EquipmentSubtype.id.name}'
    subtype_id = Column(INTEGER, ForeignKey(id_subtype_ref), nullable=True)
    id_model_ref = f'{EquipmentModel.__tablename__}.{EquipmentModel.id.name}'
    model_id = Column(INTEGER, ForeignKey(id_model_ref), nullable=True)

    id_label = Column(TEXT)                                                         # Номер заказа
    prefix = Column(TEXT)                                                           # Префикс
    serial = Column(TEXT)                                                           # Серийный номер
    malfunction = Column(TEXT)                                                      # Тип устройства
    packagelist = Column(TEXT)                                                      # Комплектация
    appearance = Column(TEXT)                                                       # Внешний вид устройства
    engineer_notes = Column(TEXT)                                                   # Заметки инженера
    manager_notes = Column(TEXT)                                                    # Заметки менеджера
    resume = Column(TEXT)                                                           # Пояснение
    cell = Column(TEXT)                                                             # Ячейка

    estimated_cost = Column(FLOAT)                                                  # Ориентировочная стоимость
    missed_payments = Column(FLOAT)                                                 # Пропущеный платеж (Возможно нужно убрать)
    discount_sum = Column(FLOAT)                                                    # Сумма скидки (Возможно нужно убрать)
    payed = Column(FLOAT)                                                           # Оплачено (Возможно нужно убрать)
    price = Column(FLOAT)                                                           # Стоимость (Возможно нужно убрать)

    urgent = Column(BOOLEAN)                                                        # Срочный заказ

    ad_campaign = relationship('AdCampaign', foreign_keys=[ad_campaign_id])
    branch = relationship('Branch', foreign_keys=[branch_id])
    client = relationship('Clients', foreign_keys=[client_id])
    engineer = relationship('Employees', foreign_keys=[engineer_id])
    manager = relationship('Employees', foreign_keys=[manager_id])
    status = relationship('Status', foreign_keys=[status_id])
    order_type = relationship('OrderType', foreign_keys=[order_type_id])
    kindof_good = relationship('EquipmentType', foreign_keys=[kindof_good_id])          # Тип техники
    brand = relationship('EquipmentBrand', foreign_keys=[brand_id])
    subtype = relationship('EquipmentSubtype', foreign_keys=[subtype_id])
    model = relationship('EquipmentModel', foreign_keys=[model_id])

    operations = relationship('Operations', backref='operations', passive_deletes=True)
    parts = relationship('OderParts', backref='oder_parts', passive_deletes=True)
    attachments = relationship('Attachments', backref='attachments', passive_deletes=True)
    payments = relationship('Payments', backref='payments', passive_deletes=True)

class GroupDictService(Base):
    __tablename__ = 'group_dict_service'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)  # ID строчки
    title = Column(TEXT)
    icon = Column(TEXT)
    deleted = Column(BOOLEAN)

    dict_service = relationship('DictService', backref='dict_service', passive_deletes=True)

class DictService(Base):
    __tablename__ = 'dict_service'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)  # ID строчки
    title = Column(TEXT)
    price = Column(FLOAT)
    cost = Column(FLOAT)                    # Себестоимость
    warranty = Column(INTEGER)
    code = Column(TEXT)                     # Код
    earnings_percent = Column(FLOAT)
    earnings_summ = Column(FLOAT)
    deleted = Column(BOOLEAN)
    category_id_ref = f'{GroupDictService.__tablename__}.{GroupDictService.id.name}'
    category_id = Column(INTEGER, ForeignKey(category_id_ref), nullable=False)  # Сотрудник

class ServicePrices(Base):
    __tablename__ = 'service_prices'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)  # ID строчки
    cost = Column(FLOAT)
    deleted = Column(BOOLEAN)
    id_discount_margin_ref = f'{DiscountMargin.__tablename__}.{DiscountMargin.id.name}'
    discount_margin_id = Column(INTEGER, ForeignKey(id_discount_margin_ref), nullable=False)
    category_id_ref = f'{DictService.__tablename__}.{DictService.id.name}'
    service_id = Column(INTEGER, ForeignKey(category_id_ref), nullable=False)

# Таблица операций
class Operations(Base):

    __tablename__ = 'operations'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)  # ID операции
    amount = Column(INTEGER)                                                    # Количество
    cost = Column(FLOAT)                                                        # Себестоимость
    discount_value = Column(FLOAT)                                              # Сумма скидки
    id_ref = f'{Employees.__tablename__}.{Employees.id.name}'
    engineer_id = Column(INTEGER, ForeignKey(id_ref), nullable=False)           # Инженер
    price = Column(FLOAT)                                                       # Цена услуги
    total = Column(FLOAT)
    title = Column(TEXT)                                                        # Наименование услуги
    comment = Column(TEXT)
    deleted = Column(BOOLEAN)
    warranty_period = Column(INTEGER)                                           # Период гарантии
    created_at = Column(INTEGER, default=time_now)                              # Дата создания
    updated_at = Column(INTEGER, default=time_now, onupdate=time_now)           # Дата обновления
    id_order_ref = f'{Orders.__tablename__}.{Orders.id.name}'
    order_id = Column(INTEGER, ForeignKey(id_order_ref, ondelete='CASCADE'))    # id заказа
    id_dict_ref = f'{DictService.__tablename__}.{DictService.id.name}'
    dict_id = Column(INTEGER, ForeignKey(id_dict_ref, ondelete='CASCADE'), nullable=True)     # id заказа

    dict_service = relationship('DictService', foreign_keys=[dict_id])

# Таблица запчастей и материалов заказа
class OderParts(Base):

    __tablename__ = 'oder_parts'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)  # ID Запчасти
    amount = Column(INTEGER)                                                    # Количество
    cost = Column(FLOAT)                                                        # Себестоимость
    discount_value = Column(FLOAT)                                              # Сумма скидки
    id_ref = f'{Employees.__tablename__}.{Employees.id.name}'
    engineer_id = Column(INTEGER, ForeignKey(id_ref), nullable=False)           # Инженер
    price = Column(FLOAT)                                                       # Цена запчасти
    total = Column(FLOAT)
    title = Column(TEXT)                                                        # Наименование запачасти
    comment = Column(TEXT)
    deleted = Column(BOOLEAN)
    warranty_period = Column(INTEGER)                                           # Период гарантии
    created_at = Column(INTEGER, default=time_now)                              # Дата создания
    updated_at = Column(INTEGER, default=time_now, onupdate=time_now)           # Дата обновления
    id_order_ref = f'{Orders.__tablename__}.{Orders.id.name}'
    order_id = Column(INTEGER, ForeignKey(id_order_ref, ondelete='CASCADE'))    # id заказа


# Таблица вложений
class Attachments(Base):

    __tablename__ = 'attachments'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)          # ID вложения
    id_ref = f'{Employees.__tablename__}.{Employees.id.name}'
    created_by_id = Column(INTEGER, ForeignKey(id_ref),  nullable=False)                # ID сотрудника, который создал
    created_at = Column(INTEGER, default=time_now)                                      # Дата создания
    updated_at = Column(INTEGER, default=time_now, onupdate=time_now)                   # Дата обновления
    filename = Column(TEXT)                                                             # Имя файла
    url = Column(TEXT)
    id_order_ref = f'{Orders.__tablename__}.{Orders.id.name}'
    order_id = Column(INTEGER, ForeignKey(id_order_ref, ondelete='CASCADE'))            # id заказа


# Таблица строк главного меню
class MenuRows(Base):

    __tablename__ = 'menu_rows'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)   # ID строчки
    title = Column(TEXT)                                                         # Значение строчки
    img = Column(TEXT)                                                           # Картинка PNG
    url = Column(TEXT)                                                           # Ссылка
    group_name = Column(TEXT)                                                    # Имя группы

# Табилци главных фильтров
class Badges(Base):

    __tablename__ = 'badges'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)   # ID беджа
    title = Column(TEXT)                                                         # Значение беджа
    img = Column(TEXT)                                                           # Картинка PNG
    color = Column(TEXT)                                                         # Цвет

# Табилци главных фильтров
class CustomFilters(Base):

    __tablename__ = 'custom_filters'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)   # ID фильтра
    title = Column(TEXT)                                                         # Значение беджа
    filters = Column(JSON)                                                       # Значение фильтра
    id_ref = f'{Employees.__tablename__}.{Employees.id.name}'
    employee_id = Column(INTEGER, ForeignKey(id_ref), nullable=False)            # id сотрудника
    general = Column(BOOLEAN)                                                    # Общий


# Таблица строк меню настроек
class SettingMenu(Base):

    __tablename__ = 'setting_menu'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)   # ID строчки
    title = Column(TEXT)                                                         # Значение строчки
    url = Column(TEXT)                                                           # Ссылка
    group_name = Column(TEXT)                                                    # Имя группы

class GenerallyInfo(Base):

    __tablename__ = 'generally_info'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)   # ID строчки
    name = Column(TEXT)                                                          # Название компании
    address = Column(TEXT)                                                       # Адрес
    email = Column(TEXT)                                                         # Электронный адрес

    ogrn = Column(TEXT)
    inn = Column(TEXT)
    kpp = Column(TEXT)
    juridical_address = Column(TEXT)
    director = Column(TEXT)
    bank_name = Column(TEXT)
    settlement_account = Column(TEXT)
    corr_account = Column(TEXT)
    bic = Column(TEXT)

    description = Column(TEXT)
    phone = Column(TEXT)
    logo = Column(TEXT)

class Counts(Base):

    __tablename__ = 'counts'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)   # ID строчки
    prefix = Column(TEXT)
    count = Column(INTEGER)
    description = Column(TEXT)


class DictMalfunction(Base):

    __tablename__ = 'malfunction'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)   # ID строчки
    title = Column(TEXT)
    count = Column(INTEGER)

class DictPackagelist(Base):

    __tablename__ = 'packagelist'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)   # ID строчки
    title = Column(TEXT)
    count = Column(INTEGER)

class ItemPayments(Base):

    __tablename__ = 'item_payments'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)   # ID строчки
    title = Column(TEXT)
    direction = Column(INTEGER)


class Cashboxs(Base):
    __tablename__ = 'cashboxs'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)   # ID строчки
    title = Column(TEXT)
    balance = Column(FLOAT)
    # position = Column(INTEGER)
    type = Column(INTEGER)
    isGlobal = Column(BOOLEAN)
    isVirtual = Column(BOOLEAN)
    deleted = Column(BOOLEAN)
    permissions = Column(ARRAY(TEXT))
    employees = Column(JSON)
    id_branch_ref = f'{Branch.__tablename__}.{Branch.id.name}'
    branch_id = Column(INTEGER, ForeignKey(id_branch_ref, ondelete='CASCADE'))


class Payments(Base):
    __tablename__ = 'payments'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)      # ID строчки

    cashflow_category = Column(TEXT)                                                # Категория расходов
    description = Column(TEXT)                                                      # Описание

    deposit = Column(FLOAT)                                                         # Баланс
    income = Column(FLOAT)                                                          # Входящяя сумма
    outcome = Column(FLOAT)                                                         # Иcходящая сумму
    direction = Column(INTEGER)                                                     # Направление платежа

    can_print_fiscal = Column(BOOLEAN)                                              # Возможно печатать чек
    deleted = Column(BOOLEAN)                                                       # Платеж удален
    is_fiscal = Column(BOOLEAN)                                                     # Чек напечатан

    created_at = Column(INTEGER, default=time_now)                                  # Дата создания
    updated_at = Column(INTEGER, default=time_now, onupdate=time_now)               # Дата обновления
    custom_created_at = Column(INTEGER)                                             # Дата установленая пользователем

    tags = Column(ARRAY(TEXT))                                                      # Теги

    relation_id = Column(INTEGER)                                                   # id связанного платежа (для перемещения)
    id_cashbox_ref = f'{Cashboxs.__tablename__}.{Cashboxs.id.name}'
    cashbox_id = Column(INTEGER, ForeignKey(id_cashbox_ref), nullable=True)         # Касса
    id_client_ref = f'{Clients.__tablename__}.{Clients.id.name}'
    client_id = Column(INTEGER, ForeignKey(id_client_ref), nullable=True)           # Клиент
    id_employee_ref = f'{Employees.__tablename__}.{Employees.id.name}'
    employee_id = Column(INTEGER, ForeignKey(id_employee_ref), nullable=False)      # Сотрудник
    id_order_ref = f'{Orders.__tablename__}.{Orders.id.name}'
    order_id = Column(INTEGER, ForeignKey(id_order_ref), nullable=True)             # Заказа

    client = relationship('Clients', foreign_keys=[client_id])
    employee = relationship('Employees', foreign_keys=[employee_id])
    order = relationship('Orders', foreign_keys=[order_id])
    cashbox = relationship('Cashboxs', foreign_keys=[cashbox_id])

class Payrolls(Base):
    __tablename__ = 'payrolls'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)  # ID строчки

    description = Column(TEXT)  # Описание

    income = Column(FLOAT)  # Входящяя сумма
    outcome = Column(FLOAT)  # Иcходящая сумму
    direction = Column(INTEGER)  # Направление платежа

    deleted = Column(BOOLEAN)  # Платеж удален
    reimburse = Column(BOOLEAN) # Совершен возврат

    created_at = Column(INTEGER, default=time_now)  # Дата создания
    updated_at = Column(INTEGER, default=time_now, onupdate=time_now)  # Дата обновления
    custom_created_at = Column(INTEGER, default=time_now)  # Дата установленая пользователем

    relation_type = Column(INTEGER) # Тип начисления
    relation_id = Column(INTEGER)  # id связанного события


    id_employee_ref = f'{Employees.__tablename__}.{Employees.id.name}'
    employee_id = Column(INTEGER, ForeignKey(id_employee_ref), nullable=False)  # Сотрудник
    id_order_ref = f'{Orders.__tablename__}.{Orders.id.name}'
    order_id = Column(INTEGER, ForeignKey(id_order_ref), nullable=True)

    order = relationship('Orders', foreign_keys=[order_id])

# relation_type
# 1 Создание заказа
# 2 Закрытие заказа
# 3 Ведение заказа
# 4 Работа - по статусу закрыт
# 5 Работа - по статусу готов
# 6 Продажа
# 7 Оклад
# 9 Премия
# 10 Взыскания
# 11 Возврат заказа

class Payrules(Base):
    __tablename__ = 'payrules'

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False)  # ID строчки
    title = Column(TEXT)
    type_rule = Column(INTEGER)             # Тип начачисления
    order_type = Column(INTEGER)            # Тип заказа
    method = Column(INTEGER)                # Начисления (0 - проценты, 1 - руб)
    coefficient = Column(FLOAT)           # Коэффициет при начаслении за работы или запчасти
    count_coeff = Column(ARRAY(JSON))              # Условия начисления
    fix_salary =Column(INTEGER)             # Оклад
    deleted = Column(BOOLEAN)
    created_at = Column(INTEGER, default=time_now)  # Дата создания
    updated_at = Column(INTEGER, default=time_now, onupdate=time_now)  # Дата обновления
    check_status = Column(INTEGER)          # 4 По статусу готов, 6 по статусу закрыт

    id_employee_ref = f'{Employees.__tablename__}.{Employees.id.name}'
    employee_id = Column(INTEGER, ForeignKey(id_employee_ref), nullable=False)  # Сотрудник


# Типы начачисления
# 1 - За создания заказа
# 2 - За закрытие заказа
# 3 - Менеджеру за обработку заказа
# 4 - Исполнителю за работы/услуги
# 5 - Исполнителю за материалы
# 6 - За продажи
# 7 - За рабочие часы
# 8 - За рабочие дни

