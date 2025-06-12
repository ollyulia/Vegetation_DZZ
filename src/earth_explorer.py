import datetime
import json
import re
import requests
import sys
import threading
import time

from pathlib import Path

class EarthExplorer:
    def __init__(self, username: str, token: str):
        self._username = username
        self._token = token

    def download_images_by_coordinates(
            self,
            start_date: str,
            end_date: str,
            lower_left_latitude: float,
            lower_left_longitude: float,
            upper_right_latitude: float,
            upper_right_longitude: float,
            path: str,
        ):

        downloaded_images = {
            "B4": {},
            "B5": {},
            "other": {},
        }

        # необходимые band со спутника для расчета ndvi
        SR_B4 = "SR_B4"
        SR_B5 = "SR_B5"

        B4_OUTPUT_PATH = f"{path}/B4"
        B5_OUTPUT_PATH = f"{path}/B5"
        OTHER_OUTPUT_PATH = f"{path}/other"

        Path(B4_OUTPUT_PATH).mkdir(parents=True, exist_ok=True)
        Path(B5_OUTPUT_PATH).mkdir(parents=True, exist_ok=True)
        Path(OTHER_OUTPUT_PATH).mkdir(parents=True, exist_ok=True)

        maxthreads = 5 # Количество потоков для загрузки
        sema = threading.Semaphore(value=maxthreads)
        label = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        threads = []

        # отправка http запроса
        def sendRequest(url, data, api_key=None):
            pos = url.rfind('/') + 1
            endpoint = url[pos:]

            json_data = json.dumps(data)

            if api_key is None:
                response = requests.post(url, json_data)
            else:
                headers = {"X-Auth-Token": api_key}
                response = requests.post(url, json_data, headers = headers)

            try:
                http_status_code = response.status_code
                if response is None:
                    print("Нет выходных данных из ответа")
                    sys.exit()
                output = json.loads(response.text)
                if output["errorCode"] is not None:
                    print("Неудачный запрос. ID: ", output["requestId"])
                    print(output["errorCode"], "-", output["errorMessage"])
                    sys.exit()
                if http_status_code == 404:
                    print("404 Not Found")
                    sys.exit()
                elif http_status_code == 401:
                    print("401 Unauthorized")
                    sys.exit()
                elif http_status_code == 400:
                    print("Error Code", http_status_code)
                    sys.exit()
            except Exception as e:
                response.close()
                pos = serviceUrl.find("api")
                print(
                    f"Ошибка при парсинге запроса к {endpoint}. Перепроверьте входные данные: {json_data}. Примеры входных данных можно найти: {url[:pos]}api/docs/reference/#{endpoint}"
                )
                sys.exit()
            response.close()
            print(f"Завершен запрос к {endpoint} с ID = {output["requestId"]}")

            return output["data"]

        def downloadFile(url):
            sema.acquire()
            try:
                response = requests.get(url, stream=True)
                disposition = response.headers["content-disposition"]
                filename = re.findall("filename=(.+)", disposition)[0].strip("\"")
                print(f"    Загрузка файла: '{filename}' ...\n")

                if SR_B4 in filename:
                    full_path = f"{B4_OUTPUT_PATH}/{filename}"

                    downloaded_images["B4"][filename] = full_path
                elif SR_B5 in filename:
                    full_path = f"{B5_OUTPUT_PATH}/{filename}"

                    downloaded_images["B5"][filename] = full_path
                else:
                    full_path = f"{OTHER_OUTPUT_PATH}/{filename}"

                    downloaded_images["other"][filename] = full_path

                open(full_path, "wb").write(response.content)
                print(f"    Файл загружен: {filename}\n")

                sema.release()
            except Exception as e:
                print(f"Не удалось скачать файл по адресу: {url}. Ошибка: {e}. Попытка скачать файл ещё раз.")
                sema.release()
                runDownload(threads, url)

        def runDownload(threads, url):
            thread = threading.Thread(target=downloadFile, args=(url,))
            threads.append(thread)
            thread.start()

        username = self._username
        token = self._token

        print("Запуск скачивания снимков...")

        serviceUrl = "https://m2m.cr.usgs.gov/api/api/json/stable/"
        login_payload = {"username" : username, "token" : token}

        print("Авторизация...")
        apiKey = sendRequest(serviceUrl + "login-token", login_payload)
        print("API ключ: успех")

        datasetName = "landsat_ot_c2_l2" # gls_all / landsat_ot_c2_l2 / landsat_ot_c2_l1 / landsat_band_files_c2_l1 / lsr_nadsat_etm_c1 /

        spatialFilter = {
            "filterType": "mbr",
            "lowerLeft": {
                "latitude": lower_left_latitude,
                "longitude": lower_left_longitude
            },
            "upperRight": {
                "latitude": upper_right_latitude,
                "longitude": upper_right_longitude
            }
        }

        temporalFilter = {
            "start": start_date,
            "end": end_date
        }

        cloudCoverFilter = {'min' : 0, 'max' : 60}

        search_payload = {
            "datasetName" : datasetName,
            "sceneFilter" : {
                "spatialFilter" : spatialFilter,
                "acquisitionFilter" : temporalFilter,
                'cloudCoverFilter' : cloudCoverFilter
            }
        }

        # def dump_json(value, name):
        #     with open(f"data/debug/band_{name}.json", 'w') as file:
        #         json.dump(value, file, indent=4)

        print("\nПодготовка к загрузке снимков.")
        print("Поиск сцен...")
        scenes = sendRequest(serviceUrl + "scene-search", search_payload, apiKey)

        # dump_json(scenes, "1_scenes")

        bandNames = {SR_B4, SR_B5}

        if scenes["recordsReturned"] > 0:
            print(f"Найдено {scenes["recordsReturned"]} подходящих сцен")

            sceneIds = []
            for result in scenes['results']:
                # Добавление этой сцены в список для загрузки
                sceneIds.append(result['entityId'])

            payload = {
                'datasetName': datasetName,
                'entityIds': sceneIds
            }

            products = sendRequest(serviceUrl + "download-options", payload, apiKey)

            # dump_json(products, "2_products")

            downloads = []
            for product in products:
                # Make sure the product is available for this scene
                if product['available']:
                    if product["secondaryDownloads"] is not None and len(product["secondaryDownloads"]) > 0:
                        for secondaryDownload in product["secondaryDownloads"]:
                            for bandName in bandNames:
                                if secondaryDownload["bulkAvailable"] and bandName in secondaryDownload["displayId"]:
                                    downloads.append(
                                        {
                                            "entityId": secondaryDownload["entityId"],
                                            "productId": secondaryDownload["id"]
                                        }
                                    )

            if downloads:
                requestedDownloadsCount = len(downloads)
                download_req_payload = {
                    "downloads": downloads,
                    "label": label
                }

                requestResults = sendRequest(serviceUrl + "download-request", download_req_payload, apiKey)

                print(f"Обнаружено подходящих файлов для скачивания {len(requestResults["availableDownloads"])}")

                # dump_json(requestResults, "3_request_results")

                # В PreparingDownloads есть действующая ссылка, которую можно использовать, но данные могут быть доступны не сразу
                # Вызовите метод download-retrieve, чтобы получить загрузку, доступную для немедленного скачивания
                if requestResults['preparingDownloads'] is not None and len(requestResults['preparingDownloads']) > 0:
                    payload = {'label': label}
                    moreDownloadUrls = sendRequest(serviceUrl + "download-retrieve", payload, apiKey)

                    # dump_json(moreDownloadUrls, f"5_more_download_urls")

                    downloadIds = []

                    for download in moreDownloadUrls['available']:
                        if str(download['downloadId']) in requestResults['newRecords'] or str(download['downloadId']) in \
                                requestResults['duplicateProducts']:
                            downloadIds.append(download['downloadId'])
                            runDownload(threads, download['url'])

                    for download in moreDownloadUrls['requested']:
                        if str(download['downloadId']) in requestResults['newRecords'] or str(download['downloadId']) in \
                                requestResults['duplicateProducts']:
                            downloadIds.append(download['downloadId'])
                            runDownload(threads, download['url'])

                    # Если вы не получили все повторно загруженные файлы, вызовите метод загрузки-извлечения еще раз, через 30 секунд
                    while len(downloadIds) < (requestedDownloadsCount - len(requestResults['failed'])):
                        preparingDownloads = requestedDownloadsCount - len(downloadIds) - len(requestResults['failed'])
                        print("\n", preparingDownloads, "загрузок недоступно. Следующая попытка через 30 секунд...")
                        time.sleep(30)
                        print("Попытка получить данные")
                        moreDownloadUrls = sendRequest(serviceUrl + "download-retrieve", payload, apiKey)
                        for download in moreDownloadUrls['available']:
                            if download['downloadId'] not in downloadIds and (
                                    str(download['downloadId']) in requestResults['newRecords'] or str(
                                    download['downloadId']) in requestResults['duplicateProducts']):
                                downloadIds.append(download['downloadId'])
                                runDownload(threads, download['url'])

                else:
                    # Get all available downloads
                    for download in requestResults['availableDownloads']:
                        runDownload(threads, download['url'])
        else:
            print("Поиск не дал результатов.")

        if threads:
            print("Загрузка файлов... Пожалуйста, не закрывайте программу.")

            for thread in threads:
                thread.join()

            print("Загрузка завершена")
        else:
            print("Не найдено файлов для скачивания.")

        # Выйдите из системы, чтобы больше нельзя было использовать API-ключ
        endpoint = "logout"
        if sendRequest(serviceUrl + endpoint, None, apiKey) is None:
            print("Успешный выход из EarthExplorer\n")
        else:
            print("Неуспешный выход из EarthExplorer\n")

        return downloaded_images
