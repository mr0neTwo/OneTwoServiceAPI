import traceback

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
        self.pgsql_connetction.session.commit()
        result = {'success': True}
        if r_filter:
            equipment_types = self.pgsql_connetction.session.query(EquipmentType).filter(
                and_(
                    EquipmentType.title.ilike(f"%{r_filter['title']}%") if r_filter.get('title') else True,
                    (r_filter['deleted'] or EquipmentType.deleted.is_(False)) if r_filter.get('deleted') is not None else True
                )
            ).order_by(EquipmentType.title).order_by(EquipmentType.id)
            count = equipment_types.count()
            result['count'] = count

            num = 50

            max_page = count // num if count % num > 0 else count // num - 1

            if r_filter.get('page', 0) > max_page != -1:
                return {'success': False, 'message': 'page is not defined'}, 400

            data = []

            for row in equipment_types[num * r_filter.get('page', 0): num * (r_filter.get('page', 0) + 1)]:
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
            self.pgsql_connetction.session.refresh(equipment_type)
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
        self.pgsql_connetction.session.close()
        return result, 201
    except:
        self.pgsql_connetction.session.rollback()
        self.pgsql_connetction.session.close()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def get_equipment_type(self, id=None, title=None, deleted=None, page=0):
    try:
        if any([id, title, deleted is not None]):
            equipment_type = self.pgsql_connetction.session.query(EquipmentType).filter(
                and_(
                    EquipmentType.id == id if id else True,
                    EquipmentType.title.ilike(f'%{title}%') if title else True,
                    (deleted or EquipmentType.deleted.is_(False)) if deleted is not None else True
                )
            ).order_by(EquipmentType.title).order_by(EquipmentType.id)

        else:
            equipment_type = self.pgsql_connetction.session.query(EquipmentType)\
                .order_by(EquipmentType.title).order_by(EquipmentType.id)
        result = {'success': True}
        count = equipment_type.count()
        result['count'] = count

        num = 50

        max_page = count // num if count % num > 0 else count // num - 1

        if page > max_page != -1:
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

        result['data'] = data
        result['page'] = page
        self.pgsql_connetction.session.close()
        return result, 200
    except:
        self.pgsql_connetction.session.rollback()
        self.pgsql_connetction.session.close()
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
        self.pgsql_connetction.session.query(EquipmentType).filter_by(id=id).update({
            'title': title if title is not None else EquipmentType.title,
            'icon': icon if icon is not None else EquipmentType.icon,
            'url': url if url is not None else EquipmentType.url,
            'branches': branches if branches is not None else EquipmentType.branches,
            'deleted': deleted if deleted is not None else EquipmentType.deleted
        })
        # Если запрос содержит список для объединения
        if list_for_join is not None:
            # Пройдем циклом по вему списку
            for equipment_type in list_for_join:
                # Отметим запись как удаленную
                self.pgsql_connetction.session.query(EquipmentType)\
                    .filter_by(id=equipment_type)\
                    .update({'deleted': True})
                # Получим список дочерних брендов
                list_brands = self.pgsql_connetction.session.query(EquipmentBrand)\
                    .filter_by(equipment_type_id=equipment_type)
                # Пройдем циклом по списку дочерних брендов
                for equipment_brand in list_brands:
                    # Заменим родительский элемент
                    self.pgsql_connetction.session.query(EquipmentBrand)\
                        .filter_by(id=equipment_brand.id)\
                        .update({'equipment_type_id': id})
        self.pgsql_connetction.session.commit()
        if r_filter:
            equipment_types = self.pgsql_connetction.session.query(EquipmentType).filter(
                and_(
                    EquipmentType.title.ilike(f"%{r_filter['title']}%") if r_filter.get('title') else True,
                    (r_filter['deleted'] or EquipmentType.deleted.is_(False)) if r_filter.get('deleted') is not None else True
                )
            ).order_by(EquipmentType.title).order_by(EquipmentType.id)
            result = {'success': True}
            count = equipment_types.count()
            result['count'] = count

            num = 50

            max_page = count // num if count % num > 0 else count // num - 1

            if r_filter.get('page', 0) > max_page != -1:
                return {'success': False, 'message': 'page is not defined'}, 400

            data = []

            for row in equipment_types[num * r_filter.get('page', 0): num * (r_filter.get('page', 0) + 1)]:
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
        self.pgsql_connetction.session.close()
        return result, 202
    except:
        self.pgsql_connetction.session.rollback()
        self.pgsql_connetction.session.close()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def del_equipment_type(self, id):
    try:
        equipment_type = self.pgsql_connetction.session.query(EquipmentType).get(id)
        if equipment_type:
            self.pgsql_connetction.session.delete(equipment_type)
            self.pgsql_connetction.session.commit()
            self.pgsql_connetction.session.close()
            return {'success': True, 'message': f'{id} deleted'}, 202
    except:
        self.pgsql_connetction.session.rollback()
        self.pgsql_connetction.session.close()
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
        self.pgsql_connetction.session.commit()
        result = {'success': True}
        if r_filter:
            equipment_brands = self.pgsql_connetction.session.query(EquipmentBrand).filter(
                and_(
                    EquipmentBrand.equipment_type_id == r_filter['equipment_type_id'] if r_filter.get('equipment_type_id') else True,
                    EquipmentBrand.title.ilike(f"%{r_filter['title']}%") if r_filter.get('title') else True,
                    (r_filter['deleted'] or EquipmentBrand.deleted.is_(False)) if r_filter.get('deleted') is not None else True
                )
            ).order_by(EquipmentBrand.title).order_by(EquipmentBrand.id)
            count = equipment_brands.count()
            result['count'] = count

            num = 50

            max_page = count // num if count % num > 0 else count // num - 1

            page = r_filter.get('page', 0)
            if page > max_page != -1:
                return {'success': False, 'message': 'page is not defined'}, 400

            data = []

            for row in equipment_brands[num * page: num * (page + 1)]:
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
        self.pgsql_connetction.session.close()
        return result, 201
    except:
        self.pgsql_connetction.session.rollback()
        self.pgsql_connetction.session.close()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def get_equipment_brand(self, id=None, title=None, equipment_type_id=None, deleted=None, page=0):
    try:
        if any([id, title, equipment_type_id, deleted is not None]):
            equipment_brand = self.pgsql_connetction.session.query(EquipmentBrand).filter(
                and_(
                    EquipmentBrand.id == id if id else True,
                    EquipmentBrand.equipment_type_id == equipment_type_id if equipment_type_id else True,
                    EquipmentBrand.title.ilike(f'%{title}%') if title else True,
                    (deleted or EquipmentBrand.deleted.is_(False)) if deleted is not None else True
                )
            ).order_by(EquipmentBrand.title).order_by(EquipmentBrand.id)
        else:
            equipment_brand = self.pgsql_connetction.session.query(EquipmentBrand)\
                .order_by(EquipmentBrand.title).order_by(EquipmentBrand.id)

        result = {'success': True}
        count = equipment_brand.count()
        result['count'] = count

        max_page = count // 50 if count % 50 > 0 else count // 50 - 1

        if page > max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []

        for row in equipment_brand[50 * page: 50 * (page + 1)]:
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
        self.pgsql_connetction.session.close()
        return result, 200
    except:
        self.pgsql_connetction.session.rollback()
        self.pgsql_connetction.session.close()
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
        self.pgsql_connetction.session.query(EquipmentBrand).filter_by(id=id).update({
            'title': title if title is not None else EquipmentBrand.title,
            'icon': icon if icon is not None else EquipmentBrand.icon,
            'url': url if url is not None else EquipmentBrand.url,
            'branches': branches if branches is not None else EquipmentBrand.branches,
            'deleted': deleted if deleted is not None else EquipmentBrand.deleted,
            'equipment_type_id': equipment_type_id if equipment_type_id is not None else EquipmentBrand.equipment_type_id,
        })
        # Если запрос содержит список для объединения
        if list_for_join is not None:

            # Пройдем циклом по вему списку
            for equipment_brand in list_for_join:

                # Отметим запись как удаленную
                self.pgsql_connetction.session.query(EquipmentBrand) \
                    .filter_by(id=equipment_brand) \
                    .update({'deleted': True})

                # Получим список дочерних модулей
                list_subtype = self.pgsql_connetction.session.query(EquipmentSubtype) \
                    .filter_by(equipment_brand_id=equipment_brand)

                # Пройдем циклом по списку дочерних брендов
                for equipment_subtype in list_subtype:

                    # Заменим родительский элемент
                    self.pgsql_connetction.session.query(EquipmentSubtype) \
                        .filter_by(id=equipment_subtype.id) \
                        .update({'equipment_brand_id': id})
        self.pgsql_connetction.session.commit()
        if r_filter:
            equipment_brands = self.pgsql_connetction.session.query(EquipmentBrand).filter(
                and_(
                    EquipmentBrand.equipment_type_id == r_filter['equipment_type_id'] if r_filter.get('equipment_type_id') else True,
                    EquipmentBrand.title.ilike(f"%{r_filter['title']}%") if r_filter.get('title') else True,
                    (r_filter['deleted'] or EquipmentBrand.deleted.is_(False)) if r_filter.get('deleted') is not None else True
                )
            ).order_by(EquipmentBrand.title).order_by(EquipmentBrand.id)
            result = {'success': True}
            count = equipment_brands.count()
            result['count'] = count

            num = 50

            max_page = count // num if count % num > 0 else count // num - 1

            page = r_filter.get('page', 0)
            if page > max_page != -1:
                return {'success': False, 'message': 'page is not defined'}, 400

            data = []

            for row in equipment_brands[num * page: num * (page + 1)]:
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
        else:
            result = {'success': True, 'message': f'{id} changed'}
        self.pgsql_connetction.session.close()
        return result, 202
    except:
        self.pgsql_connetction.session.rollback()
        self.pgsql_connetction.session.close()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def del_equipment_brand(self, id):
    try:
        equipment_brand = self.pgsql_connetction.session.query(EquipmentBrand).get(id)
        if equipment_brand:
            self.pgsql_connetction.session.delete(equipment_brand)
            self.pgsql_connetction.session.commit()
            self.pgsql_connetction.session.close()
            return {'success': True, 'message': f'{id} deleted'}, 202
    except:
        self.pgsql_connetction.session.rollback()
        self.pgsql_connetction.session.close()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


