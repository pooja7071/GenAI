"""
Lesson Evaluator Component
Evaluates generated lessons against the rubric using AI
"""

import os
from typing import Dict, Any, Optional
from openai import OpenAI
from datetime import datetime
from evaluation_rubric import LessonRubric, EvaluationCheckpoint, CheckpointStatus
import json


class LessonEvaluator:
    """Evaluates lessons against the rubric using AI"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the lesson evaluator with OpenAI client"""
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o"
        self.rubric = LessonRubric()
    
    def evaluate_lesson(
        self,
        lesson_content: str,
        topic: str,
        iteration: int = 1
    ) -> Dict[str, Any]:
        """
        Evaluate a lesson against the rubric
        
        Args:
            lesson_content: The generated lesson content
            topic: The topic of the lesson
            iteration: Current iteration number
        
        Returns:
            Dictionary containing evaluation results
        """
        evaluation_prompt = self._create_evaluation_prompt(lesson_content, topic)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert educational content evaluator. Your role is to assess lesson content against specific quality criteria for beginner learners."
                    },
                    {
                        "role": "user",
                        "content": evaluation_prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent evaluation
                max_tokens=2500
            )
            
            if not response.choices or len(response.choices) == 0:
                raise Exception("No evaluation response generated from API")
            
            evaluation_result = response.choices[0].message.content
            if not evaluation_result:
                raise Exception("Empty evaluation content generated from API")
            parsed_results = self._parse_evaluation_results(evaluation_result)
            
            # Update rubric with parsed results
            self._update_rubric_with_results(parsed_results)
            
            from evaluation_rubric import EvaluationResult
            result = EvaluationResult(self.rubric, lesson_content, iteration)
            result.timestamp = datetime.utcnow().isoformat()
            
            return {
                "evaluation_result": result.to_dict(),
                "raw_evaluation": evaluation_result,
                "topic": topic,
                "iteration": iteration,
                "timestamp": datetime.utcnow().isoformat(),
                "model_used": self.model
            }
            
        except Exception as e:
            raise Exception(f"Failed to evaluate lesson: {str(e)}")
    
    def _create_evaluation_prompt(self, lesson_content: str, topic: str) -> str:
        """Create the evaluation prompt"""
        checkpoints_desc = self._get_checkpoints_description()
        
        return f"""
Evaluate the following beginner lesson about "{topic}" against these specific checkpoints:

{checkpoints_desc}

LESSON TO EVALUATE:
{lesson_content}

For each checkpoint:
1. Determine if it PASS or FAIL (be strict - no partial credit)
2. If FAIL, provide specific feedback explaining why
3. If FAIL, provide 1-2 specific suggestions for improvement

Format your response as JSON like this:
{{
  "evaluations": [
    {{
      "checkpoint_name": "factual_accuracy",
      "status": "pass",
      "feedback": "",
      "suggestions": []
    }},
    {{
      "checkpoint_name": "simple_vocabulary",
      "status": "fail",
      "feedback": "Uses too many technical terms without explanation",
      "suggestions": ["Replace 'vector embeddings' with 'number representations'", "Explain 'semantic search' in simpler terms"]
    }}
  ]
}}

Be thorough but fair. The target audience is 12th-grade students with limited English vocabulary.
"""
    
    def _get_checkpoints_description(self) -> str:
        """Get formatted description of all checkpoints"""
        descriptions = []
        for checkpoint in self.rubric.checkpoints:
            descriptions.append(
                f"- {checkpoint.name} ({checkpoint.category}): {checkpoint.description}"
            )
        return "\n".join(descriptions)
    
    def _parse_evaluation_results(self, raw_evaluation: str) -> Dict[str, Any]:
        """Parse the JSON evaluation results"""
        try:
            # Extract JSON from the response (in case there's extra text)
            json_start = raw_evaluation.find('{')
            json_end = raw_evaluation.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = raw_evaluation[json_start:json_end]
                return json.loads(json_str)
            else:
                # Fallback: try to parse the whole response as JSON
                return json.loads(raw_evaluation)
                
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse evaluation results as JSON: {str(e)}")
    
    def _update_rubric_with_results(self, parsed_results: Dict[str, Any]):
        """Update the rubric with evaluation results"""
        evaluations = parsed_results.get("evaluations", [])
        
        for evaluation in evaluations:
            checkpoint_name = evaluation.get("checkpoint_name")
            status = evaluation.get("status", "fail").lower()
            feedback = evaluation.get("feedback", "")
            suggestions = evaluation.get("suggestions", [])
            
            try:
                checkpoint = self.rubric.get_checkpoint_by_name(checkpoint_name)
                checkpoint.status = CheckpointStatus.PASS if status == "pass" else CheckpointStatus.FAIL
                checkpoint.feedback = feedback
                checkpoint.suggestions = suggestions
            except ValueError:
                # Checkpoint not found, skip
                continue
    
    def evaluate_quick_check(
        self,
        lesson_content: str,
        topic: str
    ) -> Dict[str, Any]:
        """
        Perform a quick evaluation focusing on critical checkpoints only
        
        Args:
            lesson_content: The generated lesson content
            topic: The topic of the lesson
        
        Returns:
            Dictionary containing quick evaluation results
        """
        critical_checkpoints = [
            "factual_accuracy",
            "simple_vocabulary",
            "no_assumptions",
            "what_is_covered",
            "why_matters_covered",
            "how_works_covered"
        ]
        
        quick_prompt = f"""
Quick evaluation of lesson about "{topic}" focusing on these critical areas:
- Factual accuracy
- Simple vocabulary for beginners
- No assumptions of prior knowledge
- Covers what the topic is
- Covers why it matters
- Covers how it works

LESSON:
{lesson_content}

For each critical area, indicate PASS or FAIL with brief explanation. Format as JSON:
{{
  "critical_evaluations": {{
    "factual_accuracy": {{"status": "pass", "feedback": ""}},
    "simple_vocabulary": {{"status": "fail", "feedback": "Uses complex terminology"}}
  }}
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a quick content evaluator focusing on critical quality checkpoints."
                    },
                    {
                        "role": "user",
                        "content": quick_prompt
                    }
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            if not response.choices or len(response.choices) == 0:
                raise Exception("No quick evaluation response generated from API")
            
            result = response.choices[0].message.content
            if not result:
                raise Exception("Empty quick evaluation content generated from API")
            return {
                "quick_evaluation": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Failed to perform quick evaluation: {str(e)}")