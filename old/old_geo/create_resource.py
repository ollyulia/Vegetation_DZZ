import os
from api import createFireLayer, createGroup, findResource

resId = 0
groupId = 0

res = findResource({"display_name": "fire_complete_dataset"}).json()
if res:
    resId = res[0]['resource']['id']
    groupId = findResource({"display_name": "fire"}).json()[0]['resource']['id']
else:
    groupId = createGroup("fire").json()["id"]
    response = createFireLayer(
        parentId=groupId,
        name="fire_complete_dataset",
    )
    resId = response.json()["id"]

print(resId)
print(groupId)
with open(".env", "a") as f:
    f.write(f"\nRESOURCE_ID={resId}")
    f.write(f"\nNEXTGIS_GROUP_ID={groupId}")
