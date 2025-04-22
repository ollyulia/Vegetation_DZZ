import requests

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

    def upload_snapshots(self, processed_images):
        print("\nНачало загрузки файлов на Геопортал")

        # os.makedirs(os.path.dirname(UPLOADED_FILES_PATH), exist_ok=True)

        # Пример объекта processed_images:
        # {
        #     "LC08_L2SP_183012_20240802_20240808_02_T2_ndvi_colored.tif": "images/ndvi_output/LC08_L2SP_183012_20240802_20240808_02_T2_ndvi_colored.tif",
        #     "LC08_L2SP_183013_20240802_20240808_02_T1_ndvi_colored.tif": "images/ndvi_output/LC08_L2SP_183013_20240802_20240808_02_T1_ndvi_colored.tif",
        #     "LC09_L2SP_184012_20240801_20240802_02_T1_ndvi_colored.tif": "images/ndvi_output/LC09_L2SP_184012_20240801_20240802_02_T1_ndvi_colored.tif",
        #     "LC09_L2SP_184013_20240801_20240802_02_T2_ndvi_colored.tif": "images/ndvi_output/LC09_L2SP_184013_20240801_20240802_02_T2_ndvi_colored.tif",
        # }

        total_files = len(processed_images)
        current_file_number = 1

        for processed_image_name, processed_image_path in processed_images.items():
            file_name_in_server = processed_image_name
            path_to_file = processed_image_path
            raster_layer_name = file_name_in_server.split(".")[0]

            print(f"[{current_file_number}/{total_files}] Добавление на карту {file_name_in_server}")

            result = self._upload_snapshot(
                path_to_file,
                file_name_in_server,
                self._resource_group_id,
                raster_layer_name,
                SRS_3857,
                self._web_map_id
            )

            if result:
                print(f"Успешное добавление файла на вебкарту: {file_name_in_server}\n")
            else:
                print(f"Не удалось добавить файл на вебкарту: {path_to_file}\n")

            current_file_number = current_file_number + 1

        print("Все файлы опубликованы\n")

        return

    def _upload_snapshot(
        self,
        path_to_file: str,
        file_name_in_server: str,
        resouce_group_parent_id: int,
        raster_layer_name: str,
        srs_id: int,
        webmap_id: int
    ):
        # Шаг 1: загружаем на Геопортал снимок
        uploaded_snapshot_file = self._upload_file_from_disk(path_to_file, file_name_in_server)

        if uploaded_snapshot_file is None:
            return False

        # with open(UPLOADED_FILES_PATH, "a") as f:
        #     f.write(f"{uploaded_snapshot_file["id"]}\n")

        # Шаг 2: создаем в Геопортал в папке пользователя растровый слой и указываем в нем ID снимка для отображения
        try:
            raster_layer_id = self._upload_raster_layer_with_file(
                uploaded_snapshot_file,
                resouce_group_parent_id,
                raster_layer_name,
                srs_id
            )
        except Exception as exception:
            print("Удаляем созданные ресурсы на Геопортале...")
            self._delete_file(uploaded_snapshot_file["id"])

            raise exception

        if raster_layer_id is None:
            print("Удаляем созданные ресурсы на Геопортале...")
            self._delete_file(uploaded_snapshot_file["id"])
            return False

        # загружаем в Геопортал файл стиля
        # uploaded_style_file = self._upload_file_from_disk("transparent_style.qml", "transparent_style.qml")
        # создаем в растровом слое стиль и указываем в нем ID ранее созданного стиля
        # style_id = self._create_transparent_style_in_layer(uploaded_style_file, raster_layer_id)

        # Шаг 3: создаем в растровом слое стиль
        try:
            style_id = self._create_raster_style_in_raster_layer(
                raster_layer_id,
                f"Raster style for raster layer (ID = {raster_layer_id})"
            )
        except Exception as exception:
            print("Удаляем созданные ресурсы на Геопортале...")
            self._delete_file(uploaded_snapshot_file["id"])
            self._delete_resource(raster_layer_id)

            raise exception

        # with open(UPLOADED_FILES_PATH, "a") as f:
        #     f.write(f"{uploaded_style_file["id"]}\n")

        if style_id is None:
            print("Удаляем созданные ресурсы на Геопортале...")
            self._delete_file(uploaded_snapshot_file["id"])
            self._delete_resource(raster_layer_id)

            return False

        # Шаг 4: добавляем новый слой на вебкарту с ID ранее созданного растрового слоя
        try:
            result = self._upload_new_layer_webmap(webmap_id, raster_layer_id, style_id, raster_layer_name)
        except Exception as exception:
            print("Удаляем созданные ресурсы на Геопортале...")
            self._delete_file(uploaded_snapshot_file["id"])
            self._delete_resource(raster_layer_id)
            self._delete_resource(style_id)

            raise exception

        if not result:
            print("Удаляем созданные ресурсы на Геопортале...")
            self._delete_file(uploaded_snapshot_file["id"])
            self._delete_resource(raster_layer_id)
            self._delete_resource(style_id)

            return False

        return True

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
        parent_id: int,
        display_name: str,
        srs_id: int
    ) -> int:
        create_data = {
            "resource": {
                "cls": "raster_layer",
                "display_name": display_name,
                "parent": {"id": parent_id}
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
