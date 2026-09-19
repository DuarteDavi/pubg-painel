import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { adminAPI } from '../api/client'

function Dashboard() {
  const { token } = useAuth()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadDashboard()
  }, [token])

  const loadDashboard = async () => {
    try {
      setLoading(true)
      const response = await adminAPI.getDashboard(token)
      setStats(response.data)
      setError('')
    } catch (err) {
      setError('Failed to load dashboard')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <main style={styles.container}>
        <div style={styles.loading}>Loading dashboard...</div>
      </main>
    )
  }

  if (error) {
    return (
      <main style={styles.container}>
        <div style={styles.error}>{error}</div>
      </main>
    )
  }

  return (
    <main style={styles.container}>
      <div style={styles.card}>
        <h2 style={styles.title}>Dashboard</h2>

        <div style={styles.statsGrid}>
          <div style={styles.statBox}>
            <div style={styles.statLabel}>Total Clients</div>
            <div style={styles.statValue}>{stats?.total_clients || 0}</div>
          </div>

          <div style={styles.statBox}>
            <div style={styles.statLabel}>Active Licenses</div>
            <div style={{ ...styles.statValue, color: '#4a7c4e' }}>
              {stats?.active_licenses || 0}
            </div>
          </div>

          <div style={styles.statBox}>
            <div style={styles.statLabel}>Expired Licenses</div>
            <div style={{ ...styles.statValue, color: '#a0451a' }}>
              {stats?.expired_licenses || 0}
            </div>
          </div>

          <div style={styles.statBox}>
            <div style={styles.statLabel}>Disabled Licenses</div>
            <div style={{ ...styles.statValue, color: '#c9a961' }}>
              {stats?.disabled_licenses || 0}
            </div>
          </div>

          <div style={styles.statBox}>
            <div style={styles.statLabel}>Total Devices</div>
            <div style={styles.statValue}>{stats?.total_devices || 0}</div>
          </div>

          <div style={styles.statBox}>
            <div style={styles.statLabel}>Recent Logins (24h)</div>
            <div style={styles.statValue}>{stats?.recent_logins || 0}</div>
          </div>
        </div>
      </div>

      <div style={styles.card}>
        <h2 style={styles.title}>About</h2>
        <p style={styles.text}>
          Survival Macro Access Control Panel v1.0
        </p>
        <p style={styles.text}>
          Manage licenses, devices, and client access.
        </p>
      </div>
    </main>
  )
}

const styles = {
  container: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '20px',
  },
  card: {
    backgroundColor: '#1a1a1a',
    border: '1px solid #3a3a3a',
    borderRadius: '6px',
    padding: '20px',
    marginBottom: '20px',
  },
  title: {
    color: '#c84c2c',
    margin: '0 0 20px 0',
    fontSize: '18px',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: '15px',
  },
  statBox: {
    backgroundColor: '#252525',
    border: 'none',
    borderLeft: '4px solid #c84c2c',
    padding: '15px',
    borderRadius: '4px',
  },
  statLabel: {
    color: '#7a7068',
    fontSize: '11px',
    textTransform: 'uppercase',
    marginBottom: '8px',
  },
  statValue: {
    fontSize: '28px',
    color: '#c84c2c',
    fontWeight: 'bold',
  },
  text: {
    color: '#e8e4d0',
    margin: '10px 0',
  },
  error: {
    backgroundColor: '#a0451a',
    color: 'white',
    padding: '15px',
    borderRadius: '4px',
  },
  loading: {
    color: '#7a7068',
    textAlign: 'center',
    padding: '40px',
  },
}

export default Dashboard
