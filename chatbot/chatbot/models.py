from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
from django.utils import timezone
from datetime import timedelta
import json
from typing import List, Dict, Any


class SoftDeleteManager(models.Manager):
    """Custom manager that excludes soft-deleted records"""
    
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)
    
    def with_deleted(self):
        """Include soft-deleted records"""
        return super().get_queryset()
    
    def only_deleted(self):
        """Get only soft-deleted records"""
        return super().get_queryset().filter(deleted_at__isnull=False)


class SoftDeleteModel(models.Model):
    """Abstract base class for soft delete functionality"""
    
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="When this record was deleted")
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()  # Manager to access all records including deleted
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False):
        """Soft delete the record"""
        self.deleted_at = timezone.now()
        self.save()
    
    def hard_delete(self, using=None, keep_parents=False):
        """Permanently delete the record"""
        super().delete(using=using, keep_parents=keep_parents)
    
    def restore(self):
        """Restore a soft-deleted record"""
        self.deleted_at = None
        self.save()
    
    @property
    def is_deleted(self):
        """Check if record is soft-deleted"""
        return self.deleted_at is not None
    
    @classmethod
    def bulk_delete(cls, queryset):
        """Bulk soft delete a queryset of records"""
        from django.utils import timezone
        return queryset.update(deleted_at=timezone.now())

class UserProfile(models.Model):
    """
    Extended user profile to store additional user information
    """
    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255)
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='light')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'chatbot_user_profile'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.full_name} ({self.user.email})"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create a UserProfile when a User is created
    """
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the UserProfile when the User is saved
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()

class Conversation(SoftDeleteModel):
    """
    Represents a chat conversation/session
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255, default="New Conversation")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chatbot_conversation'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', '-updated_at']),
            models.Index(fields=['deleted_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"
    
    @property
    def message_count(self):
        return self.messages.count()
    
    @property
    def last_message_time(self):
        last_message = self.messages.order_by('-created_at').first()
        return last_message.created_at if last_message else self.created_at
    
    def delete(self, using=None, keep_parents=False):
        """Soft delete the conversation and all its messages"""
        # Soft delete all messages in this conversation using bulk update
        # This is more efficient than iterating through each message
        from django.utils import timezone
        self.messages.all().update(deleted_at=timezone.now())
        # Soft delete the conversation itself
        super().delete(using=using, keep_parents=keep_parents)

class Message(SoftDeleteModel):
    """
    Individual messages within a conversation
    """
    SENDER_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chatbot_message'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['deleted_at']),
        ]
    
    def __str__(self):
        return f"{self.sender}: {self.content[:50]}..."

class ChatHistory(models.Model):
    """
    Store chat history for logged-in users (Legacy - to be deprecated)
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_history')
    message = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chatbot_chat_history'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Chat by {self.user.email} at {self.timestamp}"

class UserSession(models.Model):
    """
    Track active user sessions across different browsers and devices
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='active_sessions')
    session_key = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    device_info = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'chatbot_user_session'
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user', '-last_activity']),
            models.Index(fields=['session_key']),
            models.Index(fields=['is_active', '-last_activity']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.device_info or 'Unknown Device'}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_stale(self):
        """Check if session is stale (no activity for more than 30 minutes)"""
        stale_threshold = timezone.now() - timedelta(minutes=30)
        return self.last_activity < stale_threshold

    def extend_session(self, hours=24):
        """Extend session expiry"""
        self.expires_at = timezone.now() + timedelta(hours=hours)
        self.save()

    def mark_active(self):
        """Mark session as active and update last activity"""
        self.is_active = True
        self.last_activity = timezone.now()
        self.save(update_fields=['is_active', 'last_activity'])

    def mark_inactive(self):
        """Mark session as inactive"""
        self.is_active = False
        self.last_activity = timezone.now()
        self.save(update_fields=['is_active', 'last_activity'])

    @classmethod
    def cleanup_expired_sessions(cls):
        """Remove expired sessions"""
        expired_count = cls.objects.filter(expires_at__lt=timezone.now()).count()
        cls.objects.filter(expires_at__lt=timezone.now()).delete()
        return expired_count

    @classmethod
    def cleanup_inactive_sessions(cls):
        """Remove inactive sessions"""
        inactive_count = cls.objects.filter(is_active=False).count()
        cls.objects.filter(is_active=False).delete()
        return inactive_count

    @classmethod
    def cleanup_stale_sessions(cls):
        """Remove stale sessions (inactive for more than 30 minutes)"""
        stale_threshold = timezone.now() - timedelta(minutes=30)
        stale_count = cls.objects.filter(
            is_active=True,
            last_activity__lt=stale_threshold
        ).count()
        cls.objects.filter(
            is_active=True,
            last_activity__lt=stale_threshold
        ).delete()
        return stale_count

    @classmethod
    def cleanup_all_old_sessions(cls):
        """Comprehensive cleanup of all old sessions"""
        expired_count = cls.cleanup_expired_sessions()
        inactive_count = cls.cleanup_inactive_sessions()
        stale_count = cls.cleanup_stale_sessions()
        
        return {
            'expired': expired_count,
            'inactive': inactive_count,
            'stale': stale_count,
            'total': expired_count + inactive_count + stale_count
        }

    @classmethod
    def get_active_sessions(cls):
        """Get all truly active, non-expired sessions"""
        # Clean up old sessions first
        cls.cleanup_all_old_sessions()
        
        # Return only active, non-expired sessions
        return cls.objects.filter(
            is_active=True,
            expires_at__gt=timezone.now()
        )

