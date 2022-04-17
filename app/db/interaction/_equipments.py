import inspect
import os
import traceback
from urllib.request import urlopen

from sqlalchemy import and_
from app.db.models.models import EquipmentType, EquipmentBrand, EquipmentSubtype, EquipmentModel
from utils import error550


# Таблица ТИПОВ ИЗДЕЛИЙ ==================================================================================


def add_equipment_type(self, title, icon, url, branches, deleted, r_filter):
    try:
        equipment_type = EquipmentType(
            title=title,
            icon=icon,
            url=url,
            branches=branches,
            deleted=deleted
        )
        self.pgsql_connetction.session.add(equipment_type)
        self.pgsql_connetction.session.flush()

        result = {'success': True}
        if r_filter:
            query = self.pgsql_connetction.session.query(EquipmentType)
            if r_filter.get('title') is not None:
                query = query.filter(EquipmentType.title.ilike(f"%{r_filter['title']}%"))
            if r_filter.get('deleted') is not None:
                query = query.filter(r_filter['deleted'] or EquipmentType.deleted.is_(False))

            query = query.order_by(EquipmentType.title)

            result['count'] = query.count()

            query = query.limit(50)
            if r_filter.get('page', 0): query = query.offset(r_filter['page'] * 50)

            equipment_types = query.all()

            data = []
            for row in equipment_types:
                data.append({
                    'id': row.id,
                    'title': row.title,
                    'icon': row.icon,
                    'url': row.url,
                    'branches': row.branches,
                    'deleted': row.deleted
                })

            result['data'] = data
            result['page'] = r_filter.get('page', 0)
        else:
            data = {
                'id': equipment_type.id,
                'title': equipment_type.title,
                'icon': equipment_type.icon,
                'url': equipment_type.url,
                'branches': equipment_type.branches,
                'deleted': equipment_type.deleted,
            }
            result['message'] = f'{equipment_type.id} added'
            result['data'] = data

        self.pgsql_connetction.session.commit()
        return result, 201
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def get_equipment_type(self, id=None, title=None, deleted=None, page=0):
    try:
        query = self.pgsql_connetction.session.query(EquipmentType)

        if id is not None: query = query.filter(EquipmentType.id == id)
        if title is not None: query = query.filter(EquipmentType.title.ilike(f'%{title}%'))
        if deleted is not None: query = query.filter(deleted or EquipmentType.deleted.is_(False))

        query = query.order_by(EquipmentType.title)

        result = {'success': True}

        result['count'] = query.count()

        query = query.limit(50)
        if page: query = query.offset(page * 50)

        equipment_type = query.all()

        data = []
        for row in equipment_type:
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
        return result, 200
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def edit_equipment_type(
        self,
        id,
        title=None,
        icon=None,
        url=None,
        branches=None,
        deleted=None,
        list_for_join=None,
        r_filter=None
    ):
    try:
        equipment_type = self.pgsql_connetction.session.query(EquipmentType).get(id)
        fields = inspect.getfullargspec(edit_equipment_type).args[:-2]  # список имен всех аргументов текущей фнкции
        for field in fields:
            war = locals()[field]   # Находим переменную от имени и присваеваем war
            if war is not None:
                setattr(equipment_type, field, war)

        list_update = [equipment_type]

        # Если запрос содержит список для объединения
        if list_for_join is not None:

            # Пройдем циклом по вему списку
            for equipment_type in list_for_join:

                # Отметим запись как удаленную
                etype = self.pgsql_connetction.session.query(EquipmentType).get(equipment_type)
                etype.deleted = True
                list_update.append(etype)

                # Получим список дочерних брендов
                list_brands = self.pgsql_connetction.session.query(EquipmentBrand)\
                    .filter_by(equipment_type_id=equipment_type)

                # Пройдем циклом по списку дочерних брендов
                for equipment_brand in list_brands:

                    # Заменим родительский элемент
                    brand = self.pgsql_connetction.session.query(EquipmentBrand).get(equipment_brand.id)
                    brand.equipment_type_id = id
                    list_update.append(brand)

        self.pgsql_connetction.session.add_all(list_update)
        self.pgsql_connetction.session.flush()

        result = {'success': True}

        if r_filter:
            query = self.pgsql_connetction.session.query(EquipmentType)
            if r_filter.get('title') is not None:
                query = query.filter(EquipmentType.title.ilike(f"%{r_filter['title']}%"))
            if r_filter.get('deleted') is not None:
                query = query.filter(r_filter['deleted'] or EquipmentType.deleted.is_(False))

            query = query.order_by(EquipmentType.title)

            result['count'] = query.count()

            query = query.limit(50)
            if r_filter.get('page', 0): query = query.offset(r_filter['page'] * 50)

            equipment_types = query.all()

            data = []
            for row in equipment_types:
                data.append({
                    'id': row.id,
                    'title': row.title,
                    'icon': row.icon,
                    'url': row.url,
                    'branches': row.branches,
                    'deleted': row.deleted
                })

            result['data'] = data
            result['page'] = r_filter.get('page', 0)
        else:
            result = {'success': True, 'message': f'{id} changed'}

        self.pgsql_connetction.session.commit()
        return result, 202
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def del_equipment_type(self, id):
    try:
        equipment_type = self.pgsql_connetction.session.query(EquipmentType).get(id)
        if equipment_type:
            self.pgsql_connetction.session.delete(equipment_type)
            self.pgsql_connetction.session.commit()
            return {'success': True, 'message': f'{id} deleted'}, 202
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


