import api

def create_point_vector_layer(
    resource_url: str,
    parent_id: int,
    display_name: str,
    srs: int,
    fields: list,
):
    json = {
        "resource": {
            "cls": "vector_layer",
            "parent": {
                "id": parent_id
            },
            "display_name": display_name,
        },
        "vector_layer": {
            "srs": {
                "id": srs
            },
            "geometry_type": "POINT",
            "fields": fields,
        }
    }

    response = api.create_vector_layer(
        resource_url,
        json
    )

    status_code = response.status_code
    if status_code == 200 or status_code == 201:
        print(f"Векторный слой для точек успешно создан! '{response.text}'")
    else:
        print(f"Ошибка создания векторного слоя для точек: '{response.text}'")

def create_polygon_vector_layer(
    resource_url: str,
    parent_id: int,
    display_name: str,
    srs: int,
    fields: list,
):
    json = {
        "resource": {
            "cls": "vector_layer",
            "parent": {
                "id": parent_id
            },
            "display_name": display_name,
        },
        "vector_layer": {
            "srs": {
                "id": srs
            },
            "geometry_type": "POLYGON",
            "fields": fields,
        }
    }

    response = api.create_vector_layer(
        resource_url,
        json
    )

    status_code = response.status_code
    if status_code == 200 or status_code == 201:
        print(f"Векторный слой для полигонов успешно создан! '{response.text}'")
    else:
        print(f"Ошибка создания векторного слоя для полигонов: '{response.text}'")


def create_multipoint_vector_layer(
    resource_url: str,
    parent_id: int,
    display_name: str,
    srs: int,
    fields: list,
):
    json = {
        "resource": {
            "cls": "vector_layer",
            "parent": {
                "id": parent_id
            },
            "display_name": display_name,
        },
        "vector_layer": {
            "srs": {
                "id": srs
            },
            "geometry_type": "MULTIPOINT",
            "fields": fields,
        }
    }

    response = api.create_vector_layer(
        resource_url,
        json
    )

    status_code = response.status_code
    if status_code == 200 or status_code == 201:
        print(f"Векторный слой для множества точек успешно создан! '{response.text}'")
    else:
        print(f"Ошибка создания векторного слоя для множества точек: '{response.text}'")


# fields: list = [
# {
#     "keyname": "name",
#     "display_name": "Name",
#     "datatype": "STRING"
# },
# {
#     "keyname": "description",
#     "display_name": "Description",
#     "datatype": "STRING"
# }
# ]
