"""
StudyMind Flask Application
Main application with API routes for the StudyMind platform
"""

import os
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.utils import secure_filename

from models import (
    db, init_db, User, Material, Task, StudySession,
    Notification, UserSettings, DailyProgress
)

# ==================== APP CONFIGURATION ====================

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'studymind-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///studymind.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'jpg', 'jpeg', 'png', 'heic'}

# Enable CORS for frontend
CORS(app, supports_credentials=True, origins=['*'])

# Initialize database
init_db(app)

# Create uploads folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# ==================== HELPERS ====================

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


def login_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """Get the currently logged-in user"""
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None


# ==================== AUTH ROUTES ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate required fields
    required = ['email', 'password', 'firstName', 'lastName']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Validate email format
    email = data['email'].strip().lower()
    if '@' not in email or '.' not in email:
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Check if email already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'error': 'Email already registered. Please login instead.'}), 400
    
    # Validate password strength
    if len(data['password']) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    try:
        # Create user
        user = User(
            email=email,
            password=data['password'],
            first_name=data['firstName'].strip(),
            last_name=data['lastName'].strip()
        )
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Create default settings
        settings = UserSettings(user_id=user.id)
        db.session.add(settings)
        
        # Create welcome notification
        notification = Notification(
            user_id=user.id,
            type='achievement',
            title='Welcome to StudyMind! 🎉',
            text='Your learning journey begins now. Upload your first material to get started.',
            icon='ri-trophy-line'
        )
        db.session.add(notification)
        
        db.session.commit()
        
        # Log user in
        session['user_id'] = user.id
        session.permanent = True
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password are required'}), 400
    
    # Find user by email
    user = User.query.filter_by(email=email).first()
    
    # Check if user exists
    if not user:
        return jsonify({'success': False, 'error': 'Account not found. Please register first.'}), 401
    
    # Check password
    if not user.check_password(password):
        return jsonify({'success': False, 'error': 'Invalid password. Please try again.'}), 401
    
    # Update last active
    user.last_active = datetime.utcnow()
    db.session.commit()
    
    # Set session
    session['user_id'] = user.id
    session.permanent = data.get('rememberMe', False)
    
    return jsonify({
        'success': True,
        'message': 'Login successful',
        'user': user.to_dict()
    })


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.pop('user_id', None)
    return jsonify({'success': True, 'message': 'Logged out successfully'})


