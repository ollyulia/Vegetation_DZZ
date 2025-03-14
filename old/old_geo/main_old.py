#import base64
import requests
import json
import os


username = "student1"
password = "ZfE-4wz-P3F-D2s"
base_res_id = 207 # Идентификатор базовой папки для пользователя student1
AUTH = (username, password)

#base_url = f'https://{username}:{password}@geo.mauniver.ru/api/'
base_url = f'https://geo.mauniver.ru/api/'
auth_url = 'component/auth/login'
res_url = 'resource/'
headers = {'Accept': '*/*'}

# Выполняем авторизацию
url = base_url + auth_url
r = requests.post(url, auth=(username, password), data={"login": "student1", "password":"ZfE-4wz-P3F-D2s"}, headers=headers)
cookies = r.cookies

url = base_url+res_url
print(url)

# data = {"resource":
#             {"cls": "resource_group",
#              "display_name": "foldername2",
#              "parent": {"id": base_res_id},
#              "description" : "wwwwwwwwww"}
#         }
#
# r = requests.post(url, data=data, cookies=cookies, headers=headers)
# print(r.text)
# #

r= requests.post(url=url,
                 json={
                     "resource": {
                         "cls":"resource_group",
                         "parent":{"id":base_res_id},
                         "display_name": 'qqqqq',
                         "description": 'qwertyu',
                     }
                 },
                 auth=AUTH
                 )