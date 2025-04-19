from enum import Enum

class ResponseSignal(Enum):

    FILE_VALIDATED_SUCCESS = "file validated successfully"
    FILE_TYPE_NOT_SUPPORTED = "file type is not supported"
    FILE_SIZE_EXCEEDED = "file size exceeded the max size"
    FILE_UPLOAD_SUCCESS = "file has been uploaded successfully"
    FILE_UPLOAD_FAILED = "file upload failed"
    PROCESSING_SUCCESS = "processing success"
    PROCESSING_FAILED = "Processing failed"