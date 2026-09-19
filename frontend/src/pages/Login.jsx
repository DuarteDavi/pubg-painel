import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { authAPI } from '../api/client'

function Login() {
  const [login, setLogin] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { login: setAuthToken } = useAuth()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await authAPI.login(login, password)
      const token = response.data.access_token
      setAuthToken(token)
      navigate('/')
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Login failed'
      setError(getErrorMessage(errorMessage))
    } finally {
      setLoading(false)
    }
  }

  const getErrorMessage = (detail) => {
    const messages = {
      INVALID_CREDENTIALS: 'Invalid login or password',
      RATE_LIMITED: 'Too many login attempts. Please try again later.',
      SESSION_EXPIRED: 'Session expired. Please login again.',
    }
    return messages[detail] || detail
  }

  return (
    <div style={styles.container}>
      <div style={styles.loginBox}>
        <div style={styles.header}>
          <h1 style={styles.title}>SURVIVAL MACRO</h1>
          <div style={styles.line}></div>
          <h2 style={styles.subtitle}>ACCESS CONTROL</h2>
          <div style={styles.lineSub}></div>
        </div>

        {error && <div style={styles.error}>{error}</div>}

        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.formGroup}>
            <label htmlFor="login" style={styles.label}>
              LOGIN
            </label>
            <input
              id="login"
              type="text"
              value={login}
              onChange={(e) => setLogin(e.target.value)}
              placeholder="Enter admin login"
              style={styles.input}
              disabled={loading}
              autoFocus
            />
          </div>

          <div style={styles.formGroup}>
            <label htmlFor="password" style={styles.label}>
              PASSWORD
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              style={styles.input}
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            style={styles.button}
            disabled={loading}
          >
            {loading ? 'LOGGING IN...' : 'ENTER'}
          </button>
        </form>

        <div style={styles.footer}>
          <p style={styles.footerText}>Survival Profile v1.0</p>
          <p style={styles.footerSubText}>Controlled Access System</p>
        </div>
      </div>
    </div>
  )
}

const styles = {
  container: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '100vh',
    backgroundColor: '#0a0a0a',
    fontFamily: "'Consolas', monospace",
  },
  loginBox: {
    width: '100%',
    maxWidth: '380px',
    backgroundColor: '#1a1a1a',
    border: '1px solid #3a3a3a',
    borderRadius: '6px',
    padding: '40px',
  },
  header: {
    textAlign: 'center',
    marginBottom: '40px',
  },
  line: {
    height: '2px',
    backgroundColor: '#c84c2c',
    margin: '15px 0 10px 0',
  },
  lineSub: {
    height: '1px',
    backgroundColor: '#3a3a3a',
    margin: '15px 0',
  },
  title: {
    color: '#c84c2c',
    fontSize: '24px',
    fontWeight: 'bold',
    margin: 0,
    marginBottom: '5px',
  },
  subtitle: {
    color: '#c9a961',
    fontSize: '14px',
    fontWeight: 'bold',
    margin: 0,
    letterSpacing: '2px',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
    marginBottom: '30px',
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  label: {
    color: '#e8e4d0',
    fontSize: '11px',
    fontWeight: 'bold',
    textTransform: 'uppercase',
    letterSpacing: '1px',
  },
  input: {
    backgroundColor: '#252525',
    border: '1px solid #c84c2c',
    borderRadius: '4px',
    color: '#e8e4d0',
    padding: '12px',
    fontSize: '13px',
    fontFamily: "'Consolas', monospace",
    outline: 'none',
  },
  button: {
    backgroundColor: '#c84c2c',
    border: 'none',
    borderRadius: '4px',
    color: 'white',
    padding: '12px',
    fontSize: '14px',
    fontWeight: 'bold',
    textTransform: 'uppercase',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
  buttonHover: {
    backgroundColor: '#9d3d21',
  },
  error: {
    backgroundColor: '#a0451a',
    color: 'white',
    padding: '12px',
    borderRadius: '4px',
    marginBottom: '20px',
    fontSize: '12px',
    textAlign: 'center',
  },
  footer: {
    textAlign: 'center',
    borderTop: '1px solid #3a3a3a',
    paddingTop: '20px',
  },
  footerText: {
    color: '#7a7068',
    fontSize: '11px',
    margin: '5px 0',
  },
  footerSubText: {
    color: '#5a5050',
    fontSize: '10px',
    margin: '0',
  },
}

export default Login
