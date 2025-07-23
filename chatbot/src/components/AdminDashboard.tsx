'use client'

import React, { useState, useEffect } from 'react'
import {
    Users,
    MessageSquare,
    Activity,
    Search,
    Plus,
    Edit,
    Trash2,
    Eye,
    LogOut,
    BarChart3,
    TrendingUp,
    Shield,
    Calendar,
    RefreshCw,
    X,
    Save,
    UserPlus,
    Settings,
    CheckCircle,
    AlertCircle,
    Monitor,
    Crown,
    User
} from 'lucide-react'
import { useRouter } from 'next/navigation'
import { multiUserAuth, UserData } from '../lib/multiUserAuth'

interface User {
    id: number
    email: string
    first_name: string
    last_name: string
    full_name: string
    is_active: boolean
    is_superuser: boolean
    date_joined: string
    last_login: string | null
    theme: string
    total_chats: number
    total_conversations: number
}

interface Analytics {
    users: {
        total: number
        active: number
        superusers: number
        today: number
        this_week: number
        this_month: number
    }
    chats: {
        total: number
        today: number
        this_week: number
        this_month: number
    }
    conversations: {
        total: number
        today: number
        this_week: number
        this_month: number
    }
    most_active_users: Array<{
        id: number
        email: string
        full_name: string
        chat_count: number
    }>
    daily_stats: Array<{
        date: string
        users: number
        chats: number
        conversations: number
    }>
}

interface UserFormData {
    email: string
    full_name: string
    password: string
    is_active: boolean
    is_superuser: boolean
}

interface ServerSession {
    id: number
    email: string
    full_name: string
    is_superuser: boolean
    device_info: string
    ip_address: string
    session_id: string
    last_activity: string
    created_at: string
}

