import api

def polygon_coordinates_to_string(coordinates: list):
    if len(coordinates) < 3:
        raise ValueError("Координаты должны содержать как минимум 3 точки для создания полигона.")

    if coordinates[0] != coordinates[-1]:
        coordinates.append(coordinates[0]) # Замыкаем полигон

    coord_strings = [f"{x} {y}" for x, y in coordinates]

    return ", ".join(coord_strings)

def test_polygon_coordinates_to_string():
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
    print(polygon_coordinates_to_string(coordinates))

# Координаты в формате: 30 10, 40 40, 20 40, 10 20, 30 10
def create_polygon_in_vector_layer(
    vector_layer_url: str,
    srs: int,
    coordinates: str,
):
    url = f"{vector_layer_url}?srs={srs}"

    feature_data = {
        "type": "Feature",
        "geom": f"POLYGON (({coordinates}))",
    }

    response = api.create_feature(url, feature_data)

    status_code = response.status_code
    if status_code == 200 or status_code == 201:
        print(f"Полигон успешно добавлен! '{response.text}'")
    else:
        print(f"Ошибка загрузки полигона: '{response.text}'")
