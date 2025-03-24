import rasterio
import numpy as np
from pathlib import Path

class Ndvi:
    def __init__(self):
        pass

    def calculate(self, downloaded_images):
        processed_images = {}

        #1. Настройка

        # Пути к каталогам с данными
        RED_BAND_DIR = "images/downloaded/B4"
        NIR_BAND_DIR = "images/downloaded/B5"
        OUTPUT_NDVI_DIR = "images/ndvi_output"

        Path(RED_BAND_DIR).mkdir(parents=True, exist_ok=True)
        Path(NIR_BAND_DIR).mkdir(parents=True, exist_ok=True)
        Path(OUTPUT_NDVI_DIR).mkdir(parents=True, exist_ok=True)

        # Пороговые значения NDVI и соответствующие цвета (RGB)
        NDVI_COLORS = {
            0.2: (134, 255, 142), # Светло-зеленый (Разряженная, слабая растительность.)
            0.4: (41, 154, 97),   # Зеленый (Умеренная биомасса.)
            0.6: (16, 117, 5)     # Темно-зеленый (Густые, здоровые посевы, которые нормально развиваются.)
        }

        # 2. Функция для расчета NDVI
        def calculate_ndvi(red_band_path, nir_band_path):
            """Рассчитывает NDVI."""
            try:
                with rasterio.open(red_band_path) as red_src, rasterio.open(nir_band_path) as nir_src:
                    red = red_src.read(1).astype(np.float32)
                    nir = nir_src.read(1).astype(np.float32)
                    with np.errstate(divide="ignore", invalid="ignore"):
                        ndvi = np.where((nir + red) > 0, (nir - red) / (nir + red), np.nan)

                    profile = red_src.profile.copy()
                    profile.update(
                        dtype=rasterio.uint8,
                        count=4,
                        compress="lzw"
                    )
                    return ndvi, profile

            except rasterio.RasterioIOError as e:
                print(f"Ошибка при чтении файла: {e}")
                return None, None
            except Exception as e:
                print(f"Ошибка при расчете NDVI: {e}")
                return None, None

        # 3. Функция для сохранения растра

        def save_raster(data, profile, output_path):
            """Сохраняет растр."""
            try:
                with rasterio.open(output_path, "w", **profile) as dst:
                    dst.write(data)

                print(f"Успешно сохранено в: {output_path}\n")
                return True
            except Exception as e:
                print(f"Ошибка при сохранении растра: {e}\n")
                return False

        # 4. Основной скрипт
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

        red_band_files_entries = downloaded_images["B4"]
        nir_band_files_entries = downloaded_images["B5"]

        print("Производится расчет NDVI")

        if len(red_band_files_entries) != len(nir_band_files_entries):
            print("Разное количество файлов.")

        for red_band_file, red_band_path in red_band_files_entries.items():
            nir_band_file = red_band_file.replace("B4", "B5")

            nir_band_path = nir_band_files_entries.get(nir_band_file)

            if nir_band_path is None:
                print(f"Для файла с красным каналом: {red_band_file}\nНе найден файл с ближним инфракрасным каналом: {nir_band_file}\n")
                continue

            output_file_name = red_band_file.split("_SR_B4.TIF")[0]
            output_file_name = f"{output_file_name}_ndvi_colored.tif"
            output_ndvi_path = f"{OUTPUT_NDVI_DIR}/{output_file_name}"

            print(f"Обработка файлов:\n    B4: {red_band_file}\n    B5: {nir_band_file}")

            ndvi, profile = calculate_ndvi(red_band_path, nir_band_path)

            if ndvi is not None and profile is not None:
                # Инициализация каналов
                red_channel = np.zeros_like(ndvi, dtype=np.uint8)
                green_channel = np.zeros_like(ndvi, dtype=np.uint8)
                blue_channel = np.zeros_like(ndvi, dtype=np.uint8)
                alpha_channel = np.zeros_like(ndvi, dtype=np.uint8)

                # Применение цветов в зависимости от значений NDVI
                for threshold, color in NDVI_COLORS.items():
                    red_channel = np.where(ndvi >= threshold, color[0], red_channel)
                    green_channel = np.where(ndvi >= threshold, color[1], green_channel)
                    blue_channel = np.where(ndvi >= threshold, color[2], blue_channel)
                    alpha_channel = np.where(ndvi >= threshold, 255, alpha_channel) # Добавляем прозрачность для ненужных частей.

                # Области, где NDVI отрицательный или NaN, делаем прозрачными
                alpha_channel = np.where((ndvi < 0) | (np.isnan(ndvi)), 0, alpha_channel)

                # Объединяем каналы
                rgba = np.stack([red_channel, green_channel, blue_channel, alpha_channel])

                # Изменяем порядок каналов для rasterio
                rgba = np.transpose(rgba, (0, 1, 2))

                # Сохраняем растр
                save_raster(rgba, profile, output_ndvi_path)

                processed_images[output_file_name] = output_ndvi_path
            else:
                print(f"Ошибка при расчете NDVI.")

        print("Обработка завершена.")

        return processed_images


def test():
    ndvi = Ndvi()

    downloaded_images = {
        "B4": [
            "LC08_L2SP_183012_20240802_20240808_02_T2_SR_B4.TIF",
            "LC08_L2SP_183013_20240802_20240808_02_T1_SR_B4.TIF",
            "LC09_L2SP_184012_20240801_20240802_02_T1_SR_B4.TIF",
            "LC09_L2SP_184013_20240801_20240802_02_T2_SR_B4.TIF"
        ],
        "B5": [
            "LC08_L2SP_183012_20240802_20240808_02_T2_SR_B5.TIF",
            "LC08_L2SP_183013_20240802_20240808_02_T1_SR_B5.TIF",
            "LC09_L2SP_184012_20240801_20240802_02_T1_SR_B5.TIF",
            "LC09_L2SP_184013_20240801_20240802_02_T2_SR_B5.TIF"
        ],
    }

    result = ndvi.calculate(downloaded_images)

    print(result)
