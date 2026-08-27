import json
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request
from app.models.user import User
from app.models.audit import AuditLog

async def record_audit_log(
    db: AsyncSession,
    action: str,
    target_entity: str,
    target_entity_id: str,
    user: Optional[User] = None,
    request: Optional[Request] = None,
    details: Optional[dict] = None
) -> AuditLog:
    ip_address = None
    user_agent = None
    if request:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")[:255]

    details_str = json.dumps(details, ensure_ascii=False) if details else None

    log_entry = AuditLog(
        user_id=user.id if user else None,
        user_email_cache=user.email if user else None,
        action=action,
        target_entity=target_entity,
        target_entity_id=target_entity_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details_json=details_str
    )
    db.add(log_entry)
    await db.flush()
    return log_entry
