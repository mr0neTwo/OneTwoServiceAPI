import inspect
import io
import traceback
from pprint import pprint
from urllib.request import urlopen
from PIL import Image
import numpy

from sqlalchemy import func
from werkzeug.security import generate_password_hash

from app.db.models.models import Employees, Payrolls


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
                 password,
                 filter_employees):
    try:
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
            password=generate_password_hash(password)
        )
        self.pgsql_connetction.session.add(employees)
        self.pgsql_connetction.session.flush()

        result = {'success': True}

        if filter_employees:

            query = self.pgsql_connetction.session.query(Employees)
            if filter_employees.get('deleted') is not None:
                query = query.filter(filter_employees['deleted'] or Employees.deleted.is_(False))

            query = query.order_by(Employees.last_name)

            result['count'] = query.count()

            query = query.limit(50)
            if filter_employees.get('page', 0): query = query.offset(filter_employees['page'] * 50)

            employees = query.all()

            data = []
            for row in employees:
                query = self.pgsql_connetction.session.query(func.sum(Payrolls.income + Payrolls.outcome))
                query = query.filter(Payrolls.employee_id == row.id)
                query = query.filter(Payrolls.deleted.is_(False))
                balance = query.scalar()

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

            result['employees'] = data
            result['page'] = filter_employees.get('page', 0)

        self.pgsql_connetction.session.commit()
        return result, 201
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def get_employee(self, id=None, deleted=None, page=0):
    try:
        query = self.pgsql_connetction.session.query(Employees)
        if id is not None:
            query = query.filter(Employees.id == id)
        if deleted is not None:
            query = query.filter(deleted or Employees.deleted.is_(False))

        query = query.order_by(Employees.last_name)

        result = {'success': True}

        result['count'] = query.count()

        query = query.limit(50)
        if page: query = query.offset(page * 50)

        employees = query.all()

        data = []
        for row in employees:

            query = self.pgsql_connetction.session.query(func.sum(Payrolls.income + Payrolls.outcome))
            query = query.filter(Payrolls.employee_id == row.id)
            query = query.filter(Payrolls.deleted.is_(False))
            balance = query.scalar()

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
        return result, 200
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def edit_employee(
        self,
        id,
        first_name,
        last_name,
        email,
        phone,
        notes,
        post,
        deleted,
        inn,
        doc_name,
        permissions,
        role_id,
        login,
        # password,
        filter_employees=None
    ):
    try:
        employee = self.pgsql_connetction.session.query(Employees).get(id)

        fields = inspect.getfullargspec(edit_employee).args[:-1]  # список имен всех аргументов текущей фнкции
        for field in fields:
            war = locals()[field]  # Находим переменную от имени и присваеваем war
            if war is not None:
                setattr(employee, field, war)
        # if password is not None: employee.password = generate_password_hash(password)

        self.pgsql_connetction.session.add(employee)

        result = {'success': True}

        if filter_employees:

            query = self.pgsql_connetction.session.query(Employees)
            if filter_employees.get('deleted') is not None:
                query = query.filter(filter_employees['deleted'] or Employees.deleted.is_(False))

            query = query.order_by(Employees.last_name)

            result['count'] = query.count()

            query = query.limit(50)
            if filter_employees.get('page', 0): query = query.offset(filter_employees['page'] * 50)

            employees = query.all()

            data = []
            for row in employees:
                query = self.pgsql_connetction.session.query(func.sum(Payrolls.income + Payrolls.outcome))
                query = query.filter(Payrolls.employee_id == row.id)
                query = query.filter(Payrolls.deleted.is_(False))
                balance = query.scalar()

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

            result['employees'] = data
            result['page'] = filter_employees.get('page', 0)

        self.pgsql_connetction.session.commit()
        return result, 202
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def del_employee(self, id):
    try:
        employees = self.pgsql_connetction.session.query(Employees).get(id)
        if employees:
            self.pgsql_connetction.session.delete(employees)
            self.pgsql_connetction.session.commit()
            return {'success': True, 'message': f'{id} deleted'}, 202
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def cange_userpassword(self, id, password):
    try:
        employee = self.pgsql_connetction.session.query(Employees).get(id)
        employee.password = generate_password_hash(password)
        self.pgsql_connetction.session.add(employee)
        self.pgsql_connetction.session.commit()
        return {'success': True, 'message': f'password has changed for{id}'}, 202
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550

