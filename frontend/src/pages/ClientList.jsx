import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { adminAPI } from '../api/client'
import Modal from '../components/Modal'

function ClientList() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const [clients, setClients] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [pageSize] = useState(10)
  const [showModal, setShowModal] = useState(false)
  const [formData, setFormData] = useState({
    login: '',
    password: '',
    passwordConfirm: '',
    product: 'survival_macro',
    deviceLimit: 1,
    licenseDays: 30,
  })
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    loadClients()
  }, [page, search, statusFilter, token])

  const loadClients = async () => {
    try {
      setLoading(true)
      const response = await adminAPI.getClients(page, pageSize, search, statusFilter, token)
      setClients(response.data.items)
      setTotal(response.data.total)
      setError('')
    } catch (err) {
      setError('Failed to load clients')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateClient = async (e) => {
    e.preventDefault()
    try {
      setCreating(true)
      await adminAPI.createClient(
        formData.login,
        formData.password,
        formData.passwordConfirm,
        formData.deviceLimit,
        formData.licenseDays,
        formData.product,
        token
      )
      setFormData({
        login: '',
        password: '',
        passwordConfirm: '',
        product: 'survival_macro',
        deviceLimit: 1,
        licenseDays: 30,
      })
      setShowModal(false)
      await loadClients()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create client')
    } finally {
      setCreating(false)
    }
  }

  const handleDeleteClient = async (clientId) => {
    if (confirm('Are you sure you want to delete this client?')) {
      try {
        await adminAPI.deleteClient(clientId, token)
        await loadClients()
      } catch (err) {
        setError('Failed to delete client')
      }
    }
  }

  const totalPages = Math.ceil(total / pageSize)

  return (
    <main style={styles.container}>
      <div style={styles.card}>
        <div style={styles.header}>
          <h2 style={styles.title}>Clients</h2>
          <button
            style={styles.createBtn}
            onClick={() => setShowModal(true)}
          >
            + Create Client
          </button>
        </div>

        {error && <div style={styles.error}>{error}</div>}

        <div style={styles.searchBar}>
          <input
            type="text"
            placeholder="Search by login..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setPage(1)
            }}
            style={styles.searchInput}
          />
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value)
              setPage(1)
            }}
            style={styles.select}
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>

        {loading ? (
          <div style={styles.loading}>Loading clients...</div>
        ) : clients.length === 0 ? (
          <div style={styles.empty}>No clients found</div>
        ) : (
          <>
            <table style={styles.table}>
              <thead>
                <tr>
                  <th>Login</th>
                  <th>Product</th>
                  <th>Status</th>
                  <th>Devices</th>
                  <th>License Expires</th>
                  <th>Days Left</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {clients.map((client) => (
                  <tr key={client.id}>
                    <td>{client.login}</td>
                    <td>{client.product || 'N/A'}</td>
                    <td>
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
                    </td>
                    <td>{client.devices_count || 0}</td>
                    <td>
                      {client.license_expires_at
                        ? new Date(client.license_expires_at).toLocaleDateString()
                        : 'N/A'}
                    </td>
                    <td>
                      <span
                        style={{
                          color: client.days_until_expiry < 0 ? '#a0451a' : '#4a7c4e',
                        }}
                      >
                        {client.days_until_expiry || 0}
                      </span>
                    </td>
                    <td>{new Date(client.created_at).toLocaleDateString()}</td>
                    <td style={styles.actions}>
                      <button
                        style={styles.btnSmall}
                        onClick={() => navigate(`/clients/${client.id}`)}
                      >
                        View
                      </button>
                      <button
                        style={{ ...styles.btnSmall, ...styles.btnDanger }}
                        onClick={() => handleDeleteClient(client.id)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {totalPages > 1 && (
              <div style={styles.pagination}>
                <button
                  disabled={page === 1}
                  onClick={() => setPage(page - 1)}
                  style={styles.paginationBtn}
                >
                  Previous
                </button>
                <span style={styles.pageInfo}>
                  Page {page} of {totalPages}
                </span>
                <button
                  disabled={page === totalPages}
                  onClick={() => setPage(page + 1)}
                  style={styles.paginationBtn}
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>

      <Modal
        isOpen={showModal}
        title="Create New Client"
        onClose={() => setShowModal(false)}
      >
        <form onSubmit={handleCreateClient} style={styles.form}>
          <div style={styles.formGroup}>
            <label>Login (3-50 chars)</label>
            <input
              type="text"
              value={formData.login}
              onChange={(e) =>
                setFormData({ ...formData, login: e.target.value })
              }
              required
              minLength="3"
              maxLength="50"
              style={styles.formInput}
            />
          </div>

          <div style={styles.formGroup}>
            <label>Product</label>
            <select
              value={formData.product}
              onChange={(e) =>
                setFormData({ ...formData, product: e.target.value })
              }
              style={styles.formInput}
            >
              <option value="survival_macro">Survival Macro</option>
              <option value="survival_vision">Survival Vision</option>
            </select>
          </div>

          <div style={styles.formGroup}>
            <label>Password (min 8 chars)</label>
            <input
              type="password"
              value={formData.password}
              onChange={(e) =>
                setFormData({ ...formData, password: e.target.value })
              }
              required
              minLength="8"
              style={styles.formInput}
            />
          </div>

          <div style={styles.formGroup}>
            <label>Confirm Password</label>
            <input
              type="password"
              value={formData.passwordConfirm}
              onChange={(e) =>
                setFormData({ ...formData, passwordConfirm: e.target.value })
              }
              required
              minLength="8"
              style={styles.formInput}
            />
          </div>

          <div style={styles.formGroup}>
            <label>Device Limit</label>
            <select
              value={formData.deviceLimit}
              onChange={(e) =>
                setFormData({ ...formData, deviceLimit: parseInt(e.target.value) })
              }
              style={styles.formInput}
            >
              <option value="1">1 Computer</option>
              <option value="2">2 Computers</option>
              <option value="3">3 Computers</option>
              <option value="5">5 Computers</option>
              <option value="10">10 Computers</option>
            </select>
          </div>

          <div style={styles.formGroup}>
            <label>License Duration (Days)</label>
            <select
              value={formData.licenseDays}
              onChange={(e) =>
                setFormData({ ...formData, licenseDays: parseInt(e.target.value) })
              }
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
              onClick={() => setShowModal(false)}
              style={styles.btnCancel}
            >
              Cancel
            </button>
            <button type="submit" style={styles.btnSubmit} disabled={creating}>
              {creating ? 'Creating...' : 'Create'}
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
    fontSize: '18px',
  },
  createBtn: {
    backgroundColor: '#c84c2c',
    color: 'white',
    border: 'none',
    padding: '10px 20px',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '12px',
    fontWeight: 'bold',
  },
  searchBar: {
    display: 'flex',
    gap: '10px',
    marginBottom: '20px',
  },
  searchInput: {
    flex: 1,
    backgroundColor: '#252525',
    border: '1px solid #3a3a3a',
    color: '#e8e4d0',
    padding: '10px',
    borderRadius: '4px',
    fontSize: '13px',
  },
  select: {
    backgroundColor: '#252525',
    border: '1px solid #3a3a3a',
    color: '#e8e4d0',
    padding: '10px',
    borderRadius: '4px',
    fontSize: '13px',
    minWidth: '150px',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    marginTop: '15px',
  },
  badge: {
    display: 'inline-block',
    padding: '4px 8px',
    borderRadius: '3px',
    fontSize: '11px',
    fontWeight: 'bold',
    textTransform: 'uppercase',
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
    gap: '8px',
  },
  btnSmall: {
    backgroundColor: '#c84c2c',
    color: 'white',
    border: 'none',
    padding: '6px 12px',
    borderRadius: '3px',
    cursor: 'pointer',
    fontSize: '11px',
  },
  btnDanger: {
    backgroundColor: '#a0451a',
  },
  pagination: {
    display: 'flex',
    justifyContent: 'center',
    gap: '10px',
    marginTop: '20px',
  },
  paginationBtn: {
    backgroundColor: '#c84c2c',
    color: 'white',
    border: 'none',
    padding: '8px 16px',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '12px',
  },
  pageInfo: {
    color: '#7a7068',
    fontSize: '12px',
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
    marginTop: '10px',
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
  error: {
    backgroundColor: '#a0451a',
    color: 'white',
    padding: '12px',
    borderRadius: '4px',
    marginBottom: '15px',
  },
  loading: {
    color: '#7a7068',
    textAlign: 'center',
    padding: '40px',
  },
  empty: {
    color: '#7a7068',
    textAlign: 'center',
    padding: '40px',
  },
}

export default ClientList
