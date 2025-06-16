# import io
# import numpy as np
# import rasterio
# import requests
# import secret
# import traceback
# from PIL import Image
# from rasterio.transform import from_bounds

# GET_METADATA_PL = "get_metadata.pl"
# GET_MAP_PL = "get_map.pl"

# # Query параметры
# # Эти два параметра не меняются из всех показанных примеров доступа к Веге
# DB_PKG_MODE = "hrsat"
# LAYERS_UNISAT = "unisat"
# SERVICE_WMS = "wms"
# FORMAT_PNG = "png"
# EXCEPTION_XML = "xml"
# SATELLITES_LANDSAT_8 = "LANDSAT 8"

# SRS_4326 = "epsg:4326"

# # Виды запросов
# # Получение метаданных (json)
# REQUEST_GET_METADATA_VARIANTS = "GetMetadataVariants"
# # Получение информации о доступных снимках
# REQUEST_GET_METADATA_IMAGES = "GetMetadata"
# # Получение снимка
# REQUEST_GET_MAP = "GetMap"

# PATH = "images/downloaded" # Путь для загрузки файлов

# def convert_png_url_to_geotiff(
#         url: str,
#         lower_left_latitude: float,
#         lower_left_longitude: float,
#         upper_right_latitude: float,
#         upper_right_longitude: float,
#         output_tif_path: str
#     ) -> bool:
#     """
#     Скачивает PNG по URL, преобразует в GeoTIFF с заданными координатами

#     :param url: URL PNG-изображения
#     :param lower_left_latitude: нижняя левая широта (ymin)
#     :param lower_left_longitude: нижняя левая долгота (xmin)
#     :param upper_right_latitude: верхняя правая широта (ymax)
#     :param upper_right_longitude: верхняя правая долгота (xmax)
#     :param output_tif_path: путь для сохранения GeoTIFF
#     :return: True при успехе, False при ошибке
#     """
#     try:
#         # 1. Скачивание данных с проверками
#         response = requests.get(url=url, stream=True)
#         response.raise_for_status()  # Проверка HTTP ошибок

#         # Проверка типа содержимого
#         content_type = response.headers.get('Content-Type', '').lower()
#         if 'image' not in content_type and not url.lower().endswith('.png'):
#             print(f"Предупреждение: URL не возвращает изображение (Content-Type: {content_type})")
#             print(f"URL: {url}")

#             return False

#         # Сохраняем сырые данные для диагностики
#         raw_data = response.content

#         # 3. Загрузка изображения
#         png_image = Image.open(io.BytesIO(raw_data))

#         # 4. Подготовка данных для GeoTIFF
#         array = np.array(png_image)

#         # 5. Создание GeoTIFF
#         bounds = (
#             lower_left_longitude,
#             lower_left_latitude,
#             upper_right_longitude,
#             upper_right_latitude
#         )

#         transform = from_bounds(*bounds, width=array.shape[1], height=array.shape[0])

#         profile = {
#             'driver': 'GTiff',
#             'height': array.shape[0],
#             'width': array.shape[1],
#             'count': 1 if array.ndim == 2 else array.shape[2],
#             'dtype': array.dtype,
#             'transform': transform,
#             'crs': 'EPSG:4326',
#         }

#         # 6. Сохранение GeoTIFF
#         with rasterio.open(output_tif_path, 'w', **profile) as dst:
#             if array.ndim == 2:
#                 dst.write(array, 1)
#             else:
#                 for i in range(profile['count']):
#                     dst.write(array[:, :, i], i+1)

#         return True

#     except Exception as exception:
#         print(f"Ошибка при обработке изображения:")
#         print(f"    URL: {url}")
#         print(f"    Тип ошибки: {type(exception).__name__}")
#         print(f"    Сообщение: {str(exception)}")
#         print("    Трассировка:")
#         print(traceback.format_exc())
#         return False


# class VegaScience:
#     def __init__(self, vega_username: str, vega_password: str, ukey: str):
#         self._base_url = f"http://{vega_username}:{vega_password}@sci-vega.ru/fap/toproxy/export/local/smiswms/"
#         self._ukey = ukey

#     def download_images_by_coordinates(
#         self,
#         start_date: str,
#         end_date: str,
#         max_cloudiness: int,
#         lower_left_latitude: float,
#         lower_left_longitude: float,
#         upper_right_latitude: float,
#         upper_right_longitude: float,
#     ):
#         downloaded_images = {
#             "B4": {},
#             "B5": {},
#             "other": {}
#         }

#         print("Начало загрузки снимков с Vega Science")

