# AAM Research Data Management Solution

## Overview
Advanced Air Mobility Research Data Management Solution is a comprehensive platform for storing, sharing, and managing research data using graph-based relationships. Built with FastAPI and Neo4j Aura, it offers robust data organization, secure sharing, and intelligent metadata management.


## 🚀 Key Features

### Data Management
- **Dual Database Architecture**
  - File Storage DB: Secure binary data storage 
  - Metadata DB: Graph-based relationship management

### 📊 Data Organization
- **Dataset Types**
  ```
  ✈️ Flight Data
  🔄 Simulation
  📊 Sensor Data
  📈 Analysis
  🎨 Visualization
  🛸 Drone Data
  ```

### 🔐 Access Control
- **Share Levels**
  ```
  PRIVATE: Personal access
  TEAM: Research team access
  GROUP: Department-wide access
  PUBLIC: Open access
  ```

### 🤝 Collaboration Features
- Team-based sharing
- Real-time updates
- Version control
- Cross-referencing datasets

## 🛠️ Technical Architecture

### Backend
- **FastAPI Framework**
  - RESTful API endpoints
  - Async request handling
  - JWT authentication
  - File upload management

### Database
- **Neo4j Aura**
  ```
  DB1: Files
  - Binary storage
  - Version tracking
  - Content encoding
  
  DB2: Metadata
  - Graph relationships
  - User connections
  - Dataset linkages
  ```

### Frontend
- **Modern Web Interface**
  - Drag-and-drop uploads
  - Interactive data visualization
  - Real-time updates
  - Responsive design

## 📈 Workflow

### 1. Data Upload
```python
# Example workflow
dataset = DatasetMetadata(
    title="Flight Test Analysis",
    description="Urban air mobility test results",
    dataset_type=DatasetType.FLIGHT_DATA,
    share_level=ShareLevel.TEAM,
    tags=["UAM", "noise-analysis"],
    version="1.0",
    authors=["researcher_id"],
    teams=["research_team_id"]
)
```

### 2. Metadata Processing
- Automatic metadata extraction
- Tag suggestions
- Relationship mapping
- Version tracking

### 3. Sharing & Collaboration
```python
# Share settings
await data_manager.update_share_level(
    dataset_id="dataset_123",
    new_share_level=ShareLevel.GROUP,
    user_id="researcher_id"
)
```

## 🔜 Upcoming Features

### AI Integration
- **Intelligent Tagging**
  - Automated metadata suggestions
  - Content classification
  - Pattern recognition

### Advanced Search
- **Similarity Search**
  - Content-based matching
  - Related dataset discovery
  - Pattern identification

### Enhanced Visualization
- **Graph Exploration**
  - Dataset relationships
  - Research networks
  - Citation tracking

## 🚀 Getting Started

### Prerequisites
```bash
python 3.8+
neo4j-driver
fastapi
uvicorn
python-jose[cryptography]
```

### Installation
```bash
# Clone repository
git clone https://github.com/your-repo/aam-rdm.git

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export NEO4J_URI_FILES="your-aura-db1-uri"
export NEO4J_URI_META="your-aura-db2-uri"
export SECRET_KEY="your-secret-key"

# Run application
uvicorn main:app --reload
```

### Configuration
```python
# Update config.py with your settings
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    NEO4J_URI_FILES = os.getenv('NEO4J_URI_FILES')
    NEO4J_URI_META = os.getenv('NEO4J_URI_META')
```

## 📖 Documentation

### API Endpoints
```
POST /upload/           # Upload new dataset
GET  /file/{file_id}   # Retrieve file
GET  /files/           # List available files
POST /share/           # Update sharing settings
```

### Data Models
```python
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
    DRONE_DATA = "drone_data"
```

## 🤝 Contributing
1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open pull request

## 📝 License
This project is licensed under MIT License - see LICENSE file for details coming soon.

## 👥 Team
- **Rsearch Data Manager**: Ahlem makhebi
- **Contact**: ahlem.makhebi@tu-dresden.de

## 🙏 Acknowledgments
- Neo4j Team
- FastAPI Community
- RTG2947 Research Group

## 📞 Support
For support and questions:
- Documentation: [coming soon]
- Issues: GitHub Issues
- Email: ahlem.makhebi@gmail.com
