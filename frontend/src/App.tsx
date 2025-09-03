import React, { useEffect, useMemo, useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import { api } from './api'
import { AuthProvider, Protected, useAuth } from './auth'
import Layout from './components/Layout'

function Home() {
  const [email,setEmail]=useState(''); const [password,setPassword]=useState(''); const [role,setRole]=useState<'host'|'cleaner'>('host');
  const { token } = useAuth()
  return (
    <div>
      <h2>Demo Controls</h2>
      <p className='muted'>No login required. Pick a demo role to interact with the API.</p>
      <div>Role
        <select value={role} onChange={e=>{const r=e.target.value as any; setRole(r); (window as any).setDemoRole && (window as any).setDemoRole(r)}}>
          <option value='host'>host</option>
          <option value='cleaner'>cleaner</option>
          <option value='admin'>admin</option>
        </select>
      </div>
      <div>Token: <code>{token || '(demo mode)'}</code></div>
    </div>
  )
}

function Host() {
  const [name,setName]=useState(''); const [addr,setAddr]=useState('');
  const [prop,setProp]=useState<any>(null)
  const [props,setProps]=useState<any[]>([])
  const [jobs,setJobs]=useState<any[]>([])
  const [start,setStart]=useState(''); const [end,setEnd]=useState(''); const [checklist,setChecklist]=useState('Change linens\nDust surfaces')
  useEffect(()=>{ loadMine(); loadJobs() },[])
  async function createProp(){ const r=await api.post('/properties/',{name, address:addr}); setProp(r.data); await loadMine() }
  async function loadMine(){ try { const r=await api.get('/properties/mine'); setProps(r.data) } catch {}
  }
  async function loadJobs(){ try { const r=await api.get('/jobs/me?limit=20'); setJobs(r.data) } catch {}
  }
  async function createJob(){ if(!prop && props[0]) setProp(props[0]); if(!prop) return; const items=checklist.split('\n').filter(Boolean).map(text=>({text}))
    const r=await api.post('/jobs/',{ property_id:(prop?.id||props[0]?.id), booking_start:start, booking_end:end, checklist:items }); alert('Job '+r.data.id+' created'); await loadJobs() }
  useEffect(()=>{
    // default next-day window
    const now=new Date(); const s=new Date(now.getTime()+24*3600*1000); const e=new Date(s.getTime()+3*3600*1000);
    setStart(s.toISOString().slice(0,19)); setEnd(e.toISOString().slice(0,19));
  },[])
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
      <div>Start (ISO) <input value={start} onChange={e=>setStart(e.target.value)} placeholder='YYYY-MM-DDTHH:mm:ss' /></div>
      <div>End (ISO) <input value={end} onChange={e=>setEnd(e.target.value)} placeholder='YYYY-MM-DDTHH:mm:ss' /></div>
      <div><textarea value={checklist} onChange={e=>setChecklist(e.target.value)} rows={4} cols={40} /></div>
      <button onClick={createJob}>Create Job</button>
      <h3 style={{marginTop:16}}>Recent Jobs</h3>
      <ul>
        {jobs.map(j=> (
          <li key={j.id}>#{j.id} prop:{j.property_id} status:{j.status} window:{new Date(j.booking_start).toLocaleString()} → {new Date(j.booking_end).toLocaleString()}</li>
        ))}
      </ul>
    </div>
  )
}

function Cleaner(){
  const [open,setOpen]=useState<any[]>([])
  const [mine,setMine]=useState<any[]>([])
  const [claimId,setClaimId]=useState('')
  useEffect(()=>{ load(); loadMine() },[])
  async function load(){ const r=await api.get('/jobs/open?limit=20'); setOpen(r.data) }
  async function loadMine(){ const r=await api.get('/jobs/me?limit=20'); setMine(r.data) }
  async function claim(){ await api.post(`/jobs/${claimId}/claim`); alert('claimed'); await load(); await loadMine() }
  return (
    <div>
      <h2>Cleaner</h2>
      <div className='row'>
        <div className='col card'>
          <h3>Open Jobs</h3>
          <ul>{open.map(j=> <li key={j.id}>#{j.id} prop:{j.property_id} window:{new Date(j.booking_start).toLocaleString()} <button onClick={()=>setClaimId(j.id)}>select</button></li>)}</ul>
        </div>
        <div className='col card'>
          <h3>My Jobs</h3>
          <ul>{mine.map(j=> <li key={j.id}>#{j.id} prop:{j.property_id} status:{j.status}</li>)}</ul>
        </div>
      </div>
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
    <AuthProvider>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/host" element={<Protected roles={['host','admin']}><Host /></Protected>} />
          <Route path="/cleaner" element={<Protected roles={['cleaner','admin']}><Cleaner /></Protected>} />
          <Route path="/jobs" element={<Protected><Job /></Protected>} />
        </Routes>
      </Layout>
    </AuthProvider>
  )
}
