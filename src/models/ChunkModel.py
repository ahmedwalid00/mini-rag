from .BaseDataModel import BaseDataModel
from .enums.DataBaseEnums import DataBaseEnums
from .db_schemes.data_chunk import DataChunk
from bson.objectid import ObjectId
from pymongo import InsertOne


class ChunkModel(BaseDataModel):
    
    def __init__(self, db_client):
        super().__init__(db_client=db_client)
        self.collection = db_client[DataBaseEnums.COLLECTION_CHUNK_NAME.value]

    async def create_chunk(self , chunk : DataChunk) :
       
        result = await self.collection.insert_one(chunk.dict(chunk.dict(by_alias=True, 
                                                                        exclude_unset=True)))
        chunk.id = result.inserted_id

        return chunk
    

    async def get_chunk(self,chunk_id : str) :
        
        record = await self.collection.find_one({
            "_id" : ObjectId(chunk_id)
        })

        if record is None : 
            return None
        
        return DataChunk(**record)
    
    async def insert_many_chunks(self, chunks : list , batch_size : int = 100) : 

        for i in range(0,len(chunks),batch_size):
            batch = chunks[i : i+batch_size]

            operations = [InsertOne(chunk.dict(by_alias=True, exclude_unset=True)) 
                          for chunk in batch]
            
            await self.collection.bulk_write(operations)

        return len(chunks)
    
    async def delete_chunk_by_project_id(self , project_id : ObjectId) :

        result = await self.collection.delete_many({
            "chunk_project_id" : project_id
        })

        return result.deleted_count
 