class TrainingDataset(models.Model):
    """
    Dataset used for training or knowledge enhancement
    """
    DATASET_TYPES = [
        ('fees', 'Fee Information'),
        ('programs', 'Program Information'),
        ('admissions', 'Admissions Information'),
        ('facilities', 'Facilities Information'),
        ('general', 'General University Information'),
        ('faq', 'Frequently Asked Questions'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    dataset_type = models.CharField(max_length=20, choices=DATASET_TYPES)
    version = models.CharField(max_length=20, default='1.0')
    description = models.TextField()
    file_path = models.CharField(max_length=500, help_text='Path to the dataset file')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used = models.DateTimeField(null=True, blank=True)
    usage_count = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'chatbot_training_dataset'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['dataset_type', 'status']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.dataset_type})"
    
    def increment_usage(self):
        """Increment usage count and update last_used timestamp"""
        self.usage_count += 1
        self.last_used = timezone.now()
        self.save(update_fields=['usage_count', 'last_used'])

class KnowledgeBaseEntry(models.Model):
    ENTRY_TYPES = [
        ('general', 'General Information'),
        ('program', 'Program Information'),
        ('accommodation', 'Accommodation Information'),
        ('module', 'Module Information'),
        ('fee', 'Fee Information'),
        ('admission', 'Admission Requirements'),
        ('facility', 'Campus Facility'),
    ]
    
    dataset = models.ForeignKey('TrainingDataset', on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField()
    category = models.CharField(max_length=100)
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPES, default='general')
    keywords = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)
    confidence_score = models.FloatField(default=0.8)
    is_validated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Soft delete fields
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Knowledge Base Entries"
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['entry_type']),
            models.Index(fields=['is_validated']),
            models.Index(fields=['is_deleted']),
        ]
    
    def __str__(self):
        return f"{self.category}: {self.question[:50]}..."
    
    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()
    
    @property
    def structured_data(self) -> dict:
        """Return structured data based on entry type"""
        if self.entry_type == 'program':
            return {
                'level': self.metadata.get('level'),
                'name': self.metadata.get('name'),
                'specialization': self.metadata.get('specialization'),
                'duration': self.metadata.get('duration'),
                'study_mode': self.metadata.get('study_mode'),
                'core_modules': self.metadata.get('core_modules', []),
                'specialized_modules': self.metadata.get('specialized_modules', [])
            }
        elif self.entry_type == 'accommodation':
            return {
                'location': self.metadata.get('location'),
                'single_rent': self.metadata.get('single_rent'),
                'sharing_rent': self.metadata.get('sharing_rent'),
                'facilities': self.metadata.get('facilities', []),
                'distance': self.metadata.get('distance')
            }
        elif self.entry_type == 'module':
            return {
                'code': self.metadata.get('code'),
                'name': self.metadata.get('name'),
                'credits': self.metadata.get('credits'),
                'prerequisites': self.metadata.get('prerequisites', []),
                'learning_outcomes': self.metadata.get('learning_outcomes', [])
            }
        return self.metadata

