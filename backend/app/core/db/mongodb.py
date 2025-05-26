"""MongoDB database operations and utilities. (Deprecated after PostgreSQL migration)"""

# from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection # Deprecated
# from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError # Deprecated
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import uuid

# from bson import ObjectId # Deprecated
# from app.config import get_settings # Settings might still be used if other parts of the file were kept
# from app.models.schemas import SchemaResponse # This was causing the circular import

# settings = get_settings()

# Create a MongoDB client instance
# client = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000) # Deprecated

# class PyObjectId(ObjectId): # Deprecated
#     """Custom ObjectId type for Pydantic models"""
#     @classmethod
#     def __get_validators__(cls):
#         yield cls.validate

#     @classmethod
#     def validate(cls, v):
#         if not ObjectId.is_valid(v):
#             raise ValueError("Invalid ObjectId")
#         return ObjectId(v)

#     @classmethod
#     def __modify_schema__(cls, field_schema):
#         field_schema.update(type="string")

# class MongoDB: # Deprecated
# """MongoDB database operations"""
# def __init__(self):
#     self.client = client
#     self.db = client[settings.MONGODB_DB]
#     self.projects = self.db[settings.MONGODB_PROJECTS_COLLECTION]
#     self.schemas = self.db[settings.MONGODB_SCHEMAS_COLLECTION]

# async def test_connection(self) -> bool:
#     """Test the MongoDB connection"""
#     try:
#         await self.client.admin.command('ismaster')
#         return True
#     except (ConnectionFailure, ServerSelectionTimeoutError):
#         return False

# async def get_database_info(self) -> Dict[str, Any]:
#     """Get information about the MongoDB database"""
#     try:
#         # Get stats about the database
#         stats = await self.db.command("dbStats")
#         collections = await self.db.list_collection_names()
#         return {
#             "status": "connected",
#             "database_name": settings.MONGODB_DB,
#             "collections": collections,
#             "storage_size": stats.get("storageSize", 0),
#             "document_count": stats.get("objects", 0)
#         }
#     except Exception as e:
#         return {
#             "status": "error",
#             "error": str(e)
#         }

# async def create_project(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
#     """Create a new project"""
#     project = {
#         "id": str(uuid.uuid4()),
#         "name": name,
#         "description": description,
#         "created_at": datetime.utcnow(),
#         "updated_at": datetime.utcnow()
#     }

#     result = await self.projects.insert_one(project)

#     if result.inserted_id:
#         project["_id"] = str(result.inserted_id)
#         return project

#     raise ValueError("Failed to create project")

# async def get_projects(self) -> List[Dict[str, Any]]:
#     """Get all projects"""
#     cursor = self.projects.find().sort("created_at", -1)
#     projects = []

#     async for project in cursor:
#         project["_id"] = str(project["_id"])
#         projects.append(project)

#     return projects

# async def get_project(self, project_id: str) -> Dict[str, Any]:
#     """Get a project by ID"""
#     project = None
#     if ObjectId.is_valid(project_id):
#         project = await self.projects.find_one({"_id": ObjectId(project_id)})

#     if not project:
#         project = await self.projects.find_one({"id": project_id})

#     if project:
#         project["_id"] = str(project["_id"])
#         return project

#     raise ValueError(f"Project with ID {project_id} not found")

# async def update_project(self, project_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
#     """Update a project"""
#     update_data["updated_at"] = datetime.utcnow()

#     query = {"id": project_id}
#     if ObjectId.is_valid(project_id):
#         query = {"$or": [{"_id": ObjectId(project_id)}, {"id": project_id}]}

#     result = await self.projects.update_one(
#         query,
#         {"$set": update_data}
#     )

#     if result.matched_count:
#         return await self.get_project(project_id)

#     raise ValueError(f"Project with ID {project_id} not found")

# async def delete_project(self, project_id: str) -> bool:
#     """Delete a project"""
#     query = {"id": project_id}
#     if ObjectId.is_valid(project_id):
#         query = {"$or": [{"_id": ObjectId(project_id)}, {"id": project_id}]}

#     result = await self.projects.delete_one(query)

#     if result.deleted_count:
#         # Also delete associated schemas
#         await self.schemas.delete_many({"project_id": project_id})
#         return True

#     return False

# async def save_schema(self, project_id: str, schema: SchemaResponse) -> Dict[str, Any]:
#     """Save a schema for a project"""
#     schema_dict = schema.model_dump()

#     # Check if project exists
#     await self.get_project(project_id)

#     schema_doc = {
#         "project_id": project_id,
#         "schema": schema_dict,
#         "created_at": datetime.utcnow(),
#         "updated_at": datetime.utcnow()
#     }

#     # Update existing schema or insert new one
#     result = await self.schemas.update_one(
#         {"project_id": project_id},
#         {"$set": schema_doc},
#         upsert=True
#     )

#     return {
#         "project_id": project_id,
#         "schema": schema_dict,
#         "updated_at": schema_doc["updated_at"]
#     }

# async def get_schema(self, project_id: str) -> SchemaResponse:
#     """Get the schema for a project"""
#     schema_doc = await self.schemas.find_one({"project_id": project_id})

#     if not schema_doc:
#         raise ValueError(f"No schema found for project {project_id}")

#     return SchemaResponse.model_validate(schema_doc["schema"])

# Create a singleton instance to be imported by other modules
# db = MongoDB() # Deprecated

# Add a note that this module is deprecated
DEPRECATED_NOTE = "This module is deprecated as the project has migrated to PostgreSQL."


def get_deprecated_mongodb_client():
    raise NotImplementedError(
        f"{DEPRECATED_NOTE} MongoDB client is no longer available."
    )


def get_deprecated_db_instance():
    raise NotImplementedError(
        f"{DEPRECATED_NOTE} MongoDB instance is no longer available."
    )
