from sqlalchemy import Column, String, Text, ARRAY, TIMESTAMP
from sqlalchemy.sql import func
from database import Base

class Complaint(Base):
    __tablename__ = "complaints"
    id = Column(String, primary_key=True)
    no_kes = Column(String)
    tarikh = Column(String)
    masa = Column(String)
    jenis = Column(String)
    keutamaan = Column(String)
    status = Column(String, default="Baharu")
    nama_pengadu = Column(String)
    emel = Column(String)
    telefon = Column(String)
    institusi = Column(String)
    daerah = Column(String)
    perihal = Column(Text)
    catatan = Column(Text)
    pegawai_agih = Column(String)
    tarikh_agih = Column(String)
    tarikh_tutup = Column(String)
    oyd_nama = Column(String)
    oyd_kp = Column(String)
    oyd_jawatan = Column(String)
    oyd_gred = Column(String)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class LogKerja(Base):
    __tablename__ = "log_kerja"
    id = Column(String, primary_key=True)  # using TEXT for UUID-like IDs
    kes_id = Column(String)
    masa = Column(String)
    tindakan = Column(String)
    catatan = Column(Text)
    oleh = Column(String)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class AuditTrail(Base):
    __tablename__ = "audit_trail"
    id = Column(String, primary_key=True)
    masa = Column(String)
    kes = Column(String)
    aksi = Column(String)
    keterangan = Column(Text)
    oleh = Column(String)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class SemakState(Base):
    __tablename__ = "semak_state"
    kes_id = Column(String, primary_key=True)
    checked_items = Column(ARRAY(String))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
