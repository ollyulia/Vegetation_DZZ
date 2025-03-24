# Скрипт для создания полигона около Мурманской области

import geo_polygons
import geo_transform
import config_urls
import json

def add_murmanskaya_oblast_polygon():
    file = open("data/murmankaya_oblast.json", "r")
    content = file.read()
    json_data = json.loads(content)
    file.close()

    coordinates = json_data["coordinates"][0]

    transformed_coordinates = geo_transform.list_wgs84_to_web_mercator(coordinates)

    geo_polygons.create_polygon_in_vector_layer(
        config_urls.MAIN_POLYGON_VECTOR_LAYER_URL,
        config_urls.SRS_3857,
        geo_polygons.polygon_coordinates_to_string(transformed_coordinates)
    )

    return

# add_murmanskaya_oblast_polygon()
