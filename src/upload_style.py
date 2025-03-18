import config_urls
import api

def create_style_in_layer(
    layer_id: int,
    display_name: str
):
    create_style_data = {
        "resource": {
            "cls": "raster_style",
            "display_name": display_name,
            "parent": {"id": layer_id}
        }
    }

    # Отправка запроса на создание стиля
    response = api.create_resource(config_urls.RESOURCE_URL, create_style_data)

    if response.status_code == 201:
        response = response.json()
        style_id = response["id"]
        print(f"Стиль успешно создан! ID стиля: {style_id}, {response}")
        return style_id
    else:
        raise Exception(f"Ошибка при создании стиля: {response.status_code}, {response.text}")
