from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import logging

from chatbot.services.conversation_memory_service import conversation_memory_service
from chatbot.models import ConversationMemory, KnowledgeBaseEntry, TrainingDataset

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process cross-conversation learning to update knowledge base from user interactions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to look back for learning data (default: 7)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without making changes'
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Also cleanup expired memories'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting cross-conversation learning process...')
        )
        
        days = options['days']
        dry_run = options['dry_run']
        cleanup = options['cleanup']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        # Process learning
        try:
            results = self.process_learning(days, dry_run)
            self.display_results(results)
            
            # Cleanup if requested
            if cleanup:
                cleanup_results = self.cleanup_memories(dry_run)
                self.display_cleanup_results(cleanup_results)
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during processing: {str(e)}')
            )
            logger.error(f'Cross-conversation learning error: {str(e)}')

    def process_learning(self, days: int, dry_run: bool) -> dict:
        """Process conversation learning data"""
        
        # Get unprocessed corrections and feedback
        cutoff_date = timezone.now() - timedelta(days=days)
        
        corrections = ConversationMemory.objects.filter(
            memory_type='correction',
            has_influenced_kb=False,
            is_active=True,
            created_at__gte=cutoff_date
        )
        
        negative_feedback = ConversationMemory.objects.filter(
            memory_type='feedback',
            has_influenced_kb=False,
            is_active=True,
            created_at__gte=cutoff_date,
            context__sentiment__lt=0
        )
        
        insights = ConversationMemory.objects.filter(
            memory_type='insight',
            has_influenced_kb=False,
            is_active=True,
            created_at__gte=cutoff_date
        )
        
        self.stdout.write(f'Found {corrections.count()} corrections to process')
        self.stdout.write(f'Found {negative_feedback.count()} negative feedback items')
        self.stdout.write(f'Found {insights.count()} insights to process')
        
        results = {
            'corrections_found': corrections.count(),
            'feedback_found': negative_feedback.count(),
            'insights_found': insights.count(),
            'corrections_processed': 0,
            'feedback_processed': 0,
            'insights_processed': 0,
            'kb_entries_created': 0,
            'kb_entries_updated': 0,
            'patterns_identified': 0
        }
        
        if not dry_run:
            # Process corrections
            for correction in corrections:
                if self.process_correction(correction):
                    results['corrections_processed'] += 1
            
            # Process negative feedback
            for feedback in negative_feedback:
                if self.process_negative_feedback(feedback):
                    results['feedback_processed'] += 1
            
            # Process insights
            for insight in insights:
                if self.process_insight(insight):
                    results['insights_processed'] += 1
            
            # Identify patterns
            patterns = self.identify_common_patterns(days)
            results['patterns_identified'] = len(patterns)
            
            # Create KB entries from patterns
            kb_created = self.create_kb_from_patterns(patterns)
            results['kb_entries_created'] = kb_created
        
        return results

    def process_correction(self, correction: ConversationMemory) -> bool:
        """Process a user correction"""
        try:
            self.stdout.write(f'Processing correction: {correction.content[:50]}...')
            
            # Analyze the correction
            original_message = correction.context.get('original_message', '')
            
            # Look for patterns like "No, it should be..." or "Actually, the correct answer is..."
            correction_patterns = [
                r'actually[,\s]+(.*)',
                r'no[,\s]+(.*)',
                r'should be[,\s]+(.*)',
                r'correct answer is[,\s]+(.*)',
                r'meant[,\s]+(.*)'
            ]
            
            import re
            corrected_info = None
            for pattern in correction_patterns:
                match = re.search(pattern, original_message.lower())
                if match:
                    corrected_info = match.group(1).strip()
                    break
            
            if corrected_info:
                # Log for manual review
                self.stdout.write(f'  Identified correction: "{corrected_info}"')
                
                # You could implement automatic KB updates here
                # For now, we'll mark it as processed and log for manual review
                
            # Mark as processed
            correction.has_influenced_kb = True
            correction.save()
            
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error processing correction {correction.id}: {str(e)}')
            )
            return False

    def process_negative_feedback(self, feedback: ConversationMemory) -> bool:
        """Process negative feedback"""
        try:
            self.stdout.write(f'Processing feedback: {feedback.content[:50]}...')
            
            # Log the feedback for analysis
            conversation = feedback.conversation
            
            # Get the assistant's response that received negative feedback
            recent_messages = conversation.messages.filter(
                created_at__lte=feedback.created_at
            ).order_by('-created_at')[:5]
            
            assistant_responses = [
                msg for msg in recent_messages 
                if msg.sender == 'assistant'
            ]
            
            if assistant_responses:
                problematic_response = assistant_responses[0].content
                self.stdout.write(f'  Problematic response: {problematic_response[:100]}...')
            
            # Mark as processed
            feedback.has_influenced_kb = True
            feedback.save()
            
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error processing feedback {feedback.id}: {str(e)}')
            )
            return False

    def process_insight(self, insight: ConversationMemory) -> bool:
        """Process extracted insights"""
        try:
            self.stdout.write(f'Processing insight: {insight.content[:50]}...')
            
            # Mark as processed
            insight.has_influenced_kb = True
            insight.save()
            
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error processing insight {insight.id}: {str(e)}')
            )
            return False

    def identify_common_patterns(self, days: int) -> list:
        """Identify common patterns in user questions and feedback"""
        patterns = []
        
        try:
            cutoff_date = timezone.now() - timedelta(days=days)
            
            # Find frequently asked topics
            topic_memories = ConversationMemory.objects.filter(
                memory_type='topic',
                is_active=True,
                created_at__gte=cutoff_date
            )
            
            # Count topic frequencies
            topic_counts = {}
            for memory in topic_memories:
                topics = memory.context.get('topics', [])
                for topic in topics:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
            
            # Identify topics asked about frequently but with low satisfaction
            frequent_topics = [
                topic for topic, count in topic_counts.items() 
                if count >= 3  # Asked at least 3 times
            ]
            
            for topic in frequent_topics:
                patterns.append({
                    'type': 'frequent_topic',
                    'topic': topic,
                    'frequency': topic_counts[topic],
                    'description': f'Topic "{topic}" was asked about {topic_counts[topic]} times'
                })
            
            self.stdout.write(f'Identified {len(patterns)} patterns')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error identifying patterns: {str(e)}')
            )
        
        return patterns

    def create_kb_from_patterns(self, patterns: list) -> int:
        """Create knowledge base entries from identified patterns"""
        created_count = 0
        
        try:
            # Get or create a dataset for learned content
            dataset, created = TrainingDataset.objects.get_or_create(
                name='Cross-Conversation Learning',
                dataset_type='general',
                defaults={
                    'description': 'Knowledge entries created from conversation patterns and feedback',
                    'file_path': 'auto_generated/conversation_learning.json',
                    'version': '1.0'
                }
            )
            
            for pattern in patterns:
                if pattern['type'] == 'frequent_topic':
                    topic = pattern['topic']
                    frequency = pattern['frequency']
                    
                    # Check if we already have a KB entry for this topic
                    existing = KnowledgeBaseEntry.objects.filter(
                        question__icontains=topic,
                        dataset=dataset
                    ).first()
                    
                    if not existing:
                        # Create a placeholder entry that needs manual review
                        entry = KnowledgeBaseEntry.objects.create(
                            dataset=dataset,
                            question=f"Frequently asked about: {topic}",
                            answer=f"This topic was asked about {frequency} times. Manual review needed to provide comprehensive answer.",
                            category='Auto-Generated',
                            entry_type='general',
                            keywords=[topic],
                            metadata={
                                'auto_generated': True,
                                'pattern_type': 'frequent_topic',
                                'frequency': frequency,
                                'needs_review': True
                            },
                            confidence_score=0.3,  # Low confidence for auto-generated
                            is_validated=False
                        )
                        
                        created_count += 1
                        self.stdout.write(f'Created KB entry for frequent topic: {topic}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating KB entries: {str(e)}')
            )
        
        return created_count

    def cleanup_memories(self, dry_run: bool) -> dict:
        """Cleanup expired memories"""
        if dry_run:
            expired_count = ConversationMemory.objects.filter(
                expires_at__lt=timezone.now(),
                is_active=True
            ).count()
            return {'expired_memories_found': expired_count}
        else:
            return conversation_memory_service.cleanup_expired_memories()

    def display_results(self, results: dict):
        """Display processing results"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('PROCESSING RESULTS:'))
        self.stdout.write('='*50)
        
        self.stdout.write(f"Corrections found: {results['corrections_found']}")
        self.stdout.write(f"Corrections processed: {results['corrections_processed']}")
        self.stdout.write(f"Negative feedback found: {results['feedback_found']}")
        self.stdout.write(f"Negative feedback processed: {results['feedback_processed']}")
        self.stdout.write(f"Insights found: {results['insights_found']}")
        self.stdout.write(f"Insights processed: {results['insights_processed']}")
        self.stdout.write(f"Patterns identified: {results['patterns_identified']}")
        self.stdout.write(f"KB entries created: {results['kb_entries_created']}")
        self.stdout.write(f"KB entries updated: {results['kb_entries_updated']}")

    def display_cleanup_results(self, results: dict):
        """Display cleanup results"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('CLEANUP RESULTS:'))
        self.stdout.write('='*50)
        
        for key, value in results.items():
            self.stdout.write(f"{key.replace('_', ' ').title()}: {value}")
        
        self.stdout.write('\n' + self.style.SUCCESS('Cross-conversation learning process completed!')) 