export default function AdminDashboard() {
    const router = useRouter()
    const [analytics, setAnalytics] = useState<Analytics | null>(null)
    const [users, setUsers] = useState<User[]>([])
    const [loading, setLoading] = useState(true)
    const [searchTerm, setSearchTerm] = useState('')
    const [currentPage, setCurrentPage] = useState(1)
    const [totalPages, setTotalPages] = useState(1)
    const [showUserModal, setShowUserModal] = useState(false)
    const [editingUser, setEditingUser] = useState<User | null>(null)
    const [userForm, setUserForm] = useState<UserFormData>({
        email: '',
        full_name: '',
        password: '',
        is_active: true,
        is_superuser: false
    })
    const [success, setSuccess] = useState('')
    const [error, setError] = useState('')
    const [activeTab, setActiveTab] = useState('analytics')
    const [isRefreshing, setIsRefreshing] = useState(false)

    // Session management state
    const [activeSessions, setActiveSessions] = useState<ServerSession[]>([])
    const [lastSessionUpdate, setLastSessionUpdate] = useState<Date | null>(null)
    const [isSessionsLoading, setIsSessionsLoading] = useState(false)
    const [sessionCleanupStats, setSessionCleanupStats] = useState<any>(null)

    useEffect(() => {
        fetchAnalytics()
        fetchUsers()
        updateSessionList()
    }, [])

    useEffect(() => {
        fetchUsers()
    }, [searchTerm, currentPage])

    // Auto-refresh sessions when sessions tab is active
    useEffect(() => {
        let intervalId: NodeJS.Timeout | null = null

        if (activeTab === 'sessions') {
            // Refresh sessions immediately when switching to sessions tab
            updateSessionList()

            // Set up auto-refresh every 30 seconds
            intervalId = setInterval(() => {
                updateSessionList()
            }, 30000) // 30 seconds
        }

        // Cleanup interval when tab changes or component unmounts
        return () => {
            if (intervalId) {
                clearInterval(intervalId)
            }
        }
    }, [activeTab])

    const getAuthToken = () => {
        const tokens = multiUserAuth.getCurrentUserTokens()
        return tokens?.access || null
    }

    const handleRefresh = async () => {
        setIsRefreshing(true)
        setError('')
        try {
            await Promise.all([fetchAnalytics(), fetchUsers()])
            updateSessionList() // Also refresh sessions
            setSuccess('Dashboard refreshed successfully!')
            setTimeout(() => setSuccess(''), 2000)
        } catch (error) {
            setError('Failed to refresh dashboard data')
            setTimeout(() => setError(''), 3000)
        } finally {
            setIsRefreshing(false)
        }
    }

    const fetchAnalytics = async () => {
        try {
            const response = await fetch('http://127.0.0.1:8000/api/admin/analytics/', {
                headers: {
                    'Authorization': `Bearer ${getAuthToken()}`
                }
            })
            const data = await response.json()
            if (data.success) {
                setAnalytics(data.analytics)
            } else {
                setError(data.error || 'Failed to fetch analytics data')
                setTimeout(() => setError(''), 3000)
            }
        } catch (error) {
            console.error('Failed to fetch analytics:', error)
            setError('Failed to connect to server. Please check your connection.')
            setTimeout(() => setError(''), 3000)
        }
    }

    const fetchUsers = async () => {
        try {
            const params = new URLSearchParams({
                search: searchTerm,
                page: currentPage.toString(),
                per_page: '10'
            })

            const response = await fetch(`http://127.0.0.1:8000/api/admin/users/?${params}`, {
                headers: {
                    'Authorization': `Bearer ${getAuthToken()}`
                }
            })
            const data = await response.json()
            if (data.success) {
                setUsers(data.users)
                setTotalPages(data.pagination.pages)
            } else {
                setError(data.error || 'Failed to fetch users data')
                setTimeout(() => setError(''), 3000)
            }
        } catch (error) {
            console.error('Failed to fetch users:', error)
            setError('Failed to connect to server. Please check your connection.')
            setTimeout(() => setError(''), 3000)
        } finally {
            setLoading(false)
        }
    }

    const handleLogout = () => {
        const currentUserData = multiUserAuth.getCurrentUserData()
        if (currentUserData) {
            multiUserAuth.removeUserSession(currentUserData.id.toString())
        }

        // Check if there are other active sessions
        if (multiUserAuth.getSessionCount() > 0) {
            // Stay on admin but reload to switch to another admin user
            window.location.reload()
        } else {
            // No other sessions, redirect to homepage
            router.push('/')
        }
    }

    const handleCreateUser = () => {
        setEditingUser(null)
        setUserForm({
            email: '',
            full_name: '',
            password: '',
            is_active: true,
            is_superuser: false
        })
        setShowUserModal(true)
    }

    const handleEditUser = (user: User) => {
        setEditingUser(user)
        setUserForm({
            email: user.email,
            full_name: user.full_name || `${user.first_name} ${user.last_name}`.trim(),
            password: '',
            is_active: user.is_active,
            is_superuser: user.is_superuser
        })
        setShowUserModal(true)
    }

    const handleSaveUser = async () => {
        try {
            const url = editingUser
                ? `http://127.0.0.1:8000/api/admin/users/${editingUser.id}/update/`
                : 'http://127.0.0.1:8000/api/admin/users/create/'

            const method = editingUser ? 'PUT' : 'POST'

            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getAuthToken()}`
                },
                body: JSON.stringify(userForm)
            })

            const data = await response.json()
            if (data.success) {
                setSuccess(data.message)
                setShowUserModal(false)
                await Promise.all([fetchUsers(), fetchAnalytics()])
                setTimeout(() => setSuccess(''), 3000)
            } else {
                setError(data.error)
                setTimeout(() => setError(''), 3000)
            }
        } catch (error) {
            setError('Failed to save user')
            setTimeout(() => setError(''), 3000)
        }
    }

    const handleDeleteUser = async (userId: number) => {
        if (!confirm('Are you sure you want to delete this user?')) return

        try {
            const response = await fetch(`http://127.0.0.1:8000/api/admin/users/${userId}/delete/`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${getAuthToken()}`
                }
            })

            const data = await response.json()
            if (data.success) {
                setSuccess(data.message)
                await Promise.all([fetchUsers(), fetchAnalytics()])
                setTimeout(() => setSuccess(''), 3000)
            } else {
                setError(data.error)
                setTimeout(() => setError(''), 3000)
            }
        } catch (error) {
            setError('Failed to delete user')
            setTimeout(() => setError(''), 3000)
        }
    }

    // Session management functions
    const updateSessionList = async () => {
        setIsSessionsLoading(true)
        try {
            const response = await fetch('http://127.0.0.1:8000/api/admin/sessions/', {
                headers: {
                    'Authorization': `Bearer ${getAuthToken()}`
                }
            })
            const data = await response.json()
            if (data.success) {
                // Convert server session format to match UserData interface
                const sessions = data.sessions.map((session: any) => ({
                    id: session.user_id,
                    email: session.email,
                    full_name: session.full_name,
                    is_superuser: session.is_superuser,
                    device_info: session.device_info,
                    ip_address: session.ip_address,
                    session_id: session.id, // Keep original session ID for termination
                    last_activity: session.last_activity,
                    created_at: session.created_at
                }))
                setActiveSessions(sessions)
                setLastSessionUpdate(new Date())

                // Store cleanup statistics if available
                if (data.cleanup_stats) {
                    setSessionCleanupStats(data.cleanup_stats)
                }
            } else {
                setError(data.error || 'Failed to fetch active sessions')
                setTimeout(() => setError(''), 3000)
            }
        } catch (error) {
            console.error('Failed to fetch sessions:', error)
            setError('Failed to connect to server. Please check your connection.')
            setTimeout(() => setError(''), 3000)
        } finally {
            setIsSessionsLoading(false)
        }
    }

    const handleLogoutSpecificUser = async (sessionId: string, event: React.MouseEvent) => {
        event.stopPropagation()

        const session = activeSessions.find(s => s.session_id === sessionId)
        const userName = session?.full_name || session?.email || 'Unknown User'

        if (window.confirm(`Are you sure you want to end ${userName}'s session? This will log them out immediately.`)) {
            try {
                const response = await fetch(`http://127.0.0.1:8000/api/admin/sessions/${sessionId}/terminate/`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${getAuthToken()}`
                    }
                })
                const data = await response.json()
                if (data.success) {
                    updateSessionList()
                    setSuccess(data.message)
                    setTimeout(() => setSuccess(''), 3000)
                } else {
                    setError(data.error || 'Failed to terminate session')
                    setTimeout(() => setError(''), 3000)
                }
            } catch (error) {
                console.error('Failed to terminate session:', error)
                setError('Failed to connect to server. Please check your connection.')
                setTimeout(() => setError(''), 3000)
            }
        }
    }

    const handleLogoutAllUsers = async () => {
        if (window.confirm('Are you sure you want to log out ALL users? This will end all active sessions including your own.')) {
            try {
                const response = await fetch('http://127.0.0.1:8000/api/admin/sessions/terminate-all/', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${getAuthToken()}`
                    }
                })
                const data = await response.json()
                if (data.success) {
                    setSuccess(data.message)
                    setTimeout(() => {
                        // Redirect to homepage since all sessions are terminated
                        window.location.href = '/'
                    }, 2000)
                } else {
                    setError(data.error || 'Failed to terminate all sessions')
                    setTimeout(() => setError(''), 3000)
                }
            } catch (error) {
                console.error('Failed to terminate all sessions:', error)
                setError('Failed to connect to server. Please check your connection.')
                setTimeout(() => setError(''), 3000)
            }
        }
    }

    const getUserIcon = (session: ServerSession) => {
        if (session.is_superuser) {
            return <Crown className="w-4 h-4 text-yellow-600" />
        }
        return <User className="w-4 h-4 text-gray-500" />
    }

    const getUserBadge = (session: ServerSession) => {
        if (session.is_superuser) {
            return (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                    <Shield className="w-3 h-3 mr-1" />
                    Admin
                </span>
            )
        }
        return (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                User
            </span>
        )
    }

    const StatCard = ({ title, value, icon: Icon, color }: { title: string, value: number | string, icon: any, color: string }) => (
        <div className="bg-white rounded-xl shadow-lg p-6 transform hover:scale-105 transition-transform duration-200">
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-gray-600 text-sm font-medium">{title}</p>
                    <p className={`text-3xl font-bold ${color} mt-2`}>{value}</p>
                </div>
                <div className={`p-3 rounded-full ${color.replace('text-', 'bg-').replace('600', '100')}`}>
                    <Icon className={`w-8 h-8 ${color}`} />
                </div>
            </div>
        </div>
    )

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
                <div className="text-center">
                    <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-gray-600 text-lg">Loading dashboard...</p>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
            {/* Header */}
            <div className="bg-white shadow-lg border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center py-6">
                        <div className="flex items-center space-x-4">
                            <div className="relative w-12 h-12">
                                <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full animate-pulse opacity-20"></div>
                                <img
                                    src="/images/gigi-avatar.png"
                                    alt="Gigi AI Admin"
                                    className="relative w-12 h-12 rounded-full shadow-lg border-2 border-white ring-4 ring-blue-100 object-cover"
                                />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                                    Admin Dashboard
                                </h1>
                                <p className="text-gray-600">Gigi AI Analytics & User Management</p>
                            </div>
                        </div>

                        <div className="flex items-center space-x-4">
                            <button
                                onClick={handleRefresh}
                                disabled={isRefreshing}
                                className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors duration-200 ${isRefreshing
                                    ? 'bg-gray-400 text-white cursor-not-allowed'
                                    : 'bg-blue-600 text-white hover:bg-blue-700'
                                    }`}
                            >
                                <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                                <span>{isRefreshing ? 'Refreshing...' : 'Refresh'}</span>
                            </button>
                            <button
                                onClick={handleLogout}
                                className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200"
                            >
                                <LogOut className="w-4 h-4" />
                                <span>Logout</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Success/Error Messages */}
            {success && (
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4">
                    <div className="bg-green-50 border border-green-200 rounded-xl p-4 flex items-center space-x-3">
                        <CheckCircle className="w-5 h-5 text-green-600" />
                        <p className="text-green-800">{success}</p>
                    </div>
                </div>
            )}

            {error && (
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4">
                    <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center space-x-3">
                        <AlertCircle className="w-5 h-5 text-red-600" />
                        <p className="text-red-800">{error}</p>
                    </div>
                </div>
            )}

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Tab Navigation */}
                <div className="mb-8">
                    <div className="flex space-x-1 bg-white rounded-xl p-1 shadow-lg">
                        <button
                            onClick={() => setActiveTab('analytics')}
                            className={`flex-1 flex items-center justify-center space-x-2 py-3 px-6 rounded-lg transition-all duration-200 ${activeTab === 'analytics'
                                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg'
                                : 'text-gray-600 hover:bg-gray-50'
                                }`}
                        >
                            <BarChart3 className="w-5 h-5" />
                            <span className="font-medium">Analytics</span>
                        </button>
                        <button
                            onClick={() => setActiveTab('users')}
                            className={`flex-1 flex items-center justify-center space-x-2 py-3 px-6 rounded-lg transition-all duration-200 ${activeTab === 'users'
                                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg'
                                : 'text-gray-600 hover:bg-gray-50'
                                }`}
                        >
                            <Users className="w-5 h-5" />
                            <span className="font-medium">User Management</span>
                        </button>
                        <button
                            onClick={() => setActiveTab('sessions')}
                            className={`flex-1 flex items-center justify-center space-x-2 py-3 px-6 rounded-lg transition-all duration-200 ${activeTab === 'sessions'
                                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg'
                                : 'text-gray-600 hover:bg-gray-50'
                                }`}
                        >
                            <Monitor className="w-5 h-5" />
                            <span className="font-medium">Sessions</span>
                        </button>
                    </div>
                </div>

                {/* Analytics Tab */}
                {activeTab === 'analytics' && analytics && (
                    <div className="space-y-8">
                        {/* Stats Overview */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                            <StatCard
                                title="Total Users"
                                value={analytics.users.total}
                                icon={Users}
                                color="text-blue-600"
                            />
                            <StatCard
                                title="Active Users"
                                value={analytics.users.active}
                                icon={Activity}
                                color="text-green-600"
                            />
                            <StatCard
                                title="Total Chats"
                                value={analytics.chats.total}
                                icon={MessageSquare}
                                color="text-purple-600"
                            />
                            <StatCard
                                title="Superusers"
                                value={analytics.users.superusers}
                                icon={Shield}
                                color="text-indigo-600"
                            />
                        </div>

                        {/* Time-based Stats */}
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                            <div className="bg-white rounded-xl shadow-lg p-6">
                                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                                    <Calendar className="w-5 h-5 mr-2 text-blue-600" />
                                    Today's Activity
                                </h3>
                                <div className="space-y-3">
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">New Users</span>
                                        <span className="font-semibold text-blue-600">{analytics.users.today}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Chats</span>
                                        <span className="font-semibold text-purple-600">{analytics.chats.today}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Conversations</span>
                                        <span className="font-semibold text-green-600">{analytics.conversations.today}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="bg-white rounded-xl shadow-lg p-6">
                                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                                    <TrendingUp className="w-5 h-5 mr-2 text-green-600" />
                                    This Week
                                </h3>
                                <div className="space-y-3">
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">New Users</span>
                                        <span className="font-semibold text-blue-600">{analytics.users.this_week}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Chats</span>
                                        <span className="font-semibold text-purple-600">{analytics.chats.this_week}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Conversations</span>
                                        <span className="font-semibold text-green-600">{analytics.conversations.this_week}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="bg-white rounded-xl shadow-lg p-6">
                                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                                    <Activity className="w-5 h-5 mr-2 text-purple-600" />
                                    This Month
                                </h3>
                                <div className="space-y-3">
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">New Users</span>
                                        <span className="font-semibold text-blue-600">{analytics.users.this_month}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Chats</span>
                                        <span className="font-semibold text-purple-600">{analytics.chats.this_month}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Conversations</span>
                                        <span className="font-semibold text-green-600">{analytics.conversations.this_month}</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Most Active Users */}
                        <div className="bg-white rounded-xl shadow-lg p-6">
                            <h3 className="text-lg font-semibold text-gray-900 mb-4">Most Active Users</h3>
                            <div className="space-y-3">
                                {analytics.most_active_users.map((user, index) => (
                                    <div key={user.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                        <div className="flex items-center space-x-3">
                                            <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full flex items-center justify-center text-white font-semibold">
                                                {index + 1}
                                            </div>
                                            <div>
                                                <p className="font-medium text-gray-900">{user.full_name || user.email}</p>
                                                <p className="text-sm text-gray-500">{user.email}</p>
                                            </div>
                                        </div>
                                        <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                                            {user.chat_count} chats
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* Users Tab */}
                {activeTab === 'users' && (
                    <div className="space-y-6">
                        {/* User Management Header */}
                        <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
                            <div className="flex items-center space-x-4">
                                <div className="relative">
                                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                                    <input
                                        type="text"
                                        placeholder="Search users..."
                                        value={searchTerm}
                                        onChange={(e) => setSearchTerm(e.target.value)}
                                        className="pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all duration-200 w-64 text-gray-900"
                                    />
                                </div>
                            </div>
                            <button
                                onClick={handleCreateUser}
                                className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105"
                            >
                                <UserPlus className="w-5 h-5" />
                                <span>Create User</span>
                            </button>
                        </div>

                        {/* Users Table */}
                        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
                            <div className="overflow-x-auto">
                                <table className="min-w-full divide-y divide-gray-200">
                                    <thead className="bg-gray-50">
                                        <tr>
                                            <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                                            <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                            <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Activity</th>
                                            <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Joined</th>
                                            <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody className="bg-white divide-y divide-gray-200">
                                        {users.map((user) => (
                                            <tr key={user.id} className="hover:bg-gray-50 transition-colors duration-200">
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <div className="flex items-center space-x-3">
                                                        <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full flex items-center justify-center text-white font-semibold">
                                                            {user.full_name.charAt(0).toUpperCase() || user.email.charAt(0).toUpperCase()}
                                                        </div>
                                                        <div>
                                                            <p className="font-medium text-gray-900">{user.full_name || `${user.first_name} ${user.last_name}`.trim()}</p>
                                                            <p className="text-sm text-gray-500">{user.email}</p>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <div className="flex flex-col space-y-1">
                                                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${user.is_active
                                                            ? 'bg-green-100 text-green-800'
                                                            : 'bg-red-100 text-red-800'
                                                            }`}>
                                                            {user.is_active ? 'Active' : 'Inactive'}
                                                        </span>
                                                        {user.is_superuser && (
                                                            <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800">
                                                                Admin
                                                            </span>
                                                        )}
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                    <div>
                                                        <p>{user.total_chats} chats</p>
                                                        <p>{user.total_conversations} conversations</p>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                    {new Date(user.date_joined).toLocaleDateString()}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                                    <div className="flex items-center space-x-2">
                                                        <button
                                                            onClick={() => handleEditUser(user)}
                                                            className="text-blue-600 hover:text-blue-900 p-2 hover:bg-blue-50 rounded-lg transition-colors duration-200"
                                                        >
                                                            <Edit className="w-4 h-4" />
                                                        </button>
                                                        <button
                                                            onClick={() => handleDeleteUser(user.id)}
                                                            className="text-red-600 hover:text-red-900 p-2 hover:bg-red-50 rounded-lg transition-colors duration-200"
                                                        >
                                                            <Trash2 className="w-4 h-4" />
                                                        </button>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>

                            {/* Pagination */}
                            {totalPages > 1 && (
                                <div className="bg-gray-50 px-6 py-4 flex items-center justify-between">
                                    <p className="text-sm text-gray-700">
                                        Page {currentPage} of {totalPages}
                                    </p>
                                    <div className="flex space-x-2">
                                        <button
                                            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                                            disabled={currentPage === 1}
                                            className="px-3 py-1 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed text-black"
                                        >
                                            Previous
                                        </button>
                                        <button
                                            onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                                            disabled={currentPage === totalPages}
                                            className="px-3 py-1 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed text-black"
                                        >
                                            Next
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Sessions Tab */}
                {activeTab === 'sessions' && (
                    <div className="space-y-6">
                        <div className="flex justify-between items-center">
                            <div>
                                <h2 className="text-2xl font-bold text-gray-900">Active User Sessions</h2>
                                <p className="text-gray-700 mt-2">
                                    Manage all currently logged-in users. Sessions automatically refresh every 30 seconds. Only active sessions are shown - inactive and expired sessions are automatically cleaned up.
                                </p>
                                {lastSessionUpdate && (
                                    <p className="text-sm text-gray-500 mt-1">
                                        Last updated: {lastSessionUpdate.toLocaleTimeString()}
                                        {isSessionsLoading && <span className="ml-2 text-blue-600">• Refreshing...</span>}
                                    </p>
                                )}
                            </div>
                            <button
                                onClick={updateSessionList}
                                disabled={isSessionsLoading}
                                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <RefreshCw className={`w-4 h-4 ${isSessionsLoading ? 'animate-spin' : ''}`} />
                                <span>{isSessionsLoading ? 'Refreshing...' : 'Refresh'}</span>
                            </button>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="bg-white rounded-lg shadow p-4">
                                <div className="flex items-center">
                                    <Users className="w-8 h-8 text-blue-600" />
                                    <div className="ml-4">
                                        <p className="text-sm font-medium text-gray-600">Total Sessions</p>
                                        <p className="text-2xl font-bold text-gray-900">{activeSessions.length}</p>
                                    </div>
                                </div>
                            </div>
                            <div className="bg-white rounded-lg shadow p-4">
                                <div className="flex items-center">
                                    <Crown className="w-8 h-8 text-yellow-600" />
                                    <div className="ml-4">
                                        <p className="text-sm font-medium text-gray-600">Admin Sessions</p>
                                        <p className="text-2xl font-bold text-gray-900">{activeSessions.filter(s => s.is_superuser).length}</p>
                                    </div>
                                </div>
                            </div>
                            <div className="bg-white rounded-lg shadow p-4">
                                <div className="flex items-center">
                                    <User className="w-8 h-8 text-green-600" />
                                    <div className="ml-4">
                                        <p className="text-sm font-medium text-gray-600">User Sessions</p>
                                        <p className="text-2xl font-bold text-gray-900">{activeSessions.filter(s => !s.is_superuser).length}</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {sessionCleanupStats && sessionCleanupStats.total > 0 && (
                            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                                <h3 className="text-sm font-medium text-green-800 mb-2">Last Session Cleanup</h3>
                                <div className="text-xs text-green-700">
                                    <p>Cleaned up {sessionCleanupStats.total} old sessions:</p>
                                    <ul className="ml-4 mt-1">
                                        {sessionCleanupStats.expired > 0 && <li>• {sessionCleanupStats.expired} expired sessions</li>}
                                        {sessionCleanupStats.inactive > 0 && <li>• {sessionCleanupStats.inactive} inactive sessions</li>}
                                        {sessionCleanupStats.stale > 0 && <li>• {sessionCleanupStats.stale} stale sessions (inactive &gt; 30 min)</li>}
                                    </ul>
                                </div>
                            </div>
                        )}

                        {activeSessions.length === 0 ? (
                            <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6 text-center text-gray-800">
                                <p>No active sessions found.</p>
                            </div>
                        ) : (
                            <div className="bg-white rounded-xl shadow-lg overflow-hidden">
                                <div className="overflow-x-auto">
                                    <table className="min-w-full divide-y divide-gray-200">
                                        <thead className="bg-gray-50">
                                            <tr>
                                                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                                                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Device & Location</th>
                                                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Activity</th>
                                                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody className="bg-white divide-y divide-gray-200">
                                            {activeSessions.map((session) => (
                                                <tr key={session.session_id} className="hover:bg-gray-50 transition-colors duration-200">
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <div className="flex items-center space-x-3">
                                                            {getUserIcon(session)}
                                                            <div>
                                                                <div className="flex items-center space-x-2">
                                                                    <p className="font-medium text-gray-900">{session.full_name || session.email}</p>
                                                                    {getUserBadge(session)}
                                                                </div>
                                                                <p className="text-sm text-gray-500">{session.email}</p>
                                                            </div>
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <div className="text-sm text-gray-900">{session.device_info}</div>
                                                        <div className="text-sm text-gray-500">{session.ip_address}</div>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                        {new Date(session.last_activity).toLocaleString()}
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                                        <button
                                                            onClick={(e) => handleLogoutSpecificUser(session.session_id, e)}
                                                            className="text-red-600 hover:text-red-900 p-2 hover:bg-red-50 rounded-lg transition-colors duration-200"
                                                            title="End user session"
                                                        >
                                                            <LogOut className="w-4 h-4" />
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                                <div className="bg-gray-50 px-6 py-4 flex justify-between items-center">
                                    <p className="text-sm text-gray-600">
                                        {activeSessions.length} active session{activeSessions.length !== 1 ? 's' : ''}
                                    </p>
                                    <button
                                        onClick={handleLogoutAllUsers}
                                        className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200 font-medium"
                                    >
                                        <LogOut className="w-4 h-4" />
                                        <span>Log Out All Users</span>
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* User Create/Edit Modal */}
            {showUserModal && (
                <div className="fixed inset-0 z-50 overflow-y-auto">
                    <div className="flex min-h-screen items-center justify-center p-4">
                        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity duration-300" onClick={() => setShowUserModal(false)} />

                        <div className="relative bg-white rounded-3xl shadow-2xl w-full max-w-md p-8 transform transition-all duration-300">
                            <button
                                onClick={() => setShowUserModal(false)}
                                className="absolute top-6 right-6 text-gray-400 hover:text-gray-600 transition-colors duration-200 hover:rotate-90 transform"
                            >
                                <X className="w-6 h-6" />
                            </button>

                            <div className="text-center mb-8">
                                <div className="w-16 h-16 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <UserPlus className="w-8 h-8 text-white" />
                                </div>
                                <h2 className="text-2xl font-bold text-gray-900">
                                    {editingUser ? 'Edit User' : 'Create New User'}
                                </h2>
                            </div>

                            <form onSubmit={(e) => { e.preventDefault(); handleSaveUser(); }} className="space-y-6">
                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 mb-3">Email Address</label>
                                    <input
                                        type="email"
                                        value={userForm.email}
                                        onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                                        className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all duration-200 text-gray-900 bg-white"
                                        required
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 mb-3">Full Name</label>
                                    <input
                                        type="text"
                                        value={userForm.full_name}
                                        onChange={(e) => setUserForm({ ...userForm, full_name: e.target.value })}
                                        className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all duration-200 text-gray-900 bg-white"
                                        required
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 mb-3">
                                        Password {editingUser && '(leave blank to keep current)'}
                                    </label>
                                    <input
                                        type="password"
                                        value={userForm.password}
                                        onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
                                        className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all duration-200 text-gray-900 bg-white"
                                        required={!editingUser}
                                    />
                                </div>

                                <div className="space-y-4">
                                    <label className="flex items-center space-x-3 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={userForm.is_active}
                                            onChange={(e) => setUserForm({ ...userForm, is_active: e.target.checked })}
                                            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                                        />
                                        <span className="text-sm font-medium text-gray-700">Active User</span>
                                    </label>

                                    <label className="flex items-center space-x-3 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={userForm.is_superuser}
                                            onChange={(e) => setUserForm({ ...userForm, is_superuser: e.target.checked })}
                                            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                                        />
                                        <span className="text-sm font-medium text-gray-700">Admin User</span>
                                    </label>
                                </div>

                                <div className="flex space-x-4 pt-4">
                                    <button
                                        type="button"
                                        onClick={() => setShowUserModal(false)}
                                        className="flex-1 py-3 px-4 border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 transition-colors duration-200"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        type="submit"
                                        className="flex-1 py-3 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 flex items-center justify-center space-x-2"
                                    >
                                        <Save className="w-4 h-4" />
                                        <span>{editingUser ? 'Update' : 'Create'}</span>
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
} 