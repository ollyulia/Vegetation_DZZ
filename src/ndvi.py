import rasterio
import numpy as np
from pathlib import Path
from collections import defaultdict
from rasterio.transform import from_origin
from rasterio.crs import CRS
from pathlib import Path
from rasterio.vrt import WarpedVRT

class Ndvi:
    def __init__(self):
        pass

    def calculate(
        self,
        downloaded_images,
        path,
    ):
        '''
        Пример объекта `downloaded_images`:
        ```
        {
            "B4": {
                "X_B4.TIF": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/B4/X_B4.TIF",
                "Y_B4.TIF": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/B4/Y_B4.TIF",
            },
            "B5": {
                "X_B5.TIF": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/B5/X_B5.TIF",
                "Y_B5.TIF": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/B5/Y_B5.TIF",
            },
        }
        ```
        '''
        OUTPUT_NDVI_DIR = f"{path}/ndvi_thresholds"
        OUTPUT_COMBINED_DIR = f"{path}/ndvi_combined"

        Path(OUTPUT_NDVI_DIR).mkdir(parents=True, exist_ok=True)
        Path(OUTPUT_COMBINED_DIR).mkdir(parents=True, exist_ok=True)

        NDVI_THRESHOLDS = {
            0.2: (107, 195, 106),
            0.3: (96, 182, 96),
            0.35: (85, 168, 84),
        }

        prepared_downloaded_images_data = self._prepare_downloaded_images(downloaded_images)

        ndvi_thresholds_images_data = self._create_ndvi_thresholds(
            prepared_downloaded_images_data,
            OUTPUT_NDVI_DIR,
            NDVI_THRESHOLDS
        )

        combined_images_data = self._combine_ndvi_thresholds(
            ndvi_thresholds_images_data,
            NDVI_THRESHOLDS,
            OUTPUT_COMBINED_DIR,
        )

        print("Обработка завершена.")
        return combined_images_data

    def _prepare_downloaded_images(self, downloaded_images):
        '''
        Преобразовывает:

        ```
        {
            "B4": {
                "X_B4.TIF": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/B4/X_B4.TIF",
                "Y_B4.TIF": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/B4/Y_B4.TIF",
            },
            "B5": {
                "X_B5.TIF": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/B5/X_B5.TIF",
                "Y_B5.TIF": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/B5/Y_B5.TIF",
            },
        }
        ```
        в
        ```
        [
            {
                "base_name": "X",
                "path_B4": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/B4/X_B4.TIF",
                "path_B5": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/B4/X_B5.TIF"
            },
            {
                "base_name": "Y",
                "path_B4": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/B4/Y_B4.TIF",
                "path_B5": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/B4/Y_B5.TIF"
            }
        ]
        ```
        '''
        prepared_downloaded_images_paths = []

        red_band_files_entries = downloaded_images["B4"]
        nir_band_files_entries = downloaded_images["B5"]

        for red_band_file, red_band_path in red_band_files_entries.items():
            nir_band_file = red_band_file.replace("B4", "B5")
            nir_band_path = nir_band_files_entries.get(nir_band_file)

            if nir_band_path is None:
                print(f"Для файла с красным каналом: {red_band_file}\nНе найден файл с ближним инфракрасным каналом: {nir_band_file}")
                continue

            base_name = red_band_file.split("_SR_B4.TIF")[0]
            prepared_downloaded_images_paths.append({
                "base_name": base_name,
                "path_B4": red_band_path,
                "path_B5": nir_band_path,
            })

        return prepared_downloaded_images_paths

    def _create_ndvi_thresholds(
        self,
        prepared_downloaded_images_data,
        OUTPUT_NDVI_DIR,
        NDVI_THRESHOLDS,
    ):
        '''
        `prepared_downloaded_images_data`:
        ```
        [
            {
                "base_name": "X",
                "path_B4": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/B4/X_B4.TIF",
                "path_B5": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/B4/X_B5.TIF"
            },
            {
                "base_name": "Y",
                "path_B4": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/B4/Y_B4.TIF",
                "path_B5": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/B4/Y_B5.TIF"
            }
        ]
        ```

        Возвращает `ndvi_thresholds_data`:
        ```
        {
            "0.2": {
                "20_X.tif": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_thresholds/20_X.tif",
                "20_Y.tif": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_thresholds/20_Y.tif"
            },
            "0.3": {
                "30_X.tif": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_thresholds/30_X.tif",
                "30_Y.tif": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_thresholds/30_Y.tif"
            },
            "0.4": {
                "40_X.tif": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_thresholds/40_X.tif",
                "40_Y.tif": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_thresholds/40_Y.tif"
            }
        }
        ```
        '''
        ndvi_thresholds_data = {}

        for entry in prepared_downloaded_images_data:
            base_name = entry["base_name"]
            red_band_path = entry["path_B4"]
            nir_band_path = entry["path_B5"]

            ndvi, profile = self._calculate_ndvi(red_band_path, nir_band_path)

            if ndvi is None or profile is None:
                continue

            for threshold, color in NDVI_THRESHOLDS.items():
                # Инициализация вложенного словаря, если его ещё нет
                if str(threshold) not in ndvi_thresholds_data:
                    ndvi_thresholds_data[str(threshold)] = {}

                output_file_name = f"{int(threshold*100)}_{base_name}.tif"
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

                if self._save_raster(rgba, profile, output_ndvi_path):
                    ndvi_thresholds_data[str(threshold)][output_file_name] = output_ndvi_path

        return ndvi_thresholds_data

    # def _combine_ndvi_thresholds(
    #     self,
    #     ndvi_thresholds_images_data,
    #     NDVI_THRESHOLDS,
    #     OUTPUT_COMBINED_DIR,
    # ):
    #     '''
    #     `ndvi_thresholds_images_data`:
    #     ```
    #     {
    #         "0.2": {
    #             "20_X.tif": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_thresholds/20_X.tif",
    #             "20_Y.tif": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_thresholds/20_Y.tif"
    #         },
    #         "0.3": {
    #             "30_X.tif": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_thresholds/30_X.tif",
    #             "30_Y.tif": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_thresholds/30_Y.tif"
    #         },
    #         "0.4": {
    #             "40_X.tif": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_thresholds/40_X.tif",
    #             "40_Y.tif": "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_thresholds/40_Y.tif"
    #         }
    #     }
    #     ```

    #     Возвращает `combined_images_data`:
    #     ```
    #     {
    #         '0.2': 'images/test/ndvi_combined/combined_threshold_20.tif',
    #         '0.3': 'images/test/ndvi_combined/combined_threshold_30.tif',
    #         '0.4': 'images/test/ndvi_combined/combined_threshold_40.tif'
    #     }
    #     ```
    #     '''
    #     combined_images_data = {}

    #     # Объединение изображений по порогам
    #     for threshold in NDVI_THRESHOLDS:
    #         combined_path = self._combine_images_for_threshold(
    #             threshold,
    #             ndvi_thresholds_images_data[str(threshold)],
    #             OUTPUT_COMBINED_DIR
    #         )

    #         if combined_path:
    #             combined_images_data[f"{threshold}"] = combined_path

    #     return combined_images_data

    def _combine_ndvi_thresholds(
        self,
        ndvi_thresholds_images_data,
        NDVI_THRESHOLDS,
        OUTPUT_COMBINED_DIR,
    ):
        '''
        Объединяет изображения NDVI по порогам в один файл с учетом CRS EPSG:32636,
        применяя стандартную цветовую схему для NDVI.
        '''
        combined_images_data = {}
        target_crs = CRS.from_epsg(32636)

        # Создаем стандартную цветовую карту для NDVI
        ndvi_colormap = {
            0: (0, 0, 0, 0),        # NoData - прозрачный
            1: (165, 0, 38, 255),    # Красный (низкие значения)
            85: (255, 255, 0, 255), # Желтый (средние значения)
            170: (0, 128, 0, 255),  # Зеленый (высокие значения)
            255: (0, 100, 0, 255)   # Темно-зеленый (максимальные значения)
        }

        Path(OUTPUT_COMBINED_DIR).mkdir(parents=True, exist_ok=True)

        for threshold in NDVI_THRESHOLDS:
            if str(threshold) not in ndvi_thresholds_images_data:
                continue

            files_dict = ndvi_thresholds_images_data[str(threshold)]
            if not files_dict:
                continue

            datasets = []
            bounds = []
            transforms = []
            shapes = []
            src_files = []

            for file_path in files_dict.values():
                try:
                    src = rasterio.open(file_path)
                    src_files.append(src)

                    if src.crs != target_crs:
                        vrt = WarpedVRT(src, crs=target_crs)
                        datasets.append(vrt)
                    else:
                        datasets.append(src)

                    bounds.append(datasets[-1].bounds)
                    transforms.append(datasets[-1].transform)
                    shapes.append(datasets[-1].shape)
                except Exception as e:
                    print(f"Ошибка открытия файла {file_path}: {e}")
                    continue

            if not datasets:
                for src in src_files:
                    src.close()
                continue

            try:
                overall_bounds = rasterio.coords.BoundingBox(
                    left=min(b.left for b in bounds),
                    bottom=min(b.bottom for b in bounds),
                    right=max(b.right for b in bounds),
                    top=max(b.top for b in bounds))

                res = datasets[0].res
                width = int(round((overall_bounds.right - overall_bounds.left) / res[0]))
                height = int(round((overall_bounds.top - overall_bounds.bottom) / res[1]))

                out_transform = from_origin(
                    overall_bounds.left, overall_bounds.top, res[0], res[1])

                first_dataset = datasets[0]
                out_profile = {
                    'driver': 'GTiff',
                    'height': height,
                    'width': width,
                    'count': 1,
                    'dtype': first_dataset.dtypes[0],
                    'crs': target_crs,
                    'transform': out_transform,
                    'compress': 'lzw',
                    'nodata': first_dataset.nodata
                }

                combined = np.zeros((height, width), dtype=out_profile['dtype'])
                combined_mask = np.zeros((height, width), dtype=bool)

                for i, dataset in enumerate(datasets):
                    try:
                        col_off = int(round((dataset.bounds.left - overall_bounds.left) / res[0]))
                        row_off = int(round((overall_bounds.top - dataset.bounds.top) / res[1]))

                        data = dataset.read(1)
                        src_height, src_width = dataset.shape
                        dst_height = min(src_height, height - row_off)
                        dst_width = min(src_width, width - col_off)

                        if dst_height <= 0 or dst_width <= 0:
                            continue

                        data = data[:dst_height, :dst_width]
                        mask = (data != dataset.nodata) if dataset.nodata is not None else np.ones_like(data, dtype=bool)
                        new_pixels = mask & (~combined_mask[row_off:row_off+dst_height, col_off:col_off+dst_width])

                        combined[row_off:row_off+dst_height, col_off:col_off+dst_width][new_pixels] = data[new_pixels]
                        combined_mask[row_off:row_off+dst_height, col_off:col_off+dst_width] |= mask

                    except Exception as e:
                        print(f"Ошибка обработки файла {src_files[i].name}: {e}")
                        continue

                threshold_percent = int(float(threshold) * 100)
                output_path = Path(OUTPUT_COMBINED_DIR) / f"combined_threshold_{threshold_percent}.tif"

                with rasterio.open(output_path, 'w', **out_profile) as dst:
                    dst.write(combined, 1)
                    # Применяем стандартную цветовую схему NDVI
                    dst.write_colormap(1, ndvi_colormap)

                combined_images_data[str(threshold)] = str(output_path)

            finally:
                for dataset in datasets:
                    if hasattr(dataset, 'close'):
                        dataset.close()
                for src in src_files:
                    src.close()

        return combined_images_data

    def _calculate_ndvi(self, red_band_path: str, nir_band_path: str):
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

    def _save_raster(self, data, profile, output_path):
        try:
            with rasterio.open(output_path, "w", **profile) as dst:
                dst.write(data)
            print(f"Успешно сохранено в: {output_path}")
            return True
        except Exception as e:
            print(f"Ошибка при сохранении растра: {e}")
            return False


