import os
import json
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from chatbot.models import FineTunedModel, ChatbotTraining
from chatbot.services.finetune_service import finetune_manager
from django.utils import timezone


class Command(BaseCommand):
    help = 'Run complete fine-tuning process: prepare data, train model, and deploy'

    def add_arguments(self, parser):
        parser.add_argument(
            '--prepare-data',
            action='store_true',
            help='Prepare training data first (runs finetune_groq command)'
        )
        parser.add_argument(
            '--model-name',
            type=str,
            default='apu-educational-counselor',
            help='Name for the fine-tuned model (default: apu-educational-counselor)'
        )
        parser.add_argument(
            '--training-file',
            type=str,
            help='Path to training data file (JSONL format)'
        )
        parser.add_argument(
            '--epochs',
            type=int,
            default=3,
            help='Number of training epochs (default: 3)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1,
            help='Training batch size (default: 1)'
        )
        parser.add_argument(
            '--learning-rate',
            type=float,
            default=1.0,
            help='Learning rate multiplier (default: 1.0)'
        )
        parser.add_argument(
            '--deploy',
            action='store_true',
            help='Deploy the model after training is complete'
        )
        parser.add_argument(
            '--monitor',
            action='store_true',
            help='Monitor an existing training job'
        )
        parser.add_argument(
            '--job-id',
            type=str,
            help='Job ID to monitor (required with --monitor)'
        )

    def handle(self, *args, **options):
        if options['monitor']:
            return self._monitor_training(options)
        
        if options['prepare_data']:
            self._prepare_data(options)
        
        training_file = options['training_file']
        if not training_file:
            # Use default training file path
            training_file = os.path.join('groq_finetune_data', f"{options['model_name']}_training_data.jsonl")
        
        if not os.path.exists(training_file):
            raise CommandError(f'Training file not found: {training_file}')
        
        self.stdout.write(f'Starting fine-tuning process with file: {training_file}')
        
        # Prepare hyperparameters
        hyperparameters = {
            'n_epochs': options['epochs'],
            'batch_size': options['batch_size'],
            'learning_rate_multiplier': options['learning_rate']
        }
        
        # Start fine-tuning
        result = finetune_manager.prepare_and_start_fine_tuning(
            training_file_path=training_file,
            model_name=options['model_name'],
            hyperparameters=hyperparameters
        )
        
        if not result['success']:
            raise CommandError(f'Fine-tuning failed: {result["error"]}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Fine-tuning started successfully!\n'
                f'Job ID: {result["job_id"]}\n'
                f'Model Name: {result["model_name"]}\n'
                f'Training Record ID: {result["training_record_id"]}'
            )
        )
        
        # Create FineTunedModel record
        admin_user = User.objects.filter(is_superuser=True).first()
        training_record = ChatbotTraining.objects.get(id=result['training_record_id'])
        
        fine_tuned_model = FineTunedModel.objects.create(
            model_name=options['model_name'],
            groq_job_id=result['job_id'],
            status='training',
            training_record=training_record,
            created_by=admin_user,
            description=f'Fine-tuned model with {hyperparameters["n_epochs"]} epochs'
        )
        
        self.stdout.write(f'Created FineTunedModel record: {fine_tuned_model.id}')
        
        # Monitor the training if requested
        if options['deploy']:
            self.stdout.write('Monitoring training progress...')
            self._monitor_training_until_complete(result['job_id'], str(training_record.id), fine_tuned_model)

    def _prepare_data(self, options):
        """Prepare training data using the finetune_groq command"""
        from django.core.management import call_command
        
        self.stdout.write('Preparing training data...')
        
        call_command(
            'finetune_groq',
            '--model-name', options['model_name'],
            '--output-dir', 'groq_finetune_data'
        )
        
        self.stdout.write('Training data prepared successfully!')

    def _monitor_training(self, options):
        """Monitor an existing training job"""
        job_id = options['job_id']
        if not job_id:
            raise CommandError('Job ID is required when using --monitor')
        
        self.stdout.write(f'Monitoring training job: {job_id}')
        
        # Find the training record
        try:
            training_record = ChatbotTraining.objects.get(parameters__job_id=job_id)
            fine_tuned_model = FineTunedModel.objects.get(groq_job_id=job_id)
        except (ChatbotTraining.DoesNotExist, FineTunedModel.DoesNotExist):
            raise CommandError(f'Training record not found for job ID: {job_id}')
        
        # Monitor the job
        result = finetune_manager.get_training_status(str(training_record.id))
        
        if not result['success']:
            raise CommandError(f'Failed to get training status: {result["error"]}')
        
        self.stdout.write(f'Training Status: {result["status"]}')
        
        if result['status'] == 'completed':
            self._handle_training_completion(training_record, fine_tuned_model, result)
        elif result['status'] == 'failed':
            self.stdout.write(self.style.ERROR(f'Training failed: {result["error_log"]}'))
        
        return result

    def _monitor_training_until_complete(self, job_id, training_record_id, fine_tuned_model):
        """Monitor training until completion"""
        import time
        
        while True:
            result = finetune_manager.get_training_status(training_record_id)
            
            if not result['success']:
                self.stdout.write(self.style.ERROR(f'Error monitoring training: {result["error"]}'))
                return
            
            status = result['status']
            self.stdout.write(f'Current status: {status}')
            
            if status == 'completed':
                self._handle_training_completion(
                    ChatbotTraining.objects.get(id=training_record_id),
                    fine_tuned_model,
                    result
                )
                break
            elif status == 'failed':
                self.stdout.write(self.style.ERROR(f'Training failed: {result["error_log"]}'))
                fine_tuned_model.status = 'failed'
                fine_tuned_model.save()
                break
            
            # Wait before checking again
            time.sleep(30)

    def _handle_training_completion(self, training_record, fine_tuned_model, result):
        """Handle training completion"""
        self.stdout.write(self.style.SUCCESS('Training completed successfully!'))
        
        # Update fine-tuned model
        results = result.get('results', {})
        fine_tuned_model.status = 'ready'
        fine_tuned_model.groq_model_id = results.get('fine_tuned_model', '')
        fine_tuned_model.trained_tokens = results.get('trained_tokens', 0)
        fine_tuned_model.save()
        
        self.stdout.write(f'Fine-tuned model ready: {fine_tuned_model.groq_model_id}')
        
        # Test the model
        self._test_model(fine_tuned_model)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Fine-tuning process completed!\n'
                f'Model ID: {fine_tuned_model.groq_model_id}\n'
                f'Trained Tokens: {fine_tuned_model.trained_tokens}\n'
                f'Status: {fine_tuned_model.status}'
            )
        )

    def _test_model(self, fine_tuned_model):
        """Test the fine-tuned model"""
        if not fine_tuned_model.groq_model_id:
            return
        
        self.stdout.write('Testing fine-tuned model...')
        
        test_messages = [
            {"role": "user", "content": "Tell me about the Computer Science program at APU"}
        ]
        
        from chatbot.services.finetune_service import GroqFineTuneService
        service = GroqFineTuneService()
        
        test_result = service.test_fine_tuned_model(fine_tuned_model.groq_model_id, test_messages)
        
        if test_result['success']:
            self.stdout.write(f'Test Response: {test_result["response"][:200]}...')
            self.stdout.write(f'Token Usage: {test_result["usage"]["total_tokens"]}')
        else:
            self.stdout.write(self.style.WARNING(f'Test failed: {test_result["error"]}'))

    def _deploy_model(self, fine_tuned_model):
        """Deploy the fine-tuned model"""
        self.stdout.write('Deploying fine-tuned model...')
        
        fine_tuned_model.activate()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Model deployed successfully!\n'
                f'Model {fine_tuned_model.model_name} is now active.'
            )
        ) 