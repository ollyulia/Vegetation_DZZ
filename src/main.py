from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src import vegetation_remote_sensing

app = FastAPI()
vegetation_app = vegetation_remote_sensing.VegetationRemoteSensing()  # Инициализация при старте сервера

# Подключаем статику и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Главная страница с формой (GET)
@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    web_map_url = f"https://geo.mauniver.ru/resource/{vegetation_app._geo_portal._web_map_id}/display"
    return templates.TemplateResponse("index.html", {
        "request": request,
        "web_map": web_map_url
    })

# Обработка формы (POST)
@app.post("/add_vegetation_data")
async def add_vegetation_data(
    start_date: str = Form(...),
    end_date: str = Form(...),
    lower_left_latitude: float = Form(...),
    lower_left_longitude: float = Form(...),
    upper_right_latitude: float = Form(...),
    upper_right_longitude: float = Form(...),
):
    try:
        message = vegetation_app.add_vegetation_to_the_webmap_from_earth_explorer(
            start_date, end_date,
            lower_left_latitude, lower_left_longitude,
            upper_right_latitude, upper_right_longitude
        )
        vegetation_app._is_working = False
        return {"message": message}
    except Exception as e:
        vegetation_app._is_working = False
        return {"message": str(e)}


@app.post("/generate_ndvi_scale")
async def generate_scale():
    scale_path = vegetation_app._create_ndvi_scale()
    return {"scale_url": f"/{scale_path}"}



# def main():
#     app = vegetation_remote_sensing.VegetationRemoteSensing()

#     if app is None:
#         return

#     # начальная и конечная дата съемки
#     start_date = "2024-08-20"
#     end_date = "2024-08-22"

#     # интересующая область задается прямоугольником
#     # Кольский полуостров
#     # левый нижний угол
#     # 66.213585, 27.771668
#     lower_left_latitude = 66.372602
#     lower_left_longitude = 29.540467
#     # правый верхний угол
#     # 69.549744, 41.416688
#     upper_right_latitude = 69.549744
#     upper_right_longitude = 41.416688

#     start_date = "2024-07-20"
#     end_date = "2024-07-30"

#     lower_left_latitude = 66.240158
#     lower_left_longitude = 32.067323
#     upper_right_latitude = 69.287122
#     upper_right_longitude = 41.559510

#     app.add_vegetation_to_the_webmap_from_earth_explorer(
#         start_date,
#         end_date,
#         lower_left_latitude,
#         lower_left_longitude,
#         upper_right_latitude,
#         upper_right_longitude,
#     )

#     return

# def continue_images_processing():
#     app = vegetation_remote_sensing.VegetationRemoteSensing()

#     if app is None:
#         return

#     start_date = "2024-08-14"
#     end_date = "2024-08-15"

#     lower_left_latitude = 68.562252
#     lower_left_longitude = 31.50702
#     upper_right_latitude = 68.915808
#     upper_right_longitude = 37.134767

#     downloaded_images_info_path = "recovery_data/2025-05-18.json"

#     path = "images/2025-05-20/2024-08-14_2024-08-15_68.562252:31.50702_68.915808:37.134767"

#     app.continue_process_images(
#         downloaded_images_info_path,
#         path,
#         lower_left_latitude,
#         lower_left_longitude,
#         upper_right_latitude,
#         upper_right_longitude,
#         start_date,
#         end_date,
#     )

#     return

# def continue_images_uploading():
#     app = vegetation_remote_sensing.VegetationRemoteSensing()

#     if app is None:
#         return

#     start_date = "2024-08-14"
#     end_date = "2024-08-15"

#     lower_left_latitude = 68.562252
#     lower_left_longitude = 31.50702
#     upper_right_latitude = 69.219015
#     upper_right_longitude = 31.50702

#     processed_images_info_path = "recovery_data/2025-05-30_17-29-26_processed_images.json"

#     app.continue_upload_to_geoportal(
#         processed_images_info_path,
#         start_date,
#         end_date,
#         lower_left_latitude,
#         lower_left_longitude,
#         upper_right_latitude,
#         upper_right_longitude
#     )

#     return


# if __name__ == "__main__":
#     main()
