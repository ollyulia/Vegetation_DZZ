import api
import config_urls

def upload_raster_layer_with_file(
    uploaded_file_metadata,
    parent_id: int,
    display_name: str,
    srs_id: int
) -> int:
    create_data = {
        "resource": {
            "cls": "raster_layer",
            "display_name": display_name,
            "parent": {"id": parent_id}
        },
        "raster_layer": {
            "source": {
                "id": uploaded_file_metadata["id"],
                "mime_type": uploaded_file_metadata["mime_type"],
                "size": uploaded_file_metadata["size"]
            },
            "srs": {"id": srs_id}
        }
    }
    response = api.create_raster_layer(config_urls.RESOURCE_URL, create_data)

    if response.status_code != 201:
        raise Exception(f"Ошибка при создании растрового слоя: {response.status_code}, {response.text}")

    response = response.json()
    raster_layer_id = response["id"]
    print(f"Растровый слой успешно создан! Id слоя: {raster_layer_id}")

    return raster_layer_id
