'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import AdminDashboard from '../../components/AdminDashboard'
import { multiUserAuth } from '../../lib/multiUserAuth'

export default function AdminPage() {
    const router = useRouter()
    const [isLoading, setIsLoading] = useState(true)
    const [isAuthenticated, setIsAuthenticated] = useState(false)
    const [isSuperuser, setIsSuperuser] = useState(false)

    useEffect(() => {
        const checkAuth = async () => {
            try {
                // Get current user's token from multi-user auth system
                const tokens = multiUserAuth.getCurrentUserTokens()
                const currentUserData = multiUserAuth.getCurrentUserData()

                if (!tokens || !tokens.access) {
                    router.push('/')
                    return
                }

                const response = await fetch('http://127.0.0.1:8000/api/auth/verify/', {
                    headers: {
                        'Authorization': `Bearer ${tokens.access}`
                    }
                })

                const data = await response.json()

                if (data.success && data.user) {
                    setIsAuthenticated(true)
                    if (data.user.is_superuser) {
                        setIsSuperuser(true)
                    } else {
                        // Not a superuser, redirect to regular chat
                        router.push('/chat')
                        return
                    }
                } else {
                    // Invalid token, remove this user's session and redirect to home
                    if (currentUserData) {
                        multiUserAuth.removeUserSession(currentUserData.id.toString())
                    }
                    router.push('/')
                    return
                }
            } catch (error) {
                console.error('Auth check failed:', error)
                router.push('/')
                return
            }

            setIsLoading(false)
        }

        checkAuth()
    }, [router])

    if (isLoading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
                <div className="text-center">
                    <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-gray-600 text-lg">Verifying admin access...</p>
                </div>
            </div>
        )
    }

    if (!isAuthenticated || !isSuperuser) {
        return null // Will redirect
    }

    return <AdminDashboard />
} 