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



def create_resource_group(url,parentID,display_name,description):
    r = requests.post(
        url=url,
        json={
            "resource": {
                "cls": "resource_group",
                "parent": {
                    "id": parentID
                },
                "display_name": display_name,
                "description": description,
            }
        },
        auth=AUTH
    )
    return r