@app.route('/api/auth/me', methods=['GET'])
@login_required
def get_me():
    """Get current user info"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'success': True, 'user': user.to_dict()})


@app.route('/api/auth/check', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({'authenticated': True, 'user': user.to_dict()})
    return jsonify({'authenticated': False})


# ==================== USER ROUTES ====================

@app.route('/api/user/stats', methods=['GET'])
@login_required
def get_user_stats():
    """Get user statistics for dashboard"""
    user = get_current_user()
    
    # Get this week's study time
    week_start = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
    week_sessions = StudySession.query.filter(
        StudySession.user_id == user.id,
        StudySession.start_time >= week_start
    ).all()
    week_study_time = sum(s.duration for s in week_sessions if s.duration)
    
    # Get last week's study time for comparison
    last_week_start = week_start - timedelta(days=7)
    last_week_sessions = StudySession.query.filter(
        StudySession.user_id == user.id,
        StudySession.start_time >= last_week_start,
        StudySession.start_time < week_start
    ).all()
    last_week_time = sum(s.duration for s in last_week_sessions if s.duration)
    
    # Calculate percentage change
    if last_week_time > 0:
        time_change = ((week_study_time - last_week_time) / last_week_time) * 100
    else:
        time_change = 100 if week_study_time > 0 else 0
    
    # Materials count
    total_materials = Material.query.filter_by(user_id=user.id).count()
    new_this_week = Material.query.filter(
        Material.user_id == user.id,
        Material.created_at >= week_start
    ).count()
    
    # Tasks stats
    total_tasks = Task.query.filter_by(user_id=user.id).count()
    completed_tasks = Task.query.filter_by(user_id=user.id, completed=True).count()
    
    return jsonify({
        'studyTime': {
            'value': round(week_study_time / 60, 1) if week_study_time else 0,
            'unit': 'h',
            'change': round(time_change),
            'label': 'Study Time This Week'
        },
        'materials': {
            'value': total_materials,
            'change': new_this_week,
            'label': 'Materials Processed'
        },
        'tasks': {
            'value': f"{completed_tasks}/{total_tasks}" if total_tasks > 0 else "0/0",
            'percentage': round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0),
            'label': 'Tasks Completed'
        },
        'streak': {
            'value': user.streak,
            'label': 'Day Streak'
        }
    })


@app.route('/api/user/settings', methods=['GET', 'PUT'])
@login_required
def user_settings():
    """Get or update user settings"""
    user = get_current_user()
    settings = UserSettings.query.filter_by(user_id=user.id).first()
    
    if request.method == 'GET':
        return jsonify(settings.to_dict() if settings else {})
    
    # PUT - Update settings
    data = request.get_json()
    
    if not settings:
        settings = UserSettings(user_id=user.id)
        db.session.add(settings)
    
    for key in ['theme', 'notifications_enabled', 'email_notifications', 
                'daily_goal', 'weekly_goal', 'reminder_time']:
        if key in data:
            setattr(settings, key, data[key])
    
    db.session.commit()
    return jsonify(settings.to_dict())


# ==================== MATERIALS ROUTES ====================

@app.route('/api/materials', methods=['GET', 'POST'])
@login_required
def materials():
    """List or create materials"""
    user = get_current_user()
    
    if request.method == 'GET':
        # Get query parameters
        status = request.args.get('status')
        file_type = request.args.get('type')
        limit = request.args.get('limit', 10, type=int)
        
        query = Material.query.filter_by(user_id=user.id)
        
        if status:
            query = query.filter_by(status=status)
        if file_type:
            query = query.filter_by(file_type=file_type)
        
        materials = query.order_by(Material.created_at.desc()).limit(limit).all()
        return jsonify([m.to_dict() for m in materials])
    
    # POST - Upload new material
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    try:
        filename = secure_filename(file.filename)
        unique_filename = f"{user.id}_{datetime.utcnow().timestamp()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        material = Material(
            user_id=user.id,
            name=request.form.get('name', filename),
            original_filename=filename,
            file_path=file_path,
            file_type=get_file_type(filename),
            file_size=file_size,
            status='new',
            subject=request.form.get('subject'),
            tags=request.form.get('tags')
        )
        db.session.add(material)
        db.session.commit()
        
        # Create notification
        notification = Notification(
            user_id=user.id,
            type='success',
            title='Material Uploaded',
            text=f'{material.name} has been uploaded and is ready for processing.',
            icon='ri-check-line'
        )
        db.session.add(notification)
        db.session.commit()
        
        return jsonify(material.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/materials/<int:material_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def material_detail(material_id):
    """Get, update, or delete a specific material"""
    user = get_current_user()
    material = Material.query.filter_by(id=material_id, user_id=user.id).first()
    
    if not material:
        return jsonify({'error': 'Material not found'}), 404
    
    if request.method == 'GET':
        return jsonify(material.to_dict())
    
    if request.method == 'PUT':
        data = request.get_json()
        for key in ['name', 'subject', 'tags', 'status']:
            if key in data:
                setattr(material, key, data[key])
        db.session.commit()
        return jsonify(material.to_dict())
    
    if request.method == 'DELETE':
        # Delete file from disk
        if material.file_path and os.path.exists(material.file_path):
            os.remove(material.file_path)
        
        db.session.delete(material)
        db.session.commit()
        return jsonify({'message': 'Material deleted'})


# ==================== TASKS ROUTES ====================

@app.route('/api/tasks', methods=['GET', 'POST'])
@login_required
def tasks():
    """List or create tasks"""
    user = get_current_user()
    
    if request.method == 'GET':
        completed = request.args.get('completed')
        limit = request.args.get('limit', 20, type=int)
        
        query = Task.query.filter_by(user_id=user.id)
        
        if completed is not None:
            query = query.filter_by(completed=completed.lower() == 'true')
        
        tasks = query.order_by(Task.due_date.asc()).limit(limit).all()
        return jsonify([t.to_dict() for t in tasks])
    
    # POST - Create new task
    data = request.get_json()
    
    if not data.get('title'):
        return jsonify({'error': 'Title is required'}), 400
    
    task = Task(
        user_id=user.id,
        material_id=data.get('materialId'),
        title=data['title'],
        description=data.get('description'),
        task_type=data.get('taskType'),
        due_date=datetime.fromisoformat(data['dueDate']) if data.get('dueDate') else None,
        estimated_time=data.get('estimatedTime'),
        priority=data.get('priority', 'medium')
    )
    db.session.add(task)
    db.session.commit()
    
    return jsonify(task.to_dict()), 201


@app.route('/api/tasks/<int:task_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def task_detail(task_id):
    """Get, update, or delete a specific task"""
    user = get_current_user()
    task = Task.query.filter_by(id=task_id, user_id=user.id).first()
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    if request.method == 'GET':
        return jsonify(task.to_dict())
    
    if request.method == 'PUT':
        data = request.get_json()
        
        for key in ['title', 'description', 'task_type', 'priority', 'estimated_time']:
            if key in data:
                setattr(task, key, data[key])
        
        if 'dueDate' in data:
            task.due_date = datetime.fromisoformat(data['dueDate']) if data['dueDate'] else None
        
        if 'completed' in data:
            task.completed = data['completed']
            task.completed_at = datetime.utcnow() if data['completed'] else None
            
            # Update daily progress
            if data['completed']:
                update_daily_progress(user.id, tasks_completed=1)
        
        db.session.commit()
        return jsonify(task.to_dict())
    
    if request.method == 'DELETE':
        db.session.delete(task)
        db.session.commit()
        return jsonify({'message': 'Task deleted'})


@app.route('/api/tasks/<int:task_id>/toggle', methods=['POST'])
@login_required
def toggle_task(task_id):
    """Toggle task completion status"""
    user = get_current_user()
    task = Task.query.filter_by(id=task_id, user_id=user.id).first()
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    task.completed = not task.completed
    task.completed_at = datetime.utcnow() if task.completed else None
    
    # Update progress if completed
    if task.completed:
        update_daily_progress(user.id, tasks_completed=1)
    
    db.session.commit()
    return jsonify(task.to_dict())


# ==================== STUDY SESSIONS ROUTES ====================

@app.route('/api/sessions', methods=['GET', 'POST'])
@login_required
def sessions():
    """List or create study sessions"""
    user = get_current_user()
    
    if request.method == 'GET':
        days = request.args.get('days', 7, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        sessions = StudySession.query.filter(
            StudySession.user_id == user.id,
            StudySession.start_time >= start_date
        ).order_by(StudySession.start_time.desc()).all()
        
        return jsonify([s.to_dict() for s in sessions])
    
    # POST - Start new session
    data = request.get_json()
    
    session_obj = StudySession(
        user_id=user.id,
        material_id=data.get('materialId') if data else None,
        activity_type=data.get('activityType', 'reading') if data else 'reading',
        date=datetime.utcnow().date()
    )
    db.session.add(session_obj)
    db.session.commit()
    
    return jsonify(session_obj.to_dict()), 201


@app.route('/api/sessions/<int:session_id>/end', methods=['POST'])
@login_required
def end_session(session_id):
    """End a study session"""
    user = get_current_user()
    session_obj = StudySession.query.filter_by(id=session_id, user_id=user.id).first()
    
    if not session_obj:
        return jsonify({'error': 'Session not found'}), 404
    
    data = request.get_json()
    
    session_obj.end_time = datetime.utcnow()
    session_obj.duration = data.get('duration', 0) if data else 0
    session_obj.pages_covered = data.get('pagesCovered', 0) if data else 0
    
    # Update user total study time
    user.total_study_time += session_obj.duration
    
    # Update daily progress
    update_daily_progress(
        user.id,
        study_time=session_obj.duration,
        pages_read=session_obj.pages_covered
    )
    
    # Update streak
    update_streak(user)
    
    db.session.commit()
    
    return jsonify(session_obj.to_dict())


# ==================== NOTIFICATIONS ROUTES ====================

@app.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    """Get user notifications"""
    user = get_current_user()
    limit = request.args.get('limit', 20, type=int)
    unread_only = request.args.get('unread', 'false').lower() == 'true'
    
    query = Notification.query.filter_by(user_id=user.id)
    
    if unread_only:
        query = query.filter_by(read=False)
    
    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
    unread_count = Notification.query.filter_by(user_id=user.id, read=False).count()
    
    return jsonify({
        'notifications': [n.to_dict() for n in notifications],
        'unread_count': unread_count
    })


@app.route('/api/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    """Mark a notification as read"""
    user = get_current_user()
    notification = Notification.query.filter_by(id=notif_id, user_id=user.id).first()
    
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    
    notification.read = True
    db.session.commit()
    
    return jsonify(notification.to_dict())


@app.route('/api/notifications/read-all', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications as read"""
    user = get_current_user()
    
    Notification.query.filter_by(user_id=user.id, read=False).update({'read': True})
    db.session.commit()
    
    return jsonify({'message': 'All notifications marked as read'})


