import requests
import json
import os

# импорт данных для авторизации
from vega import *

base_url = f'http://{user}:{pwd}@sci-vega.ru/fap/toproxy'

def get_all_params(base_url='', server='', url_file='', user='', pwd='', ukey=''):
    if not base_url or not user or not pwd or not ukey or not server or not url_file:
        print('Не указаны обязательные параметры!')
        return

    # Дополняем базовый URL данными
    base_url = f'{base_url}/{server}/local/smiswms/{url_file}?ukey={ukey}'

    # Запрос всех возможных значений параметров (справочников) - спутники, приборы, станции, продукты:
    # Переменные в запросе
    db_pkg_mode='hrsat'
    layers='unisat'
    REQUEST='GetMetadataVariants'
    url=f'{base_url}&db_pkg_mode={db_pkg_mode}&layers={layers}&REQUEST={REQUEST}'

    # print(url)

    r = requests.get(url)
    if r.status_code != 200:
        r = 'Ошибка!'

    return r.json()

def write_json_to_file(json_data, file_path):
    formatted_json = json.dumps(json_data, indent=4)

    with open(file_path, "w") as f:
        f.write(str(formatted_json))
        print(f"JSON успешно записан в файл по пути: '{file_path}'")

    return

def print_all_entries(json_data):
    print("Справочники:")
    for key in json_data.keys():
        print(key)
    return

def get_specified_device(json_data, device):
    print(f"Информация по отдельному прибору \"{device}\":")
    print(json_data["devices_info"][device])

    return

def get_image():

    layers = "unisat"
    unisat_uids = "2503070951511033504900361"
    service = "wms"
    request = "GetMap"
    BBOX = "31.043,67.093,35.283,70.246"
    format = "png"
    db_pkg_mode = "hrsat"
    height = 1024
    width = 1024
    ukey = "53616c7465645f5f4d5d9043e4ef4a6f7c915d382c1a2260fd9f01800279786afb18a03f7be9b321"

    # http://sci-vega.ru/fap/toproxy/export/local/smiswms/get_map.pl?layers=unisat&unisat_uids=2503070951511033504900361&service=wms&request=GetMap&
    # BBOX=31.043,67.093,35.283,70.246
    # format=png
    # db_pkg_mode=hrsat
    # height=1024
    # width=1024
    # ukey=53616c7465645f5f4d5d9043e4ef4a6f7c915d382c1a2260fd9f01800279786afb18a03f7be9b321
    base_url = "http://sci-vega.ru/fap/toproxy/export/local/smiswms/get_map.pl"
    image_url = f"{base_url}?layers={layers}&unisat_uids={unisat_uids}&service={service}&request={request}&BBOX={BBOX}&format={format}&db_pkg_mode={db_pkg_mode}&height={height}&width={width}&ukey={ukey}"

    print(image_url)


def get_json_from_file(file_path):
    file = open(file_path, "r")
    # Read the entire content of the file
    content = file.read()
    # Print the content
    json_data = json.loads(content)
    # Close the file
    file.close()

    return json_data

def main():
    server = 'export'
    url_file = 'get_metadata.pl'
    # json_data = get_all_params(base_url, server, url_file, user, pwd, ukey)

    file_path = "/home/student/Projects/pythonProject/all_params.json"

    json_data = get_json_from_file(file_path)

    # print(json_data)



    # write_json_to_file(json_data, file_path)

    # Демонстрация доступа к данным:
    # - все справочники
    print_all_entries(json_data)


    # - отдельный прибор
    device = "HYPERION"
    get_specified_device(json_data, device)

    # - графическое изображение
    get_image()

    return

main()

# print(r.headers['content-type'])
# print(r.encoding)
# print(r.text)
# print(r.json())
# print(r.json()['stations_info']['PLANETA'])
# print(r.json()['products_info']['KMSS_NIR_GEOCORR'])

# server = 'nffc_hrsatdb'
# url_file= 'get_map.pl'
# print(get_zzz(base_url, server, url_file, user, pwd, ukey))
