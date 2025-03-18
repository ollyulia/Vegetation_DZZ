import api
import config_urls

def upload_new_layer_webmap(
    webmap_id: int,
    raster_layer_id: int,
    raster_layer_style_id: int,
):
    # Шаг 1: Получение текущей конфигурации веб-карты
    GET_WEBMAP_URL = f"{config_urls.RESOURCE_URL}{webmap_id}"
    response = api.get_webmap(GET_WEBMAP_URL)

    if response.status_code != 200:
        raise Exception(f"Ошибка при получении веб-карты: {response.status_code}, {response.text}")

    webmap_config = response.json()

    # Шаг 2: Добавление нового слоя в конфигурацию
    new_layer = {
        "item_type": "layer",
        "display_name": "Test-Raster-Layer-Name",
        "layer_enabled": True,
        "layer_identifiable": True,
        "layer_transparency": None,
        "layer_style_id": raster_layer_style_id,
        "style_parent_id": raster_layer_id,
        "layer_min_scale_denom": None,
        "layer_max_scale_denom": None,
        "layer_adapter": "image",
        "draw_order_position": None,
        "legend_symbols": None,
    }

    # Шаг 3: Добавляем новый слой в массив layers
    layers = webmap_config["webmap"]["root_item"]["children"]
    layers.append(new_layer)

    payload = {"webmap":{"root_item":{"item_type":"root", "children": layers } }}

    response = api.put_new_layer_in_webmap(GET_WEBMAP_URL, payload)

    if response.status_code != 200:
        print(f"Ошибка при обновлении веб-карты: {response.status_code}, {response.text}")

    response = response.json()
    print(f"Слой успешно добавлен на веб-карту! '{response}'")
