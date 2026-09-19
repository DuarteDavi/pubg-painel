import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { adminAPI } from '../api/client'
import Modal from '../components/Modal'

function ClientDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { token } = useAuth()
  const [client, setClient] = useState(null)
  const [devices, setDevices] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showRenewModal, setShowRenewModal] = useState(false)
  const [showPasswordModal, setShowPasswordModal] = useState(false)
  const [renewDays, setRenewDays] = useState(30)
  const [newPassword, setNewPassword] = useState('')

  useEffect(() => {
    loadClientData()
  }, [id, token])

  const loadClientData = async () => {
    try {
      setLoading(true)
      const [clientRes, devicesRes] = await Promise.all([
        adminAPI.getClient(id, token),
        adminAPI.getDevices(id, token),
      ])
      setClient(clientRes.data)
      setDevices(devicesRes.data)
      setError('')
    } catch (err) {
      setError('Failed to load client data')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleRenewLicense = async (e) => {
    e.preventDefault()
    try {
      await adminAPI.renewLicense(id, renewDays, token)
      setShowRenewModal(false)
      await loadClientData()
    } catch (err) {
      setError('Failed to renew license')
    }
  }

  const handleResetPassword = async (e) => {
    e.preventDefault()
    try {
      await adminAPI.resetPassword(id, newPassword, token)
      setShowPasswordModal(false)
      setNewPassword('')
      setError('Password reset successfully!')
      setTimeout(() => setError(''), 3000)
    } catch (err) {
      setError('Failed to reset password')
    }
  }

  const handleActivate = async () => {
    try {
      await adminAPI.activateClient(id, token)
      await loadClientData()
    } catch (err) {
      setError('Failed to activate client')
    }
  }

  const handleDeactivate = async () => {
    try {
      await adminAPI.deactivateClient(id, token)
      await loadClientData()
    } catch (err) {
      setError('Failed to deactivate client')
    }
  }

  const handleRemoveDevice = async (deviceId) => {
    if (confirm('Remove this device?')) {
      try {
        await adminAPI.removeDevice(id, deviceId, token)
        await loadClientData()
      } catch (err) {
        setError('Failed to remove device')
      }
    }
  }

  if (loading) {
    return (
      <main style={styles.container}>
        <div style={styles.loading}>Loading...</div>
      </main>
    )
  }

  if (!client) {
    return (
      <main style={styles.container}>
        <div style={styles.error}>Client not found</div>
      </main>
    )
  }

  const daysLeft = client.days_until_expiry || 0
  const isExpired = daysLeft < 0

  return (
    <main style={styles.container}>
      {error && <div style={styles.errorBox}>{error}</div>}

      <div style={styles.card}>
        <div style={styles.header}>
          <h2 style={styles.title}>{client.login}</h2>
          <button
            onClick={() => navigate('/clients')}
            style={styles.backBtn}
          >
            ← Back
          </button>
        </div>

        <div style={styles.infoGrid}>
          <div style={styles.infoItem}>
            <label>Status</label>
            <span
              style={{
                ...styles.badge,
                ...(client.status === 'active'
                  ? styles.badgeActive
                  : styles.badgeInactive),
              }}
            >
              {client.status}
            </span>
          </div>

          <div style={styles.infoItem}>
            <label>Created</label>
            <span>{new Date(client.created_at).toLocaleDateString()}</span>
          </div>

          <div style={styles.infoItem}>
            <label>Last Login</label>
            <span>
              {client.last_login_at
                ? new Date(client.last_login_at).toLocaleString()
                : 'Never'}
            </span>
          </div>

          <div style={styles.infoItem}>
            <label>License Expires</label>
            <span
              style={{
                color: isExpired ? '#a0451a' : '#4a7c4e',
              }}
            >
              {client.license_expires_at
                ? new Date(client.license_expires_at).toLocaleDateString()
                : 'N/A'}
            </span>
          </div>

          <div style={styles.infoItem}>
            <label>Days Until Expiry</label>
            <span
              style={{
                color: isExpired ? '#a0451a' : '#4a7c4e',
                fontSize: '18px',
                fontWeight: 'bold',
              }}
            >
              {daysLeft > 0 ? daysLeft : 'Expired'}
            </span>
          </div>

          <div style={styles.infoItem}>
            <label>Devices Linked</label>
            <span>{devices.length}</span>
          </div>
        </div>

        <div style={styles.actions}>
          {client.status === 'active' ? (
            <button onClick={handleDeactivate} style={styles.btnDanger}>
              Deactivate
            </button>
          ) : (
            <button onClick={handleActivate} style={styles.btnSuccess}>
              Activate
            </button>
          )}
          <button
            onClick={() => setShowRenewModal(true)}
            style={styles.btnPrimary}
          >
            Renew License
          </button>
          <button
            onClick={() => setShowPasswordModal(true)}
            style={styles.btnPrimary}
          >
            Reset Password
          </button>
        </div>
      </div>

      <div style={styles.card}>
        <h3 style={styles.subtitle}>Linked Devices ({devices.length})</h3>

        {devices.length === 0 ? (
          <p style={styles.emptyText}>No devices linked</p>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr>
                <th>Device Name</th>
                <th>Last IP</th>
                <th>Last Seen</th>
                <th>Linked At</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {devices.map((device) => (
                <tr key={device.id}>
                  <td>{device.device_name || 'Unknown'}</td>
                  <td>{device.last_ip || 'N/A'}</td>
                  <td>
                    {device.last_seen_at
                      ? new Date(device.last_seen_at).toLocaleString()
                      : 'N/A'}
                  </td>
                  <td>{new Date(device.linked_at).toLocaleString()}</td>
                  <td>
                    <button
                      onClick={() => handleRemoveDevice(device.id)}
                      style={styles.btnSmallDanger}
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <Modal
        isOpen={showRenewModal}
        title="Renew License"
        onClose={() => setShowRenewModal(false)}
      >
        <form onSubmit={handleRenewLicense} style={styles.form}>
          <div style={styles.formGroup}>
            <label>Duration (Days)</label>
            <select
              value={renewDays}
              onChange={(e) => setRenewDays(parseInt(e.target.value))}
              style={styles.formInput}
            >
              <option value="7">7 Days</option>
              <option value="15">15 Days</option>
              <option value="30">30 Days</option>
              <option value="90">90 Days</option>
            </select>
          </div>

          <div style={styles.formActions}>
            <button
              type="button"
              onClick={() => setShowRenewModal(false)}
              style={styles.btnCancel}
            >
              Cancel
            </button>
            <button type="submit" style={styles.btnSubmit}>
              Renew
            </button>
          </div>
        </form>
      </Modal>

      <Modal
        isOpen={showPasswordModal}
        title="Reset Password"
        onClose={() => setShowPasswordModal(false)}
      >
        <form onSubmit={handleResetPassword} style={styles.form}>
          <div style={styles.formGroup}>
            <label>New Password (min 8 chars)</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength="8"
              style={styles.formInput}
            />
          </div>

          <div style={styles.formActions}>
            <button
              type="button"
              onClick={() => setShowPasswordModal(false)}
              style={styles.btnCancel}
            >
              Cancel
            </button>
            <button type="submit" style={styles.btnSubmit}>
              Reset
            </button>
          </div>
        </form>
      </Modal>
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
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
  },
  title: {
    color: '#c84c2c',
    margin: 0,
    fontSize: '24px',
  },
  subtitle: {
    color: '#c84c2c',
    margin: '0 0 15px 0',
    fontSize: '16px',
  },
  backBtn: {
    backgroundColor: '#3a3a3a',
    color: '#e8e4d0',
    border: 'none',
    padding: '10px 20px',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  infoGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '20px',
    marginBottom: '30px',
  },
  infoItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  badge: {
    display: 'inline-block',
    padding: '6px 12px',
    borderRadius: '3px',
    fontSize: '12px',
    fontWeight: 'bold',
    textTransform: 'uppercase',
    width: 'fit-content',
  },
  badgeActive: {
    backgroundColor: '#4a7c4e',
    color: 'white',
  },
  badgeInactive: {
    backgroundColor: '#a0451a',
    color: 'white',
  },
  actions: {
    display: 'flex',
    gap: '10px',
    flexWrap: 'wrap',
  },
  btnPrimary: {
    backgroundColor: '#c84c2c',
    color: 'white',
    border: 'none',
    padding: '10px 20px',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '12px',
  },
  btnDanger: {
    backgroundColor: '#a0451a',
    color: 'white',
    border: 'none',
    padding: '10px 20px',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '12px',
  },
  btnSuccess: {
    backgroundColor: '#4a7c4e',
    color: 'white',
    border: 'none',
    padding: '10px 20px',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '12px',
  },
  btnSmallDanger: {
    backgroundColor: '#a0451a',
    color: 'white',
    border: 'none',
    padding: '6px 12px',
    borderRadius: '3px',
    cursor: 'pointer',
    fontSize: '11px',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '15px',
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  formInput: {
    backgroundColor: '#252525',
    border: '1px solid #3a3a3a',
    color: '#e8e4d0',
    padding: '10px',
    borderRadius: '4px',
    fontSize: '13px',
  },
  formActions: {
    display: 'flex',
    gap: '10px',
  },
  btnCancel: {
    backgroundColor: '#3a3a3a',
    color: '#e8e4d0',
    border: 'none',
    padding: '10px 20px',
    borderRadius: '4px',
    cursor: 'pointer',
    flex: 1,
  },
  btnSubmit: {
    backgroundColor: '#c84c2c',
    color: 'white',
    border: 'none',
    padding: '10px 20px',
    borderRadius: '4px',
    cursor: 'pointer',
    flex: 1,
  },
  errorBox: {
    backgroundColor: '#a0451a',
    color: 'white',
    padding: '15px',
    borderRadius: '4px',
    marginBottom: '20px',
  },
  loading: {
    color: '#7a7068',
    textAlign: 'center',
    padding: '40px',
  },
  emptyText: {
    color: '#7a7068',
    textAlign: 'center',
    padding: '20px',
  },
}

export default ClientDetail
