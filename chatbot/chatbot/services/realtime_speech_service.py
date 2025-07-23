#!/usr/bin/env python3
"""
Real-Time Speech-to-Text Service
Multiple high-accuracy real-time speech recognition providers
"""

import logging
import tempfile
import wave
import json
import asyncio
from typing import Optional, Dict, Any, List
import numpy as np

# Optional imports for different speech services
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

try:
    import azure.cognitiveservices.speech as speechsdk
    AZURE_SPEECH_AVAILABLE = True
except ImportError:
    AZURE_SPEECH_AVAILABLE = False

try:
    import google.cloud.speech as gcs
    GOOGLE_CLOUD_SPEECH_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_SPEECH_AVAILABLE = False



logger = logging.getLogger(__name__)

class RealTimeSpeechService:
    """
    High-accuracy real-time speech-to-text service with multiple providers
    """
    
    def __init__(self):
        self.sample_rate = 16000  # Standard for most speech services
        self.channels = 1
        
        # Available services
        self.available_services = self._check_available_services()
        logger.info(f"Available speech services: {list(self.available_services.keys())}")
        
    def _check_available_services(self) -> Dict[str, bool]:
        """Check which speech recognition services are available"""
        services = {
            'web_speech_api': True,  # Browser-based, always available
            'speech_recognition': SPEECH_RECOGNITION_AVAILABLE,
            'azure_speech': AZURE_SPEECH_AVAILABLE,
            'google_cloud': GOOGLE_CLOUD_SPEECH_AVAILABLE,
        }
        return {k: v for k, v in services.items() if v}
    
    def get_recommended_service(self) -> str:
        """Get the recommended service based on availability and performance"""
        # Priority order: best performance and accuracy for server-side transcription
        priority_order = [
            'speech_recognition', # Good accuracy, uses Google Speech API
            'azure_speech',      # Best for real-time, high accuracy
            'google_cloud',      # Excellent accuracy, good real-time
            'web_speech_api',    # Browser-based fallback
        ]
        
        for service in priority_order:
            if service in self.available_services:
                return service
        
        return 'speech_recognition'  # Fallback
    
    async def transcribe_audio_file(self, audio_file_path: str, service_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcribe an audio file using the specified service
        """
        if not service_name:
            service_name = self.get_recommended_service()
        
        logger.info(f"Transcribing audio file with {service_name}")
        
        if service_name == 'speech_recognition':
            return await self._transcribe_file_speech_recognition(audio_file_path)
        elif service_name == 'web_speech_api':
            # Web Speech API is browser-only, suggest using SpeechRecognition instead
            logger.info("Web Speech API requested but it's browser-only, trying SpeechRecognition instead")
            return await self._transcribe_file_speech_recognition(audio_file_path)
        else:
            return {'error': f'File transcription not supported for {service_name}'}
    
    async def _transcribe_file_speech_recognition(self, audio_file: str) -> Dict[str, Any]:
        """Transcribe audio file using SpeechRecognition library"""
        if not SPEECH_RECOGNITION_AVAILABLE:
            return {'error': 'speech_recognition library not installed. Run: pip install SpeechRecognition', 'success': False}
        
        import asyncio
        import concurrent.futures
        
        def _sync_transcribe():
            """Synchronous transcription function to run in thread"""
            try:
                recognizer = sr.Recognizer()
                
                # Optimize recognizer settings for better accuracy
                recognizer.energy_threshold = 300
                recognizer.dynamic_energy_threshold = True
                recognizer.pause_threshold = 0.8
                recognizer.operation_timeout = None
                recognizer.phrase_threshold = 0.3
                recognizer.non_speaking_duration = 0.8
                
                # Debug: Check file info
                import os
                logger.info(f"Attempting to read audio file: {audio_file}")
                logger.info(f"File exists: {os.path.exists(audio_file)}")
                if os.path.exists(audio_file):
                    logger.info(f"File size: {os.path.getsize(audio_file)} bytes")
                    logger.info(f"File extension: {os.path.splitext(audio_file)[1]}")
                
                # Try to open the audio file with SpeechRecognition
                try:
                    with sr.AudioFile(audio_file) as source:
                        # Adjust for noise
                        recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        audio = recognizer.record(source)
                        logger.info("✅ Successfully opened audio file with SpeechRecognition")
                except Exception as file_error:
                    logger.error(f"Failed to read audio file: {file_error}")
                    logger.error(f"File details - Path: {audio_file}, Exists: {os.path.exists(audio_file)}")
                    return {
                        'error': f'Audio file format not supported: {file_error}',
                        'success': False,
                        'suggestion': 'Ensure audio is in WAV format with proper encoding'
                    }
                
                # Try engines in order of preference for accuracy
                engines = [
                    ('Google Speech Recognition', lambda: recognizer.recognize_google(audio, language='en-US', show_all=False)),
                    ('Google (with confidence)', lambda: self._get_google_with_confidence(recognizer, audio)),
                ]
                
                engine_errors = []
                
                for engine_name, engine_func in engines:
                    try:
                        logger.info(f"🔄 Trying {engine_name}...")
                        result = engine_func()
                        
                        if result and (isinstance(result, str) and result.strip()):
                            confidence = 0.85  # Default confidence
                            text = result
                            
                            # Handle confidence if available
                            if isinstance(result, dict) and 'alternative' in result:
                                best_alt = result['alternative'][0]
                                text = best_alt.get('transcript', '')
                                confidence = best_alt.get('confidence', 0.85)
                            
                            if text.strip():
                                logger.info(f"✅ Transcribed ({engine_name}): {text} (confidence: {confidence:.2f})")
                                return {
                                    'transcription': text,
                                    'confidence': confidence,
                                    'engine': engine_name,
                                    'detected_language': 'en-US',
                                    'success': True
                                }
                    except Exception as e:
                        error_msg = str(e)
                        logger.warning(f"❌ {engine_name} failed: {error_msg}")
                        engine_errors.append(f"{engine_name}: {error_msg}")
                        continue
                
                # Return detailed error information
                error_details = "; ".join(engine_errors) if engine_errors else "No engines available"
                logger.error(f"All speech recognition engines failed: {error_details}")
                
                return {
                    'error': f'All recognition engines failed to transcribe audio: {error_details}', 
                    'success': False,
                    'engine_errors': engine_errors
                }
                
            except Exception as e:
                logger.error(f"Speech recognition error: {e}")
                return {'error': str(e), 'success': False}
        
        # Run the synchronous function in a thread pool
        try:
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(executor, _sync_transcribe)
                return result
        except Exception as e:
            logger.error(f"Async speech recognition error: {e}")
            return {'error': str(e), 'success': False}
    
    def _get_google_with_confidence(self, recognizer, audio):
        """Get Google recognition result with confidence scores"""
        try:
            result = recognizer.recognize_google(audio, language='en-US', show_all=True)
            if result and 'alternative' in result:
                return result
            return None
        except:
            return None
    

    

    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about available services and their capabilities"""
        services_info = {
            'web_speech_api': {
                'name': 'Web Speech API',
                'accuracy': 'High',
                'latency': 'Very Low (Real-time)',
                'cost': 'Free',
                'setup': 'No setup required',
                'real_time': True,
                'description': 'Browser-based speech recognition, works immediately with microphone',
                'pros': ['Zero latency', 'No API keys needed', 'Real-time streaming'],
                'cons': ['Browser dependent', 'Requires internet']
            },
            'speech_recognition': {
                'name': 'SpeechRecognition Library',
                'accuracy': 'High',
                'latency': 'Low (1-3 seconds)',
                'cost': 'Free (with Google limit)',
                'setup': 'pip install SpeechRecognition',
                'real_time': True,
                'description': 'Python library supporting multiple engines including Google',
                'pros': ['Multiple engines', 'Good accuracy', 'Easy to use'],
                'cons': ['Requires internet', 'API limits']
            },

            'azure_speech': {
                'name': 'Azure Speech Services',
                'accuracy': 'Excellent',
                'latency': 'Very Low (Real-time)',
                'cost': 'Free tier: 5 hours/month',
                'setup': 'Azure account + SDK installation',
                'real_time': True,
                'description': 'Microsoft\'s enterprise speech service with real-time streaming',
                'pros': ['Real-time streaming', 'Excellent accuracy', 'Enterprise grade'],
                'cons': ['Setup required', 'Azure account needed']
            },
            'google_cloud': {
                'name': 'Google Cloud Speech-to-Text',
                'accuracy': 'Excellent',
                'latency': 'Low (Real-time capable)',
                'cost': 'Free tier: 60 minutes/month',
                'setup': 'Google Cloud account + credentials',
                'real_time': True,
                'description': 'Google\'s enterprise speech service with streaming support',
                'pros': ['Excellent accuracy', 'Real-time streaming', 'Many languages'],
                'cons': ['Setup required', 'Google Cloud account needed']
            }
        }
        
        return {
            'available_services': self.available_services,
            'recommended': self.get_recommended_service(),
            'services_info': {k: v for k, v in services_info.items() if k in self.available_services}
        }

# Singleton instance
realtime_speech_service = RealTimeSpeechService() 