# ==================== PROGRESS ROUTES ====================

@app.route('/api/progress/daily', methods=['GET'])
@login_required
def get_daily_progress():
    """Get daily progress for a date range"""
    user = get_current_user()
    days = request.args.get('days', 7, type=int)
    
    start_date = datetime.utcnow().date() - timedelta(days=days-1)
    
    progress = DailyProgress.query.filter(
        DailyProgress.user_id == user.id,
        DailyProgress.date >= start_date
    ).order_by(DailyProgress.date.asc()).all()
    
    return jsonify([p.to_dict() for p in progress])


@app.route('/api/progress/weekly', methods=['GET'])
@login_required
def get_weekly_progress():
    """Get weekly summary"""
    user = get_current_user()
    
    week_start = datetime.utcnow().date() - timedelta(days=datetime.utcnow().weekday())
    
    progress = DailyProgress.query.filter(
        DailyProgress.user_id == user.id,
        DailyProgress.date >= week_start
    ).all()
    
    total_time = sum(p.study_time for p in progress)
    total_tasks = sum(p.tasks_completed for p in progress)
    total_materials = sum(p.materials_processed for p in progress)
    total_pages = sum(p.pages_read for p in progress)
    days_goal_met = sum(1 for p in progress if p.goal_met)
    
    return jsonify({
        'total_study_time': total_time,
        'total_tasks_completed': total_tasks,
        'total_materials_processed': total_materials,
        'total_pages_read': total_pages,
        'days_goal_met': days_goal_met,
        'daily_breakdown': [p.to_dict() for p in progress]
    })


