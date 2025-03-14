# API к сервисам спутниковых данных Вега

Сервисы спутниковых данных Вега обеспечивают два основных вида запросов:
1. Поиск снимков
2. Отображение снимков

Для работы со всеми сервисами необходимо передать параметр авторизации &ukey=<ключ>

## Поиск снимков

Пример запроса на поиск снимков:

```
http://sci-vega.ru/fap/toproxy/export/local/smiswms/get_metadata.pl?REQUEST=GetMetadata&BBOX=38.62716004621514,51.356,42.71267395378486,57.304167&height=895&width=1553&dt=2021-02-08&db_pkg_mode=hrsat&dt_from=2021-02-05&limit=150&layers=unisat&satellites=LANDSAT 8&stations=&devices=&products=&max_cloudiness=10&srs=epsg:4326
```

**Изменяемые cgi параметры:**
- ```bbox,srs``` – координаты области в проекции SRS, поддержана epsg нотация (epsg:4326 - значение по умолчанию)
- ```dt,dt_from``` – даты конца и начала интервала, соответственно
- ```satellites,devices,stations``` – идентификаторы спутников, приборов, станций (из справочника, при отсутствии выдаются все доступные данные).
- ```max_cloudiness, min_cloudiness```  - максимальная и минимальная облачность снимка в процентах, опциональные
- ```height``` - ширина окна запроса в пикселях
- ```width``` - высота окна запроса в пикселях
- ```limit``` - размер порции запроса

Базовые продукты в получаемых результатах – ```v_color,v_pan, v_ndvi``` (Цветной, Панхром, NDVI). В результатах можно всегда выбирать продукт по умолчанию (default)

Ответ на запрос поиска метаданных содержит 2 секции ```INFO``` и ```DATA```.
В секции ```INFO``` есть секция ```query``` - он содержит информацию по количеству записей и параметры запроса порции.  
Если парамерт ```INFO->query->next``` имеет значение отличное от **null**, то есть еще следующая порция данных. 
Аналогично параметр ```INFO->query->previous``` - то есть еще предыдущая порция данных. 
Для запроса следующей порции нужно к запросу добавить параметр 
```&next=[значение INFO->query->next]```, аналогично для предыдущей порции ```&previous=[значение INFO->query->previous]```.

Значение ```INFO->query->total_count``` показывает общее число найденных данных.

## Отображение снимков

Для запроса картинки (изображения продукта по сцене) из ответа сервиса поиска снимков необходимо извлечь:

- id, который у каждого продукта и сцены свой (уникальный)
- атрибуты доступа к сервису

Алгоритм следующий:

1) Извлекается из секции ```products``` нужный продукт и его ```ID```, ```SERVER```,
2) Формируется запрос на локальный сервер интерфейсов в формате:
    ```   
    http://sci-vega.ru/fap/toproxy/[SERVER]/local/smiswms/get_map.pl?layers=unisat&unisat_uids=[ID]&db_pkg_mode=hrsat
    ```
   Пример запроса изображения по ```id```:
   
    ```
    http://sci-vega.ru/fap/toproxy/export/local/smiswms/get_map.pl?layers=unisat&db_pkg_mode=hrsat&FORMAT=png&WIDTH=862&HEIGHT=1255&BBOX=38.62716004621514,51.356,42.71267395378486,57.304167&EXCEPTIONS=xml&SERVICE=WMS&REQUEST=GetMap&transparent=1&unisat_uids=2102070811012323270071
    ```
Для отображения сцен в тайловых слоях существует специализированный сервис, поддерживающий кэширование и выделенный пул серверов для параллельного предоставления данных (согласовывается дополнительно)

Ключевые (изменяемые) параметры
- ```bbox,srs``` – координаты области в проекции SRS (epsg:4326 поддерживается, значение по умолчанию)
- ```height``` - ширина окна запроса в пикселях
- ```width``` - высота окна запроса в пикселях
- ```unisat_uids``` – идентификатор сцены (из метаданных)

## Дополнительные запросы
    
1. Запрос всех возможных значений параметров (справочников) - спутники, приборы, станции, продукты:
    ```
    http://sci-vega.ru/fap/toproxy/export/local/smiswms/get_metadata.pl?db_pkg_mode=hrsat&layers=unisat&REQUEST=GetMetadataVariants
    ```
3. Запрос карты покрытия контурами сцен
    ```   
    http://sci-vega.ru/fap/toproxy/export/local/smiswms/get_map.pl?layers=unisat_set_contour&db_pkg_mode=hrsat&FORMAT=png&WIDTH=1553&HEIGHT=895&BBOX=-40.139667,-65.00000126529298,220.139667,85.00000126529298&EXCEPTIONS=xml&SERVICE=WMS&REQUEST=GetMap&transparent=1&unisat_set_contour_products=v_color,v_ndvi&unisat_set_contour_dt=2021-02-08&unisat_set_contour_dt_from=2021-02-05&unisat_max_cloudiness=10
    ```
    Параметры запроса по значениям идентичны параметрам сервиса поиска метаданных. Имена образованы от названия параметра сервиса поиска + префикс unisat_set_contour_

# Полезные ссылки

https://requests.readthedocs.io/en/latest/index.html

https://docs.nextgis.ru/docs_ngweb_dev/doc/developer/toc.html

https://www.qgis.org/
