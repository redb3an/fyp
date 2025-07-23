import json
import os
import tempfile
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework import status
import uuid
from groq import Groq
from .services.chatbot_service import GroqChatbot
# Local Whisper removed - using real-time services only
# from .services.whisper_service import LocalWhisperService
from .services.realtime_speech_service import realtime_speech_service
from .models import UserProfile, ChatHistory, Conversation, Message

class SessionValidatedJWTAuthentication(JWTAuthentication):
    """
    Custom JWT Authentication that also validates UserSession status
    """
    def authenticate(self, request):
        # First, do standard JWT authentication
        result = super().authenticate(request)
        if result is None:
            return None
        
        user, validated_token = result
        
        # Check if user has any active sessions and update last activity
        try:
            from .models import UserSession
            from django.utils import timezone
            
            # Get the most recent active session for this user
            active_session = UserSession.objects.filter(
                user=user, 
                is_active=True,
                expires_at__gt=timezone.now()
            ).order_by('-last_activity').first()
            
            if not active_session:
                # No active session found, authentication fails
                return None
            
            # Update last activity timestamp (heartbeat)
            active_session.last_activity = timezone.now()
            active_session.save(update_fields=['last_activity'])
                
        except Exception as e:
            # If session check fails, allow authentication to proceed
            # (fallback to standard JWT validation)
            pass
        
        return user, validated_token

def index(request):
    """
    Main chatbot interface with token-based authentication for iframe embedding
    """
    user = None
    
    # Check for token in URL parameters (for iframe embedding)
    token = request.GET.get('token')
    if token:
        try:
            from rest_framework_simplejwt.tokens import UntypedToken
            from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
            from django.contrib.auth.models import User
            import jwt
            from django.conf import settings
            
            # Validate the token
            UntypedToken(token)
            
            # Decode the token to get user info
            decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = decoded_token.get('user_id')
            user = User.objects.get(id=user_id)
            
        except (InvalidToken, TokenError, User.DoesNotExist, jwt.InvalidTokenError):
            # If token is invalid, show login required message
            return render(request, 'chatbot/index.html', {
                'auth_required': True,
                'error': 'Invalid authentication token. Please log in again.'
            })
    else:
        # Fallback to session-based authentication
        if not request.user.is_authenticated:
            return render(request, 'chatbot/index.html', {
                'auth_required': True,
                'error': 'Authentication required. Please log in.'
            })
        user = request.user
    
    # Get user's conversations and messages (modern system)
    conversations = Conversation.objects.filter(user=user).order_by('-updated_at')
    
    # Get user's full name from profile or first/last name
    full_name = ''
    try:
        profile = UserProfile.objects.get(user=user)
        full_name = profile.full_name
    except UserProfile.DoesNotExist:
        full_name = f"{user.first_name} {user.last_name}".strip()
    
    # Fallback to email if no name is available
    if not full_name:
        full_name = user.email.split('@')[0]  # Use email prefix
    
    return render(request, 'chatbot/index.html', {
        'conversations': conversations,
        'user_id': user.id,
        'user': user,
        'user_full_name': full_name,
        'auth_required': False
    })

