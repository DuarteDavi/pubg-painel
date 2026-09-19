function Modal({ isOpen, title, onClose, children }) {
  if (!isOpen) return null

  return (
    <div style={styles.modalOverlay} onClick={onClose}>
      <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div style={styles.modalHeader}>
          <h2 style={styles.title}>{title}</h2>
          <button style={styles.closeBtn} onClick={onClose}>
            ×
          </button>
        </div>
        <div style={styles.modalBody}>{children}</div>
      </div>
    </div>
  )
}

const styles = {
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  modal: {
    backgroundColor: '#1a1a1a',
    border: '2px solid #c84c2c',
    borderRadius: '6px',
    maxWidth: '500px',
    width: '90%',
    maxHeight: '90vh',
    overflow: 'auto',
  },
  modalHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottom: '1px solid #3a3a3a',
    padding: '20px',
  },
  title: {
    color: '#c84c2c',
    margin: 0,
    fontSize: '18px',
  },
  closeBtn: {
    background: 'none',
    border: 'none',
    color: '#7a7068',
    fontSize: '28px',
    cursor: 'pointer',
    padding: 0,
  },
  modalBody: {
    padding: '20px',
  },
}

export default Modal
