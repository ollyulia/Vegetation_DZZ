import api
import config_urls
import os

# uploaded file metadata have this shape:
# {
#     "id": "0195a94109009c45abe81a84debf08a5",
#     "mime_type": "image/tiff",
#     "name": "output.tif",
#     "size": 3149175
# }
def upload_file_from_disk(file_path: str, file_name_in_server: str):
    with open(file_path, "rb") as file_content:
        files = {
            #         FileName,  FileContent, FileContentType
            "file": (file_name_in_server, file_content, "image/tiff")
        }
        response = api.upload_file(config_urls.FILE_UPLOAD_URL, files)

    if response.status_code != 200:
        raise Exception(f"Ошибка при загрузке файла: {response.status_code}, {response.text}")

    upload = response.json()["upload_meta"][0]
    print("Файл загружен. Данные: ", upload)

    uploaded_files_path = "data/uploaded_files_ids.txt"

    os.makedirs(os.path.dirname(uploaded_files_path), exist_ok=True)

    # Список id всех загруженных файлов
    with open(uploaded_files_path, "a") as f:
        f.write(f"{upload["id"]}\n")

    return upload

def delete_file_by_id(file_id: str):
    delete_file_url = f"{config_urls.FILE_UPLOAD_URL}{file_id}"

    response = api.delete_file(delete_file_url)

    if response.status_code == 204:
        print("Файл успешно удалён!")
    else:
        print(f"Ошибка при удалении файла: {response.status_code}, {response.text}")

# delete_file_by_id("0195aac9924068da910362faaf30d3de")
