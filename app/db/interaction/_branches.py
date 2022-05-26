import inspect
import traceback

from sqlalchemy import or_

from app.db.models.models import Branch, Schedule


def add_branch(
        self,
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
        deleted,
        schedule=None,
        branch_filter=None
    ):
    try:
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
        self.pgsql_connetction.session.flush()

        if schedule:
            self.pgsql_connetction.session.refresh(branch)
            for schedule_day in schedule:
                day = Schedule(
                    start_time=schedule_day['start_time'],
                    end_time=schedule_day['end_time'],
                    work_day=schedule_day['work_day'],
                    week_day=schedule_day['week_day'],
                    branch_id=branch.id
                )
                self.pgsql_connetction.session.add(day)
            self.pgsql_connetction.session.flush()

        result = {'success': True}

        if branch_filter:
            query = self.pgsql_connetction.session.query(Branch)

            if branch_filter.get('deleted') is not None:
                query = query.filter(deleted or Branch.deleted.is_(False))
            query = query.order_by(Branch.name)

            result['count'] = query.count()

            query = query.limit(50)
            page = branch_filter.get('page', 0)
            if page: query = query.offset(page * 50)

            branches = query.all()

            if branch_filter.get('employee_id') is not None:
                branches = list(filter(lambda branch:  branch_filter['employee_id'] in branch.employees, branches))

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

            result['branches'] = data

        self.pgsql_connetction.session.commit()
        return result, 201
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def get_branch(self, id=None, deleted=None, employee_id=None, page=0):
    try:
        query = self.pgsql_connetction.session.query(Branch)
        if id is not None:
            query = query.filter(Branch.id == id)
        if deleted is not None:
            query = query.filter(or_(deleted, Branch.deleted.is_(False)))
        query = query.order_by(Branch.name)

        result = {'success': True}

        result['count'] = query.count()

        query = query.limit(50)
        if page: query = query.offset(page * 50)

        branches = query.all()

        if employee_id is not None:
            branches = list(filter(lambda branch: employee_id in branch.employees, branches))

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

        result['data'] = data
        result['page'] = page
        return result, 200
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def edit_branch(
        self,
        id,
        name=None,
        address=None,
        phone=None,
        color=None,
        icon=None,
        orders_type_id=None,
        orders_type_strategy=None,
        orders_prefix=None,
        documents_prefix=None,
        employees=None,
        deleted=None,
        schedule=None,
        branch_filter=None
    ):
    try:
        branch = self.pgsql_connetction.session.query(Branch).get(id)
        fields = inspect.getfullargspec(edit_branch).args[:-2]  # список имен всех аргументов текущей фнкции
        for field in fields:
            war = locals()[field]  # Находим переменную от имени и присваеваем war
            if war is not None:
                setattr(branch, field, war)
        self.pgsql_connetction.session.add(branch)
        self.pgsql_connetction.session.flush()

        if schedule:
            for schedule_day in schedule:
                day = self.pgsql_connetction.session.query(Schedule).get(schedule_day['id'])
                if schedule_day.get('start_time') is not None:
                    day.start_time = schedule_day['start_time']
                if schedule_day.get('end_time') is not None:
                    day.end_time = schedule_day['end_time']
                if schedule_day.get('work_day') is not None:
                    day.work_day = schedule_day['work_day']
                if schedule_day.get('week_day') is not None:
                    day.week_day = schedule_day['week_day']
                if schedule_day.get('branch_id') is not None:
                    day.branch_id = schedule_day['branch_id']
                self.pgsql_connetction.session.add(day)
            self.pgsql_connetction.session.flush()

        result = {'success': True}

        if branch_filter:
            query = self.pgsql_connetction.session.query(Branch)
            if branch_filter.get('deleted') is not None:
                query = query.filter(deleted or Branch.deleted.is_(False))
            query = query.order_by(Branch.name)

            result['count'] = query.count()

            query = query.limit(50)
            page = branch_filter.get('page', 0)
            if page: query = query.offset(page * 50)

            branches = query.all()

            if branch_filter.get('employee_id') is not None:
                branches = list(filter(lambda branch:  branch_filter['employee_id'] in branch.employees, branches))

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

            result['branches'] = data

        self.pgsql_connetction.session.commit()
        return result, 202
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550


def del_branch(self, id):
    try:
        branch = self.pgsql_connetction.session.query(Branch).get(id)
        if branch:
            self.pgsql_connetction.session.delete(branch)
            self.pgsql_connetction.session.commit()
            return {'success': True, 'message': f'{id} deleted'}, 202
    except:
        self.pgsql_connetction.session.rollback()
        print(traceback.format_exc())
        result = {'success': False, 'message': 'server error'}
        return result, 550