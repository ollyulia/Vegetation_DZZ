# Файл для работы с созданием множества точек на векторном слое

import api

def multipoint_coordinates_to_string(coordinates: list):
    coord_strings = [f"{x} {y}" for x, y in coordinates]

    return ", ".join(coord_strings)

def create_multipoint_in_vector_layer(
    vector_layer_url: str,
    srs: int,
    coordinates: str
):
    url = f"{vector_layer_url}?srs={srs}"

    feature_data = {
        "type": "Feature",
        "geom": f"MULTIPOINT ({coordinates})",
    }

    response = api.create_feature(url, feature_data)

    status_code = response.status_code
    if status_code == 200 or status_code == 201:
        print(f"Точки успешно добавлены! {response.text}")
    else:
        print(f"Ошибка загрузки точек: {response.text}")


def test_multipoint_coordinates_to_string():
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
    print(multipoint_coordinates_to_string(coordinates))
