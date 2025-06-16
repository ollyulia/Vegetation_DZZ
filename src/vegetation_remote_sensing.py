import json
import os
import traceback

from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw

from src import earth_explorer
from src import geo_portal
from src import ndvi
from src import secret

NDVI_THRESHOLDS = {
    0.2: (107, 195, 106),
    0.3: (96, 182, 96),
    0.35: (85, 168, 84),
}

class VegetationRemoteSensing:
    def __init__(
            self,
            earth_explorer_username=None,
            earth_explorer_token=None,
            geo_portal_username=None,
            geo_portal_password=None,
            geo_portal_resource_group_id=None,
            geo_portal_web_map_id=None,
        ):
        params_provided = all([
            earth_explorer_username is not None,
            earth_explorer_token is not None,
            geo_portal_username is not None,
            geo_portal_password is not None,
            geo_portal_resource_group_id is not None,
            geo_portal_web_map_id is not None
        ])

        secrets_available = secret.check()

        if not params_provided and not secrets_available:
            print("Пожалуйста, укажите все необходимые данные для авторизации либо в параметрах, либо в файле secret.py")
            return None

        ee_user = earth_explorer_username if earth_explorer_username is not None else secret.EARTH_EXPLORER_USERNAME
        ee_token = earth_explorer_token if earth_explorer_token is not None else secret.EARTH_EXPLORER_TOKEN
        gp_user = geo_portal_username if geo_portal_username is not None else secret.GEO_PORTAL_USERNAME
        gp_pass = geo_portal_password if geo_portal_password is not None else secret.GEO_PORTAL_PASSWORD
        gp_res = geo_portal_resource_group_id if geo_portal_resource_group_id is not None else secret.GEO_PORTAL_RESOURCE_GROUP_ID
        gp_map = geo_portal_web_map_id if geo_portal_web_map_id is not None else secret.GEO_PORTAL_WEB_MAP_ID

        self._earth_explorer = earth_explorer.EarthExplorer(ee_user, ee_token)
        self._ndvi = ndvi.Ndvi()
        self._geo_portal = geo_portal.GeoPortal(gp_user, gp_pass, gp_res, gp_map)
        self._is_working = False

    def add_vegetation_to_the_webmap_from_earth_explorer(
        self,
        start_date: str,
        end_date: str,
        lower_left_latitude: float,
        lower_left_longitude: float,
        upper_right_latitude: float,
        upper_right_longitude: float,
        min_cloudiness: int,
        max_cloudiness: int,
    ):
        """Функция приложения по добавлению растительности по спутниковым снимкам с EarthExplorer.
        По указанным дате и координатам:
        - обращается к EarthExplorer
        - скачивает красный и ближний инфракрасный каналы подходящих снимков
        - рассчитывает индекс NDVI и сохраняет в виде карты с зеленой растительностью
        - создает необходимые ресурсы (слои, стили и т.д.) на Геопортале и загружает карту растительности

        В случае ошибок в промежуточных этапах (рассчет NDVI и загрузка на Геопортал), сохраняет информацию в файлах в папке `recovery_data`
        """
        if self._is_working:
            message = "Программа уже работает. Пожалуйста, подождите завершения работы скрипта."
            print(message)
            return message

        self._is_working = True

        if not self._validate_date(start_date):
            message = "Неверный формат начальной даты. Пожалуйста, введите дату в формате ГГГГ-ММ-ДД"
            print(message)

            return message

        if not self._validate_date(start_date):
            message = "Неверный формат конечной даты. Пожалуйста, введите дату в формате ГГГГ-ММ-ДД"
            print(message)

            return message

        # Проверка, что начальная дата не позже конечной
        if datetime.strptime(start_date, "%Y-%m-%d") > datetime.strptime(end_date, "%Y-%m-%d"):
            message = "Ошибка: Начальная дата не может быть позже конечной"
            print(message)

            return message

        # latitude широта
        # lower_left_latitude = 67.111400
        # upper_right_latitude = 67.971667
        if lower_left_latitude >= upper_right_latitude:
            message = f"Ошибка: Неправильно задана широта: {lower_left_latitude} не должно быть больше или равно {upper_right_latitude}"
            print(message)

            return message

        # longitude долгота
        # lower_left_longitude = 35.672218
        # upper_right_longitude = 39.264748
        if lower_left_longitude >= upper_right_longitude:
            message = f"Ошибка: Неправильно задана долгота: {lower_left_longitude} не должно быть больше или равно {upper_right_longitude}"
            print(message)

            return message

        print("Начало работы скрипта по добавлению растительности на вебкарту")

        # Путь для загрузки файлов
        strftime = datetime.now().strftime("%Y-%m-%d")
        PATH = f"images/{strftime}/{start_date}_{end_date}_{lower_left_latitude}:{lower_left_longitude}_{upper_right_latitude}:{upper_right_longitude}"
        Path(PATH).mkdir(parents=True, exist_ok=True)

        # скачивание красного и ближнего инфракрасного каналов подходящих снимков
        downloaded_images_data = self._earth_explorer.download_images_by_coordinates(
            start_date,
            end_date,
            lower_left_latitude,
            lower_left_longitude,
            upper_right_latitude,
            upper_right_longitude,
            min_cloudiness,
            max_cloudiness,
            PATH,
        )
        # Пример объекта downloaded_images:
        # {
        #     "B4": {
        #         "A_SR_B4.TIF": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/B4/A_SR_B4.TIF",
        #         "B_SR_B4.TIF": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/B4/B_SR_B4.TIF",
        #     },
        #     "B5": {
        #         "A_SR_B5.TIF": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/B5/A_SR_B5.TIF",
        #         "B_SR_B5.TIF": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/B5/B_SR_B5.TIF",
        #     },
        #     "other": {
        #         "some_filename.extension": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/other/some_filename.extension"
        #     }
        # }

        if len(downloaded_images_data["B4"]) == 0:
            message = "По указанным данным не найдено снимков. Попробуйте изменить дату."
            print(message)

            return message

        try:
            # рассчет NDVI
            processed_images = self._ndvi.calculate(downloaded_images_data, PATH, NDVI_THRESHOLDS)
            # Пример processed_images: {
            #     "0.2": [
            #         "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_thresholds/20_X.tif",
            #         "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_thresholds/20_Y.tif"
            #     ]
            #     "0.3": [
            #         "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_thresholds/30_X.tif",
            #         "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_thresholds/30_Y.tif"
            #     ]
            #     "0.4": [
            #         "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_thresholds/40_X.tif",
            #         "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_thresholds/40_Y.tif"
            #     ]
            # }
        except Exception as exception:
            message = f"Случилась ошибка: {exception}\n{traceback.format_exc()}"
            print(message)

            error_dir = f"recovery_data"
            os.makedirs(error_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{error_dir}/{timestamp}_downloaded_images.json"

            with open(filename, "w") as file:
                json.dump(processed_images, file, indent=4)

            print(f"Информация об скачанных снимках сохранена в {filename}")

            return message

        try:
            # загрузка на Геопортал
            self._geo_portal.upload_snapshots(
                processed_images,
                start_date,
                end_date,
                lower_left_latitude,
                lower_left_longitude,
                upper_right_latitude,
                upper_right_longitude,
            )
        except Exception as exception:
            message = f"Случилась ошибка: {exception}\n{traceback.format_exc()}"
            print(message)

            error_dir = f"recovery_data"
            os.makedirs(error_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{error_dir}/{timestamp}_processed_images.json"

            with open(filename, "w") as file:
                json.dump(processed_images, file, indent=4)

            print(f"Информация об обработанных файлах сохранена в {filename}")

            return message

        message = "Растительность успешно добавлена"
        print(message)

        return message

    def _validate_date(self, date_str):
        """Проверяет, соответствует ли строка формату ГГГГ-ММ-ДД."""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def _create_ndvi_scale(self):
        width, height = 600, 100
        img = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        # Рисуем градиент
        for i in range(width):
            pos = i / width
            if pos < 0.2:
                color = (107, 195, 106)
            elif pos < 0.3:
                color = (96, 182, 96)
            else:
                color = (85, 168, 84)
            draw.line([(i, 0), (i, height-30)], fill=color)

        # Добавляем подписи
        for threshold, color in NDVI_THRESHOLDS.items():
            x = int(threshold * width)
            draw.line([(x, height-30), (x, height-20)], fill=(0, 0, 0))
            draw.text((x-10, height-20), f"{threshold}", fill=(0, 0, 0))

        os.makedirs("static/ndvi_scales", exist_ok=True)
        image_path = f"static/ndvi_scales/ndvi_scale_{len(os.listdir('static/ndvi_scales'))}.png"
        img.save(image_path)
        return image_path

    def continue_process_images(
            self,
            downloaded_images_path,
            path,
            lower_left_latitude,
            lower_left_longitude,
            upper_right_latitude,
            upper_right_longitude,
            start_date,
            end_date,
        ):
        """Функция для продолжения работы скрипта, если во время обработки снимков произошла ошибка.
        Ожидается, что в указанном пути существует файл `{filename}.json` со следующей структурой:
        ```
        {
            "B4": {
                "{filename}_SR_B4.TIF": "images/downloaded/B4/{filename}_SR_B4.TIF",
                "{filename}_SR_B4.TIF": "images/downloaded/B4/{filename}_SR_B4.TIF",
            },
            "B5": {
                "{filename}_SR_B5.TIF": "images/downloaded/B5/{filename}_SR_B5.TIF",
                "{filename}_SR_B5.TIF": "images/downloaded/B5/{filename}_SR_B5.TIF",
            },
            "other": {
                "{filename}.{extension}": "images/downloaded/other/{filename}.{extension}"
            }
        }
        ```

        :param downloaded_images_path: Путь к `json` файлу
        :type downloaded_images_path: str
        """
        try:
            with open(downloaded_images_path, "r") as file:
                downloaded_images = json.load(file)
        except FileNotFoundError:
            print(f"Файл не найден: {downloaded_images_path}")
        except json.JSONDecodeError as json_err:
            print(f"Ошибка: файл не является валидным JSON: {json_err}")
        except Exception as e:
            print("Неизвестная ошибка: ", e)

        try:
            processed_images = self._ndvi.calculate(downloaded_images, path)
        except Exception as exception:
            print(f"Случилась ошибка: {exception}\n{traceback.format_exc()}")

            return

        try:
            self._geo_portal.upload_snapshots(
                processed_images,
                start_date,
                end_date,
                lower_left_latitude,
                lower_left_longitude,
                upper_right_latitude,
                upper_right_longitude,
            )
        except Exception as exception:
            print(f"Случилась ошибка: {exception}\n{traceback.format_exc()}")

            error_dir = f"recovery_data"
            os.makedirs(error_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{error_dir}/{timestamp}_processed_images.json"

            with open(filename, "w") as file:
                json.dump(processed_images, file, indent=4)

            print(f"Информация об обработанных файлах сохранена в {filename}")

            return

        print("Растительность успешно добавлена")

        return

    def continue_upload_to_geoportal(
            self,
            processed_images_path,
            start_date,
            end_date,
            lower_left_latitude,
            lower_left_longitude,
            upper_right_latitude,
            upper_right_longitude,
        ):
        """Функция для продолжения работы скрипта, если во время отправки снимков на Геопортал произошла ошибка.
        Ожидается, что в указанном пути существует файл `{filename}.json` со следующей структурой:
        ```
        {
            "{filename}.tif": "images/ndvi_output/{filename}.tif",
            "{filename}.tif": "images/ndvi_output/{filename}.tif",
            "{filename}.tif": "images/ndvi_output/{filename}.tif"
        }
        ```

        :param processed_images_path: Путь к `json` файлу
        :type processed_images_path: str
        """
        try:
            with open(processed_images_path, "r") as file:
                processed_images = json.load(file)
        except FileNotFoundError:
            print(f"Файл не найден: {processed_images_path}")
        except json.JSONDecodeError as json_err:
            print(f"Ошибка: файл не является валидным JSON: {json_err}")
        except Exception as e:
            print("Неизвестная ошибка: ", e)

        try:
            self._geo_portal.upload_snapshots(
                processed_images,
                start_date,
                end_date,
                lower_left_latitude,
                lower_left_longitude,
                upper_right_latitude,
                upper_right_longitude,
            )
        except Exception as exception:
            print(f"Случилась ошибка: {exception}\n{traceback.format_exc()}")

            return

        print("Растительность успешно добавлена")
