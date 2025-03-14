SRS_3857 = 3857
SRS_4326 = 4326

# id папки проекта
PARENT_ID = 220

BASE_URL = 'https://geo.mauniver.ru/'
RESOURCE_URL = f'{BASE_URL}api/resource/'

# id тестового векторного слоя с точками
MAIN_POINT_VECTOR_LAYER_ID = 435
# id тестового векторного слоя с полигонами
MAIN_POLYGON_VECTOR_LAYER_ID = 436

# основные векторные слои
MAIN_POINT_VECTOR_LAYER_URL = f'{RESOURCE_URL}{MAIN_POINT_VECTOR_LAYER_ID}/feature/'
MAIN_POLYGON_VECTOR_LAYER_URL = f'{RESOURCE_URL}{MAIN_POLYGON_VECTOR_LAYER_ID}/feature/'



# id тестового векторного слоя с точками
TEST_POINT_VECTOR_LAYER_ID = 425
# id тестового векторного слоя с полигонами
TEST_POLYGON_VECTOR_LAYER_ID = 433
# id тестового векторного слоя с множество точек
TEST_MULTIPOINT_VECTOR_LAYER_ID = 441


# тестовые векторные слои
TEST_POINT_VECTOR_LAYER_URL = f'{RESOURCE_URL}{TEST_POINT_VECTOR_LAYER_ID}/feature/'
TEST_POLYGON_VECTOR_LAYER_URL = f'{RESOURCE_URL}{TEST_POLYGON_VECTOR_LAYER_ID}/feature/'
TEST_MULTIPOINT_VECTOR_LAYER_URL = f'{RESOURCE_URL}{TEST_MULTIPOINT_VECTOR_LAYER_ID}/feature/'