# Таблица МОДИФИКАЦИЙ ИЗДЕЛИЙ ==================================================================================

def add_equipment_subtype(self, title, icon, url, branches, deleted, equipment_brand_id, r_filter):
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
        self.pgsql_connetction.session.commit()
        result = {'success': True}
        if r_filter:
            equipment_subtypes = self.pgsql_connetction.session.query(EquipmentSubtype).filter(
                and_(
                    EquipmentSubtype.equipment_brand_id == r_filter['equipment_brand_id'] if r_filter.get('equipment_brand_id') else True,
                    EquipmentSubtype.title.ilike(f"%{r_filter['title']}%") if r_filter.get('title') else True,
                    (r_filter['deleted'] or EquipmentSubtype.deleted.is_(False)) if r_filter.get('deleted') is not None else True
                )
            ).order_by(EquipmentSubtype.title).order_by(EquipmentSubtype.id)
            count = equipment_subtypes.count()
            result['count'] = count

            num = 50

            max_page = count // num if count % num > 0 else count // num - 1

            page = r_filter.get('page', 0)
            if page > max_page != -1:
                return {'success': False, 'message': 'page is not defined'}, 400

            data = []

            for row in equipment_subtypes[num * page: num * (page + 1)]:
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
        else:
            self.pgsql_connetction.session.refresh(equipment_subtype)
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
        self.pgsql_connetction.session.close()
        return result, 201
    except:
        self.pgsql_connetction.session.rollback()
        self.pgsql_connetction.session.close()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def get_equipment_subtype(self, id=None, title=None, equipment_brand_id=None, deleted=None, page=0):
    try:
        if any([id, title, equipment_brand_id, deleted is not None]):
            equipment_subtype = self.pgsql_connetction.session.query(EquipmentSubtype).filter(
                and_(
                    EquipmentSubtype.id == id if id else True,
                    EquipmentSubtype.equipment_brand_id == equipment_brand_id if equipment_brand_id else True,
                    EquipmentSubtype.title.ilike(f'%{title}%') if title else True,
                    (deleted or EquipmentSubtype.deleted.is_(False)) if deleted is not None else True
                )
            ).order_by(EquipmentSubtype.title).order_by(EquipmentSubtype.id)
        else:
            equipment_subtype = self.pgsql_connetction.session.query(EquipmentSubtype).order_by(EquipmentSubtype.title).order_by(EquipmentSubtype.id)

        result = {'success': True}
        count = equipment_subtype.count()
        result['count'] = count

        max_page = count // 50 if count % 50 > 0 else count // 50 - 1

        if page > max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []
        for row in equipment_subtype[50 * page: 50 * (page + 1)]:
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
        self.pgsql_connetction.session.close()
        return result, 200
    except:
        self.pgsql_connetction.session.rollback()
        self.pgsql_connetction.session.close()
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
        r_filter=None
    ):
    try:
        self.pgsql_connetction.session.query(EquipmentSubtype).filter_by(id=id).update({
            'title': title if title is not None else EquipmentSubtype.title,
            'icon': icon if icon is not None else EquipmentSubtype.icon,
            'url': url if url is not None else EquipmentSubtype.url,
            'branches': branches if branches is not None else EquipmentSubtype.branches,
            'deleted': deleted if deleted is not None else EquipmentSubtype.deleted,
            'equipment_brand_id': equipment_brand_id if equipment_brand_id is not None else EquipmentSubtype.equipment_brand_id,
        })
        # Если запрос содержит список для объединения
        if list_for_join is not None:

            # Пройдем циклом по вему списку
            for equipment_subtype in list_for_join:

                # Отметим запись как удаленную
                self.pgsql_connetction.session.query(EquipmentSubtype) \
                    .filter_by(id=equipment_subtype) \
                    .update({'deleted': True})

                # Получим список дочерних модулей
                list_models = self.pgsql_connetction.session.query(EquipmentModel) \
                    .filter_by(equipment_subtype_id=equipment_subtype)

                # Пройдем циклом по списку дочерних брендов
                for equipment_model in list_models:

                    # Заменим родительский элемент
                    self.pgsql_connetction.session.query(EquipmentModel) \
                        .filter_by(id=equipment_model.id) \
                        .update({'equipment_subtype_id': id})
        self.pgsql_connetction.session.commit()
        if r_filter:
            equipment_subtypes = self.pgsql_connetction.session.query(EquipmentSubtype).filter(
                and_(
                    EquipmentSubtype.equipment_brand_id == r_filter['equipment_brand_id'] if r_filter.get('equipment_brand_id') else True,
                    EquipmentSubtype.title.ilike(f"%{r_filter['title']}%") if r_filter.get('title') else True,
                    (r_filter['deleted'] or EquipmentSubtype.deleted.is_(False)) if r_filter.get('deleted') is not None else True
                )
            ).order_by(EquipmentSubtype.title).order_by(EquipmentSubtype.id)
            result = {'success': True}
            count = equipment_subtypes.count()
            result['count'] = count

            num = 50

            max_page = count // num if count % num > 0 else count // num - 1

            page = r_filter.get('page', 0)
            if page > max_page != -1:
                return {'success': False, 'message': 'page is not defined'}, 400

            data = []

            for row in equipment_subtypes[num * page: num * (page + 1)]:
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
        else:
            result = {'success': True, 'message': f'{id} changed'}
        self.pgsql_connetction.session.close()
        return result, 202
    except:
        self.pgsql_connetction.session.rollback()
        self.pgsql_connetction.session.close()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def del_equipment_subtype(self, id):
    try:
        equipment_subtype = self.pgsql_connetction.session.query(EquipmentSubtype).get(id)
        if equipment_subtype:
            self.pgsql_connetction.session.delete(equipment_subtype)
            self.pgsql_connetction.session.commit()
            self.pgsql_connetction.session.close()
            return {'success': True, 'message': f'{id} deleted'}, 202
    except:
        self.pgsql_connetction.session.rollback()
        self.pgsql_connetction.session.close()
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
        self.pgsql_connetction.session.commit()
        result = {'success': True}
        if r_filter:
            equipment_models = self.pgsql_connetction.session.query(EquipmentModel).filter(
                and_(
                    EquipmentModel.equipment_subtype_id == r_filter['equipment_subtype_id'] if r_filter.get('equipment_subtype_id') else True,
                    EquipmentModel.title.ilike(f"%{r_filter['title']}%") if r_filter.get('title') else True,
                    (r_filter['deleted'] or EquipmentModel.deleted.is_(False)) if r_filter.get('deleted') is not None else True
                )
            ).order_by(EquipmentModel.title).order_by(EquipmentModel.id)
            count = equipment_models.count()
            result['count'] = count

            num = 50

            max_page = count // num if count % num > 0 else count // num - 1

            page = r_filter.get('page', 0)
            if page > max_page != -1:
                return {'success': False, 'message': 'page is not defined'}, 400

            data = []

            for row in equipment_models[num * page: num * (page + 1)]:
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
        self.pgsql_connetction.session.close()
        return result, 201
    except:
        self.pgsql_connetction.session.rollback()
        self.pgsql_connetction.session.close()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def get_equipment_model(self, id=None, title=None, equipment_subtype_id=None, deleted=None, page=0):
    try:
        if any([id, title, equipment_subtype_id, deleted is not None]):
            equipment_model = self.pgsql_connetction.session.query(EquipmentModel).filter(
                and_(
                    EquipmentModel.id == id if id else True,
                    EquipmentModel.equipment_subtype_id == equipment_subtype_id if equipment_subtype_id else True,
                    EquipmentModel.title.ilike(f'%{title}%') if title else True,
                    (deleted or EquipmentModel.deleted.is_(False)) if deleted is not None else True
                )
            ).order_by(EquipmentModel.title).order_by(EquipmentModel.id)
        else:
            equipment_model = self.pgsql_connetction.session.query(EquipmentModel).order_by(EquipmentModel.title).order_by(EquipmentModel.id)

        self.pgsql_connetction.session.expire_all()
        result = {'success': True}
        count = equipment_model.count()
        result['count'] = count

        max_page = count // 50 if count % 50 > 0 else count // 50 - 1

        if page > max_page != -1:
            return {'success': False, 'message': 'page is not defined'}, 400

        data = []
        for row in equipment_model[50 * page: 50 * (page + 1)]:
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
        self.pgsql_connetction.session.close()
        return result, 200
    except:
        self.pgsql_connetction.session.rollback()
        self.pgsql_connetction.session.close()
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
        self.pgsql_connetction.session.query(EquipmentModel).filter_by(id=id).update({
            'title': title if title is not None else EquipmentModel.title,
            'icon': icon if icon is not None else EquipmentModel.icon,
            'url': url if url is not None else EquipmentModel.url,
            'branches': branches if branches is not None else EquipmentModel.branches,
            'deleted': deleted if deleted is not None else EquipmentModel.deleted,
            'equipment_subtype_id': equipment_subtype_id if equipment_subtype_id is not None else EquipmentModel.equipment_subtype_id,
        })
        self.pgsql_connetction.session.commit()
        if r_filter:
            equipment_models = self.pgsql_connetction.session.query(EquipmentModel).filter(
                and_(
                    EquipmentModel.equipment_subtype_id == r_filter['equipment_subtype_id'] if r_filter.get('equipment_subtype_id') else True,
                    EquipmentModel.title.ilike(f"%{r_filter['title']}%") if r_filter.get('title') else True,
                    (r_filter['deleted'] or EquipmentModel.deleted.is_(False)) if r_filter.get('deleted') is not None else True
                )
            ).order_by(EquipmentModel.title).order_by(EquipmentModel.id)
            result = {'success': True}
            count = equipment_models.count()
            result['count'] = count

            num = 50

            max_page = count // num if count % num > 0 else count // num - 1

            page = r_filter.get('page', 0)
            if page > max_page != -1:
                return {'success': False, 'message': 'page is not defined'}, 400

            data = []

            for row in equipment_models[num * page: num * (page + 1)]:
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
        else:
            result = {'success': True, 'message': f'{id} changed'}
        self.pgsql_connetction.session.close()
        return result, 202
    except:
        self.pgsql_connetction.session.rollback()
        self.pgsql_connetction.session.close()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def del_equipment_model(self, id):
    try:
        equipment_model = self.pgsql_connetction.session.query(EquipmentModel).get(id)
        if equipment_model:
            self.pgsql_connetction.session.delete(equipment_model)
            self.pgsql_connetction.session.commit()
            self.pgsql_connetction.session.close()
            return {'success': True, 'message': f'{id} deleted'}, 202
    except:
        self.pgsql_connetction.session.rollback()
        self.pgsql_connetction.session.close()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550