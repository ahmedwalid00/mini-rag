from helpers.config import Settings , get_settings
import os
import string
import random

class BaseController:
    
    def __init__(self):
        
        self.app_settings = get_settings()
        self.base_dir = os.path.dirname( os.path.dirname(__file__) )
        self.files_dir = os.path.join(
            self.base_dir , "assets/files"
        )

        self.database_dir = os.path.join(
            self.base_dir , 
            "assets/database"
        )
    
    def generate_random_string(self, length: int=12):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    def get_database_path(self , database_name : str) : 
        database_path = os.path.join(
            self.database_dir , 
            database_name
        )

        if not os.path.exists(path=database_path) :
            os.mkdir(database_path)

        return database_path
    