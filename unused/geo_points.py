# Файл для работы с созданием точки на векторном слое

import api

def create_point_in_vector_layer(
    vector_url: str,
    srs: int,
    x: int,
    y: int
):
    url = f"{vector_url}?srs={srs}"

    feature_data = {
        "type": "Feature",
        "geom": f"POINT ({x} {y})",
    }

    response = api.create_feature(url, feature_data)

    status_code = response.status_code
    if status_code == 200 or status_code == 201:
        print(f"Точка успешно добавлена! {response.text}")
    else:
        print(f"Ошибка загрузки точки: {response.text}")
