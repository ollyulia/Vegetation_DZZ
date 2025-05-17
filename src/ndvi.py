import rasterio
import numpy as np
from pathlib import Path
from collections import defaultdict

class Ndvi:
    def __init__(self):
        pass

    def calculate(self, downloaded_images, path):
        threshold_images = defaultdict(dict)
        processed_images = {}

        OUTPUT_NDVI_DIR = f"{path}/ndvi_output"
        OUTPUT_COMBINED_DIR = f"{path}/ndvi_combined"

        Path(OUTPUT_NDVI_DIR).mkdir(parents=True, exist_ok=True)
        Path(OUTPUT_COMBINED_DIR).mkdir(parents=True, exist_ok=True)

        NDVI_THRESHOLDS = {
            0.2: (107, 195, 106),
            0.3: (96, 182, 96),
            0.35: (85, 168, 84),
        }

        def calculate_ndvi(red_band_path, nir_band_path):
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
            except Exception as e:
                print(f"Ошибка при расчете NDVI: {e}")
                return None, None

        def save_raster(data, profile, output_path):
            try:
                with rasterio.open(output_path, "w", **profile) as dst:
                    dst.write(data)
                print(f"Успешно сохранено в: {output_path}")
                return True
            except Exception as e:
                print(f"Ошибка при сохранении растра: {e}")
                return False

        def combine_images_for_threshold(threshold, files_dict, output_dir):
            """Объединяет GeoTIFF-файлы с учетом их координат и разрешения"""
            if not files_dict:
                return None

            # 1. Собираем метаданные всех изображений
            datasets = []
            bounds = []
            transforms = []
            shapes = []

            for file_path in files_dict.values():
                try:
                    src = rasterio.open(file_path)
                    datasets.append(src)
                    bounds.append(src.bounds)
                    transforms.append(src.transform)
                    shapes.append(src.shape)
                except Exception as e:
                    print(f"Ошибка открытия файла {file_path}: {e}")
                    continue

            if not datasets:
                return None

            # 2. Определяем общую область покрытия и разрешение
            overall_bounds = rasterio.coords.BoundingBox(
                left=min(b.left for b in bounds),
                bottom=min(b.bottom for b in bounds),
                right=max(b.right for b in bounds),
                top=max(b.top for b in bounds)
            )

            # Используем разрешение первого изображения как эталонное
            res = datasets[0].res
            crs = datasets[0].crs

            # 3. Рассчитываем размеры выходного растра
            width = int(round((overall_bounds.right - overall_bounds.left) / res[0]))
            height = int(round((overall_bounds.top - overall_bounds.bottom) / res[1]))

            # 4. Создаем выходной профиль
            out_transform = rasterio.transform.from_origin(
                overall_bounds.left, overall_bounds.top, res[0], res[1]
            )

            out_profile = {
                'driver': 'GTiff',
                'height': height,
                'width': width,
                'count': 4,
                'dtype': 'uint8',
                'crs': crs,
                'transform': out_transform,
                'compress': 'lzw'
            }

            # 5. Создаем пустой массив для объединенных данных
            combined = np.zeros((4, height, width), dtype=np.uint8)
            combined_alpha = np.zeros((height, width), dtype=np.uint8)

            # 6. Процесс объединения
            for src in datasets:
                try:
                    # Вычисляем смещение в пикселях
                    col_off = int(round((src.bounds.left - overall_bounds.left) / res[0]))
                    row_off = int(round((overall_bounds.top - src.bounds.top) / res[1]))

                    # Читаем все данные из исходного файла
                    data = src.read()

                    # Определяем область вставки
                    src_height, src_width = src.shape
                    dst_height = min(src_height, height - row_off)
                    dst_width = min(src_width, width - col_off)

                    if dst_height <= 0 or dst_width <= 0:
                        continue

                    # Обрезаем данные если нужно
                    data = data[:, :dst_height, :dst_width]

                    # Создаем маску непрозрачных пикселей
                    mask = data[3] > 0
                    new_pixels = mask & (combined_alpha[
                        row_off:row_off+dst_height,
                        col_off:col_off+dst_width] == 0)

                    # Обновляем только новые пиксели (которые еще не были заполнены)
                    for band in range(3):
                        combined[
                            band,
                            row_off:row_off+dst_height,
                            col_off:col_off+dst_width
                        ][new_pixels] = data[band][new_pixels]

                    # Обновляем альфа-канал
                    combined_alpha[
                        row_off:row_off+dst_height,
                        col_off:col_off+dst_width][new_pixels] = 255
                    combined[3] = combined_alpha

                except Exception as e:
                    print(f"Ошибка обработки файла {src.name}: {e}")
                    continue

            # 7. Сохранение результата
            output_path = f"{output_dir}/combined_threshold_{threshold}.tif"
            try:
                with rasterio.open(output_path, 'w', **out_profile) as dst:
                    dst.write(combined)
                print(f"Успешно создан объединенный файл: {output_path}")
                return output_path
            except Exception as e:
                print(f"Ошибка сохранения объединенного файла: {e}")
                return None
            finally:
                # Закрываем все файлы
                for src in datasets:
                    try:
                        src.close()
                    except:
                        pass






        # Основная обработка файлов
        red_band_files_entries = downloaded_images["B4"]
        nir_band_files_entries = downloaded_images["B5"]

        print("Производится расчет NDVI")

        if len(red_band_files_entries) != len(nir_band_files_entries):
            print("Разное количество файлов.")

        total_files = len(red_band_files_entries)
        current_file_number = 1

        for red_band_file, red_band_path in red_band_files_entries.items():
            nir_band_file = red_band_file.replace("B4", "B5")
            nir_band_path = nir_band_files_entries.get(nir_band_file)

            if nir_band_path is None:
                print(f"Для файла с красным каналом: {red_band_file}\nНе найден файл с ближним инфракрасным каналом: {nir_band_file}")
                total_files -= 1
                continue

            base_output_name = red_band_file.split("_SR_B4.TIF")[0]
            print(f"[{current_file_number}/{total_files}] Обработка файлов:\n    B4: {red_band_file}\n    B5: {nir_band_file}")

            ndvi, profile = calculate_ndvi(red_band_path, nir_band_path)

            if ndvi is not None and profile is not None:
                for threshold, color in NDVI_THRESHOLDS.items():
                    output_file_name = f"{base_output_name}_ndvi_threshold_{threshold}.tif"
                    output_ndvi_path = f"{OUTPUT_NDVI_DIR}/{output_file_name}"

                    # Создание изображения для порога
                    red_channel = np.zeros_like(ndvi, dtype=np.uint8)
                    green_channel = np.zeros_like(ndvi, dtype=np.uint8)
                    blue_channel = np.zeros_like(ndvi, dtype=np.uint8)
                    alpha_channel = np.zeros_like(ndvi, dtype=np.uint8)

                    mask = ndvi >= threshold
                    red_channel[mask] = color[0]
                    green_channel[mask] = color[1]
                    blue_channel[mask] = color[2]
                    alpha_channel[mask] = 255
                    alpha_channel[(ndvi < threshold) | (np.isnan(ndvi))] = 0

                    rgba = np.stack([red_channel, green_channel, blue_channel, alpha_channel])
                    rgba = np.transpose(rgba, (0, 1, 2))

                    if save_raster(rgba, profile, output_ndvi_path):
                        threshold_images[str(threshold)][output_file_name] = output_ndvi_path

            current_file_number += 1

        # Объединение изображений по порогам
        for threshold in NDVI_THRESHOLDS:
            combined_path = combine_images_for_threshold(
                threshold,
                threshold_images[str(threshold)],
                OUTPUT_COMBINED_DIR
            )
            if combined_path:
                processed_images[f"combined_threshold_{threshold}"] = combined_path

        print("Обработка завершена.")
        return processed_images


