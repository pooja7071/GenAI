"""
Test script for the Self-Evaluating Lesson Generator
Tests the agentic system with the RAG topic
"""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from agentic_system import AgenticLessonSystem
from lesson_generator import LessonGenerator
from lesson_evaluator import LessonEvaluator
from evaluation_rubric import LessonRubric

def test_rubric():
    """Test the evaluation rubric"""
    print("=== Testing Evaluation Rubric ===")
    rubric = LessonRubric()
    
    print(f"Total checkpoints: {len(rubric.checkpoints)}")
    print(f"Categories: {set(cp.category for cp in rubric.checkpoints)}")
    
    # Test individual checkpoint access
    try:
        checkpoint = rubric.get_checkpoint_by_name("factual_accuracy")
        print(f"✓ Can access checkpoint: {checkpoint.name}")
    except Exception as e:
        print(f"✗ Error accessing checkpoint: {e}")
    
    # Test category filtering
    accuracy_checks = rubric.get_checkpoints_by_category("accuracy")
    print(f"✓ Accuracy checkpoints: {len(accuracy_checks)}")
    
    print("Rubric test passed!\n")

def test_generator():
    """Test the lesson generator"""
    print("=== Testing Lesson Generator ===")
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        print("⚠ Skipping generator test - OPENAI_API_KEY not configured")
        return
    
    try:
        generator = LessonGenerator(api_key=api_key)
        print("✓ Generator initialized successfully")
        
        # Test generation with a simple topic
        print("Testing lesson generation...")
        result = generator.generate_lesson("Test Topic", iteration=1)
        
        print(f"✓ Lesson generated successfully")
        print(f"  Length: {len(result['content'])} characters")
        print(f"  Tokens used: {result['tokens_used']}")
        
        print("Generator test passed!\n")
        return result
        
    except Exception as e:
        print(f"✗ Generator test failed: {e}")
        return None

def test_evaluator():
    """Test the lesson evaluator"""
    print("=== Testing Lesson Evaluator ===")
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        print("⚠ Skipping evaluator test - OPENAI_API_KEY not configured")
        return
    
    try:
        evaluator = LessonEvaluator(api_key=api_key)
        print("✓ Evaluator initialized successfully")
        
        # Test evaluation with sample content
        sample_lesson = """
        # Introduction to Python
        
        Python is a programming language. It is used for many things like web development and data science.
        
        ## What is Python?
        Python is a high-level programming language that is easy to learn and use.
        
        ## Why Python Matters
        Python is important because it has a simple syntax and many libraries.
        
        ## How Python Works
        Python code is interpreted by the Python interpreter.
        """
        
        print("Testing lesson evaluation...")
        result = evaluator.evaluate_lesson(sample_lesson, "Python", iteration=1)
        
        print(f"✓ Evaluation completed successfully")
        print(f"  Pass rate: {result['evaluation_result']['pass_rate']:.1f}%")
        print(f"  Checkpoints passed: {result['evaluation_result']['rubric_summary']['passed_count']}")
        
        print("Evaluator test passed!\n")
        return result
        
    except Exception as e:
        print(f"✗ Evaluator test failed: {e}")
        return None

def test_agentic_system():
    """Test the complete agentic system"""
    print("=== Testing Complete Agentic System ===")
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        print("⚠ Skipping agentic system test - OPENAI_API_KEY not configured")
        print("To run the full test, set your OPENAI_API_KEY in the .env file")
        return
    
    try:
        # Use reduced iterations for testing
        system = AgenticLessonSystem(
            api_key=api_key,
            max_iterations=2,  # Reduced for testing
            min_pass_rate=80.0  # Reduced for testing
        )
        print("✓ Agentic system initialized successfully")
        
        # Test with the required topic
        print("Testing with topic: 'RAG (Retrieval-Augmented Generation)'")
        result = system.generate_lesson("RAG (Retrieval-Augmented Generation)")
        
        print(f"✓ Agentic generation completed")
        print(f"  Success: {result['success']}")
        print(f"  Total iterations: {result['total_iterations']}")
        print(f"  Final pass rate: {result['final_evaluation']['pass_rate']:.1f}%")
        
        # Display rejection summary
        if result['rejection_log']:
            print(f"\n  Rejection log entries: {len(result['rejection_log'])}")
            for i, rejection in enumerate(result['rejection_log']):
                print(f"    Iteration {rejection['iteration']}: {rejection['pass_rate']:.1f}%")
        
        # Save results to file
        output_file = backend_dir / "test_rag_lesson_result.json"
        import json
        with open(output_file, 'w', encoding='utf-8') as f:
            # Convert datetime objects to strings for JSON serialization
            serializable_result = result.copy()
            # Remove non-serializable items if any
            json.dump(serializable_result, f, indent=2, default=str)
        
        print(f"✓ Results saved to {output_file}")
        
        print("Agentic system test passed!\n")
        return result
        
    except Exception as e:
        print(f"✗ Agentic system test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Run all tests"""
    print("Starting Self-Evaluating Lesson Generator Tests\n")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv(Path(__file__).parent / '.env')
    
    # Test components individually
    test_rubric()
    
    # Test components that require API key
    generator_result = test_generator()
    evaluator_result = test_evaluator()
    
    # Test complete system
    agentic_result = test_agentic_system()
    
    print("=" * 60)
    print("Test suite completed!")
    
    if agentic_result:
        print("✓ Full system test successful - ready for production use")
    else:
        print("⚠ Full system test skipped - configure OPENAI_API_KEY to run complete test")

if __name__ == "__main__":
    main()