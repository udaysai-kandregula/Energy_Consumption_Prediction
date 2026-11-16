
import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './style.css'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, info) {
    console.error('React component crashed:', error)
    console.error('Component details:', info.componentStack)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 30, color: 'red' }}>
          <h2>Dashboard Error</h2>
          <pre>{this.state.error?.message}</pre>
          <p>Open Chrome Console (F12) for more details.</p>
        </div>
      )
    }

    return this.props.children
  }
}

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
)
