"""
Agentic System - Generate → Evaluate → Regenerate Loop
Main component that orchestrates the self-evaluating lesson generation
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from lesson_generator import LessonGenerator
from lesson_evaluator import LessonEvaluator
from evaluation_rubric import EvaluationResult
from memory_manager import MemoryManager
import json


class AgenticLessonSystem:
    """
    Self-evaluating lesson generation system
    Implements the generate → evaluate → regenerate loop
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        max_iterations: int = 3,
        min_pass_rate: float = 100.0,
        memory_manager: Optional[MemoryManager] = None
    ):
        """
        Initialize the agentic system
        
        Args:
            openai_api_key: OpenAI API key (falls back to environment variable)
            max_iterations: Maximum number of generate-evaluate cycles
            min_pass_rate: Minimum pass rate (0-100) to accept a lesson
            memory_manager: Optional memory manager for persistent storage
        """
        self.api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided")
        
        self.generator = LessonGenerator(api_key=self.api_key)
        self.evaluator = LessonEvaluator(api_key=self.api_key)
        self.max_iterations = max_iterations
        self.min_pass_rate = min_pass_rate
        self.memory_manager = memory_manager
        
        # Memory system
        self.session_history = []
        self.rejection_log = []
        self.final_lesson = None
        self.final_evaluation = None
        self.session_id = None
    
    def generate_lesson(
        self,
        topic: str,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a self-evaluated lesson for the given topic
        
        Args:
            topic: The topic to generate a lesson for
            additional_context: Optional additional context for generation
        
        Returns:
            Dictionary containing the final lesson and complete process log
        """
        print(f"Starting agentic lesson generation for topic: {topic}")
        print(f"Max iterations: {self.max_iterations}, Min pass rate: {self.min_pass_rate}%")
        
        current_lesson = None
        current_evaluation = None
        feedback = None
        
        for iteration in range(1, self.max_iterations + 1):
            print(f"\n--- Iteration {iteration} ---")
            
            # GENERATE phase
            print("Generating lesson...")
            if additional_context:
                generation_result = self.generator.generate_with_context(
                    topic=topic,
                    additional_context=additional_context,
                    feedback=feedback,
                    iteration=iteration
                )
            else:
                generation_result = self.generator.generate(
                    topic=topic,
                    feedback=feedback,
                    iteration=iteration
                )
            
            current_lesson = generation_result["content"]
            print(f"Lesson generated (tokens: {generation_result['tokens_used']})")
            
            # EVALUATE phase
            print("Evaluating lesson...")
            evaluation_result = self.evaluator.evaluate_lesson(
                lesson_content=current_lesson,
                topic=topic,
                iteration=iteration
            )
            
            current_evaluation = evaluation_result["evaluation_result"]
            eval_result_obj = EvaluationResult(
                self.evaluator.rubric,
                current_lesson,
                iteration
            )
            eval_result_obj.timestamp = evaluation_result["timestamp"]
            
            pass_rate = current_evaluation["pass_rate"]
            all_passed = current_evaluation["all_passed"]
            
            print(f"Evaluation complete: {pass_rate:.1f}% pass rate")
            print(f"Checkpoints passed: {current_evaluation['rubric_summary']['passed_count']}/{current_evaluation['rubric_summary']['total_checkpoints']}")
            
            # Store in session history
            session_entry = {
                "iteration": iteration,
                "generation": generation_result,
                "evaluation": evaluation_result,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.session_history.append(session_entry)
            
            # Check if lesson passes criteria
            if all_passed and pass_rate >= self.min_pass_rate:
                print("✓ Lesson meets all quality criteria!")
                self.final_lesson = current_lesson
                self.final_evaluation = current_evaluation
                break
            
            # REGENERATE phase (if not final iteration)
            if iteration < self.max_iterations:
                print("Lesson did not meet criteria. Preparing for regeneration...")
                
                # Log rejection
                rejection_entry = {
                    "iteration": iteration,
                    "pass_rate": pass_rate,
                    "failed_checkpoints": current_evaluation["failed_checkpoints"],
                    "feedback": eval_result_obj.get_regeneration_feedback(),
                    "timestamp": datetime.utcnow().isoformat()
                }
                self.rejection_log.append(rejection_entry)
                
                # Generate feedback for next iteration
                feedback = eval_result_obj.get_regeneration_feedback()
                print(f"Feedback for regeneration: {len(feedback)} characters")
            else:
                print("Reached maximum iterations. Returning best available lesson.")
                self.final_lesson = current_lesson
                self.final_evaluation = current_evaluation
                
                # Final rejection log
                rejection_entry = {
                    "iteration": iteration,
                    "pass_rate": pass_rate,
                    "failed_checkpoints": current_evaluation["failed_checkpoints"],
                    "feedback": "Max iterations reached",
                    "timestamp": datetime.utcnow().isoformat()
                }
                self.rejection_log.append(rejection_entry)
        
        # Prepare final result
        result = {
            "topic": topic,
            "final_lesson": self.final_lesson,
            "final_evaluation": self.final_evaluation,
            "session_history": self.session_history,
            "rejection_log": self.rejection_log,
            "total_iterations": len(self.session_history),
            "success": self.final_evaluation["all_passed"] if self.final_evaluation else False,
            "metadata": {
                "max_iterations": self.max_iterations,
                "min_pass_rate": self.min_pass_rate,
                "completion_time": datetime.utcnow().isoformat()
            }
        }
        
        print(f"\n--- Process Complete ---")
        print(f"Total iterations: {result['total_iterations']}")
        print(f"Success: {result['success']}")
        print(f"Final pass rate: {self.final_evaluation['pass_rate']:.1f}%")
        
        return result
    
    def get_rejection_summary(self) -> Dict[str, Any]:
        """Get a summary of all rejections and improvements made"""
        if not self.rejection_log:
            return {"message": "No rejections - lesson passed on first attempt"}
        
        summary = {
            "total_rejections": len(self.rejection_log),
            "improvement_trajectory": [],
            "common_failure_points": {},
            "total_improvements": 0
        }
        
        # Track improvement trajectory
        previous_pass_rate = 0
        for rejection in self.rejection_log:
            current_pass_rate = rejection["pass_rate"]
            improvement = current_pass_rate - previous_pass_rate
            previous_pass_rate = current_pass_rate
            
            summary["improvement_trajectory"].append({
                "iteration": rejection["iteration"],
                "pass_rate": current_pass_rate,
                "improvement": improvement,
                "failed_count": len(rejection["failed_checkpoints"])
            })
            
            # Track common failure points
            for failed_checkpoint in rejection["failed_checkpoints"]:
                checkpoint_name = failed_checkpoint["name"]
                if checkpoint_name not in summary["common_failure_points"]:
                    summary["common_failure_points"][checkpoint_name] = 0
                summary["common_failure_points"][checkpoint_name] += 1
        
        summary["total_improvements"] = sum(
            1 for traj in summary["improvement_trajectory"] 
            if traj["improvement"] > 0
        )
        
        return summary
    
    def export_session(self, filepath: str):
        """Export the complete session to a JSON file"""
        session_data = {
            "final_lesson": self.final_lesson,
            "final_evaluation": self.final_evaluation,
            "session_history": self.session_history,
            "rejection_log": self.rejection_log,
            "rejection_summary": self.get_rejection_summary(),
            "export_timestamp": datetime.utcnow().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        print(f"Session exported to {filepath}")
    
    def get_final_lesson_formatted(self) -> str:
        """Get the final lesson in a clean format"""
        if not self.final_lesson:
            return "No lesson generated yet."
        
        return f"""
# Lesson: {self.session_history[0]['generation']['topic'] if self.session_history else 'Unknown Topic'}

## Quality Metrics
- Pass Rate: {self.final_evaluation['pass_rate']:.1f}%
- Checkpoints Passed: {self.final_evaluation['rubric_summary']['passed_count']}/{self.final_evaluation['rubric_summary']['total_checkpoints']}
- Iterations Required: {len(self.session_history)}

## Lesson Content

{self.final_lesson}

---
Generated by Self-Evaluating Lesson Generator
Evaluation completed: {self.final_evaluation.get('timestamp', 'Unknown')}
"""
    
    def reset_session(self):
        """Reset the session for a new generation"""
        self.session_history = []
        self.rejection_log = []
        self.final_lesson = None
        self.final_evaluation = None
        self.session_id = None
        print("Session reset. Ready for new generation.")
    
    async def save_to_memory(self, session_data: Dict[str, Any]) -> Optional[str]:
        """
        Save the current session to memory
        
        Args:
            session_data: The session data to save
        
        Returns:
            Session ID if successful, None otherwise
        """
        if not self.memory_manager:
            print("Memory manager not configured. Skipping save.")
            return None
        
        try:
            session_id = await self.memory_manager.save_session(session_data)
            self.session_id = session_id
            print(f"Session saved to memory with ID: {session_id}")
            return session_id
        except Exception as e:
            print(f"Error saving to memory: {str(e)}")
            return None
    
    async def load_from_memory(self, session_id: str) -> bool:
        """
        Load a session from memory
        
        Args:
            session_id: The session ID to load
        
        Returns:
            True if successful, False otherwise
        """
        if not self.memory_manager:
            print("Memory manager not configured. Cannot load session.")
            return False
        
        try:
            session_data = await self.memory_manager.get_session(session_id)
            if not session_data:
                print(f"Session {session_id} not found.")
                return False
            
            # Restore session state
            self.session_history = session_data.get("session_history", [])
            self.rejection_log = session_data.get("rejection_log", [])
            self.final_lesson = session_data.get("final_lesson")
            self.final_evaluation = session_data.get("final_evaluation")
            self.session_id = session_id
            
            print(f"Session {session_id} loaded successfully.")
            return True
        except Exception as e:
            print(f"Error loading from memory: {str(e)}")
            return False