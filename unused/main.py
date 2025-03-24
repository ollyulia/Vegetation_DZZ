import config_urls
import geo_vector_layers

# 67.065293 35.128784
# 67.724026 39.852905
# {"filterType": "mbr","lowerLeft": {"latitude": "35.128784","longitude": "67.065293"},"upperRight": {"latitude": "67.724026", "longitude": "39.852905"}}
def create_main_vector_layers():
    geo_vector_layers.create_point_vector_layer(
        config_urls.RESOURCE_URL,
        config_urls.PARENT_ID,
        "main-point-layer",
        config_urls.SRS_3857,
        []
    )

    geo_vector_layers.create_polygon_vector_layer(
        config_urls.RESOURCE_URL,
        config_urls.PARENT_ID,
        "main-polygon-layer",
        config_urls.SRS_3857,
        []
    )

    return