#         print("Получение информации о доступных снимках...")
#         avaliable_images_url = self._format_url_avaliable_images(
#             start_date,
#             end_date,
#             max_cloudiness,
#             lower_left_latitude,
#             lower_left_longitude,
#             upper_right_latitude,
#             upper_right_longitude
#         )

#         response = self._get_content(avaliable_images_url).json()

#         data = response["DATA"]

#         data_len = len(data)
#         if data_len == 0:
#             print("Снимки не найдены.")
#             return downloaded_images
#         else:
#             print(f"Найдено {data_len} снимков.")

#         # {
#         #     "date": str,
#         #     "B4_ID": str,
#         #     "B5_ID": str
#         # }
#         prepared_ids = []

#         for data_object in data:
#             common = data_object["common"]
#             if common is None:
#                 print("    Не найдено поле common")
#                 continue

#             device = common["device"]
#             if device is None or device != "OLI_TIRS": # нужный девайс, иначе снимки не совсем те
#                 continue

#             date = common["dt"]
#             if date is None:
#                 print("    Не найдено поле dt")
#                 continue
#             date = date.replace("-", "")
#             date = date.replace(":", "")
#             date = date.replace(" ", "_")

#             products = data_object["products"]

#             if products is None:
#                 print("    Не найдено поле products")
#                 continue

#             band_4 = products["v_red_ch"]
#             if band_4 is None:
#                 print("    Не найден 4 канал")
#                 continue

#             band_4_id = band_4["id"]
#             if band_4_id is None:
#                 print("    Не найден id снимка 4 канала")
#                 continue

#             band_5 = products["v_nir_ch"]
#             if band_5 is None:
#                 print("    Не найден 5 канал")
#                 continue

#             band_5_id = band_5["id"]
#             if band_5_id is None:
#                 print("    Не найден id снимка 5 канала")
#                 continue

#             ids = {
#                 "date": date,
#                 "B4_ID": band_4_id,
#                 "B5_ID": band_5_id
#             }

#             prepared_ids.append(ids)

#         print("Скачивание снимков.")
#         total_images_to_download = len(prepared_ids)
#         current_image_to_download = 1

#         for prepared_obj in prepared_ids:
#             print(f"[{current_image_to_download}/{total_images_to_download}] Загрузка снимка...")
#             url = self._format_url_image_by_id(
#                 prepared_obj["B4_ID"],
#                 lower_left_latitude,
#                 lower_left_longitude,
#                 upper_right_latitude,
#                 upper_right_longitude
#             )
#             filename = f"{prepared_obj["date"]}_SR_B4"
#             output_tif_path = f"{PATH}/B4/{filename}.TIF"
#             if convert_png_url_to_geotiff(
#                 url,
#                 lower_left_latitude,
#                 lower_left_longitude,
#                 upper_right_latitude,
#                 upper_right_longitude,
#                 output_tif_path
#             ):
#                 downloaded_images["B4"][filename] = output_tif_path

#             url = self._format_url_image_by_id(
#                 prepared_obj["B5_ID"],
#                 lower_left_latitude,
#                 lower_left_longitude,
#                 upper_right_latitude,
#                 upper_right_longitude
#             )
#             filename = f"{prepared_obj["date"]}_SR_B5"
#             output_tif_path = f"{PATH}/B5/{filename}.TIF"

#             if convert_png_url_to_geotiff(
#                 url,
#                 lower_left_latitude,
#                 lower_left_longitude,
#                 upper_right_latitude,
#                 upper_right_longitude,
#                 output_tif_path
#             ):
#                 downloaded_images["B5"][filename] = output_tif_path

#             current_image_to_download = current_image_to_download + 1

#         print("Загрузка снимков завершена.")

#         return downloaded_images

#     def _get_content(self, url: str):
#         response = requests.get(
#             url=url
#         )

#         return response

#     def _format_query_params(self, query_params: dict) -> str:
#         query_string = "&".join([f"{key}={value}" for key, value in query_params.items()])

#         return query_string


#     def _format_url_avaliable_images(
#         self,
#         start_date: str,
#         end_date: str,
#         max_cloudiness: int,
#         lower_left_latitude: float,
#         lower_left_longitude: float,
#         upper_right_latitude: float,
#         upper_right_longitude: float,
#     ) -> str:
#         """Запрос:

#         ```
#         ```

#         Ответ:

#         ```
#         {
#             "DATA": [
#                 {
#                     "products": {
#                         "lc2_sr_b4": {
#                             "server": "nffc_hrsatdb",
#                             "id": "2407180630100232310107950"
#                         },
#                         "v_red_ch": {
#                             "product": "lc2_sr_b4",
#                             "server": "nffc_hrsatdb",
#                             "id": "2407180630100232310107950"
#                         },
#                         "lc2_sr_b5": {
#                             "server": "nffc_hrsatdb",
#                             "id": "2407180630100232310107960"
#                         },
#                         "v_nir_ch": {
#                             "server": "nffc_hrsatdb",
#                             "product": "lc2_sr_b5",
#                             "id": "2407180630100232310107960"
#                         },
#                         ...
#                     },
#                     "common": {
#                         "device": "OLI_TIRS_BOA",
#                         "dt": "2024-07-18 06:30:10",
#                         "daynight": "unknown",
#                         "satellite": "LANDSAT 8",
#                         "station": "USGS"
#                     }
#                 },
#                 ...
#             ],
#             "INFO": {
#                 "query": {
#                     "total_count": 8,
#                     "predicted_count": 0,
#                     "previous": null,
#                     "next": null,
#                     "last": 8,
#                     "count": 8,
#                     "first": 1
#                 },
#                 "servers": {
#                     "nffc_hrsatdb": {
#                         "is_local": 1,
#                         "url": "hrsatdb.nffc.aviales.ru",
#                         "service_host": "iki-blades",
#                         "center": "IKI",
#                         "accessibility": 1
#                     }
#                 },
#                 "stations": {
#                     "USGS": {
#                         "tz": "3"
#                     }
#                 },
#                 "user": "zzz",
#                 "project": "fap",
#                 "db_pkg_mode": "hrsat"
#             }
#         }
#         ```
#         """
#         query_params = {
#             "db_pkg_mode": DB_PKG_MODE,
#             "layers": LAYERS_UNISAT,
#             "request": REQUEST_GET_METADATA_IMAGES,

#             "BBOX": f"{lower_left_latitude},{lower_left_longitude},{upper_right_latitude},{upper_right_longitude}",
#             "srs": SRS_4326,
#             "max_cloudiness": max_cloudiness,

#             "width": 1024,
#             "height": 1024,

#             "dt_from": start_date,
#             "dt": end_date,

#             "limit": "150",

#             "satellites": SATELLITES_LANDSAT_8,
#             "stations": "",
#             "devices": "",
#             "products": "",

#             "ukey": self._ukey
#         }

#         formatted_query_params = self._format_query_params(query_params)

#         url = f"{self._base_url}{GET_METADATA_PL}?{formatted_query_params}"

#         return url

#     def _format_url_image_by_id(
#             self,
#             image_id: int,
#             lower_left_latitude: float,
#             lower_left_longitude: float,
#             upper_right_latitude: float,
#             upper_right_longitude: float,
#     ) -> str:
#         # Запроса изображения по id:
#         # http://sci-vega.ru/fap/toproxy/export/local/smiswms/get_map.pl?layers=unisat&db_pkg_mode=hrsat&FORMAT=png&WIDTH=862&HEIGHT=1255&BBOX=38.62716004621514,51.356,42.71267395378486,57.304167&EXCEPTIONS=xml&SERVICE=WMS&REQUEST=GetMap&transparent=1&unisat_uids=2102070811012323270071

#         query_params = {
#             "db_pkg_mode": DB_PKG_MODE,
#             "layers": LAYERS_UNISAT,
#             "request": REQUEST_GET_MAP,

#             "service": SERVICE_WMS,

#             "BBOX": f"{lower_left_latitude},{lower_left_longitude},{upper_right_latitude},{upper_right_longitude}",
#             "width": 1024,
#             "height": 1024,

#             "FORMAT": FORMAT_PNG,
#             "transparent": 1,

#             "EXCEPTIONS": EXCEPTION_XML,
#             "unisat_uids": image_id,

#             "ukey": self._ukey
#         }

#         formatted_query_params = self._format_query_params(query_params)

#         url = f"{self._base_url}{GET_MAP_PL}?{formatted_query_params}"

#         return url


# def main():
#     vega = VegaScience(secret.VEGA_USERNAME, secret.VEGA_PASSWORD, secret.VEGA_UKEY)

#     # image_id = 2407180630100232310107950

#     lower_left_latitude = 60.503652
#     lower_left_longitude = 31.478316
#     upper_right_latitude = 63.137372
#     upper_right_longitude = 36.927534

#     downloaded_images = vega._format_url_avaliable_images(
#         "2024-07-15",
#         "2024-07-18",
#         10,
#         lower_left_latitude,
#         lower_left_longitude,
#         upper_right_latitude,
#         upper_right_longitude
#     )

#     print(downloaded_images)

