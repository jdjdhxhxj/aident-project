"""
StudyMind Database Models
SQLAlchemy ORM models for the StudyMind application
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """User account model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    avatar_initials = db.Column(db.String(2))
    
    # Stats
    streak = db.Column(db.Integer, default=0)
    total_study_time = db.Column(db.Integer, default=0)  # in minutes
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    materials = db.relationship('Material', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    sessions = db.relationship('StudySession', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    settings = db.relationship('UserSettings', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def __init__(self, email, password, first_name, last_name):
        self.email = email
        self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
        self.avatar_initials = f"{first_name[0]}{last_name[0]}".upper()
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': f"{self.first_name} {self.last_name}",
            'avatar_initials': self.avatar_initials,
            'streak': self.streak,
            'total_study_time': self.total_study_time,
            'last_active': self.last_active.isoformat() if self.last_active else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<User {self.email}>'


class Material(db.Model):
    """Uploaded study materials (PDFs, docs, images, etc.)"""
    __tablename__ = 'materials'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # File info
    name = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    file_type = db.Column(db.String(20))  # pdf, doc, ppt, img
    file_size = db.Column(db.Integer)  # in bytes
    page_count = db.Column(db.Integer, default=0)
    
    # Processing status
    status = db.Column(db.String(20), default='new')  # new, processing, completed, error
    processed_content = db.Column(db.Text)  # Extracted/processed text
    
    # Metadata
    subject = db.Column(db.String(100))
    tags = db.Column(db.String(500))  # Comma-separated tags
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tasks = db.relationship('Task', backref='material', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'page_count': self.page_count,
            'status': self.status,
            'subject': self.subject,
            'tags': self.tags.split(',') if self.tags else [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Material {self.name}>'


class Task(db.Model):
    """Study tasks and assignments"""
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=True)
    
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    task_type = db.Column(db.String(50))  # review, quiz, summary, exam_prep
    
    # Status
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    
    # Scheduling
    due_date = db.Column(db.DateTime)
    estimated_time = db.Column(db.Integer)  # in minutes
    priority = db.Column(db.String(10), default='medium')  # low, medium, high
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'material_id': self.material_id,
            'title': self.title,
            'description': self.description,
            'task_type': self.task_type,
            'completed': self.completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'estimated_time': self.estimated_time,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Task {self.title}>'


class StudySession(db.Model):
    """Track study sessions for progress analytics"""
    __tablename__ = 'study_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=True)
    
    # Session data
    duration = db.Column(db.Integer, default=0)  # in minutes
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    
    # Activity tracking
    activity_type = db.Column(db.String(50))  # reading, quiz, flashcards, notes
    pages_covered = db.Column(db.Integer, default=0)
    
    # Date for easy querying
    date = db.Column(db.Date, default=datetime.utcnow().date)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'material_id': self.material_id,
            'duration': self.duration,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'activity_type': self.activity_type,
            'pages_covered': self.pages_covered,
            'date': self.date.isoformat() if self.date else None
        }
    
    def __repr__(self):
        return f'<StudySession {self.id} - {self.duration}min>'


class Notification(db.Model):
    """User notifications"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Notification content
    type = db.Column(db.String(30))  # update, success, warning, achievement, reminder, error
    title = db.Column(db.String(255), nullable=False)
    text = db.Column(db.Text)
    icon = db.Column(db.String(50))
    
    # Status
    read = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'title': self.title,
            'text': self.text,
            'icon': self.icon,
            'read': self.read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Notification {self.title}>'


class UserSettings(db.Model):
    """User preferences and settings"""
    __tablename__ = 'user_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    
    # Preferences
    theme = db.Column(db.String(20), default='dark')
    notifications_enabled = db.Column(db.Boolean, default=True)
    email_notifications = db.Column(db.Boolean, default=True)
    
    # Study goals
    daily_goal = db.Column(db.Integer, default=60)  # minutes
    weekly_goal = db.Column(db.Integer, default=300)  # minutes
    reminder_time = db.Column(db.String(5), default='09:00')
    
    # Timestamps
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'theme': self.theme,
            'notifications_enabled': self.notifications_enabled,
            'email_notifications': self.email_notifications,
            'daily_goal': self.daily_goal,
            'weekly_goal': self.weekly_goal,
            'reminder_time': self.reminder_time
        }
    
    def __repr__(self):
        return f'<UserSettings for user {self.user_id}>'


class DailyProgress(db.Model):
    """Daily progress tracking for statistics"""
    __tablename__ = 'daily_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    
    # Daily stats
    study_time = db.Column(db.Integer, default=0)  # minutes
    materials_processed = db.Column(db.Integer, default=0)
    tasks_completed = db.Column(db.Integer, default=0)
    pages_read = db.Column(db.Integer, default=0)
    
    # Streak tracking
    goal_met = db.Column(db.Boolean, default=False)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'date', name='unique_user_date'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.isoformat() if self.date else None,
            'study_time': self.study_time,
            'materials_processed': self.materials_processed,
            'tasks_completed': self.tasks_completed,
            'pages_read': self.pages_read,
            'goal_met': self.goal_met
        }
    
    def __repr__(self):
        return f'<DailyProgress {self.date} - {self.study_time}min>'


def init_db(app):
    """Initialize the database with the Flask app"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")