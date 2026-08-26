"""
Evaluation Rubric for Self-Evaluating Lesson Generator
Designed for beginner-friendly content assessment with pass/fail checkpoints
"""

from typing import Dict, List, Any
from enum import Enum


class CheckpointStatus(Enum):
    PASS = "pass"
    FAIL = "fail"


class EvaluationCheckpoint:
    """Individual evaluation checkpoint with pass/fail criteria"""
    
    def __init__(self, name: str, description: str, category: str):
        self.name = name
        self.description = description
        self.category = category
        self.status = CheckpointStatus.FAIL
        self.feedback = ""
        self.suggestions = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "status": self.status.value,
            "feedback": self.feedback,
            "suggestions": self.suggestions
        }


class LessonRubric:
    """Comprehensive rubric for evaluating beginner lesson content"""
    
    def __init__(self):
        self.checkpoints = self._initialize_checkpoints()
    
    def _initialize_checkpoints(self) -> List[EvaluationCheckpoint]:
        """Initialize all evaluation checkpoints"""
        return [
            # Accuracy & Groundedness
            EvaluationCheckpoint(
                "factual_accuracy",
                "All technical claims are factually accurate and up-to-date",
                "accuracy"
            ),
            EvaluationCheckpoint(
                "concept_clarity",
                "Core concepts are explained clearly without ambiguity",
                "accuracy"
            ),
            EvaluationCheckpoint(
                "no_hallucinations",
                "No fabricated information or false claims about the topic",
                "accuracy"
            ),
            
            # Beginner-Friendly Language
            EvaluationCheckpoint(
                "simple_vocabulary",
                "Uses simple, everyday language appropriate for 12th-grade level",
                "beginner_friendly"
            ),
            EvaluationCheckpoint(
                "no_assumptions",
                "Does not assume prior knowledge of the topic",
                "beginner_friendly"
            ),
            EvaluationCheckpoint(
                "gradual_complexity",
                "Starts simple and gradually increases complexity",
                "beginner_friendly"
            ),
            
            # Teaches by Example
            EvaluationCheckpoint(
                "concrete_examples",
                "Includes concrete, relatable examples to illustrate concepts",
                "examples"
            ),
            EvaluationCheckpoint(
                "analogy_usage",
                "Uses analogies to relate new concepts to familiar ones",
                "examples"
            ),
            EvaluationCheckpoint(
                "step_by_step",
                "Breaks down complex processes into clear steps",
                "examples"
            ),
            
            # Jargon Management
            EvaluationCheckpoint(
                "jargon_explained",
                "All technical terms are explained when first introduced",
                "jargon"
            ),
            EvaluationCheckpoint(
                "minimal_jargon",
                "Uses technical jargon only when necessary",
                "jargon"
            ),
            EvaluationCheckpoint(
                "glossary_provided",
                "Key terms are summarized or highlighted for easy reference",
                "jargon"
            ),
            
            # Key Points Coverage
            EvaluationCheckpoint(
                "what_is_covered",
                "Clearly explains what the topic is",
                "coverage"
            ),
            EvaluationCheckpoint(
                "why_matters_covered",
                "Explains why the topic is important or useful",
                "coverage"
            ),
            EvaluationCheckpoint(
                "how_works_covered",
                "Explains how the topic works in practice",
                "coverage"
            ),
            EvaluationCheckpoint(
                "use_cases_covered",
                "Provides real-world use cases or applications",
                "coverage"
            ),
            
            # Coherent Teaching Flow
            EvaluationCheckpoint(
                "logical_structure",
                "Content follows a logical progression from basic to advanced",
                "flow"
            ),
            EvaluationCheckpoint(
                "smooth_transitions",
                "Smooth transitions between sections and concepts",
                "flow"
            ),
            EvaluationCheckpoint(
                "conclusion_summary",
                "Ends with a summary or key takeaways",
                "flow"
            ),
            EvaluationCheckpoint(
                "appropriate_length",
                "Content is appropriately detailed without being overwhelming",
                "flow"
            )
        ]
    
    def get_checkpoint_by_name(self, name: str) -> EvaluationCheckpoint:
        """Get a specific checkpoint by name"""
        for checkpoint in self.checkpoints:
            if checkpoint.name == name:
                return checkpoint
        raise ValueError(f"Checkpoint '{name}' not found")
    
    def get_checkpoints_by_category(self, category: str) -> List[EvaluationCheckpoint]:
        """Get all checkpoints in a specific category"""
        return [cp for cp in self.checkpoints if cp.category == category]
    
    def get_failed_checkpoints(self) -> List[EvaluationCheckpoint]:
        """Get all checkpoints that failed"""
        return [cp for cp in self.checkpoints if cp.status == CheckpointStatus.FAIL]
    
    def get_passed_checkpoints(self) -> List[EvaluationCheckpoint]:
        """Get all checkpoints that passed"""
        return [cp for cp in self.checkpoints if cp.status == CheckpointStatus.PASS]
    
    def calculate_pass_rate(self) -> float:
        """Calculate the percentage of passed checkpoints"""
        if not self.checkpoints:
            return 0.0
        passed = len(self.get_passed_checkpoints())
        return (passed / len(self.checkpoints)) * 100
    
    def all_passed(self) -> bool:
        """Check if all checkpoints passed"""
        return all(cp.status == CheckpointStatus.PASS for cp in self.checkpoints)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rubric to dictionary format"""
        return {
            "checkpoints": [cp.to_dict() for cp in self.checkpoints],
            "pass_rate": self.calculate_pass_rate(),
            "all_passed": self.all_passed(),
            "total_checkpoints": len(self.checkpoints),
            "passed_count": len(self.get_passed_checkpoints()),
            "failed_count": len(self.get_failed_checkpoints())
        }


class EvaluationResult:
    """Result of lesson evaluation"""
    
    def __init__(self, rubric: LessonRubric, lesson_content: str, iteration: int):
        self.rubric = rubric
        self.lesson_content = lesson_content
        self.iteration = iteration
        self.passed = rubric.all_passed()
        self.pass_rate = rubric.calculate_pass_rate()
        self.failed_checkpoints = rubric.get_failed_checkpoints()
        self.timestamp = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert evaluation result to dictionary"""
        return {
            "iteration": self.iteration,
            "passed": self.passed,
            "pass_rate": self.pass_rate,
            "failed_checkpoints": [cp.to_dict() for cp in self.failed_checkpoints],
            "rubric_summary": self.rubric.to_dict(),
            "timestamp": self.timestamp
        }
    
    def get_regeneration_feedback(self) -> str:
        """Generate feedback for regeneration based on failed checkpoints"""
        if not self.failed_checkpoints:
            return "All checkpoints passed. No regeneration needed."
        
        feedback_parts = ["The lesson needs improvement in the following areas:"]
        
        for checkpoint in self.failed_checkpoints:
            feedback_parts.append(f"\n- {checkpoint.name}: {checkpoint.description}")
            if checkpoint.feedback:
                feedback_parts.append(f"  Issue: {checkpoint.feedback}")
            if checkpoint.suggestions:
                feedback_parts.append(f"  Suggestions: {', '.join(checkpoint.suggestions)}")
        
        return "\n".join(feedback_parts)