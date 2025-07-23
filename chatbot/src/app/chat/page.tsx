'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { LogOut, User, Loader2 } from 'lucide-react'
import { multiUserAuth, UserData } from '../../lib/multiUserAuth'

interface User {
    id: number
    email: string
    full_name: string
    is_authenticated: boolean
}

export default function ChatPage() {
    const router = useRouter()
    const [user, setUser] = useState<User | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [iframeLoaded, setIframeLoaded] = useState(false)

    useEffect(() => {
        const checkAuth = async () => {
            // Get current user's token from multi-user auth system
            const tokens = multiUserAuth.getCurrentUserTokens()
            const currentUserData = multiUserAuth.getCurrentUserData()

            if (!tokens || !tokens.access) {
                router.push('/')
                return
            }

            try {
                // Verify token with Django backend
                const response = await fetch('http://localhost:8000/api/auth/verify/', {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${tokens.access}`,
                        'Content-Type': 'application/json',
                    }
                })

                if (response.ok) {
                    const userData = await response.json()
                    setUser(userData.user)

                    // Apply user's theme preference to the Next.js page AND store for iframe
                    const userTheme = userData.user.theme || 'light'
                    document.body.setAttribute('data-theme', userTheme)

                    // Store theme for iframe communication
                    sessionStorage.setItem('user_theme', userTheme)
                } else {
                    // Token is invalid, remove this user's session and redirect to login
                    if (currentUserData) {
                        multiUserAuth.removeUserSession(currentUserData.id.toString())
                    }
                    router.push('/')
                    return
                }
            } catch (error) {
                console.error('Auth verification failed:', error)
                // If verification fails, still allow access but show warning
                setUser({
                    id: 0,
                    email: 'Unknown',
                    full_name: 'User',
                    is_authenticated: true
                })
            }

            setIsLoading(false)
        }

        checkAuth()
    }, [router])

    const handleLogout = async () => {
        try {
            const tokens = multiUserAuth.getCurrentUserTokens()
            const currentUserData = multiUserAuth.getCurrentUserData()

            if (tokens?.access) {
                // Call Django logout API to invalidate JWT token
                await fetch('http://localhost:8000/api/auth/logout/', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${tokens.access}`,
                        'Content-Type': 'application/json',
                    }
                })
            }

            // Remove current user's session from multi-user auth system
            if (currentUserData) {
                multiUserAuth.removeUserSession(currentUserData.id.toString())
            }
        } catch (error) {
            console.error('Logout error:', error)
        } finally {
            sessionStorage.removeItem('user_theme')  // Clear theme data

            // Check if there are other active sessions
            if (multiUserAuth.getSessionCount() > 0) {
                // Stay on chat page but reload to switch to another user
                window.location.reload()
            } else {
                // No other sessions, redirect to homepage
                router.push('/')
            }
        }
    }

    const handleIframeLoad = () => {
        setIframeLoaded(true)
        console.log('Chatbot iframe loaded successfully')

        // Send iframe size information to Django template
        const iframe = document.getElementById('chatbot-iframe') as HTMLIFrameElement
        if (iframe && iframe.contentWindow) {
            const sendSizeInfo = () => {
                const message = {
                    type: 'VIEWPORT_SIZE',
                    width: window.innerWidth,
                    height: window.innerHeight,
                    isMobile: window.innerWidth <= 640,
                    isTablet: window.innerWidth > 640 && window.innerWidth <= 1024
                }
                iframe.contentWindow?.postMessage(message, 'http://localhost:8000')
            }

            // Send initial size
            setTimeout(sendSizeInfo, 100)

            // Set up resize handler
            const handleResize = () => {
                sendSizeInfo()
            }

            window.addEventListener('resize', handleResize)
        }
    }

    // Set up iframe communication
    useEffect(() => {
        const handleIframeMessage = (event: MessageEvent) => {
            if (event.origin !== 'http://localhost:8000') {
                return
            }

            if (event.data?.type === 'IFRAME_READY') {
                // Send authentication data when iframe is ready
                const iframe = document.getElementById('chatbot-iframe') as HTMLIFrameElement
                const tokens = multiUserAuth.getCurrentUserTokens()
                const userTheme = sessionStorage.getItem('user_theme') || 'light'

                if (iframe && iframe.contentWindow && tokens?.access) {
                    iframe.contentWindow.postMessage({
                        type: 'AUTH_TOKEN',
                        token: tokens.access,
                        user: user,
                        theme: userTheme  // Explicitly send theme data
                    }, 'http://localhost:8000')
                }
            } else if (event.data?.type === 'LOGOUT_SUCCESS') {
                // Handle logout initiated from iframe
                const currentUserData = multiUserAuth.getCurrentUserData()
                if (currentUserData) {
                    multiUserAuth.removeUserSession(currentUserData.id.toString())
                }
                sessionStorage.removeItem('user_theme')  // Clear theme data

                // Check if there are other active sessions
                if (multiUserAuth.getSessionCount() > 0) {
                    // Stay on chat page but reload to switch to another user
                    window.location.reload()
                } else {
                    // No other sessions, redirect to homepage
                    router.push('/')
                }
            } else if (event.data?.type === 'THEME_CHANGED') {
                // Handle theme changes from iframe
                const newTheme = event.data.theme
                if (newTheme && (newTheme === 'light' || newTheme === 'dark')) {
                    document.body.setAttribute('data-theme', newTheme)
                    sessionStorage.setItem('user_theme', newTheme)
                }
            }
        }

        // Add event listener for iframe messages
        window.addEventListener('message', handleIframeMessage)

        // Clean up event listener on component unmount
        return () => {
            window.removeEventListener('message', handleIframeMessage)
        }
    }, [user, router])

    if (isLoading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 flex items-center justify-center">
                <div className="text-center">
                    <Loader2 className="w-12 h-12 animate-spin text-blue-600 mx-auto mb-4" />
                    <p className="text-gray-600">Authenticating...</p>
                </div>
            </div>
        )
    }

    const tokens = multiUserAuth.getCurrentUserTokens()
    const chatbotUrl = `http://localhost:8000/?token=${encodeURIComponent(tokens?.access || '')}`

    return (
        <div className="min-h-screen bg-white">
            {/* Main Content - Embedded Chatbot (Full Screen) */}
            <div className="relative">
                {/* Loading overlay */}
                {!iframeLoaded && (
                    <div className="absolute inset-0 bg-white flex items-center justify-center z-20">
                        <div className="text-center">
                            <img
                                src="/images/gigi-avatar.png"
                                alt="Gigi AI"
                                className="w-16 h-16 rounded-full mx-auto mb-4 border-2 border-blue-600/20"
                                onError={(e) => {
                                    e.currentTarget.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHZpZXdCb3g9IjAgMCA2NCA2NCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMzIiIGN5PSIzMiIgcj0iMzIiIGZpbGw9IiM2MzY2RjEiLz4KPGNpcmNsZSBjeD0iMzIiIGN5PSIyNiIgcj0iMTAiIGZpbGw9IndoaXRlIi8+CjxwYXRoIGQ9Ik0xNiA1MkMxNiA0NC4xIDIyLjUgNDAiIDMyIDQwUzQ4IDQ0LjEgNDggNTIiIGZpbGw9IndoaXRlIi8+Cjwvc3ZnPgo='
                                }}
                            />
                            <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-2" />
                            <p className="text-gray-600 font-medium">Loading Gigi AI...</p>
                            <p className="text-sm text-gray-500">Your Educational Counselor</p>
                        </div>
                    </div>
                )}

                {/* Embedded Django Chatbot - Full Screen Responsive */}
                <iframe
                    id="chatbot-iframe"
                    src={chatbotUrl}
                    className="w-full border-0 responsive-iframe"
                    style={{
                        height: '100vh',
                        minHeight: '100vh',
                        maxWidth: '100vw'
                    }}
                    onLoad={handleIframeLoad}
                    allow="camera; microphone; fullscreen"
                    title="Gigi AI Chatbot"
                />

                {/* User info and logout - bottom left corner */}
                {/* <div className="fixed bottom-4 left-4 z-30 bg-white/90 backdrop-blur-sm border border-gray-200 rounded-lg px-3 py-2 shadow-lg">
                    <div className="flex items-center space-x-3">
                        <div className="flex items-center space-x-2">
                            <User className="w-4 h-4 text-gray-600" />
                            <span className="text-sm text-gray-700 font-medium">
                                {user?.full_name || 'User'}
                            </span>
                        </div>
                        <button
                            onClick={handleLogout}
                            className="flex items-center space-x-1 px-2 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600 transition-colors duration-200"
                            title="Logout and return to homepage"
                        >
                            <LogOut className="w-3 h-3" />
                            <span>Logout</span>
                        </button>
                    </div>
                </div> */}
            </div>
        </div>
    )
}
