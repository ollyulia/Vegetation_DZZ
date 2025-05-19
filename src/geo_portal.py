import requests
import datetime

import secret

BASE_URL = "https://geo.mauniver.ru/"
RESOURCE_URL = f"{BASE_URL}api/resource/"
FILE_UPLOAD_URL = f"{BASE_URL}api/component/file_upload/"

SRS_3857 = 3857
SRS_4326 = 4326

UPLOADED_FILES_PATH = "uploaded_files_ids.txt"

class GeoPortal:
    def __init__(self, username: str, password: str, resource_group_id: int, web_map_id: int):
        self._auth = (username, password)
        self._resource_group_id = resource_group_id
        self._web_map_id = web_map_id

    def upload_snapshots(
            self,
            processed_images,
            start_date: str,
            end_date: str,
            lower_left_latitude: float,
            lower_left_longitude: float,
            upper_right_latitude: float,
            upper_right_longitude: float,
        ):
        '''
        Пример объекта `processed_images`:
        ```
        {
            "0.2": [
                "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_thresholds/20_X.tif",
                "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_thresholds/20_Y.tif"
            ]
            "0.3": [
                "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_thresholds/30_X.tif",
                "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_thresholds/30_Y.tif"
            ]
            "0.4": [
                "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_thresholds/40_X.tif",
                "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_thresholds/40_Y.tif"
            ]
        }
        ```
        '''
        print("\nНачало загрузки файлов на Геопортал")

        # Создание папки для текущего запроса на сервере
        current_group_name = f"[{start_date} {end_date}] ({lower_left_latitude}, {lower_left_longitude}, {upper_right_latitude}, {upper_right_longitude}) - {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"
        current_request_resource_group_id = self._create_group(self._resource_group_id, current_group_name)

        sorted_keys = sorted(processed_images.keys(), key=lambda x: float(x), reverse=True)

        current_file_number = 1
        total_files = len(sorted_keys)

        uploaded_images_data = []

        for threshold in sorted_keys:
            layers = []
            paths_to_files = processed_images[threshold]

            for path_to_file in paths_to_files:
                file_name_in_server = f"{threshold} порог | [{start_date} {end_date}] ({lower_left_latitude}, {lower_left_longitude}, {upper_right_latitude}, {upper_right_longitude}) - {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"
                raster_layer_name = file_name_in_server

                print(f"[{current_file_number}/{total_files}] Добавление на карту {path_to_file}")

                # Шаг 1: загрузка снимка на сервер
                uploaded_snapshot_file = self._upload_file_from_disk(path_to_file, file_name_in_server)

                if uploaded_snapshot_file is None:
                    print(f"Не удалось добавить файл на вебкарту: {path_to_file}\n")
                    total_files = total_files - 1
                    continue

                print(uploaded_snapshot_file)

                # Шаг 2: создание растрового слоя со снимком
                try:
                    raster_layer_id = self._upload_raster_layer_with_file(
                        uploaded_snapshot_file,
                        current_request_resource_group_id,
                        raster_layer_name,
                        SRS_3857
                    )
                except Exception as exception:
                    print(f"Не удалось добавить файл на вебкарту: {path_to_file}\n")
                    print("Удаляем созданные ресурсы на Геопортале...")
                    self._delete_file(uploaded_snapshot_file["id"])
                    total_files = total_files - 1
                    continue

                if raster_layer_id is None:
                    print(f"Не удалось добавить файл на вебкарту: {path_to_file}\n")
                    print("Удаляем созданные ресурсы на Геопортале...")
                    self._delete_file(uploaded_snapshot_file["id"])
                    total_files = total_files - 1
                    continue

                # Шаг 3: создаем в растровом слое стиль
                try:
                    raster_style_id = self._create_raster_style_in_raster_layer(
                        raster_layer_id,
                        f"Raster style for raster layer (ID = {raster_layer_id})"
                    )
                except Exception as exception:
                    print(f"Не удалось добавить файл на вебкарту: {path_to_file}\n")
                    print("Удаляем созданные ресурсы на Геопортале...")
                    self._delete_file(uploaded_snapshot_file["id"])
                    self._delete_resource(raster_layer_id)
                    total_files = total_files - 1
                    continue

                if raster_style_id is None:
                    print(f"Не удалось добавить файл на вебкарту: {path_to_file}\n")
                    print("Удаляем созданные ресурсы на Геопортале...")
                    self._delete_file(uploaded_snapshot_file["id"])
                    self._delete_resource(raster_layer_id)
                    total_files = total_files - 1
                    continue

                print(f"Успешная загрузка на Геопортал снимка: {path_to_file}\n")

                # Добавляем инфу об raster_layer_id, raster_layer_style_id, raster_layer_name
                layer = {
                    "item_type": "layer",
                    "display_name": raster_layer_name,
                    "layer_enabled": True,
                    "layer_identifiable": True,
                    "layer_transparency": None,
                    "layer_style_id": raster_style_id,
                    "style_parent_id": raster_layer_id,
                    "layer_min_scale_denom": None,
                    "layer_max_scale_denom": None,
                    "layer_adapter": "image",
                    "draw_order_position": 1,
                    "legend_symbols": None,
                }

                layers.append(layer)
                current_file_number = current_file_number + 1

            # Создаем новую группу
            new_group = {
                "item_type": "group",
                "display_name": f"{threshold}",
                "children": layers,  # Здесь будут находиться слои
                "group_expanded": False,  # Группа будет развернута по умолчанию
                "draw_order_position": 1
            }

            uploaded_images_data.append(new_group)

        # Шаг 4: создаем и добавляем в группу на вебкарте все загруженные снимки
        try:
            result = self._create_layer_group_in_webmap(
            self._web_map_id,
            current_group_name,
            uploaded_images_data
        )
        except Exception as exception:
            print("Удаляем созданные ресурсы на Геопортале...")
            for image_data in uploaded_images_data:
                print("Удаляем созданные ресурсы на Геопортале...")
                self._delete_file(image_data["uploaded_snapshot_file"])
                self._delete_resource(image_data["raster_layer_id"])
                self._delete_resource(image_data["raster_style_id"])
                self._delete_resource(current_request_resource_group_id)

            raise exception

        if not result:
            print("Удаляем созданные ресурсы на Геопортале...")
            for image_data in uploaded_images_data:
                print("Удаляем созданные ресурсы на Геопортале...")
                self._delete_file(image_data["uploaded_snapshot_file"])
                self._delete_resource(image_data["raster_layer_id"])
                self._delete_resource(image_data["raster_style_id"])
                self._delete_resource(current_request_resource_group_id)

            print(f"Не удалось добавить снимки на вебкарту\n")
            return

        print("Все снимки опубликованы\n")

        return

    def _get_content(self, url: str):
        response = requests.get(
            url=url,
            auth=self._auth
        )

        return response

    def _put_content(self, url: str, content):
        response = requests.put(
            url=url,
            json=content,
            auth=self._auth
        )

        return response

    def _post_json(
        self,
        url: str,
        json
    ):
        response = requests.post(
            url=url,
            json=json,
            auth=self._auth
        )

        return response

    def _delete_resource(self, resource_id: int):
        delete_resource_url = f"{RESOURCE_URL}{resource_id}"
        response = requests.delete(delete_resource_url, auth=self._auth)

        if response.status_code == 200:
            print("    Ресурс успешно удалён.")
        else:
            print(f"Ошибка {response.status_code} при удалении ресурса: {response.text}")

    def _post_files(self, url: str, files):
        response = requests.post(
            url=url,
            files=files,
            auth=self._auth
        )

        return response

    def _delete_file(self, file_id: str):
        delete_file_url = f"{FILE_UPLOAD_URL}{file_id}"
        response = requests.delete(delete_file_url, auth=self._auth)

        if response.status_code == 204:
            print("    Файл успешно удалён")
        else:
            print(f"Ошибка {response.status_code} при удалении файла: {response.text}")

    # Форма значения по ключу upload_meta у загруженного файла имеет вид:
    # {
    #     "id": "0195a94109009c45abe81a84debf08a5",
    #     "mime_type": "image/tiff",
    #     "name": "output.tif",
    #     "size": 3149175
    # }
    def _upload_file_from_disk(self, file_path: str, file_name_in_server: str):
        with open(file_path, "rb") as file_content:
            files = {
                #                   FileName,  FileContent, FileContentType
                "file": (file_name_in_server, file_content, "image/tiff")
            }
            print(f"    Отправка файла '{file_path}' ...")
            response = self._post_files(FILE_UPLOAD_URL, files)

        if response.status_code != 200:
            print(f"Ошибка {response.status_code} при загрузке файла '{file_path}': {response.text}")
            return None

        upload = response.json()["upload_meta"][0]
        upload_id = upload["id"]
        print(f"    Файл загружен. ID загруженного файла: {upload_id}")

        return upload

    def _upload_raster_layer_with_file(
        self,
        uploaded_file_metadata,
        resouce_group_parent_id: int,
        display_name: str,
        srs_id: int
    ) -> int:
        create_data = {
            "resource": {
                "cls": "raster_layer",
                "display_name": display_name,
                "parent": {"id": resouce_group_parent_id}
            },
            "raster_layer": {
                "source": {
                    "id": uploaded_file_metadata["id"],
                    "mime_type": uploaded_file_metadata["mime_type"],
                    "size": uploaded_file_metadata["size"]
                },
                "srs": {"id": srs_id}
            }
        }

        print(f"    Создание растрового слоя в группе с id = {resouce_group_parent_id}")
        response = self._post_json(RESOURCE_URL, create_data)

        if response.status_code != 201:
            print(f"Ошибка {response.status_code} при создании растрового слоя: {response.text}")
            return None
        response = response.json()
        raster_layer_id = response["id"]
        print(f"    Растровый слой успешно создан. ID слоя: {raster_layer_id}")
        return raster_layer_id

    def _create_transparent_style_in_layer(
        self,
        uploaded_style_file,
        raster_layer_id: int,
    ):
        create_style_data = {
            "qgis_raster_style": {
                "file_upload": {
                    "id": uploaded_style_file["id"],
                    "mime_type": uploaded_style_file["mime_type"],
                    "size": uploaded_style_file["size"],
                }
            },
            "res_meta": {
                "items": {
                }
            },
            "resource": {
                "cls": "qgis_raster_style",
                "display_name": "QGIS transparent style",
                "parent": {
                    "id": raster_layer_id
                }
            }
        }

        response = self._post_json(RESOURCE_URL, create_style_data)

        if response.status_code != 201:
            print(f"Ошибка {response.status_code} при создании стиля: {response.text}")
            return None
        response = response.json()
        style_id = response["id"]
        print(f"Стиль успешно создан. ID стиля: {style_id}")
        return style_id

    def _create_raster_style_in_raster_layer(
        self,
        raster_layer_id: int,
        display_name: str
    ):
        create_style_data = {
            "resource": {
                "cls": "raster_style",
                "display_name": display_name,
                "parent": {"id": raster_layer_id}
            }
        }

        response = self._post_json(RESOURCE_URL, create_style_data)

        if response.status_code != 201:
            print(f"Ошибка {response.status_code} при создании стиля: {response.text}")
            return None
        response = response.json()
        style_id = response["id"]
        print(f"    Стиль успешно создан. ID стиля: {style_id}")
        return style_id


    def _upload_new_layer_webmap(
        self,
        webmap_id: int,
        raster_layer_id: int,
        raster_layer_style_id: int,
        raster_layer_name: str
    ):
        # Шаг 1: Получение текущей конфигурации веб-карты
        get_webmap_url = f"{RESOURCE_URL}{webmap_id}"
        response = self._get_content(get_webmap_url)

        if response.status_code != 200:
            print(f"Ошибка {response.status_code} при получении веб-карты: {response.text}")
            return False

        webmap_config = response.json()

        # Шаг 2: Добавление нового слоя в конфигурацию
        new_layer = {
            "item_type": "layer",
            "display_name": raster_layer_name,
            "layer_enabled": True,
            "layer_identifiable": True,
            "layer_transparency": None,
            "layer_style_id": raster_layer_style_id,
            "style_parent_id": raster_layer_id,
            "layer_min_scale_denom": None,
            "layer_max_scale_denom": None,
            "layer_adapter": "image",
            "draw_order_position": 1,
            "legend_symbols": None,
        }

        # Шаг 3: Добавляем новый слой в массив layers
        layers = webmap_config["webmap"]["root_item"]["children"]
        layers.append(new_layer)

        payload = {"webmap":{"root_item":{"item_type":"root", "children": layers } }}

        response = self._put_content(get_webmap_url, payload)

        if response.status_code != 200:
            print(f"Ошибка {response.status_code} при обновлении веб-карты: {response.text}")
            return False

        print(f"    Слой успешно добавлен на веб-карту.")

        return True

    def _create_group(
        self,
        resouce_group_parent_id: int,
        display_name: str,
    ):
        create_group_data = {
            "resource": {
                "cls": "resource_group",
                "parent": {
                    "id": resouce_group_parent_id
                },
                "display_name": display_name,
            }
        }

        response = self._post_json(RESOURCE_URL, create_group_data)

        if response.status_code != 201:
            print(f"Ошибка {response.status_code} при создании группы: {response.text}")
            return None

        response = response.json()
        # response = {"id": 945, "parent": {"id": 714}}

        group_id = response["id"]

        return group_id

    def _create_layer_group_in_webmap(
            self,
            webmap_id: int,
            group_name: str,
            layers_data,
        ):
            # Получаем текущую конфигурацию веб-карты
            get_webmap_url = f"{RESOURCE_URL}{webmap_id}"
            response = self._get_content(get_webmap_url)

            if response.status_code != 200:
                print(f"Ошибка {response.status_code} при получении веб-карты: {response.text}")
                return False

            webmap_config = response.json()

            # Создаем новую группу
            new_group = {
                "item_type": "group",
                "display_name": group_name,
                "children": layers_data,  # Здесь будут находиться слои
                "group_expanded": True,  # Группа будет развернута по умолчанию
                "draw_order_position": 1
            }

            # Добавляем новую группу в массив layers
            layers = webmap_config["webmap"]["root_item"]["children"]
            layers.append(new_group)

            payload = {"webmap": {"root_item": {"item_type": "root", "children": layers}}}

            response = self._put_content(get_webmap_url, payload)

            if response.status_code != 200:
                print(f"Ошибка {response.status_code} при обновлении веб-карты: {response.text}")
                return False

            print(f"    Группа '{group_name}' успешно создана на веб-карте.")
            return True


    def _create_raster_layer(self):
        create_data = {
            "resource": {
                "cls": "raster_layer",
                "display_name": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "parent": {"id": self._resource_group_id}
            },
            "raster_layer": {
                "srs": {"id": SRS_3857},
                "source": {'id': '0196e46af5405ca5ffb68e16ac2d87fa', 'size': 40751989, 'name': '0.3 порог | [2024-08-20 2024-08-22] (66.213585, 27.771668, 69.549744, 41.416688) - 2025-05-18 20:22:10', 'mime_type': 'image/tiff'}
            }
        }

        response = self._post_json(RESOURCE_URL, create_data)

        if response.status_code != 201:
            print(f"Ошибка {response.status_code} при создании растрового слоя: {response.text}")
            try:
                print(response.json())
            except Exception as e:
                print(e)
            return None
        response = response.json()
        raster_layer_id = response["id"]
        print(f"    Растровый слой успешно создан. ID слоя: {raster_layer_id}")
        print(response)
        return raster_layer_id

    def _get_raster_layer(
            self,
            raster_layer: int,
        ):
            get_raster_layer = f"{RESOURCE_URL}{raster_layer}"
            response = self._get_content(get_raster_layer)

            if response.status_code != 200:
                print(f"Ошибка {response.status_code} при получении веб-карты: {response.text}")
                return False

            raster_layer_config = response.json()

            print(raster_layer_config)


