'use client'

import React, { useState, useEffect } from 'react'
import { X, Mail, Lock, Eye, EyeOff, User, AlertCircle, CheckCircle, Check } from 'lucide-react'

interface RegisterModalProps {
    isOpen: boolean
    onClose: () => void
    onSwitchToLogin: () => void
}

export default function RegisterModal({ isOpen, onClose, onSwitchToLogin }: RegisterModalProps) {
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        password: '',
        confirmPassword: ''
    })
    const [showPassword, setShowPassword] = useState(false)
    const [showConfirmPassword, setShowConfirmPassword] = useState(false)
    const [loading, setLoading] = useState(false)
    const [errors, setErrors] = useState<{ [key: string]: string }>({})
    const [success, setSuccess] = useState(false)
    const [passwordStrength, setPasswordStrength] = useState(0)

    // Reset form when modal opens/closes
    useEffect(() => {
        if (isOpen) {
            setErrors({})
            setSuccess(false)
        } else {
            // Reset form when modal closes
            setTimeout(() => {
                setFormData({
                    name: '',
                    email: '',
                    password: '',
                    confirmPassword: ''
                })
                setShowPassword(false)
                setShowConfirmPassword(false)
                setErrors({})
                setSuccess(false)
                setPasswordStrength(0)
            }, 300) // Wait for closing animation
        }
    }, [isOpen])

    // Calculate password strength
    useEffect(() => {
        const password = formData.password
        let strength = 0
        if (password.length >= 8) strength++
        if (/[A-Z]/.test(password)) strength++
        if (/[a-z]/.test(password)) strength++
        if (/[0-9]/.test(password)) strength++
        if (/[^A-Za-z0-9]/.test(password)) strength++
        setPasswordStrength(strength)
    }, [formData.password])

    if (!isOpen) return null

    const validateForm = () => {
        const newErrors: { [key: string]: string } = {}

        if (formData.name.length < 2) {
            newErrors.name = 'Name must be at least 2 characters'
        }

        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
            newErrors.email = 'Please enter a valid email address'
        }

        if (formData.password.length < 8) {
            newErrors.password = 'Password must be at least 8 characters'
        }

        if (formData.password !== formData.confirmPassword) {
            newErrors.confirmPassword = 'Passwords do not match'
        }

        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!validateForm()) return

        setLoading(true)
        setErrors({})

        try {
            // Call Django registration API
            console.log('Registration attempt:', formData)

            const response = await fetch('http://127.0.0.1:8000/api/auth/register/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            })

            const data = await response.json()

            if (data.success) {
                setSuccess(true)
                console.log('Registration successful:', data.user)

                // Wait for success animation then switch to login
                setTimeout(() => {
                    onClose()
                    setTimeout(() => {
                        onSwitchToLogin()
                    }, 300)
                }, 2000)
            } else {
                throw new Error(data.error || 'Registration failed')
            }

        } catch (error: any) {
            console.error('Registration error:', error)
            if (error.message.includes('fetch')) {
                setErrors({ general: 'Unable to connect to server. Please try again.' })
            } else {
                setErrors({ general: error.message || 'Registration failed. Please try again.' })
            }
        } finally {
            setLoading(false)
        }
    }

    const handleInputChange = (field: string, value: string) => {
        setFormData(prev => ({ ...prev, [field]: value }))
        // Clear error when user starts typing
        if (errors[field]) {
            setErrors(prev => ({ ...prev, [field]: '' }))
        }
    }

    const handleSwitchToLogin = () => {
        onClose()
        setTimeout(() => {
            onSwitchToLogin()
        }, 300)
    }

    const getPasswordStrengthColor = () => {
        if (passwordStrength <= 2) return 'bg-red-500'
        if (passwordStrength <= 3) return 'bg-yellow-500'
        return 'bg-green-500'
    }

    const getPasswordStrengthText = () => {
        if (passwordStrength <= 2) return 'Weak'
        if (passwordStrength <= 3) return 'Medium'
        return 'Strong'
    }

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
                <div className={`relative bg-white rounded-3xl shadow-2xl w-full max-w-md p-8 transform transition-all duration-300 max-h-[90vh] overflow-y-auto ${isOpen ? 'scale-100 opacity-100 translate-y-0' : 'scale-95 opacity-0 translate-y-4'
                    }`}>
                    {/* Close button */}
                    <button
                        onClick={onClose}
                        className="absolute top-6 right-6 text-gray-400 hover:text-gray-600 transition-colors duration-200 hover:rotate-90 transform z-10"
                    >
                        <X className="w-6 h-6" />
                    </button>

                    {/* Header */}
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
                            Join Gigi AI
                        </h2>
                        <p className="text-gray-600 text-lg">Create your account to start your AI journey</p>
                    </div>

                    {/* Success State */}
                    {success && (
                        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-xl flex items-center space-x-3 animate-bounce">
                            <CheckCircle className="w-6 h-6 text-green-600" />
                            <div>
                                <p className="text-green-800 font-medium">Account created successfully!</p>
                                <p className="text-green-600 text-sm">Redirecting to login...</p>
                            </div>
                        </div>
                    )}

                    {/* General Error */}
                    {errors.general && (
                        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center space-x-3 animate-shake">
                            <AlertCircle className="w-6 h-6 text-red-600" />
                            <div>
                                <p className="text-red-800 font-medium">Registration failed</p>
                                <p className="text-red-600 text-sm">{errors.general}</p>
                            </div>
                        </div>
                    )}

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="space-y-5">
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-3">
                                Full Name
                            </label>
                            <div className="relative group">
                                <User className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5 group-focus-within:text-blue-500 transition-colors duration-200" />
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) => handleInputChange('name', e.target.value)}
                                    className={`w-full pl-12 pr-4 py-4 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all duration-200 hover:border-gray-400 text-lg text-gray-900 placeholder-gray-500 ${errors.name ? 'border-red-500 ring-2 ring-red-500/20' : 'border-gray-300'
                                        }`}
                                    placeholder="Enter your full name"
                                    required
                                    disabled={loading || success}
                                />
                            </div>
                            {errors.name && <p className="mt-2 text-sm text-red-600 flex items-center space-x-1">
                                <AlertCircle className="w-4 h-4" />
                                <span>{errors.name}</span>
                            </p>}
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-3">
                                Email Address
                            </label>
                            <div className="relative group">
                                <Mail className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5 group-focus-within:text-blue-500 transition-colors duration-200" />
                                <input
                                    type="email"
                                    value={formData.email}
                                    onChange={(e) => handleInputChange('email', e.target.value)}
                                    className={`w-full pl-12 pr-4 py-4 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all duration-200 hover:border-gray-400 text-lg text-gray-900 placeholder-gray-500 ${errors.email ? 'border-red-500 ring-2 ring-red-500/20' : 'border-gray-300'
                                        }`}
                                    placeholder="Enter your email"
                                    required
                                    disabled={loading || success}
                                />
                            </div>
                            {errors.email && <p className="mt-2 text-sm text-red-600 flex items-center space-x-1">
                                <AlertCircle className="w-4 h-4" />
                                <span>{errors.email}</span>
                            </p>}
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-3">
                                Password
                            </label>
                            <div className="relative group">
                                <Lock className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5 group-focus-within:text-blue-500 transition-colors duration-200" />
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    value={formData.password}
                                    onChange={(e) => handleInputChange('password', e.target.value)}
                                    className={`w-full pl-12 pr-14 py-4 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all duration-200 hover:border-gray-400 text-lg text-gray-900 placeholder-gray-500 ${errors.password ? 'border-red-500 ring-2 ring-red-500/20' : 'border-gray-300'
                                        }`}
                                    placeholder="Create a password"
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

                            {/* Password Strength Indicator */}
                            {formData.password && (
                                <div className="mt-3">
                                    <div className="flex items-center space-x-2">
                                        <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                                            <div
                                                className={`h-full transition-all duration-300 ${getPasswordStrengthColor()}`}
                                                style={{ width: `${(passwordStrength / 5) * 100}%` }}
                                            />
                                        </div>
                                        <span className={`text-sm font-medium ${passwordStrength <= 2 ? 'text-red-600' :
                                            passwordStrength <= 3 ? 'text-yellow-600' : 'text-green-600'
                                            }`}>
                                            {getPasswordStrengthText()}
                                        </span>
                                    </div>
                                </div>
                            )}

                            {errors.password && <p className="mt-2 text-sm text-red-600 flex items-center space-x-1">
                                <AlertCircle className="w-4 h-4" />
                                <span>{errors.password}</span>
                            </p>}
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-3">
                                Confirm Password
                            </label>
                            <div className="relative group">
                                <Lock className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5 group-focus-within:text-blue-500 transition-colors duration-200" />
                                <input
                                    type={showConfirmPassword ? 'text' : 'password'}
                                    value={formData.confirmPassword}
                                    onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                                    className={`w-full pl-12 pr-14 py-4 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all duration-200 hover:border-gray-400 text-lg text-gray-900 placeholder-gray-500 ${errors.confirmPassword ? 'border-red-500 ring-2 ring-red-500/20' : 'border-gray-300'
                                        }`}
                                    placeholder="Confirm your password"
                                    required
                                    disabled={loading || success}
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                    className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors duration-200"
                                    disabled={loading || success}
                                >
                                    {showConfirmPassword ? <Eye className="w-5 h-5" /> : <EyeOff className="w-5 h-5" />}
                                </button>
                            </div>
                            {errors.confirmPassword && <p className="mt-2 text-sm text-red-600 flex items-center space-x-1">
                                <AlertCircle className="w-4 h-4" />
                                <span>{errors.confirmPassword}</span>
                            </p>}
                        </div>

                        {/* Terms and Privacy */}
                        <div className="flex items-start space-x-3 p-4 bg-gray-50 rounded-xl">
                            <div className="flex-shrink-0 mt-0.5">
                                <Check className="w-4 h-4 text-blue-600" />
                            </div>
                            <p className="text-sm text-gray-600 leading-relaxed">
                                By creating an account, you agree to our{' '}
                                <button type="button" className="text-blue-600 hover:text-blue-500 font-medium hover:underline">
                                    Terms of Service
                                </button>{' '}
                                and{' '}
                                <button type="button" className="text-blue-600 hover:text-blue-500 font-medium hover:underline">
                                    Privacy Policy
                                </button>
                            </p>
                        </div>

                        <button
                            type="submit"
                            disabled={loading || success}
                            className="w-full py-4 px-6 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 focus:ring-4 focus:ring-blue-500/50 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-[1.02] active:scale-[0.98] font-semibold text-lg shadow-lg hover:shadow-xl"
                        >
                            {loading ? (
                                <div className="flex items-center justify-center space-x-3">
                                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                    <span>Creating Account...</span>
                                </div>
                            ) : success ? (
                                <div className="flex items-center justify-center space-x-3">
                                    <CheckCircle className="w-5 h-5" />
                                    <span>Account Created!</span>
                                </div>
                            ) : (
                                'Create Account'
                            )}
                        </button>
                    </form>

                    {/* Footer */}
                    <div className="mt-8 text-center">
                        <p className="text-gray-600">
                            Already have an account?{' '}
                            <button
                                onClick={handleSwitchToLogin}
                                className="text-blue-600 hover:text-blue-500 font-semibold transition-colors duration-200 hover:underline"
                                disabled={loading || success}
                            >
                                Sign in
                            </button>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
} 