def test_calculate():
    ndvi = Ndvi()

    downloaded_images = {
        "B4": {
            "LC08_L2SP_187011_20240814_20240822_02_T1_SR_B4.TIF": "images/2025-05-20/2024-08-14_2024-08-15_68.562252:31.50702_68.915808:37.134767/B4/LC08_L2SP_187011_20240814_20240822_02_T1_SR_B4.TIF",
            "LC08_L2SP_187012_20240814_20240822_02_T1_SR_B4.TIF": "images/2025-05-20/2024-08-14_2024-08-15_68.562252:31.50702_68.915808:37.134767/B4/LC08_L2SP_187012_20240814_20240822_02_T1_SR_B4.TIF",
            "LC09_L2SP_186011_20240815_20240816_02_T1_SR_B4.TIF": "images/2025-05-20/2024-08-14_2024-08-15_68.562252:31.50702_68.915808:37.134767/B4/LC09_L2SP_186011_20240815_20240816_02_T1_SR_B4.TIF",
            "LC09_L2SP_186012_20240815_20240816_02_T1_SR_B4.TIF": "images/2025-05-20/2024-08-14_2024-08-15_68.562252:31.50702_68.915808:37.134767/B4/LC09_L2SP_186012_20240815_20240816_02_T1_SR_B4.TIF"
        },
        "B5": {
            "LC08_L2SP_187011_20240814_20240822_02_T1_SR_B5.TIF": "images/2025-05-20/2024-08-14_2024-08-15_68.562252:31.50702_68.915808:37.134767/B5/LC08_L2SP_187011_20240814_20240822_02_T1_SR_B5.TIF",
            "LC08_L2SP_187012_20240814_20240822_02_T1_SR_B5.TIF": "images/2025-05-20/2024-08-14_2024-08-15_68.562252:31.50702_68.915808:37.134767/B5/LC08_L2SP_187012_20240814_20240822_02_T1_SR_B5.TIF",
            "LC09_L2SP_186011_20240815_20240816_02_T1_SR_B5.TIF": "images/2025-05-20/2024-08-14_2024-08-15_68.562252:31.50702_68.915808:37.134767/B5/LC09_L2SP_186011_20240815_20240816_02_T1_SR_B5.TIF",
            "LC09_L2SP_186012_20240815_20240816_02_T1_SR_B5.TIF": "images/2025-05-20/2024-08-14_2024-08-15_68.562252:31.50702_68.915808:37.134767/B5/LC09_L2SP_186012_20240815_20240816_02_T1_SR_B5.TIF"
        }
    }

    path = "images/test"
    processed_images = ndvi.calculate(downloaded_images, path)

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
