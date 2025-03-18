# Файл для работы с трансформацией координат

from pyproj import Transformer

#  долгота   широта
# longitude latitude
#     /\
#     ||    <------>
#     \/

def wgs84_to_web_mercator(longitude, latitude):
    """
    70.0127481, 31.1982503 -> (7793783, 3658523)
    """
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    x, y = transformer.transform(longitude, latitude)

    return round(x), round(y)

def list_wgs84_to_web_mercator(coordinates: list):
    """
    [[70.0127481, 31.1982503]] -> [[7793783, 3658523]]
    """
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

    result = []

    for longitude, latitude in coordinates:
        x, y = transformer.transform(longitude, latitude)
        result.append([round(x), round(y)])

    return result

def web_mercator_to_wgs84(x, y):
    """
    (7792367.0, 3660972.0) -> (70.0127481, 31.1982503)
    """
    transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
    longitude, latitude = transformer.transform(x, y)

    return round(longitude, 6), round(latitude, 6)
