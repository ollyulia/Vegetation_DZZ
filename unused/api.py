# Этот файл предназначен для взаимодействия с API геопортала университета

import requests
from config_secret import *

def create_vector_layer(
    url: str,
    json
):
    response = requests.post(
        url=url,
        json=json,
        auth=AUTH
    )
    return response

def create_feature(
    url: str,
    json
):
    response = requests.post(
        url=url,
        json=json,
        auth=AUTH
    )

    return response

def upload_file(
    file_upload_url: str,
    files
):
    response = requests.post(
        url=file_upload_url,
        files=files,
        auth=AUTH
    )

    return response

def delete_file(file_delete_url: str):
    response = requests.delete(file_delete_url, auth=AUTH)

    return response

def create_resource(
    url: str,
    json
):
    response = requests.post(
        url=url,
        json=json,
        auth=AUTH
    )

    return response

def get_webmap(url: str):
    response = requests.get(url=url, auth=AUTH)

    return response

def put_new_layer_in_webmap(url: str, json):
    response = requests.put(url=url, json=json, auth=AUTH)

    return response

# Example JSON data
# {
#     "resource": {
#         "cls": "raster_layer",
#         "display_name": "Raster layer name",
#         "parent": {"id": number} # parent id
#     },
#     "raster_layer": {
#         "source": {
#             "id": "0eddf759-86d3-4fe0-b0f1-869fe783d2ed",
#             "mime_type": "application/octet-stream",
#             "size": 2299
#         },
#         "srs": {"id": 3857}
#     }
# }
def create_raster_layer(
    url: str,
    json
):
    response = requests.post(
        url=url,
        json=json,
        auth=AUTH
    )

    return response


def create_resource_group(
    url: str,
    json
):
    response = requests.post(
        url=url,
        json=json,
        auth=AUTH
    )

    return response
