import contextlib
from fastapi import FastAPI, Request 
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from routes import base, data
from helpers.config import get_settings

app = FastAPI()

@app.on_event("startup")
async def startup_db_client():
    settings = get_settings()
    app.mongo_conn = AsyncIOMotorClient(settings.MONGODB_URL)
    app.db_client = app.mongo_conn[settings.MONGODB_DATABASE]

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongo_conn.close()

app.include_router(base.base_route)
app.include_router(data.data_route)

# Define the lifespan asynchronous context manager
# @asynccontextmanager
# async def lifespan(app: FastAPI):

#     settings = get_settings()
#     # Connect to MongoDB
#     mongo_conn = AsyncIOMotorClient(settings.MONGODB_URL)
#     db_client = mongo_conn[settings.MONGODB_DATABASE]

#     app.state.mongo_conn = mongo_conn
#     app.state.db_client = db_client

#     yield  

#     app.state.mongo_conn.close()
    
# app = FastAPI(lifespan=lifespan)

# --- IMPORTANT NOTE FOR YOUR ROUTES ---
# Previously, you might have accessed the db client in your routes like:
# db = request.app.db_client
#
# NOW, using app.state, you should access it like:
# db = request.app.state.db_client
#
# Make sure to update your route handlers in base.py and data.py accordingly!
# You'll need to import Request from fastapi in those route files
# and ensure your route functions accept 'request: Request' as an argument.
# Example route function signature: async def my_route(request: Request):
# --------------------------------------

# Include your routers (no changes needed here)
# app.include_router(base.base_route)
# app.include_router(data.data_route)

 

