import geo_transform
import geo_points as points
import geo_polygons as polygons
import geo_vector_layers as vector_layers
import config_urls
import json

def test_json_reading_and_transformation():
    file = open("src/data/murmankaya_oblast.json", "r")
    content = file.read()
    json_data = json.loads(content)
    file.close()

    coordinates = json_data["coordinates"][0]

    result = geo_transform.list_wgs84_to_web_mercator(coordinates, False)

    string = polygons.polygon_coordinates_to_string(result)

    print(string)

def add_multipoint():
    points.create_points_in_vector_layer(config_urls.TEST_MULTIPOINT_VECTOR_LAYER_URL, config_urls.SRS_3857)

    return

add_multipoint()

# def create_multipoint_layer():
#     vector_layers.create_multipoint_vector_layer(
#         config_urls.RESOURCE_URL,
#         config_urls.PARENT_ID,
#         "test-multipoint-layer",
#         config_urls.SRS_3857,
#         []
#     )

#     return
