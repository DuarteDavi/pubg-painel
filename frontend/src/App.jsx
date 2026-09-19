import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import ClientList from './pages/ClientList'
import ClientDetail from './pages/ClientDetail'
import Header from './components/Header'

const ProtectedRoute = ({ element }) => {
  const { token } = useAuth()
  return token ? element : <Navigate to="/login" replace />
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute
                element={
                  <>
                    <Header />
                    <Dashboard />
                  </>
                }
              />
            }
          />
          <Route
            path="/clients"
            element={
              <ProtectedRoute
                element={
                  <>
                    <Header />
                    <ClientList />
                  </>
                }
              />
            }
          />
          <Route
            path="/clients/:id"
            element={
              <ProtectedRoute
                element={
                  <>
                    <Header />
                    <ClientDetail />
                  </>
                }
              />
            }
          />
        </Routes>
      </AuthProvider>
    </Router>
  )
}

export default App
