"""
StudyMind AI Service
Uses Google Gemini AI (free) to process files and create study materials
"""

import os
import base64
import json
import re
from datetime import datetime
import google.generativeai as genai
from PIL import Image
import PyPDF2
from docx import Document
import io

# ==================== CONFIGURATION ====================

# Get API key from environment variable
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not set!")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Models - Updated to latest Gemini models (2024/2025)
TEXT_MODEL = genai.GenerativeModel('gemini-1.5-flash')
VISION_MODEL = genai.GenerativeModel('gemini-1.5-flash')


# ==================== TEXT EXTRACTION ====================

def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error extracting PDF: {e}")
    return text.strip()


def extract_text_from_docx(file_path):
    """Extract text from Word document"""
    text = ""
    try:
        doc = Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"Error extracting DOCX: {e}")
    return text.strip()


def extract_text_from_image(file_path):
    """Extract text from image using Gemini Vision"""
    try:
        image = Image.open(file_path)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        response = VISION_MODEL.generate_content([
            "Extract all text from this image. If it's handwritten notes, transcribe them accurately. "
            "Preserve the structure and formatting as much as possible.",
            image
        ])
        
        return response.text
    except Exception as e:
        print(f"Error extracting text from image: {e}")
        return ""


def get_file_content(file_path, file_type):
    """Get content from file based on type"""
    if file_type == 'pdf':
        return extract_text_from_pdf(file_path)
    elif file_type in ['doc', 'docx']:
        return extract_text_from_docx(file_path)
    elif file_type in ['img', 'image', 'jpg', 'jpeg', 'png', 'heic']:
        return extract_text_from_image(file_path)
    else:
        # Try to read as plain text
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return ""


# ==================== AI COMPENDIUM GENERATION ====================

