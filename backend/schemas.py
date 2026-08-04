from pydantic import BaseModel
from typing import Optional, List

class ComplaintBase(BaseModel):
    id: str
    no_kes: Optional[str] = None
    tarikh: Optional[str] = None
    masa: Optional[str] = None
    jenis: Optional[str] = None
    keutamaan: Optional[str] = None
    status: Optional[str] = "Baharu"
    nama_pengadu: Optional[str] = None
    emel: Optional[str] = None
    telefon: Optional[str] = None
    institusi: Optional[str] = None
    daerah: Optional[str] = None
    perihal: Optional[str] = None
    catatan: Optional[str] = None
    pegawai_agih: Optional[str] = None
    tarikh_agih: Optional[str] = None
    tarikh_tutup: Optional[str] = None
    oyd_nama: Optional[str] = None
    oyd_kp: Optional[str] = None
    oyd_jawatan: Optional[str] = None
    oyd_gred: Optional[str] = None

class ComplaintCreate(ComplaintBase):
    pass

class ComplaintUpdate(BaseModel):
    no_kes: Optional[str] = None
    tarikh: Optional[str] = None
    masa: Optional[str] = None
    jenis: Optional[str] = None
    keutamaan: Optional[str] = None
    status: Optional[str] = None
    nama_pengadu: Optional[str] = None
    emel: Optional[str] = None
    telefon: Optional[str] = None
    institusi: Optional[str] = None
    daerah: Optional[str] = None
    perihal: Optional[str] = None
    catatan: Optional[str] = None
    pegawai_agih: Optional[str] = None
    tarikh_agih: Optional[str] = None
    tarikh_tutup: Optional[str] = None
    oyd_nama: Optional[str] = None
    oyd_kp: Optional[str] = None
    oyd_jawatan: Optional[str] = None
    oyd_gred: Optional[str] = None

class ComplaintOut(ComplaintBase):
    class Config:
        from_attributes = True

class LogKerjaBase(BaseModel):
    id: str
    kes_id: str
    masa: str
    tindakan: str
    catatan: Optional[str] = None
    oleh: str

class LogKerjaOut(LogKerjaBase):
    class Config:
        from_attributes = True

class AuditBase(BaseModel):
    id: str
    masa: str
    kes: Optional[str] = None
    aksi: str
    keterangan: Optional[str] = None
    oleh: str

class AuditOut(AuditBase):
    class Config:
        from_attributes = True

class SemakStateIn(BaseModel):
    kes_id: str
    checked_items: List[str]

class SemakStateOut(SemakStateIn):
    class Config:
        from_attributes = True

class SyncPayload(BaseModel):
    complaints: List[ComplaintCreate]
    log_kerja: List[LogKerjaBase]
    audit_trail: List[AuditBase]
    semak_state: dict  # {kes_id: [items]}
    aduan_counter: int
