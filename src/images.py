import geo_transform

import os
import requests

import numpy as np
from PIL import Image
import rasterio
from rasterio.transform import from_bounds


def get_image():
    layers = "unisat"
    unisat_uids = "2503070951511033504900361"
    service = "wms"
    request = "GetMap"
    BBOX = "31.043,67.093,35.283,70.246"
    format = "tif"
    db_pkg_mode = "hrsat"
    height = 1024
    width = 1024
    ukey = "53616c7465645f5f4d5d9043e4ef4a6f7c915d382c1a2260fd9f01800279786afb18a03f7be9b321"

    # http://sci-vega.ru/fap/toproxy/export/local/smiswms/get_map.pl?layers=unisat&unisat_uids=2503070951511033504900361&service=wms&request=GetMap&
    # BBOX=31.043,67.093,35.283,70.246
    # format=tif
    # db_pkg_mode=hrsat
    # height=1024
    # width=1024
    # ukey=53616c7465645f5f4d5d9043e4ef4a6f7c915d382c1a2260fd9f01800279786afb18a03f7be9b321
    base_url = "http://sci-vega.ru/fap/toproxy/export/local/smiswms/get_map.pl"
    image_url = f"{base_url}?layers={layers}&unisat_uids={unisat_uids}&service={service}&request={request}&BBOX={BBOX}&format={format}&db_pkg_mode={db_pkg_mode}&height={height}&width={width}&ukey={ukey}"

    print(image_url)

    return image_url

# # URL для загрузки PNG
# url = get_image()

# # Географические координаты (BBOX)
# left, bottom = geo_transform.wgs84_to_web_mercator(31.043, 67.093)
# right, top = geo_transform.wgs84_to_web_mercator(35.283, 70.246)

# # Размеры изображения
# width, height = 1024, 1024

# # Загрузка PNG
# response = requests.get(url)
# if response.status_code != 200:
#     raise Exception("Ошибка при загрузке изображения")

# # Открытие изображения с помощью Pillow
# image = Image.open(requests.get(url, stream=True).raw)

# # Преобразование изображения в массив numpy
# image_array = np.array(image)

# # Если изображение RGBA, оставляем только RGB
# if image_array.shape[2] == 4:
#     image_array = image_array[:, :, :3]

# # Трансформация для GeoTIFF
# transform = from_bounds(left, bottom, right, top, width, height)

# # Сохранение в GeoTIFF
# with rasterio.open(
#     "output.tif",  # Имя выходного файла
#     "w",  # Режим записи
#     driver="GTiff",  # Формат файла
#     height=height,  # Высота изображения
#     width=width,  # Ширина изображения
#     count=3,  # Количество каналов (RGB)
#     dtype=image_array.dtype,  # Тип данных
#     crs="EPSG:3857",  # Система координат (WGS84)
#     transform=transform,  # Геопривязка
# ) as dst:
#     # Запись данных
#     for channel in range(3):  # RGB
#         dst.write(image_array[:, :, channel], channel + 1)

# print("GeoTIFF успешно сохранён: output.tif")


# # get_image()

def main():
    url = get_image()

    # current_directory = os.getcwd()

    # print(current_directory)
    output_folder = "images"

    # Имя файла
    filename = "image.tif"
    file_path = os.path.join(output_folder, filename)

    # Выполняем GET-запрос
    response = requests.get(url)

    # Проверяем статус ответа
    if response.status_code == 200:
        # Сохраняем содержимое ответа в файл
        with open(file_path, "wb") as file:
            file.write(response.content)
        print(f"Файл сохранён: {file_path}")
    else:
        print(f"Ошибка: {response.status_code}")

main()
