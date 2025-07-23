from typing import List, Dict, Any
import logging
from django.db.models import Q
from chatbot.models import KnowledgeBaseEntry
from .enhanced_rag_service import EnhancedRAGService

logger = logging.getLogger(__name__)

class ProgramRecommendationService:
    """
    Advanced program recommendation service with personalized matching
    """
    
    def __init__(self):
        self.rag_service = EnhancedRAGService()
        
        # Academic interest areas for better matching
        self.interest_areas = {
            'technology': ['programming', 'software', 'cybersecurity', 'data science', 'AI', 'networking'],
            'business': ['management', 'marketing', 'entrepreneurship', 'finance', 'economics'],
            'engineering': ['mechanical', 'electrical', 'robotics', 'automation', 'design'],
            'creative': ['design', 'multimedia', 'animation', 'visual effects', 'gaming'],
            'analytics': ['data', 'statistics', 'analysis', 'research', 'business intelligence']
        }
        
        # Career path mappings
        self.career_paths = {
            'software_developer': ['computer science', 'software engineering', 'information technology'],
            'data_scientist': ['data science', 'artificial intelligence', 'analytics'],
            'business_analyst': ['business information systems', 'business analytics', 'information systems'],
            'cybersecurity_expert': ['cybersecurity', 'network security', 'digital forensics'],
            'project_manager': ['project management', 'business administration', 'technology management']
        }
        
        # Study mode preferences
        self.study_modes = ['Full-time', 'Part-time', 'Online/ODL']
        
    def recommend_programs(self, 
                         academic_background: str,
                         interests: List[str],
                         career_goals: str,
                         study_mode_preference: str = None,
                         budget_range: str = None) -> List[Dict[str, Any]]:
        """
        Get personalized program recommendations based on multiple factors
        
        Args:
            academic_background: Previous education and qualifications
            interests: List of academic/professional interests
            career_goals: Desired career path or industry
            study_mode_preference: Preferred mode of study (optional)
            budget_range: Preferred budget range (optional)
            
        Returns:
            List of recommended programs with scores and explanations
        """
        try:
            # Build comprehensive search query
            search_query = self._build_search_query(
                academic_background=academic_background,
                interests=interests,
                career_goals=career_goals
            )
            
            # Get initial program matches
            programs = self.rag_service.retrieve_relevant_knowledge(
                query=search_query,
                categories=['Programs and Courses']
            )
            
            # Score and rank programs
            scored_programs = self._score_programs(
                programs=programs,
                interests=interests,
                career_goals=career_goals,
                study_mode=study_mode_preference,
                budget_range=budget_range
            )
            
            # Add detailed explanations
            recommendations = self._add_recommendation_explanations(scored_programs)
            
            logger.info(f"Generated {len(recommendations)} program recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating program recommendations: {str(e)}")
            return []
    
    def _build_search_query(self, 
                          academic_background: str,
                          interests: List[str],
                          career_goals: str) -> str:
        """Build optimized search query for program matching"""
        
        # Extract education level from background
        education_level = self._extract_education_level(academic_background)
        
        # Map interests to program areas
        program_areas = self._map_interests_to_areas(interests)
        
        # Build query with weighted components
        query_parts = [
            f"programs for {education_level} students",
            f"interested in {', '.join(program_areas)}",
            f"career in {career_goals}"
        ]
        
        return " ".join(query_parts)
    
    def _score_programs(self,
                       programs: List[Dict[str, Any]],
                       interests: List[str],
                       career_goals: str,
                       study_mode: str = None,
                       budget_range: str = None) -> List[Dict[str, Any]]:
        """Score programs based on multiple criteria"""
        
        scored_results = []
        
        for program in programs:
            entry = program['entry']
            base_score = program['relevance_score']
            
            # Extract program details
            program_info = self.rag_service._extract_program_info(entry)
            
            # Interest matching score (30%)
            interest_score = self._calculate_interest_match(
                program_info=program_info,
                interests=interests
            )
            
            # Career alignment score (30%)
            career_score = self._calculate_career_alignment(
                program_info=program_info,
                career_goals=career_goals
            )
            
            # Study mode compatibility (20%)
            mode_score = 1.0
            if study_mode and program_info['study_mode']:
                mode_score = 1.2 if study_mode == program_info['study_mode'] else 0.8
            
            # Budget compatibility (20%)
            budget_score = 1.0
            if budget_range:
                budget_score = self._calculate_budget_compatibility(
                    program_info=program_info,
                    budget_range=budget_range
                )
            
            # Calculate weighted final score
            final_score = (
                base_score * 0.2 +
                interest_score * 0.3 +
                career_score * 0.3 +
                mode_score * 0.1 +
                budget_score * 0.1
            )
            
            scored_results.append({
                'program': program_info,
                'score': min(final_score, 1.0),
                'matching_factors': {
                    'interest_match': interest_score,
                    'career_alignment': career_score,
                    'mode_compatibility': mode_score,
                    'budget_compatibility': budget_score
                }
            })
        
        # Sort by final score
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        return scored_results
    
    def _calculate_interest_match(self,
                                program_info: Dict[str, Any],
                                interests: List[str]) -> float:
        """Calculate how well program matches user interests"""
        
        match_score = 0.0
        program_keywords = set()
        
        # Extract keywords from program info
        if program_info['name']:
            program_keywords.update(self._extract_keywords(program_info['name']))
        if program_info['specialization']:
            program_keywords.update(self._extract_keywords(program_info['specialization']))
        
        # Add keywords from modules
        for module in program_info['core_modules'] + program_info['specialized_modules']:
            program_keywords.update(self._extract_keywords(module))
        
        # Calculate matches with interest areas
        for interest in interests:
            interest_keywords = set()
            for area, keywords in self.interest_areas.items():
                if interest.lower() in area.lower():
                    interest_keywords.update(keywords)
            
            if interest_keywords:
                matches = len(program_keywords.intersection(interest_keywords))
                match_score += matches * 0.1
        
        return min(match_score, 1.0)
    
    def _calculate_career_alignment(self,
                                  program_info: Dict[str, Any],
                                  career_goals: str) -> float:
        """Calculate how well program aligns with career goals"""
        
        alignment_score = 0.0
        career_keywords = set()
        
        # Get relevant career paths
        for career, programs in self.career_paths.items():
            if career_goals.lower() in career.lower():
                career_keywords.update(self._extract_keywords(" ".join(programs)))
        
        # Match with program details
        program_text = " ".join([
            program_info['name'] or "",
            program_info['specialization'] or "",
            " ".join(program_info['core_modules']),
            " ".join(program_info['specialized_modules'])
        ])
        
        program_keywords = set(self._extract_keywords(program_text))
        
        # Calculate alignment score
        if career_keywords:
            matches = len(program_keywords.intersection(career_keywords))
            alignment_score = min(matches * 0.15, 1.0)
        
        return alignment_score
    
    def _calculate_budget_compatibility(self,
                                     program_info: Dict[str, Any],
                                     budget_range: str) -> float:
        """Calculate program's compatibility with budget range"""
        # Simple implementation - can be enhanced with actual fee data
        return 1.0
    
    def _add_recommendation_explanations(self,
                                       scored_programs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add detailed explanations for recommendations"""
        
        explained_results = []
        
        for program in scored_programs:
            explanation = []
            
            # Program strength explanation
            if program['score'] >= 0.8:
                explanation.append("Excellent match based on your profile")
            elif program['score'] >= 0.6:
                explanation.append("Good match for your interests and goals")
            else:
                explanation.append("Moderate match that may be worth considering")
            
            # Interest match explanation
            interest_score = program['matching_factors']['interest_match']
            if interest_score >= 0.7:
                explanation.append("Strongly aligns with your academic interests")
            elif interest_score >= 0.5:
                explanation.append("Contains elements matching your interests")
            
            # Career alignment explanation
            career_score = program['matching_factors']['career_alignment']
            if career_score >= 0.7:
                explanation.append("Excellent preparation for your career goals")
            elif career_score >= 0.5:
                explanation.append("Provides relevant skills for your career path")
            
            # Add mode and budget explanations if applicable
            if program['matching_factors']['mode_compatibility'] > 1.0:
                explanation.append("Offers your preferred study mode")
            if program['matching_factors']['budget_compatibility'] > 0.8:
                explanation.append("Within your budget range")
            
            explained_results.append({
                **program,
                'explanation': explanation
            })
        
        return explained_results
    
    def _extract_education_level(self, academic_background: str) -> str:
        """Extract education level from background"""
        background_lower = academic_background.lower()
        
        if 'spm' in background_lower or 'o-level' in background_lower:
            return 'Foundation or Diploma'
        elif 'stpm' in background_lower or 'a-level' in background_lower:
            return 'Undergraduate'
        elif 'degree' in background_lower or 'bachelor' in background_lower:
            return 'Postgraduate'
        elif 'master' in background_lower:
            return 'Doctoral'
        else:
            return 'Foundation'
    
    def _map_interests_to_areas(self, interests: List[str]) -> List[str]:
        """Map user interests to program areas"""
        program_areas = set()
        
        for interest in interests:
            interest_lower = interest.lower()
            
            # Check each interest area
            for area, keywords in self.interest_areas.items():
                if any(kw in interest_lower for kw in keywords):
                    program_areas.add(area)
        
        return list(program_areas) if program_areas else ['general']
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        import re
        
        # Clean and normalize text
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Extract words (3+ characters)
        words = re.findall(r'\b[a-z]{3,}\b', text)
        
        return words 