from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import asyncio
import aiofiles
from pathlib import Path
import jwt
from neo4j import AsyncGraphDatabase  # Using the async Neo4j driver
import logging
from enum import Enum

# Models (same as in your previous code)
class ShareLevel(str, Enum):
    PRIVATE = "private"
    TEAM = "team"
    GROUP = "group"
    PUBLIC = "public"

class DatasetType(str, Enum):
    FLIGHT_DATA = "flight_data"
    SIMULATION = "simulation"
    SENSOR_DATA = "sensor_data"
    ANALYSIS = "analysis"
    VISUALIZATION = "visualization"

class DatasetMetadata(BaseModel):
    title: str
    description: str
    dataset_type: DatasetType
    share_level: ShareLevel
    tags: List[str]
    version: str
    parent_version: Optional[str]
    authors: List[str]
    teams: List[str]
    related_datasets: List[str] = []

class UpdateNotification(BaseModel):
    dataset_id: str
    version: str
    updated_by: str
    update_type: str
    description: str
    timestamp: datetime

class Config:
    SECRET_KEY = "your-secret-key"
    NETWORK_DRIVE_PATH = Path("C:/aam_research")
    
    # Neo4j Aura connection details (replace these with your actual Aura credentials)
    NEO4J_URI = "neo4j+s://dc10cabb.databases.neo4j.io:7687"
    NEO4J_USER = "<neo4j>"
    NEO4J_PASSWORD = "<kgnK-nfUCe3hlkyqHUwQZOSLoRQjXxo_klhT2eXK9LA>"
    
    ALLOWED_EXTENSIONS = {
        'data': ['.csv', '.xlsx', '.json', '.h5'],
        'video': ['.mp4', '.avi', '.mov'],
        'image': ['.jpg', '.png', '.tif']
    }

class DatabaseManager:
    def __init__(self):
        # Connecting to the Neo4j Aura instance
        self.driver = AsyncGraphDatabase.driver(
            Config.NEO4J_URI,
            auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD)
        )

    async def create_dataset_node(self, metadata: DatasetMetadata, file_path: str):
        async with self.driver.session() as session:
            await session.run("""
                CREATE (d:Dataset {
                    id: $id,
                    title: $title,
                    description: $description,
                    type: $type,
                    share_level: $share_level,
                    version: $version,
                    parent_version: $parent_version,
                    file_path: $file_path,
                    created_at: datetime(),
                    tags: $tags
                })
                WITH d
                UNWIND $authors as author
                MERGE (u:User {username: author})
                CREATE (u)-[:AUTHORED]->(d)
                WITH d
                UNWIND $teams as team
                MERGE (t:Team {name: team})
                CREATE (d)-[:BELONGS_TO]->(t)
            """, {
                'id': str(file_path),
                'title': metadata.title,
                'description': metadata.description,
                'type': metadata.dataset_type,
                'share_level': metadata.share_level,
                'version': metadata.version,
                'parent_version': metadata.parent_version,
                'file_path': file_path,
                'tags': metadata.tags,
                'authors': metadata.authors,
                'teams': metadata.teams
            })

    async def create_update_notification(self, notification: UpdateNotification):
        async with self.driver.session() as session:
            await session.run("""
                MATCH (d:Dataset {id: $dataset_id})
                CREATE (n:UpdateNotification {
                    id: randomUUID(),
                    version: $version,
                    updated_by: $updated_by,
                    update_type: $update_type,
                    description: $description,
                    timestamp: datetime()
                })-[:UPDATES]->(d)
            """, notification.dict())

    async def get_dataset_updates(self, dataset_id: str):
        async with self.driver.session() as session:
            result = await session.run("""
                MATCH (n:UpdateNotification)-[:UPDATES]->(d:Dataset {id: $dataset_id})
                RETURN n ORDER BY n.timestamp DESC
            """, {'dataset_id': dataset_id})
            return [dict(record['n']) for record in await result.fetch()]

class DataManager:
    def __init__(self):
        self.db = DatabaseManager()
        
    async def save_file(self, file: UploadFile, metadata: DatasetMetadata) -> str:
        """Save file to network drive with version control"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_path = Config.NETWORK_DRIVE_PATH / metadata.dataset_type / timestamp
        version_path.mkdir(parents=True, exist_ok=True)
        
        file_path = version_path / file.filename
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                while chunk := await file.read(8192):
                    await f.write(chunk)
            
            await self.db.create_dataset_node(metadata, str(file_path))
            return str(file_path)
        except Exception as e:
            logging.error(f"File save error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

# FastAPI app
app = FastAPI(title="AAM Research Data Portal")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Initialize managers
data_manager = DataManager()

# Auth setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401)

# API Routes (same as in your previous code)
@app.post("/upload/")  # etc.
async def upload_dataset(
    file: UploadFile = File(...),
    metadata: DatasetMetadata = Depends(),
    current_user: dict = Depends(get_current_user)
):
    if not any(file.filename.endswith(ext) for exts in Config.ALLOWED_EXTENSIONS.values() for ext in exts):
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    file_path = await data_manager.save_file(file, metadata)
    
    # Create update notification
    notification = UpdateNotification(
        dataset_id=file_path,
        version=metadata.version,
        updated_by=current_user['username'],
        update_type="create",
        description=f"Initial upload of {metadata.title}",
        timestamp=datetime.now()
    )
    await data_manager.db.create_update_notification(notification)
    
    return {"message": "Upload successful", "file_path": file_path}
