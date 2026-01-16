"""
AI Routes for StudyMind
"""

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os

# Import AI service functions
from ai_service import (
    process_material, 
    create_compendium,
    generate_flashcards,
    generate_quiz,
    get_file_content,
    ask_question,
    explain_concept
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

@ai_bp.route('/api/ai/process', methods=['POST', 'OPTIONS'])
def process_file():
    """
    Process uploaded file with AI and create compendium
    """
    # Handle preflight request
    if request.method == 'OPTIONS':
        return '', 200
    
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
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in process_file: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/api/ai/compendium', methods=['POST', 'OPTIONS'])
def create_compendium_endpoint():
    """
    Create compendium from text content
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    
    if not data or not data.get('content'):
        return jsonify({'success': False, 'error': 'No content provided'}), 400
    
    content = data['content']
    goal = data.get('goal', 'understand')
    
    result = create_compendium(content, goal)
    return jsonify(result)


@ai_bp.route('/api/ai/ask', methods=['POST', 'OPTIONS'])
def ask_question_endpoint():
    """
    Ask a question about material
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    content = data.get('content', '')
    question = data.get('question', '')
    
    if not question:
        return jsonify({'success': False, 'error': 'No question provided'}), 400
    
    result = ask_question(content, question)
    return jsonify(result)


@ai_bp.route('/api/ai/explain', methods=['POST', 'OPTIONS'])
def explain_concept_endpoint():
    """
    Explain a concept
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    
    if not data or not data.get('concept'):
        return jsonify({'success': False, 'error': 'No concept provided'}), 400
    
    concept = data['concept']
    context = data.get('context', '')
    
    result = explain_concept(concept, context)
    return jsonify(result)


@ai_bp.route('/api/ai/flashcards', methods=['POST', 'OPTIONS'])
def generate_flashcards_endpoint():
    """
    Generate flashcards from content
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    
    if not data or not data.get('content'):
        return jsonify({'success': False, 'error': 'No content provided'}), 400
    
    content = data['content']
    count = data.get('count', 10)
    
    result = generate_flashcards(content, count)
    return jsonify(result)


@ai_bp.route('/api/ai/quiz', methods=['POST', 'OPTIONS'])
def generate_quiz_endpoint():
    """
    Generate quiz from content
    """
    if request.method == 'OPTIONS':
        return '', 200
    
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