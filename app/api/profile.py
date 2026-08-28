import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models.user import User, UserRole
from app.models.profile import Profile, IdentityDocument
from app.schemas.profile import ProfileOut, ProfileUpdate, DocumentOut
from app.core.security import get_current_active_user
from app.core.audit import record_audit_log

router = APIRouter(prefix="/profile", tags=["Profile & Documents"])

@router.get("/me", response_model=ProfileOut)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Profile)
        .where(Profile.user_id == current_user.id)
        .options(
            selectinload(Profile.guardians),
            selectinload(Profile.confession_fathers),
            selectinload(Profile.documents)
        )
    )
    res = await db.execute(stmt)
    profile = res.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="الملف الشخصي غير موجود")
    return ProfileOut.model_validate(profile)

@router.put("/me", response_model=ProfileOut)
async def update_my_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Profile)
        .where(Profile.user_id == current_user.id)
        .options(
            selectinload(Profile.guardians),
            selectinload(Profile.confession_fathers),
            selectinload(Profile.documents)
        )
    )
    res = await db.execute(stmt)
    profile = res.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="الملف الشخصي غير موجود")

    data = payload.model_dump(exclude_unset=True) if hasattr(payload, "model_dump") else payload.dict(exclude_unset=True)
    
    # If phone number is updated, check uniqueness and format
    if "phone_number" in data and data["phone_number"]:
        clean_phone = data["phone_number"].strip()
        import re
        if not re.match(r"^01[0125]\d{8}$", clean_phone):
            raise HTTPException(status_code=400, detail="رقم الهاتف غير صالح. يجب أن يتكون من 11 رقماً ويبدأ بـ (010 أو 011 أو 012 أو 015).")
        
        stmt_dup = select(Profile.id).where(Profile.phone_number == clean_phone, Profile.id != profile.id)
        if (await db.execute(stmt_dup)).scalar_one_or_none():
            raise HTTPException(status_code=400, detail="رقم الهاتف الجديد مسجل بالفعل لحساب آخر في النظام.")
        data["phone_number"] = clean_phone

    for field, val in data.items():
        if val is not None:
            setattr(profile, field, val)

    await db.commit()
    
    stmt_refetch = (
        select(Profile)
        .where(Profile.id == profile.id)
        .options(
            selectinload(Profile.guardians),
            selectinload(Profile.confession_fathers),
            selectinload(Profile.documents)
        )
    )
    profile = (await db.execute(stmt_refetch)).scalar_one()
    return ProfileOut.model_validate(profile)

@router.post("/upload-document", response_model=DocumentOut)
async def upload_document(
    doc_type: str = Form(...),  # NATIONAL_ID_FRONT, NATIONAL_ID_BACK, CONFESSION_LETTER, OTHER
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Profile).where(Profile.user_id == current_user.id)
    res = await db.execute(stmt)
    profile = res.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="الملف الشخصي غير موجود")

    # Validate file extension
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"نوع الملف غير مسموح. الأنواع المسموحة: {', '.join(settings.ALLOWED_EXTENSIONS)}")

    # Read content & check size
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="حجم الملف يتجاوز الحد الأقصى المسموح به (5 ميجابايت)")

    # Save to private storage
    doc_id = str(uuid.uuid4())
    profile_dir = settings.PRIVATE_STORAGE_DIR / profile.id
    profile_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = profile_dir / f"{doc_id}_{doc_type}.{ext}"
    with open(file_path, "wb") as f:
        f.write(content)

    # Save DB record
    doc_record = IdentityDocument(
        id=doc_id,
        profile_id=profile.id,
        doc_type=doc_type,
        file_path=str(file_path),
        file_name=file.filename,
        file_size_bytes=len(content),
        mime_type=file.content_type or f"image/{ext}"
    )
    db.add(doc_record)
    await db.commit()
    await db.refresh(doc_record)
    return DocumentOut.model_validate(doc_record)

@router.get("/document/{doc_id}")
async def get_secure_document(
    doc_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(IdentityDocument).where(IdentityDocument.id == doc_id)
    res = await db.execute(stmt)
    doc = res.scalar_one_or_none()
    if not doc or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="المستند غير موجود")

    # Check permission
    # If user is applicant, must own document
    if current_user.role == UserRole.APPLICANT:
        stmt_prof = select(Profile).where(Profile.user_id == current_user.id)
        res_prof = await db.execute(stmt_prof)
        my_prof = res_prof.scalar_one_or_none()
        if not my_prof or my_prof.id != doc.profile_id:
            raise HTTPException(status_code=403, detail="ليس لديك صلاحية لعرض هذا المستند")
    else:
        # Staff or Mother Superior: Audit Log is MANDATORY
        action = "VIEW_ID_CARD" if "NATIONAL_ID" in doc.doc_type else "VIEW_CONFESSION_LETTER"
        await record_audit_log(
            db,
            action=action,
            target_entity="IDENTITY_DOCUMENT",
            target_entity_id=doc.id,
            user=current_user,
            request=request,
            details={"doc_type": doc.doc_type, "profile_id": doc.profile_id, "file_name": doc.file_name}
        )
        await db.commit()

    return FileResponse(doc.file_path, media_type=doc.mime_type, filename=doc.file_name)
