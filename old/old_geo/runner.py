import os
import sys
from datetime import datetime, timedelta
from api import addFeatures, createFireLayer
from pyproj import Transformer

SRC_MERCATOR = 3857
SRC_DEFAULT = 4326
TRANSFORMER = Transformer.from_crs(SRC_DEFAULT, SRC_MERCATOR)

def json_feature(date: datetime, coords):
    return {
        "fields": {
            os.getenv("DATE_FIELD", "date"): {
                "year": date.year,
                "month": date.month,
                "day": date.day,
            },
            os.getenv("TIME_FIELD", "time"): {
                "hour": date.hour,
                "minute": date.minute,
                "second": date.second
            }
        },
        "geom": f"POINT ({coords[0]} {coords[1]})"
    }

def read_files(start_date, end_date):
    end_date = end_date + timedelta(days=1)
    DIR_PATH = os.getenv("PATH_DIR", "./archive/")
    res = { 'flat': [], 'grouped': {} }
    last_read_date = start_date
    with os.scandir(DIR_PATH) as file_iterator:
        for file in file_iterator:
            try:
                file_date = datetime.strptime(file.name, 'fire_%Y-%m-%d_%H_%M.txt')
                if start_date <= file_date <= end_date:
                    if file_date > last_read_date:
                        last_read_date = file_date
                    with open(file.path, 'r') as f:
                        for line in f:
                            coords = list(map(float, reversed(line.split(","))))
                            res['flat'].append(json_feature(file_date, coords))
                            reprojected_feature = json_feature(file_date, TRANSFORMER.transform(coords[1], coords[0]))
                            date_str = file_date.strftime("%Y-%m-%d")
                            if date_str not in res['grouped']:
                                res['grouped'][date_str] = []
                            res['grouped'][date_str].append(reprojected_feature)

            except ValueError:
                print(f"not a data file: ${file.name}")

    return res, last_read_date

def get_start_date():
    dir = os.path.dirname(os.path.realpath(__file__))
    if os.path.exists(f"{dir}/last_read.txt"):
        with open(f"{dir}/last_read.txt", "r") as f:
            last_date = datetime.strptime(f.read(), "%Y-%m-%d")
            last_date = last_date + timedelta(days=1)
            return last_date

    return datetime.strptime("2000-01-01", "%Y-%m-%d")

def save_last_read_date(date: datetime):
    dir = os.path.dirname(os.path.realpath(__file__))
    with open(f"{dir}/last_read.txt", "w") as f:
        f.write(date.strftime("%Y-%m-%d"))

if __name__ == "__main__":

    date_bounds = [get_start_date(), datetime.now()]

    if len(sys.argv) > 1:
        for i in range(1, len(sys.argv)):
            date_bounds[i] = datetime.strptime(sys.argv[i], '%Y-%m-%d')

    if os.getenv("RESOURCE_ID") is None or os.getenv("NEXTGIS_GROUP_ID") is None:
        raise Exception("set RESOURCE_ID and NEXTGIS_GROUP_ID on .env or run create_resource")

    print(os.getenv("RESOURCE_ID"))
    print(os.getenv("NEXTGIS_GROUP_ID"))

    features, last_read_date = read_files(*date_bounds)
    if features:
        response = addFeatures(int(os.getenv("RESOURCE_ID")), features['flat'])
        print(response.json())
        for key, f in features["grouped"].items():
            res = createFireLayer(int(os.getenv("NEXTGIS_GROUP_ID")), f"fire_{key}", SRC_MERCATOR).json()
            print(res)
            addFeatures(res["id"], f)
        save_last_read_date(last_read_date)
    else:
        print("No changes")