def test_group_creation():
    geo = GeoPortal(
        secret.GEO_PORTAL_USERNAME,
        secret.GEO_PORTAL_PASSWORD,
        secret.GEO_PORTAL_RESOURCE_GROUP_ID,
        secret.GEO_PORTAL_WEB_MAP_ID
    )

    # x = geo._upload_file_from_disk(
    #     "images/2025-05-18/2024-08-20_2024-08-22_66.213585:27.771668_69.549744:27.771668/ndvi_combined/combined_threshold_35.tif",
    #     "dsadqeqrwerwer"
    # )

    # print(x)

    id = geo._create_raster_layer()
    geo._get_raster_layer(id)

    # print(geo._upload_raster_layer_with_file({}, 993, "dasdqeqwr", SRS_3857))
    # Создание растрового слоя в группе с id = 987
    # {'id': '0196e46af5405ca5ffb68e16ac2d87fa', 'size': 40751989, 'name': '0.3 порог | [2024-08-20 2024-08-22] (66.213585, 27.771668, 69.549744, 41.416688) - 2025-05-18 20:22:10', 'mime_type': 'image/tiff'}



    # print(geo._create_group(geo._resource_group_id, "Test name for group"))
    # geo._create_layer_group_in_webmap(geo._web_map_id, "Test name for group 2")
    # processes_images = {
    #     "1_combined_threshold_20.tif": "images/test/ndvi_combined/1_combined_threshold_20.tif",
    #     "1_combined_threshold_30.tif": "images/test/ndvi_combined/1_combined_threshold_30.tif",
    #     "1_combined_threshold_35.tif": "images/test/ndvi_combined/1_combined_threshold_35.tif",
    # }

    # geo.upload_snapshots(processes_images)

# test_group_creation()

# {
#     'item_type': 'group',
#     'display_name': 'Test name for group',
#     'group_expanded': True,
#     'group_exclusive': False,
#     'children': [
#         {
#             'item_type': 'layer',
#             'display_name': 'LC08_L2SP_188012_20240821_20240830_02_T1_ndvi_colored',
#             'layer_enabled': True,
#             'layer_identifiable': True,
#             'layer_transparency': None,
#             'layer_style_id': 874,
#             'style_parent_id': 873,
#             'layer_min_scale_denom': None,
#             'layer_max_scale_denom': None,
#             'layer_adapter': 'image',
#             'draw_order_position': 1,
#             'legend_symbols': None
#         }
#     ]
# }
