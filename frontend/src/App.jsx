import {useState,useEffect,useCallback} from 'react'
const MODULES={patients:['Patients',['name','age','gender','phone','address','status']],
 appointments:['Appointments',['patient','doctor','date','time','status']],
 records:['Medical records',['patient','diagnosis','prescription','notes','date']],
 lab:['Laboratory',['patient','test','result','status','date']],
 pharmacy:['Pharmacy',['medicine','stock','price','expiry']],
 billing:['Billing',['patient','description','amount','insurance','status']],
 audit:['Audit trail',['ts','user','action','resource','rid'],true]}
const api=async(path,tok,opt={})=>{const r=await fetch('/api/'+path,{...opt,headers:{'Content-Type':'application/json',Authorization:'Bearer '+tok}})
 const j=await r.json();if(!r.ok)throw new Error(j.detail||'Request failed');return j}

function Login({onLogin}){const[u,setU]=useState('admin'),[p,setP]=useState('admin123'),[e,setE]=useState('')
 const go=async()=>{try{const r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});const j=await r.json();if(!r.ok)throw new Error(j.detail);onLogin(j)}catch(x){setE(x.message)}}
 return <div className="login"><h2>MEDICONNECT</h2><input value={u} onChange={x=>setU(x.target.value)} aria-label="Username"/>
 <input type="password" value={p} onChange={x=>setP(x.target.value)} aria-label="Password"/>
 <button className="p" onClick={go}>Sign in</button><p className="err">{e}</p>
 <p className="hint">Demo: admin/admin123, drsmith/doctor123, nancy/nurse123, ravi/pharma123, lena/lab123, bill/bill123, rita/desk123</p></div>}

function Dashboard({tok}){const[s,setS]=useState({});useEffect(()=>{api('dashboard/stats',tok).then(setS)},[tok])
 const L={patients:'Patients',appointments_today:'Appointments today',pending_labs:'Pending lab tests',low_stock:'Low-stock medicines',unpaid:'Unpaid bills'}
 return <><h2>Hospital overview</h2><div className="stats">{Object.keys(L).map(k=><div className="stat" key={k}><b>{s[k]??'-'}</b>{L[k]}</div>)}</div></>}

function Module({name,tok}){const[title,fields,ro]=MODULES[name];const[rows,setRows]=useState([]),[f,setF]=useState({}),[q,setQ]=useState(''),[err,setErr]=useState('')
 const load=useCallback(()=>api(name,tok).then(setRows).catch(x=>setErr(x.message)),[name,tok])
 useEffect(()=>{setErr('');setF({});load()},[load])
 const save=async e=>{e.preventDefault();try{await api(name,tok,{method:'POST',body:JSON.stringify(f)});setF({});setErr('');load()}catch(x){setErr(x.message)}}
 const del=async id=>{try{await api(`${name}/${id}`,tok,{method:'DELETE'});load()}catch(x){setErr(x.message)}}
 const shown=rows.filter(r=>JSON.stringify(r).toLowerCase().includes(q.toLowerCase()))
 return <><h2>{title}</h2>
 {!ro&&<form onSubmit={save}>{fields.map(k=><input key={k} placeholder={k} value={f[k]||''} onChange={e=>setF({...f,[k]:e.target.value})}/>)}<button className="p">Add record</button></form>}
 <input placeholder="Search" value={q} onChange={e=>setQ(e.target.value)} style={{marginBottom:12}}/><p className="err">{err}</p>
 <table><thead><tr>{fields.map(k=><th key={k}>{k}</th>)}{!ro&&<th/>}</tr></thead><tbody>
 {shown.map(r=><tr key={r.id}>{fields.map(k=><td key={k}>{k==='ts'?new Date(r[k]*1000).toLocaleString():r[k]}</td>)}{!ro&&<td><button className="d" onClick={()=>del(r.id)}>Delete</button></td>}</tr>)}
 {!shown.length&&<tr><td colSpan={fields.length+1}>No records yet. Add the first one above.</td></tr>}</tbody></table></>}

export default function App(){const[s,setS]=useState(()=>JSON.parse(sessionStorage.getItem('mc')||'null')),[tab,setTab]=useState('dash')
 const login=x=>{sessionStorage.setItem('mc',JSON.stringify(x));setS(x)},out=()=>{sessionStorage.removeItem('mc');setS(null)}
 if(!s)return <Login onLogin={login}/>
 return <div className="app"><nav><h1>MEDICONNECT</h1><button className={tab==='dash'?'on':''} onClick={()=>setTab('dash')}>Dashboard</button>
 {Object.entries(MODULES).filter(([k])=>k!=='audit'||s.role==='admin').map(([k,v])=><button key={k} className={tab===k?'on':''} onClick={()=>setTab(k)}>{v[0]}</button>)}
 <button onClick={out}>Sign out ({s.username}, {s.role})</button></nav>
 <main>{tab==='dash'?<Dashboard tok={s.token}/>:<Module key={tab} name={tab} tok={s.token}/>}</main></div>}
