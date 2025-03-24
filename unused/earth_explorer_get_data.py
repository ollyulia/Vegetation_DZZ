import datetime
import json  # Работает, задать область поиска, проверить название спутника, выбрать даты
import re
import sys
import threading
import time
import requests

path = "images/downloaded"  # Путь для загрузки файлов
maxthreads = 5  # Количество потоков для загрузки
sema = threading.Semaphore(value=maxthreads)
label = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
threads = []


# отправка http запроса
def send_request(url, data, apikey=None):
    pos = url.rfind("/") + 1
    endpoint = url[pos:]
    json_data = json.dumps(data)

    if apikey is None:
        response = requests.post(url, json_data)
    else:
        headers = {"X-Auth-Token": apikey}
        response = requests.post(url, json_data, headers=headers)

    try:
        http_status_code = response.status_code
        if response is None:
            print("No output from service")
            sys.exit()
        output = json.loads(response.text)
        if output["errorCode"] is not None:
            print("Failed Request ID", output["requestId"])
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
            f"Failed to parse request {endpoint} response. Re-check the input {json_data}. The input examples can be found at {url[:pos]}api/docs/reference/#{endpoint}\n")
        sys.exit()
    response.close()
    print(f"Finished request {endpoint} with request ID {output["requestId"]}\n")

    return output["data"]


def download_file(url):
    #max_attempts = 5
    #attempt = 0
    # while attempt < max_attempts:
    #     try:
    #         # Попытка загрузки файла
    #         runDownload(url)
    #         print("Загрузка завершена успешно.")
    #         break  # Выход из цикла, если загрузка успешна
    #     except Exception as e:
    #         attempt += 1
    #         print(f"Ошибка при загрузке: {e}. Попытка {attempt} из {max_attempts}.")
    #
    #         if attempt < max_attempts:
    #             # Можете сделать паузу перед следующей попыткой
    #             time.sleep(2)  # Задержка в 2 секунды перед повторной попыткой
    #         else:
    #             print("Все попытки загрузки исчерпаны.")
    sema.acquire()
    global path
    try:
        response = requests.get(url, stream=True)
        disposition = response.headers['content-disposition']
        filename = re.findall("filename=(.+)", disposition)[0].strip("\"")
        print(f"Downloading {filename} ...\n")
        if path != "" and path[-1] != "/":
            filename = "/" + filename
        open(path + filename, 'wb').write(response.content)
        print(f"Downloaded {filename}\n")
        sema.release()
    except Exception as e:
        print(f"Failed to download from {url}. {e}. Will try to re-download.")
        sema.release()
        run_download(threads, url)


def run_download(threads, url):
    thread = threading.Thread(target=download_file, args=(url,))
    threads.append(thread)
    thread.start()


def dump_json(value, name):
    with open(f"data/debug/common_{name}.json", 'w') as file:
        json.dump(value, file, indent=4)


