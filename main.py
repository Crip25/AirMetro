from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime
from jose import jwt
from neo4j import AsyncGraphDatabase
import logging
import os
from enum import Enum
import base64
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request

class ShareLevel(str, Enum):
    PRIVATE = "private"
    TEAM = "team"
    GROUP = "group"
   

class DatasetType(str, Enum):
    FLIGHT_DATA = "flight_data"
    SIMULATION = "simulation data"
    SENSOR_DATA = "sensor_data"
    ANALYSIS = "analysis data"
    VISUALIZATION = "visualization data"
    test= "test data"

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
    SECRET_KEY = os.getenv('SECRET_KEY', '[secrt k:d9a39c2a641482135a6242d14f2bb6a888db4f2931054ffad0783e6d018d2eba]')
    
    NEO4J_URI_FILES = os.getenv('NEO4J_URI_FILES', 'neo4j+s://4d450adb.databases.neo4j.io]')
    NEO4J_USER_FILES = os.getenv('NEO4J_USER_FILES', 'neo4j')
    NEO4J_PASSWORD_FILES = os.getenv('NEO4J_PASSWORD_FILES', '[lphtTzkwtbJ8dVPN7KDn8DrTXJe80tsb-bTIOr3YHtI]')
    
    NEO4J_URI_META = os.getenv('NEO4J_URI_META', 'neo4j+s://dc10cabb.databases.neo4j.io')
    NEO4J_USER_META = os.getenv('NEO4J_USER_META', 'neo4j')
    NEO4J_PASSWORD_META = os.getenv('NEO4J_PASSWORD_META', '[kgnK-nfUCe3hlkyqHUwQZOSLoRQjXxo_klhT2eXK9LA]')

class DatabaseManager:
    def __init__(self):
        self.files_driver = None
        self.meta_driver = None
    
    async def get_drivers(self):
        try:
            if not self.files_driver:
                self.files_driver = AsyncGraphDatabase.driver(
                    Config.NEO4J_URI_FILES,
                    auth=(Config.NEO4J_USER_FILES, Config.NEO4J_PASSWORD_FILES)
                )
            if not self.meta_driver:
                self.meta_driver = AsyncGraphDatabase.driver(
                    Config.NEO4J_URI_META,
                    auth=(Config.NEO4J_USER_META, Config.NEO4J_PASSWORD_META)
                )
            return self.files_driver, self.meta_driver
        except Exception as e:
            logging.error(f"Database connection error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

    async def save_file_content(self, file_id: str, content: bytes):
        try:
            files_driver, _ = await self.get_drivers()
            encoded = base64.b64encode(content).decode()
            
            async with files_driver.session() as session:
                await session.run("""
                    CREATE (f:File {
                        id: $id,
                        content: $content,
                        created_at: datetime()
                    })
                """, {'id': file_id, 'content': encoded})
        except Exception as e:
            logging.error(f"Save file content error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    async def create_dataset_node(self, file_id: str, metadata: DatasetMetadata):
        try:
            _, meta_driver = await self.get_drivers()
            
            async with meta_driver.session() as session:
                await session.run("""
                    CREATE (d:Dataset {
                        id: $id,
                        title: $title,
                        description: $description,
                        type: $type,
                        share_level: $share_level,
                        version: $version,
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
                    'id': file_id,
                    'title': metadata.title,
                    'description': metadata.description,
                    'type': metadata.dataset_type,
                    'share_level': metadata.share_level,
                    'version': metadata.version,
                    'tags': metadata.tags,
                    'authors': metadata.authors,
                    'teams': metadata.teams
                })
        except Exception as e:
            logging.error(f"Create dataset error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create dataset: {str(e)}")

class DataManager:
    def __init__(self):
        self.db = DatabaseManager()

    async def save_file(self, file: UploadFile, metadata: DatasetMetadata) -> str:
        """Save file content to file DB and metadata to meta DB"""
        try:
            file_id = f"{metadata.title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            content = await file.read()
            
            await self.db.save_file_content(file_id, content)
            await self.db.create_dataset_node(file_id, metadata)
            return file_id
        except Exception as e:
            logging.error(f"Save error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_file(self, file_id: str):
        try:
            files_driver, _ = await self.db.get_drivers()
            async with files_driver.session() as session:
                result = await session.run(
                    "MATCH (f:File {id: $id}) RETURN f.content",
                    {'id': file_id}
                )
                record = await result.single()
                if record:
                    return base64.b64decode(record['f.content'])
                raise HTTPException(status_code=404, detail="File not found")
        except Exception as e:
            logging.error(f"Get file error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve file: {str(e)}")

app = FastAPI(title="AAM Research Data Portal")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Initialize managers
data_manager = DataManager()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logging.error(f"Internal error: {str(exc)}")
    return JSONResponse(status_code=500, content={"detail": str(exc)})

@app.post("/upload/")
async def upload_dataset(
    file: UploadFile = File(...),
    metadata: DatasetMetadata = Depends(),
    current_user: dict = Depends(get_current_user)
):
    try:
        file_id = await data_manager.save_file(file, metadata)
        return {"message": "Upload successful", "file_id": file_id}
    except Exception as e:
        logging.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/file/{file_id}")
async def get_file(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        content = await data_manager.get_file(file_id)
        return Response(content=content, media_type="application/octet-stream")
    except Exception as e:
        logging.error(f"File retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
