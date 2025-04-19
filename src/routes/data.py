from fastapi import FastAPI , APIRouter , Depends , UploadFile ,status
from fastapi.responses import JSONResponse
from helpers.config import Settings , get_settings
from controllers import DataController , ProcessController
from controllers.ProjectController import ProjectController
from routes.schemes.data_schemes import ProcessRequest
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
    project_id : str , 
    file : UploadFile
    ,settings : Settings = Depends(get_settings)
) : 
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
async def process_endpoint(project_id : str , 
                           process_request : ProcessRequest) : 
    
    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    chunk_overlap = process_request.chunk_overlap

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
    
    return file_chunks
