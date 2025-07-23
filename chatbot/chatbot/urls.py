from django.urls import path
from django.contrib.auth.decorators import login_required
from django.views.generic import RedirectView
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Main pages
    path('', views.index, name='index'),
    path('chat/', views.user_chat, name='chat'),  # For iframe embedding with token
    path('chat/<int:user_id>/', views.user_chat, name='user_chat'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Authentication endpoints
    path('api/auth/login/', views.login_user, name='login'),
    path('api/auth/login/', views.login_user, name='login-slash'),
    path('accounts/login/', RedirectView.as_view(url='/api/auth/login/', permanent=True), name='account-login'),
    
    path('api/auth/register/', views.register_user, name='register'),
    path('api/auth/register/', views.register_user, name='register-slash'),
    
    path('api/auth/logout/', views.logout_user, name='logout'),
    path('api/auth/logout/', views.logout_user, name='logout-slash'),
    
    path('api/auth/verify/', views.verify_token, name='verify-token'),  # JWT token verification
    path('api/auth/status/', views.check_auth_status, name='auth-status'),
    path('api/auth/status/', views.check_auth_status, name='auth-status-slash'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Chat endpoints
    path('api/chat/history/', views.get_chat_history, name='chat_history'),
    path('api/chat/', views.chat_endpoint, name='chat'),
    
    # Conversation management endpoints
    path('api/conversations/', views.get_conversations, name='get_conversations'),
    path('api/conversations/create/', views.create_conversation, name='create_conversation'),
    path('api/conversations/<uuid:conversation_id>/', views.get_conversation_messages, name='get_conversation_messages'),
    path('api/conversations/<uuid:conversation_id>/rename/', views.rename_conversation, name='rename_conversation'),
    path('api/conversations/<uuid:conversation_id>/delete/', views.delete_conversation, name='delete_conversation'),
    
    # User preference endpoints
    path('api/user/theme/', views.get_user_theme, name='get_user_theme'),
    path('api/user/theme/set/', views.set_user_theme, name='set_user_theme'),
    
    # Admin user management endpoints
    path('api/admin/users/', views.get_all_users, name='get_all_users'),
    path('api/admin/users/create/', views.create_user_admin, name='create_user_admin'),
    path('api/admin/users/<int:user_id>/', views.get_user_details_admin, name='get_user_details_admin'),
    path('api/admin/users/<int:user_id>/update/', views.update_user_admin, name='update_user_admin'),
    path('api/admin/users/<int:user_id>/delete/', views.delete_user_admin, name='delete_user_admin'),
    path('api/admin/analytics/', views.get_admin_analytics, name='get_admin_analytics'),
    
    # Admin session management endpoints
    path('api/admin/sessions/', views.get_active_sessions, name='get_active_sessions'),
    path('api/admin/sessions/<uuid:session_id>/terminate/', views.terminate_user_session, name='terminate_user_session'),
    path('api/admin/sessions/terminate-all/', views.terminate_all_sessions, name='terminate_all_sessions'),
    
    # Debug endpoint
    path('api/admin/debug/soft-delete/', views.debug_soft_delete, name='debug_soft_delete'),
    
    # Session heartbeat endpoint
    path('api/auth/heartbeat/', views.session_heartbeat, name='session_heartbeat'),
    
    # API endpoints
    path('api/transcribe/', views.transcribe_audio, name='transcribe-endpoint'),
    path('api/tts/', views.text_to_speech, name='tts-endpoint'),
    path('api/upload/', views.upload_file, name='upload-endpoint'),
    path('api/start-recording/', views.start_recording, name='start-recording'),
    path('api/stop-recording/', views.stop_recording, name='stop-recording'),
    path('api/transcribe-from-mic/', views.transcribe_from_mic, name='transcribe-from-mic'),
    path('api/recording-status/', views.recording_status, name='recording-status'),
] 