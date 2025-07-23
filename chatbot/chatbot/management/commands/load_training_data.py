import json
import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from chatbot.models import TrainingDataset, KnowledgeBaseEntry
from django.utils import timezone


class Command(BaseCommand):
    help = 'Load prepared training data into knowledge base for enhanced RAG'

    def add_arguments(self, parser):
        parser.add_argument(
            '--training-file',
            type=str,
            default='groq_finetune_data/apu-counselor-v1_training_data.jsonl',
            help='Path to the training data file (JSONL format)'
        )
        parser.add_argument(
            '--dataset-name',
            type=str,
            default='Enhanced Training Dataset',
            help='Name for the dataset'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing knowledge entries before loading'
        )

    def handle(self, *args, **options):
        training_file = options['training_file']
        dataset_name = options['dataset_name']
        clear_existing = options['clear_existing']
        
        if not os.path.exists(training_file):
            raise CommandError(f'Training file not found: {training_file}')
        
        self.stdout.write(f'Loading training data from: {training_file}')
        
        try:
            # Get or create admin user
            admin_user, created = User.objects.get_or_create(
                username='admin',
                defaults={
                    'email': 'admin@apu.edu.my',
                    'first_name': 'System',
                    'last_name': 'Administrator',
                    'is_staff': True,
                    'is_superuser': True
                }
            )
            
            # Create or get the training dataset
            dataset, created = TrainingDataset.objects.get_or_create(
                name=dataset_name,
                defaults={
                    'dataset_type': 'general',
                    'description': f'Enhanced training dataset loaded from {training_file}',
                    'file_path': training_file,
                    'created_by': admin_user,
                    'status': 'active'
                }
            )
            
            if created:
                self.stdout.write(f'Created new dataset: {dataset_name}')
            else:
                self.stdout.write(f'Using existing dataset: {dataset_name}')
                dataset.updated_at = timezone.now()
                dataset.save()
            
            # Clear existing entries if requested
            if clear_existing:
                deleted_count = KnowledgeBaseEntry.objects.filter(dataset=dataset).count()
                KnowledgeBaseEntry.objects.filter(dataset=dataset).delete()
                self.stdout.write(f'Cleared {deleted_count} existing knowledge entries')
            
            # Load training data
            loaded_entries = 0
            skipped_entries = 0
            
            with open(training_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        data = json.loads(line.strip())
                        
                        # Extract question and answer from messages
                        messages = data.get('messages', [])
                        if len(messages) < 2:
                            skipped_entries += 1
                            continue
                        
                        user_message = None
                        assistant_message = None
                        
                        for msg in messages:
                            if msg.get('role') == 'user':
                                user_message = msg.get('content', '')
                            elif msg.get('role') == 'assistant':
                                assistant_message = msg.get('content', '')
                        
                        if not user_message or not assistant_message:
                            skipped_entries += 1
                            continue
                        
                        # Determine category from content
                        category = self._determine_category(user_message, assistant_message)
                        
                        # Generate keywords
                        keywords = self._generate_keywords(user_message, assistant_message)
                        
                        # Create knowledge entry
                        entry = KnowledgeBaseEntry.objects.create(
                            dataset=dataset,
                            entry_type='qa',
                            category=category,
                            question=user_message,
                            answer=assistant_message,
                            keywords=keywords,
                            confidence_score=1.0,
                            is_validated=True
                        )
                        
                        loaded_entries += 1
                        
                        if loaded_entries % 100 == 0:
                            self.stdout.write(f'Loaded {loaded_entries} entries...')
                        
                    except json.JSONDecodeError:
                        self.stdout.write(f'Warning: Invalid JSON at line {line_num}')
                        skipped_entries += 1
                        continue
                    except Exception as e:
                        self.stdout.write(f'Error processing line {line_num}: {str(e)}')
                        skipped_entries += 1
                        continue
            
            # Update dataset usage
            dataset.increment_usage()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully loaded training data!\n'
                    f'Loaded entries: {loaded_entries}\n'
                    f'Skipped entries: {skipped_entries}\n'
                    f'Dataset: {dataset.name} (ID: {dataset.id})'
                )
            )
            
        except Exception as e:
            raise CommandError(f'Error loading training data: {str(e)}')

    def _determine_category(self, question, answer):
        """Determine category from question and answer content"""
        question_lower = question.lower()
        answer_lower = answer.lower()
        
        # Check for specific categories
        if any(word in question_lower for word in ['fee', 'cost', 'price', 'tuition', 'scholarship']):
            return 'Fees and Financial Aid'
        elif any(word in question_lower for word in ['admission', 'requirement', 'apply', 'entry']):
            return 'Admissions'
        elif any(word in question_lower for word in ['program', 'course', 'degree', 'diploma']):
            return 'Programs and Courses'
        elif any(word in question_lower for word in ['module', 'curriculum', 'subject']):
            return 'Curriculum and Modules'
        elif any(word in question_lower for word in ['facility', 'campus', 'lab', 'library']):
            return 'Campus and Facilities'
        elif any(word in question_lower for word in ['student life', 'club', 'society', 'activity']):
            return 'Student Life'
        elif any(word in answer_lower for word in ['school of computing', 'computer science', 'computing']):
            return 'School of Computing'
        elif any(word in answer_lower for word in ['school of business', 'business', 'management']):
            return 'School of Business'
        elif any(word in answer_lower for word in ['school of engineering', 'engineering']):
            return 'School of Engineering'
        elif any(word in answer_lower for word in ['accounting', 'finance']):
            return 'School of Accounting & Finance'
        else:
            return 'General Information'

    def _generate_keywords(self, question, answer):
        """Generate keywords from question and answer"""
        import re
        
        # Combine question and answer
        text = f"{question} {answer}".lower()
        
        # Extract meaningful words (remove common words)
        stop_words = {'the', 'is', 'are', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'this', 'that', 'these', 'those', 'what', 'how', 'why', 'when', 'where', 'who', 'which'}
        
        # Extract words
        words = re.findall(r'\b[a-z]{3,}\b', text)
        keywords = [word for word in words if word not in stop_words]
        
        # Remove duplicates and limit to 20 keywords
        unique_keywords = list(dict.fromkeys(keywords))[:20]
        
        return unique_keywords 