#     # url = vega._format_url_avaliable_images(
#     #     "2024-07-15",
#     #     "2024-07-20",
#     #     25,
#     #     lower_left_latitude,
#     #     lower_left_longitude,
#     #     upper_right_latitude,
#     #     upper_right_longitude
#     # )


#     # date = "2024-07-18 06:30:10"

#     # date = date.replace("-", "")
#     # date = date.replace(":", "")
#     # date = date.replace(" ", "_")

#     # print(date)

#     # response = vega._get_content(url)

#     # print(response.json())


#     # print(vega.get_image_by_id(2408070914502323270451))
#     # print(vega.get_image_by_id(2408070914500232310100451))
#     # print(vega.get_image_by_id(2408070914260232310100451))
#     # print(vega.get_image_by_id(2408050927142323270451))
#     # print(vega.get_image_by_id(2408050927140232310100451))
#     # print(vega.get_image_by_id(2408030939132323270451))

#     # ndvi
#     # print(vega.get_image_by_id(2408030939132323270131))
#     # v_vegetation
#     # print(vega.get_image_by_id(2408030939132323270131))

#     # ndvi
#     # print(vega.get_image_by_id(2408050926502323270131))
#     # v_vegetation
#     # print(vega.get_image_by_id(2408050926502323270451))

#     # print(vega.get_image_by_id(2408050926500232310100451))

#     # print(vega._format_url_avaliable_images())


# # main()

# # --------------------------------------------------
# #
# # Запрос на получение информации о доступных снимках
# # http://sci-vega.ru/fap/toproxy/export/local/smiswms/get_metadata.pl?REQUEST=GetMetadata&BBOX=38.62716004621514,51.356,42.71267395378486,57.304167&height=895&width=1553&dt=2021-02-08&db_pkg_mode=hrsat&dt_from=2021-02-05&limit=150&layers=unisat&satellites=LANDSAT 8&stations=&devices=&products=&max_cloudiness=10&srs=epsg:4326
# #
# # Объяснения ссылки:
# # http://sci-vega.ru/fap/toproxy/export/local/smiswms/get_metadata.pl? - базовая ссылка

# # db_pkg_mode=hrsat& - стандартное значение
# # layers=unisat& - стандартное значение
# # request=GetMetadata& - тип запроса
# #
# # BBOX=38.62716004621514,51.356,42.71267395378486,57.304167& - координаты области в проекции SRS, поддержана epsg нотация (epsg:4326 - значение по умолчанию)
# # width=1553& - высота зароса в пикселях
# # height=895& - ширина запроса в пикселях
# # srs=epsg:4326
# #
# # dt_from=2021-02-05& - дата начала интервала
# # dt=2021-02-08& - дата конца интервала
# # limit=150& - размер порции запроса
# #
# # идентификаторы спутников, приборов, станций
# # (из справочника, при отсутствии выдаются все доступные данные).
# # satellites=LANDSAT 8&
# # stations=&
# # devices=&
# # products=&
# #
# # max_cloudiness=10& - максимальная и минимальная облачность снимка в процентах, опциональные
# #
# # -------------------------------------------------------------------------------------------
# #
# # Запрос на получение снимка:
# # http://sci-vega.ru/fap/toproxy/export/local/smiswms/get_map.pl?layers=unisat&unisat_uids=2503070951511033504900361&service=wms&request=GetMap&BBOX=31.043,67.093,35.283,70.246&format=png&db_pkg_mode=hrsat&height=1024&width=1024&ukey=53616c7465645f5f4d5d9043e4ef4a6f7c915d382c1a2260fd9f01800279786afb18a03f7be9b321
# #
# # http://sci-vega.ru/fap/toproxy/export/local/smiswms/get_map.pl?
# #
# # db_pkg_mode=hrsat&
# # layers=unisat&
# # request=GetMap&
# # service=wms&
# #
# # BBOX=31.043,67.093,35.283,70.246&
# # width=1024&
# # height=1024&
# # format=png&
# #
# # unisat_uids=2503070951511033504900361&
# # ukey=53616c7465645f5f4d5d9043e4ef4a6f7c915d382c1a2260fd9f01800279786afb18a03f7be9b321
# #
# # -------------------------------------------------------------------------------------
# #
# # Запрос всех возможных значений параметров (справочников) - спутники, приборы, станции, продукты:
# # http://sci-vega.ru/fap/toproxy/export/local/smiswms/get_metadata.pl?db_pkg_mode=hrsat&layers=unisat&REQUEST=GetMetadataVariants
# #
# # http://sci-vega.ru/fap/toproxy/export/local/smiswms/get_metadata.pl?
# #
# # db_pkg_mode=hrsat&
# # layers=unisat&
# # request=GetMetadataVariants
# #
# # ----------------------------------
# #
# # Запрос изображения по id:
# # http://sci-vega.ru/fap/toproxy/export/local/smiswms/get_map.pl?layers=unisat&db_pkg_mode=hrsat&FORMAT=png&WIDTH=862&HEIGHT=1255&BBOX=38.62716004621514,51.356,42.71267395378486,57.304167&EXCEPTIONS=xml&SERVICE=WMS&REQUEST=GetMap&transparent=1&unisat_uids=2102070811012323270071
# #
# # http://sci-vega.ru/fap/toproxy/export/local/smiswms/get_map.pl?
# #
# # db_pkg_mode=hrsat&
# # layers=unisat&
# # request=GetMap&
# # service=wms&
# #
# # BBOX=38.62716004621514,51.356,42.71267395378486,57.304167&
# # width=862&
# # height=1255&
# #
# # FORMAT=png&
# # EXCEPTIONS=xml&
# # transparent=1&
# #
# # unisat_uids=2102070811012323270071
# #
# # ----------------------------------
# #
# # Запроса изображения по id:
# # http://sci-vega.ru/fap/toproxy/export/local/smiswms/get_map.pl?layers=unisat&db_pkg_mode=hrsat&FORMAT=png&WIDTH=862&HEIGHT=1255&BBOX=38.62716004621514,51.356,42.71267395378486,57.304167&EXCEPTIONS=xml&SERVICE=WMS&REQUEST=GetMap&transparent=1&unisat_uids=2102070811012323270071
# #
# # http://sci-vega.ru/fap/toproxy/export/local/smiswms/get_map.pl?

