from fastapi import FastAPI , APIRouter , Depends
from helpers.config import get_settings , Settings

base_route = APIRouter(
    prefix='/api/v1'
)


@base_route.get("/")
async def welcome_fun(settings : Settings = Depends(get_settings)):
    # settings = get_settings()
    app_name = settings.APP_NAME
    return {"messege" : "Hello World" , 
            "app_name" : app_name}
