"""MEDICONNECT backend: FastAPI + SQLite. Run: uvicorn main:app --reload"""
import sqlite3, hashlib, os, time, jwt
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer

SECRET = os.getenv("SECRET", "change-me-in-production")
DB = os.getenv("DB", "mediconnect.db")
app = FastAPI(title="MEDICONNECT")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
bearer = HTTPBearer()

# resource -> (fields, roles allowed to write). Admin can do everything.
R = {
 "patients": (["name","age","gender","phone","address","status"], ["admin","nurse","doctor","reception"]),
 "appointments": (["patient","doctor","date","time","status"], ["admin","reception","doctor"]),
 "records": (["patient","diagnosis","prescription","notes","date"], ["admin","doctor"]),
 "lab": (["patient","test","result","status","date"], ["admin","lab","doctor"]),
 "pharmacy": (["medicine","stock","price","expiry"], ["admin","pharmacist"]),
 "billing": (["patient","description","amount","insurance","status"], ["admin","billing"]),
}
USERS = [("admin","admin123","admin"),("drsmith","doctor123","doctor"),("nancy","nurse123","nurse"),
         ("ravi","pharma123","pharmacist"),("lena","lab123","lab"),("bill","bill123","billing"),("rita","desk123","reception")]

def db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

def pw(p): return hashlib.pbkdf2_hmac("sha256", p.encode(), b"mediconnect", 100000).hex()

@app.on_event("startup")
def init():
    c = db()
    c.execute("CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, hash TEXT, role TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, ts REAL, user TEXT, action TEXT, resource TEXT, rid INTEGER)")
    for name,(f,_) in R.items():
        c.execute(f"CREATE TABLE IF NOT EXISTS {name}(id INTEGER PRIMARY KEY, " + ",".join(f"{x} TEXT" for x in f) + ")")
    for u,p,r in USERS: c.execute("INSERT OR IGNORE INTO users VALUES(?,?,?)", (u,pw(p),r))
    c.commit(); c.close()

def user(cred=Depends(bearer)):
    try: return jwt.decode(cred.credentials, SECRET, algorithms=["HS256"])
    except Exception: raise HTTPException(401, "Session expired. Sign in again.")

@app.post("/api/login")
def login(d: dict):
    c = db(); row = c.execute("SELECT * FROM users WHERE username=?", (d.get("username"),)).fetchone()
    if not row or row["hash"] != pw(d.get("password","")): raise HTTPException(401, "Wrong username or password.")
    tok = jwt.encode({"sub": row["username"], "role": row["role"], "exp": time.time()+8*3600}, SECRET, "HS256")
    return {"token": tok, "role": row["role"], "username": row["username"]}

def check(name, u, write):
    if name not in R: raise HTTPException(404, "Unknown module")
    if write and u["role"] not in R[name][1]: raise HTTPException(403, f"Your role ({u['role']}) cannot change {name}.")

def log(u, action, name, rid):
    c = db(); c.execute("INSERT INTO audit(ts,user,action,resource,rid) VALUES(?,?,?,?,?)", (time.time(),u["sub"],action,name,rid)); c.commit()

@app.get("/api/dashboard/stats")
def stats(u=Depends(user)):
    c = db(); n = lambda q: c.execute(q).fetchone()[0]
    return {"patients": n("SELECT COUNT(*) FROM patients"), "appointments_today": n("SELECT COUNT(*) FROM appointments WHERE date=date('now')"),
            "pending_labs": n("SELECT COUNT(*) FROM lab WHERE status!='Completed'"), "low_stock": n("SELECT COUNT(*) FROM pharmacy WHERE CAST(stock AS INT)<20"),
            "unpaid": n("SELECT COALESCE(SUM(CAST(amount AS REAL)),0) FROM billing WHERE status!='Paid'")}

@app.get("/api/{name}")
def lst(name: str, u=Depends(user)):
    if name == "audit":
        if u["role"] != "admin": raise HTTPException(403, "Admins only.")
        return [dict(r) for r in db().execute("SELECT * FROM audit ORDER BY id DESC LIMIT 200")]
    check(name, u, False)
    return [dict(r) for r in db().execute(f"SELECT * FROM {name} ORDER BY id DESC")]

@app.post("/api/{name}")
def add(name: str, d: dict, u=Depends(user)):
    check(name, u, True); f = R[name][0]; c = db()
    cur = c.execute(f"INSERT INTO {name}({','.join(f)}) VALUES({','.join('?'*len(f))})", [str(d.get(x,"")) for x in f])
    c.commit(); log(u, "create", name, cur.lastrowid); return {"id": cur.lastrowid}

@app.put("/api/{name}/{rid}")
def upd(name: str, rid: int, d: dict, u=Depends(user)):
    check(name, u, True); f = R[name][0]; c = db()
    c.execute(f"UPDATE {name} SET " + ",".join(f"{x}=?" for x in f) + " WHERE id=?", [str(d.get(x,"")) for x in f] + [rid])
    c.commit(); log(u, "update", name, rid); return {"ok": True}

@app.delete("/api/{name}/{rid}")
def rm(name: str, rid: int, u=Depends(user)):
    check(name, u, True); c = db(); c.execute(f"DELETE FROM {name} WHERE id=?", (rid,)); c.commit()
    log(u, "delete", name, rid); return {"ok": True}
