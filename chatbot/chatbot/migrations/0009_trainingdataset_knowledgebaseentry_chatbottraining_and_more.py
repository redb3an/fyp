# Generated by Django 4.2.7 on 2025-07-10 07:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('chatbot', '0008_usersession'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrainingDataset',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('dataset_type', models.CharField(choices=[('fees', 'Fee Information'), ('programs', 'Program Information'), ('admissions', 'Admissions Information'), ('facilities', 'Facilities Information'), ('general', 'General University Information'), ('faq', 'Frequently Asked Questions')], max_length=20)),
                ('version', models.CharField(default='1.0', max_length=20)),
                ('description', models.TextField()),
                ('file_path', models.CharField(help_text='Path to the dataset file', max_length=500)),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive'), ('archived', 'Archived')], default='active', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_used', models.DateTimeField(blank=True, null=True)),
                ('usage_count', models.PositiveIntegerField(default=0)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'chatbot_training_dataset',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='KnowledgeBaseEntry',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('entry_type', models.CharField(choices=[('qa', 'Question-Answer Pair'), ('fact', 'Factual Information'), ('procedure', 'Process/Procedure'), ('policy', 'Policy Information')], max_length=20)),
                ('category', models.CharField(help_text='Category/topic of the entry', max_length=100)),
                ('question', models.TextField(help_text='Question or topic')),
                ('answer', models.TextField(help_text='Answer or information')),
                ('keywords', models.JSONField(default=list, help_text='Keywords for search/retrieval')),
                ('confidence_score', models.FloatField(default=1.0, help_text='Confidence level of the information (0.0-1.0)')),
                ('is_validated', models.BooleanField(default=False, help_text='Whether this entry has been validated')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entries', to='chatbot.trainingdataset')),
            ],
            options={
                'db_table': 'chatbot_knowledge_entry',
                'ordering': ['category', '-confidence_score'],
            },
        ),
        migrations.CreateModel(
            name='ChatbotTraining',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('training_type', models.CharField(choices=[('prompt_update', 'System Prompt Update'), ('knowledge_refresh', 'Knowledge Base Refresh'), ('performance_tune', 'Performance Tuning')], max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=10)),
                ('parameters', models.JSONField(default=dict, help_text='Training parameters and configuration')),
                ('results', models.JSONField(default=dict, help_text='Training results and metrics')),
                ('error_log', models.TextField(blank=True, help_text='Error messages if training failed')),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('datasets_used', models.ManyToManyField(blank=True, to='chatbot.trainingdataset')),
                ('started_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'chatbot_training',
                'ordering': ['-started_at'],
            },
        ),
        migrations.AddIndex(
            model_name='trainingdataset',
            index=models.Index(fields=['dataset_type', 'status'], name='chatbot_tra_dataset_54a287_idx'),
        ),
        migrations.AddIndex(
            model_name='trainingdataset',
            index=models.Index(fields=['status', '-created_at'], name='chatbot_tra_status_77e5dc_idx'),
        ),
        migrations.AddIndex(
            model_name='knowledgebaseentry',
            index=models.Index(fields=['dataset', 'entry_type'], name='chatbot_kno_dataset_9c8413_idx'),
        ),
        migrations.AddIndex(
            model_name='knowledgebaseentry',
            index=models.Index(fields=['category', 'is_validated'], name='chatbot_kno_categor_2a86ad_idx'),
        ),
        migrations.AddIndex(
            model_name='knowledgebaseentry',
            index=models.Index(fields=['confidence_score', '-created_at'], name='chatbot_kno_confide_d7e9a2_idx'),
        ),
        migrations.AddIndex(
            model_name='chatbottraining',
            index=models.Index(fields=['status', '-started_at'], name='chatbot_tra_status_289767_idx'),
        ),
        migrations.AddIndex(
            model_name='chatbottraining',
            index=models.Index(fields=['training_type', 'status'], name='chatbot_tra_trainin_0e45da_idx'),
        ),
    ]
