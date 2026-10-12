# MEDICONNECT - Hospital Management & Patient Record System
Modules: patient registration, appointments, EMR, laboratory, pharmacy, billing, dashboard, audit trail.
Security: JWT login, role-based write access, PBKDF2 password hashes, audit log of every change.

## Run
Backend:  cd backend && pip install -r requirements.txt && uvicorn main:app --reload   (port 8000)
Frontend: cd frontend && npm install && npm run dev                                   (port 5173)

Demo logins are listed on the sign-in screen. Change SECRET and demo passwords before real use.
## Not included yet
Insurance/lab-system integrations, admission-discharge-transfer workflow, edit-in-place, field-level encryption.