# Таблица БРЕНДОВ ИЗДЕЛИЙ ==================================================================================

def add_equipment_brand(self, title, icon, url, branches, deleted, equipment_type_id, r_filter):
    try:
        equipment_brand = EquipmentBrand(
            title=title,
            icon=icon,
            url=url,
            branches=branches,
            deleted=deleted,
            equipment_type_id=equipment_type_id
        )
        self.pgsql_connetction.session.add(equipment_brand)
        self.pgsql_connetction.session.flush()

        result = {'success': True}

        if r_filter:
            query = self.pgsql_connetction.session.query(EquipmentBrand)
            if r_filter.get('equipment_type_id') is not None:
                query = query.filter(EquipmentBrand.equipment_type_id == r_filter['equipment_type_id'])
            if r_filter.get('title') is not None:
                query = query.filter(EquipmentBrand.title.ilike(f"%{r_filter['title']}%"))
            if r_filter.get('deleted') is not None:
                query = query.filter(r_filter['deleted'] or EquipmentBrand.deleted.is_(False))

            query = query.order_by(EquipmentBrand.title)

            result['count'] = query.count()

            query = query.limit(50)
            if r_filter.get('page', 0): query = query.offset(r_filter['page'] * 50)

            equipment_brands = query.all()

            data = []
            for row in equipment_brands:
                data.append({
                    'id': row.id,
                    'title': row.title,
                    'icon': row.icon,
                    'url': row.url,
                    'branches': row.branches,
                    'deleted': row.deleted,
                    'equipment_type_id': row.equipment_type_id
                })

            result['data'] = data
            result['page'] = r_filter.get('page', 0)
        else:
            self.pgsql_connetction.session.refresh(equipment_brand)
            data = {
                'id': equipment_brand.id,
                'title': equipment_brand.title,
                'icon': equipment_brand.icon,
                'url': equipment_brand.url,
                'branches': equipment_brand.branches,
                'deleted': equipment_brand.deleted,
                'equipment_type_id': equipment_brand.equipment_type_id
            }
            result['message'] = f'{equipment_brand.id} added'
            result['data'] = data
        self.pgsql_connetction.session.commit()
        return result, 201
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def get_equipment_brand(self, id=None, title=None, equipment_type_id=None, deleted=None, page=0):
    try:
        query = self.pgsql_connetction.session.query(EquipmentBrand)

        if id is not None: query = query.filter(EquipmentBrand.id == id)
        if equipment_type_id is not None: query = query.filter(EquipmentBrand.equipment_type_id == equipment_type_id)
        if title is not None: query = query.filter(EquipmentBrand.title.ilike(f'%{title}%'))
        if deleted is not None: query = query.filter(deleted or EquipmentBrand.deleted.is_(False))

        query = query.order_by(EquipmentBrand.title)

        result = {'success': True}

        result['count'] = query.count()

        query = query.limit(50)
        if page: query = query.offset(page * 50)

        equipment_brand = query.all()

        data = []
        for row in equipment_brand:
            data.append({
                'id': row.id,
                'title': row.title,
                'icon': row.icon,
                'url': row.url,
                'branches': row.branches,
                'deleted': row.deleted,
                'equipment_type_id': row.equipment_type_id
            })

        result['data'] = data
        result['page'] = page
        return result, 200
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def edit_equipment_brand(
        self,
        id,
        title=None,
        icon=None,
        url=None,
        branches=None,
        deleted=None,
        equipment_type_id=None,
        list_for_join=None,
        r_filter=None
     ):
    try:
        equipment_brand = self.pgsql_connetction.session.query(EquipmentBrand).get(id)
        fields = inspect.getfullargspec(edit_equipment_brand).args[:-2]  # список имен всех аргументов текущей фнкции
        for field in fields:
            war = locals()[field]  # Находим переменную от имени и присваеваем war
            if war is not None:
                setattr(equipment_brand, field, war)

        list_update = [equipment_brand]

        # Если запрос содержит список для объединения
        if list_for_join is not None:

            # Пройдем циклом по вему списку
            for equipment_brand in list_for_join:

                # Отметим запись как удаленную
                brand = self.pgsql_connetction.session.query(EquipmentBrand).get(equipment_brand)
                brand.deleted = True
                list_update.append(brand)

                # Получим список дочерних модулей
                list_subtype = self.pgsql_connetction.session.query(EquipmentSubtype) \
                    .filter_by(equipment_brand_id=equipment_brand)

                # Пройдем циклом по списку дочерних брендов
                for equipment_subtype in list_subtype:

                    # Заменим родительский элемент
                    subtype = self.pgsql_connetction.session.query(EquipmentSubtype).get(equipment_subtype.id)
                    subtype.equipment_brand_id = id
                    list_update.append(subtype)

        self.pgsql_connetction.session.add_all(list_update)
        self.pgsql_connetction.session.flush()

        result = {'success': True}

        if r_filter:
            query = self.pgsql_connetction.session.query(EquipmentBrand)
            if r_filter.get('equipment_type_id') is not None:
                query = query.filter(EquipmentBrand.equipment_type_id == r_filter['equipment_type_id'])
            if r_filter.get('title') is not None:
                query = query.filter(EquipmentBrand.title.ilike(f"%{r_filter['title']}%"))
            if r_filter.get('deleted') is not None:
                query = query.filter(r_filter['deleted'] or EquipmentBrand.deleted.is_(False))

            query = query.order_by(EquipmentBrand.title)

            result['count'] = query.count()

            query = query.limit(50)
            if r_filter.get('page', 0): query = query.offset(r_filter['page'] * 50)

            equipment_brands = query.all()

            data = []
            for row in equipment_brands:
                data.append({
                    'id': row.id,
                    'title': row.title,
                    'icon': row.icon,
                    'url': row.url,
                    'branches': row.branches,
                    'deleted': row.deleted,
                    'equipment_type_id': row.equipment_type_id
                })

            result['data'] = data
            result['page'] = r_filter.get('page', 0)
        else:
            result = {'success': True, 'message': f'{id} changed'}
        self.pgsql_connetction.session.commit()
        return result, 202
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def del_equipment_brand(self, id):
    try:
        equipment_brand = self.pgsql_connetction.session.query(EquipmentBrand).get(id)
        if equipment_brand:
            self.pgsql_connetction.session.delete(equipment_brand)
            self.pgsql_connetction.session.commit()
            return {'success': True, 'message': f'{id} deleted'}, 202
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


