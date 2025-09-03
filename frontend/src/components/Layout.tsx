import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import './styles.css'

export default function Layout({ children }: { children: React.ReactNode }) {
  const { token, role, logout } = useAuth()
  const nav = useNavigate()
  return (
    <div className="container">
      <header className="nav">
        <div className="brand">Airbnb Cleaning SaaS</div>
        <nav className="links">
          <Link to="/">Home</Link>
          <Link to="/host">Host</Link>
          <Link to="/cleaner">Cleaner</Link>
          <Link to="/jobs">Jobs</Link>
        </nav>
        <div className="auth">
          {token ? (
            <>
              <span className="role">{role}</span>
              <button onClick={()=>{logout(); nav('/')}}>Logout</button>
            </>
          ) : (<span>Signed out</span>)}
        </div>
      </header>
      <main className="content">{children}</main>
    </div>
  )
}

