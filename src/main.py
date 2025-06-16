from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src import vegetation_remote_sensing

app = FastAPI()
app.state.vegetation_app = None

# Подключаем статику и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    if app.state.vegetation_app is None:
        return templates.TemplateResponse(
            "missing_credentials.html",
            {
                "request": request
            }
        )

    web_map_url = f"https://geo.mauniver.ru/resource/{app.state.vegetation_app._geo_portal._web_map_id}/display"
    return templates.TemplateResponse("index.html", {
        "request": request,
        "web_map": web_map_url
    })

@app.post("/add_vegetation_data")
async def add_vegetation_data(
    request: Request,
    start_date: str = Form(...),
    end_date: str = Form(...),
    lower_left_latitude: float = Form(...),
    lower_left_longitude: float = Form(...),
    upper_right_latitude: float = Form(...),
    upper_right_longitude: float = Form(...),
    min_cloudiness: int = Form(...),
    max_cloudiness: int = Form(...),
):
    if app.state.vegetation_app is None:
        return templates.TemplateResponse(
            "missing_credentials.html",
            {
                "request": request
            }
        )

    try:
        message = app.state.vegetation_app.add_vegetation_to_the_webmap_from_earth_explorer(
            start_date, end_date,
            lower_left_latitude, lower_left_longitude,
            upper_right_latitude, upper_right_longitude,
            min_cloudiness, max_cloudiness,
        )
        app.state.vegetation_app._is_working = False
        return {"message": message}
    except Exception as e:
        app.state.vegetation_app._is_working = False
        return {"message": str(e)}


@app.post("/generate_ndvi_scale")
async def generate_scale(request: Request):
    if app.state.vegetation_app is None:
        return RedirectResponse(url="/enter_credentials")

    scale_path = app.state.vegetation_app._create_ndvi_scale()
    return {"scale_url": f"/{scale_path}"}


@app.get("/enter_credentials", response_class=HTMLResponse)
async def enter_credentials(request: Request):
    return templates.TemplateResponse(
        "missing_credentials.html",
        {
            "request": request,
        }
    )

@app.post("/save_credentials", response_class=HTMLResponse)
async def save_credentials(
    request: Request,
    earth_explorer_username: str = Form(...),
    earth_explorer_token: str = Form(...),
    geo_portal_username: str = Form(...),
    geo_portal_password: str = Form(...),
    geo_portal_resource_group_id: str = Form(...),
    geo_portal_web_map_id: str = Form(...)
):

    app.state.vegetation_app = vegetation_remote_sensing.VegetationRemoteSensing(
        earth_explorer_username=earth_explorer_username,
        earth_explorer_token=earth_explorer_token,
        geo_portal_username=geo_portal_username,
        geo_portal_password=geo_portal_password,
        geo_portal_resource_group_id=geo_portal_resource_group_id,
        geo_portal_web_map_id=geo_portal_web_map_id
    )

    # Перенаправляем на главную страницу после успешного сохранения
    web_map_url = f"https://geo.mauniver.ru/resource/{geo_portal_web_map_id}/display"
    return templates.TemplateResponse("index.html", {
        "request": request,
        "web_map": web_map_url
    })
