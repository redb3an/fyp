# APU Educational Counselor Chatbot

A professional chatbot interface with enhanced AI capabilities, featuring text-to-speech, speech-to-text, intelligent avatar system, advanced memory management, and context-aware responses powered by Groq AI.

## Core Features

- **Modern ChatGPT-like Interface**: Clean, responsive design with mobile support
- **Enhanced RAG System**: Advanced retrieval with optional vector embeddings
- **Conversation Memory Strategies**: Four intelligent memory management approaches
- **Real-time Speech Services**: Multiple provider support for speech-to-text
- **Intelligent Avatar System**: Natural behaviors with lip-sync and blinking
- **Program Recommendations**: AI-powered academic program matching
- **Cross-conversation Learning**: Knowledge base updates from user interactions

## Enhanced AI Capabilities

### **Advanced RAG (Retrieval Augmented Generation)**

The system features a sophisticated RAG implementation with multiple search strategies:

- **Vector Similarity Search**: Uses sentence-transformers and FAISS for semantic matching
- **Exact Question Matching**: Direct question-answer pair retrieval
- **Semantic Similarity**: Content-based matching with confidence scoring
- **Keyword Matching**: Traditional keyword-based search with category weights
- **Conversation-aware Context**: Integrates conversation history for better results

```python
# Vector embeddings with fallback to keyword search
vector_libs = ['sentence-transformers', 'faiss-cpu', 'numpy']
search_strategies = ['vector', 'exact', 'semantic', 'keyword', 'category']
```

### **Conversation Memory Strategies**

The chatbot implements four memory strategies for different use cases:

#### **1. Short-term Memory** (`'short_term'`)
- **Purpose**: Recent conversation context (5-10 messages)
- **Retention**: 1 day
- **Use Cases**: Immediate follow-ups, conversation continuity

#### **2. Cross-conversation Learning** (`'cross_learning'`)
- **Purpose**: Updates knowledge base from user interactions
- **Retention**: 180 days
- **Use Cases**: Learning from corrections, improving responses

#### **3. RAG Context-aware** (`'rag_context'`)
- **Purpose**: Enhanced retrieval with conversation history
- **Retention**: 7 days
- **Use Cases**: Personalized responses, intent tracking

#### **4. Hybrid Strategy** (`'hybrid'`)
- **Purpose**: Combines all approaches
- **Retention**: 30 days
- **Use Cases**: Production environments, balanced performance

### **Memory Strategy Configuration**

```python
from chatbot.services.conversation_memory_service import ConversationMemoryService

# Initialize with specific strategy
memory_service = ConversationMemoryService(default_strategy='rag_context')

# Extract memories from conversation
memories = memory_service.extract_memory_from_message(
    message=user_message,
    conversation=conversation,
    strategy='hybrid'  # Optional strategy override
)

# Get conversation context for RAG
context = memory_service.get_conversation_context(
    conversation=conversation,
    strategy='rag_context'
)
```

## Avatar Features

The chatbot includes an advanced avatar system with natural human-like behaviors:

### **Visual Behaviors**
- **Continuous Blinking**: Natural blinking patterns that continue even during speech
- **Lip Synchronization**: Mouth movements synchronized with speech at natural pace
- **Adaptive Animation**: Animation speed adjusts based on speech rate for realistic lip-sync

### **Speaking Behaviors**
- **Natural Speech Speed**: 15% slower than normal speed (0.85x) for better comprehension
- **Smooth Transitions**: Enhanced mouth opening/closing animations with rate scaling
- **Voice Preferences**: Prioritizes high-quality female voices (Wavenet when available)

### **Configuration**
The avatar system uses an advanced configuration that can be customized:

```javascript
{
  "avatar": {
    "defaultBehavior": {
      "blinking": "human-like"  // continuous blinking throughout
    },
    "speakingBehavior": {
      "onStart": {
        "mouthAnimation": {
          "type": "open_half_to_full",
          "syncWithTTS": true,
          "pace": "match_tts",
          "rateScale": 0.9  // slows mouth to 90% of base animation speed
        }
      },
      "onEnd": {
        "mouthAnimation": "close"
      }
    }
  },
  "tts": {
    "voice": {
      "gender": "female",
      "preset": "en-US-Wavenet-F"
    },
    "speed": 0.85  // Natural speaking speed
  }
}
```

## Real-time Speech Services

The chatbot supports multiple speech-to-text providers for enhanced accuracy:

### **Currently Available Services**
1. **SpeechRecognition Library**: Google Speech API integration (your current setup)
2. **Web Speech API**: Browser-based fallback

### **Optional Services (Not Currently Installed)**
The framework supports additional services that can be added:
- **Azure Cognitive Services**: Requires `azure-cognitiveservices-speech>=1.31.0`
- **Google Cloud Speech**: Requires `google-cloud-speech>=2.21.0`

### **Current Service Selection**
Your system currently uses:
```python
# Default: SpeechRecognition library with Google Speech API
service = 'speech_recognition'  # Uses Google's free Speech API
fallback = 'web_speech_api'     # Browser-based backup
```

## Setting up Groq API for Speech Recognition

### Requirements

- Python 3.7+
- Groq API key (Get one from [Groq Console](https://console.groq.com/))

### Installation

1. Install the required packages:

```bash
pip install -r requirements.txt
```

2. Set your Groq API key as an environment variable:

```bash
# For Windows
set GROQ_API_KEY=your_groq_api_key_here

# For macOS/Linux
export GROQ_API_KEY=your_groq_api_key_here
```

3. Your current setup is ready to go! You're using Google Speech API via SpeechRecognition (no additional API keys needed).

4. Optional: To add enterprise speech services, install additional packages and configure:

```bash
# For Azure Speech Service (optional)
pip install azure-cognitiveservices-speech>=1.31.0
set AZURE_SPEECH_KEY=your_azure_key_here
set AZURE_SPEECH_REGION=your_region

# For Google Cloud Speech (optional)  
pip install google-cloud-speech>=2.21.0
set GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

## Real-time Speech Processing

Your system currently uses **Google Speech API** via the SpeechRecognition library for optimal performance and accuracy. 

### **Current Setup**
- **Primary Service**: SpeechRecognition library → Google Speech API (free, no API key required)
- **Fallback**: Web Speech API (browser-based)
- **Performance**: Good accuracy with real-time processing
- **Language Support**: Multilingual support

### **Expandable Architecture**
Your speech service framework supports additional providers that can be added later:
- **Azure Cognitive Services**: Enterprise-grade accuracy
- **Google Cloud Speech**: Enhanced enterprise features
- **Automatic Selection**: System chooses best available service

## Program Recommendation System

The chatbot includes an intelligent program recommendation service:

### **Features**
- **Interest Area Mapping**: Maps user interests to relevant programs
- **Career Path Alignment**: Suggests programs based on career goals
- **Study Mode Preferences**: Considers full-time, part-time, and online options
- **Personalized Matching**: Uses conversation history for better recommendations

### **Usage**
```python
from chatbot.services.program_recommendation_service import ProgramRecommendationService

recommender = ProgramRecommendationService()

# Get recommendations based on interests
recommendations = recommender.get_recommendations(
    interests=['programming', 'data science'],
    career_goals=['software developer'],
    study_mode='Full-time'
)
```

## Customization Options

### **Memory Strategy Configuration**

```python
# Change memory strategy for specific needs
memory_service.set_strategy('cross_learning')  # Focus on learning
memory_service.set_strategy('short_term')      # Recent context only
memory_service.set_strategy('rag_context')     # Enhanced retrieval
memory_service.set_strategy('hybrid')          # Balanced approach
```

### **RAG Service Configuration**

```python
# Customize RAG parameters
rag_service = EnhancedRAGService(
    max_results=10,           # Number of results to retrieve
    min_confidence=0.4,       # Minimum confidence threshold
    chunk_size=512,           # Text chunk size for processing
    chunk_overlap=128         # Overlap between chunks
)
```

### **Avatar Behavior**

To customize avatar behavior, you can update the configuration in `static/chatbot/avatar/avatar.js`:

```javascript
// Example: Faster blinking
window.updateAvatarBehavior({
  "avatar": {
    "defaultBehavior": {
      "blinking": "human-like"
    },
    "speakingBehavior": {
      "onStart": {
        "mouthAnimation": {
          "type": "open_half_to_full",
          "rateScale": 1.2  // Faster mouth animation
        }
      }
    }
  },
  "tts": {
    "speed": 1.0  // Normal speaking speed
  }
});
```

### **Speech Service Selection**

Your current setup uses Google Speech API via the SpeechRecognition library:

```python
# Current setup (what you have now)
current_service = 'speech_recognition'  # Google Speech API via SpeechRecognition library

# To add additional services, install the required packages:
# pip install azure-cognitiveservices-speech>=1.31.0    # For Azure
# pip install google-cloud-speech>=2.21.0               # For Google Cloud

# Then configure with API keys:
# set AZURE_SPEECH_KEY=your_key
# set GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

### **TTS Voice Selection**

The system automatically selects the best available voice, but you can customize voice preferences:

```javascript
// In the avatar configuration
"tts": {
  "voice": {
    "gender": "female",           // or "male"
    "preset": "en-US-Wavenet-F"  // Preferred voice name
  },
  "speed": 0.85                   // Speaking rate (0.1 to 10)
}
```

## Usage

1. **Natural Conversations**: Chat with Gigi using the ChatGPT-like interface
2. **Voice Input**: Speak to the chatbot using Google Speech API recognition
3. **Avatar Interaction**: Watch Gigi's natural blinking and lip movements during conversations
4. **Conversation History**: Save and manage multiple conversation threads
5. **User Profiles**: Personalized experience with user preferences and settings

## Technical Architecture

### **Enhanced RAG Pipeline**
- **Knowledge Retrieval**: Multi-strategy search with vector embeddings
- **Context Integration**: Conversation memory enhances retrieval relevance
- **Scoring System**: Advanced relevance and confidence scoring
- **Fallback Support**: Graceful degradation when vector libs unavailable

### **Memory Management System**
- **Strategy-based Processing**: Four distinct memory strategies
- **Automatic Cleanup**: Expired memory management
- **Cross-conversation Learning**: Knowledge base improvements from interactions
- **Database Integration**: Comprehensive memory storage and retrieval

### **Speech Integration**
- **Multi-provider Support**: Automatic service selection based on availability
- **Real-time Processing**: Optimized for real-time speech recognition
- **Fallback System**: Graceful degradation across providers
- **Audio Processing**: WebM to WAV conversion and format handling

### **Avatar System**
- **Avatar Controller**: `static/chatbot/avatar/avatar.js` - Manages avatar behaviors and animations
- **Avatar Assets**: `static/chatbot/avatar/` - Contains avatar images for different expressions
- **Configuration**: JSON-based configuration system for easy customization

## Database Schema (SQLite)

Your system uses **SQLite database** with the following main models:

### **Core Models (Actively Used)**
- **UserProfile**: User preferences and settings
- **Conversation**: Chat conversations with soft delete
- **Message**: Individual chat messages
- **ChatHistory**: Legacy chat storage (being deprecated)

### **Advanced Features (Framework Ready)**
- **ConversationMemory**: Memory strategy management (used in services)
- **KnowledgeBaseEntry**: RAG knowledge storage
- **FineTunedModel**: Model performance tracking (used in admin commands)
- **TrainingDataset**: Learning data storage

## Main Features You're Using

Based on your actual implementation:

- **Chat Interface**: Real-time conversations with SQLite storage
- **User Management**: Profiles, preferences, authentication
- **Speech Recognition**: Google Speech API via SpeechRecognition library
- **Avatar System**: Natural behaviors with lip-sync
- **Conversation Management**: Create, update, delete conversations

## Performance (SQLite Setup)

Your current SQLite-based setup includes:

- **Efficient SQLite Queries**: Optimized conversation and message retrieval
- **Soft Delete Support**: Fast deletion without data loss
- **Indexed Lookups**: User-based conversation filtering
- **Lazy Loading**: Vector libraries loaded only when needed (for future RAG enhancement)
- **Real-time Processing**: Fast speech recognition with Google Speech API

## References

### **Currently Used Technologies**
- [SpeechRecognition Library](https://pypi.org/project/SpeechRecognition/) - Your speech-to-text solution
- [Django Documentation](https://docs.djangoproject.com/en/4.2/) - Your web framework
- [SQLite Documentation](https://www.sqlite.org/docs.html) - Your database
- [Web Speech API Documentation](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API) - Browser fallback

### **Optional Enhancements (Framework Ready)**
- [SentenceTransformers Documentation](https://www.sbert.net/) - For enhanced RAG (optional)
- [FAISS Documentation](https://faiss.ai/) - For vector search (optional)
- [Memory Strategy Guide](chatbot/services/MEMORY_STRATEGY_GUIDE.md) - Advanced memory features
- [Avatar System Configuration Guide](static/chatbot/avatar/avatar.js) - Avatar customization 