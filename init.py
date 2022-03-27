


from urllib.request import urlopen
from data import test_img




import base64
data_uri = base64.b64encode(open('build/static/data/PCB/subtype31.jpeg', 'rb').read()).decode('utf-8')
print(data_uri[:77] == test_img[23:100])
print(test_img[23:100])