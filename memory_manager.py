"""
Memory Manager Component
Handles persistent storage and retrieval of lesson generation sessions
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path


class MemoryManager:
    """
    Manages persistent memory for the agentic lesson system
    Stores sessions, evaluations, and learns from feedback
    """
    
    def __init__(self, mongo_url: str, db_name: str):
        """
        Initialize the memory manager with MongoDB connection
        
        Args:
            mongo_url: MongoDB connection string
            db_name: Database name
        """
        self.client = AsyncIOMotorClient(mongo_url)
        self.db = self.client[db_name]
        self.sessions_collection = self.db.lesson_sessions
        self.evaluations_collection = self.db.lesson_evaluations
        self.feedback_collection = self.db.feedback_memory
        self.analytics_collection = self.db.analytics
    
    async def save_session(
        self,
        session_data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> str:
        """
        Save a complete generation session to memory
        
        Args:
            session_data: Complete session data from agentic system
            session_id: Optional session ID (generates one if not provided)
        
        Returns:
            The session ID
        """
        if session_id is None:
            session_id = self._generate_session_id()
        
        session_document = {
            "session_id": session_id,
            "topic": session_data.get("topic"),
            "final_lesson": session_data.get("final_lesson"),
            "final_evaluation": session_data.get("final_evaluation"),
            "total_iterations": session_data.get("total_iterations"),
            "success": session_data.get("success"),
            "session_history": session_data.get("session_history", []),
            "rejection_log": session_data.get("rejection_log", []),
            "metadata": session_data.get("metadata", {}),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await self.sessions_collection.update_one(
            {"session_id": session_id},
            {"$set": session_document},
            upsert=True
        )
        
        # Also save individual evaluations for analysis
        await self._save_evaluations(session_data, session_id)
        
        # Extract and save feedback patterns
        await self._save_feedback_patterns(session_data, session_id)
        
        # Update analytics
        await self._update_analytics(session_data)
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a session by ID
        
        Args:
            session_id: The session ID to retrieve
        
        Returns:
            Session data or None if not found
        """
        session = await self.sessions_collection.find_one(
            {"session_id": session_id},
            {"_id": 0}
        )
        return session
    
    async def get_recent_sessions(
        self,
        limit: int = 10,
        topic_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent sessions, optionally filtered by topic
        
        Args:
            limit: Maximum number of sessions to return
            topic_filter: Optional topic to filter by
        
        Returns:
            List of session summaries
        """
        query = {}
        if topic_filter:
            query["topic"] = {"$regex": topic_filter, "$options": "i"}
        
        cursor = self.sessions_collection.find(
            query,
            {"_id": 0, "session_id": 1, "topic": 1, "success": 1, 
             "total_iterations": 1, "created_at": 1}
        ).sort("created_at", -1).limit(limit)
        
        sessions = await cursor.to_list(length=limit)
        return sessions
    
    async def get_feedback_patterns(
        self,
        checkpoint_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get feedback patterns to learn from common failures
        
        Args:
            checkpoint_name: Optional specific checkpoint to analyze
        
        Returns:
            List of feedback patterns and improvement suggestions
        """
        query = {}
        if checkpoint_name:
            query["checkpoint_name"] = checkpoint_name
        
        cursor = self.feedback_collection.find(query).sort("frequency", -1)
        patterns = await cursor.to_list(length=50)
        
        # Convert ObjectId to string for JSON serialization
        for pattern in patterns:
            if "_id" in pattern:
                pattern["_id"] = str(pattern["_id"])
        
        return patterns
    
    async def get_learning_insights(self) -> Dict[str, Any]:
        """
        Get insights learned from previous sessions
        
        Returns:
            Dictionary containing learning insights and statistics
        """
        # Get overall statistics
        total_sessions = await self.sessions_collection.count_documents({})
        successful_sessions = await self.sessions_collection.count_documents({"success": True})
        
        # Get common failure points
        pipeline = [
            {"$unwind": "$rejection_log"},
            {"$unwind": "$rejection_log.failed_checkpoints"},
            {"$group": {
                "_id": "$rejection_log.failed_checkpoints.name",
                "frequency": {"$sum": 1},
                "recent_failures": {
                    "$push": {
                        "session_id": "$session_id",
                        "feedback": "$rejection_log.failed_checkpoints.feedback",
                        "timestamp": "$created_at"
                    }
                }
            }},
            {"$sort": {"frequency": -1}},
            {"$limit": 10}
        ]
        
        common_failures = await self.sessions_collection.aggregate(pipeline).to_list(10)
        
        # Get average iterations
        pipeline_avg = [
            {"$group": {
                "_id": None,
                "avg_iterations": {"$avg": "$total_iterations"},
                "max_iterations": {"$max": "$total_iterations"},
                "min_iterations": {"$min": "$total_iterations"}
            }}
        ]
        
        avg_stats = await self.sessions_collection.aggregate(pipeline_avg).to_list(1)
        iteration_stats = avg_stats[0] if avg_stats else {}
        
        return {
            "total_sessions": total_sessions,
            "success_rate": (successful_sessions / total_sessions * 100) if total_sessions > 0 else 0,
            "common_failure_points": common_failures,
            "iteration_statistics": {
                "average": iteration_stats.get("avg_iterations", 0),
                "maximum": iteration_stats.get("max_iterations", 0),
                "minimum": iteration_stats.get("min_iterations", 0)
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def _save_evaluations(self, session_data: Dict[str, Any], session_id: str):
        """Save individual evaluations from session history"""
        for history_entry in session_data.get("session_history", []):
            evaluation_doc = {
                "session_id": session_id,
                "iteration": history_entry.get("iteration"),
                "evaluation": history_entry.get("evaluation", {}),
                "generation": history_entry.get("generation", {}),
                "timestamp": history_entry.get("timestamp")
            }
            
            await self.evaluations_collection.insert_one(evaluation_doc)
    
    async def _save_feedback_patterns(self, session_data: Dict[str, Any], session_id: str):
        """Extract and save feedback patterns for learning"""
        for rejection in session_data.get("rejection_log", []):
            for failed_checkpoint in rejection.get("failed_checkpoints", []):
                checkpoint_name = failed_checkpoint.get("name")
                feedback = failed_checkpoint.get("feedback", "")
                suggestions = failed_checkpoint.get("suggestions", [])
                
                # Update or insert feedback pattern
                await self.feedback_collection.update_one(
                    {
                        "checkpoint_name": checkpoint_name,
                        "feedback_pattern": feedback[:100]  # First 100 chars as pattern key
                    },
                    {
                        "$inc": {"frequency": 1},
                        "$set": {
                            "last_seen": datetime.utcnow(),
                            "suggestions": suggestions
                        },
                        "$push": {
                            "session_ids": session_id,
                            "timestamps": datetime.utcnow()
                        }
                    },
                    upsert=True
                )
    
    async def _update_analytics(self, session_data: Dict[str, Any]):
        """Update analytics with session data"""
        analytics_doc = {
            "session_id": session_data.get("session_id"),
            "topic": session_data.get("topic"),
            "success": session_data.get("success"),
            "total_iterations": session_data.get("total_iterations"),
            "final_pass_rate": session_data.get("final_evaluation", {}).get("pass_rate", 0),
            "timestamp": datetime.utcnow()
        }
        
        await self.analytics_collection.insert_one(analytics_doc)
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        import uuid
        return str(uuid.uuid4())
    
    async def export_session_to_file(
        self,
        session_id: str,
        filepath: str
    ) -> bool:
        """
        Export a session to a JSON file
        
        Args:
            session_id: The session ID to export
            filepath: The file path to export to
        
        Returns:
            True if successful, False otherwise
        """
        try:
            session = await self.get_session(session_id)
            if not session:
                return False
            
            # Convert datetime objects to ISO strings
            session = self._serialize_datetime(session)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(session, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error exporting session: {str(e)}")
            return False
    
    def _serialize_datetime(self, obj: Any) -> Any:
        """Convert datetime objects to ISO strings in nested structures"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._serialize_datetime(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetime(item) for item in obj]
        else:
            return obj
    
    async def close(self):
        """Close the database connection"""
        self.client.close()