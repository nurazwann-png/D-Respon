from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
import uuid

from database import get_db, init_db
from models import Complaint, LogKerja, AuditTrail, SemakState
from schemas import (
    ComplaintCreate, ComplaintUpdate, ComplaintOut,
    LogKerjaBase, LogKerjaOut,
    AuditBase, AuditOut,
    SemakStateIn, SemakStateOut,
    SyncPayload,
)
from auth import verify_google_token

app = FastAPI(title="D-Respon API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://prestij-nurazwann-smartassist.as.r.appspot.com", "http://localhost:8119"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

# ── COMPLAINTS ──────────────────────────────────────────────────────────────

@app.get("/api/complaints", response_model=List[ComplaintOut])
def list_complaints(db: Session = Depends(get_db), user=Depends(verify_google_token)):
    return db.query(Complaint).order_by(Complaint.created_at.desc()).all()

@app.post("/api/complaints", response_model=ComplaintOut)
def create_complaint(c: ComplaintCreate, db: Session = Depends(get_db), user=Depends(verify_google_token)):
    obj = Complaint(**c.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@app.put("/api/complaints/{cid}", response_model=ComplaintOut)
def update_complaint(cid: str, data: ComplaintUpdate, db: Session = Depends(get_db), user=Depends(verify_google_token)):
    obj = db.query(Complaint).filter(Complaint.id == cid).first()
    if not obj:
        raise HTTPException(404, "Aduan tidak dijumpai")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

@app.delete("/api/complaints/{cid}")
def delete_complaint(cid: str, db: Session = Depends(get_db), user=Depends(verify_google_token)):
    obj = db.query(Complaint).filter(Complaint.id == cid).first()
    if not obj:
        raise HTTPException(404, "Aduan tidak dijumpai")
    db.delete(obj)
    db.commit()
    return {"ok": True}

# ── LOG KERJA ──────────────────────────────────────────────────────────────

@app.get("/api/log-kerja", response_model=List[LogKerjaOut])
def list_log(db: Session = Depends(get_db), user=Depends(verify_google_token)):
    return db.query(LogKerja).order_by(LogKerja.created_at.desc()).all()

@app.post("/api/log-kerja", response_model=LogKerjaOut)
def create_log(entry: LogKerjaBase, db: Session = Depends(get_db), user=Depends(verify_google_token)):
    obj = LogKerja(**entry.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

# ── AUDIT TRAIL ─────────────────────────────────────────────────────────────

@app.get("/api/audit", response_model=List[AuditOut])
def list_audit(db: Session = Depends(get_db), user=Depends(verify_google_token)):
    return db.query(AuditTrail).order_by(AuditTrail.created_at.desc()).limit(500).all()

@app.post("/api/audit", response_model=AuditOut)
def create_audit(entry: AuditBase, db: Session = Depends(get_db), user=Depends(verify_google_token)):
    obj = AuditTrail(**entry.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

# ── SEMAK STATE ─────────────────────────────────────────────────────────────

@app.get("/api/semak/{kes_id}", response_model=SemakStateOut)
def get_semak(kes_id: str, db: Session = Depends(get_db), user=Depends(verify_google_token)):
    obj = db.query(SemakState).filter(SemakState.kes_id == kes_id).first()
    if not obj:
        return {"kes_id": kes_id, "checked_items": []}
    return obj

@app.put("/api/semak/{kes_id}", response_model=SemakStateOut)
def update_semak(kes_id: str, data: SemakStateIn, db: Session = Depends(get_db), user=Depends(verify_google_token)):
    obj = db.query(SemakState).filter(SemakState.kes_id == kes_id).first()
    if obj:
        obj.checked_items = data.checked_items
    else:
        obj = SemakState(kes_id=kes_id, checked_items=data.checked_items)
        db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

# ── BULK SYNC (migrate from localStorage) ──────────────────────────────────

@app.post("/api/sync")
def bulk_sync(payload: SyncPayload, db: Session = Depends(get_db), user=Depends(verify_google_token)):
    """One-shot migration: push all localStorage data into the database."""
    # Complaints
    for c in payload.complaints:
        if not db.query(Complaint).filter(Complaint.id == c.id).first():
            db.add(Complaint(**c.model_dump()))

    # Log Kerja
    existing_logs = {r.id for r in db.query(LogKerja.id).all()}
    for l in payload.log_kerja:
        if l.id not in existing_logs:
            db.add(LogKerja(**l.model_dump()))

    # Audit Trail
    existing_audit = {r.id for r in db.query(AuditTrail.id).all()}
    for a in payload.audit_trail:
        if a.id not in existing_audit:
            db.add(AuditTrail(**a.model_dump()))

    # Semak State
    for kes_id, items in payload.semak_state.items():
        obj = db.query(SemakState).filter(SemakState.kes_id == kes_id).first()
        if obj:
            obj.checked_items = list(items)
        else:
            db.add(SemakState(kes_id=kes_id, checked_items=list(items)))

    db.commit()
    return {"ok": True, "complaints": len(payload.complaints), "logs": len(payload.log_kerja)}
