import os
import json
import traceback
from datetime import datetime

from src import geo_portal
from src import earth_explorer
from src import ndvi
from src import secret

class VegetationRemoteSensing:
    def __init__(self):
        all_set = secret.check()
        if not all_set:
            print("Пожалуйста, укажите все необходимые данные для авторизации в файле secret.py")
            return None

        self._earth_explorer = earth_explorer.EarthExplorer(
            secret.EARTH_EXPLORER_USERNAME,
            secret.EARTH_EXPLORER_TOKEN
        )
        self._ndvi = ndvi.Ndvi()
        self._geo_portal = geo_portal.GeoPortal(
            secret.GEO_PORTAL_USERNAME,
            secret.GEO_PORTAL_PASSWORD,
            secret.GEO_PORTAL_RESOURCE_GROUP_ID,
            secret.GEO_PORTAL_WEB_MAP_ID
        )

    def add_vegetation_to_the_webmap(
        self,
        start_date: str,
        end_date: str,
        lower_left_latitude: float,
        lower_left_longitude: float,
        upper_right_latitude: float,
        upper_right_longitude: float
    ):
        """Главная функция приложения.
        По указанным дате и координатам:
        - обращается к EarthExplorer
        - скачивает красный и ближний инфракрасный каналы подходящих снимков
        - рассчитывает индекс NDVI и сохраняет в виде карты с зеленой растительностью
        - создает необходимые ресурсы (слои, стили и т.д.) на Геопортале и загружает карту растительности

        В случае ошибок в промежуточных этапах (рассчет NDVI и загрузка на Геопортал), сохраняет информацию в файлах в папке `recovery_data`
        """
        if not self._validate_date(start_date):
            print("Неверный формат начальной даты. Пожалуйста, введите дату в формате ГГГГ-ММ-ДД")
            return

        if not self._validate_date(start_date):
            print("Неверный формат конечной даты. Пожалуйста, введите дату в формате ГГГГ-ММ-ДД")
            return

        # Проверка, что начальная дата не позже конечной
        if datetime.strptime(start_date, "%Y-%m-%d") > datetime.strptime(end_date, "%Y-%m-%d"):
            print("Ошибка: Начальная дата не может быть позже конечной")
            return

        # latitude широта
        # lower_left_latitude = 67.111400
        # upper_right_latitude = 67.971667
        if lower_left_latitude >= upper_right_latitude:
            print(f"Ошибка: Неправильно задана широта: {lower_left_latitude} не должно быть больше или равно {upper_right_latitude}")
            return

        # longitude долгота
        # lower_left_longitude = 35.672218
        # upper_right_longitude = 39.264748
        if lower_left_longitude >= upper_right_longitude:
            print(f"Ошибка: Неправильно задана долгота: {lower_left_longitude} не должно быть больше или равно {upper_right_longitude}")
            return

        print("Начало работы скрипта по добавлению растительности на вебкарту")

        # скачивание красного и ближнего инфракрасного каналов подходящих снимков
        downloaded_images = self._earth_explorer.download_images_by_coordinates(
            start_date,
            end_date,
            lower_left_latitude,
            lower_left_longitude,
            upper_right_latitude,
            upper_right_longitude
        )
        # Пример объекта downloaded_images:
        # {
        #     "B4": {
        #         "LC08_L2SP_181013_20240804_20240808_02_T1_SR_B4.TIF": "images/downloaded/B4/LC08_L2SP_181013_20240804_20240808_02_T1_SR_B4.TIF",
        #         "LC08_L2SP_186012_20240807_20240814_02_T1_SR_B4.TIF": "images/downloaded/B4/LC08_L2SP_186012_20240807_20240814_02_T1_SR_B4.TIF",
        #     },
        #     "B5": {
        #         "LC08_L2SP_181013_20240804_20240808_02_T1_SR_B5.TIF": "images/downloaded/B5/LC08_L2SP_181013_20240804_20240808_02_T1_SR_B5.TIF",
        #         "LC08_L2SP_186012_20240807_20240814_02_T1_SR_B5.TIF": "images/downloaded/B5/LC08_L2SP_186012_20240807_20240814_02_T1_SR_B5.TIF",
        #     },
        #     "other": {
        #         "some_filename.extension": "images/downloaded/other/some_filename.extension"
        #     }
        # }

        if len(downloaded_images["B4"]) == 0:
            print("По указанным данным не найдено снимков. Попробуйте изменить дату.")
            return

        try:
            # рассчет NDVI
            processed_images = self._ndvi.calculate(downloaded_images)
            # Пример объекта processed_images:
            # {
            #     "LC08_L2SP_183012_20240802_20240808_02_T2_ndvi_colored.tif": "images/ndvi_output/LC08_L2SP_183012_20240802_20240808_02_T2_ndvi_colored.tif",
            #     "LC08_L2SP_183013_20240802_20240808_02_T1_ndvi_colored.tif": "images/ndvi_output/LC08_L2SP_183013_20240802_20240808_02_T1_ndvi_colored.tif",
            #     "LC09_L2SP_184012_20240801_20240802_02_T1_ndvi_colored.tif": "images/ndvi_output/LC09_L2SP_184012_20240801_20240802_02_T1_ndvi_colored.tif",
            #     "LC09_L2SP_184013_20240801_20240802_02_T2_ndvi_colored.tif": "images/ndvi_output/LC09_L2SP_184013_20240801_20240802_02_T2_ndvi_colored.tif",
            # }
        except Exception as exception:
            print(f"Случилась ошибка: {exception}\n{traceback.format_exc()}")

            error_dir = f"recovery_data"
            os.makedirs(error_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{error_dir}/{timestamp}_downloaded_images.json"

            with open(filename, "w") as file:
                json.dump(processed_images, file, indent=4)

            print(f"Информация об скачанных снимках сохранена в {filename}")

            return

        try:
            # загрузка на Геопортал
            self._geo_portal.upload_snapshots(processed_images)
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


    def continue_process_images(self, downloaded_images_path):
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
            processed_images = self._ndvi.calculate(downloaded_images)
        except Exception as exception:
            print(f"Случилась ошибка: {exception}\n{traceback.format_exc()}")

            return

        try:
            self._geo_portal.upload_snapshots(processed_images)
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

    def continue_upload_to_geoportal(self, processed_images_path):
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
            self._geo_portal.upload_snapshots(processed_images)
        except Exception as exception:
            print(f"Случилась ошибка: {exception}\n{traceback.format_exc()}")

            return

        print("Растительность успешно добавлена")


    def start(self):
        """Запускает взаимодействие с пользователем."""
        while True:
            print("\nВыберите действие:")
            print("1. Нанести на карту растительность по введенным координатам в виде прямоугольника")
            print("2. Выйти")
            choice = input("Ваш выбор: ")

            if choice == "1":
                # Ввод и валидация начальной даты
                while True:
                    start_date = input("Введите начальную дату в формате ГГГГ-ММ-ДД (пример: 2024-08-01): ")
                    if self._validate_date(start_date):
                        break
                    else:
                        print("Неверный формат даты. Пожалуйста, введите дату в формате ГГГГ-ММ-ДД.")

                # Ввод и валидация конечной даты
                while True:
                    end_date = input("Введите конечную дату в формате ГГГГ-ММ-ДД (пример: 2024-08-01): ")
                    if self._validate_date(end_date):
                        break
                    else:
                        print("Неверный формат даты. Пожалуйста, введите дату в формате ГГГГ-ММ-ДД.")

                # Проверка, что начальная дата не позже конечной
                if datetime.strptime(start_date, "%Y-%m-%d") > datetime.strptime(end_date, "%Y-%m-%d"):
                    print("Ошибка: Начальная дата не может быть позже конечной.")
                    continue

                # Ввод координат левого нижнего угла прямоугольника
                while True:
                    print("Ввод координаты левого нижнего угла прямоугольника")
                    lower_left_latitude, lower_left_longitude = self._enter_coordinates()
                    print(f"    Широта = {lower_left_latitude}, Долгота = {lower_left_longitude}")

                    okay = input("Вас устраивают введенные координаты? (y/n): ")
                    if (str.lower(okay) == "y"):
                        break
                    print("Вас не устроили веденные координаты левого нижнего угла прямоугольника.")

                # Ввод координат правого верхнего угла прямоугольника
                while True:
                    print("Ввод координат правого верхнего угла прямоугольника")
                    upper_right_latitude, upper_right_longitude = self._enter_coordinates()
                    print(f"    Широта = {upper_right_latitude}, Долгота = {upper_right_longitude}")

                    okay = input("Вас устраивают введенные координаты? (y/n): ")
                    if (str.lower(okay) == "y"):
                        break
                    print("Вас не устроили веденные координаты правого верхнего угла прямоугольника.")

                downloaded_images = self._earth_explorer.download_images_by_coordinates(
                    start_date,
                    end_date,
                    lower_left_latitude,
                    lower_left_longitude,
                    upper_right_latitude,
                    upper_right_longitude
                )

                # [
                #     {
                #         'name': 'LC08_L2SP_183012_20240802_20240808_02_T2_ndvi_colored.tif',
                #         'path': 'images/ndvi_output/LC08_L2SP_183012_20240802_20240808_02_T2_ndvi_colored.tif',
                #     },
                #     {
                #         'name': 'LC08_L2SP_183013_20240802_20240808_02_T1_ndvi_colored.tif',
                #         'path': 'images/ndvi_output/LC08_L2SP_183013_20240802_20240808_02_T1_ndvi_colored.tif',
                #     },
                #     {
                #         'name': 'LC09_L2SP_184012_20240801_20240802_02_T1_ndvi_colored.tif',
                #         'path': 'images/ndvi_output/LC09_L2SP_184012_20240801_20240802_02_T1_ndvi_colored.tif',
                #     },
                #     {
                #         'name': 'LC09_L2SP_184013_20240801_20240802_02_T2_ndvi_colored.tif',
                #         'path': 'images/ndvi_output/LC09_L2SP_184013_20240801_20240802_02_T2_ndvi_colored.tif',
                #     }
                # ]
                processed_images = self._ndvi.calculate(downloaded_images)

                self._geo_portal.upload_snapshots(processed_images)

            elif choice == "2":
                print("Выход из программы.")
                break
            else:
                print("Неверный выбор.")

    def _enter_coordinates(self):
        """Запрашивает у пользователя координаты и обрабатывает их."""
        latitude = input("    Введите широту (latitude, y): ")
        longitude = input("    Введите долготу (longitude, x): ")

        return (latitude, longitude)

    def _validate_date(self, date_str):
        """Проверяет, соответствует ли строка формату ГГГГ-ММ-ДД."""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False