# Таблица МОДИФИКАЦИЙ ИЗДЕЛИЙ ==================================================================================

def add_equipment_subtype(self, title, icon, url, branches, deleted, equipment_brand_id, r_filter, img):
    try:
        equipment_subtype = EquipmentSubtype(
            title=title,
            icon=icon,
            url=url,
            branches=branches,
            deleted=deleted,
            equipment_brand_id=equipment_brand_id
        )
        self.pgsql_connetction.session.add(equipment_subtype)
        self.pgsql_connetction.session.flush()

        result = {'success': True}

        # загрузка изображения
        if img:
            # Загрузим данные из URI в переменную
            with urlopen(img) as response:
                data = response.read()
            # Определим путь для сохранения файла
            url_file = f'build/static/data/PCB/subtype{equipment_subtype.id}.jpeg'
            # Запишим файл изображения по данному пути
            with open(url_file, 'wb') as f:
                f.write(data)
            # Определим путь для доступа к этому файлу изображения
            url = f'data/PCB/subtype{equipment_subtype.id}.jpeg'
            # Сохраним этот путь в таблице данных
            self.pgsql_connetction.session.query(EquipmentSubtype)\
                .filter_by(id=equipment_subtype.id)\
                .update({'url': url})

        if r_filter:
            query = self.pgsql_connetction.session.query(EquipmentSubtype)
            if r_filter.get('equipment_brand_id') is not None:
                query = query.filter(EquipmentSubtype.equipment_brand_id == r_filter['equipment_brand_id'])
            if r_filter.get('title') is not None:
                query = query.filter(EquipmentSubtype.title.ilike(f"%{r_filter['title']}%"))
            if r_filter.get('deleted') is not None:
                query = query.filter(r_filter['deleted'] or EquipmentSubtype.deleted.is_(False))

            query = query.order_by(EquipmentSubtype.title)

            result['count'] = query.count()

            query = query.limit(50)
            if r_filter.get('page', 0): query = query.offset(r_filter['page'] * 50)

            equipment_subtypes = query.all()

            data = []

            for row in equipment_subtypes:
                data.append({
                    'id': row.id,
                    'title': row.title,
                    'icon': row.icon,
                    'url': row.url,
                    'branches': row.branches,
                    'deleted': row.deleted,
                    'equipment_brand_id': row.equipment_brand_id
                })

            result['data'] = data
            result['page'] = r_filter.get('page', 0)
        else:

            data = {
                'id': equipment_subtype.id,
                'title': equipment_subtype.title,
                'icon': equipment_subtype.icon,
                'url': equipment_subtype.url,
                'branches': equipment_subtype.branches,
                'deleted': equipment_subtype.deleted,
                'equipment_brand_id': equipment_subtype.equipment_brand_id
            }
            result['message'] = f'{equipment_subtype.id} added'
            result['data'] = data
        self.pgsql_connetction.session.commit()
        return result, 201
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def get_equipment_subtype(self, id=None, title=None, equipment_brand_id=None, deleted=None, page=0):
    try:
        query = self.pgsql_connetction.session.query(EquipmentSubtype)

        if id is not None: query = query.filter(EquipmentSubtype.id == id)
        if equipment_brand_id is not None: query = query.filter(EquipmentSubtype.equipment_brand_id == equipment_brand_id)
        if title is not None: query = query.filter(EquipmentSubtype.title.ilike(f'%{title}%'))
        if deleted is not None: query = query.filter(deleted or EquipmentSubtype.deleted.is_(False))

        query = query.order_by(EquipmentSubtype.title)

        result = {'success': True}

        result['count'] = query.count()

        query = query.limit(50)
        if page: query = query.offset(page * 50)

        equipment_subtype = query.all()

        data = []
        for row in equipment_subtype:
            data.append({
                'id': row.id,
                'title': row.title,
                'icon': row.icon,
                'url': row.url,
                'branches': row.branches,
                'deleted': row.deleted,
                'equipment_brand_id': row.equipment_brand_id
            })

        result['data'] = data
        result['page'] = page
        return result, 200
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def edit_equipment_subtype(
        self,
        id,
        title=None,
        icon=None,
        url=None,
        branches=None,
        deleted=None,
        equipment_brand_id=None,
        list_for_join=None,
        r_filter=None,
        img=None
    ):
    try:
        # Загрузка изображения
        if img:
            # Загрузим данные из URI в переменную
            with urlopen(img) as response:
                data = response.read()

            # Определим путь для сохранения файла
            url = f'build/static/data/PCB/subtype{id}.jpeg'

            # Запишим файл изображения по данному пути
            with open(url, 'wb') as f:
                f.write(data)

            # Определим путь для доступа к этому файлу изображения
            url = f'data/PCB/subtype{id}.jpeg'

        equipment_subtype = self.pgsql_connetction.session.query(EquipmentSubtype).get(id)
        fields = inspect.getfullargspec(edit_equipment_subtype).args[:-2]  # список имен всех аргументов текущей фнкции
        for field in fields:
            war = locals()[field]  # Находим переменную от имени и присваеваем war
            if war is not None:
                setattr(equipment_subtype, field, war)

        list_update = [equipment_subtype]

        # Если запрос содержит список для объединения
        if list_for_join is not None:

            # Пройдем циклом по вему списку
            for equipment_subtype in list_for_join:

                # Отметим запись как удаленную
                subtype = self.pgsql_connetction.session.query(EquipmentSubtype).get(equipment_subtype)
                subtype.deleted = True
                list_update.append(subtype)

                # Получим список дочерних модулей
                list_models = self.pgsql_connetction.session.query(EquipmentModel) \
                    .filter_by(equipment_subtype_id=equipment_subtype)

                # Пройдем циклом по списку дочерних брендов
                for equipment_model in list_models:

                    # Заменим родительский элемент
                    model = self.pgsql_connetction.session.query(EquipmentModel).get(equipment_model.id)
                    model.equipment_subtype_id = id
                    list_update.append(model)

        self.pgsql_connetction.session.add_all(list_update)
        self.pgsql_connetction.session.flush()

        result = {'success': True}

        if r_filter:
            query = self.pgsql_connetction.session.query(EquipmentSubtype)
            if r_filter.get('equipment_brand_id') is not None:
                query = query.filter(EquipmentSubtype.equipment_brand_id == r_filter['equipment_brand_id'])
            if r_filter.get('title') is not None:
                query = query.filter(EquipmentSubtype.title.ilike(f"%{r_filter['title']}%"))
            if r_filter.get('deleted') is not None:
                query = query.filter(r_filter['deleted'] or EquipmentSubtype.deleted.is_(False))

            query = query.order_by(EquipmentSubtype.title)

            result['count'] = query.count()

            query = query.limit(50)
            if r_filter.get('page', 0): query = query.offset(r_filter['page'] * 50)

            equipment_subtypes = query.all()

            data = []
            for row in equipment_subtypes:
                data.append({
                    'id': row.id,
                    'title': row.title,
                    'icon': row.icon,
                    'url': row.url,
                    'branches': row.branches,
                    'deleted': row.deleted,
                    'equipment_brand_id': row.equipment_brand_id
                })

            result['data'] = data
            result['page'] = r_filter.get('page', 0)
        else:
            result = {'success': True, 'message': f'{id} changed'}
        self.pgsql_connetction.session.commit()
        return result, 202
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def del_equipment_subtype(self, id):
    try:
        equipment_subtype = self.pgsql_connetction.session.query(EquipmentSubtype).get(id)
        if equipment_subtype:
            self.pgsql_connetction.session.delete(equipment_subtype)
            self.pgsql_connetction.session.commit()
            return {'success': True, 'message': f'{id} deleted'}, 202
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


