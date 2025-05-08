from stores.vectordb.providers import QdrantDBProvider , PGVectorProvider
from stores.vectordb import VectorDBEnums
from controllers.BaseController import BaseController
from sqlalchemy.orm import sessionmaker

class VectorDBProviderFactory:

    def __init__(self , config , db_client : sessionmaker):
        self.config = config
        self.base_controller = BaseController()
        self.db_client = db_client

    def create(self , provider : str) : 
        if provider == VectorDBEnums.QDRANT.value:
            db_qdrant_client = self.base_controller.get_database_path(database_name=self.config.VECTOR_DB_BACKEND)
            return QdrantDBProvider(
                db_path=db_qdrant_client , 
                distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
                default_vector_size=self.config.EMBEDDING_MODEL_SIZE,
                index_threshold=self.config.VECTOR_DB_PGVEC_INDEX_THRESHOLD,
            )
        
        if provider == VectorDBEnums.PGVECTOR.value:
            return PGVectorProvider(
                db_client=self.db_client,
                distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
                default_vector_size=self.config.EMBEDDING_MODEL_SIZE,
                index_threshold=self.config.VECTOR_DB_PGVEC_INDEX_THRESHOLD
            )
        
        return None
    
