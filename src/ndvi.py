import numpy as np
import os
import rasterio
<<<<<<< HEAD
import tempfile
import shutil
import json
import pyproj

from shapely.geometry import shape, mapping
from shapely.ops import transform
from functools import partial
from rasterio.mask import mask
=======
import glob
import tempfile
import shutil

>>>>>>> refs/remotes/origin/main
from pathlib import Path
from rasterio.merge import merge
from rasterio.warp import calculate_default_transform, reproject, Resampling
from tqdm import tqdm

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

<<<<<<< HEAD
        combined_images_data = self._combine_ndvi_thresholds(
            ndvi_thresholds_images_data,
            NDVI_THRESHOLDS,
            OUTPUT_COMBINED_DIR,
        )

        print("Обработка завершена.")
        return combined_images_data
=======
        # combined_images_data = self._combine_ndvi_thresholds(
        #     ndvi_thresholds_images_data,
        #     NDVI_THRESHOLDS,
        #     OUTPUT_COMBINED_DIR,
        # )

        print("Обработка завершена.")
        return ndvi_thresholds_images_data
>>>>>>> refs/remotes/origin/main

    def _prepare_downloaded_images(self, downloaded_images):
        '''
        Преобразовывает `downloaded_images`:
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
        в `prepared_downloaded_images_paths`:
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
<<<<<<< HEAD
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
=======
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
>>>>>>> refs/remotes/origin/main
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
                # Инициализация вложенного списка, если его ещё нет
                if str(threshold) not in ndvi_thresholds_data:
<<<<<<< HEAD
                    ndvi_thresholds_data[str(threshold)] = {}
=======
                    ndvi_thresholds_data[str(threshold)] = []
>>>>>>> refs/remotes/origin/main

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
<<<<<<< HEAD
                    ndvi_thresholds_data[str(threshold)][output_file_name] = output_ndvi_path
=======
                    ndvi_thresholds_data[str(threshold)].append(output_ndvi_path)
>>>>>>> refs/remotes/origin/main

        return ndvi_thresholds_data

    def _combine_ndvi_thresholds(
        self,
        ndvi_thresholds_images_data,
        NDVI_THRESHOLDS,
        OUTPUT_COMBINED_DIR,
    ):
        '''
        `ndvi_thresholds_images_data`:
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

        Возвращает `combined_images_data`:
        ```
        {
            '0.2': 'images/test/ndvi_combined/combined_threshold_20.tif',
            '0.3': 'images/test/ndvi_combined/combined_threshold_30.tif',
            '0.4': 'images/test/ndvi_combined/combined_threshold_40.tif'
        }
        ```
        '''
        combined_images_data = {}

        # Объединение изображений по порогам
        for threshold in NDVI_THRESHOLDS:
            combined_path = self._create_mosaic(
                threshold,
                ndvi_thresholds_images_data[str(threshold)],
                OUTPUT_COMBINED_DIR,
                "EPSG:32636"
            )

            if combined_path:
                combined_images_data[f"{threshold}"] = combined_path

        return combined_images_data

<<<<<<< HEAD
    def _load_mask(self, mask_path, target_crs):
        """Загрузка и трансформация маски в целевую систему координат"""
        with open(mask_path) as f:
            geojson = json.load(f)

        geom = shape(geojson)
        if not geom.is_valid:
            geom = geom.buffer(0)

        src_crs = pyproj.CRS.from_epsg(4326)  # WGS84
        dst_crs = pyproj.CRS.from_string(target_crs)

        project = partial(
            pyproj.transform,
            pyproj.Proj(src_crs),
            pyproj.Proj(dst_crs)
        )

        transformed_geom = transform(project, geom)
        return [mapping(transformed_geom)]

=======
>>>>>>> refs/remotes/origin/main
    def _reproject_to_target_crs(self, src_path, target_crs='EPSG:32636'):
        """
        Трансформирует растровый файл в целевую систему координат (CRS) с оптимизированными настройками
        """
        with rasterio.open(src_path) as src:
            transform, width, height = calculate_default_transform(
                src.crs,
                target_crs,
                src.width,
                src.height,
                *src.bounds
            )

            kwargs = src.meta.copy()
            kwargs.update({
                'crs': target_crs,
                'transform': transform,
                'width': width,
                'height': height,
<<<<<<< HEAD
                'compress': 'lzw',
                'tiled': True,
                'blockxsize': 256,
=======
                'compress': 'lzw',  # Add compression
                'tiled': True,      # Use tiled storage
                'blockxsize': 256,  # Tile size
>>>>>>> refs/remotes/origin/main
                'blockysize': 256
            })

            temp_dir = tempfile.mkdtemp()
            temp_file = os.path.join(temp_dir, os.path.basename(src_path))

            with rasterio.open(temp_file, 'w', **kwargs) as dst:
                for i in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=target_crs,
                        resampling=Resampling.nearest,
                        num_threads=2
                    )

            return temp_file, temp_dir

    def _create_mosaic(self, threshold, tif_files, output_dir, target_crs='EPSG:32636'):
<<<<<<< HEAD
        """Объединяет обработанные снимки, обрезает по маске и создает единый файл"""
=======
        """Объединяет обработанные снимки и создает единый файл"""
>>>>>>> refs/remotes/origin/main

        if not tif_files:
            print("Не найдено файлов.")
            return

        print(f"Объединение {len(tif_files)} файлов с порогом {threshold} ...")

        src_files_to_mosaic = []
        temp_dirs = []

        try:
<<<<<<< HEAD
            # Обработка файлов с прогресс-баром
=======
            # Process files with progress tracking
>>>>>>> refs/remotes/origin/main
            for file_name, file_path in tqdm(tif_files.items(), desc="Объединение файлов"):
                try:
                    with rasterio.open(file_path) as src:
                        if src.crs.to_string() != target_crs:
                            temp_file, temp_dir = self._reproject_to_target_crs(file_path, target_crs)
                            temp_dirs.append(temp_dir)
                            src_reproj = rasterio.open(temp_file)
                            src_files_to_mosaic.append(src_reproj)
                        else:
                            src_orig = rasterio.open(file_path)
                            src_files_to_mosaic.append(src_orig)
                except Exception as e:
                    print(f"\nОшибка объединения: {os.path.basename(file_path)}: {e}")
                    continue

            if not src_files_to_mosaic:
                print("Не найдено подходящих файлов для объединения.")
                return

            print("\nОбъединение файлов (может занять некоторое время)...")
            mosaic, out_trans = merge(
                src_files_to_mosaic,
                method='first',
                dtype='uint16',
                resampling=Resampling.nearest
            )

<<<<<<< HEAD
            # Создаем временный файл мозаики для обрезки
            mosaic_meta = src_files_to_mosaic[0].meta.copy()
            mosaic_meta.update({
=======
            out_meta = src_files_to_mosaic[0].meta.copy()
            out_meta.update({
>>>>>>> refs/remotes/origin/main
                "driver": "GTiff",
                "height": mosaic.shape[1],
                "width": mosaic.shape[2],
                "transform": out_trans,
<<<<<<< HEAD
                "crs": target_crs
            })

            temp_mosaic_path = os.path.join(tempfile.mkdtemp(), 'mosaic_temp.tif')
            with rasterio.open(temp_mosaic_path, 'w', **mosaic_meta) as dst:
                dst.write(mosaic)

            # Загрузка маски
            mask_geometries = self._load_mask('data/murmankaya_oblast.json', target_crs)
            if not mask_geometries:
                print("Не удалось загрузить маску. Сохранение без обрезки.")
                output_path = f"{output_dir}/combined_threshold_{int(threshold*100)}.tif"
                with rasterio.open(output_path, "w", **out_meta) as dst:
                    dst.write(mosaic)
                return output_path

            # Проверка пересечения маски с мозаикой
            mosaic_bounds = box(*rasterio.warp.transform_bounds(
                target_crs, 'EPSG:4326', *out_trans * (0, mosaic.shape[2], 0, mosaic.shape[1])
            )
            mask_shape = shape(mask_geometries[0])

            if not mosaic_bounds.intersects(mask_shape):
                print("Маска не пересекается с мозаикой. Сохранение без обрезки.")
                output_path = f"{output_dir}/combined_threshold_{int(threshold*100)}.tif"
                with rasterio.open(output_path, "w", **out_meta) as dst:
                    dst.write(mosaic)
                return output_path
            # Обрезка по маске
            print("Обрезка по маске...")
            with rasterio.open(temp_mosaic_path) as src:
                out_image, out_transform = mask(
                    src,
                    mask_geometries,
                    crop=True,
                    all_touched=True
                )
                out_meta = src.meta.copy()
                out_meta.update({
                    "driver": "GTiff",
                    "height": out_image.shape[1],
                    "width": out_image.shape[2],
                    "transform": out_transform,
                    "compress": 'deflate',
                    "zlevel": 6,
                    "predictor": 2,
                    "tiled": True,
                    "blockxsize": 512,
                    "blockysize": 512,
                    "nodata": 0,
                    "BIGTIFF": 'IF_NEEDED'
                })

                output_path = f"{output_dir}/combined_threshold_{int(threshold*100)}_masked.tif"
                with rasterio.open(output_path, "w", **out_meta) as dst:
                    dst.write(out_image)

=======
                "crs": target_crs,
                "compress": 'deflate',
                "zlevel": 6,
                "predictor": 2,
                "tiled": True,
                "blockxsize": 512,
                "blockysize": 512,
                "nodata": 0,
                "BIGTIFF": 'IF_NEEDED'
            })

            output_path = f"{output_dir}/combined_threshold_{int(threshold*100)}.tif"

            with rasterio.open(output_path, "w", **out_meta) as dst:
                dst.write(mosaic)

>>>>>>> refs/remotes/origin/main
            print(f"\nУспешно создан файл: {output_path}")

        except Exception as e:
            print(f"\nError during mosaic creation: {e}")
<<<<<<< HEAD
            raise
        finally:
            # Очистка ресурсов
=======
        finally:
>>>>>>> refs/remotes/origin/main
            for src in src_files_to_mosaic:
                try:
                    src.close()
                except:
                    pass

            for temp_dir in temp_dirs:
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass

<<<<<<< HEAD
            try:
                os.remove(temp_mosaic_path)
                os.rmdir(os.path.dirname(temp_mosaic_path))
            except:
                pass

=======
>>>>>>> refs/remotes/origin/main
        return output_path

    def _combine_images_for_threshold(self, threshold, files_dict, output_dir):
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
        output_path = f"{output_dir}/combined_threshold_{int(threshold*100)}.tif"
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
            "LC08_L2SP_188011_20240821_20240830_02_T1_SR_B4.TIF": "images/test/B4/LC08_L2SP_188011_20240821_20240830_02_T1_SR_B4.TIF",
            "LC08_L2SP_188012_20240821_20240830_02_T1_SR_B4.TIF": "images/test/B4/LC08_L2SP_188012_20240821_20240830_02_T1_SR_B4.TIF"
        },
        "B5": {
            "LC08_L2SP_188011_20240821_20240830_02_T1_SR_B5.TIF": "images/test/B5/LC08_L2SP_188011_20240821_20240830_02_T1_SR_B5.TIF",
            "LC08_L2SP_188012_20240821_20240830_02_T1_SR_B5.TIF": "images/test/B5/LC08_L2SP_188012_20240821_20240830_02_T1_SR_B5.TIF"
        },
    }

    path = "images/test"
<<<<<<< HEAD
    processed_images = ndvi.calculate(downloaded_images, path)
=======
    processed_images = ndvi.test(downloaded_images, path)
>>>>>>> refs/remotes/origin/main

    print(processed_images)

# test_calculate()

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
