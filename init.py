import traceback
from pprint import pprint

try:
    a = 0
    b = 1
    print(b/a)
except Exception as ex:
    print(ex.args[-1])
    # print(ex)
    # pprint(dir(ex))
    print(traceback.format_exc())
finally:
    print('finally')

print('next code')