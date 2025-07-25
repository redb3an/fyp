# Generated by Django 4.2.7 on 2025-07-13 11:03

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0012_conversationmemory_programrecommendation_and_more'),
    ]

    operations = [
        # Drop the existing ConversationMemory table to recreate with new structure
        migrations.RunSQL(
            "DROP TABLE IF EXISTS chatbot_conversation_memory;",
            reverse_sql="-- No reverse operation needed"
        ),
        
        # Recreate ConversationMemory with the new enhanced structure
        migrations.CreateModel(
            name='ConversationMemory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('memory_strategy', models.CharField(choices=[('short_term', 'Short-term Memory (Recent 5-10 messages)'), ('cross_learning', 'Cross-conversation Learning (Updates KB)'), ('rag_context', 'RAG Context-aware (Enhances retrieval)'), ('hybrid', 'Hybrid Strategy (Combines all approaches)')], default='hybrid', help_text='Strategy for how this memory should be processed and utilized', max_length=20)),
                ('recent_messages', models.JSONField(default=list, help_text='Stores recent conversation messages for short-term memory strategy')),
                ('memory_type', models.CharField(choices=[('context', 'Conversation Context'), ('intent', 'User Intent'), ('preference', 'User Preference'), ('topic', 'Discussion Topic'), ('feedback', 'User Feedback'), ('correction', 'User Correction'), ('insight', 'Extracted Insight')], max_length=20)),
                ('content', models.TextField(help_text='The actual memory content or insight')),
                ('context', models.JSONField(default=dict, help_text='Additional context and metadata')),
                ('priority', models.CharField(choices=[('low', 'Low Priority'), ('medium', 'Medium Priority'), ('high', 'High Priority'), ('critical', 'Critical')], default='medium', max_length=10)),
                ('confidence_score', models.FloatField(default=0.7, help_text='Confidence in this memory (0.0-1.0)')),
                ('relevance_score', models.FloatField(default=0.5, help_text='Relevance to user (0.0-1.0)')),
                ('is_active', models.BooleanField(default=True)),
                ('expires_at', models.DateTimeField(blank=True, help_text='When this memory should expire', null=True)),
                ('access_count', models.PositiveIntegerField(default=0, help_text='How many times this memory was accessed')),
                ('last_accessed', models.DateTimeField(blank=True, null=True)),
                ('has_influenced_kb', models.BooleanField(default=False, help_text='Whether this memory has influenced the knowledge base (cross-learning strategy)')),
                ('rag_weight', models.FloatField(default=1.0, help_text='Weight factor for RAG context strategy (higher = more influence)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memories', to='chatbot.conversation')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conversation_memories', to='auth.user')),
                ('kb_entry_created', models.ForeignKey(blank=True, help_text='KB entry created from this memory (cross-learning strategy)', null=True, on_delete=django.db.models.deletion.SET_NULL, to='chatbot.knowledgebaseentry')),
            ],
            options={
                'db_table': 'chatbot_conversation_memory',
                'ordering': ['-created_at'],
            },
        ),
        
        # Add indexes for the new structure
        migrations.AddIndex(
            model_name='conversationmemory',
            index=models.Index(fields=['conversation', '-created_at'], name='chatbot_conversationmemory_conversation_id_idx'),
        ),
        migrations.AddIndex(
            model_name='conversationmemory',
            index=models.Index(fields=['user', 'memory_type', '-created_at'], name='chatbot_conversationmemory_user_memory_type_idx'),
        ),
        migrations.AddIndex(
            model_name='conversationmemory',
            index=models.Index(fields=['memory_strategy', 'is_active', '-created_at'], name='chatbot_conversationmemory_strategy_active_idx'),
        ),
        migrations.AddIndex(
            model_name='conversationmemory',
            index=models.Index(fields=['is_active', 'priority', '-created_at'], name='chatbot_conversationmemory_active_priority_idx'),
        ),
        migrations.AddIndex(
            model_name='conversationmemory',
            index=models.Index(fields=['expires_at'], name='chatbot_conversationmemory_expires_at_idx'),
        ),
    ]
