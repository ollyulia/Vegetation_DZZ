# Файл для работы с созданием группы ресурсов

import api
import config_urls

def create_resource_group(display_name: str, description: str):
    resouce_url = config_urls.RESOURCE_URL
    json = {
        "resource": {
            "cls": "resource_group",
            "parent": {
                "id": config_urls.PARENT_ID
            },
            "display_name": display_name,
            "description": description,
        }
    }

    response = api.create_resource_group(resouce_url, json)

    status_code = response.status_code
    if status_code == 200 or status_code == 201:
        print(f"Группа ресурсов успешно создана! '{response.text}'")
    else:
        print(f"Ошибка создания группы ресурсов: '{response.text}'")

create_resource_group("test-resource-group", "test-description")
