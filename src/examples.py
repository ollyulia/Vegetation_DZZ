import config_urls
import geo_points
import geo_multipoints
import geo_polygons

def create_point():
    geo_points.create_point_in_vector_layer(
        config_urls.TEST_POINT_VECTOR_LAYER_URL,
        config_urls.SRS_3857,
        300000,
        300000
    )

    return

def create_polygon():
    coordinates = [
        [
            3528982,
            10844751
        ],
        [
            3503299,
            10718782
        ],
        [
            3785811,
            10628281
        ],
        [
            3832284,
            10808061
        ]
    ]

    geo_polygons.create_polygon_in_vector_layer(
        config_urls.TEST_POLYGON_VECTOR_LAYER_URL,
        config_urls.SRS_3857,
        geo_polygons.polygon_coordinates_to_string(coordinates)
    )

    return

def create_multipoint():
    coordinates = [
        [
            3566524,
            10809315
        ],
        [
            3588538,
            10657664
        ],
        [
            3801338,
            10669894
        ],
        [
            3789108,
            10816653
        ]
    ]

    geo_multipoints.create_multipoint_in_vector_layer(
        config_urls.TEST_MULTIPOINT_VECTOR_LAYER_URL,
        config_urls.SRS_3857,
        geo_multipoints.multipoint_coordinates_to_string(coordinates)
    )

    return

create_multipoint()
