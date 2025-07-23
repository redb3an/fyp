import pandas as pd
import json
import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from chatbot.models import TrainingDataset, KnowledgeBaseEntry, ChatbotTraining
from django.utils import timezone
from django.conf import settings


class Command(BaseCommand):
    help = 'Fine-tune Groq model with APU programs, academic info, and module data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--excel-file',
            type=str,
            default='Data 1.xlsx',
            help='Path to the Excel file with programs (default: Data 1.xlsx)'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='groq_finetune_data',
            help='Directory to save fine-tuning datasets (default: groq_finetune_data)'
        )
        parser.add_argument(
            '--model-name',
            type=str,
            default='apu-educational-counselor',
            help='Name for the fine-tuned model (default: apu-educational-counselor)'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing knowledge entries before processing'
        )

    def handle(self, *args, **options):
        self.excel_file = options['excel_file']
        self.output_dir = options['output_dir']
        self.model_name = options['model_name']
        self.clear_existing = options['clear_existing']
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.stdout.write(f'Starting fine-tuning data preparation for: {self.model_name}')
        
        # Prepare all training data
        training_data = []
        
        # Process Excel data (Programs and Courses)
        self.stdout.write('Processing Excel data...')
        excel_data = self._process_excel_data()
        training_data.extend(excel_data)
        
        # Process JSONL academic information
        self.stdout.write('Processing academic information...')
        jsonl_data = self._process_academic_jsonl()
        training_data.extend(jsonl_data)
        
        # Process module lists
        self.stdout.write('Processing module lists...')
        module_data = self._process_module_lists()
        training_data.extend(module_data)
        
        # Save training data to JSONL format for Groq
        output_file = os.path.join(self.output_dir, f'{self.model_name}_training_data.jsonl')
        self._save_training_data(training_data, output_file)
        
        # Create training dataset record
        self._create_training_record(training_data, output_file)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Fine-tuning data prepared successfully!\n'
                f'Total training examples: {len(training_data)}\n'
                f'Output file: {output_file}\n'
                f'Model name: {self.model_name}'
            )
        )

    def _process_excel_data(self):
        """Process Excel file to extract programs and courses information"""
        if not os.path.exists(self.excel_file):
            raise CommandError(f'Excel file "{self.excel_file}" not found')
        
        try:
            # Read first sheet of Excel file
            df = pd.read_excel(self.excel_file, sheet_name=0)
            self.stdout.write(f'Found {len(df)} programs in Excel file')
            
            training_examples = []
            
            for index, row in df.iterrows():
                try:
                    course_code = str(row.get('COURSE CODE', '')).strip()
                    programme = str(row.get('PROGRAMME', '')).strip()
                    faculty = str(row.get('FACULTY', '')).strip()
                    program_type = str(row.get('PROGRAM TYPE', '')).strip()
                    study_mode = str(row.get('STUDY MODE', '')).strip()
                    
                    # Skip rows with missing data
                    if not course_code or not programme or course_code == 'nan' or programme == 'nan':
                        continue
                    
                    # Generate multiple training examples for each program
                    examples = self._generate_program_examples(course_code, programme, faculty, program_type, study_mode)
                    training_examples.extend(examples)
                    
                except Exception as e:
                    self.stdout.write(f'Error processing row {index}: {str(e)}')
                    continue
            
            self.stdout.write(f'Generated {len(training_examples)} training examples from Excel data')
            return training_examples
            
        except Exception as e:
            raise CommandError(f'Error processing Excel file: {str(e)}')

    def _generate_program_examples(self, course_code, programme, faculty, program_type, study_mode):
        """Generate multiple training examples for a program"""
        examples = []
        
        # Get faculty full name
        faculty_full = self._get_faculty_full_name(faculty)
        
        # Base program information
        program_info = {
            'course_code': course_code,
            'programme': programme,
            'faculty': faculty_full,
            'program_type': program_type,
            'study_mode': study_mode
        }
        
        # Example 1: Direct program inquiry
        examples.append({
            "messages": [
                {"role": "user", "content": f"Tell me about the {programme} program"},
                {"role": "assistant", "content": self._create_program_response(program_info)}
            ]
        })
        
        # Example 2: Course code inquiry
        examples.append({
            "messages": [
                {"role": "user", "content": f"What is {course_code}?"},
                {"role": "assistant", "content": self._create_course_code_response(program_info)}
            ]
        })
        
        # Example 3: Faculty-based inquiry
        if faculty_full:
            examples.append({
                "messages": [
                    {"role": "user", "content": f"What programs are offered by {faculty_full}?"},
                    {"role": "assistant", "content": self._create_faculty_response(program_info)}
                ]
            })
        
        # Example 4: Program type inquiry
        if program_type:
            examples.append({
                "messages": [
                    {"role": "user", "content": f"What {program_type} programs does APU offer?"},
                    {"role": "assistant", "content": self._create_program_type_response(program_info)}
                ]
            })
        
        return examples

    def _process_academic_jsonl(self):
        """Process the academic information in JSONL format"""
        academic_data = [
            {"section": "2025 Fees (Malaysian & International)", "content": "In 2025, APU's tuition fees for Malaysian students are approximately: RM19,600 for Certificate courses; RM27,200 for Foundation programs; RM46,000–50,000 for Diploma programs; RM97,400–119,600 for Undergraduate degree courses; and RM26,000–45,800 for Postgraduate (Master's or PhD) programmes:contentReference[oaicite:0]{index=0}:contentReference[oaicite:1]{index=1}. International students pay additional charges on top of the domestic fees, ranging roughly from RM1,000 up to RM20,000 extra depending on the course:contentReference[oaicite:2]{index=2}. For example, a Certificate program costs about RM19,600 for local students, whereas international students pay around RM21,200 in total:contentReference[oaicite:3]{index=3}:contentReference[oaicite:4]{index=4}. *(Fees are subject to change; refer to APU's official sources for the most up-to-date figures.)*"},
            {"section": "Study Durations by Programme Level", "content": "APU's programme durations vary by level of study. Certificate programmes typically take about 1 year 4 months (approximately 16 months) to complete:contentReference[oaicite:5]{index=5}:contentReference[oaicite:6]{index=6}. Foundation programmes are 1 year (12 months) long:contentReference[oaicite:7]{index=7}. Diploma programmes generally require 2 years of full-time study:contentReference[oaicite:8]{index=8}. Most Bachelor's (Honours) degree programmes span 3 years, except for Engineering degrees which run 4 years to meet professional requirements:contentReference[oaicite:9]{index=9}:contentReference[oaicite:10]{index=10}. Master's degree courses usually take 1 year of full-time study to finish:contentReference[oaicite:11]{index=11}, while PhD programmes are typically at least 3 years in duration (full-time):contentReference[oaicite:12]{index=12}:contentReference[oaicite:13]{index=13}."},
            {"section": "Admission Requirements – Certificate Programs", "content": "For admission into APU's Certificate courses (e.g. Certificate in Administrative Skills), the minimum requirement is **1 Credit in SPM** (with at least a pass in Bahasa Malaysia and Sejarah):contentReference[oaicite:14]{index=14}. Equivalent qualifications are also accepted – for instance, **1 O-Level/IGCSE credit (grade C and above)** or **1 UEC credit (grade B and above):contentReference[oaicite:15]{index=15}**. These certificate programs are designed for students who have at least one credit from secondary school, providing a pathway into diploma studies."},
            {"section": "Admission Requirements – Foundation Programs", "content": "Entry into APU's Foundation programs requires a minimum of **5 Credits at SPM** level (in 5 different subjects) including any specified key subjects, with a pass in Bahasa Malaysia and Sejarah:contentReference[oaicite:16]{index=16}. Similarly, **5 credits in O-Levels/IGCSE** or **5 Bs in UEC** are accepted as equivalent. Different foundation pathways (e.g. Engineering, Computing, Business routes) may have particular subject requirements (for example, the Engineering route typically requires credits in Mathematics and a science subject):contentReference[oaicite:17]{index=17}:contentReference[oaicite:18]{index=18}."},
            {"section": "Admission Requirements – Diploma Programs", "content": "For APU's Diploma courses, students generally need at least **3 Credits in SPM** (in three different subjects) with a pass in Bahasa Malaysia and Sejarah:contentReference[oaicite:19]{index=19}. Equivalent qualifications like **3 O-Level/IGCSE credits** or an appropriate certificate (e.g. a relevant certificate from a recognized institution) are also considered. These requirements ensure that diploma entrants have a sufficient secondary education foundation in key subjects before pursuing the 2-year specialized diploma curriculum."},
            {"section": "Admission Requirements – Undergraduate Degrees", "content": "Admission into APU's Bachelor's degree programs typically requires a recognized pre-university qualification. For example, students can qualify with **2 Passes in STPM** (Malaysia's Form 6) or **2 A-Level passes**, or with a **Matriculation/Foundation certificate (CGPA ≥ 2.0)**:contentReference[oaicite:20]{index=20}:contentReference[oaicite:21]{index=21}. A relevant **Diploma (Level 4 MQF) with CGPA ≥ 2.0** also provides entry into degree programs (often into Year 2). UEC students need at least **5 Grade B passes** in the UEC Senior Middle III examination to enter undergraduate courses:contentReference[oaicite:22]{index=22}. Note that specific programs may impose additional requirements – for instance, computing and engineering degrees expect credits in Mathematics and/or science subjects at SPM/O-Level:contentReference[oaicite:23]{index=23}. International qualifications are assessed based on equivalence to these standards as set by the Malaysian Qualifications Agency."},
            {"section": "Admission Requirements – Postgraduate (Masters & PhD)", "content": "For admission into APU's **Master's degree** programs, the general requirement is a relevant **Bachelor's degree** (usually with a minimum CGPA as specified by the program, often around 2.50 or higher on a 4.00 scale):contentReference[oaicite:24]{index=24}:contentReference[oaicite:25]{index=25}. Some Master's programmes may require the prior degree to be in a related field of study, and applicants with lower CGPA might be considered on a case-by-case basis if they have sufficient professional experience. Entry into a **Ph.D. (Doctoral)** program requires a **Master's degree** in a related discipline; occasionally, candidates with only a Bachelor's (Honours) degree but excellent academic standing can be considered for direct PhD admission, subject to strict conditions and approval. All postgraduate applicants must also meet any specific program prerequisites and the university's English language requirements."},
            {"section": "Common vs. Specialised Modules in Programmes", "content": "APU's academic programs are structured with a combination of common core modules and specialised modules. **Common modules** cover fundamental knowledge and skills that all students in the programme or faculty must learn, laying the groundwork in areas such as computing, business, or engineering basics:contentReference[oaicite:26]{index=26}. **Specialised modules**, on the other hand, dive deeper into the specific field or specialisation that a student chooses, providing focused expertise (e.g. cybersecurity, data science, marketing, etc.):contentReference[oaicite:27]{index=27}:contentReference[oaicite:28]{index=28}. For example, in the B.Sc. Computer Science degree, Year 1 includes common modules like *Introduction to Networking*, *Systems Analysis and Design*, and *Introduction to Databases*, alongside specialised modules like *Introduction to Artificial Intelligence* and *C Programming* which are specific to the computer science domain:contentReference[oaicite:29]{index=29}:contentReference[oaicite:30]{index=30}. As students progress to Year 2 and 3, they continue to take some common modules (such as innovation and research methods) and a larger number of specialised modules aligned with their chosen specialism:contentReference[oaicite:31]{index=31}:contentReference[oaicite:32]{index=32}."},
            {"section": "Scholarships and Financial Aid", "content": "APU offers various scholarships and financial aid options to help students fund their studies. Notably, the **APU Merit Scholarships** provide tuition fee waivers based on academic excellence – high achievers can earn substantial awards, even up to a 100% tuition fee waiver for the most outstanding students:contentReference[oaicite:33]{index=33}. There are also scholarships targeted at specific student groups, such as **SPM Scholarships** and **UEC Scholarships** for top-performing Malaysian students in those examinations:contentReference[oaicite:34]{index=34}. In addition, APU facilitates **student loans** (for Malaysian students, e.g. PTPTN loans) and may offer other bursaries or discounts (for example, alumni or sibling discounts). Prospective students are encouraged to apply for scholarships during the admission process, and eligibility is generally determined by academic results, extracurricular achievements, and in some cases socio-economic background."},
            {"section": "Campus Facilities", "content": "Asia Pacific University is equipped with modern, world-class facilities at its campus to enrich student learning and campus life. There are extensive teaching and learning amenities, including state-of-the-art **computer labs** and specialized **engineering laboratories**, where students work with the latest software, hardware and equipment relevant to their disciplines:contentReference[oaicite:35]{index=35}:contentReference[oaicite:36]{index=36}. The campus houses unique facilities like an on-site **Financial Trading Centre** simulating a real trading floor, a fully-functional **Cyber Security Talent Zone** (with an industry-grade Security Operations Centre and Cyber Range for cyber-defense simulations):contentReference[oaicite:37]{index=37}:contentReference[oaicite:38]{index=38}, and a dedicated **Psychology Centre** with labs for experiments and therapy sessions:contentReference[oaicite:39]{index=39}. For creative students, APU also features an advanced **XR Studio** with volumetric video capture and AR/VR development tools – the first of its kind in the region:contentReference[oaicite:40]{index=40}:contentReference[oaicite:41]{index=41}. On the recreational side, the campus provides a range of **sports and recreational facilities**: there is a large multipurpose sports ground (for football, rugby, etc.), basketball courts, and a forthcoming swimming pool on campus:contentReference[oaicite:42]{index=42}:contentReference[oaicite:43]{index=43}. Students additionally have access to the nearby National Sports Complex facilities (for sports like swimming, hockey, squash and more) and can unwind in the on-campus **students' lounge** and cafeteria spaces:contentReference[oaicite:44]{index=44}:contentReference[oaicite:45]{index=45}."},
            {"section": "Student Life, Clubs and Societies", "content": "Student life at APU is vibrant and multicultural, with a community of over 13,000 students from more than 130 countries around the world:contentReference[oaicite:46]{index=46}:contentReference[oaicite:47]{index=47}. There are **over 60 clubs and societies** active on campus, spanning academic, cultural, athletic, and special interest groups, which means there are plenty of events, activities, trips and projects happening throughout the year:contentReference[oaicite:48]{index=48}. Students are encouraged to take part in these co-curricular activities – they can join existing clubs or even start new ones, participate in competitions, or be elected to the Students' Representative Council to develop leadership skills. APU also runs a **Student Ambassador** program, where students assist in university events and gain professional experience working with people from diverse cultures:contentReference[oaicite:49]{index=49}. Overall, APU's campus environment is lively and supportive: learning extends beyond the classroom through industry exposure, intercultural activities, sports and workshops, ensuring students have a rewarding and holistic university experience."}
        ]
        
        training_examples = []
        
        for item in academic_data:
            section = item['section']
            content = item['content']
            
            # Clean content by removing contentReference citations
            clean_content = self._clean_content(content)
            
            # Generate training examples for this section
            examples = self._generate_academic_examples(section, clean_content)
            training_examples.extend(examples)
        
        self.stdout.write(f'Generated {len(training_examples)} training examples from academic data')
        return training_examples

    def _process_module_lists(self):
        """Process module lists by study area"""
        module_data = {
            "Accounting and Finance": {
                "coreModules": [
                    "Quantitative Skills", "Introduction to Management", "Business and Communication Skills", "Financial Accounting 1",
                    "Accounting Information System", "Business Economics", "Financial Accounting 2", "SAP ERP System in Accounting",
                    "Business Law", "Marketing", "Fundamentals of Entrepreneurship", "Advanced Financial Accounting & Reporting",
                    "Taxation", "Management Accounting", "Auditing and Assurance", "Emerging Technologies for Accounting and Finance",
                    "Financial Management", "Corporate Governance and Risk Management", "Advanced Corporate Reporting",
                    "Data Analytics in Accounting and Finance", "Company Law", "Performance Management", "Advanced Auditing",
                    "Research Methodology in Accounting and Finance", "Corporate Finance", "Advanced Taxation",
                    "Strategy, Sustainability & Leadership", "Advanced Performance Management", "Reflective Practice in Accounting & Finance",
                    "Seminar in Accounting & Finance", "Specialised Accounting", "Accounting & Finance Research Project"
                ],
                "specializedModules": [
                    "Forensic Accounting", "Accounting Theory and Emerging Issues", "Public Sector Accounting", "Robo Auditing & Analytics"
                ]
            },
            "Actuarial Studies": {
                "coreModules": [
                    "Probability Models", "Linear Algebra", "Business and Communication Skills", "Calculus", "Calculus II",
                    "Financial Accounting", "Microeconomics", "Macroeconomics", "Introduction to R Programming", "Statistics",
                    "Advanced Probability Models", "Predictive Analytics", "Financial Mathematics", "Regression Analysis",
                    "Financial Economics", "Business Research Methods", "Financial Management", "Business Ethics & Governance",
                    "Mathematics of Financial Derivatives", "Stochastic Processes", "Asset and Liability Valuations",
                    "Life Contingencies", "Corporate Finance", "Risk Theory", "Investigation in Actuarial Studies",
                    "Option and Bond Valuations", "Survival Analysis", "Life Contingencies 2", "Project in Actuarial Studies"
                ],
                "specializedModules": [
                    "Programming for Data Analytics", "Operational Research and Analytics", "Behavioural Science & Marketing Analytics",
                    "Advanced Predictive Analytics"
                ]
            },
            "Architecture": {
                "coreModules": [
                    "Architectural Design Studio 1", "Architectural Representation", "Architectural History and Theory",
                    "Architectural Design Studio 2", "Construction Technology", "Digital Architecture", "Architectural Design Studio 3",
                    "Integrated Technology", "Critical and Cultural Studies", "Architectural Design Studio 4", "Environment and Behaviour",
                    "Energy and Building", "Architectural Design Studio 5", "Contextualising Architectural Humanities",
                    "Innovation in Construction Practice", "Architectural Design Studio 6: Design Synthesis and Resolution",
                    "Critical Building Analysis", "Professional Practice"
                ],
                "specializedModules": []
            },
            "Computing and Technology": {
                "coreModules": [
                    "Introduction to Networking", "Systems Software and Computing Concepts", "Introduction to Databases",
                    "Python Programming", "Systems Analysis and Design", "Integrated Computer Systems", "Fundamentals of Entrepreneurship",
                    "Innovation Process", "Research Methods for Computing and Technology", "Project Management", "Venture Building"
                ],
                "specializedModules": [
                    "Digital Thinking and Innovation", "Mathematical Concepts for Computing", "Introduction to Artificial Intelligence",
                    "Introduction to C Programming", "Systems and Network Administration", "System Development Methods",
                    "Object Oriented Development with Java", "Web Applications", "Concurrent Programming",
                    "Computer Systems Low Level Technique", "Data Structures", "Investigations in Computer Science",
                    "Algorithmics", "User Experience", "Advanced Database Systems", "Project in Computer Science"
                ]
            },
            "Business and Management": {
                "coreModules": [
                    "Introduction to Management", "Digital Thinking and Innovation", "Quantitative Skills", "Business and Communications Skills",
                    "Business Economics", "People Management", "Accounting Skills", "Marketing", "Business Law",
                    "Fundamentals of Entrepreneurship", "Behavioural Science in Organisation", "Innovation Process",
                    "Business Ethics and Governance", "Business Research Methods", "Delivering Customer Value",
                    "Enterprise Resource Planning with SAP Platform", "Strategic Management", "Leadership Theory and Practice",
                    "Venture Building"
                ],
                "specializedModules": [
                    "Operations Management", "E-Business Management", "Critical Thinking in Management", "Employee Development",
                    "International Culture and Communications", "Managing People and Performance", "Managing Change",
                    "Asian Economics", "Investigation in Business Management", "Contemporary Management", "Global Marketing",
                    "Business Management Project"
                ]
            },
            "Engineering": {
                "coreModules": [
                    "Instrumentation & Measurement", "Engineering Materials", "Programming with Python", "Engineering Mathematics 1",
                    "Introduction to C Programming", "Engineering Mathematics 2", "Analysis of Circuits", "Fundamentals of Entrepreneurship",
                    "Digital Electronics", "Introduction to Electrical Systems", "Engineering Mathematics 3", "Engineering Software & Applications",
                    "Innovation Process", "Analogue Electronics", "Electromagnetic Field Theory", "Signals & Linear Systems",
                    "Control Engineering", "Engineering Mathematics 4", "Communication Engineering Principles", "Venture Building",
                    "Microprocessor Systems & Embedded Software", "Digital Signal Processing", "Engineering Project Management",
                    "Project Phase 1 (Investigation)", "Group Design Project 1", "Project Phase 2 (Implementation)",
                    "Engineer in Society", "Group Design Project 2"
                ],
                "specializedModules": [
                    "Introduction to Networking", "Human Computer Interaction", "Object Oriented Development with Java",
                    "Fundamentals of Integrated Circuits Design", "Modern Communication Systems", "VLSI Design",
                    "Analogue Integrated Circuits & Systems", "Computer Systems Security", "User Experience"
                ]
            }
        }
        
        training_examples = []
        
        for study_area, modules in module_data.items():
            examples = self._generate_module_examples(study_area, modules)
            training_examples.extend(examples)
        
        self.stdout.write(f'Generated {len(training_examples)} training examples from module data')
        return training_examples

    def _generate_module_examples(self, study_area, modules):
        """Generate training examples for module information"""
        examples = []
        
        core_modules = modules.get('coreModules', [])
        specialized_modules = modules.get('specializedModules', [])
        
        # Example 1: Core modules inquiry
        if core_modules:
            examples.append({
                "messages": [
                    {"role": "user", "content": f"What are the core modules in {study_area}?"},
                    {"role": "assistant", "content": self._create_core_modules_response(study_area, core_modules)}
                ]
            })
        
        # Example 2: Specialized modules inquiry
        if specialized_modules:
            examples.append({
                "messages": [
                    {"role": "user", "content": f"What specialized modules are available in {study_area}?"},
                    {"role": "assistant", "content": self._create_specialized_modules_response(study_area, specialized_modules)}
                ]
            })
        
        # Example 3: General curriculum inquiry
        examples.append({
            "messages": [
                {"role": "user", "content": f"Tell me about the curriculum structure for {study_area}"},
                {"role": "assistant", "content": self._create_curriculum_response(study_area, core_modules, specialized_modules)}
            ]
        })
        
        return examples

    def _create_core_modules_response(self, study_area, core_modules):
        """Create response for core modules inquiry"""
        response = f"The core modules for {study_area} at APU include:\n\n"
        for i, module in enumerate(core_modules[:10], 1):  # Show first 10 modules
            response += f"{i}. {module}\n"
        
        if len(core_modules) > 10:
            response += f"\n...and {len(core_modules) - 10} more modules. "
        
        response += f"\n\nThese core modules provide the fundamental knowledge and skills required for {study_area}. They cover essential concepts that all students in this field must master."
        
        return response

    def _create_specialized_modules_response(self, study_area, specialized_modules):
        """Create response for specialized modules inquiry"""
        if not specialized_modules:
            return f"The {study_area} program focuses primarily on core modules with integrated specialization throughout the curriculum."
        
        response = f"The specialized modules for {study_area} at APU include:\n\n"
        for i, module in enumerate(specialized_modules, 1):
            response += f"{i}. {module}\n"
        
        response += f"\n\nThese specialized modules allow students to develop expertise in specific areas within {study_area}, preparing them for advanced roles in their chosen field."
        
        return response

    def _create_curriculum_response(self, study_area, core_modules, specialized_modules):
        """Create comprehensive curriculum response"""
        response = f"The {study_area} program at APU is structured with a combination of core and specialized modules:\n\n"
        
        response += f"**Core Modules ({len(core_modules)} modules):**\n"
        response += "These provide fundamental knowledge and skills essential for the field.\n\n"
        
        if specialized_modules:
            response += f"**Specialized Modules ({len(specialized_modules)} modules):**\n"
            response += "These allow students to develop expertise in specific areas of interest.\n\n"
        
        response += f"The curriculum is designed to provide both breadth and depth, ensuring students graduate with comprehensive knowledge in {study_area} while also developing specialized skills that make them competitive in the job market."
        
        return response

    def _generate_academic_examples(self, section, content):
        """Generate training examples for academic information"""
        examples = []
        
        # Map sections to common question patterns
        question_patterns = {
            "2025 Fees": [
                "What are the tuition fees at APU?",
                "How much does it cost to study at APU?",
                "Tell me about APU's fees for 2025"
            ],
            "Study Durations": [
                "How long do programs take at APU?",
                "What is the duration of courses at APU?",
                "How many years is a degree at APU?"
            ],
            "Admission Requirements": [
                "What are the admission requirements for APU?",
                "How can I apply to APU?",
                "What qualifications do I need for APU?"
            ],
            "Scholarships": [
                "Does APU offer scholarships?",
                "What financial aid is available at APU?",
                "How can I get a scholarship at APU?"
            ],
            "Campus Facilities": [
                "What facilities does APU have?",
                "Tell me about APU's campus",
                "What can I expect from APU's facilities?"
            ],
            "Student Life": [
                "What is student life like at APU?",
                "What activities are available at APU?",
                "Tell me about clubs and societies at APU"
            ]
        }
        
        # Find matching patterns
        for pattern_key, questions in question_patterns.items():
            if pattern_key.lower() in section.lower():
                for question in questions:
                    examples.append({
                        "messages": [
                            {"role": "user", "content": question},
                            {"role": "assistant", "content": content}
                        ]
                    })
                break
        
        return examples

    def _clean_content(self, content):
        """Clean content by removing citations and formatting"""
        import re
        # Remove contentReference citations
        content = re.sub(r':contentReference\[oaicite:\d+\]\{index=\d+\}', '', content)
        # Clean up extra spaces
        content = re.sub(r'\s+', ' ', content).strip()
        return content

    def _create_program_response(self, program_info):
        """Create comprehensive program response"""
        response = f"The {program_info['programme']} (Course Code: {program_info['course_code']}) is offered by APU's {program_info['faculty']}. "
        
        if program_info['program_type']:
            response += f"This is a {program_info['program_type']} program "
        
        if program_info['study_mode']:
            mode_text = program_info['study_mode'].lower()
            if mode_text == 'fulltime':
                response += "offered in full-time mode. "
            elif mode_text == 'part time':
                response += "offered in part-time mode. "
        
        response += "APU is known for its industry-focused curriculum, strong partnerships with leading companies, and excellent graduate employment rates. For specific admission requirements, fees, and detailed course structure, I recommend contacting our admissions office."
        
        return response

    def _create_course_code_response(self, program_info):
        """Create course code specific response"""
        return f"{program_info['course_code']} is the course code for {program_info['programme']}, offered by APU's {program_info['faculty']}. This program is designed to provide students with comprehensive knowledge and practical skills in their chosen field."

    def _create_faculty_response(self, program_info):
        """Create faculty-specific response"""
        return f"{program_info['faculty']} offers various programs including {program_info['programme']} ({program_info['course_code']}). Our faculty is committed to providing high-quality education with industry-relevant curriculum and experienced faculty members."

    def _create_program_type_response(self, program_info):
        """Create program type response"""
        return f"APU offers {program_info['program_type']} programs including {program_info['programme']} ({program_info['course_code']}) through {program_info['faculty']}. These programs are designed to meet industry standards and prepare students for successful careers."

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

    def _save_training_data(self, training_data, output_file):
        """Save training data in JSONL format for Groq"""
        with open(output_file, 'w', encoding='utf-8') as f:
            for example in training_data:
                json.dump(example, f, ensure_ascii=False)
                f.write('\n')
        
        self.stdout.write(f'Saved {len(training_data)} training examples to {output_file}')

    def _create_training_record(self, training_data, output_file):
        """Create training dataset record in database"""
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
        
        # Create training dataset
        dataset = TrainingDataset.objects.create(
            name=f'{self.model_name} Fine-tuning Dataset',
            dataset_type='general',
            description=f'Comprehensive dataset for fine-tuning {self.model_name} with APU programs, academic info, and modules',
            file_path=output_file,
            created_by=admin_user,
            status='active'
        )
        
        # Create training record
        training_record = ChatbotTraining.objects.create(
            training_type='prompt_update',
            status='pending',
            parameters={
                'model_name': self.model_name,
                'training_examples': len(training_data),
                'data_sources': ['excel_programs', 'academic_jsonl', 'module_lists'],
                'output_file': output_file
            },
            started_by=admin_user
        )
        training_record.datasets_used.add(dataset)
        
        self.stdout.write(f'Created training record: {training_record.id}') 