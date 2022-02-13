from app.db.interaction.interaction import DbInteraction
import time

start_time = time.time()
db = DbInteraction(
    host='5.53.124.252',
    port='5432',
    user='postgres',
    password='225567',
    db_name='one_two',
    rebuild_db=False
)
db.create_all_tables()
db.initial_data()
db.update_date_from_remonline()
db.reset_dict()

dtime = time.time() - start_time
hours = int(dtime // 3600)
minutes = int((dtime % 3600) // 60)
seconds = int((dtime % 3600) % 60)
print(f'Обновление завершено за {hours}:{minutes:02}:{seconds:02}')

