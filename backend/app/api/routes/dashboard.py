from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from datetime import datetime

router = APIRouter()

# Dependency to get MongoDB client
async def get_db():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB]
    try:
        yield db
    finally:
        client.close()

@router.get("/summary")
async def dashboard_summary(db=Depends(get_db)):
    projects = await db.projects.find().sort("updated_at", -1).to_list(5)
    active_projects = await db.projects.count_documents({})
    tables_processed = 0
    last_activity = {"timestamp": None, "description": "No recent activity"}
    recent_projects = []

    if projects:
        tables_processed = sum(len(p.get("schema", {}).get("tables", [])) for p in projects)
        last = projects[0]
        last_activity = {
            "timestamp": last.get("updated_at", last.get("created_at", datetime.utcnow())),
            "description": f"Updated {last.get('name', 'a project')}"
        }
        recent_projects = [
            {
                "id": str(p["_id"]),
                "name": p.get("name", "Untitled"),
                "updatedAt": p.get("updated_at", p.get("created_at", datetime.utcnow()))
            }
            for p in projects
        ]

    return {
        "activeProjects": active_projects,
        "tablesProcessed": tables_processed,
        "lastActivity": last_activity,
        "recentProjects": recent_projects
    }
