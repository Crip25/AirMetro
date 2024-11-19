##Update Config to use environment variables
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import jwt
from neo4j import AsyncGraphDatabase
import logging
from enum import Enum
import base64

# Keep existing Enums (ShareLevel, DatasetType)

class Config:
    SECRET_KEY = "[your-generated-secret-key]"
    
    NEO4J_URI_FILES = "neo4j+s://[first-db-id].databases.neo4j.io:7687"
    NEO4J_USER_FILES = "neo4j"
    NEO4J_PASSWORD_FILES = "[first-db-password]"
    
    NEO4J_URI_META = "neo4j+s://dc10cabb.databases.neo4j.io:7687"
    NEO4J_USER_META = "neo4j"
    NEO4J_PASSWORD_META = "kgnK-nfUCe3hlkyqHUwQZOSLoRQjXxo_klhT2eXK9LA"

class DatabaseManager:
    def __init__(self):
        self.files_driver = None
        self.meta_driver = None
    
    async def get_drivers(self):
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

    async def save_file_content(self, file_id: str, content: bytes):
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

    async def create_dataset_node(self, file_id: str, metadata: DatasetMetadata):
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

class DataManager:
    def __init__(self):
        self.db = DatabaseManager()

    async def save_file(self, file: UploadFile, metadata: DatasetMetadata) -> str:
        """Save file content to file DB and metadata to meta DB"""
        file_id = f"{metadata.title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        content = await file.read()
        
        try:
            await self.db.save_file_content(file_id, content)
            await self.db.create_dataset_node(file_id, metadata)
            return file_id
        except Exception as e:
            logging.error(f"Save error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_file(self, file_id: str):
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

# FastAPI app setup (keep existing)
app = FastAPI(title="AAM Research Data Portal")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, 
                  allow_methods=["*"], allow_headers=["*"])

data_manager = DataManager()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Keep existing authentication functions

@app.post("/upload/")
async def upload_dataset(
    file: UploadFile = File(...),
    metadata: DatasetMetadata = Depends(),
    current_user: dict = Depends(get_current_user)
):
    file_id = await data_manager.save_file(file, metadata)
    return {"message": "Upload successful", "file_id": file_id}

@app.get("/file/{file_id}")
async def get_file(file_id: str, current_user: dict = Depends(get_current_user)):
    content = await data_manager.get_file(file_id)
    return Response(content=content, media_type="application/octet-stream")
