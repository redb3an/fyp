# No longer used, used load_new_dataset.py

import pandas as pd
import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from chatbot.models import TrainingDataset, KnowledgeBaseEntry
from django.utils import timezone


class Command(BaseCommand):
    help = 'Load university dataset from Excel file into knowledge base'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='Data 1.xlsx',
            help='Path to the Excel file (default: Data 1.xlsx)'
        )
        parser.add_argument(
            '--dataset-name',
            type=str,
            default='APU Programs Dataset',
            help='Name for the dataset (default: APU Programs Dataset)'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing knowledge entries before loading new data'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        dataset_name = options['dataset_name']
        clear_existing = options['clear_existing']
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise CommandError(f'File "{file_path}" does not exist.')
        
        self.stdout.write(f'Loading dataset from: {file_path}')
        
        try:
            # Read the Excel file
            df = pd.read_excel(file_path)
            self.stdout.write(f'Found {len(df)} rows in the dataset')
            self.stdout.write(f'Columns: {list(df.columns)}')
            
            # Get or create admin user for dataset creation
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
                    'dataset_type': 'programs',
                    'description': f'University programs dataset loaded from {file_path}',
                    'file_path': file_path,
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
            
            # Process each row and create knowledge entries
            created_entries = 0
            skipped_entries = 0
            
            for index, row in df.iterrows():
                try:
                    course_code = str(row.get('COURSE CODE', '')).strip()
                    programme = str(row.get('PROGRAMME', '')).strip()
                    faculty = str(row.get('FACULTY', '')).strip()
                    program_type = str(row.get('PROGRAM TYPE', '')).strip()
                    study_mode = str(row.get('STUDY MODE', '')).strip()
                    
                    # Skip rows with missing essential data
                    if not course_code or not programme or course_code == 'nan' or programme == 'nan':
                        skipped_entries += 1
                        continue
                    
                    # Create question and answer for this program
                    question = f"Tell me about the {programme} program"
                    answer = self._create_program_answer(course_code, programme, faculty, program_type, study_mode)
                    
                    # Generate keywords for better searchability
                    keywords = self._generate_keywords(course_code, programme, faculty, program_type, study_mode)
                    
                    # Create the knowledge entry
                    entry = KnowledgeBaseEntry.objects.create(
                        dataset=dataset,
                        entry_type='fact',
                        category=faculty or 'General',
                        question=question,
                        answer=answer,
                        keywords=keywords,
                        confidence_score=1.0,
                        is_validated=True
                    )
                    
                    created_entries += 1
                    
                    # Create additional entries for different query patterns
                    self._create_additional_entries(dataset, course_code, programme, faculty, program_type, study_mode)
                    created_entries += 2  # We create 2 additional entries per program
                    
                except Exception as e:
                    self.stdout.write(f'Error processing row {index}: {str(e)}')
                    skipped_entries += 1
                    continue
            
            # Update dataset usage
            dataset.increment_usage()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully loaded dataset!\n'
                    f'Created entries: {created_entries}\n'
                    f'Skipped entries: {skipped_entries}\n'
                    f'Dataset: {dataset.name} (ID: {dataset.id})'
                )
            )
            
        except Exception as e:
            raise CommandError(f'Error loading dataset: {str(e)}')
    
    def _create_program_answer(self, course_code, programme, faculty, program_type, study_mode):
        """Create a comprehensive answer about the program"""
        answer = f"The {programme} is offered by APU under the course code {course_code}."
        
        if faculty:
            faculty_full = self._get_faculty_full_name(faculty)
            answer += f" This program is offered by the {faculty_full}."
        
        if program_type:
            answer += f" It is a {program_type} program."
        
        if study_mode:
            if study_mode.lower() == 'fulltime':
                answer += " The program is offered in full-time mode."
            elif study_mode.lower() == 'part time':
                answer += " The program is offered in part-time mode."
            elif study_mode.lower() == 'distance learning':
                answer += " The program is offered through distance learning."
        
        answer += " For more details about admission requirements, fees, and course structure, please contact our admissions office."
        
        return answer
    
    def _get_faculty_full_name(self, faculty_code):
        """Convert faculty code to full name"""
        faculty_names = {
            'GSoB': 'Graduate School of Business',
            'SoC': 'School of Computing',
            'GSoT': 'Graduate School of Technology',
            'SoT': 'School of Technology',
            'SoE': 'School of Engineering',
            'SAF': 'School of Accounting & Finance',
            'SoMAQS': 'School of Management & Quantitative Studies',
            'SoB': 'School of Business',
            'SoMM': 'School of Media & Mass Communication',
            'SoMAD': 'School of Media Arts & Design',
            'SoP': 'School of Psychology',
            'SoF': 'School of Finance',
            'SGHT': 'School of Global Hospitality & Tourism',
            'ACD': 'Academic Development',
            'APLC': 'APU Language Centre',
            'SoA': 'School of Architecture'
        }
        return faculty_names.get(faculty_code, faculty_code)
    
    def _generate_keywords(self, course_code, programme, faculty, program_type, study_mode):
        """Generate keywords for better search"""
        keywords = [course_code.lower()]
        
        # Add program name words
        prog_words = programme.lower().split()
        keywords.extend([word for word in prog_words if len(word) > 2])
        
        # Add faculty
        if faculty:
            keywords.append(faculty.lower())
            faculty_full = self._get_faculty_full_name(faculty).lower()
            keywords.extend(faculty_full.split())
        
        # Add program type
        if program_type:
            keywords.extend(program_type.lower().split())
        
        # Add study mode
        if study_mode:
            keywords.extend(study_mode.lower().split())
        
        # Add common search terms
        keywords.extend(['program', 'course', 'degree', 'study', 'apu', 'asia pacific university'])
        
        # Remove duplicates and short words
        keywords = list(set([kw for kw in keywords if len(kw) > 1]))
        
        return keywords
    
    def _create_additional_entries(self, dataset, course_code, programme, faculty, program_type, study_mode):
        """Create additional knowledge entries for different query patterns"""
        
        # Entry for course code queries
        if course_code:
            KnowledgeBaseEntry.objects.create(
                dataset=dataset,
                entry_type='fact',
                category='Course Codes',
                question=f"What is {course_code}?",
                answer=f"{course_code} is the course code for {programme} at APU. " + 
                       self._create_program_answer(course_code, programme, faculty, program_type, study_mode),
                keywords=[course_code.lower(), 'course code'] + self._generate_keywords(course_code, programme, faculty, program_type, study_mode),
                confidence_score=1.0,
                is_validated=True
            )
        
        # Entry for faculty queries
        if faculty:
            faculty_full = self._get_faculty_full_name(faculty)
            KnowledgeBaseEntry.objects.create(
                dataset=dataset,
                entry_type='fact',
                category=faculty,
                question=f"What programs does {faculty_full} offer?",
                answer=f"The {faculty_full} ({faculty}) offers the {programme} program among others. " +
                       f"This is a {program_type} program available in {study_mode} mode.",
                keywords=[faculty.lower(), faculty_full.lower()] + self._generate_keywords(course_code, programme, faculty, program_type, study_mode),
                confidence_score=0.9,
                is_validated=True
            ) 