from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    UserProfile, 
    ChatHistory, 
    Conversation, 
    Message, 
    UserSession,
    TrainingDataset,
    KnowledgeBaseEntry,
    ChatbotTraining
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'theme', 'is_active', 'created_at')
    list_filter = ('theme', 'is_active', 'created_at')
    search_fields = ('full_name', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'message_preview', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('user__username', 'user__email', 'message', 'response')
    readonly_fields = ('timestamp',)
    
    def message_preview(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'message_count', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'message_count', 'last_message_time')
    inlines = [MessageInline]

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'sender', 'content_preview', 'created_at')
    list_filter = ('sender', 'created_at')
    search_fields = ('content', 'conversation__title')
    readonly_fields = ('created_at',)
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_info', 'is_active', 'last_activity', 'expires_at')
    list_filter = ('is_active', 'last_activity', 'expires_at')
    search_fields = ('user__username', 'user__email', 'device_info', 'ip_address')
    readonly_fields = ('created_at', 'last_activity', 'is_expired')

class KnowledgeBaseEntryInline(admin.TabularInline):
    model = KnowledgeBaseEntry
    extra = 0
    fields = ('entry_type', 'category', 'question', 'confidence_score', 'is_validated')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(TrainingDataset)
class TrainingDatasetAdmin(admin.ModelAdmin):
    list_display = ('name', 'dataset_type', 'status', 'entries_count', 'usage_count', 'created_at')
    list_filter = ('dataset_type', 'status', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'last_used', 'entries_count')
    inlines = [KnowledgeBaseEntryInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'dataset_type', 'version', 'description')
        }),
        ('File Information', {
            'fields': ('file_path', 'status')
        }),
        ('Usage Statistics', {
            'fields': ('usage_count', 'last_used', 'entries_count'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def entries_count(self, obj):
        count = obj.entries.count()
        if count > 0:
            url = reverse('admin:chatbot_knowledgebaseentry_changelist') + f'?dataset__id__exact={obj.id}'
            return format_html('<a href="{}">{} entries</a>', url, count)
        return '0 entries'
    entries_count.short_description = 'Knowledge Entries'

@admin.register(KnowledgeBaseEntry)
class KnowledgeBaseEntryAdmin(admin.ModelAdmin):
    list_display = ('question_preview', 'category', 'entry_type', 'dataset', 'confidence_score', 'is_validated', 'created_at')
    list_filter = ('entry_type', 'category', 'is_validated', 'confidence_score', 'dataset', 'created_at')
    search_fields = ('question', 'answer', 'category', 'keywords')
    readonly_fields = ('created_at', 'updated_at', 'keywords_display')
    
    fieldsets = (
        ('Content', {
            'fields': ('dataset', 'entry_type', 'category', 'question', 'answer')
        }),
        ('Metadata', {
            'fields': ('keywords', 'keywords_display', 'confidence_score', 'is_validated'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def question_preview(self, obj):
        return obj.question[:50] + "..." if len(obj.question) > 50 else obj.question
    question_preview.short_description = 'Question'
    
    def keywords_display(self, obj):
        if obj.keywords:
            keywords = obj.keywords[:10]  # Show first 10 keywords
            display = ', '.join(keywords)
            if len(obj.keywords) > 10:
                display += f' ... (+{len(obj.keywords) - 10} more)'
            return display
        return 'No keywords'
    keywords_display.short_description = 'Keywords Preview'
    keywords_display.help_text = 'First 10 keywords for quick reference'

@admin.register(ChatbotTraining)
class ChatbotTrainingAdmin(admin.ModelAdmin):
    list_display = ('training_type', 'status', 'started_at', 'completed_at', 'datasets_count', 'started_by')
    list_filter = ('training_type', 'status', 'started_at')
    search_fields = ('training_type', 'error_log')
    readonly_fields = ('started_at', 'completed_at', 'duration', 'datasets_count')
    filter_horizontal = ('datasets_used',)
    
    fieldsets = (
        ('Training Information', {
            'fields': ('training_type', 'status', 'started_by')
        }),
        ('Configuration', {
            'fields': ('parameters', 'datasets_used'),
        }),
        ('Results', {
            'fields': ('results', 'error_log'),
            'classes': ('collapse',)
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'duration'),
            'classes': ('collapse',)
        })
    )
    
    def datasets_count(self, obj):
        count = obj.datasets_used.count()
        if count > 0:
            datasets = ', '.join([d.name for d in obj.datasets_used.all()[:3]])
            if count > 3:
                datasets += f' ... (+{count - 3} more)'
            return f'{count}: {datasets}'
        return '0 datasets'
    datasets_count.short_description = 'Datasets Used'
    
    def duration(self, obj):
        if obj.completed_at and obj.started_at:
            delta = obj.completed_at - obj.started_at
            hours, remainder = divmod(delta.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours > 0:
                return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
            elif minutes > 0:
                return f"{int(minutes)}m {int(seconds)}s"
            else:
                return f"{int(seconds)}s"
        return 'N/A'
    duration.short_description = 'Duration'

# Admin site customization
admin.site.site_header = "APU Chatbot Administration"
admin.site.site_title = "APU Chatbot Admin"
admin.site.index_title = "Welcome to APU Chatbot Administration"
