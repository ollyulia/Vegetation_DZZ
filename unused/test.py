import geo_transform
import geo_multipoints
import geo_polygons
import geo_vector_layers
import config_urls
import json
import traceback

from datetime import datetime

def test_json_reading_and_transformation():
    file = open("src/data/murmankaya_oblast.json", "r")
    content = file.read()
    json_data = json.loads(content)
    file.close()

    coordinates = json_data["coordinates"][0]

    result = geo_transform.list_wgs84_to_web_mercator(coordinates, False)

    string = geo_polygons.polygon_coordinates_to_string(result)

    print(string)

def add_multipoint():
    geo_multipoints.create_multipoint_in_vector_layer(config_urls.TEST_MULTIPOINT_VECTOR_LAYER_URL, config_urls.SRS_3857)

    return


def test():
    downloaded_images = {
        "B4": [
            "LC08_L2SP_183012_20240802_20240808_02_T2_SR_B4.TIF",
            "LC08_L2SP_183013_20240802_20240808_02_T1_SR_B4.TIF",
            "LC09_L2SP_184012_20240801_20240802_02_T1_SR_B4.TIF",
            "LC09_L2SP_184013_20240801_20240802_02_T2_SR_B4.TIF"
        ],
        "B5": [
            "LC08_L2SP_183012_20240802_20240808_02_T2_SR_B5.TIF",
            "LC08_L2SP_183013_20240802_20240808_02_T1_SR_B5.TIF",
            "LC09_L2SP_184012_20240801_20240802_02_T1_SR_B5.TIF",
            "LC09_L2SP_184013_20240801_20240802_02_T2_SR_B5.TIF"
        ],
    }

    # B4
    # LC08_L2SP_183012_20240802_20240808_02_T2_SR_B4.TIF
    # LC08_L2SP_183013_20240802_20240808_02_T1_SR_B4.TIF
    # LC09_L2SP_184012_20240801_20240802_02_T1_SR_B4.TIF
    # LC09_L2SP_184013_20240801_20240802_02_T2_SR_B4.TIF

    # B5
    # LC08_L2SP_183012_20240802_20240808_02_T2_SR_B5.TIF
    # LC08_L2SP_183013_20240802_20240808_02_T1_SR_B5.TIF
    # LC09_L2SP_184012_20240801_20240802_02_T1_SR_B5.TIF
    # LC09_L2SP_184013_20240801_20240802_02_T2_SR_B5.TIF

    b4_files = downloaded_images["B4"]
    b5_files = downloaded_images["B5"]

    for b4_file in b4_files:
        expected_b5_file = b4_file.replace("B4", "B5")

        file_name = b4_file.split("_SR_B4.TIF")[0]

        print(file_name)

        if expected_b5_file in b5_files:
            print(f"B4: {b4_file}\nB5: {expected_b5_file}\n")
        else:
            print(f"  Found B4: {b4_file}\nMissing B5: {expected_b5_file}\n")




def test2():
    x = {
        "mare": 1,
        "asd": "dasd"
    }

    y = {
        "mare": 2,
        "qwe": "pfdo"
    }

    print(x.get("mare"))

    for key, value in x.items():
        print(f"{key}: {value}")
        if key in y:
            print(f"{key} in y")
        else:
            print(f"{key} not in y")

    print(len(x))

# test2()

def test3():
    try:
        try:
            [][3]
        except Exception as exception:
            print("Inner exception")
            raise exception

    except Exception as exception:
        print(f"Outer exception: {exception}\n{traceback.format_exc()}")

        return
