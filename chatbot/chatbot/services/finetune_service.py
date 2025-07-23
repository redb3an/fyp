import logging
import os
import json
import time
from typing import Dict, Any, Optional, List
from groq import Groq
from django.conf import settings
from django.utils import timezone
from ..models import ChatbotTraining, TrainingDataset

logger = logging.getLogger(__name__)


class GroqFineTuneService:
    """
    Service for managing Groq fine-tuning operations
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'GROQ_API_KEY', os.environ.get('GROQ_API_KEY'))
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in settings or environment variables")
        
        self.client = Groq(api_key=self.api_key)
        self.base_model = "llama3-8b-8192"  # Base model for fine-tuning
        
    def upload_training_file(self, file_path: str, purpose: str = "fine-tune") -> Dict[str, Any]:
        """
        Upload training data file to Groq
        
        Args:
            file_path: Path to the training data file (JSONL format)
            purpose: Purpose of the file (default: "fine-tune")
            
        Returns:
            Dictionary containing file upload response
        """
        try:
            logger.info(f"Uploading training file: {file_path}")
            
            with open(file_path, 'rb') as file:
                response = self.client.files.create(
                    file=file,
                    purpose=purpose
                )
            
            logger.info(f"File uploaded successfully: {response.id}")
            return {
                'success': True,
                'file_id': response.id,
                'filename': response.filename,
                'purpose': response.purpose,
                'status': response.status,
                'bytes': response.bytes,
                'created_at': response.created_at
            }
            
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_fine_tuning_job(self, training_file_id: str, model_name: str, 
                             hyperparameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a fine-tuning job on Groq
        
        Args:
            training_file_id: ID of the uploaded training file
            model_name: Name for the fine-tuned model
            hyperparameters: Optional hyperparameters for training
            
        Returns:
            Dictionary containing job creation response
        """
        try:
            logger.info(f"Creating fine-tuning job for model: {model_name}")
            
            # Default hyperparameters
            default_hyperparameters = {
                "n_epochs": 3,
                "batch_size": 1,
                "learning_rate_multiplier": 1.0
            }
            
            if hyperparameters:
                default_hyperparameters.update(hyperparameters)
            
            response = self.client.fine_tuning.jobs.create(
                training_file=training_file_id,
                model=self.base_model,
                suffix=model_name,
                hyperparameters=default_hyperparameters
            )
            
            logger.info(f"Fine-tuning job created successfully: {response.id}")
            return {
                'success': True,
                'job_id': response.id,
                'object': response.object,
                'model': response.model,
                'created_at': response.created_at,
                'finished_at': response.finished_at,
                'fine_tuned_model': response.fine_tuned_model,
                'status': response.status,
                'trained_tokens': response.trained_tokens,
                'hyperparameters': response.hyperparameters
            }
            
        except Exception as e:
            logger.error(f"Error creating fine-tuning job: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_fine_tuning_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of a fine-tuning job
        
        Args:
            job_id: ID of the fine-tuning job
            
        Returns:
            Dictionary containing job status information
        """
        try:
            response = self.client.fine_tuning.jobs.retrieve(job_id)
            
            return {
                'success': True,
                'job_id': response.id,
                'status': response.status,
                'model': response.model,
                'fine_tuned_model': response.fine_tuned_model,
                'created_at': response.created_at,
                'finished_at': response.finished_at,
                'trained_tokens': response.trained_tokens,
                'validation_file': response.validation_file,
                'training_file': response.training_file,
                'hyperparameters': response.hyperparameters,
                'result_files': response.result_files,
                'error': response.error
            }
            
        except Exception as e:
            logger.error(f"Error retrieving job status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_fine_tuning_jobs(self, limit: int = 20) -> Dict[str, Any]:
        """
        List all fine-tuning jobs
        
        Args:
            limit: Maximum number of jobs to return
            
        Returns:
            Dictionary containing list of jobs
        """
        try:
            response = self.client.fine_tuning.jobs.list(limit=limit)
            
            jobs = []
            for job in response.data:
                jobs.append({
                    'job_id': job.id,
                    'status': job.status,
                    'model': job.model,
                    'fine_tuned_model': job.fine_tuned_model,
                    'created_at': job.created_at,
                    'finished_at': job.finished_at,
                    'trained_tokens': job.trained_tokens
                })
            
            return {
                'success': True,
                'jobs': jobs,
                'has_more': response.has_more
            }
            
        except Exception as e:
            logger.error(f"Error listing fine-tuning jobs: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancel_fine_tuning_job(self, job_id: str) -> Dict[str, Any]:
        """
        Cancel a fine-tuning job
        
        Args:
            job_id: ID of the fine-tuning job to cancel
            
        Returns:
            Dictionary containing cancellation response
        """
        try:
            response = self.client.fine_tuning.jobs.cancel(job_id)
            
            return {
                'success': True,
                'job_id': response.id,
                'status': response.status,
                'model': response.model,
                'fine_tuned_model': response.fine_tuned_model
            }
            
        except Exception as e:
            logger.error(f"Error canceling fine-tuning job: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_fine_tuned_model(self, model_id: str) -> Dict[str, Any]:
        """
        Delete a fine-tuned model
        
        Args:
            model_id: ID of the fine-tuned model to delete
            
        Returns:
            Dictionary containing deletion response
        """
        try:
            response = self.client.models.delete(model_id)
            
            return {
                'success': True,
                'model_id': model_id,
                'deleted': response.deleted
            }
            
        except Exception as e:
            logger.error(f"Error deleting fine-tuned model: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_fine_tuned_model(self, model_id: str, test_messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Test a fine-tuned model with sample messages
        
        Args:
            model_id: ID of the fine-tuned model
            test_messages: List of test messages in OpenAI format
            
        Returns:
            Dictionary containing test results
        """
        try:
            logger.info(f"Testing fine-tuned model: {model_id}")
            
            completion = self.client.chat.completions.create(
                model=model_id,
                messages=test_messages,
                temperature=0.7,
                max_tokens=1024
            )
            
            return {
                'success': True,
                'model_id': model_id,
                'response': completion.choices[0].message.content,
                'usage': {
                    'prompt_tokens': completion.usage.prompt_tokens,
                    'completion_tokens': completion.usage.completion_tokens,
                    'total_tokens': completion.usage.total_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"Error testing fine-tuned model: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def start_fine_tuning_process(self, training_file_path: str, model_name: str, 
                                training_record_id: str, hyperparameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Start the complete fine-tuning process
        
        Args:
            training_file_path: Path to the training data file
            model_name: Name for the fine-tuned model
            training_record_id: ID of the training record in database
            hyperparameters: Optional hyperparameters for training
            
        Returns:
            Dictionary containing process results
        """
        try:
            # Get training record
            training_record = ChatbotTraining.objects.get(id=training_record_id)
            training_record.status = 'running'
            training_record.save()
            
            logger.info(f"Starting fine-tuning process for: {model_name}")
            
            # Step 1: Upload training file
            upload_result = self.upload_training_file(training_file_path)
            if not upload_result['success']:
                training_record.status = 'failed'
                training_record.error_log = f"File upload failed: {upload_result['error']}"
                training_record.save()
                return upload_result
            
            file_id = upload_result['file_id']
            
            # Step 2: Create fine-tuning job
            job_result = self.create_fine_tuning_job(file_id, model_name, hyperparameters)
            if not job_result['success']:
                training_record.status = 'failed'
                training_record.error_log = f"Job creation failed: {job_result['error']}"
                training_record.save()
                return job_result
            
            job_id = job_result['job_id']
            
            # Update training record with job information
            training_record.parameters.update({
                'file_id': file_id,
                'job_id': job_id,
                'model_name': model_name,
                'hyperparameters': hyperparameters or {}
            })
            training_record.save()
            
            logger.info(f"Fine-tuning process started successfully. Job ID: {job_id}")
            
            return {
                'success': True,
                'job_id': job_id,
                'file_id': file_id,
                'model_name': model_name,
                'training_record_id': training_record_id,
                'status': 'running'
            }
            
        except Exception as e:
            logger.error(f"Error starting fine-tuning process: {str(e)}")
            try:
                training_record = ChatbotTraining.objects.get(id=training_record_id)
                training_record.status = 'failed'
                training_record.error_log = str(e)
                training_record.save()
            except:
                pass
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def monitor_fine_tuning_job(self, job_id: str, training_record_id: str) -> Dict[str, Any]:
        """
        Monitor a fine-tuning job and update the training record
        
        Args:
            job_id: ID of the fine-tuning job
            training_record_id: ID of the training record in database
            
        Returns:
            Dictionary containing monitoring results
        """
        try:
            # Get job status
            status_result = self.get_fine_tuning_job_status(job_id)
            if not status_result['success']:
                return status_result
            
            # Update training record
            training_record = ChatbotTraining.objects.get(id=training_record_id)
            
            job_status = status_result['status']
            
            if job_status == 'succeeded':
                training_record.status = 'completed'
                training_record.completed_at = timezone.now()
                training_record.results = {
                    'fine_tuned_model': status_result['fine_tuned_model'],
                    'trained_tokens': status_result['trained_tokens'],
                    'job_id': job_id,
                    'finished_at': status_result['finished_at']
                }
                logger.info(f"Fine-tuning job completed successfully: {status_result['fine_tuned_model']}")
                
            elif job_status == 'failed':
                training_record.status = 'failed'
                training_record.error_log = f"Fine-tuning job failed: {status_result.get('error', 'Unknown error')}"
                logger.error(f"Fine-tuning job failed: {job_id}")
                
            elif job_status == 'cancelled':
                training_record.status = 'cancelled'
                logger.info(f"Fine-tuning job cancelled: {job_id}")
                
            else:
                # Job is still running
                training_record.parameters.update({
                    'last_status_check': timezone.now().isoformat(),
                    'current_status': job_status
                })
                logger.info(f"Fine-tuning job status: {job_status}")
            
            training_record.save()
            
            return {
                'success': True,
                'job_id': job_id,
                'status': job_status,
                'fine_tuned_model': status_result.get('fine_tuned_model'),
                'trained_tokens': status_result.get('trained_tokens')
            }
            
        except Exception as e:
            logger.error(f"Error monitoring fine-tuning job: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_available_models(self) -> Dict[str, Any]:
        """
        Get list of available models (including fine-tuned ones)
        
        Returns:
            Dictionary containing available models
        """
        try:
            response = self.client.models.list()
            
            models = []
            for model in response.data:
                models.append({
                    'id': model.id,
                    'object': model.object,
                    'created': model.created,
                    'owned_by': model.owned_by
                })
            
            return {
                'success': True,
                'models': models
            }
            
        except Exception as e:
            logger.error(f"Error getting available models: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


class FineTuningManager:
    """
    High-level manager for fine-tuning operations
    """
    
    def __init__(self):
        self.service = GroqFineTuneService()
    
    def prepare_and_start_fine_tuning(self, training_file_path: str, model_name: str, 
                                    user_id: Optional[int] = None, 
                                    hyperparameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Prepare and start the fine-tuning process
        
        Args:
            training_file_path: Path to the training data file
            model_name: Name for the fine-tuned model
            user_id: Optional user ID who started the training
            hyperparameters: Optional hyperparameters for training
            
        Returns:
            Dictionary containing process results
        """
        from django.contrib.auth.models import User
        
        try:
            # Create training record
            user = User.objects.get(id=user_id) if user_id else None
            training_record = ChatbotTraining.objects.create(
                training_type='performance_tune',
                status='pending',
                parameters={
                    'model_name': model_name,
                    'training_file': training_file_path,
                    'hyperparameters': hyperparameters or {}
                },
                started_by=user
            )
            
            # Start fine-tuning process
            result = self.service.start_fine_tuning_process(
                training_file_path=training_file_path,
                model_name=model_name,
                training_record_id=str(training_record.id),
                hyperparameters=hyperparameters
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in prepare_and_start_fine_tuning: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_training_status(self, training_record_id: str) -> Dict[str, Any]:
        """
        Get the status of a training process
        
        Args:
            training_record_id: ID of the training record
            
        Returns:
            Dictionary containing training status
        """
        try:
            training_record = ChatbotTraining.objects.get(id=training_record_id)
            
            # If job is running, check current status
            if training_record.status == 'running' and 'job_id' in training_record.parameters:
                job_id = training_record.parameters['job_id']
                monitor_result = self.service.monitor_fine_tuning_job(job_id, training_record_id)
                
                if monitor_result['success']:
                    training_record.refresh_from_db()
            
            return {
                'success': True,
                'training_record_id': str(training_record.id),
                'status': training_record.status,
                'training_type': training_record.training_type,
                'parameters': training_record.parameters,
                'results': training_record.results,
                'error_log': training_record.error_log,
                'started_at': training_record.started_at,
                'completed_at': training_record.completed_at
            }
            
        except ChatbotTraining.DoesNotExist:
            return {
                'success': False,
                'error': 'Training record not found'
            }
        except Exception as e:
            logger.error(f"Error getting training status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


# Create a singleton instance
finetune_manager = FineTuningManager() 