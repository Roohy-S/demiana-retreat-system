from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User, UserRole
from app.models.profile import Profile
from app.models.admin_notes import AdministrativeNote, Violation, Restriction
from app.schemas.admin_notes import (
    AdministrativeNoteCreate, AdministrativeNoteOut,
    ViolationCreate, ViolationOut
)
from app.core.security import require_mother_superior
from app.core.audit import record_audit_log

router = APIRouter(prefix="/admin-notes", tags=["Administrative Notes & Violations"])

@router.post("/notes", response_model=AdministrativeNoteOut)
async def create_administrative_note(
    payload: AdministrativeNoteCreate,
    current_user: User = Depends(require_mother_superior),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Profile).where(Profile.id == payload.profile_id)
    profile = (await db.execute(stmt)).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="الملف الشخصي غير موجود")

    note = AdministrativeNote(
        profile_id=profile.id,
        author_user_id=current_user.id,
        author_name_cache=current_user.email,
        note_type=payload.note_type,
        severity=payload.severity,
        content=payload.content,
        recommendation=payload.recommendation,
        is_active=True
    )
    db.add(note)
    profile.has_active_warning = True

    await record_audit_log(
        db,
        action="ADD_ADMIN_NOTE",
        target_entity="PROFILE",
        target_entity_id=profile.id,
        user=current_user,
        details={"severity": payload.severity, "recommendation": payload.recommendation}
    )
    await db.commit()
    await db.refresh(note)
    return note

@router.post("/violations", response_model=ViolationOut)
async def create_violation(
    payload: ViolationCreate,
    current_user: User = Depends(require_mother_superior),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Profile).where(Profile.id == payload.profile_id)
    profile = (await db.execute(stmt)).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="الملف الشخصي غير موجود")

    violation = Violation(
        profile_id=profile.id,
        booking_id=payload.booking_id,
        recorded_by_user_id=current_user.id,
        violation_title=payload.violation_title,
        violation_description=payload.violation_description,
        action_taken=payload.action_taken,
        occurred_at=payload.occurred_at or date.today()
    )
    db.add(violation)
    profile.has_active_warning = True

    await record_audit_log(
        db,
        action="ADD_VIOLATION",
        target_entity="PROFILE",
        target_entity_id=profile.id,
        user=current_user,
        details={"title": payload.violation_title}
    )
    await db.commit()
    await db.refresh(violation)
    return violation

@router.get("/notes/{profile_id}", response_model=List[AdministrativeNoteOut])
async def list_notes_for_profile(
    profile_id: str,
    current_user: User = Depends(require_mother_superior),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AdministrativeNote).where(AdministrativeNote.profile_id == profile_id).order_by(AdministrativeNote.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.put("/notes/{note_id}/deactivate", response_model=AdministrativeNoteOut)
async def deactivate_administrative_note(
    note_id: str,
    current_user: User = Depends(require_mother_superior),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AdministrativeNote).where(AdministrativeNote.id == note_id).with_for_update()
    note = (await db.execute(stmt)).scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="الملاحظة غير موجودة")

    note.is_active = False

    # Check if profile still has any active notes/violations
    stmt_active_n = select(AdministrativeNote).where(AdministrativeNote.profile_id == note.profile_id, AdministrativeNote.is_active == True, AdministrativeNote.id != note.id)
    has_active_notes = (await db.execute(stmt_active_n)).scalars().first() is not None
    stmt_active_v = select(Violation).where(Violation.profile_id == note.profile_id, Violation.is_resolved == False)
    has_active_viols = (await db.execute(stmt_active_v)).scalars().first() is not None

    stmt_prof = select(Profile).where(Profile.id == note.profile_id).with_for_update()
    prof = (await db.execute(stmt_prof)).scalar_one_or_none()
    if prof and not has_active_notes and not has_active_viols:
        prof.has_active_warning = False

    await db.commit()
    await db.refresh(note)
    return note

@router.get("/violations/{profile_id}", response_model=List[ViolationOut])
async def list_violations_for_profile(
    profile_id: str,
    current_user: User = Depends(require_mother_superior),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Violation).where(Violation.profile_id == profile_id).order_by(Violation.occurred_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.put("/violations/{violation_id}/resolve", response_model=ViolationOut)
async def resolve_violation(
    violation_id: str,
    current_user: User = Depends(require_mother_superior),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Violation).where(Violation.id == violation_id).with_for_update()
    violation = (await db.execute(stmt)).scalar_one_or_none()
    if not violation:
        raise HTTPException(status_code=404, detail="المخالفة غير موجودة")

    violation.is_resolved = True

    # Check if profile still has any active notes/violations
    stmt_active_n = select(AdministrativeNote).where(AdministrativeNote.profile_id == violation.profile_id, AdministrativeNote.is_active == True)
    has_active_notes = (await db.execute(stmt_active_n)).scalars().first() is not None
    stmt_active_v = select(Violation).where(Violation.profile_id == violation.profile_id, Violation.is_resolved == False, Violation.id != violation.id)
    has_active_viols = (await db.execute(stmt_active_v)).scalars().first() is not None

    stmt_prof = select(Profile).where(Profile.id == violation.profile_id).with_for_update()
    prof = (await db.execute(stmt_prof)).scalar_one_or_none()
    if prof and not has_active_notes and not has_active_viols:
        prof.has_active_warning = False

    await db.commit()
    await db.refresh(violation)
    return violation
