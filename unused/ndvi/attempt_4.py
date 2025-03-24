import rasterio
import numpy as np
import logging
import os
import glob

#1. Настройка

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Пути к каталогам с данными
RED_BAND_DIR = 'B4'
NIR_BAND_DIR = 'B5'
OUTPUT_NDVI_DIR = 'output'

# Шаблоны имен файлов
RED_BAND_PATTERN = '*.TIF'
NIR_BAND_PATTERN = '*.TIF'

# Пороговые значения NDVI и соответствующие цвета (RGB)
NDVI_COLORS = {

    0.2: (134, 255, 142),  # Светло-зеленый (Разряженная, слабая растительность.)
    0.4: (41, 154, 97),      # Зеленый (Умеренная биомасса.)
    0.6: (16, 117, 5)       # Темно-зеленый (Густые, здоровые посевы, которые нормально развиваются.)
}


# 2. Функция для расчета NDVI

def calculate_ndvi(red_band_path, nir_band_path):
    """Рассчитывает NDVI."""
    try:
        with rasterio.open(red_band_path) as red_src, \
             rasterio.open(nir_band_path) as nir_src:

            red = red_src.read(1).astype(np.float32)
            nir = nir_src.read(1).astype(np.float32)
            with np.errstate(divide='ignore', invalid='ignore'):
                ndvi = np.where((nir + red) > 0, (nir - red) / (nir + red), np.nan)

            profile = red_src.profile.copy()
            profile.update(
                dtype=rasterio.uint8,
                count=4,
                compress='lzw'
            )
            return ndvi, profile

    except rasterio.RasterioIOError as e:
        logging.error(f"Ошибка при чтении файла: {e}")
        return None, None
    except Exception as e:
        logging.error(f"Ошибка при расчете NDVI: {e}")
        return None, None

# 3. Функция для сохранения растра

def save_raster(data, profile, output_path):
    """Сохраняет растр."""
    try:
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(data)
        logging.info(f"Растр сохранен в {output_path}")
        return True
    except Exception as e:
        logging.error(f"Ошибка при сохранении растра: {e}")
        return False

# 4. Основной скрипт

if __name__ == "__main__":
    red_band_files = sorted(glob.glob(os.path.join(RED_BAND_DIR, RED_BAND_PATTERN)))
    nir_band_files = sorted(glob.glob(os.path.join(NIR_BAND_DIR, NIR_BAND_PATTERN)))

    if len(red_band_files) != len(nir_band_files):
        logging.error("Разное количество файлов.")
        exit()

    for red_band_path, nir_band_path in zip(red_band_files, nir_band_files):
        file_name = os.path.basename(red_band_path).split('.')[0]
        output_ndvi_path = os.path.join(OUTPUT_NDVI_DIR, f'{file_name}_ndvi_colored.tif')

        logging.info(f"Обработка: {red_band_path} и {nir_band_path}")

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
                alpha_channel = np.where(ndvi >= threshold, 255, alpha_channel) #Добавляем прозрачность для ненужных частей.

            # Области, где NDVI отрицательный или NaN, делаем прозрачными
            alpha_channel = np.where((ndvi < 0) | (np.isnan(ndvi)), 0, alpha_channel)

            # Объединяем каналы
            rgba = np.stack([red_channel, green_channel, blue_channel, alpha_channel])

            # Изменяем порядок каналов для rasterio
            rgba = np.transpose(rgba, (0, 1, 2))

            # Сохраняем растр
            success = save_raster(rgba, profile, output_ndvi_path)

            if success:
                logging.info(f"Успешно сохранено: {output_ndvi_path}")
            else:
                logging.error(f"Ошибка при сохранении.")
        else:
            logging.error(f"Ошибка при расчете NDVI.")

    logging.info("Обработка завершена.")