def create_compendium(content, goal="understand"):
    """
    Create a study compendium from content using AI
    """
    
    prompts = {
        "understand": """
            Analyze this study material and create a comprehensive explanation:
            
            1. **Main Concepts** - List and explain the key concepts
            2. **Detailed Explanation** - Break down complex topics into simple terms
            3. **Examples** - Provide practical examples for each concept
            4. **Connections** - Show how concepts relate to each other
            5. **Common Misconceptions** - Address potential confusion points
            
            Make it easy to understand for a student.
        """,
        
        "summary": """
            Create a concise summary of this material:
            
            1. **Overview** - 2-3 sentence overview
            2. **Key Points** - Bullet list of main points (max 10)
            3. **Important Terms** - Define key vocabulary
            4. **Quick Facts** - Essential facts to remember
            5. **Conclusion** - Main takeaway
            
            Keep it brief but comprehensive.
        """,
        
        "exam": """
            Create exam preparation materials:
            
            1. **Topics to Master** - List all topics that might be tested
            2. **Key Definitions** - Important terms and definitions
            3. **Formulas/Rules** - Any formulas or rules to memorize
            4. **Potential Exam Questions** - 10 likely exam questions with answers
            5. **Study Priority** - Rank topics by importance (High/Medium/Low)
            6. **Common Mistakes** - What to avoid in exam
            
            Focus on what's most likely to be tested.
        """,
        
        "questions": """
            Generate practice questions based on this material:
            
            1. **Multiple Choice Questions** (5 questions with 4 options each, mark correct answer)
            2. **True/False Questions** (5 questions with explanations)
            3. **Short Answer Questions** (5 questions with model answers)
            4. **Essay Questions** (2 questions with key points to cover)
            5. **Application Questions** (3 real-world scenario questions)
            
            Include answers for all questions.
        """,
        
        "plan": """
            Create a study plan based on this material:
            
            1. **Learning Objectives** - What student should master
            2. **Topic Breakdown** - Divide into study sessions
            3. **Time Estimates** - How long each topic needs
            4. **Suggested Order** - Best sequence to learn
            5. **Checkpoints** - Self-test points
            6. **Resources Needed** - Additional materials helpful
            7. **Weekly Schedule** - Sample 1-week study plan
            
            Make it practical and achievable.
        """,
        
        "review": """
            Create quick review flashcards and notes:
            
            1. **Flashcards** - 15 question/answer pairs for key concepts
            2. **One-Page Summary** - Everything on one page
            3. **Mnemonics** - Memory tricks for hard concepts
            4. **Quick Quiz** - 5 rapid-fire questions
            5. **Last-Minute Tips** - What to review right before exam
            
            Optimize for fast review.
        """
    }
    
    prompt = prompts.get(goal, prompts["understand"])
    
    full_prompt = f"""
    You are StudyMind AI, an expert educational assistant.
    
    {prompt}
    
    MATERIAL TO ANALYZE:
    ---
    {content[:15000]}
    ---
    
    Format your response with clear headers, bullet points, and organized sections.
    Use markdown formatting.
    """
    
    try:
        response = TEXT_MODEL.generate_content(full_prompt)
        return {
            "success": True,
            "compendium": response.text,
            "goal": goal,
            "created_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"Error creating compendium: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def create_compendium_from_image(image_path, goal="understand"):
    """Create compendium directly from image (handwritten notes, diagrams, etc.)"""
    
    prompts = {
        "understand": "Analyze this study material image and create a comprehensive explanation with main concepts, examples, and connections.",
        "summary": "Create a concise summary of the content shown in this image with key points and important terms.",
        "exam": "Create exam preparation materials based on what's shown in this image, including potential questions and study priorities.",
        "questions": "Generate practice questions based on the content in this image. Include multiple choice, true/false, and short answer questions with answers.",
        "plan": "Create a study plan based on the material shown in this image.",
        "review": "Create quick review flashcards and notes based on this image."
    }
    
    try:
        image = Image.open(image_path)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        prompt = f"""
        You are StudyMind AI, an expert educational assistant.
        
        Analyze this study material (could be handwritten notes, textbook page, diagram, etc.)
        and {prompts.get(goal, prompts["understand"])}
        
        Format your response with clear headers, bullet points, and organized sections.
        Use markdown formatting.
        """
        
        response = VISION_MODEL.generate_content([prompt, image])
        
        return {
            "success": True,
            "compendium": response.text,
            "goal": goal,
            "created_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"Error creating compendium from image: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# ==================== ADDITIONAL AI FEATURES ====================

def ask_question(content, question):
    """Ask a question about the material"""
    prompt = f"""
    Based on this study material:
    ---
    {content[:10000]}
    ---
    
    Answer this question: {question}
    
    Provide a clear, educational answer. If the answer isn't in the material, 
    say so but try to help based on general knowledge.
    """
    
    try:
        response = TEXT_MODEL.generate_content(prompt)
        return {"success": True, "answer": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}


def explain_concept(concept, context=""):
    """Explain a specific concept"""
    prompt = f"""
    Explain the concept of "{concept}" in a clear, educational way.
    
    {"Context from study material: " + context[:5000] if context else ""}
    
    Include:
    1. Simple definition
    2. Detailed explanation
    3. Real-world examples
    4. Common uses/applications
    5. Related concepts
    
    Make it easy to understand for a student.
    """
    
    try:
        response = TEXT_MODEL.generate_content(prompt)
        return {"success": True, "explanation": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_flashcards(content, count=10):
    """Generate flashcards from content"""
    prompt = f"""
    Create {count} flashcards from this study material:
    ---
    {content[:10000]}
    ---
    
    Format as JSON array:
    [
        {{"front": "Question", "back": "Answer"}},
        ...
    ]
    
    Focus on the most important concepts.
    Return ONLY the JSON array, no other text.
    """
    
    try:
        response = TEXT_MODEL.generate_content(prompt)
        text = response.text
        # Find JSON array in response
        match = re.search(r'\[[\s\S]*\]', text)
        if match:
            flashcards = json.loads(match.group())
            return {"success": True, "flashcards": flashcards}
        return {"success": False, "error": "Could not parse flashcards"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_quiz(content, question_count=5):
    """Generate a quiz from content"""
    prompt = f"""
    Create a quiz with {question_count} multiple choice questions from this material:
    ---
    {content[:10000]}
    ---
    
    Format as JSON:
    {{
        "questions": [
            {{
                "question": "Question text",
                "options": ["A", "B", "C", "D"],
                "correct": 0,
                "explanation": "Why this is correct"
            }}
        ]
    }}
    
    Return ONLY the JSON, no other text.
    """
    
    try:
        response = TEXT_MODEL.generate_content(prompt)
        text = response.text
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            quiz = json.loads(match.group())
            return {"success": True, "quiz": quiz}
        return {"success": False, "error": "Could not parse quiz"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== MAIN PROCESSING FUNCTION ====================

def process_material(file_path, file_type, goal="understand"):
    """
    Main function to process uploaded material
    """
    result = {
        "success": False,
        "file_path": file_path,
        "file_type": file_type,
        "goal": goal,
        "content_preview": "",
        "compendium": None,
        "flashcards": None,
        "error": None
    }
    
    try:
        # For images, use vision model directly
        if file_type in ['img', 'image', 'jpg', 'jpeg', 'png', 'heic']:
            compendium_result = create_compendium_from_image(file_path, goal)
            content = ""  # No text content for images
        else:
            # Extract text from document
            content = get_file_content(file_path, file_type)
            
            if not content:
                result["error"] = "Could not extract content from file"
                return result
            
            result["content_preview"] = content[:500] + "..." if len(content) > 500 else content
            
            # Generate compendium
            compendium_result = create_compendium(content, goal)
        
        if compendium_result.get("success"):
            result["success"] = True
            result["compendium"] = compendium_result["compendium"]
            
            # Generate flashcards for certain goals (only if we have text content)
            if goal in ["understand", "exam", "review"] and content:
                flashcards_result = generate_flashcards(content, count=10)
                if flashcards_result.get("success"):
                    result["flashcards"] = flashcards_result["flashcards"]
        else:
            result["error"] = compendium_result.get("error", "Unknown error")
        
        return result
        
    except Exception as e:
        print(f"Error processing material: {e}")
        result["error"] = str(e)
        return result


# ==================== TESTING ====================

if __name__ == "__main__":
    print("Testing AI Service...")
    print(f"API Key set: {'Yes' if GEMINI_API_KEY else 'No'}")
    
    if GEMINI_API_KEY:
        # Test with sample text
        sample_text = """
        Machine Learning is a subset of artificial intelligence that enables systems to learn 
        and improve from experience without being explicitly programmed.
        """
        
        result = create_compendium(sample_text, "summary")
        
        if result["success"]:
            print("✅ AI Service working!")
            print(result["compendium"][:200] + "...")
        else:
            print("❌ Error:", result["error"])
    else:
        print("❌ GEMINI_API_KEY not set")