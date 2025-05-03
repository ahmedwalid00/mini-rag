from fastapi import FastAPI 
from motor.motor_asyncio import AsyncIOMotorClient
from routes import base, data ,nlp
from stores.llm.templates.template_parser import TemplateParser
from helpers.config import get_settings
from stores.llm import LLMProviderFactory 
from stores.vectordb import VectorDBProviderFactory

app = FastAPI()


async def startup_span():
    settings = get_settings()
    app.mongo_conn = AsyncIOMotorClient(settings.MONGODB_URL)
    app.db_client = app.mongo_conn[settings.MONGODB_DATABASE]

    llm_provider_factory = LLMProviderFactory(config=settings)

    #generation client 
    app.generation_client  = llm_provider_factory.create(provider=settings.GENERATION_BACKEND)
    app.generation_client.set_generation_model(model_id=settings.GENERATION_MODEL_ID)

    #embedding client 
    app.embedding_client = llm_provider_factory.create(provider=settings.EMBEDDING_BACKEND)
    app.embedding_client.set_embedding_model(model_id=settings.EMBEDDING_MODEL_ID,
                                             embedding_size=settings.EMBEDDING_MODEL_SIZE)
    
    #VectorDB client
    vectordb_provider_factory = VectorDBProviderFactory(config=settings)
    app.vectordb_client = vectordb_provider_factory.create(
        provider=settings.VECTOR_DB_BACKEND)
    app.vectordb_client.connect()

    #Template Parser
    app.template_parser = TemplateParser(
        language=settings.PRIMARY_LANG,
        default_language=settings.DEFAULT_LANG
    )


async def shutdown_span():
    app.mongo_conn.close()
    app.vectordb_client.disconnect()


# app.router.lifespan.on_startup.append(startup_span)
# app.router.lifespan.on_shutdown.append(shutdown_span)

app.on_event("startup")(startup_span)
app.on_event("shutdown")(shutdown_span)

app.include_router(base.base_route)
app.include_router(data.data_route)
app.include_router(nlp.nlp_router)

