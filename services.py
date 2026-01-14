"""
StudyMind Database Services
Business logic and utility functions for database operations
"""

from datetime import datetime, timedelta
from sqlalchemy import func
from models import db, User, Material, Task, StudySession, Notification, DailyProgress, UserSettings


class UserService:
    """Service class for user-related operations"""
    
    @staticmethod
    def get_user_by_email(email):
        """Get user by email address"""
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID"""
        return User.query.get(user_id)
    
    @staticmethod
    def update_last_active(user_id):
        """Update user's last active timestamp"""
        user = User.query.get(user_id)
        if user:
            user.last_active = datetime.utcnow()
            db.session.commit()
    
    @staticmethod
    def get_user_dashboard_data(user_id):
        """Get all dashboard data for a user"""
        user = User.query.get(user_id)
        if not user:
            return None
        
        # Get stats
        stats = StatsService.get_user_stats(user_id)
        
        # Get recent materials
        recent_materials = Material.query.filter_by(user_id=user_id)\
            .order_by(Material.created_at.desc())\
            .limit(5).all()
        
        # Get pending tasks
        pending_tasks = Task.query.filter_by(user_id=user_id, completed=False)\
            .order_by(Task.due_date.asc())\
            .limit(5).all()
        
        # Get unread notifications
        notifications = Notification.query.filter_by(user_id=user_id, read=False)\
            .order_by(Notification.created_at.desc())\
            .limit(10).all()
        
        return {
            'user': user.to_dict(),
            'stats': stats,
            'recent_materials': [m.to_dict() for m in recent_materials],
            'pending_tasks': [t.to_dict() for t in pending_tasks],
            'notifications': [n.to_dict() for n in notifications]
        }


