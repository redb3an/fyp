'use client'

import React, { useState, useEffect } from 'react'
import { X, Mail, Lock, Eye, EyeOff, AlertCircle, CheckCircle } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { multiUserAuth, UserData, AuthTokens } from '../../lib/multiUserAuth'

interface LoginModalProps {
    isOpen: boolean
    onClose: () => void
    onSwitchToRegister: () => void
}

// ForgotPasswordModal component
function ForgotPasswordModal({ isOpen, onClose }: { isOpen: boolean, onClose: () => void }) {
    const [email, setEmail] = useState('')
    const [loading, setLoading] = useState(false)
    const [success, setSuccess] = useState(false)
    const [error, setError] = useState('')

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError('')
        setSuccess(false)
        try {
            const response = await fetch('http://127.0.0.1:8000/api/auth/forgot-password/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            })
            const data = await response.json()
            if (data.success) {
                setSuccess(true)
            } else {
                setError(data.error || 'Failed to send reset email.')
            }
        } catch (err: any) {
            setError('Unable to connect to server. Please try again.')
        } finally {
            setLoading(false)
        }
    }

    if (!isOpen) return null
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="bg-white rounded-3xl shadow-2xl w-full max-w-md p-8 relative">
                <button onClick={onClose} className="absolute top-6 right-6 text-gray-400 hover:text-gray-600 transition-colors duration-200">
                    <span className="text-xl">&times;</span>
                </button>
                <h2 className="text-2xl font-bold mb-4 text-center">Forgot Password</h2>
                {success ? (
                    <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-xl text-green-800 text-center">
                        If the email exists, a reset link has been sent.
                    </div>
                ) : (
                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-2">Email Address</label>
                            <input
                                type="email"
                                value={email}
                                onChange={e => setEmail(e.target.value)}
                                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-lg text-gray-900"
                                placeholder="Enter your email"
                                required
                                disabled={loading}
                            />
                        </div>
                        {error && <div className="text-red-600 text-sm text-center">{error}</div>}
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-all font-semibold text-lg"
                        >
                            {loading ? 'Sending...' : 'Send Reset Link'}
                        </button>
                    </form>
                )}
            </div>
        </div>
    )
}

