# Ваше имя аккаунта на сайте EarthExplorer
EARTH_EXPLORER_USERNAME: str = None
# Ваш токен (не пароль!) для аккаунта на сайте EarthExplorer
EARTH_EXPLORER_TOKEN: str = None

# Ваше имя аккаунта на сайте Геопортала университета
GEO_PORTAL_USERNAME: str = None
# Ваш пароль для аккаунта на сайте Геопортала университета
GEO_PORTAL_PASSWORD: str = None

# ID папки на Геопортале университета, в которую будут сохраняться растровые слои с растительностью
GEO_PORTAL_RESOURCE_GROUP_ID: int = None
# ID вебкарты на Геопортале университета, на которой будут отображаться растровые слои с растительностью
GEO_PORTAL_WEB_MAP_ID: int = None

def check():
    all_set = True

    if EARTH_EXPLORER_USERNAME is None:
        print("Имя пользователя для входа в EarthExplorer не найдено")
        all_set = False

    if EARTH_EXPLORER_TOKEN is None:
        print("Токен для входа в EarthExplorer не найден")
        all_set = False

    if GEO_PORTAL_USERNAME is None:
        print("Имя пользователя для входа в Геопортал не найдено")
        all_set = False

    if GEO_PORTAL_PASSWORD is None:
        print("Пароль для входа в Геопортал не найден")
        all_set = False

    if GEO_PORTAL_RESOURCE_GROUP_ID is None:
        print("ID папки для сохранения снимков в Геопортале не найден")
        all_set = False

    if GEO_PORTAL_WEB_MAP_ID is None:
        print("ID вебкарты в Геопортале не найден")
        all_set = False

    return all_set
