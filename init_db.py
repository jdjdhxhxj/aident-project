"""
StudyMind Database Initialization and Seed Data
Run this script to set up the database with sample data
"""

from datetime import datetime, timedelta
import random

from app import app
from models import (
    db, User, Material, Task, StudySession,
    Notification, UserSettings, DailyProgress
)


def create_tables():
    """Create all database tables"""
    with app.app_context():
        db.create_all()
        print("✓ Database tables created successfully!")


def seed_demo_user():
    """Create a demo user with sample data"""
    with app.app_context():
        # Check if demo user exists
        existing = User.query.filter_by(email='demo@studymind.com').first()
        if existing:
            print("⚠ Demo user already exists, skipping...")
            return existing
        
        # Create demo user
        user = User(
            email='demo@studymind.com',
            password='demo123',
            first_name='Alex',
            last_name='Kowalski'
        )
        user.streak = 7
        user.total_study_time = 750  # 12.5 hours in minutes
        db.session.add(user)
        db.session.flush()
        
        # Create settings
        settings = UserSettings(
            user_id=user.id,
            theme='dark',
            notifications_enabled=True,
            daily_goal=60,
            weekly_goal=300
        )
        db.session.add(settings)
        
        print(f"✓ Demo user created: {user.email}")
        return user


def seed_materials(user):
    """Create sample materials"""
    with app.app_context():
        materials_data = [
            {
                'name': 'Chapter 5 - Machine Learning Fundamentals.pdf',
                'file_type': 'pdf',
                'page_count': 24,
                'status': 'completed',
                'subject': 'Computer Science',
                'created_at': datetime.utcnow() - timedelta(hours=2)
            },
            {
                'name': 'Lecture Notes - Data Structures.docx',
                'file_type': 'doc',
                'page_count': 18,
                'status': 'completed',
                'subject': 'Computer Science',
                'created_at': datetime.utcnow() - timedelta(days=1)
            },
            {
                'name': 'Statistics Week 8 - Regression Analysis.pptx',
                'file_type': 'ppt',
                'page_count': 42,
                'status': 'processing',
                'subject': 'Statistics',
                'created_at': datetime.utcnow() - timedelta(days=3)
            },
            {
                'name': 'Handwritten Notes - Calculus.jpg',
                'file_type': 'img',
                'page_count': 3,
                'status': 'new',
                'subject': 'Mathematics',
                'created_at': datetime.utcnow() - timedelta(days=7)
            },
            {
                'name': 'Physics Lab Report Template.docx',
                'file_type': 'doc',
                'page_count': 8,
                'status': 'completed',
                'subject': 'Physics',
                'created_at': datetime.utcnow() - timedelta(days=5)
            },
            {
                'name': 'Organic Chemistry - Chapter 12.pdf',
                'file_type': 'pdf',
                'page_count': 36,
                'status': 'completed',
                'subject': 'Chemistry',
                'created_at': datetime.utcnow() - timedelta(days=10)
            }
        ]
        
        for data in materials_data:
            material = Material(
                user_id=user.id,
                name=data['name'],
                original_filename=data['name'],
                file_type=data['file_type'],
                page_count=data['page_count'],
                status=data['status'],
                subject=data['subject'],
                file_size=random.randint(100000, 5000000)
            )
            material.created_at = data['created_at']
            db.session.add(material)
        
        db.session.commit()
        print(f"✓ Created {len(materials_data)} sample materials")


def seed_tasks(user):
    """Create sample tasks"""
    with app.app_context():
        tasks_data = [
            {
                'title': 'Review Machine Learning notes',
                'task_type': 'review',
                'completed': True,
                'due_date': datetime.utcnow() - timedelta(days=1),
                'estimated_time': 30,
                'priority': 'high'
            },
            {
                'title': 'Complete Data Structures quiz',
                'task_type': 'quiz',
                'completed': True,
                'due_date': datetime.utcnow() - timedelta(hours=12),
                'estimated_time': 45,
                'priority': 'high'
            },
            {
                'title': 'Create flashcards for Statistics',
                'task_type': 'flashcards',
                'completed': False,
                'due_date': datetime.utcnow() + timedelta(days=1),
                'estimated_time': 20,
                'priority': 'medium'
            },
            {
                'title': 'Summarize Calculus chapter',
                'task_type': 'summary',
                'completed': False,
                'due_date': datetime.utcnow() + timedelta(days=2),
                'estimated_time': 25,
                'priority': 'medium'
            },
            {
                'title': 'Practice regression problems',
                'task_type': 'practice',
                'completed': False,
                'due_date': datetime.utcnow() + timedelta(days=3),
                'estimated_time': 40,
                'priority': 'high'
            },
            {
                'title': 'Review Physics lab procedures',
                'task_type': 'review',
                'completed': False,
                'due_date': datetime.utcnow() + timedelta(days=5),
                'estimated_time': 15,
                'priority': 'low'
            },
            {
                'title': 'Prepare for Chemistry midterm',
                'task_type': 'exam_prep',
                'completed': False,
                'due_date': datetime.utcnow() + timedelta(days=7),
                'estimated_time': 120,
                'priority': 'high'
            }
        ]
        
        for data in tasks_data:
            task = Task(
                user_id=user.id,
                title=data['title'],
                task_type=data['task_type'],
                completed=data['completed'],
                due_date=data['due_date'],
                estimated_time=data['estimated_time'],
                priority=data['priority']
            )
            if data['completed']:
                task.completed_at = data['due_date']
            db.session.add(task)
        
        db.session.commit()
        print(f"✓ Created {len(tasks_data)} sample tasks")


