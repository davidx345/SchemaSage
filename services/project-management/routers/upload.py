"""
File upload router with S3 support
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
import uuid
import os
from typing import List
import logging

from config import settings
from utils.s3_manager import s3_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["upload"])

def validate_file(file: UploadFile) -> bool:
    """Validate file size and extension"""
    # Check file size
    if file.size and file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size {file.size} exceeds maximum allowed size {settings.MAX_FILE_SIZE}"
        )
    
    # Check file extension
    if file.filename:
        file_ext = file.filename.split('.')[-1].lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '{file_ext}' not allowed. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
    
    return True

@router.post("/file")
async def upload_file(file: UploadFile = File(...)):
    """Upload a single file to S3 or local storage"""
    try:
        # Validate file
        validate_file(file)
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_ext = file.filename.split('.')[-1] if file.filename else 'bin'
        key = f"uploads/{file_id}.{file_ext}"
        
        if settings.USE_S3:
            # Upload to S3
            file_url = s3_manager.upload_file(
                file.file, 
                key, 
                content_type=file.content_type
            )
            
            if not file_url:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to upload file to S3"
                )
            
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={
                    "message": "File uploaded successfully",
                    "file_id": file_id,
                    "filename": file.filename,
                    "url": file_url,
                    "storage": "s3"
                }
            )
        else:
            # Fallback to local storage
            os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
            file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}.{file_ext}")
            
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={
                    "message": "File uploaded successfully",
                    "file_id": file_id,
                    "filename": file.filename,
                    "path": file_path,
                    "storage": "local"
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during file upload"
        )

@router.post("/files")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    """Upload multiple files to S3 or local storage"""
    if len(files) > 10:  # Limit number of files
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files allowed per upload"
        )
    
    results = []
    
    for file in files:
        try:
            # Validate file
            validate_file(file)
            
            # Generate unique filename
            file_id = str(uuid.uuid4())
            file_ext = file.filename.split('.')[-1] if file.filename else 'bin'
            key = f"uploads/{file_id}.{file_ext}"
            
            if settings.USE_S3:
                # Upload to S3
                file_url = s3_manager.upload_file(
                    file.file, 
                    key, 
                    content_type=file.content_type
                )
                
                if file_url:
                    results.append({
                        "filename": file.filename,
                        "file_id": file_id,
                        "url": file_url,
                        "status": "success",
                        "storage": "s3"
                    })
                else:
                    results.append({
                        "filename": file.filename,
                        "status": "error",
                        "error": "Failed to upload to S3"
                    })
            else:
                # Fallback to local storage
                os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
                file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}.{file_ext}")
                
                with open(file_path, "wb") as buffer:
                    content = await file.read()
                    buffer.write(content)
                
                results.append({
                    "filename": file.filename,
                    "file_id": file_id,
                    "path": file_path,
                    "status": "success",
                    "storage": "local"
                })
                
        except Exception as e:
            logger.error(f"Error uploading file {file.filename}: {e}")
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": str(e)
            })
    
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "message": f"Processed {len(files)} files",
            "results": results
        }
    )

@router.delete("/file/{file_id}")
async def delete_file(file_id: str):
    """Delete a file from S3 or local storage"""
    try:
        if settings.USE_S3:
            # Try to delete from S3 (assuming file extension, or search)
            # This is a simplified version - in production, you'd store the key in a database
            success = s3_manager.delete_file(f"uploads/{file_id}")
            
            if success:
                return JSONResponse(
                    content={"message": "File deleted successfully from S3"}
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found or failed to delete"
                )
        else:
            # Local storage deletion
            import glob
            pattern = os.path.join(settings.UPLOAD_DIR, f"{file_id}.*")
            files = glob.glob(pattern)
            
            if files:
                os.remove(files[0])
                return JSONResponse(
                    content={"message": "File deleted successfully from local storage"}
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file {file_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during file deletion"
        )