export default function LoginModal({ isOpen, onClose, onSwitchToRegister }: LoginModalProps) {
    const router = useRouter()
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [showPassword, setShowPassword] = useState(false)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [success, setSuccess] = useState(false)
    const [showForgotPassword, setShowForgotPassword] = useState(false)

    // Reset form when modal opens/closes
    useEffect(() => {
        if (isOpen) {
            setError('')
            setSuccess(false)
        } else {
            // Reset form when modal closes
            setTimeout(() => {
                setEmail('')
                setPassword('')
                setShowPassword(false)
                setError('')
                setSuccess(false)
            }, 300) // Wait for closing animation
        }
    }, [isOpen])

    const storeTokens = (tokens: AuthTokens, userData: UserData) => {
        // Use multi-user auth manager to store user-specific tokens
        multiUserAuth.addUserSession(userData, tokens)
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError('')

        try {
            const response = await fetch('http://127.0.0.1:8000/api/auth/login/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email,
                    password
                })
            })

            const data = await response.json()

            if (data.success) {
                // Store tokens and user data using multi-user auth manager
                storeTokens(data.tokens, data.user)

                setSuccess(true)
                console.log('Login successful:', data.user)

                // Wait for success animation then redirect
                setTimeout(() => {
                    onClose()
                    // Check if user is superuser and redirect accordingly
                    if (data.user && data.user.is_superuser) {
                        router.push('/admin')
                    } else {
                        router.push('/chat')
                    }
                }, 1500)
            } else {
                throw new Error(data.error || 'Login failed')
            }

        } catch (error: any) {
            console.error('Login error:', error)
            if (error.message.includes('fetch')) {
                setError('Unable to connect to server. Please try again.')
            } else {
                setError(error.message || 'Login failed. Please try again.')
            }
        } finally {
            setLoading(false)
        }
    }

    const handleSwitchToRegister = () => {
        onClose()
        setTimeout(() => {
            onSwitchToRegister()
        }, 300)
    }

    if (!isOpen) return null

    return (
        <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex min-h-screen items-center justify-center p-4">
                {/* Enhanced Backdrop with blur effect */}
                <div
                    className={`fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity duration-300 ${isOpen ? 'opacity-100' : 'opacity-0'
                        }`}
                    onClick={onClose}
                />

                {/* Enhanced Modal with better animations */}
                <div className={`relative bg-white rounded-3xl shadow-2xl w-full max-w-md p-8 transform transition-all duration-300 ${isOpen ? 'scale-100 opacity-100 translate-y-0' : 'scale-95 opacity-0 translate-y-4'
                    }`}>
                    {/* Close button */}
                    <button
                        onClick={onClose}
                        className="absolute top-6 right-6 text-gray-400 hover:text-gray-600 transition-colors duration-200 hover:rotate-90 transform"
                    >
                        <X className="w-6 h-6" />
                    </button>

                    {/* Header with improved avatar */}
                    <div className="text-center mb-8">
                        <div className="relative mx-auto mb-6 w-20 h-20">
                            <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full animate-pulse opacity-20"></div>
                            <img
                                src="/images/gigi-avatar.png"
                                alt="Gigi AI"
                                className="relative w-20 h-20 rounded-full shadow-lg border-4 border-white ring-4 ring-blue-100 hover:scale-105 transition-transform duration-300 object-cover"
                                onError={(e) => {
                                    // Fallback avatar
                                    e.currentTarget.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAiIGhlaWdodD0iODAiIHZpZXdCb3g9IjAgMCA4MCA4MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iNDAiIGN5PSI0MCIgcj0iNDAiIGZpbGw9IiM2MzY2RjEiLz4KPGNpcmNsZSBjeD0iNDAiIGN5PSIzMiIgcj0iMTIiIGZpbGw9IndoaXRlIi8+CjxwYXRoIGQ9Ik0yMCA2NEMyMCA1Ni4yIDI2LjUgNTAgNDAiIGZpbGw9IndoaXRlIi8+Cjwvc3ZnPgo='
                                }}
                            />
                        </div>
                        <h2 className="text-3xl font-bold text-gray-900 mb-3 bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                            Welcome Back!
                        </h2>
                        <p className="text-gray-600 text-lg">Sign in to continue your conversation with Gigi AI</p>
                    </div>

                    {/* Success State */}
                    {success && (
                        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-xl flex items-center space-x-3 animate-bounce">
                            <CheckCircle className="w-6 h-6 text-green-600" />
                            <div>
                                <p className="text-green-800 font-medium">Login successful!</p>
                                <p className="text-green-600 text-sm">Redirecting to your dashboard...</p>
                            </div>
                        </div>
                    )}

                    {/* Error State */}
                    {error && (
                        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center space-x-3 animate-shake">
                            <AlertCircle className="w-6 h-6 text-red-600" />
                            <div>
                                <p className="text-red-800 font-medium">Login failed</p>
                                <p className="text-red-600 text-sm">{error}</p>
                            </div>
                        </div>
                    )}

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div className="space-y-5">
                            <div>
                                <label className="block text-sm font-semibold text-gray-700 mb-3">
                                    Email Address
                                </label>
                                <div className="relative group">
                                    <Mail className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5 group-focus-within:text-blue-500 transition-colors duration-200" />
                                    <input
                                        type="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        className="w-full pl-12 pr-4 py-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all duration-200 hover:border-gray-400 text-lg text-gray-900 placeholder-gray-500"
                                        placeholder="Enter your email"
                                        required
                                        disabled={loading || success}
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-semibold text-gray-700 mb-3">
                                    Password
                                </label>
                                <div className="relative group">
                                    <Lock className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5 group-focus-within:text-blue-500 transition-colors duration-200" />
                                    <input
                                        type={showPassword ? 'text' : 'password'}
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        className="w-full pl-12 pr-14 py-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all duration-200 hover:border-gray-400 text-lg text-gray-900 placeholder-gray-500"
                                        placeholder="Enter your password"
                                        required
                                        disabled={loading || success}
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors duration-200"
                                        disabled={loading || success}
                                    >
                                        {showPassword ? <Eye className="w-5 h-5" /> : <EyeOff className="w-5 h-5" />}
                                    </button>
                                </div>
                            </div>
                        </div>

                        <div className="flex items-center justify-between">
                            <label className="flex items-center group cursor-pointer">
                                <input
                                    type="checkbox"
                                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 transition-colors duration-200"
                                    disabled={loading || success}
                                />
                                <span className="ml-3 text-sm text-gray-600 group-hover:text-gray-800 transition-colors duration-200">Remember me</span>
                            </label>
                            <button
                                type="button"
                                className="text-sm text-blue-600 hover:text-blue-500 font-medium transition-colors duration-200 hover:underline"
                                disabled={loading || success}
                                onClick={() => setShowForgotPassword(true)}
                            >
                                Forgot password?
                            </button>
                        </div>

                        <button
                            type="submit"
                            disabled={loading || success}
                            className="w-full py-4 px-6 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 focus:ring-4 focus:ring-blue-500/50 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-[1.02] active:scale-[0.98] font-semibold text-lg shadow-lg hover:shadow-xl"
                        >
                            {loading ? (
                                <div className="flex items-center justify-center space-x-3">
                                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                    <span>Signing In...</span>
                                </div>
                            ) : success ? (
                                <div className="flex items-center justify-center space-x-3">
                                    <CheckCircle className="w-5 h-5" />
                                    <span>Success!</span>
                                </div>
                            ) : (
                                'Sign In'
                            )}
                        </button>
                    </form>

                    {/* Footer */}
                    <div className="mt-8 text-center">
                        <p className="text-gray-600">
                            Don't have an account?{' '}
                            <button
                                onClick={handleSwitchToRegister}
                                className="text-blue-600 hover:text-blue-500 font-semibold transition-colors duration-200 hover:underline"
                                disabled={loading || success}
                            >
                                Sign up now
                            </button>
                        </p>
                    </div>
                </div>
            </div>
            <ForgotPasswordModal isOpen={showForgotPassword} onClose={() => setShowForgotPassword(false)} />
        </div>
    )
} 