import json
import logging
from pathlib import Path
from django.core.management.base import BaseCommand
from django.utils import timezone
from chatbot.models import TrainingDataset, KnowledgeBaseEntry

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Load new academic programs, qualifications, and SPM profiles data into the knowledge base'

    def add_arguments(self, parser):
        parser.add_argument('--programs-file', type=str, help='Path to academic programs JSONL file')
        parser.add_argument('--studymode-file', type=str, help='Path to study mode and accommodation JSONL file')
        parser.add_argument('--qualification-file', type=str, help='Path to qualification to programme mapping JSON file')
        parser.add_argument('--spm-profiles-file', type=str, help='Path to SPM profiles JSON file')
        parser.add_argument('--validate', action='store_true', help='Mark entries as validated')

    def handle(self, *args, **options):
        programs_file = options['programs_file']
        studymode_file = options['studymode_file']
        qualification_file = options['qualification_file']
        spm_profiles_file = options['spm_profiles_file']
        validate_entries = options['validate']

        try:
            # Create new dataset
            dataset = TrainingDataset.objects.create(
                name=f"Academic Programs and Qualifications Data {timezone.now().strftime('%Y%m%d')}",
                description="Updated program listings, qualifications, and SPM profiles information",
                dataset_type='programs',  # Using a valid choice from DATASET_TYPES
                file_path='multiple_files',  # Since we're loading from multiple files
                status='active'
            )
            self.stdout.write(f"Created new dataset: {dataset.name}")

            # Load program data
            if programs_file:
                self._load_programs(programs_file, dataset, validate_entries)

            # Load study mode and accommodation data
            if studymode_file:
                self._load_studymode_data(studymode_file, dataset, validate_entries)

            # Load qualification mapping data
            if qualification_file:
                self._load_qualification_data(qualification_file, dataset, validate_entries)

            # Load SPM profiles data
            if spm_profiles_file:
                self._load_spm_profiles(spm_profiles_file, dataset, validate_entries)

            self.stdout.write(self.style.SUCCESS('Successfully loaded new dataset'))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error loading dataset: {str(e)}'))
            logger.error(f"Dataset loading error: {str(e)}", exc_info=True)

    def _load_programs(self, file_path: str, dataset: TrainingDataset, validate: bool):
        """Load academic programs data"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    program_data = json.loads(line)
                    
                    # Create program entry
                    entry = KnowledgeBaseEntry(
                        dataset=dataset,
                        entry_type='program',
                        category=f"Programs - {program_data['level']}",
                        question=f"What is the {program_data['programme']}?",
                        answer=f"The {program_data['programme']} is a {program_data['level']} level program at APU.",
                        keywords=[program_data['level'].lower(), 'program', 'course'] + 
                                program_data['programme'].lower().split(),
                        metadata={
                            'level': program_data['level'],
                            'name': program_data['programme'],
                            'specialization': self._extract_specialization(program_data['programme']),
                        },
                        is_validated=validate
                    )
                    entry.save()
                    
            self.stdout.write(f"Loaded programs from {file_path}")
            
        except Exception as e:
            self.stderr.write(f"Error loading programs: {str(e)}")
            logger.error(f"Program loading error: {str(e)}", exc_info=True)

    def _load_studymode_data(self, file_path: str, dataset: TrainingDataset, validate: bool):
        """Load study mode and accommodation data"""
        try:
            # Read the entire file first
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split into lines and process each line
            lines = content.split('\n')
            current_json = ''
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # If line starts with {, it's a new JSON object
                if line.startswith('{'):
                    current_json = line
                    
                    # If line ends with }, it's a complete JSON object
                    if line.endswith('}'):
                        try:
                            data = json.loads(current_json)
                            self._process_data_entry(data, dataset, validate)
                        except json.JSONDecodeError:
                            continue
                        current_json = ''
                        
                # If we have a current_json and line ends with }, it completes the JSON object
                elif current_json and line.endswith('}'):
                    current_json += line
                    try:
                        data = json.loads(current_json)
                        self._process_data_entry(data, dataset, validate)
                    except json.JSONDecodeError:
                        continue
                    current_json = ''
                    
                # If we have a current_json, append this line
                elif current_json:
                    current_json += line
                    
            self.stdout.write(f"Loaded study mode and accommodation data from {file_path}")
            
        except Exception as e:
            self.stderr.write(f"Error loading study mode data: {str(e)}")
            logger.error(f"Study mode data loading error: {str(e)}", exc_info=True)

    def _process_data_entry(self, data: dict, dataset: TrainingDataset, validate: bool):
        """Process a single data entry"""
        try:
            # Process study mode information
            if 'section' in data and data['section'] == 'Study mode':
                entry = KnowledgeBaseEntry(
                    dataset=dataset,
                    entry_type='general',
                    category='Study Mode',
                    question=f"What are the study modes available at APU?",
                    answer=data['content'],
                    keywords=['study mode', 'full-time', 'part-time', 'online', 'odl'],
                    is_validated=validate
                )
                entry.save()
                
            # Process accommodation information
            elif 'location' in data and 'average_single_rent' in data:
                entry = KnowledgeBaseEntry(
                    dataset=dataset,
                    entry_type='accommodation',
                    category='Accommodation',
                    question=f"What accommodation is available at {data['location']}?",
                    answer=self._format_accommodation_answer(data),
                    keywords=['accommodation', 'housing', 'rent', data['location'].lower()],
                    metadata={
                        'location': data['location'],
                        'single_rent': self._parse_rent(data['average_single_rent']),
                        'sharing_rent': self._parse_rent(data.get('average_sharing_rent')),
                    },
                    is_validated=validate
                )
                entry.save()
                
        except Exception as e:
            logger.error(f"Error processing data entry: {str(e)}", exc_info=True)

    def _load_qualification_data(self, file_path: str, dataset: TrainingDataset, validate: bool):
        """Load qualification to programme mapping data"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                qualification_data = json.load(f)
                
                # Create a dictionary to group programs by qualification
                qual_to_programs = {}
                for entry in qualification_data:
                    qual = entry['QUALIFICATION']
                    prog = entry['PROGRAMME']
                    if qual not in qual_to_programs:
                        qual_to_programs[qual] = []
                    qual_to_programs[qual].append(prog)
                
                # Create entries for each qualification
                for qualification, programs in qual_to_programs.items():
                    entry = KnowledgeBaseEntry(
                        dataset=dataset,
                        entry_type='qualification',
                        category='Qualification Requirements',
                        question=f"What programs can I enter with {qualification}?",
                        answer=self._format_qualification_answer(qualification, programs),
                        keywords=['qualification', 'entry requirement', qualification.lower()] + 
                                [prog.lower() for prog in programs],
                        metadata={
                            'qualification': qualification,
                            'eligible_programs': programs
                        },
                        is_validated=validate
                    )
                    entry.save()
                    
            self.stdout.write(f"Loaded qualification mappings from {file_path}")
            
        except Exception as e:
            self.stderr.write(f"Error loading qualification data: {str(e)}")
            logger.error(f"Qualification data loading error: {str(e)}", exc_info=True)

    def _load_spm_profiles(self, file_path: str, dataset: TrainingDataset, validate: bool):
        """Load SPM profiles data"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                spm_data = json.load(f)
                
                for profile in spm_data:
                    # Create a dictionary of subject-grade pairs
                    grades = {}
                    subjects = profile.get('subjects', [])
                    grade_values = profile.get('grades', [])
                    
                    for subject, grade in zip(subjects, grade_values):
                        if grade:  # Only include non-null grades
                            grades[subject] = grade
                    
                    # Create SPM profile entry
                    entry = KnowledgeBaseEntry(
                        dataset=dataset,
                        entry_type='spm_profile',
                        category='SPM Profiles',
                        question=f"What programs are suitable for a student with these SPM results?",
                        answer=self._format_spm_profile_answer({'grades': grades}),
                        keywords=['spm', 'grades', 'profile'] + 
                                [f"{subject}:{grade}" for subject, grade in grades.items()],
                        metadata={
                            'student_id': profile.get('ID'),
                            'grades': grades,
                            'credit_count': profile.get('credit_count', 0)
                        },
                        is_validated=validate
                    )
                    entry.save()
                    
            self.stdout.write(f"Loaded SPM profiles from {file_path}")
            
        except Exception as e:
            self.stderr.write(f"Error loading SPM profiles: {str(e)}")
            logger.error(f"SPM profiles loading error: {str(e)}", exc_info=True)

    def _extract_specialization(self, program_name: str) -> str:
        """Extract specialization from program name if present"""
        if 'with' in program_name:
            return program_name.split('with')[-1].strip()
        return None

    def _parse_rent(self, rent_str: str) -> float:
        """Parse rent string to float"""
        if not rent_str or rent_str == 'null':
            return None
        return float(rent_str.replace('RM ', '').replace(',', ''))

    def _format_accommodation_answer(self, data: dict) -> str:
        """Format accommodation data into readable answer"""
        answer_parts = [f"Accommodation at {data['location']}:"]
        
        if data['average_single_rent']:
            answer_parts.append(f"Single room rent: {data['average_single_rent']}")
        if data['average_sharing_rent']:
            answer_parts.append(f"Shared room rent: {data['average_sharing_rent']}")
            
        return "\n".join(answer_parts) 

    def _format_qualification_answer(self, qualification: str, programs: list) -> str:
        """Format qualification data into readable answer"""
        if not programs:
            return f"There are currently no direct program mappings for {qualification}."
            
        answer = f"With {qualification}, you can apply for the following programs:\n"
        for program in programs:
            answer += f"- {program}\n"
        return answer

    def _format_spm_profile_answer(self, profile: dict) -> str:
        """Format SPM profile data into readable answer"""
        answer = "Based on your SPM results:\n"
        
        # Add grades if available
        if 'grades' in profile:
            for subject, grade in profile['grades'].items():
                answer += f"- {subject}: {grade}\n"
            
        return answer 