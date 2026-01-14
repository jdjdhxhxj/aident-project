"""
AI Routes for StudyMind
Add these routes to your app.py
"""

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os

# Import AI service
from ai_service import (
    process_material, 
    create_compendium,
    generate_flashcards,
    get_file_content
)

ai_bp = Blueprint('ai', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'jpg', 'jpeg', 'png', 'heic'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_type(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    type_map = {
        'pdf': 'pdf',
        'doc': 'doc', 'docx': 'doc',
        'ppt': 'ppt', 'pptx': 'ppt',
        'jpg': 'img', 'jpeg': 'img', 'png': 'img', 'heic': 'img'
    }
    return type_map.get(ext, 'other')


# ==================== AI ENDPOINTS ====================

@ai_bp.route('/api/ai/process', methods=['POST'])
def process_file():
    """
    Process uploaded file with AI and create compendium
    
    Form data:
    - file: The file to process
    - goal: understand|summary|exam|questions|plan|review
    """
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    goal = request.form.get('goal', 'understand')
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'File type not allowed'}), 400
    
    try:
        # Save file temporarily
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file.save(file_path)
        
        # Get file type
        file_type = get_file_type(filename)
        
        # Process with AI
        result = process_material(file_path, file_type, goal)
        
        # Clean up temp file (optional - you might want to keep it)
        # os.remove(file_path)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/api/ai/compendium', methods=['POST'])
def create_compendium_endpoint():
    """
    Create compendium from text content
    
    JSON body:
    - content: Text content to process
    - goal: understand|summary|exam|questions|plan|review
    """
    data = request.get_json()
    
    if not data or not data.get('content'):
        return jsonify({'success': False, 'error': 'No content provided'}), 400
    
    content = data['content']
    goal = data.get('goal', 'understand')
    
    result = create_compendium(content, goal)
    return jsonify(result)


@ai_bp.route('/api/ai/ask', methods=['POST'])
def ask_question_endpoint():
    """
    Ask a question about material
    
    JSON body:
    - content: The study material
    - question: The question to ask
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    content = data.get('content', '')
    question = data.get('question', '')
    
    if not question:
        return jsonify({'success': False, 'error': 'No question provided'}), 400
    
    result = ask_question(content, question)
    return jsonify(result)


@ai_bp.route('/api/ai/explain', methods=['POST'])
def explain_concept_endpoint():
    """
    Explain a concept
    
    JSON body:
    - concept: The concept to explain
    - context: Optional context from study material
    """
    data = request.get_json()
    
    if not data or not data.get('concept'):
        return jsonify({'success': False, 'error': 'No concept provided'}), 400
    
    concept = data['concept']
    context = data.get('context', '')
    
    result = explain_concept(concept, context)
    return jsonify(result)


@ai_bp.route('/api/ai/flashcards', methods=['POST'])
def generate_flashcards_endpoint():
    """
    Generate flashcards from content
    
    JSON body:
    - content: The study material
    - count: Number of flashcards (default 10)
    """
    data = request.get_json()
    
    if not data or not data.get('content'):
        return jsonify({'success': False, 'error': 'No content provided'}), 400
    
    content = data['content']
    count = data.get('count', 10)
    
    result = generate_flashcards(content, count)
    return jsonify(result)


@ai_bp.route('/api/ai/quiz', methods=['POST'])
def generate_quiz_endpoint():
    """
    Generate quiz from content
    
    JSON body:
    - content: The study material
    - count: Number of questions (default 5)
    """
    data = request.get_json()
    
    if not data or not data.get('content'):
        return jsonify({'success': False, 'error': 'No content provided'}), 400
    
    content = data['content']
    count = data.get('count', 5)
    
    result = generate_quiz(content, count)
    return jsonify(result)


# ==================== REGISTRATION ====================

def register_ai_routes(app):
    """Register AI routes with the Flask app"""
    app.register_blueprint(ai_bp)
    print("✅ AI routes registered")


# ==================== USAGE IN app.py ====================
"""
To use these routes, add to your app.py:

from ai_routes import register_ai_routes

# After creating Flask app
app = Flask(__name__)
...
register_ai_routes(app)
"""