# # db_pkg_mode=hrsat&
# # layers=unisat&
# # request=GetMap&
# # service=wms&

# # BBOX=38.62716004621514,51.356,42.71267395378486,57.304167&
# # width=1024&
# # height=1024&

# # FORMAT=png&
# # EXCEPTIONS=xml&
# # transparent=1&
# #
# # source
# # unisat_uids=2102070811492323270600

# # def get_all_params(base_url, server, url_file, user, pwd, ukey):
# #     if not base_url or not user or not pwd or not ukey or not server or not url_file:
# #         print("Не указаны обязательные параметры!")
# #         return

# #     # Дополняем базовый URL данными
# #     base_url = f'{base_url}/{server}/local/smiswms/{url_file}?ukey={ukey}'

# #     # Запрос всех возможных значений параметров (справочников) - спутники, приборы, станции, продукты:
# #     # Переменные в запросе
# #     url=f'{base_url}&db_pkg_mode={db_pkg_mode}&layers={layers}&REQUEST={REQUEST}'

# #     # print(url)

# #     r = requests.get(url)
# #     if r.status_code != 200:
# #         r = 'Ошибка!'

# #     return r.json()


# # def main():
# #     # server = 'export'
# #     # url_file = 'get_metadata.pl'
# #     # json_data = get_all_params(base_url, server, url_file, user, pwd, ukey)

# #     # file_path = "/home/student/Projects/pythonProject/all_params.json"

# #     # json_data = get_json_from_file(file_path)

# #     # print(json_data)



# #     # write_json_to_file(json_data, file_path)

# #     # Демонстрация доступа к данным:
# #     # - все справочники
# #     # print_all_entries(json_data)


# #     # - отдельный прибор
# #     # device = "HYPERION"
# #     # get_specified_device(json_data, device)

# #     # - графическое изображение

# #     return

# # main()

# # # print(r.headers['content-type'])
# # # print(r.encoding)
# # # print(r.text)
# # # print(r.json())
# # # print(r.json()['stations_info']['PLANETA'])
# # # print(r.json()['products_info']['KMSS_NIR_GEOCORR'])

# # # server = 'nffc_hrsatdb'
# # # url_file= 'get_map.pl'
# # # print(get_zzz(base_url, server, url_file, user, pwd, ukey))




# # def print_all_entries(json_data):
# #     print("Справочники:")
# #     for key in json_data.keys():
# #         print(key)
# #     return

# # def get_specified_device(json_data, device):
# #     print(f"Информация по отдельному прибору \"{device}\":")
# #     print(json_data["devices_info"][device])

# #     return


# # def read_json_from_file(file_path):
# #     file = open(file_path, "r")
# #     content = file.read()
# #     json_data = json.loads(content)
# #     file.close()

# #     return json_data

# # def write_json_to_file(json_data, file_path):
# #     formatted_json = json.dumps(json_data, indent=4)

# #     with open(file_path, "w") as f:
# #         f.write(str(formatted_json))
# #         print(f"JSON успешно записан в файл по пути: '{file_path}'")

# #     return