class MaterialService:
    """Service class for material-related operations"""
    
    @staticmethod
    def get_user_materials(user_id, filters=None, page=1, per_page=10):
        """Get paginated materials for a user with optional filters"""
        query = Material.query.filter_by(user_id=user_id)
        
        if filters:
            if filters.get('status'):
                query = query.filter_by(status=filters['status'])
            if filters.get('file_type'):
                query = query.filter_by(file_type=filters['file_type'])
            if filters.get('subject'):
                query = query.filter_by(subject=filters['subject'])
            if filters.get('search'):
                search = f"%{filters['search']}%"
                query = query.filter(Material.name.ilike(search))
        
        return query.order_by(Material.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def update_material_status(material_id, status):
        """Update material processing status"""
        material = Material.query.get(material_id)
        if material:
            material.status = status
            material.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Create notification if processing is complete
            if status == 'completed':
                notification = Notification(
                    user_id=material.user_id,
                    type='success',
                    title='Processing Complete',
                    text=f'{material.name} is ready for study.',
                    icon='ri-check-line'
                )
                db.session.add(notification)
                db.session.commit()
            
            return material
        return None
    
    @staticmethod
    def get_material_stats(user_id):
        """Get material statistics for a user"""
        total = Material.query.filter_by(user_id=user_id).count()
        by_type = db.session.query(
            Material.file_type,
            func.count(Material.id)
        ).filter_by(user_id=user_id).group_by(Material.file_type).all()
        
        by_status = db.session.query(
            Material.status,
            func.count(Material.id)
        ).filter_by(user_id=user_id).group_by(Material.status).all()
        
        return {
            'total': total,
            'by_type': dict(by_type),
            'by_status': dict(by_status)
        }


class TaskService:
    """Service class for task-related operations"""
    
    @staticmethod
    def get_user_tasks(user_id, completed=None, due_soon=False):
        """Get tasks for a user with filters"""
        query = Task.query.filter_by(user_id=user_id)
        
        if completed is not None:
            query = query.filter_by(completed=completed)
        
        if due_soon:
            # Tasks due in the next 3 days
            deadline = datetime.utcnow() + timedelta(days=3)
            query = query.filter(
                Task.due_date <= deadline,
                Task.completed == False
            )
        
        return query.order_by(Task.due_date.asc()).all()
    
    @staticmethod
    def get_upcoming_deadlines(user_id, days=7):
        """Get upcoming task deadlines"""
        deadline = datetime.utcnow() + timedelta(days=days)
        
        return Task.query.filter(
            Task.user_id == user_id,
            Task.due_date <= deadline,
            Task.due_date >= datetime.utcnow(),
            Task.completed == False
        ).order_by(Task.due_date.asc()).all()
    
    @staticmethod
    def create_study_tasks_for_material(user_id, material_id, goal_type):
        """Auto-generate study tasks based on material and goal"""
        material = Material.query.get(material_id)
        if not material:
            return []
        
        tasks_config = {
            'understand': [
                {'title': f'Read through {material.name}', 'type': 'reading', 'time': 30},
                {'title': f'Take notes on key concepts', 'type': 'notes', 'time': 20},
                {'title': f'Create summary of {material.name}', 'type': 'summary', 'time': 15}
            ],
            'exam_prep': [
                {'title': f'First read of {material.name}', 'type': 'reading', 'time': 30},
                {'title': f'Create flashcards', 'type': 'flashcards', 'time': 20},
                {'title': f'Practice quiz', 'type': 'quiz', 'time': 15},
                {'title': f'Review weak areas', 'type': 'review', 'time': 20},
                {'title': f'Final review', 'type': 'review', 'time': 15}
            ],
            'quick_review': [
                {'title': f'Skim {material.name}', 'type': 'reading', 'time': 15},
                {'title': f'Review key points', 'type': 'review', 'time': 10}
            ]
        }
        
        tasks_to_create = tasks_config.get(goal_type, tasks_config['understand'])
        created_tasks = []
        
        base_date = datetime.utcnow()
        for i, task_info in enumerate(tasks_to_create):
            task = Task(
                user_id=user_id,
                material_id=material_id,
                title=task_info['title'],
                task_type=task_info['type'],
                estimated_time=task_info['time'],
                due_date=base_date + timedelta(days=i+1),
                priority='medium'
            )
            db.session.add(task)
            created_tasks.append(task)
        
        db.session.commit()
        return created_tasks


class SessionService:
    """Service class for study session operations"""
    
    @staticmethod
    def start_session(user_id, material_id=None, activity_type='reading'):
        """Start a new study session"""
        session = StudySession(
            user_id=user_id,
            material_id=material_id,
            activity_type=activity_type,
            date=datetime.utcnow().date()
        )
        db.session.add(session)
        db.session.commit()
        return session
    
    @staticmethod
    def end_session(session_id, duration, pages_covered=0):
        """End a study session and update stats"""
        session = StudySession.query.get(session_id)
        if not session:
            return None
        
        session.end_time = datetime.utcnow()
        session.duration = duration
        session.pages_covered = pages_covered
        
        # Update user stats
        user = User.query.get(session.user_id)
        if user:
            user.total_study_time += duration
        
        # Update daily progress
        ProgressService.update_daily(
            session.user_id,
            study_time=duration,
            pages_read=pages_covered
        )
        
        db.session.commit()
        return session
    
    @staticmethod
    def get_session_history(user_id, days=30):
        """Get study session history"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        return StudySession.query.filter(
            StudySession.user_id == user_id,
            StudySession.start_time >= start_date
        ).order_by(StudySession.start_time.desc()).all()


class StatsService:
    """Service class for statistics and analytics"""
    
    @staticmethod
    def get_user_stats(user_id):
        """Get comprehensive user statistics"""
        user = User.query.get(user_id)
        if not user:
            return None
        
        # This week's data
        week_start = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
        last_week_start = week_start - timedelta(days=7)
        
        # Study time this week
        week_sessions = StudySession.query.filter(
            StudySession.user_id == user_id,
            StudySession.start_time >= week_start
        ).all()
        week_time = sum(s.duration or 0 for s in week_sessions)
        
        # Study time last week
        last_week_sessions = StudySession.query.filter(
            StudySession.user_id == user_id,
            StudySession.start_time >= last_week_start,
            StudySession.start_time < week_start
        ).all()
        last_week_time = sum(s.duration or 0 for s in last_week_sessions)
        
        # Calculate change percentage
        if last_week_time > 0:
            time_change = ((week_time - last_week_time) / last_week_time) * 100
        else:
            time_change = 100 if week_time > 0 else 0
        
        # Materials
        total_materials = Material.query.filter_by(user_id=user_id).count()
        new_materials = Material.query.filter(
            Material.user_id == user_id,
            Material.created_at >= week_start
        ).count()
        
        # Tasks
        total_tasks = Task.query.filter_by(user_id=user_id).count()
        completed_tasks = Task.query.filter_by(user_id=user_id, completed=True).count()
        
        return {
            'study_time': {
                'value': round(week_time / 60, 1),
                'change': round(time_change),
                'unit': 'hours'
            },
            'materials': {
                'total': total_materials,
                'new_this_week': new_materials
            },
            'tasks': {
                'total': total_tasks,
                'completed': completed_tasks,
                'completion_rate': round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0)
            },
            'streak': user.streak
        }
    
    @staticmethod
    def get_study_heatmap(user_id, days=90):
        """Get study activity heatmap data"""
        start_date = datetime.utcnow().date() - timedelta(days=days)
        
        progress = DailyProgress.query.filter(
            DailyProgress.user_id == user_id,
            DailyProgress.date >= start_date
        ).all()
        
        return {
            p.date.isoformat(): {
                'study_time': p.study_time,
                'goal_met': p.goal_met
            } for p in progress
        }


class ProgressService:
    """Service class for progress tracking"""
    
    @staticmethod
    def update_daily(user_id, study_time=0, materials_processed=0, 
                     tasks_completed=0, pages_read=0):
        """Update daily progress"""
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
        
        # Check daily goal
        settings = UserSettings.query.filter_by(user_id=user_id).first()
        if settings and progress.study_time >= settings.daily_goal:
            if not progress.goal_met:
                progress.goal_met = True
                ProgressService.update_streak(user_id)
        
        db.session.commit()
        return progress
    
    @staticmethod
    def update_streak(user_id):
        """Update user's study streak"""
        user = User.query.get(user_id)
        if not user:
            return
        
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        
        yesterday_progress = DailyProgress.query.filter_by(
            user_id=user_id,
            date=yesterday,
            goal_met=True
        ).first()
        
        if yesterday_progress:
            user.streak += 1
        else:
            # Check if this is the first day or streak was broken
            user.streak = 1
        
        # Achievement notifications for milestones
        milestones = [7, 14, 30, 60, 100, 365]
        if user.streak in milestones:
            NotificationService.create_achievement(
                user_id,
                f'🔥 {user.streak}-Day Streak!',
                f'Incredible! You\'ve studied for {user.streak} days in a row!'
            )
        
        db.session.commit()
    
    @staticmethod
    def get_weekly_summary(user_id):
        """Get weekly progress summary"""
        week_start = datetime.utcnow().date() - timedelta(days=datetime.utcnow().weekday())
        
        progress = DailyProgress.query.filter(
            DailyProgress.user_id == user_id,
            DailyProgress.date >= week_start
        ).all()
        
        return {
            'total_study_time': sum(p.study_time for p in progress),
            'total_tasks': sum(p.tasks_completed for p in progress),
            'total_pages': sum(p.pages_read for p in progress),
            'days_goal_met': sum(1 for p in progress if p.goal_met),
            'daily': [p.to_dict() for p in progress]
        }


class NotificationService:
    """Service class for notifications"""
    
    @staticmethod
    def create(user_id, type, title, text, icon=None):
        """Create a new notification"""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            text=text,
            icon=icon
        )
        db.session.add(notification)
        db.session.commit()
        return notification
    
    @staticmethod
    def create_achievement(user_id, title, text):
        """Create an achievement notification"""
        return NotificationService.create(
            user_id,
            type='achievement',
            title=title,
            text=text,
            icon='ri-trophy-line'
        )
    
    @staticmethod
    def create_reminder(user_id, title, text):
        """Create a reminder notification"""
        return NotificationService.create(
            user_id,
            type='reminder',
            title=title,
            text=text,
            icon='ri-alarm-line'
        )
    
    @staticmethod
    def create_deadline_warning(user_id, task):
        """Create a deadline warning notification"""
        days_left = (task.due_date.date() - datetime.utcnow().date()).days
        
        return NotificationService.create(
            user_id,
            type='warning',
            title=f'Deadline in {days_left} day{"s" if days_left != 1 else ""}',
            text=f'{task.title} is due soon!',
            icon='ri-calendar-event-line'
        )
    
    @staticmethod
    def get_unread_count(user_id):
        """Get count of unread notifications"""
        return Notification.query.filter_by(user_id=user_id, read=False).count()
    
    @staticmethod
    def mark_all_read(user_id):
        """Mark all notifications as read"""
        Notification.query.filter_by(user_id=user_id, read=False)\
            .update({'read': True})
        db.session.commit()