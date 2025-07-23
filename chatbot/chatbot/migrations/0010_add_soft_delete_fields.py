# Generated manually for soft delete functionality

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0009_trainingdataset_knowledgebaseentry_chatbottraining_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='deleted_at',
            field=models.DateTimeField(blank=True, help_text='When this record was deleted', null=True),
        ),
        migrations.AddField(
            model_name='message',
            name='deleted_at',
            field=models.DateTimeField(blank=True, help_text='When this record was deleted', null=True),
        ),
        migrations.AddIndex(
            model_name='conversation',
            index=models.Index(fields=['deleted_at'], name='chatbot_conversation_deleted_at_idx'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['deleted_at'], name='chatbot_message_deleted_at_idx'),
        ),
    ] 