def test_calculate():
    ndvi = Ndvi()

    downloaded_images = {
        "B4": {
            "LC09_L2SP_186012_20240815_20240816_02_T1_SR_B4.TIF": "images/downloaded/B4/LC09_L2SP_186012_20240815_20240816_02_T1_SR_B4.TIF",
            "LC09_L2SP_186013_20240815_20240816_02_T1_SR_B4.TIF": "images/downloaded/B4/LC09_L2SP_186013_20240815_20240816_02_T1_SR_B4.TIF",
        },
        "B5": {
            "LC09_L2SP_186012_20240815_20240816_02_T1_SR_B5.TIF": "images/downloaded/B5/LC09_L2SP_186012_20240815_20240816_02_T1_SR_B5.TIF",
            "LC09_L2SP_186013_20240815_20240816_02_T1_SR_B5.TIF": "images/downloaded/B5/LC09_L2SP_186013_20240815_20240816_02_T1_SR_B5.TIF",
        },
    }

    processed_images = ndvi.calculate(downloaded_images, "images/test")

    print(processed_images)

test_calculate()

x = {
    'threshold_0.2_LC09_L2SP_186012_20240815_20240816_02_T1_ndvi_threshold_0.2.tif': 'images/test/ndvi_output/LC09_L2SP_186012_20240815_20240816_02_T1_ndvi_threshold_0.2.tif',
    'threshold_0.3_LC09_L2SP_186012_20240815_20240816_02_T1_ndvi_threshold_0.3.tif': 'images/test/ndvi_output/LC09_L2SP_186012_20240815_20240816_02_T1_ndvi_threshold_0.3.tif',
    'threshold_0.4_LC09_L2SP_186012_20240815_20240816_02_T1_ndvi_threshold_0.4.tif': 'images/test/ndvi_output/LC09_L2SP_186012_20240815_20240816_02_T1_ndvi_threshold_0.4.tif',
    'threshold_0.2_LC09_L2SP_186013_20240815_20240816_02_T1_ndvi_threshold_0.2.tif': 'images/test/ndvi_output/LC09_L2SP_186013_20240815_20240816_02_T1_ndvi_threshold_0.2.tif',
    'threshold_0.3_LC09_L2SP_186013_20240815_20240816_02_T1_ndvi_threshold_0.3.tif': 'images/test/ndvi_output/LC09_L2SP_186013_20240815_20240816_02_T1_ndvi_threshold_0.3.tif',
    'threshold_0.4_LC09_L2SP_186013_20240815_20240816_02_T1_ndvi_threshold_0.4.tif': 'images/test/ndvi_output/LC09_L2SP_186013_20240815_20240816_02_T1_ndvi_threshold_0.4.tif'
}

