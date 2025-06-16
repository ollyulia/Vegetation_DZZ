from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src import vegetation_remote_sensing

app = FastAPI()
vegetation_app = vegetation_remote_sensing.VegetationRemoteSensing()
if vegetation_app is None:
    raise Exception("Не хватает данных для авторизации. Укажите все необходимые поля в файле secret.py")

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
