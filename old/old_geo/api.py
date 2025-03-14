import os
import requests

HOST = os.getenv("NEXTGIS_URL", "localhost:8080")
AUTH = (os.getenv("NEXTGIS_USER", "administrator"), os.getenv("NEXTGIS_PASSWORD", "admin"))

def addFeature(resId: int, feature: dict):
    return requests.post(
        url=f"{HOST}/api/resource/{resId}/feature/?src=4326",
        json=feature,
        
    )

def addFeatures(resId: int, features: list):
    return requests.patch(
            url=f"{HOST}/api/resource/{resId}/feature/?src=4326",
            json=features,
            auth=AUTH
        )

def createGroup(name: str, description="", parentId=0):
     return requests.post(
        url=f"{HOST}/api/resource/",
        json={
            "resource": {
                "cls":"resource_group",
                "parent":{
                    "id":parentId
                },
                "display_name": name,
                "description": description,
            }
        },
        auth=AUTH
    )

def createResource(parentId: int, 
                   name: str,
                   geometry_type: str,
                   fields: list,
                   srs: int = 4326,
                   description: str = ""):
    return requests.post(
        url=f"{HOST}/api/resource/",
        json={
            "resource":{
                "cls":"vector_layer",
                "parent":{
                    "id":parentId
                },
                "display_name": name,
                "description": description,
            },
            "vector_layer":{
                "srs":{ "id": srs },
                "geometry_type": geometry_type,
                "fields": fields,
            }
        },
        auth=AUTH
    )

def createFireLayer(parentId: int, name: str, srs: int = 4326):
    return createResource(
        parentId=parentId,
        name=name,
        geometry_type="POINT",
        fields=[
            {
                "keyname": os.getenv("DATE_FIELD", "date"),
                "display_name": os.getenv("DATE_FIELD", "date"),
                "datatype": "DATE"
            },
            
            {
                "keyname": os.getenv("TIME_FIELD", "time"),
                "display_name": os.getenv("TIME_FIELD", "time"),
                "datatype": "TIME"
            },
        ],
        srs=srs
    )

def findResource(searchParams: dict):
    return requests.get(
        url=f"{HOST}/api/resource/search/",
        params=searchParams,
        auth=AUTH
    )

