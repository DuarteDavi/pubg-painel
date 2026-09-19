import React, { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext()

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem('admin_token'))
  const [isAuthenticated, setIsAuthenticated] = useState(!!token)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (token) {
      localStorage.setItem('admin_token', token)
      setIsAuthenticated(true)
    } else {
      localStorage.removeItem('admin_token')
      setIsAuthenticated(false)
    }
  }, [token])

  const login = (newToken) => {
    setToken(newToken)
  }

  const logout = () => {
    setToken(null)
    localStorage.removeItem('admin_token')
  }

  return (
    <AuthContext.Provider value={{ token, isAuthenticated, login, logout, loading, setLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
