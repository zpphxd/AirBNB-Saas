import React, { useEffect, useState } from 'react'
import { Routes, Route, Link, useNavigate } from 'react-router-dom'
import { api, saveToken, getToken, setToken } from './api'

function Nav() {
  const nav = useNavigate()
  function logout() { localStorage.removeItem('token'); setToken(null); nav('/'); }
  return (
    <nav style={{display:'flex',gap:12,marginBottom:16}}>
      <Link to="/">Home</Link>
      <Link to="/host">Host</Link>
      <Link to="/cleaner">Cleaner</Link>
      <Link to="/jobs">Job</Link>
      <button onClick={logout}>Logout</button>
    </nav>
  )
}

function Home() {
  const [email,setEmail]=useState(''); const [password,setPassword]=useState(''); const [role,setRole]=useState<'host'|'cleaner'>('host');
  const [token,setTok]=useState(getToken())
  async function register() {
    const r = await api.post('/auth/register', { email, password, role })
    saveToken(r.data.token); setTok(r.data.token)
  }
  async function login() {
    const r = await api.post(`/auth/login?email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`)
    saveToken(r.data.token); setTok(r.data.token)
  }
  return (
    <div>
      <h2>Auth</h2>
      <div>Email <input value={email} onChange={e=>setEmail(e.target.value)} /></div>
      <div>Password <input type="password" value={password} onChange={e=>setPassword(e.target.value)} /></div>
      <div>Role <select value={role} onChange={e=>setRole(e.target.value as any)}><option>host</option><option>cleaner</option></select></div>
      <div style={{display:'flex',gap:8}}>
        <button onClick={register}>Register</button>
        <button onClick={login}>Login</button>
      </div>
      <div>Token: <code>{token || '(none)'}</code></div>
    </div>
  )
}

function Host() {
  const [name,setName]=useState(''); const [addr,setAddr]=useState('');
  const [prop,setProp]=useState<any>(null)
  const [props,setProps]=useState<any[]>([])
  const [start,setStart]=useState(''); const [end,setEnd]=useState(''); const [checklist,setChecklist]=useState('Change linens\nDust surfaces')
  useEffect(()=>{ loadMine() },[])
  async function createProp(){ const r=await api.post('/properties/',{name, address:addr}); setProp(r.data); await loadMine() }
  async function loadMine(){ try { const r=await api.get('/properties/mine'); setProps(r.data) } catch {}
  }
  async function createJob(){ if(!prop && props[0]) setProp(props[0]); if(!prop) return; const items=checklist.split('\n').filter(Boolean).map(text=>({text}))
    const r=await api.post('/jobs/',{ property_id:(prop?.id||props[0]?.id), booking_start:start, booking_end:end, checklist:items }); alert('Job '+r.data.id+' created') }
  return (
    <div>
      <h2>Host</h2>
      <h3>Create Property</h3>
      <input placeholder='Name' value={name} onChange={e=>setName(e.target.value)} />
      <input placeholder='Address' value={addr} onChange={e=>setAddr(e.target.value)} />
      <button onClick={createProp}>Create</button>
      <pre>{prop?JSON.stringify(prop,null,2):''}</pre>
      <h4>Your Properties</h4>
      <ul>{props.map(p=> <li key={p.id}>#{p.id} {p.name}</li>)}</ul>
      <h3>Create Job</h3>
      <div>Start ISO <input value={start} onChange={e=>setStart(e.target.value)} placeholder='2025-09-10T11:00:00Z' /></div>
      <div>End ISO <input value={end} onChange={e=>setEnd(e.target.value)} placeholder='2025-09-10T14:00:00Z' /></div>
      <div><textarea value={checklist} onChange={e=>setChecklist(e.target.value)} rows={4} cols={40} /></div>
      <button onClick={createJob}>Create Job</button>
    </div>
  )
}

function Cleaner(){
  const [open,setOpen]=useState<any[]>([])
  const [claimId,setClaimId]=useState('')
  async function load(){ const r=await api.get('/jobs/open'); setOpen(r.data) }
  async function claim(){ await api.post(`/jobs/${claimId}/claim`); alert('claimed'); await load() }
  return (
    <div>
      <h2>Cleaner</h2>
      <button onClick={load}>Load open jobs</button>
      <ul>{open.map(j=> <li key={j.id}>#{j.id} prop:{j.property_id} <button onClick={()=>setClaimId(j.id)}>select</button></li>)}</ul>
      <div>Claim selected Job ID: <input value={claimId} onChange={e=>setClaimId(e.target.value)} /><button onClick={claim}>Claim</button></div>
    </div>
  )
}

function Job(){
  const [jobId,setJobId]=useState('');
  const [job,setJob]=useState<any>(null)
  const [tick,setTick]=useState('')
  const [rating,setRating]=useState({stars:5,feedback:''})
  async function load(){ const r=await api.get(`/jobs/${jobId}`); setJob(r.data) }
  async function doTick(){ const ids=tick.split(',').map(s=>Number(s.trim())).filter(Boolean); const r=await api.post(`/jobs/${jobId}/checklist/tick`,{item_ids:ids}); setJob({...job, checklist_items:r.data}) }
  async function upload(itemId:number, file:File){ const fd=new FormData(); fd.append('file', file); const r=await api.post(`/jobs/${jobId}/checklist/${itemId}/photo`,fd,{headers:{}}); alert('uploaded '+r.data.photo_path) }
  async function complete(){ await api.post(`/jobs/${jobId}/complete`); alert('completed') }
  async function rate(){ await api.post(`/jobs/${jobId}/rating`, rating); alert('rated') }
  return (
    <div>
      <h2>Job</h2>
      <div>Job ID <input value={jobId} onChange={e=>setJobId(e.target.value)} /> <button onClick={load}>Load</button></div>
      {job && (
        <div>
          <div>Status: {job.status}</div>
          <h4>Checklist</h4>
          <ul>
            {job.checklist_items?.map((it:any)=> (
              <li key={it.id}>
                #{it.id} {it.text} {it.checked?'[✓]':''}
                <input type="file" onChange={e=> e.target.files && upload(it.id, e.target.files[0])} />
              </li>
            ))}
          </ul>
          <div>Tick IDs: <input value={tick} onChange={e=>setTick(e.target.value)} placeholder="1,2" /> <button onClick={doTick}>Tick</button></div>
          <button onClick={complete}>Mark Complete</button>
          <h4>Rate</h4>
          <div>Stars <input type="number" min={1} max={5} value={rating.stars} onChange={e=>setRating({...rating, stars:Number(e.target.value)})} /> Feedback <input value={rating.feedback} onChange={e=>setRating({...rating, feedback:e.target.value})} /></div>
          <button onClick={rate}>Submit Rating</button>
        </div>
      )}
    </div>
  )
}

export default function App(){
  return (
    <div style={{padding:16}}>
      <h1>Airbnb Cleaning & Maintenance</h1>
      <Nav />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/host" element={<Host />} />
        <Route path="/cleaner" element={<Cleaner />} />
        <Route path="/jobs" element={<Job />} />
      </Routes>
    </div>
  )
}

