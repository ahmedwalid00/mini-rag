from fastapi import FastAPI , APIRouter , Depends , UploadFile ,status ,Request
from fastapi.responses import JSONResponse
from helpers.config import Settings , get_settings
from controllers import DataController , ProcessController
from controllers.ProjectController import ProjectController
from routes.schemes.data_schemes import ProcessRequest
from models.ChunkModel import ChunkModel
from models.ProjectModel import ProjectModel
from models.db_schemes import DataChunk
from models import ResponseSignal
import aiofiles
import os
import logging

logger = logging.getLogger('uvicorn.error')


data_route = APIRouter(
    prefix='/api/v1/data'
)

@data_route.post('/upload/{project_id}')
async def upload_data(
    request : Request ,
    project_id : str , 
    file : UploadFile
    ,settings : Settings = Depends(get_settings)
) : 
    
    project_model = ProjectModel(db_client=request.app.db_client)
    
    project = await project_model.get_project_or_create_one(project_id=project_id)

    data_controller = DataController()
    is_valid , signal_response = data_controller.validate_uploaded_file(file=file)

    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST , 
            content=signal_response
            
        )
    
    project_controller = ProjectController()
   
    file_path , file_id = data_controller.generate_unique_filepath(original_file_name=file.filename,
                                                         project_id=project_id)
    
    try :
        async with aiofiles.open(file=file_path , mode="wb") as f :
           while chunk := await file.read(settings.FILE_DEFAULT_CHUNK_SIZE) :
                await f.write(chunk)
    except Exception as e :

        logger.error(f"Error while uploading file {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST , 
            content= {
                "signal" : ResponseSignal.FILE_UPLOAD_FAILED.value
            }
        )
    
    return JSONResponse(
        status_code=status.HTTP_200_OK , 
        content={
            "signal" : ResponseSignal.FILE_UPLOAD_SUCCESS.value , 
            "file id" : file_id
        }
    )

@data_route.post("/process/{project_id}")
async def process_endpoint(request : Request ,
                           project_id : str , 
                           process_request : ProcessRequest) : 
    
    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    chunk_overlap = process_request.chunk_overlap
    do_reset = process_request.do_reset

    project_model = ProjectModel(db_client=request.app.db_client)

    project = await project_model.get_project_or_create_one(project_id=project_id)

    process_controller = ProcessController(project_id=project_id)

    file_content = process_controller.get_file_content(file_id=file_id)
    file_chunks = process_controller.process_file_content(
        file_id=file_id , 
        file_content=file_content,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    if file_chunks is None or len(file_chunks) == 0 :
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST ,
            content= {
                "signal" : ResponseSignal.PROCESSING_FAILED.value 
            }
        )
    
    file_chunks_contents = [

        DataChunk(
            chunk_text = chunk.page_content,
            chunk_metadata = chunk.metadata , 
            chunk_order = i+1 ,
            chunk_project_id = project.id
        )
        for i,chunk in enumerate(file_chunks)
    ] 

    chunk_model = ChunkModel(db_client=request.app.db_client)



    no_recoreds = await chunk_model.insert_many_chunks(chunks=file_chunks_contents)

    if do_reset == 1 :
        _ = await chunk_model.delete_chunk_by_project_id(
            project_id=project.id
            )

    return JSONResponse(
        content= {
            "signal" : ResponseSignal.PROCESSING_SUCCESS.value ,
            "inserted_chunks" : no_recoreds
        }
    )