# 0.1: (117, 209, 117),
# 0.2: (107, 195, 106),
# 0.3: (96, 182, 96), # Светло-зеленый
# 0.4: (85, 168, 84),   # Зеленый
# 0.5: (74, 155, 74),     # Темно-зеленый
# 0.6: (64, 141, 64),
# 0.7: (42, 116, 42),
# 0.8: (30, 101, 30),
# 0.9: (20, 88, 21),

# x = defaultdict(
#     <class 'dict'>,
#     {
#         '0.2': {
#             'LC09_L2SP_186012_20240815_20240816_02_T1_ndvi_threshold_0.2.tif': 'images/test/ndvi_output/LC09_L2SP_186012_20240815_20240816_02_T1_ndvi_threshold_0.2.tif',
#             'LC09_L2SP_186013_20240815_20240816_02_T1_ndvi_threshold_0.2.tif': 'images/test/ndvi_output/LC09_L2SP_186013_20240815_20240816_02_T1_ndvi_threshold_0.2.tif'
#         },
#         '0.3': {
#             'LC09_L2SP_186012_20240815_20240816_02_T1_ndvi_threshold_0.3.tif': 'images/test/ndvi_output/LC09_L2SP_186012_20240815_20240816_02_T1_ndvi_threshold_0.3.tif',
#             'LC09_L2SP_186013_20240815_20240816_02_T1_ndvi_threshold_0.3.tif': 'images/test/ndvi_output/LC09_L2SP_186013_20240815_20240816_02_T1_ndvi_threshold_0.3.tif'
#         },
#         '0.4': {
#             'LC09_L2SP_186012_20240815_20240816_02_T1_ndvi_threshold_0.4.tif': 'images/test/ndvi_output/LC09_L2SP_186012_20240815_20240816_02_T1_ndvi_threshold_0.4.tif',
#             'LC09_L2SP_186013_20240815_20240816_02_T1_ndvi_threshold_0.4.tif': 'images/test/ndvi_output/LC09_L2SP_186013_20240815_20240816_02_T1_ndvi_threshold_0.4.tif'
#         }
#     }
# )