# ==================== HELPER FUNCTIONS ====================

def update_daily_progress(user_id, study_time=0, materials_processed=0, 
                          tasks_completed=0, pages_read=0):
    """Update or create daily progress record"""
    today = datetime.utcnow().date()
    
    progress = DailyProgress.query.filter_by(
        user_id=user_id,
        date=today
    ).first()
    
    if not progress:
        progress = DailyProgress(user_id=user_id, date=today)
        db.session.add(progress)
    
    progress.study_time += study_time
    progress.materials_processed += materials_processed
    progress.tasks_completed += tasks_completed
    progress.pages_read += pages_read
    
    # Check if daily goal met
    settings = UserSettings.query.filter_by(user_id=user_id).first()
    if settings and progress.study_time >= settings.daily_goal:
        progress.goal_met = True
    
    db.session.commit()


def update_streak(user):
    """Update user's study streak"""
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    
    # Check if studied yesterday
    yesterday_progress = DailyProgress.query.filter_by(
        user_id=user.id,
        date=yesterday,
        goal_met=True
    ).first()
    
    today_progress = DailyProgress.query.filter_by(
        user_id=user.id,
        date=today
    ).first()
    
    if today_progress and today_progress.goal_met:
        if yesterday_progress:
            user.streak += 1
        else:
            user.streak = 1
        
        # Create achievement notification for milestone streaks
        if user.streak in [7, 14, 30, 60, 100]:
            notification = Notification(
                user_id=user.id,
                type='achievement',
                title=f'🔥 {user.streak}-Day Streak!',
                text=f'Amazing! You\'ve studied for {user.streak} days in a row!',
                icon='ri-fire-line'
            )
            db.session.add(notification)


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500


# ==================== RUN APP ====================

from ai_routes import register_ai_routes
register_ai_routes(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)