from stores.llm.LLMInterface import LLMInterface
from stores.llm.LLMEnums import CoHereEnums , DocumentTypeEnum
from typing import List , Optional
import cohere
import logging

class CoHereProvider(LLMInterface):
    def __init__(self , api_key : str , 
                 default_input_max_characters : int = 1000 , 
                 default_generation_max_output_tokens : int = 1000 , 
                 default_generation_temperature : float = 0.1):
        
        self.api_key = api_key
      
        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature

        self.enums = CoHereEnums
 
        self.generation_model_id  = None

        self.embedding_model_id = None
        self.embedding_size = None

        self.client = cohere.Client(
            api_key = self.api_key
        )

        self.logger = logging.getLogger(__name__)

    
    def set_generation_model(self, model_id: str): 
        self.generation_model_id = model_id


    def set_embedding_model(self, model_id: str, embedding_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size


    def process_text(self , text : str) : 
        return text[:self.default_input_max_characters].strip()
    

    def generate_text(self, prompt: str, chat_history: list=[], max_output_tokens: int=None,
                            temperature: float = None):
        
        if not self.client:
            self.logger.error("CoHere client was not set")
            return None
        
        if not self.generation_model_id:
            self.logger.error("Generation model for CoHere was not set")
            return None
        
        max_output_tokens = max_output_tokens if max_output_tokens else self.default_generation_max_output_tokens
        temperature = temperature if temperature else self.default_generation_temperature

        response = self.client.chat(
            model=self.generation_model_id , 
            chat_history=chat_history,
            message=self.process_text(text=prompt),
            temperature=temperature,
            max_tokens=max_output_tokens
        )
        
        if not response or not response.text:
            self.logger.error("Error while generating text with CoHere")
            return None
        
        return response.text
    
    def embed_text(self, text: str, document_type: str = None):

        if not self.client:
            self.logger.error("CoHere client was not set")
            return None
        
        if not self.embedding_model_id:
            self.logger.error("Embedding model for CoHere was not set")
            return None
        
        input_type = CoHereEnums.DOCUMENT
        if document_type == DocumentTypeEnum.QUERY:
            input_type = CoHereEnums.QUERY

        response = self.client.embed(
            model=self.embedding_model_id , 
            texts= [text] , 
            input_type= input_type,
            embedding_types=['float']
        )

        if not response or not response.embeddings or not response.embeddings.float:
            self.logger.error("Error while embedding text with CoHere")
            return None
        
        return response.embeddings.float[0]
    

    def embed_texts(self, texts: List[str], document_type: str = None):
        """
        Embeds a list of texts in a single API call.

        Args:
            texts: A list of strings to embed.
            document_type: The type of document (e.g., 'search_document', 'search_query').

        Returns:
            A list of embedding vectors (list of floats), or None if an error occurs.
        """
        if not self.client:
            self.logger.error("CoHere client was not set")
            return None

        if not self.embedding_model_id:
            self.logger.error("Embedding model for CoHere was not set")
            return None

        input_type = CoHereEnums.DOCUMENT.value # Default to DOCUMENT value
        if document_type == DocumentTypeEnum.QUERY.value:
            input_type = CoHereEnums.QUERY.value

        try:
            response = self.client.embed(
                model=self.embedding_model_id,
                texts=texts,  # Pass the entire list here
                input_type=input_type,
                embedding_types=['float']
            )

            if not response or not response.embeddings or not response.embeddings.float:
                self.logger.error("Error or unexpected response structure while embedding batch text with CoHere")
                return None

            return response.embeddings.float # This is expected to be List[List[float]]
        
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during batch embedding with CoHere: {e}", exc_info=True)
            return None


    def construct_prompt(self, prompt: str, role: str):
        return {
            "role": role,
            "text": self.process_text(prompt)
        }