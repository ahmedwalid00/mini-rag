from fastapi import FastAPI , APIRouter , Depends , UploadFile ,status ,Request
from fastapi.responses import JSONResponse
from helpers.config import Settings , get_settings
from controllers import DataController , ProcessController
from controllers.ProjectController import ProjectController
from controllers.NlpController import NLPController
from routes.schemes.data_schemes import ProcessRequest
from models.enums.AssetTypeEnums import AssetType
from models.ChunkModel import ChunkModel 
from models.AssetModel import AssetModel
from models.ProjectModel import ProjectModel
from models.db_schemes import DataChunk , Asset
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
    project_id : int , 
    file : UploadFile
    ,settings : Settings = Depends(get_settings)
) : 
    
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client)
    
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
    
    asset_model = await AssetModel.create_instance(db_client=request.app.db_client)

    asset_resource = Asset(
        asset_project_id= project.project_id , 
        asset_type = AssetType.FILE.value , 
        asset_name = file_id , 
        asset_size = os.path.getsize(file_path)
    ) 

    asset_recored = await asset_model.create_asset(asset=asset_resource)

    
    return JSONResponse(
        status_code=status.HTTP_200_OK , 
        content={
            "signal" : ResponseSignal.FILE_UPLOAD_SUCCESS.value , 
            "file id" : str(asset_recored.asset_name)
        }
    )



@data_route.post("/process/{project_id}")
async def process_endpoint(request : Request ,
                           project_id : int , 
                           process_request : ProcessRequest) : 
    
    chunk_size = process_request.chunk_size
    chunk_overlap = process_request.chunk_overlap
    do_reset = process_request.do_reset

    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client)

    project = await project_model.get_project_or_create_one(project_id=project_id)

    asset_model = await AssetModel.create_instance(db_client=request.app.db_client)

    project_file_ids = {}

    if process_request.file_id : 
        record = await asset_model.get_asset_record(
            asset_project_id=project.project_id,
            asset_name=process_request.file_id)
        
        if record == None:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST ,
                content={
                    "signal" : ResponseSignal.FILE_ID_ERROR.value
                }
            )
    
        project_file_ids = {record.asset_id : record.asset_name}

    else : 
       
        project_files = await asset_model.get_all_project_assets(
            asset_project_id=project.project_id,
            asset_type=AssetType.FILE.value
                                            )
        project_file_ids = {
            record.asset_id : record.asset_name
              for record in project_files}

    if len(project_file_ids) == 0 :
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST , 
            content={
                "signal" : ResponseSignal.NO_FILES_ERROR.value
            }
        )
    
    chunk_model = await ChunkModel.create_instance(db_client=request.app.db_client)
    process_controller = ProcessController(project_id=project_id)

    nlp_controller = NLPController(
               vectordb_client=request.app.vectordb_client,
                generation_client=request.app.generation_client,
                embedding_client=request.app.embedding_client,
                template_parser=request.app.template_parser
            )

    if do_reset == 1 :
        collection_name = nlp_controller.create_collection_name(project_id=project.project_id)
        _ = await request.app.vectordb_client.delete_collection(collection_name=collection_name)
        
        _ = await chunk_model.delete_chunks_by_project_id(
                project_id=project.project_id
                )
        
    no_recoreds = 0 
    no_files = 0
    
    for asset_id , file_id in project_file_ids.items():

        file_content = process_controller.get_file_content(file_id=file_id)

        if file_content is None:
            logger.error(f"Error while Processing file : {file_id}")
            continue

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
                chunk_project_id = project.project_id , 
                chunk_asset_id=asset_id
            )
            for i,chunk in enumerate(file_chunks)
        ] 

        no_recoreds += await chunk_model.insert_many_chunks(chunks=file_chunks_contents)
        no_files += 1


    return JSONResponse(
            content= {
                "signal" : ResponseSignal.PROCESSING_SUCCESS.value ,
                "inserted_chunks" : no_recoreds , 
                "files_proccessed" : no_files
            }
        )