def seed_study_sessions(user):
    """Create sample study sessions"""
    with app.app_context():
        # Create sessions for the past 7 days
        for days_ago in range(7):
            date = datetime.utcnow() - timedelta(days=days_ago)
            
            # 1-3 sessions per day
            num_sessions = random.randint(1, 3)
            
            for _ in range(num_sessions):
                duration = random.randint(15, 90)
                session = StudySession(
                    user_id=user.id,
                    duration=duration,
                    start_time=date - timedelta(hours=random.randint(1, 12)),
                    activity_type=random.choice(['reading', 'quiz', 'flashcards', 'notes']),
                    pages_covered=random.randint(5, 20),
                    date=date.date()
                )
                session.end_time = session.start_time + timedelta(minutes=duration)
                db.session.add(session)
        
        db.session.commit()
        print("✓ Created sample study sessions")


def seed_notifications(user):
    """Create sample notifications"""
    with app.app_context():
        notifications_data = [
            {
                'type': 'update',
                'title': 'StudyMind v2.5 Released!',
                'text': 'New AI features, voice notes, and improved performance.',
                'icon': 'ri-rocket-line',
                'read': False,
                'created_at': datetime.utcnow() - timedelta(hours=2)
            },
            {
                'type': 'achievement',
                'title': 'Achievement Unlocked! 🎉',
                'text': '7-day streak completed. Keep going!',
                'icon': 'ri-trophy-line',
                'read': False,
                'created_at': datetime.utcnow() - timedelta(hours=4)
            },
            {
                'type': 'reminder',
                'title': 'Study Reminder',
                'text': 'Time to review Machine Learning Chapter 5!',
                'icon': 'ri-alarm-line',
                'read': False,
                'created_at': datetime.utcnow() - timedelta(hours=5)
            },
            {
                'type': 'success',
                'title': 'Processing Complete',
                'text': 'Data Structures notes are ready for study.',
                'icon': 'ri-check-line',
                'read': True,
                'created_at': datetime.utcnow() - timedelta(days=1)
            },
            {
                'type': 'warning',
                'title': 'Deadline in 3 days',
                'text': 'Statistics exam approaching. 65% prepared.',
                'icon': 'ri-calendar-event-line',
                'read': False,
                'created_at': datetime.utcnow() - timedelta(days=1)
            },
            {
                'type': 'update',
                'title': 'New: Study Groups',
                'text': 'Collaborate with friends on shared materials.',
                'icon': 'ri-group-line',
                'read': True,
                'created_at': datetime.utcnow() - timedelta(days=3)
            },
            {
                'type': 'error',
                'title': 'Missed Session',
                'text': 'You missed your scheduled Calculus review on Friday.',
                'icon': 'ri-error-warning-line',
                'read': True,
                'created_at': datetime.utcnow() - timedelta(days=4)
            }
        ]
        
        for data in notifications_data:
            notification = Notification(
                user_id=user.id,
                type=data['type'],
                title=data['title'],
                text=data['text'],
                icon=data['icon'],
                read=data['read']
            )
            notification.created_at = data['created_at']
            db.session.add(notification)
        
        db.session.commit()
        print(f"✓ Created {len(notifications_data)} sample notifications")


def seed_daily_progress(user):
    """Create sample daily progress data"""
    with app.app_context():
        # Create progress for the past 14 days
        for days_ago in range(14):
            date = (datetime.utcnow() - timedelta(days=days_ago)).date()
            
            # Random but realistic study data
            study_time = random.randint(30, 120) if days_ago < 7 else random.randint(0, 90)
            
            progress = DailyProgress(
                user_id=user.id,
                date=date,
                study_time=study_time,
                materials_processed=random.randint(0, 3),
                tasks_completed=random.randint(0, 5),
                pages_read=random.randint(10, 50),
                goal_met=study_time >= 60
            )
            db.session.add(progress)
        
        db.session.commit()
        print("✓ Created sample daily progress data")


def seed_all():
    """Seed all sample data"""
    print("\n🌱 Starting database seeding...\n")
    
    create_tables()
    
    with app.app_context():
        user = seed_demo_user()
        seed_materials(user)
        seed_tasks(user)
        seed_study_sessions(user)
        seed_notifications(user)
        seed_daily_progress(user)
        
        db.session.commit()
    
    print("\n✅ Database seeding completed!")
    print("\n📝 Demo Account Credentials:")
    print("   Email: demo@studymind.com")
    print("   Password: demo123\n")


def reset_database():
    """Drop all tables and recreate them"""
    with app.app_context():
        print("⚠ Dropping all tables...")
        db.drop_all()
        print("✓ Tables dropped")
        
        print("Creating new tables...")
        db.create_all()
        print("✓ Tables created")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--reset':
            reset_database()
            seed_all()
        elif sys.argv[1] == '--seed':
            seed_all()
        elif sys.argv[1] == '--create':
            create_tables()
        else:
            print("Usage: python init_db.py [--reset|--seed|--create]")
    else:
        seed_all()