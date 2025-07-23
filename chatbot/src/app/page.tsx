'use client'

import React, { useState } from 'react'
import LoginModal from '@/components/auth/LoginModal'
import RegisterModal from '@/components/auth/RegisterModal'

export default function HomePage() {
    const [showLogin, setShowLogin] = useState(false)
    const [showRegister, setShowRegister] = useState(false)

    const features = [
        {
            title: 'Advanced AI Intelligence',
            description: 'Powered by state-of-the-art language models for natural conversations',
            icon: '🧠'
        },
        {
            title: 'Seamless Chat Experience',
            description: 'Intuitive interface designed for effortless communication',
            icon: '💬'
        },
        {
            title: 'Secure & Private',
            description: 'Your conversations are protected with enterprise-grade security',
            icon: '🔒'
        }
    ]

    const handleSwitchToLogin = () => {
        setShowRegister(false)
        setTimeout(() => setShowLogin(true), 300)
    }

    const handleSwitchToRegister = () => {
        setShowLogin(false)
        setTimeout(() => setShowRegister(true), 300)
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
            {/* Hero Section */}
            <div className="relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 to-indigo-600/10"></div>

                {/* Animated background elements */}
                <div className="absolute inset-0 overflow-hidden">
                    <div className="absolute -top-10 -right-10 w-20 h-20 bg-blue-400/20 rounded-full animate-pulse"></div>
                    <div className="absolute top-1/2 -left-10 w-32 h-32 bg-indigo-400/20 rounded-full animate-pulse delay-1000"></div>
                    <div className="absolute bottom-10 right-1/3 w-16 h-16 bg-purple-400/20 rounded-full animate-pulse delay-500"></div>
                </div>

                {/* Navigation */}
                <nav className="relative z-10 px-6 py-6">
                    <div className="max-w-7xl mx-auto flex justify-between items-center">
                        <div className="flex items-center space-x-4">
                            <div className="relative">
                                <img
                                    src="/images/gigi-avatar.png"
                                    alt="Gigi AI"
                                    className="w-10 h-10 rounded-full border-2 border-blue-600/30 shadow-lg hover:scale-110 transition-transform duration-300 object-cover"
                                    onError={(e) => {
                                        // Fallback avatar
                                        e.currentTarget.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMjAiIGN5PSIyMCIgcj0iMjAiIGZpbGw9IiM2MzY2RjEiLz4KPGNpcmNsZSBjeD0iMjAiIGN5PSIxNiIgcj0iNiIgZmlsbD0id2hpdGUiLz4KPHBhdGggZD0iTTEwIDMyQzEwIDI4LjEgMTMuMjUgMjUgMjAiIGZpbGw9IndoaXRlIi8+Cjwvc3ZnPgo='
                                    }}
                                />
                                <div className="absolute inset-0 rounded-full bg-gradient-to-t from-blue-600/20 to-transparent"></div>
                            </div>
                            <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                                Gigi AI
                            </span>
                        </div>

                        <div className="flex space-x-4">
                            <button
                                onClick={() => setShowLogin(true)}
                                className="px-6 py-3 text-gray-700 hover:text-blue-600 transition-colors duration-200 font-medium hover:bg-white/50 rounded-lg"
                            >
                                Sign In
                            </button>
                            <button
                                onClick={() => setShowRegister(true)}
                                className="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105"
                            >
                                Get Started
                            </button>
                        </div>
                    </div>
                </nav>

                {/* Hero Content */}
                <div className="relative z-10 px-6 py-20">
                    <div className="max-w-4xl mx-auto text-center">
                        <div className="animate-fade-in">
                            {/* Enhanced Gigi Avatar */}
                            <div className="mb-12 flex justify-center">
                                <div className="relative group">
                                    <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full animate-pulse opacity-30 group-hover:opacity-40 transition-opacity duration-300"></div>
                                    <div className="absolute inset-0 bg-gradient-to-r from-blue-400 to-purple-400 rounded-full animate-ping opacity-20"></div>
                                    <img
                                        src="/images/gigi-avatar.png"
                                        alt="Gigi AI Avatar"
                                        className="relative w-40 h-40 md:w-48 md:h-48 rounded-full shadow-2xl border-6 border-white/70 hover:scale-110 transition-transform duration-500 object-cover z-10"
                                        onError={(e) => {
                                            // Enhanced fallback avatar
                                            e.currentTarget.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTkyIiBoZWlnaHQ9IjE5MiIgdmlld0JveD0iMCAwIDE5MiAxOTIiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxjaXJjbGUgY3g9Ijk2IiBjeT0iOTYiIHI9Ijk2IiBmaWxsPSJ1cmwoI2dyYWQpIi8+CjxjaXJjbGUgY3g9Ijk2IiBjeT0iNzYiIHI9IjI4IiBmaWxsPSJ3aGl0ZSIvPgo8cGF0aCBkPSJNNDggMTUyQzQ4IDEzMy4yIDY0IDEyMCA5NiIgZmlsbD0id2hpdGUiLz4KPGR1ZnM+CjxsaW5lYXJHcmFkaWVudCBpZD0iZ3JhZCIgeDE9IjAiIHkxPSIwIiB4Mj0iMSIgeTI9IjEiPgo8c3RvcCBvZmZzZXQ9IjAlIiBzdG9wLWNvbG9yPSIjNjM2NkYxIi8+CjxzdG9wIG9mZnNldD0iMTAwJSIgc3RvcC1jb2xvcj0iIzgwODRGNCIvPgo8L2xpbmVhckdyYWRpZW50Pgo8L2RlZnM+Cjwvc3ZnPgo='
                                        }}
                                    />
                                    {/* Floating particles around avatar */}
                                    <div className="absolute top-4 left-4 w-3 h-3 bg-blue-400 rounded-full animate-bounce delay-100"></div>
                                    <div className="absolute top-8 right-8 w-2 h-2 bg-indigo-400 rounded-full animate-bounce delay-300"></div>
                                    <div className="absolute bottom-6 left-8 w-2 h-2 bg-purple-400 rounded-full animate-bounce delay-500"></div>
                                </div>
                            </div>

                            <h1 className="text-6xl md:text-7xl font-bold text-gray-900 mb-8 leading-tight">
                                Meet{' '}
                                <span className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent animate-pulse">
                                    Gigi AI
                                </span>
                            </h1>
                            <p className="text-xl md:text-2xl text-gray-600 mb-12 max-w-3xl mx-auto leading-relaxed">
                                Your intelligent conversation partner that understands, learns, and adapts to provide
                                personalized assistance across all your needs.
                            </p>
                        </div>

                        <div className="flex flex-col sm:flex-row gap-6 justify-center items-center">
                            <button
                                onClick={() => setShowRegister(true)}
                                className="px-10 py-5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-2xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-300 shadow-lg hover:shadow-2xl transform hover:scale-105 font-semibold text-lg"
                            >
                                Start Chatting Now →
                            </button>
                            <button
                                onClick={() => setShowLogin(true)}
                                className="px-10 py-5 border-2 border-gray-300 text-gray-700 rounded-2xl hover:border-blue-600 hover:text-blue-600 hover:bg-blue-50 transition-all duration-300 font-semibold text-lg"
                            >
                                Already have an account?
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Features Section */}
            <div className="py-24 px-6">
                <div className="max-w-6xl mx-auto">
                    <div className="text-center mb-20">
                        <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
                            Why Choose Gigi AI?
                        </h2>
                        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                            Experience the next generation of AI conversation technology
                        </p>
                    </div>

                    <div className="grid md:grid-cols-3 gap-10">
                        {features.map((feature, index) => (
                            <div
                                key={index}
                                className="bg-white rounded-3xl p-10 shadow-xl hover:shadow-2xl transition-all duration-500 border border-gray-100 group hover:scale-105"
                            >
                                <div className="text-5xl mb-6 group-hover:scale-110 transition-transform duration-300">
                                    {feature.icon}
                                </div>
                                <h3 className="text-2xl font-bold text-gray-900 mb-4">
                                    {feature.title}
                                </h3>
                                <p className="text-gray-600 leading-relaxed text-lg">
                                    {feature.description}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Enhanced CTA Section */}
            <div className="py-24 px-6 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 relative overflow-hidden">
                {/* Background patterns */}
                <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmZmZmYiIGZpbGwtb3BhY2l0eT0iMC4xIj48cGF0aCBkPSJtMzYgMzQgNi0yLTYtMnptLTEwLTEyIDE4LTYtMTggNiIvPjwvZz48L2c+PC9zdmc+')] opacity-20"></div>

                <div className="max-w-4xl mx-auto text-center relative z-10">
                    <div>
                        <h2 className="text-4xl md:text-5xl font-bold text-white mb-8">
                            Ready to Experience the Future?
                        </h2>
                        <p className="text-xl text-blue-100 mb-12 max-w-2xl mx-auto leading-relaxed">
                            Join thousands of users who are already enjoying smarter conversations with Gigi AI
                        </p>
                        <button
                            onClick={() => setShowRegister(true)}
                            className="px-12 py-5 bg-white text-blue-600 rounded-2xl hover:bg-gray-50 transition-all duration-300 shadow-xl hover:shadow-2xl font-bold text-lg transform hover:scale-105"
                        >
                            Get Started for Free
                        </button>
                    </div>
                </div>
            </div>

            <footer className="bg-gradient-to-t from-indigo-50 to-white border-t border-gray-200 py-8">
                <div className="max-w-4xl mx-auto text-center">
                    <p className="text-gray-500 text-sm">
                        &copy; {new Date().getFullYear()} Gigi AI. All rights reserved.
                    </p>
                    <p className="text-gray-400 text-xs mt-2">
                        Built with ❤️ for smarter conversations.
                    </p>
                </div>
            </footer>

            {/* Enhanced Modals with proper switching */}
            <LoginModal
                isOpen={showLogin}
                onClose={() => setShowLogin(false)}
                onSwitchToRegister={handleSwitchToRegister}
            />
            <RegisterModal
                isOpen={showRegister}
                onClose={() => setShowRegister(false)}
                onSwitchToLogin={handleSwitchToLogin}
            />
        </div>
    )
} 