class ChatbotTraining(models.Model):
    """
    Track chatbot training sessions and results
    """
    TRAINING_TYPES = [
        ('prompt_update', 'System Prompt Update'),
        ('knowledge_refresh', 'Knowledge Base Refresh'),
        ('performance_tune', 'Performance Tuning'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    training_type = models.CharField(max_length=20, choices=TRAINING_TYPES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    parameters = models.JSONField(default=dict, help_text='Training parameters and configuration')
    results = models.JSONField(default=dict, help_text='Training results and metrics')
    error_log = models.TextField(blank=True, help_text='Error messages if training failed')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    started_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    datasets_used = models.ManyToManyField(TrainingDataset, blank=True)
    
    class Meta:
        db_table = 'chatbot_training'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['status', '-started_at']),
            models.Index(fields=['training_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.training_type} - {self.status} ({self.started_at})"
    
    def mark_completed(self, results=None):
        """Mark training as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if results:
            self.results.update(results)
        self.save(update_fields=['status', 'completed_at', 'results'])
    
    def mark_failed(self, error_message):
        """Mark training as failed with error message"""
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.error_log = error_message
        self.save(update_fields=['status', 'completed_at', 'error_log'])

class FineTunedModel(models.Model):
    """
    Track fine-tuned models and their deployment status
    """
    STATUS_CHOICES = [
        ('training', 'Training'),
        ('ready', 'Ready'),
        ('deployed', 'Deployed'),
        ('failed', 'Failed'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model_name = models.CharField(max_length=255, unique=True)
    groq_model_id = models.CharField(max_length=255, blank=True, help_text='Groq model ID')
    groq_job_id = models.CharField(max_length=255, blank=True, help_text='Groq fine-tuning job ID')
    base_model = models.CharField(max_length=100, default='llama3-8b-8192')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='training')
    training_record = models.ForeignKey(ChatbotTraining, on_delete=models.CASCADE, related_name='fine_tuned_models')
    
    # Model performance metrics
    trained_tokens = models.PositiveIntegerField(default=0)
    training_examples = models.PositiveIntegerField(default=0)
    validation_loss = models.FloatField(null=True, blank=True)
    training_accuracy = models.FloatField(null=True, blank=True)
    
    # Deployment information
    is_active = models.BooleanField(default=False, help_text='Whether this model is currently active')
    deployment_date = models.DateTimeField(null=True, blank=True)
    last_used = models.DateTimeField(null=True, blank=True)
    usage_count = models.PositiveIntegerField(default=0)
    
    # Version information
    version = models.CharField(max_length=20, default='1.0')
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'chatbot_fine_tuned_model'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['is_active', '-created_at']),
            models.Index(fields=['groq_model_id']),
            models.Index(fields=['groq_job_id']),
        ]
    
    def __str__(self):
        return f"{self.model_name} (v{self.version}) - {self.status}"
    
    def activate(self):
        """Activate this model and deactivate others"""
        # Deactivate other models
        FineTunedModel.objects.filter(is_active=True).update(is_active=False)
        
        # Activate this model
        self.is_active = True
        self.deployment_date = timezone.now()
        self.status = 'deployed'
        self.save()
    
    def deactivate(self):
        """Deactivate this model"""
        self.is_active = False
        self.save()
    
    def increment_usage(self):
        """Increment usage count and update last used timestamp"""
        self.usage_count += 1
        self.last_used = timezone.now()
        self.save(update_fields=['usage_count', 'last_used'])
    
    @classmethod
    def get_active_model(cls):
        """Get the currently active fine-tuned model"""
        return cls.objects.filter(is_active=True, status='deployed').first()
    
    @classmethod
    def get_latest_ready_model(cls):
        """Get the latest ready model"""
        return cls.objects.filter(status='ready').order_by('-created_at').first()
    
    @property
    def is_deployed(self):
        """Check if model is deployed"""
        return self.status == 'deployed' and self.is_active
    
    @property
    def training_duration(self):
        """Calculate training duration if available"""
        if self.training_record.completed_at and self.training_record.started_at:
            return self.training_record.completed_at - self.training_record.started_at
        return None
    
    def get_performance_metrics(self):
        """Get performance metrics summary"""
        return {
            'trained_tokens': self.trained_tokens,
            'training_examples': self.training_examples,
            'validation_loss': self.validation_loss,
            'training_accuracy': self.training_accuracy,
            'usage_count': self.usage_count,
            'training_duration': self.training_duration
        }


class ModelPerformanceMetric(models.Model):
    """
    Track performance metrics for fine-tuned models
    """
    METRIC_TYPES = [
        ('accuracy', 'Accuracy'),
        ('response_time', 'Response Time'),
        ('user_satisfaction', 'User Satisfaction'),
        ('relevance_score', 'Relevance Score'),
        ('engagement_rate', 'Engagement Rate'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model = models.ForeignKey(FineTunedModel, on_delete=models.CASCADE, related_name='performance_metrics')
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES)
    value = models.FloatField()
    measurement_date = models.DateTimeField(auto_now_add=True)
    context = models.JSONField(default=dict, help_text='Additional context for the metric')
    
    class Meta:
        db_table = 'chatbot_model_performance_metric'
        ordering = ['-measurement_date']
        indexes = [
            models.Index(fields=['model', 'metric_type', '-measurement_date']),
        ]
    
    def __str__(self):
        return f"{self.model.model_name} - {self.metric_type}: {self.value}"


class ConversationMemory(models.Model):
    """
    Enhanced conversation memory system with strategic memory management.
    
    This model supports three main memory strategies:
    1. SHORT_TERM: Stores recent conversation context (5-10 messages)
    2. CROSS_LEARNING: Updates knowledge base from user interactions  
    3. RAG_CONTEXT: Provides conversation-aware context for RAG pipeline
    
    Memory Types:
    - context: Short-term conversation context
    - intent: User intentions and goals
    - preference: User preferences and choices
    - topic: Discussion topics and subjects
    - feedback: User feedback on responses
    - correction: User corrections to chatbot responses
    - insight: Extracted insights from conversation patterns
    """
    
    MEMORY_TYPES = [
        ('context', 'Conversation Context'),
        ('intent', 'User Intent'),
        ('preference', 'User Preference'),
        ('topic', 'Discussion Topic'),
        ('feedback', 'User Feedback'),
        ('correction', 'User Correction'),
        ('insight', 'Extracted Insight'),
    ]
    
    # Memory strategy selection - core feature requested
    MEMORY_STRATEGIES = [
        ('short_term', 'Short-term Memory (Recent 5-10 messages)'),
        ('cross_learning', 'Cross-conversation Learning (Updates KB)'),
        ('rag_context', 'RAG Context-aware (Enhances retrieval)'),
        ('hybrid', 'Hybrid Strategy (Combines all approaches)'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low Priority'),
        ('medium', 'Medium Priority'),
        ('high', 'High Priority'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='memories')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversation_memories')
    
    # Memory strategy configuration - NEW FEATURE
    memory_strategy = models.CharField(
        max_length=20, 
        choices=MEMORY_STRATEGIES, 
        default='hybrid',
        help_text='Strategy for how this memory should be processed and utilized'
    )
    
    # Recent conversation messages storage - NEW FEATURE
    recent_messages = models.JSONField(
        default=list,
        help_text='Stores recent conversation messages for short-term memory strategy'
    )
    
    # Memory content and metadata
    memory_type = models.CharField(max_length=20, choices=MEMORY_TYPES)
    content = models.TextField(help_text='The actual memory content or insight')
    context = models.JSONField(default=dict, help_text='Additional context and metadata')
    
    # Memory metadata
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    confidence_score = models.FloatField(default=0.7, help_text='Confidence in this memory (0.0-1.0)')
    relevance_score = models.FloatField(default=0.5, help_text='Relevance to user (0.0-1.0)')
    
    # Memory lifecycle management
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text='When this memory should expire')
    access_count = models.PositiveIntegerField(default=0, help_text='How many times this memory was accessed')
    last_accessed = models.DateTimeField(null=True, blank=True)
    
    # Cross-conversation learning integration - ENHANCED
    has_influenced_kb = models.BooleanField(
        default=False, 
        help_text='Whether this memory has influenced the knowledge base (cross-learning strategy)'
    )
    kb_entry_created = models.ForeignKey(
        KnowledgeBaseEntry, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text='KB entry created from this memory (cross-learning strategy)'
    )
    
    # RAG context integration - ENHANCED
    rag_weight = models.FloatField(
        default=1.0, 
        help_text='Weight factor for RAG context strategy (higher = more influence)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chatbot_conversation_memory'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['conversation', '-created_at']),
            models.Index(fields=['user', 'memory_type', '-created_at']),
            models.Index(fields=['memory_strategy', 'is_active', '-created_at']),
            models.Index(fields=['is_active', 'priority', '-created_at']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.memory_type} ({self.memory_strategy}): {self.content[:50]}..."
    
    def access(self):
        """Mark this memory as accessed and update access statistics"""
        self.access_count += 1
        self.last_accessed = timezone.now()
        self.save(update_fields=['access_count', 'last_accessed'])
    
    def is_expired(self):
        """Check if this memory has expired based on strategy and timestamp"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    def extend_expiry(self, days=7):
        """Extend the expiry of this memory (useful for important memories)"""
        if self.expires_at:
            self.expires_at = max(self.expires_at, timezone.now()) + timedelta(days=days)
        else:
            self.expires_at = timezone.now() + timedelta(days=days)
        self.save(update_fields=['expires_at'])
    
    def update_recent_messages(self, messages: List[Dict[str, Any]]):
        """
        Update recent messages for short-term memory strategy
        
        Args:
            messages: List of message dictionaries with 'content', 'sender', 'timestamp'
        """
        if self.memory_strategy in ['short_term', 'hybrid']:
            # Keep only last 10 messages for short-term strategy
            self.recent_messages = messages[-10:]
            self.save(update_fields=['recent_messages'])
    
    def get_strategy_config(self) -> Dict[str, Any]:
        """Get configuration settings for this memory's strategy"""
        strategy_configs = {
            'short_term': {
                'retention_days': 1,
                'max_messages': 10,
                'priority_boost': 0.0,
                'rag_weight': 0.5
            },
            'cross_learning': {
                'retention_days': 180,
                'max_messages': 5,
                'priority_boost': 0.3,
                'rag_weight': 0.8
            },
            'rag_context': {
                'retention_days': 7,
                'max_messages': 15,
                'priority_boost': 0.2,
                'rag_weight': 1.0
            },
            'hybrid': {
                'retention_days': 30,
                'max_messages': 12,
                'priority_boost': 0.1,
                'rag_weight': 0.9
            }
        }
        return strategy_configs.get(self.memory_strategy, strategy_configs['hybrid'])
    
    @classmethod
    def cleanup_expired(cls):
        """Remove expired memories based on their strategy settings"""
        expired_count = cls.objects.filter(
            expires_at__lt=timezone.now(),
            is_active=True
        ).count()
        cls.objects.filter(
            expires_at__lt=timezone.now(),
            is_active=True
        ).update(is_active=False)
        return expired_count
    
    @classmethod
    def get_active_memories(cls, conversation=None, user=None, memory_type=None, strategy=None):
        """
        Get active, non-expired memories with strategy filtering
        
        Args:
            conversation: Filter by conversation
            user: Filter by user
            memory_type: Filter by memory type
            strategy: Filter by memory strategy
        """
        queryset = cls.objects.filter(is_active=True)
        
        # Filter out expired memories
        queryset = queryset.filter(
            models.Q(expires_at__isnull=True) | 
            models.Q(expires_at__gt=timezone.now())
        )
        
        if conversation:
            queryset = queryset.filter(conversation=conversation)
        if user:
            queryset = queryset.filter(user=user)
        if memory_type:
            queryset = queryset.filter(memory_type=memory_type)
        if strategy:
            queryset = queryset.filter(memory_strategy=strategy)
            
        return queryset.order_by('-priority', '-relevance_score', '-created_at')
    
    @classmethod
    def get_short_term_context(cls, conversation: 'Conversation', max_messages: int = 10) -> List[Dict[str, Any]]:
        """
        Get short-term conversation context using short_term strategy memories
        
        Returns:
            List of recent messages with metadata
        """
        short_term_memories = cls.get_active_memories(
            conversation=conversation,
            strategy='short_term'
        )
        
        all_messages = []
        for memory in short_term_memories:
            if memory.recent_messages:
                all_messages.extend(memory.recent_messages)
        
        # Sort by timestamp and return most recent
        all_messages.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return all_messages[:max_messages]
    
    @classmethod
    def get_cross_learning_insights(cls, user: User = None) -> List['ConversationMemory']:
        """
        Get memories that should influence knowledge base (cross-learning strategy)
        
        Args:
            user: Filter by specific user (optional)
        """
        queryset = cls.get_active_memories(
            user=user,
            strategy='cross_learning'
        ).filter(
            memory_type__in=['correction', 'feedback', 'insight'],
            has_influenced_kb=False
        )
        
        return list(queryset)
    
    @classmethod
    def get_rag_context_memories(cls, conversation: 'Conversation', user: User = None) -> List['ConversationMemory']:
        """
        Get memories optimized for RAG context enhancement
        
        Args:
            conversation: Current conversation
            user: User for cross-conversation context
        """
        queryset = cls.get_active_memories(
            conversation=conversation,
            user=user,
            strategy='rag_context'
        ).filter(
            memory_type__in=['intent', 'preference', 'topic', 'context']
        )
        
        return list(queryset.order_by('-rag_weight', '-relevance_score')[:15])


class ProgramRecommendation(models.Model):
    """
    Store program recommendations made to users for tracking and improvement
    """
    RECOMMENDATION_STATUS = [
        ('pending', 'Pending Review'),
        ('accepted', 'Accepted by User'),
        ('rejected', 'Rejected by User'),
        ('applied', 'User Applied'),
        ('enrolled', 'User Enrolled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='program_recommendations')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='recommendations')
    
    # Recommendation details
    recommended_programs = models.JSONField(help_text='List of recommended programs with scores')
    user_criteria = models.JSONField(help_text='User criteria used for recommendation')
    recommendation_reasoning = models.TextField(default='', help_text='Why these programs were recommended')
    
    # User response
    status = models.CharField(max_length=10, choices=RECOMMENDATION_STATUS, default='pending')
    user_feedback = models.TextField(blank=True, help_text='User feedback on recommendations')
    selected_programs = models.JSONField(default=list, help_text='Programs user showed interest in')
    
    # Metadata
    confidence_score = models.FloatField(default=0.7, help_text='Confidence in recommendation quality')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chatbot_program_recommendation'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"Recommendation for {self.user.email} - {self.status}"
