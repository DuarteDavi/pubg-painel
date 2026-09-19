import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { authAPI } from '../api/client'

function Header() {
  const navigate = useNavigate()
  const location = useLocation()
  const { token, logout } = useAuth()

  const handleLogout = async () => {
    try {
      if (token) {
        await authAPI.logout(token)
      }
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      logout()
      navigate('/login')
    }
  }

  const isActive = (path) => location.pathname === path

  return (
    <header style={styles.header}>
      <div style={styles.left}>
        <h1 style={styles.title}>SURVIVAL MACRO</h1>
        <p style={styles.subtitle}>ACCESS CONTROL</p>
      </div>

      <nav style={styles.nav}>
        <a
          href="/"
          onClick={(e) => {
            e.preventDefault()
            navigate('/')
          }}
          style={{
            ...styles.navLink,
            ...(isActive('/') && styles.navLinkActive),
          }}
        >
          Dashboard
        </a>
        <a
          href="/clients"
          onClick={(e) => {
            e.preventDefault()
            navigate('/clients')
          }}
          style={{
            ...styles.navLink,
            ...(isActive('/clients') && styles.navLinkActive),
          }}
        >
          Clients
        </a>
      </nav>

      <button onClick={handleLogout} style={styles.logoutBtn}>
        Logout
      </button>
    </header>
  )
}

const styles = {
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
    borderBottom: '2px solid #c84c2c',
    padding: '20px',
    gap: '20px',
  },
  left: {
    flex: 1,
  },
  title: {
    color: '#c84c2c',
    fontSize: '20px',
    fontWeight: 'bold',
    margin: 0,
  },
  subtitle: {
    color: '#c9a961',
    fontSize: '10px',
    margin: '4px 0 0 0',
    letterSpacing: '1px',
  },
  nav: {
    display: 'flex',
    gap: '20px',
    flex: 1,
    justifyContent: 'center',
  },
  navLink: {
    color: '#e8e4d0',
    textDecoration: 'none',
    fontSize: '12px',
    fontWeight: 'bold',
    padding: '8px 12px',
    borderBottom: '2px solid transparent',
    cursor: 'pointer',
    transition: 'all 0.2s',
    textTransform: 'uppercase',
  },
  navLinkActive: {
    color: '#c84c2c',
    borderBottomColor: '#c84c2c',
  },
  logoutBtn: {
    backgroundColor: '#c84c2c',
    color: 'white',
    border: 'none',
    padding: '8px 16px',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '12px',
    fontWeight: 'bold',
    textTransform: 'uppercase',
    transition: 'background-color 0.2s',
  },
}

export default Header