# ================================
# AUTHENTICATION API ENDPOINTS
# ================================

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Register a new user with email, password, and full name
    """
    try:
        data = json.loads(request.body)
        
        # Extract data from request
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        confirm_password = data.get('confirmPassword', '')  # Match frontend field name
        full_name = data.get('name', '').strip()  # Match frontend field name
        
        # Validation
        if not email or not password or not full_name:
            return JsonResponse({
                'success': False,
                'error': 'Email, password, and full name are required'
            }, status=400)
        
        if password != confirm_password:
            return JsonResponse({
                'success': False,
                'error': 'Passwords do not match'
            }, status=400)
        
        if len(password) < 8:
            return JsonResponse({
                'success': False,
                'error': 'Password must be at least 8 characters long'
            }, status=400)
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'error': 'An account with this email already exists'
            }, status=400)
        
        # Create the user
        try:
            # Create user without saving first to set the password correctly
            user = User(
                username=email,  # Use email as username
                email=email,
                first_name=full_name.split(' ')[0] if full_name else '',
                last_name=' '.join(full_name.split(' ')[1:]) if len(full_name.split(' ')) > 1 else ''
            )
            user.set_password(password)  # This properly hashes the password
            user.save()
            
            # Create or update the user profile
            UserProfile.objects.get_or_create(
                user=user,
                defaults={'full_name': full_name}
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Account created successfully!',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': full_name
                }
            }, status=201)
            
        except IntegrityError:
            return JsonResponse({
                'success': False,
                'error': 'An account with this email already exists'
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Registration failed: {str(e)}'
        }, status=500)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """
    Login user with email and password, return JWT tokens
    """
    try:
        data = json.loads(request.body)
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return Response({
                'success': False,
                'error': 'Email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Authenticate user
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            if user.is_active:
                # Generate tokens
                refresh = RefreshToken.for_user(user)
                
                # Create server-side session tracking
                try:
                    from .models import UserSession
                    from datetime import timedelta
                    from django.utils import timezone
                    import uuid
                    
                    # Get request metadata
                    ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
                    if ip_address:
                        ip_address = ip_address.split(',')[0].strip()
                    else:
                        ip_address = request.META.get('REMOTE_ADDR')
                    
                    user_agent = request.META.get('HTTP_USER_AGENT', '')
                    
                    # Parse browser info for device_info
                    device_info = 'Unknown Browser'
                    if user_agent:
                        try:
                            from user_agents import parse
                            ua = parse(user_agent)
                            device_info = f"{ua.browser.family} on {ua.os.family}"
                            if ua.device.family != 'Other':
                                device_info += f" ({ua.device.family})"
                        except:
                            device_info = 'Unknown Browser'
                    
                    # Create session entry
                    session = UserSession.objects.create(
                        user=user,
                        session_key=str(uuid.uuid4()),
                        ip_address=ip_address,
                        user_agent=user_agent,
                        device_info=device_info,
                        expires_at=timezone.now() + timedelta(hours=24)
                    )
                    
                except Exception as e:
                    # Don't fail login if session tracking fails
                    print(f"Failed to create session tracking: {e}")
                
                # Get user profile information
                full_name = ''
                if hasattr(user, 'profile') and user.profile.full_name:
                    full_name = user.profile.full_name
                else:
                    full_name = f"{user.first_name} {user.last_name}".strip()
                
                return Response({
                    'success': True,
                    'message': 'Login successful!',
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'full_name': full_name,
                        'is_authenticated': True,
                        'is_superuser': user.is_superuser
                    },
                    'tokens': {
                        'access': str(refresh.access_token),
                        'refresh': str(refresh)
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': 'Account is deactivated'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                'success': False,
                'error': 'Invalid email or password'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Login failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([SessionValidatedJWTAuthentication])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """
    Logout the current user and mark their session as inactive
    """
    try:
        user = request.user
        
        # Mark user's sessions as inactive and clean up immediately
        from .models import UserSession
        from django.utils import timezone
        
        # Get request metadata to try to identify the specific session
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
        if ip_address:
            ip_address = ip_address.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Try to find and deactivate the specific session first
        # Look for the most recent active session with matching IP and user agent
        specific_session = UserSession.objects.filter(
            user=user,
            is_active=True,
            ip_address=ip_address,
            user_agent=user_agent
        ).order_by('-last_activity').first()
        
        if specific_session:
            # Mark the specific session as inactive and delete it immediately
            specific_session.delete()
        else:
            # If we can't identify the specific session, mark and delete the most recent active session
            recent_session = UserSession.objects.filter(
                user=user,
                is_active=True
            ).order_by('-last_activity').first()
            
            if recent_session:
                recent_session.delete()
        
        # Clean up any remaining inactive sessions for this user
        UserSession.objects.filter(user=user, is_active=False).delete()
        
        # Perform Django logout
        logout(request)
        
        return JsonResponse({
            'success': True,
            'message': 'Logged out successfully'
        }, status=200)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Logout failed: {str(e)}'
        }, status=500)

@api_view(['GET'])
@authentication_classes([SessionValidatedJWTAuthentication])
@permission_classes([IsAuthenticated])
def verify_token(request):
    """
    Verify JWT token and return user info
    """
    try:
        user = request.user
        full_name = ''
        if hasattr(user, 'profile') and user.profile.full_name:
            full_name = user.profile.full_name
        else:
            full_name = f"{user.first_name} {user.last_name}".strip()
        
        # Get user theme preference
        theme = 'light'  # default
        try:
            if hasattr(user, 'profile') and user.profile:
                theme = user.profile.theme
        except:
            pass

        return Response({
            'success': True,
            'is_authenticated': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': full_name,
                'is_superuser': user.is_superuser,
                'theme': theme
            }
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
def check_auth_status(request):
    """
    Check if user is authenticated and return user info
    """
    if request.user.is_authenticated:
        full_name = ''
        if hasattr(request.user, 'profile') and request.user.profile.full_name:
            full_name = request.user.profile.full_name
        else:
            full_name = f"{request.user.first_name} {request.user.last_name}".strip()
        
        return JsonResponse({
            'success': True,
            'is_authenticated': True,
            'user': {
                'id': request.user.id,
                'email': request.user.email,
                'full_name': full_name
            }
        })
    else:
        return JsonResponse({
            'success': True,
            'is_authenticated': False,
            'user': None
        })

# ================================
# CONVERSATION MANAGEMENT API ENDPOINTS
# ================================

@api_view(['GET'])
@authentication_classes([SessionAuthentication, JWTAuthentication, SessionValidatedJWTAuthentication])
@permission_classes([IsAuthenticated])
def get_conversations(request):
    """
    Get all conversations for the authenticated user
    """
    try:
        conversations = Conversation.objects.filter(user=request.user).order_by('-updated_at')
        
        conversations_data = [{
            'id': str(conv.id),
            'title': conv.title,
            'message_count': conv.message_count,
            'created_at': conv.created_at.isoformat(),
            'updated_at': conv.updated_at.isoformat(),
            'last_message_time': conv.last_message_time.isoformat()
        } for conv in conversations]
        
        return Response({
            'success': True,
            'conversations': conversations_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to fetch conversations: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([SessionAuthentication, JWTAuthentication, SessionValidatedJWTAuthentication])
@permission_classes([IsAuthenticated])
def create_conversation(request):
    """
    Create a new conversation for the authenticated user
    """
    try:
        data = json.loads(request.body) if request.body else {}
        title = data.get('title', 'New Conversation')
        
        conversation = Conversation.objects.create(
            user=request.user,
            title=title
        )
        
        return Response({
            'success': True,
            'conversation': {
                'id': str(conversation.id),
                'title': conversation.title,
                'message_count': 0,
                'created_at': conversation.created_at.isoformat(),
                'updated_at': conversation.updated_at.isoformat()
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to create conversation: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@authentication_classes([SessionAuthentication, JWTAuthentication, SessionValidatedJWTAuthentication])
@permission_classes([IsAuthenticated])
def get_conversation_messages(request, conversation_id):
    """
    Get all messages for a specific conversation
    """
    try:
        # Verify the conversation belongs to the authenticated user
        conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        
        messages = Message.objects.filter(conversation=conversation).order_by('created_at')
        
        messages_data = [{
            'id': str(msg.id),
            'content': msg.content,
            'sender': msg.sender,
            'created_at': msg.created_at.isoformat()
        } for msg in messages]
        
        return Response({
            'success': True,
            'conversation': {
                'id': str(conversation.id),
                'title': conversation.title,
                'messages': messages_data
            }
        }, status=status.HTTP_200_OK)
        
    except Conversation.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Conversation not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to fetch conversation messages: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@authentication_classes([SessionAuthentication, JWTAuthentication, SessionValidatedJWTAuthentication])
@permission_classes([IsAuthenticated])
def rename_conversation(request, conversation_id):
    """
    Rename a conversation
    """
    try:
        data = json.loads(request.body)
        new_title = data.get('title', '').strip()
        
        if not new_title:
            return Response({
                'success': False,
                'error': 'Title is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify the conversation belongs to the authenticated user
        conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        conversation.title = new_title
        conversation.save()
        
        return Response({
            'success': True,
            'conversation': {
                'id': str(conversation.id),
                'title': conversation.title,
                'updated_at': conversation.updated_at.isoformat()
            }
        }, status=status.HTTP_200_OK)
        
    except Conversation.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Conversation not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to rename conversation: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@authentication_classes([SessionAuthentication, JWTAuthentication, SessionValidatedJWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_conversation(request, conversation_id):
    """
    Soft delete a conversation and all its messages
    """
    try:
        # Verify the conversation belongs to the authenticated user
        conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        conversation.delete()  # This will now use soft delete
        
        return Response({
            'success': True,
            'message': 'Conversation deleted successfully'
        }, status=status.HTTP_200_OK)
        
    except Conversation.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Conversation not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to delete conversation: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ================================
# USER PREFERENCE API ENDPOINTS
# ================================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_user_theme(request):
    """
    Get the user's theme preference
    """
    try:
        profile = UserProfile.objects.get(user=request.user)
        return Response({
            'success': True,
            'theme': profile.theme
        }, status=status.HTTP_200_OK)
        
    except UserProfile.DoesNotExist:
        # Create profile with default theme if it doesn't exist
        profile = UserProfile.objects.create(
            user=request.user,
            full_name=f"{request.user.first_name} {request.user.last_name}".strip() or request.user.email,
            theme='light'
        )
        return Response({
            'success': True,
            'theme': profile.theme
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to get theme preference: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def set_user_theme(request):
    """
    Set the user's theme preference
    """
    try:
        data = json.loads(request.body) if request.body else {}
        theme = data.get('theme')
        
        if theme not in ['light', 'dark']:
            return Response({
                'success': False,
                'error': 'Theme must be either "light" or "dark"'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create user profile
        profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'full_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.email,
                'theme': theme
            }
        )
        
        if not created:
            profile.theme = theme
            profile.save()
        
        return Response({
            'success': True,
            'theme': profile.theme,
            'message': 'Theme preference updated successfully'
        }, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to set theme preference: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ================================
# USER MANAGEMENT API ENDPOINTS (ADMIN ONLY)
# ================================

@api_view(['GET'])
@authentication_classes([SessionValidatedJWTAuthentication])
@permission_classes([IsAuthenticated])
def get_all_users(request):
    """
    Get all users with optional search and pagination (Admin only)
    """
    if not request.user.is_superuser:
        return Response({
            'success': False,
            'error': 'Permission denied. Admin access required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        from django.db.models import Q
        search = request.GET.get('search', '')
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        
        # Base queryset
        users = User.objects.all().order_by('-date_joined')
        
        # Apply search filter
        if search:
            search_words = search.strip().split()
            for word in search_words:
                users = users.filter(
                    Q(email__icontains=word) |
                    Q(first_name__icontains=word) |
                    Q(last_name__icontains=word) |
                    Q(profile__full_name__icontains=word)
                )
        
        # Get total count
        total_users = users.count()
        
        # Apply pagination
        start = (page - 1) * per_page
        end = start + per_page
        users = users[start:end]
        
        # Prepare user data
        users_data = []
        for user in users:
            profile = getattr(user, 'profile', None)
            total_chats = Message.all_objects.filter(conversation__user=user).count()
            total_conversations = Conversation.all_objects.filter(user=user).count()
            
            users_data.append({
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': profile.full_name if profile else f"{user.first_name} {user.last_name}".strip(),
                'is_active': user.is_active,
                'is_superuser': user.is_superuser,
                'date_joined': user.date_joined.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'theme': profile.theme if profile else 'light',
                'total_chats': total_chats,
                'total_conversations': total_conversations
            })
        
        return Response({
            'success': True,
            'users': users_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_users,
                'pages': (total_users + per_page - 1) // per_page
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to fetch users: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_user_admin(request):
    """
    Create a new user (Admin only)
    """
    if not request.user.is_superuser:
        return Response({
            'success': False,
            'error': 'Permission denied. Admin access required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        data = json.loads(request.body)
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        full_name = data.get('full_name', '').strip()
        is_superuser = data.get('is_superuser', False)
        is_active = data.get('is_active', True)
        
        # Validation
        if not email or not password or not full_name:
            return Response({
                'success': False,
                'error': 'Email, password, and full name are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email=email).exists():
            return Response({
                'success': False,
                'error': 'User with this email already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create user
        user = User(
            username=email,
            email=email,
            first_name=full_name.split(' ')[0] if full_name else '',
            last_name=' '.join(full_name.split(' ')[1:]) if len(full_name.split(' ')) > 1 else '',
            is_active=is_active,
            is_superuser=is_superuser,
            is_staff=is_superuser  # Staff status follows superuser status
        )
        user.set_password(password)
        user.save()
        
        # Create or update profile
        UserProfile.objects.get_or_create(
            user=user,
            defaults={'full_name': full_name}
        )
        
        return Response({
            'success': True,
            'message': 'User created successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': full_name,
                'is_active': user.is_active,
                'is_superuser': user.is_superuser
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to create user: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_user_admin(request, user_id):
    """
    Update a user (Admin only)
    """
    if not request.user.is_superuser:
        return Response({
            'success': False,
            'error': 'Permission denied. Admin access required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id)
        data = json.loads(request.body)
        
        # Update user fields
        if 'email' in data:
            new_email = data['email'].strip().lower()
            if new_email != user.email and User.objects.filter(email=new_email).exists():
                return Response({
                    'success': False,
                    'error': 'User with this email already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
            user.email = new_email
            user.username = new_email
        
        if 'full_name' in data:
            full_name = data['full_name'].strip()
            user.first_name = full_name.split(' ')[0] if full_name else ''
            user.last_name = ' '.join(full_name.split(' ')[1:]) if len(full_name.split(' ')) > 1 else ''
            
            # Update profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.full_name = full_name
            profile.save()
        
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        if 'is_superuser' in data:
            user.is_superuser = data['is_superuser']
            user.is_staff = data['is_superuser']  # Staff follows superuser
        
        user.save()
        
        return Response({
            'success': True,
            'message': 'User updated successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.profile.full_name if hasattr(user, 'profile') else f"{user.first_name} {user.last_name}".strip(),
                'is_active': user.is_active,
                'is_superuser': user.is_superuser
            }
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to update user: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_user_admin(request, user_id):
    """
    Delete a user (Admin only)
    """
    if not request.user.is_superuser:
        return Response({
            'success': False,
            'error': 'Permission denied. Admin access required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id)
        
        # Prevent self-deletion
        if user.id == request.user.id:
            return Response({
                'success': False,
                'error': 'Cannot delete your own account'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user_email = user.email
        user.delete()
        
        return Response({
            'success': True,
            'message': f'User {user_email} deleted successfully'
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to delete user: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_user_details_admin(request, user_id):
    """
    Get detailed user information (Admin only)
    """
    if not request.user.is_superuser:
        return Response({
            'success': False,
            'error': 'Permission denied. Admin access required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id)
        profile = getattr(user, 'profile', None)
        
        # Get user statistics (including deleted records for historical totals)
        total_chats = Message.all_objects.filter(conversation__user=user).count()
        total_conversations = Conversation.all_objects.filter(user=user).count()
        recent_conversations = Conversation.objects.filter(user=user).order_by('-updated_at')[:5]
        
        recent_conversations_data = [{
            'id': str(conv.id),
            'title': conv.title,
            'message_count': conv.message_count,
            'created_at': conv.created_at.isoformat(),
            'updated_at': conv.updated_at.isoformat()
        } for conv in recent_conversations]
        
        return Response({
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': profile.full_name if profile else f"{user.first_name} {user.last_name}".strip(),
                'is_active': user.is_active,
                'is_superuser': user.is_superuser,
                'date_joined': user.date_joined.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'theme': profile.theme if profile else 'light',
                'total_chats': total_chats,
                'total_conversations': total_conversations,
                'recent_conversations': recent_conversations_data
            }
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to fetch user details: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@authentication_classes([SessionValidatedJWTAuthentication])
@permission_classes([IsAuthenticated])
def get_admin_analytics(request):
    """
    Get analytics data for admin dashboard
    """
    if not request.user.is_superuser:
        return Response({
            'success': False,
            'error': 'Permission denied. Admin access required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        from django.db.models import Count, Q
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # User statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        superusers = User.objects.filter(is_superuser=True).count()
        users_today = User.objects.filter(date_joined__date=today.date()).count()
        users_this_week = User.objects.filter(date_joined__gte=week_ago).count()
        users_this_month = User.objects.filter(date_joined__gte=month_ago).count()
        
        # Chat statistics (including deleted records for historical totals)
        total_chats = Message.all_objects.count()
        chats_today = Message.all_objects.filter(created_at__date=today.date()).count()
        chats_this_week = Message.all_objects.filter(created_at__gte=week_ago).count()
        chats_this_month = Message.all_objects.filter(created_at__gte=month_ago).count()
        
        # Conversation statistics (including deleted records for historical totals)
        total_conversations = Conversation.all_objects.count()
        conversations_today = Conversation.all_objects.filter(created_at__date=today.date()).count()
        conversations_this_week = Conversation.all_objects.filter(created_at__gte=week_ago).count()
        conversations_this_month = Conversation.all_objects.filter(created_at__gte=month_ago).count()
        
        # Most active users (based on message count from conversations, including deleted)
        from django.db.models import Q, Subquery, OuterRef
        
        # Create a subquery to count all messages (including soft-deleted) for each user
        user_message_counts = Message.all_objects.filter(
            conversation__user=OuterRef('pk')
        ).values('conversation__user').annotate(
            count=Count('id')
        ).values('count')
        
        most_active_users = User.objects.annotate(
            chat_count=Subquery(user_message_counts)
        ).filter(chat_count__gt=0).order_by('-chat_count')[:10]
        
        most_active_data = [{
            'id': user.id,
            'email': user.email,
            'full_name': user.profile.full_name if hasattr(user, 'profile') else f"{user.first_name} {user.last_name}".strip(),
            'chat_count': user.chat_count
        } for user in most_active_users]
        
        # Daily stats for the last 7 days (including deleted records for historical accuracy)
        daily_stats = []
        for i in range(7):
            date = (today - timedelta(days=i)).date()
            daily_stats.append({
                'date': date.isoformat(),
                'users': User.objects.filter(date_joined__date=date).count(),
                'chats': Message.all_objects.filter(created_at__date=date).count(),
                'conversations': Conversation.all_objects.filter(created_at__date=date).count()
            })
        
        return Response({
            'success': True,
            'analytics': {
                'users': {
                    'total': total_users,
                    'active': active_users,
                    'superusers': superusers,
                    'today': users_today,
                    'this_week': users_this_week,
                    'this_month': users_this_month
                },
                'chats': {
                    'total': total_chats,
                    'today': chats_today,
                    'this_week': chats_this_week,
                    'this_month': chats_this_month
                },
                'conversations': {
                    'total': total_conversations,
                    'today': conversations_today,
                    'this_week': conversations_this_week,
                    'this_month': conversations_this_month
                },
                'most_active_users': most_active_data,
                'daily_stats': daily_stats
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to fetch analytics: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@authentication_classes([SessionValidatedJWTAuthentication])
@permission_classes([IsAuthenticated])
def get_active_sessions(request):
    """
    Get all active user sessions across all browsers and devices (Admin only)
    """
    if not request.user.is_superuser:
        return Response({
            'success': False,
            'error': 'Permission denied. Admin access required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        from .models import UserSession
        import socket
        from user_agents import parse
        
        # Comprehensive cleanup of all old sessions
        cleanup_stats = UserSession.cleanup_all_old_sessions()
        
        # Get all truly active sessions
        active_sessions = UserSession.get_active_sessions().select_related('user', 'user__profile')
        
        sessions_data = []
        for session in active_sessions:
            # Parse user agent for device info
            user_agent = parse(session.user_agent or '')
            device_info = f"{user_agent.browser.family} on {user_agent.os.family}"
            if user_agent.device.family != 'Other':
                device_info += f" ({user_agent.device.family})"
            
            # Get location info (basic IP geolocation would go here)
            location = session.location or 'Unknown'
            
            sessions_data.append({
                'id': str(session.id),
                'user_id': session.user.id,
                'email': session.user.email,
                'full_name': session.user.profile.full_name if hasattr(session.user, 'profile') else f"{session.user.first_name} {session.user.last_name}".strip(),
                'is_superuser': session.user.is_superuser,
                'device_info': device_info,
                'ip_address': session.ip_address,
                'location': location,
                'created_at': session.created_at.isoformat(),
                'last_activity': session.last_activity.isoformat(),
                'expires_at': session.expires_at.isoformat()
            })
        
        return Response({
            'success': True,
            'sessions': sessions_data,
            'total_sessions': len(sessions_data),
            'cleanup_stats': cleanup_stats
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to fetch active sessions: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([SessionValidatedJWTAuthentication])
@permission_classes([IsAuthenticated])
def terminate_user_session(request, session_id):
    """
    Terminate a specific user session (Admin only)
    """
    if not request.user.is_superuser:
        return Response({
            'success': False,
            'error': 'Permission denied. Admin access required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        from .models import UserSession
        from django.utils import timezone
        
        # Find the session
        session = UserSession.objects.get(id=session_id, is_active=True)
        session_user_email = session.user.email
        
        # Delete the session immediately instead of marking as inactive
        session.delete()
        
        # Clean up any other inactive sessions for the same user
        UserSession.objects.filter(user__email=session_user_email, is_active=False).delete()
        
        return Response({
            'success': True,
            'message': f'Session for {session_user_email} has been terminated successfully.'
        }, status=status.HTTP_200_OK)
        
    except UserSession.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Session not found or already terminated.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to terminate session: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([SessionValidatedJWTAuthentication])
@permission_classes([IsAuthenticated])
def terminate_all_sessions(request):
    """
    Terminate all active user sessions (Admin only)
    """
    if not request.user.is_superuser:
        return Response({
            'success': False,
            'error': 'Permission denied. Admin access required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        from .models import UserSession
        
        # Get count before termination
        active_count = UserSession.objects.filter(is_active=True).count()
        
        # Delete all sessions (both active and inactive)
        total_deleted = UserSession.objects.all().delete()[0]
        
        return Response({
            'success': True,
            'message': f'All {active_count} active sessions have been terminated successfully. Total {total_deleted} sessions removed from database.'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to terminate all sessions: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([SessionValidatedJWTAuthentication])
@permission_classes([IsAuthenticated])
def session_heartbeat(request):
    """
    Keep user session alive by updating last activity
    """
    try:
        from .models import UserSession
        from django.utils import timezone
        
        user = request.user
        
        # Get request metadata
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
        if ip_address:
            ip_address = ip_address.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Find and update the current session
        current_session = UserSession.objects.filter(
            user=user,
            is_active=True,
            ip_address=ip_address,
            user_agent=user_agent
        ).order_by('-last_activity').first()
        
        if current_session:
            current_session.mark_active()
            
            return Response({
                'success': True,
                'message': 'Session heartbeat updated',
                'last_activity': current_session.last_activity.isoformat()
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': 'No active session found'
            }, status=status.HTTP_404_NOT_FOUND)
            
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to update session heartbeat: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ChatbotSingleton:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = GroqChatbot()
        return cls._instance

# Whisper singleton removed - using real-time services only
# class WhisperSingleton:
#     _instance = None
#     
#     @classmethod
#     def get_instance(cls, model_size="small"):
#         if cls._instance is None:
#             cls._instance = LocalWhisperService(model_size)
#         return cls._instance

def get_chat_suggestions(user_message="", response=""):
    """
    Generate contextual chat suggestions based on user message and response
    """
    # Default suggestions for general university inquiries
    default_suggestions = [
        "Tell me about APU's undergraduate programs",
        "What are the admission requirements?",
        "Can you help with course consultation?",
        "What scholarships are available?",
        "Tell me about campus facilities"
    ]
    
    # Course and program related suggestions
    program_suggestions = [
        "What computing programs do you offer?",
        "Tell me about business programs",
        "What engineering courses are available?",
        "Information about design programs",
        "Dual degree options at APU"
    ]
    
    # Admission and application suggestions
    admission_suggestions = [
        "How do I apply to APU?",
        "What documents do I need for application?",
        "When is the application deadline?",
        "What are the entry requirements?",
        "Can you help with the application process?"
    ]
    
    # FAQ suggestions
    faq_suggestions = [
        "What is APU's ranking?",
        "Where is APU located?",
        "What are the tuition fees?",
        "Course fees for international students",
        "Course fees for domestic students",
        "Do you have student accommodation?",
        "What industry partnerships does APU have?"
    ]
    
    # Campus life suggestions
    campus_suggestions = [
        "Tell me about student life at APU",
        "What clubs and societies are available?",
        "What facilities does the campus have?",
        "Information about student support services",
        "What recreational activities are available?"
    ]
    
    # Career and placement suggestions
    career_suggestions = [
        "What career support does APU provide?",
        "Tell me about job placement rates",
        "What companies recruit from APU?",
        "Information about internship programs",
        "How does APU help with career development?"
    ]
    
    # Contextual suggestion selection based on keywords in user message and response
    user_msg_lower = user_message.lower()
    response_lower = response.lower()
    
    suggestions = []
    
    # Check for specific contexts and provide relevant suggestions
    if any(keyword in user_msg_lower for keyword in ['program', 'course', 'study', 'major', 'degree']):
        suggestions.extend(program_suggestions[:3])
    elif any(keyword in user_msg_lower for keyword in ['apply', 'admission', 'entry', 'requirement']):
        suggestions.extend(admission_suggestions[:3])
    elif any(keyword in user_msg_lower for keyword in ['campus', 'facility', 'life', 'student']):
        suggestions.extend(campus_suggestions[:3])
    elif any(keyword in user_msg_lower for keyword in ['career', 'job', 'placement', 'internship']):
        suggestions.extend(career_suggestions[:3])
    elif any(keyword in user_msg_lower for keyword in ['fee', 'cost', 'scholarship', 'financial']):
        suggestions.extend(faq_suggestions[:3])
    elif any(keyword in user_msg_lower for keyword in ['hello', 'hi', 'start', 'help']) or not user_message.strip():
        # First-time users or greetings - show diverse options
        suggestions = [
            "Tell me about APU's programs",
            "Help me choose the right course",
            "What are the admission requirements?",
            "Information about scholarships and fees",
            "Tell me about campus life"
        ]
    else:
        # Default mix of suggestions for general inquiries
        suggestions = [
            "Tell me about APU's undergraduate programs",
            "What are the admission requirements?",
            "Help me with course consultation",
            "What scholarships are available?",
            "Information about campus facilities"
        ]
    
    # Ensure we have exactly 5 suggestions and they're unique
    all_available = default_suggestions + program_suggestions + admission_suggestions + faq_suggestions + campus_suggestions + career_suggestions
    
    # Remove duplicates while maintaining order
    seen = set()
    unique_suggestions = []
    for suggestion in suggestions:
        if suggestion not in seen:
            unique_suggestions.append(suggestion)
            seen.add(suggestion)
    
    # Fill up to 5 suggestions if needed
    while len(unique_suggestions) < 5:
        for suggestion in all_available:
            if suggestion not in seen:
                unique_suggestions.append(suggestion)
                seen.add(suggestion)
                if len(unique_suggestions) >= 5:
                    break
    
    return unique_suggestions[:5]

@api_view(['GET'])
@authentication_classes([SessionValidatedJWTAuthentication])
@permission_classes([IsAuthenticated])
def get_chat_history(request):
    """
    Get chat history for the authenticated user
    """
    try:
        chat_history = ChatHistory.objects.filter(user=request.user).order_by('timestamp')
        
        history_data = [{
            'id': chat.id,
            'message': chat.message,
            'response': chat.response,
            'timestamp': chat.timestamp.isoformat()
        } for chat in chat_history]
        
        return Response({
            'success': True,
            'chat_history': history_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to fetch chat history: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([SessionAuthentication, JWTAuthentication, SessionValidatedJWTAuthentication])
@permission_classes([IsAuthenticated])
def chat_endpoint(request):
    """
    Handle chat messages and store them in conversations for authenticated users
    """
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
        conversation_id = data.get('conversation_id')  # Optional conversation ID
        
        if not user_message:
            return Response({
                'success': False,
                'error': 'Message is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get chatbot instance
        chatbot = ChatbotSingleton.get_instance()
        
        # Get response from chatbot
        response = chatbot.get_response(user_message)
        
        # Get suggestions for the next message
        suggestions = get_chat_suggestions(user_message, response)
        
        conversation = None
        # Store messages in conversation if user is authenticated
        if request.user.is_authenticated:
            try:
                # If conversation_id is provided, verify it belongs to the user
                if conversation_id:
                    conversation = Conversation.objects.get(id=conversation_id, user=request.user)
                else:
                    # Create a new conversation
                    # Generate title from first user message (first 30 characters)
                    title = user_message[:30] + "..." if len(user_message) > 30 else user_message
                    conversation = Conversation.objects.create(
                        user=request.user,
                        title=title
                    )
                
                # Save user message
                Message.objects.create(
                    conversation=conversation,
                    content=user_message,
                    sender='user'
                )
                
                # Save assistant response
                Message.objects.create(
                    conversation=conversation,
                    content=response,
                    sender='assistant'
                )
                
                # Update conversation's updated_at timestamp
                conversation.save()
                
            except Conversation.DoesNotExist:
                # If conversation doesn't exist or doesn't belong to user,
                # create a new one
                title = user_message[:30] + "..." if len(user_message) > 30 else user_message
                conversation = Conversation.objects.create(
                    user=request.user,
                    title=title
                )
                
                # Save user message
                Message.objects.create(
                    conversation=conversation,
                    content=user_message,
                    sender='user'
                )
                
                # Save assistant response
                Message.objects.create(
                    conversation=conversation,
                    content=response,
                    sender='assistant'
                )
        
        response_data = {
            'success': True,
            'response': response,
            'suggestions': suggestions
        }
        
        # Include conversation ID in response if user is authenticated
        if conversation:
            response_data['conversation_id'] = str(conversation.id)
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@require_http_methods(["POST"])
def transcribe_audio(request):
    print("=" * 50)
    print("🎙️ TRANSCRIBE_AUDIO REQUEST RECEIVED")
    print("=" * 50)
    try:
        if 'audio' not in request.FILES:
            print("❌ No audio file provided in request")
            return JsonResponse({'error': 'No audio file provided'}, status=400)
        
        audio_file = request.FILES['audio']
        print(f"Received audio file: {audio_file.name}, size: {audio_file.size} bytes")
        
        # Get parameters
        model_size = request.POST.get('model_size', 'small')
        language = request.POST.get('language', None)
        service_name = request.POST.get('service', None)  # Allow service selection
        
        # Create temporary files for the uploaded audio and converted audio
        temp_filename = f"temp_audio_{uuid.uuid4()}"
        original_path = os.path.join(settings.MEDIA_ROOT, f"{temp_filename}_original")
        converted_path = os.path.join(settings.MEDIA_ROOT, f"{temp_filename}.wav")
        
        # Ensure the media directory exists
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        
        # Save the original uploaded file
        with open(original_path, 'wb+') as destination:
            for chunk in audio_file.chunks():
                destination.write(chunk)
        
        print(f"Original audio file saved to: {original_path}")
        
        # Convert audio to WAV format for SpeechRecognition library
        try:
            from pydub import AudioSegment
            print(f"Converting audio from {audio_file.name} to WAV format...")
            
            # Detect file format and convert to WAV
            if audio_file.name.endswith('.webm') or 'webm' in str(audio_file.content_type):
                # WebM format
                audio = AudioSegment.from_file(original_path, format="webm")
            elif audio_file.name.endswith('.mp4') or audio_file.name.endswith('.m4a'):
                # MP4/M4A format
                audio = AudioSegment.from_file(original_path, format="mp4")
            elif audio_file.name.endswith('.ogg'):
                # OGG format
                audio = AudioSegment.from_file(original_path, format="ogg")
            elif audio_file.name.endswith('.wav'):
                # Already WAV, just copy
                audio = AudioSegment.from_wav(original_path)
            else:
                # Try to auto-detect format
                audio = AudioSegment.from_file(original_path)
            
            # Convert to mono, 16kHz (optimal for speech recognition)
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(16000)
            audio = audio.set_sample_width(2)  # 16-bit
            
            # Export as WAV
            audio.export(converted_path, format="wav")
            print(f"Audio converted and saved to: {converted_path}")
            
            # Use the converted WAV file
            temp_path = converted_path
            print(f"✅ Audio conversion successful!")
            print(f"   Original file: {original_path} ({os.path.getsize(original_path)} bytes)")
            print(f"   Converted file: {converted_path} ({os.path.getsize(converted_path)} bytes)")
            print(f"   Will use converted file for transcription: {temp_path}")
            
        except Exception as e:
            print(f"❌ Audio conversion failed: {e}")
            print("Trying to use original file directly...")
            temp_path = original_path
            print(f"   Will use original file: {temp_path}")
        
        print(f"Audio file saved to: {temp_path}")
        
        # Use real-time speech services (no Whisper fallback)
        print(f"Attempting transcription with real-time service: {service_name or 'auto'}")
        
        # Use async to await the real-time service
        import asyncio
        try:
            result = asyncio.run(realtime_speech_service.transcribe_audio_file(temp_path, service_name))
            
            if result.get('success', False):
                transcription_text = result['transcription']
                confidence = result.get('confidence', 0.8)
                detected_language = result.get('detected_language', 'en-US')
                engine = result.get('engine', 'unknown')
                
                print(f"Real-time transcription successful ({engine}): {transcription_text}")
                print(f"Confidence score: {confidence:.2f}")
                
                # Generate chatbot response
                chatbot = ChatbotSingleton.get_instance()
                print("Generating response...")
                response = chatbot.get_response(transcription_text)
                print(f"Response generated: {response}")
                
                # Generate contextual suggestions
                suggestions = get_chat_suggestions(transcription_text, response)
                
                # Clean up the temporary files
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    if 'original_path' in locals() and os.path.exists(original_path):
                        os.remove(original_path)
                    print("Temporary files cleaned up")
                except Exception as cleanup_error:
                    print(f"Cleanup error: {cleanup_error}")
                
                return JsonResponse({
                    'transcription': transcription_text,
                    'response': response,
                    'suggestions': suggestions,
                    'detected_language': detected_language,
                    'confidence': confidence,
                    'service_used': engine,
                    'success': True
                })
            else:
                error_msg = result.get('error', 'Unknown transcription error')
                print(f"Real-time service failed: {error_msg}")
                
                # Clean up temp files
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    if 'original_path' in locals() and os.path.exists(original_path):
                        os.remove(original_path)
                except Exception as cleanup_error:
                    print(f"Cleanup error: {cleanup_error}")
                
                return JsonResponse({
                    'error': f'Speech recognition failed: {error_msg}',
                    'success': False,
                    'service_attempted': service_name or 'auto',
                    'suggestion': 'Try speaking more clearly or check your microphone. You can also type your message instead.'
                }, status=400)
                
        except Exception as e:
            print(f"Real-time service error: {e}")
            
            # Clean up temp files
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                if 'original_path' in locals() and os.path.exists(original_path):
                    os.remove(original_path)
            except Exception as cleanup_error:
                print(f"Cleanup error: {cleanup_error}")
            
            return JsonResponse({
                'error': f'Speech recognition service error: {str(e)}',
                'success': False,
                'suggestion': 'Speech recognition is temporarily unavailable. Please type your message instead.'
            }, status=500)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in transcribe_audio: {str(e)}")
        print(f"Error details: {error_details}")
        
        # Clean up temp files in case of error
        try:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
            if 'original_path' in locals() and os.path.exists(original_path):
                os.remove(original_path)
        except Exception as cleanup_error:
            print(f"Error cleanup failed: {cleanup_error}")
            
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def text_to_speech(request):
    """
    Endpoint to convert text to speech using Groq's text-to-speech API
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    try:
        data = json.loads(request.body)
        text = data.get('text', '')
        
        if not text:
            return JsonResponse({'error': 'No text provided'}, status=400)
        
        # The TTS API implementation would go here when Groq releases their TTS API
        # Currently, Groq doesn't have a public TTS API, so we'll return an informational message
        
        return JsonResponse({
            'status': 'info',
            'message': 'Groq TTS API integration is pending. Groq has mentioned TTS in their documentation but has not yet released the API. Using Web Speech API as fallback.'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def upload_file(request):
    """
    Endpoint to handle file uploads (both photos and other files)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)
    
    file = request.FILES['file']
    file_type = request.POST.get('type', 'file')  # 'photo' or 'file'
    
    try:
        # Generate a unique filename
        ext = os.path.splitext(file.name)[1]
        filename = f"{uuid.uuid4()}{ext}"
        
        # Create appropriate directory based on file type
        if file_type == 'photo':
            path = f'uploads/photos/{filename}'
        else:
            path = f'uploads/files/{filename}'
        
        # Save the file
        path = default_storage.save(path, ContentFile(file.read()))
        url = default_storage.url(path)
        
        return JsonResponse({
            'status': 'success',
            'url': url,
            'filename': file.name,
            'type': file_type
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def start_recording(request):
    """Start microphone recording - deprecated, use browser Web Speech API instead"""
    return JsonResponse({
        'error': 'Server-side recording deprecated. Use browser Web Speech API instead.',
        'suggestion': 'Click the microphone button in the chat interface for real-time speech recognition.'
    }, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def stop_recording(request):
    """Stop microphone recording - deprecated, use browser Web Speech API instead"""
    return JsonResponse({
        'error': 'Server-side recording deprecated. Use browser Web Speech API instead.',
        'suggestion': 'Use the microphone button in the chat interface for real-time speech recognition.'
    }, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def transcribe_from_mic(request):
    """Record from microphone - deprecated, use browser Web Speech API instead"""
    return JsonResponse({
        'error': 'Server-side microphone recording deprecated. Use browser Web Speech API instead.',
        'suggestion': 'Use the microphone button in the chat interface for real-time speech recognition.'
    }, status=400)

@csrf_exempt
@require_http_methods(["GET"])
def recording_status(request):
    """Get current recording status - deprecated"""
    return JsonResponse({
        'error': 'Server-side recording deprecated. Use browser Web Speech API instead.',
        'suggestion': 'Use the microphone button in the chat interface for real-time speech recognition.'
    }, status=400)

@login_required
def user_dashboard(request):
    """Dashboard for regular users showing their conversations"""
    user = request.user
    conversations = Conversation.objects.filter(user=user).order_by('-updated_at')
    user_messages = Message.objects.filter(conversation__user=user)
    
    # Get user stats (including deleted records for historical totals)
    user_messages_all = Message.all_objects.filter(conversation__user=user)
    total_chats = user_messages_all.count()
    chats_today = user_messages_all.filter(created_at__date=timezone.now().date()).count()
    chats_this_week = user_messages_all.filter(created_at__gte=timezone.now() - timedelta(days=7)).count()
    
    context = {
        'user_profile': user.profile,
        'conversations': conversations,
        'total_chats': total_chats,
        'chats_today': chats_today,
        'chats_this_week': chats_this_week,
    }
    return render(request, 'chatbot/user_dashboard.html', context)

def user_chat(request, user_id=None):
    """
    Render chat page with token-based authentication for iframe embedding
    """
    user = None
    
    # Check for token in URL parameters (for iframe embedding)
    token = request.GET.get('token')
    if token:
        try:
            from rest_framework_simplejwt.tokens import UntypedToken
            from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
            from django.contrib.auth.models import User
            import jwt
            from django.conf import settings
            
            # Validate the token
            UntypedToken(token)
            
            # Decode the token to get user info
            decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = decoded_token.get('user_id')
            user = User.objects.get(id=user_id)
            
        except (InvalidToken, TokenError, User.DoesNotExist, jwt.InvalidTokenError):
            # If token is invalid, show login required message
            return render(request, 'chatbot/chat.html', {
                'auth_required': True,
                'error': 'Invalid authentication token. Please log in again.'
            })
    else:
        # Fallback to session-based authentication
        if not request.user.is_authenticated:
            return render(request, 'chatbot/chat.html', {
                'auth_required': True,
                'error': 'Authentication required. Please log in.'
            })
        user = request.user
        user_id = user.id
    
    # If we have a user_id parameter and it doesn't match, check permissions
    if user_id and int(user_id) != user.id and not user.is_superuser:
        raise Http404("Chat not found")
    
    # Get user's conversations
    conversations = Conversation.objects.filter(user=user).order_by('-updated_at')
    
    return render(request, 'chatbot/chat.html', {
        'conversations': conversations,
        'user_id': user.id,
        'user': user,
        'auth_required': False
    })

def avatar_test(request):
    """
    View for testing avatar animations
    """
    return render(request, 'chatbot/avatar_test.html')

def is_superuser(user):
    return user.is_superuser

@user_passes_test(is_superuser)
def admin_dashboard(request):
    """Analytics dashboard for superusers"""
    # User Statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    superusers = User.objects.filter(is_superuser=True).count()
    
    # Chat Statistics (including deleted records for historical totals)
    total_chats = Message.all_objects.count()
    today = timezone.now()
    chats_today = Message.all_objects.filter(
        created_at__date=today.date()
    ).count()
    chats_this_week = Message.all_objects.filter(
        created_at__gte=today - timedelta(days=7)
    ).count()
    
    # Most Active Users (based on message count from conversations, including deleted)
    from django.db.models import Subquery, OuterRef
    
    # Create a subquery to count all messages (including soft-deleted) for each user
    user_message_counts = Message.all_objects.filter(
        conversation__user=OuterRef('pk')
    ).values('conversation__user').annotate(
        count=Count('id')
    ).values('count')
    
    most_active_users = User.objects.annotate(
        chat_count=Subquery(user_message_counts)
    ).filter(chat_count__gt=0).order_by('-chat_count')[:5]
    
    most_active_users_data = []
    for user in most_active_users:
        profile = getattr(user, 'profile', None)
        most_active_users_data.append({
            'user__username': user.username,
            'user__email': user.email,
            'user__profile__full_name': profile.full_name if profile else f"{user.first_name} {user.last_name}".strip(),
            'chat_count': user.chat_count
        })
    
    # All Users with their recent conversations
    users = User.objects.all().order_by('-date_joined')
    user_data = []
    for user in users:
        recent_conversations = Conversation.objects.filter(user=user).order_by('-updated_at')[:5]
        user_data.append({
            'user': user,
            'profile': user.profile,
            'recent_conversations': recent_conversations,
            'total_chats': Message.all_objects.filter(conversation__user=user).count()
        })
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'superusers': superusers,
        'total_chats': total_chats,
        'chats_today': chats_today,
        'chats_this_week': chats_this_week,
        'most_active_users': most_active_users_data,
        'user_data': user_data,
    }
    return render(request, 'chatbot/admin_dashboard.html', context)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def debug_soft_delete(request):
    """
    Debug view to test soft delete functionality (Admin only)
    """
    if not request.user.is_superuser:
        return Response({
            'success': False,
            'error': 'Permission denied. Admin access required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Get counts for debugging
        total_conversations = Conversation.all_objects.count()
        active_conversations = Conversation.objects.count()
        deleted_conversations = Conversation.all_objects.filter(deleted_at__isnull=False).count()
        
        total_messages = Message.all_objects.count()
        active_messages = Message.objects.count()
        deleted_messages = Message.all_objects.filter(deleted_at__isnull=False).count()
        
        # Get some sample data
        sample_deleted_conversations = Conversation.all_objects.filter(deleted_at__isnull=False)[:5]
        sample_deleted_messages = Message.all_objects.filter(deleted_at__isnull=False)[:5]
        
        debug_data = {
            'conversations': {
                'total': total_conversations,
                'active': active_conversations,
                'deleted': deleted_conversations,
                'sample_deleted': [{
                    'id': str(conv.id),
                    'title': conv.title,
                    'deleted_at': conv.deleted_at.isoformat() if conv.deleted_at else None,
                    'user_email': conv.user.email
                } for conv in sample_deleted_conversations]
            },
            'messages': {
                'total': total_messages,
                'active': active_messages,
                'deleted': deleted_messages,
                'sample_deleted': [{
                    'id': str(msg.id),
                    'content': msg.content[:50] + '...' if len(msg.content) > 50 else msg.content,
                    'sender': msg.sender,
                    'deleted_at': msg.deleted_at.isoformat() if msg.deleted_at else None,
                    'conversation_id': str(msg.conversation.id)
                } for msg in sample_deleted_messages]
            }
        }
        
        return Response({
            'success': True,
            'debug_data': debug_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Debug failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

