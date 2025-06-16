import numpy as np
import os
import rasterio
import tempfile

from contextlib import ExitStack
from pathlib import Path
from rasterio.merge import merge
from rasterio.warp import calculate_default_transform, reproject, Resampling

class Ndvi:
    def __init__(self):
        pass

    def calculate(
        self,
        downloaded_images,
        path,
        NDVI_THRESHOLDS
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

        print("Вычисление NDVI")
        prepared_downloaded_images_data = self._prepare_downloaded_images(downloaded_images)

        print("Разбиение снимка на пороговые значения")
        ndvi_thresholds_images_data = self._create_ndvi_thresholds(
            prepared_downloaded_images_data,
            OUTPUT_NDVI_DIR,
            NDVI_THRESHOLDS
        )

        print("Объединение снимков по пороговым значениям")
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

        Возвращает `combined_files`:
        ```
        {
            "0.2": [
                "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_combined/combined_threshold_20_part1.tif",
                "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_combined/combined_threshold_20_part2.tif"
            ]
            "0.3": [
                "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_combined/combined_threshold_30_part1.tif",
                "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_combined/combined_threshold_30_part2.tif"
            ],
            "0.4": [
                "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_combined/combined_threshold_40_part1.tif",
                "images/2025-05-17/2024-08-15_2024-08-20_x1:y1_x2:y2/ndvi_combined/combined_threshold_40_part2.tif"
            ]
        }
        ```
        '''
        files_per_combined = 2
        combined_files = {}

        os.makedirs(OUTPUT_COMBINED_DIR, exist_ok=True)

        for threshold, files_dict in ndvi_thresholds_images_data.items():
            file_paths = list(files_dict.values())
            combined_files[threshold] = []

            for i in range(0, len(file_paths), files_per_combined):
                group = file_paths[i:i+files_per_combined]
                if not group:
                    continue

                output_filename = f"combined_threshold_{int(float(threshold)*100)}_part{i//files_per_combined+1}.tif"
                output_path = os.path.join(OUTPUT_COMBINED_DIR, output_filename)
                print(f"Объединение {output_path}")

                try:
                    self.merge_tiffs(group, output_path, compress=True)
                    combined_files[threshold].append(output_path)
                except Exception as e:
                    print(f"Ошибка при объединении файлов {group}: {e}")
                    continue

        return combined_files

    def merge_tiffs(self, input_paths, output_path, compress=True):
        """
        Объединяет несколько TIFF-файлов в один с возможностью сжатия.

        Args:
            input_paths (list): Список путей к входным файлам
            output_path (str): Путь для сохранения объединенного файла
            compress (bool): Применять ли сжатие к выходному файлу
        """
        # Используем ExitStack для управления контекстами файлов
        with ExitStack() as stack:
            src_files = []
            reprojected_files = []

            # Открываем все исходные файлы
            for path in input_paths:
                src = stack.enter_context(rasterio.open(path))
                src_files.append(src)

            # Определяем целевой CRS (берем первый файл как эталон)
            target_crs = src_files[0].crs

            # Подготовка файлов для объединения
            files_to_merge = []

            for src in src_files:
                if src.crs == target_crs:
                    files_to_merge.append(src)
                else:
                    # Репроектируем в целевой CRS
                    transform, width, height = calculate_default_transform(
                        src.crs, target_crs, src.width, src.height, *src.bounds)

                    # Создаем временный файл для репроекции
                    tmpfile = tempfile.NamedTemporaryFile(suffix='.tif', delete=False)
                    tmpfile.close()
                    reprojected_path = tmpfile.name
                    reprojected_files.append(reprojected_path)  # Запоминаем для удаления

                    kwargs = src.meta.copy()
                    kwargs.update({
                        'crs': target_crs,
                        'transform': transform,
                        'width': width,
                        'height': height
                    })

                    with rasterio.open(reprojected_path, 'w', **kwargs) as dst:
                        for band in range(1, src.count + 1):
                            reproject(
                                source=rasterio.band(src, band),
                                destination=rasterio.band(dst, band),
                                src_transform=src.transform,
                                src_crs=src.crs,
                                dst_transform=transform,
                                dst_crs=target_crs,
                                resampling=Resampling.nearest)

                    # Открываем репроектированный файл
                    reprojected_src = stack.enter_context(rasterio.open(reprojected_path))
                    files_to_merge.append(reprojected_src)

            # Объединяем все файлы
            mosaic, out_trans = merge(files_to_merge)

            # Параметры сжатия
            compress_opts = {
                'compress': 'DEFLATE',
                'predictor': 2,  # Для float-данных лучше использовать predictor=2
                'zlevel': 6,     # Уровень компрессии (1-9)
                'num_threads': 'ALL_CPUS'  # Использовать все ядра для сжатия
            } if compress else {}

            # Сохраняем объединенный файл
            out_meta = files_to_merge[0].meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "height": mosaic.shape[1],
                "width": mosaic.shape[2],
                "transform": out_trans,
                "crs": target_crs,
                **compress_opts  # Добавляем параметры сжатия
            })

            with rasterio.open(output_path, "w", **out_meta) as dest:
                dest.write(mosaic)

        # Удаляем временные файлы после использования
        for path in reprojected_files:
            try:
                os.unlink(path)
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
