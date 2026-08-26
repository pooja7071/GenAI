from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from agentic_system import AgenticLessonSystem
from memory_manager import MemoryManager


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize Memory Manager
memory_manager = MemoryManager(mongo_url, os.environ['DB_NAME'])

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# Agentic System Models
class LessonGenerationRequest(BaseModel):
    topic: str = Field(..., description="The topic to generate a lesson for")
    additional_context: Optional[str] = Field(None, description="Additional context for lesson generation")
    max_iterations: int = Field(3, description="Maximum number of generate-evaluate cycles")
    min_pass_rate: float = Field(100.0, description="Minimum pass rate to accept lesson")

class LessonGenerationResponse(BaseModel):
    topic: str
    final_lesson: str
    final_evaluation: dict
    session_history: list
    rejection_log: list
    total_iterations: int
    success: bool
    metadata: dict
    session_id: Optional[str] = None

class SessionListResponse(BaseModel):
    sessions: List[dict]
    total_count: int

class LearningInsightsResponse(BaseModel):
    total_sessions: int
    success_rate: float
    common_failure_points: list
    iteration_statistics: dict
    generated_at: str

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

# Agentic System Endpoints
@api_router.post("/generate-lesson", response_model=LessonGenerationResponse)
async def generate_lesson(request: LessonGenerationRequest, background_tasks: BackgroundTasks):
    """
    Generate a self-evaluating lesson for the given topic
    """
    try:
        # Initialize agentic system with memory manager
        system = AgenticLessonSystem(
            max_iterations=request.max_iterations,
            min_pass_rate=request.min_pass_rate,
            memory_manager=memory_manager
        )
        
        # Generate the lesson
        result = system.generate_lesson(
            topic=request.topic,
            additional_context=request.additional_context
        )
        
        # Save to memory in background
        if result:
            background_tasks.add_task(system.save_to_memory, result)
        
        # Prepare response
        response = LessonGenerationResponse(
            topic=result["topic"],
            final_lesson=result["final_lesson"],
            final_evaluation=result["final_evaluation"],
            session_history=result["session_history"],
            rejection_log=result["rejection_log"],
            total_iterations=result["total_iterations"],
            success=result["success"],
            metadata=result["metadata"],
            session_id=system.session_id
        )
        
        return response
        
    except Exception as e:
        logging.error(f"Error generating lesson: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate lesson: {str(e)}")

@api_router.get("/sessions", response_model=SessionListResponse)
async def get_sessions(limit: int = 10, topic_filter: Optional[str] = None):
    """
    Get recent lesson generation sessions
    """
    try:
        sessions = await memory_manager.get_recent_sessions(limit, topic_filter)
        total_count = len(sessions)
        
        return SessionListResponse(
            sessions=sessions,
            total_count=total_count
        )
    except Exception as e:
        logging.error(f"Error fetching sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch sessions: {str(e)}")

@api_router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Get details of a specific session
    """
    try:
        session = await memory_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch session: {str(e)}")

@api_router.get("/insights", response_model=LearningInsightsResponse)
async def get_insights():
    """
    Get learning insights from previous sessions
    """
    try:
        insights = await memory_manager.get_learning_insights()
        return LearningInsightsResponse(**insights)
    except Exception as e:
        logging.error(f"Error fetching insights: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch insights: {str(e)}")

@api_router.get("/feedback-patterns")
async def get_feedback_patterns(checkpoint_name: Optional[str] = None):
    """
    Get feedback patterns for learning from common failures
    """
    try:
        patterns = await memory_manager.get_feedback_patterns(checkpoint_name)
        return {"patterns": patterns}
    except Exception as e:
        logging.error(f"Error fetching feedback patterns: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch feedback patterns: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    await memory_manager.close()
    client.close()

