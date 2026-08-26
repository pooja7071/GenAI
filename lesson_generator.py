"""
Lesson Generator Component
Generates beginner-friendly lessons on given topics using AI
"""

import os
from typing import Dict, Any, Optional
from openai import OpenAI
from datetime import datetime


class LessonGenerator:
    """Generates beginner lessons for specified topics"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the lesson generator with OpenAI client"""
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o"  # Using GPT-4o for better quality
    
    def generate_lesson(
        self, 
        topic: str, 
        feedback: Optional[str] = None,
        iteration: int = 1
    ) -> Dict[str, Any]:
        """
        Generate a beginner lesson for the given topic
        
        Args:
            topic: The topic to teach (e.g., "RAG (Retrieval-Augmented Generation)")
            feedback: Optional feedback from previous evaluation to improve the lesson
            iteration: Current iteration number (for logging purposes)
        
        Returns:
            Dictionary containing the generated lesson and metadata
        """
        
        base_prompt = self._create_base_prompt(topic)
        
        if feedback and iteration > 1:
            prompt = self._create_improvement_prompt(base_prompt, feedback)
        else:
            prompt = base_prompt
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert educational content creator specializing in making complex topics accessible to beginners. Your audience is 12th-grade students from India with limited English vocabulary and non-English-medium backgrounds."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            if not response.choices or len(response.choices) == 0:
                raise Exception("No response generated from API")
            
            lesson_content = response.choices[0].message.content
            if not lesson_content:
                raise Exception("Empty content generated from API")
            
            return {
                "content": lesson_content,
                "topic": topic,
                "iteration": iteration,
                "timestamp": datetime.utcnow().isoformat(),
                "model_used": self.model,
                "tokens_used": response.usage.total_tokens if response.usage else 0
            }
            
        except Exception as e:
            raise Exception(f"Failed to generate lesson: {str(e)}")
    
    def _create_base_prompt(self, topic: str) -> str:
        """Create the base prompt for lesson generation"""
        return f"""
Create a comprehensive beginner lesson about: {topic}

Target Audience:
- 12th-grade graduate from India
- Limited English vocabulary
- Non-English-medium background
- No prior knowledge of this topic

Lesson Requirements:
1. Start with a simple explanation of what the topic is
2. Explain why this topic matters and is useful
3. Break down how it works in simple terms
4. Use concrete examples and analogies
5. Explain any technical terms when you first use them
6. Use simple, everyday language
7. Include real-world applications or use cases
8. End with a summary of key points

Structure your lesson with clear headings and paragraphs. Keep explanations gradual - start simple and build complexity slowly.

Length: Aim for 800-1200 words to be comprehensive but not overwhelming.
"""
    
    def _create_improvement_prompt(self, base_prompt: str, feedback: str) -> str:
        """Create a prompt for improving an existing lesson based on feedback"""
        return f"""
{base_prompt}

FEEDBACK FOR IMPROVEMENT:
{feedback}

Please regenerate the lesson addressing these specific issues. Focus on improving the areas mentioned in the feedback while maintaining the beginner-friendly approach.
"""
    
    def generate_with_context(
        self,
        topic: str,
        additional_context: str,
        feedback: Optional[str] = None,
        iteration: int = 1
    ) -> Dict[str, Any]:
        """
        Generate a lesson with additional context
        
        Args:
            topic: The topic to teach
            additional_context: Extra context or requirements for the lesson
            feedback: Optional feedback from previous evaluation
            iteration: Current iteration number
        
        Returns:
            Dictionary containing the generated lesson and metadata
        """
        base_prompt = self._create_base_prompt(topic)
        enhanced_prompt = f"{base_prompt}\n\nADDITIONAL CONTEXT:\n{additional_context}"
        
        if feedback and iteration > 1:
            enhanced_prompt = self._create_improvement_prompt(enhanced_prompt, feedback)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert educational content creator specializing in making complex topics accessible to beginners."
                    },
                    {
                        "role": "user",
                        "content": enhanced_prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            lesson_content = response.choices[0].message.content
            
            return {
                "content": lesson_content,
                "topic": topic,
                "iteration": iteration,
                "timestamp": datetime.utcnow().isoformat(),
                "model_used": self.model,
                "tokens_used": response.usage.total_tokens if response.usage else 0,
                "additional_context_provided": True
            }
            
        except Exception as e:
            raise Exception(f"Failed to generate lesson with context: {str(e)}")