if __name__ == '__main__':

    with open('config.json') as config_file:
        config = json.load(config_file)

    username = config['ERS_USERNAME']
    token = config['ERS_TOKEN']


    print("\nRunning Scripts...\n")

    serviceUrl = "https://m2m.cr.usgs.gov/api/api/json/stable/"

    # login-token
    payload = {'username': username, 'token': token}

    apiKey = send_request(serviceUrl + "login-token", payload)

    #print("API Key: " + apiKey + "\n")
    print('API KEY: TRUE'+'\n')

    datasetName = "landsat_ot_c2_l2" #????????? gls_all / landsat_band_files_c2_l1 / landsat_ot_c2_l1 / lsr_nadsat_etm_c1 /

    # Безуспешная попытка задания полигона в качестве области запроса
    # spatialFilter = {
    #     'filterType': "geojson",
    #     "geojson": {
    #         "type": "Polygon",
    #         "coordinates": [
    #             [
    #                 [-120.0, 30.0],
    #                 [-120.0, 40.0],
    #                 [-110.0, 40.0],
    #                 [-110.0, 30.0],
    #                 [-120.0, 30.0]
    #             ]
    #         ]
    #     }
    # }
    # 68.814676, 31.931682
    # 69.214024, 34.293742
    spatialFilter = {
        'filterType': "mbr",
        'lowerLeft': {
            'latitude': 68.57,
            'longitude': 33.03
        },
        'upperRight': {
            'latitude': 68.58,
            'longitude': 33.07
        }
    }

    temporalFilter = {'start': '2024-07-14', 'end': '2024-07-24'}

    payload = {'datasetName': datasetName,
               'spatialFilter': spatialFilter,
               'temporalFilter': temporalFilter}

    print("Searching datasets...\n")
    datasets = send_request(serviceUrl + "dataset-search", payload, apiKey)

    dump_json(datasets, "1_datasets")

    print("Found ", len(datasets), " datasets\n")

    count = 1

    # download datasets
    for dataset in datasets:

        # Поскольку я запускал это раньше, я знаю, что мне нужен GLS_ALL, я не хочу загружать то, что мне не нужно
        # поэтому мы пропустим любые другие наборы данных, которые могут быть найдены, и запишем их в журнал, если я захочу их просмотреть
        # загрузка этих данных в будущем.
        if dataset['datasetAlias'] != datasetName:
            print("Found dataset " + dataset['collectionName'] + " but skipping it.\n")
            continue

        # Я не хочу ограничивать свои результаты, но, используя запрос "dataset-filters request", вы можете
        # найти дополнительные фильтры

        acquisitionFilter = {
            "start": "2024-07-14",
            "end": "2024-07-24"
        }

        payload = {'datasetName': dataset['datasetAlias'],
                   'maxResults': 2,
                   'startingNumber': 1,
                   'sceneFilter': {
                       'spatialFilter': spatialFilter,
                       'acquisitionFilter': acquisitionFilter}}

        # Теперь нужно запустить поиск по сцене, чтобы найти данные для загрузки
        print("Searching scenes...\n\n")

        scenes = send_request(serviceUrl + "scene-search", payload, apiKey)

        dump_json(scenes, f"2_scenes_{count}")

        # Что-то нашлось?
        if scenes['recordsReturned'] > 0:
            # Объединение списка идентификаторов сцен
            sceneIds = []
            for result in scenes['results']:
                # Добавление этой сцены в список для загрузки
                sceneIds.append(result['entityId'])

            # Найдите варианты загрузки этих сцен
            # ПРИМЕЧАНИЕ: Помните, что список сцен не может превышать 50 000 элементов!
            payload = {'datasetName': dataset['datasetAlias'], 'entityIds': sceneIds}

            downloadOptions = send_request(serviceUrl + "download-options", payload, apiKey)

            dump_json(downloadOptions, f"3_download_options_{count}")

            # Aggregate a list of available products
            downloads = []
            for product in downloadOptions:
                # Make sure the product is available for this scene
                if product['available']:
                    downloads.append(
                        {
                            'entityId': product['entityId'],
                            'productId': product['id']
                        }
                    )

            # Did we find products?
            if downloads:
                requestedDownloadsCount = len(downloads)
                # set a label for the download request
                label = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")  # Customized label using date time
                payload = {
                    'downloads': downloads,
                    'label': label
                }
                # Call the download to get the direct download urls
                requestResults = send_request(serviceUrl + "download-request", payload, apiKey)

                dump_json(requestResults, f"4_request_results_{count}")

                # В PreparingDownloads есть действующая ссылка, которую можно использовать, но данные могут быть доступны не сразу
                # Вызовите метод download-retrieve, чтобы получить загрузку, доступную для немедленного скачивания
                if requestResults['preparingDownloads'] is not None and len(requestResults['preparingDownloads']) > 0:
                    payload = {'label': label}
                    moreDownloadUrls = send_request(serviceUrl + "download-retrieve", payload, apiKey)

                    dump_json(moreDownloadUrls, f"5_more_download_urls_{count}")

                    downloadIds = []

                    for download in moreDownloadUrls['available']:
                        if str(download['downloadId']) in requestResults['newRecords'] or str(download['downloadId']) in \
                                requestResults['duplicateProducts']:
                            downloadIds.append(download['downloadId'])
                            run_download(threads, download['url'])

                    for download in moreDownloadUrls['requested']:
                        if str(download['downloadId']) in requestResults['newRecords'] or str(download['downloadId']) in \
                                requestResults['duplicateProducts']:
                            downloadIds.append(download['downloadId'])
                            run_download(threads, download['url'])

                    # Если вы не получили все повторно загруженные файлы, вызовите метод загрузки-извлечения еще раз, через 30 секунд
                    while len(downloadIds) < (requestedDownloadsCount - len(requestResults['failed'])):
                        preparingDownloads = requestedDownloadsCount - len(downloadIds) - len(requestResults['failed'])
                        print("\n", preparingDownloads, "downloads are not available. Waiting for 30 seconds.\n")
                        time.sleep(30)
                        print("Trying to retrieve data\n")
                        moreDownloadUrls = send_request(serviceUrl + "download-retrieve", payload, apiKey)
                        for download in moreDownloadUrls['available']:
                            if download['downloadId'] not in downloadIds and (
                                    str(download['downloadId']) in requestResults['newRecords'] or str(
                                    download['downloadId']) in requestResults['duplicateProducts']):
                                downloadIds.append(download['downloadId'])
                                run_download(threads, download['url'])

                else:
                    # Get all available downloads
                    for download in requestResults['availableDownloads']:
                        run_download(threads, download['url'])
        else:
            print("Search found no results.\n")

    print("Downloading files... Please do not close the program\n")
    for thread in threads:
        thread.join()

    print("Complete Downloading")

    # Выйдите из системы, чтобы больше нельзя было использовать API-ключ
    endpoint = "logout"
    if send_request(serviceUrl + endpoint, None, apiKey) is None:
        print("Logged Out\n\n")
    else:
        print("Logout Failed\n\n")
