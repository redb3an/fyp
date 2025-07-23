'use client'

import React, { useState, useEffect } from 'react'
import { User, ChevronDown, ChevronRight, LogOut, Crown, Shield } from 'lucide-react'
import { multiUserAuth, UserData } from '../lib/multiUserAuth'

interface UserSwitcherProps {
    onUserSwitch?: (userId: string) => void
    className?: string
    showLogoutAll?: boolean
}

export default function UserSwitcher({ onUserSwitch, className = '', showLogoutAll = true }: UserSwitcherProps) {
    const [isOpen, setIsOpen] = useState(false)
    const [activeUsers, setActiveUsers] = useState<UserData[]>([])
    const [currentUser, setCurrentUser] = useState<UserData | null>(null)

    useEffect(() => {
        updateUserList()
    }, [])

    const updateUserList = () => {
        const users = multiUserAuth.getActiveUsers()
        const current = multiUserAuth.getCurrentUserData()
        setActiveUsers(users)
        setCurrentUser(current)
    }

    const handleUserSwitch = (userId: string) => {
        if (multiUserAuth.switchToUser(userId)) {
            updateUserList()
            setIsOpen(false)
            if (onUserSwitch) {
                onUserSwitch(userId)
            } else {
                // Default behavior: reload the page to reflect the switch
                window.location.reload()
            }
        }
    }

    const handleLogoutUser = (userId: string, event: React.MouseEvent) => {
        event.stopPropagation()
        multiUserAuth.removeUserSession(userId)
        updateUserList()

        // If we logged out the current user and there are other sessions
        if (currentUser?.id.toString() === userId && multiUserAuth.getSessionCount() > 0) {
            // Switch to another user automatically
            const remainingUsers = multiUserAuth.getActiveUsers()
            if (remainingUsers.length > 0) {
                handleUserSwitch(remainingUsers[0].id.toString())
            }
        } else if (multiUserAuth.getSessionCount() === 0) {
            // No users left, redirect to login
            window.location.href = '/'
        }
    }

    const handleLogoutAll = () => {
        multiUserAuth.clearAllSessions()
        window.location.href = '/'
    }

    const getUserIcon = (user: UserData) => {
        if (user.is_superuser) {
            return <Crown className="w-4 h-4 text-yellow-600" />
        }
        return <User className="w-4 h-4 text-gray-500" />
    }

    const getUserBadge = (user: UserData) => {
        if (user.is_superuser) {
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

    if (activeUsers.length <= 1 && !showLogoutAll) {
        return null // Don't show if only one user and no logout all option
    }

    return (
        <div className={`relative ${className}`}>
            {/* Current User Display */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center space-x-2 p-2 rounded-lg bg-white border border-gray-200 shadow-sm hover:shadow-md transition-all duration-200 min-w-[200px]"
            >
                <div className="flex items-center space-x-2 flex-1">
                    {currentUser && getUserIcon(currentUser)}
                    <div className="text-left flex-1">
                        <div className="text-sm font-medium text-gray-900 truncate">
                            {currentUser?.full_name || 'No User'}
                        </div>
                        <div className="text-xs text-gray-500 truncate">
                            {currentUser?.email || ''}
                        </div>
                    </div>
                </div>
                {activeUsers.length > 1 && (
                    <div className="flex items-center space-x-1">
                        <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-1 rounded-full">
                            {activeUsers.length}
                        </span>
                        {isOpen ? (
                            <ChevronDown className="w-4 h-4 text-gray-400" />
                        ) : (
                            <ChevronRight className="w-4 h-4 text-gray-400" />
                        )}
                    </div>
                )}
            </button>

            {/* Dropdown Menu */}
            {isOpen && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto">
                    {/* Active Users Header */}
                    <div className="px-3 py-2 border-b border-gray-100">
                        <h3 className="text-sm font-medium text-gray-900">
                            Active Sessions ({activeUsers.length})
                        </h3>
                    </div>

                    {/* User List */}
                    <div className="py-1">
                        {activeUsers.map((user) => (
                            <div
                                key={user.id}
                                className={`flex items-center justify-between px-3 py-2 hover:bg-gray-50 cursor-pointer ${currentUser?.id === user.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                                    }`}
                                onClick={() => handleUserSwitch(user.id.toString())}
                            >
                                <div className="flex items-center space-x-3 flex-1 min-w-0">
                                    {getUserIcon(user)}
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center space-x-2">
                                            <span className="text-sm font-medium text-gray-900 truncate">
                                                {user.full_name}
                                            </span>
                                            {currentUser?.id === user.id && (
                                                <span className="text-xs text-blue-600 font-medium">
                                                    (Current)
                                                </span>
                                            )}
                                        </div>
                                        <div className="text-xs text-gray-500 truncate">{user.email}</div>
                                        <div className="mt-1">
                                            {getUserBadge(user)}
                                        </div>
                                    </div>
                                </div>
                                <button
                                    onClick={(e) => handleLogoutUser(user.id.toString(), e)}
                                    className="ml-2 p-1 rounded-full hover:bg-red-100 text-gray-400 hover:text-red-600 transition-colors duration-200"
                                    title="Logout this user"
                                >
                                    <LogOut className="w-4 h-4" />
                                </button>
                            </div>
                        ))}
                    </div>

                    {/* Logout All */}
                    {showLogoutAll && activeUsers.length > 1 && (
                        <div className="border-t border-gray-100">
                            <button
                                onClick={handleLogoutAll}
                                className="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 transition-colors duration-200 flex items-center space-x-2"
                            >
                                <LogOut className="w-4 h-4" />
                                <span>Logout All Users</span>
                            </button>
                        </div>
                    )}
                </div>
            )}

            {/* Backdrop */}
            {isOpen && (
                <div
                    className="fixed inset-0 z-40"
                    onClick={() => setIsOpen(false)}
                />
            )}
        </div>
    )
} 