# Таблица МОДИФИКАЦИЙ ИЗДЕЛИЙ ==================================================================================

def add_equipment_model(self, title, icon, url, branches, deleted, equipment_subtype_id, r_filter):
    try:
        equipment_model = EquipmentModel(
            title=title,
            icon=icon,
            url=url,
            branches=branches,
            deleted=deleted,
            equipment_subtype_id=equipment_subtype_id
        )
        self.pgsql_connetction.session.add(equipment_model)
        self.pgsql_connetction.session.flush()

        result = {'success': True}

        if r_filter:

            query = self.pgsql_connetction.session.query(EquipmentModel)
            if r_filter.get('equipment_subtype_id') is not None:
                query = query.filter(EquipmentModel.equipment_subtype_id == r_filter['equipment_subtype_id'])
            if r_filter.get('title') is not None:
                query = query.filter(EquipmentModel.title.ilike(f"%{r_filter['title']}%"))
            if r_filter.get('deleted') is not None:
                query = query.filter(r_filter['deleted'] or EquipmentModel.deleted.is_(False))

            query = query.order_by(EquipmentModel.title)

            result['count'] = query.count()

            query = query.limit(50)
            if r_filter.get('page', 0): query = query.offset(r_filter['page'] * 50)

            equipment_models = query.all()

            data = []

            for row in equipment_models:
                data.append({
                    'id': row.id,
                    'title': row.title,
                    'icon': row.icon,
                    'url': row.url,
                    'branches': row.branches,
                    'deleted': row.deleted,
                    'equipment_subtype_id': row.equipment_subtype_id
                })

            result['data'] = data
            result['page'] = r_filter.get('page', 0)
        else:
            self.pgsql_connetction.session.refresh(equipment_model)
            data = {
                'id': equipment_model.id,
                'title': equipment_model.title,
                'icon': equipment_model.icon,
                'url': equipment_model.url,
                'branches': equipment_model.branches,
                'deleted': equipment_model.deleted,
                'equipment_subtype_id': equipment_model.equipment_subtype_id
            }
            result['message'] = f'{equipment_model.id} added'
            result['data'] = data

        self.pgsql_connetction.session.commit()
        return result, 201
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def get_equipment_model(self, id=None, title=None, equipment_subtype_id=None, deleted=None, page=0):
    try:
        query = self.pgsql_connetction.session.query(EquipmentModel)

        if id is not None:
            query = query.filter(EquipmentModel.id == id)
        if equipment_subtype_id is not None:
            query = query.filter(EquipmentModel.equipment_subtype_id == equipment_subtype_id)
        if title is not None:
            query = query.filter(EquipmentModel.title.ilike(f'%{title}%'))
        if deleted is not None:
            query = query.filter(deleted or EquipmentModel.deleted.is_(False))

        query = query.order_by(EquipmentModel.title)

        result = {'success': True}

        result['count'] = query.count()

        query = query.limit(50)
        if page: query = query.offset(page * 50)

        equipment_model = query.all()

        data = []
        for row in equipment_model:
            data.append({
                'id': row.id,
                'title': row.title,
                'icon': row.icon,
                'url': row.url,
                'branches': row.branches,
                'deleted': row.deleted,
                'equipment_subtype_id': row.equipment_subtype_id
            })

        result['data'] = data
        result['page'] = page
        return result, 200
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def edit_equipment_model(
        self,
        id,
        title=None,
        icon=None,
        url=None,
        branches=None,
        deleted=None,
        equipment_subtype_id=None,
        r_filter=None
    ):
    try:
        equipment_model = self.pgsql_connetction.session.query(EquipmentModel).get(id)
        fields = inspect.getfullargspec(edit_equipment_model).args[:-2]  # список имен всех аргументов текущей фнкции
        for field in fields:
            war = locals()[field]  # Находим переменную от имени и присваеваем war
            if war is not None:
                setattr(equipment_model, field, war)

        self.pgsql_connetction.session.add(equipment_model)
        self.pgsql_connetction.session.flush()

        result = {'success': True}

        if r_filter:
            query = self.pgsql_connetction.session.query(EquipmentModel)
            if r_filter.get('equipment_subtype_id') is not None:
                query = query.filter(EquipmentModel.equipment_subtype_id == r_filter['equipment_subtype_id'])
            if r_filter.get('title') is not None:
                query = query.filter(EquipmentModel.title.ilike(f"%{r_filter['title']}%"))
            if r_filter.get('deleted') is not None:
                query = query.filter(r_filter['deleted'] or EquipmentModel.deleted.is_(False))

            query = query.order_by(EquipmentModel.title)

            result['count'] = query.count()

            query = query.limit(50)
            if r_filter.get('page', 0): query = query.offset(r_filter['page'] * 50)

            equipment_brands = query.all()

            data = []
            for row in equipment_brands:
                data.append({
                    'id': row.id,
                    'title': row.title,
                    'icon': row.icon,
                    'url': row.url,
                    'branches': row.branches,
                    'deleted': row.deleted,
                    'equipment_subtype_id': row.equipment_subtype_id
                })

            result['data'] = data
            result['page'] = r_filter.get('page', 0)
        else:
            result = {'success': True, 'message': f'{id} changed'}
        self.pgsql_connetction.session.commit()
        return result, 202
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def del_equipment_model(self, id):
    try:
        equipment_model = self.pgsql_connetction.session.query(EquipmentModel).get(id)
        if equipment_model:
            self.pgsql_connetction.session.delete(equipment_model)
            self.pgsql_connetction.session. v()
            return {'success': True, 'message': f'{id} deleted'}, 202
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550