def change_avatar(self, employee_id, left, top, size, img):
    try:
        # Загрузим данные из URI в переменную
        with urlopen(img) as response:
            data = response.read()

        image_file = io.BytesIO(data)
        img = Image.open(image_file)
        img.thumbnail(size)

        # Создадим Numpy массив из данных
        img = numpy.asarray(img, dtype=numpy.uint8)

        # height = img.shape[0]
        # width = img.shape[1]
        y = 0 if top > 0 else abs(top) # Координата Х с которой начинаем резать
        x = 0 if left > 0 else abs(left) # Координата Y с которой начинаем резать
        h = 250 # Высота обрезки
        w = 250 # Длина обрезки
        # Если сверху есть пустая полоса
        color = [40, 46, 51]
        if top > 0:
            # Создадам пустой массив нужного нам цвета
            chanal_r = numpy.zeros((top, img.shape[1], 1), dtype=int)
            chanal_r.fill(color[0])
            chanal_g = numpy.zeros((top, img.shape[1], 1), dtype=int)
            chanal_g.fill(color[1])
            chanal_b = numpy.zeros((top, img.shape[1], 1), dtype=int)
            chanal_b.fill(color[2])
            arr_top = numpy.concatenate((chanal_r, chanal_g, chanal_b), axis=2)
            # Добавим к текущей картинке
            img = numpy.concatenate((arr_top, img), axis=0)
        # Если слева есть пустая полоса
        if left > 0:
            chanal_r = numpy.zeros((img.shape[0], left, 1), dtype=int)
            chanal_r.fill(color[0])
            chanal_g = numpy.zeros((img.shape[0], left, 1), dtype=int)
            chanal_g.fill(color[1])
            chanal_b = numpy.zeros((img.shape[0], left, 1), dtype=int)
            chanal_b.fill(color[2])
            arr_left = numpy.concatenate((chanal_r, chanal_g, chanal_b), axis=2)
            # Добавим к текущей картинке
            img = numpy.concatenate((arr_left, img), axis=1)
        # Если снизу есть пустая полоса
        if img.shape[0] - y < h:
            height_button = h - (img.shape[0] - y)
            chanal_r = numpy.zeros((height_button, img.shape[1], 1), dtype=int)
            chanal_r.fill(color[0])
            chanal_g = numpy.zeros((height_button, img.shape[1], 1), dtype=int)
            chanal_g.fill(color[1])
            chanal_b = numpy.zeros((height_button, img.shape[1], 1), dtype=int)
            chanal_b.fill(color[2])
            arr_left = numpy.concatenate((chanal_r, chanal_g, chanal_b), axis=2)
            # Добавим к текущей картинке
            img = numpy.concatenate((img, arr_left), axis=0)
        # Если справа есть пустая полоса
        if img.shape[1] - x < w:
            width_right = w - (img.shape[1] - x)
            chanal_r = numpy.zeros((img.shape[0], width_right, 1), dtype=int)
            chanal_r.fill(color[0])
            chanal_g = numpy.zeros((img.shape[0], width_right, 1), dtype=int)
            chanal_g.fill(color[1])
            chanal_b = numpy.zeros((img.shape[0], width_right, 1), dtype=int)
            chanal_b.fill(color[2])
            arr_left = numpy.concatenate((chanal_r, chanal_g, chanal_b), axis=2)
            # Добавим к текущей картинке
            img = numpy.concatenate((img, arr_left), axis=1)

        # Обрезаем изображение
        crop = img[y:y + h, x:x + w]
        # Сохраняем на диске
        # cv2.imwrite(f'build/static/data/avatars/ava{employee_id}.jpeg', crop)
        crop = Image.fromarray(numpy.uint8(crop)).convert('RGB')
        crop.save(f'build/static/data/avatars/ava{employee_id}.jpeg')


        employee = self.pgsql_connetction.session.query(Employees).get(employee_id)
        # Определим путь для доступа к этому файлу изображения
        employee.avatar = f'data/avatars/ava{employee_id}.jpeg'

        self.pgsql_connetction.session.add(employee)
        self.pgsql_connetction.session.flush()
        self.pgsql_connetction.session.refresh(employee)

        result = {'success': True}


        result['user'] = {
            'id': employee.id,
            'first_name': employee.first_name,
            'last_name': employee.last_name,
            'email': employee.email,
            'phone': employee.phone,
            'notes': employee.notes,
            'deleted': employee.deleted,
            'inn': employee.inn,
            'doc_name': employee.doc_name,
            'post': employee.post,
            'permissions': employee.permissions,
            'role': {
                'id': employee.role.id,
                'title': employee.role.title,
                'earnings_visibility': employee.role.earnings_visibility,
                'leads_visibility': employee.role.leads_visibility,
                'orders_visibility': employee.role.orders_visibility,
                'permissions': employee.role.permissions,
                'settable_statuses': employee.role.settable_statuses,
                'visible_statuses': employee.role.visible_statuses,
                'settable_discount_margin': employee.role.settable_discount_margin
            },
            'login': employee.login,
            'table_headers': [{
                'id': head.id,
                'title': head.title,
                'field': head.field,
                'width': head.width,
                'employee_id': head.employee_id,
                'visible': head.visible
            } for head in employee.table_headers] if employee.table_headers else [],
            'payrules': [{
                'id': pr.id,
                'type_rule': pr.type_rule,
                'order_type': pr.order_type,
                'method': pr.method,
                'coefficient': pr.coefficient,
                'count_coeff': pr.count_coeff,
                'fix_salary': pr.fix_salary
            } for pr in employee.payrules] if employee.payrules else [],
        }

        self.pgsql_connetction.session.commit()
        return result, 202

    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550



