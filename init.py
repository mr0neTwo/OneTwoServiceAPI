import random
from pprint import pprint

from data import equipment_type



t_fil = [{
    'title': random.choice(equipment_type)[:random.randint(30, 50)],
    'deleted': bool(random.randint(0, 1))
} for x in range(10)] + [False, False, False]

pprint(t_fil)