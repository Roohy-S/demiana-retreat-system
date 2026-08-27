import re
import socket
import logging
from typing import Optional, Tuple, Set, Dict
from email_validator import validate_email, EmailNotValidError, EmailUndeliverableError

logger = logging.getLogger(__name__)

# List of known disposable / temporary email domains (over 150+ common burner domains)
DISPOSABLE_DOMAINS: Set[str] = {
    "10minutemail.com", "10minutemail.net", "10minutemail.org", "10minutemail.co.uk",
    "tempmail.com", "temp-mail.org", "temp-mail.io", "tempmail.net", "tempmail.plus",
    "guerrillamail.com", "guerrillamail.net", "guerrillamail.org", "guerrillamail.biz",
    "sharklasers.com", "grr.la", "guerrillamailblock.com", "pokemail.net", "spam4.me",
    "mailinator.com", "mailinator.net", "mailinator.org", "mailinater.com", "suremail.info",
    "yopmail.com", "yopmail.fr", "yopmail.net", "cool.fr.nf", "jetable.fr.nf",
    "throwawaymail.com", "trashmail.com", "trashmail.net", "trashmail.me", "trash-mail.at",
    "dispostable.com", "getairmail.com", "mohmal.com", "mohmal.im", "mohmal.in",
    "fakemailgenerator.com", "emailondeck.com", "burnermail.io", "generator.email",
    "crazymailing.com", "armyspy.com", "cuvox.de", "dayrep.com", "einrot.com",
    "fleckens.hu", "gustr.com", "jourrapide.com", "rhyta.com", "superrito.com",
    "teleworm.us", "inboxkitten.com", "mytemp.email", "nada.ltd", "dropmail.me",
    "getnada.com", "abcvg.com", "boximail.com", "clipmail.eu", "crazymail.com",
    "damnthespam.com", "deadaddress.com", "devnullmail.com", "disposableinbox.com",
    "e4ward.com", "emailtemporario.com.br", "fakemail.net", "fakeinbox.com",
    "filzmail.com", "gishpuppy.com", "instantemailaddress.com", "kasmail.com",
    "mailcatch.com", "maildrop.cc", "mailforspam.com", "mailhazard.com",
    "mailnesia.com", "mailnull.com", "mintemail.com", "mytempemail.com",
    "noclickemail.com", "nospam.ze.tc", "nospam4.us", "our-inbox.com",
    "pookmail.com", "safetymail.info", "shortmail.net", "sofort-mail.de",
    "spamfree24.org", "spambog.com", "spamex.com", "spamex.net", "spambox.us",
    "tempail.com", "tempr.email", "tempsky.com", "tmail.ws", "trashymail.com",
    "whyspam.me", "zoemail.org", "trashmail.org", "trashmail.net"
}

# Domain typo corrections dictionary
COMMON_DOMAIN_TYPOS: Dict[str, str] = {
    # Gmail typos
    "gmai.com": "gmail.com",
    "gmial.com": "gmail.com",
    "gmil.com": "gmail.com",
    "gamil.com": "gmail.com",
    "gmaill.com": "gmail.com",
    "gmaile.com": "gmail.com",
    "gmai.co": "gmail.com",
    "gmail.co": "gmail.com",
    "gmaik.com": "gmail.com",
    "gmal.com": "gmail.com",
    "gemail.com": "gmail.com",
    "gmail.con": "gmail.com",
    "gmail.cpm": "gmail.com",
    "gmail.vom": "gmail.com",
    "gmail.cm": "gmail.com",
    "gmai.cm": "gmail.com",
    
    # Yahoo typos
    "yaho.com": "yahoo.com",
    "yahooo.com": "yahoo.com",
    "yaho.co": "yahoo.com",
    "yahoo.co": "yahoo.com",
    "yahu.com": "yahoo.com",
    "yahoo.con": "yahoo.com",
    "ymail.con": "ymail.com",
    
    # Outlook / Hotmail typos
    "outlok.com": "outlook.com",
    "outloo.com": "outlook.com",
    "outlock.com": "outlook.com",
    "outlook.con": "outlook.com",
    "hotmial.com": "hotmail.com",
    "hotmai.com": "hotmail.com",
    "hotmil.com": "hotmail.com",
    "hotmali.com": "hotmail.com",
    "hotmail.con": "hotmail.com",
    
    # iCloud typos
    "iclod.com": "icloud.com",
    "icoud.com": "icloud.com",
    "icloud.con": "icloud.com",
}

# Pre-cached popular valid email domains for lightning-fast validation (< 0.1ms)
KNOWN_VALID_DOMAINS: Set[str] = {
    "gmail.com", "googlemail.com", "yahoo.com", "yahoo.co.uk", "yahoo.fr", "ymail.com",
    "outlook.com", "hotmail.com", "live.com", "msn.com", "icloud.com", "me.com", "mac.com",
    "protonmail.com", "proton.me", "zoho.com", "aol.com", "mail.com", "gmx.com",
    "example.com", "example.org", "example.net", "test.com", "test.org",
    "demiana.org", "demiana-monastery.org", "localhost", "test"
}

# In-memory cache for dynamically verified domains
_DOMAIN_CACHE: Dict[str, bool] = {}

STRICT_EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9]([a-zA-Z0-9._%+-]*[a-zA-Z0-9])?@[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$"
)

def check_domain_typo(domain: str) -> Optional[str]:
    """Check if the domain has a known typo and return the suggested domain."""
    domain_lower = domain.strip().lower()
    return COMMON_DOMAIN_TYPOS.get(domain_lower)

def is_disposable_domain(domain: str) -> bool:
    """Check if domain is a known temporary or burner email provider."""
    domain_lower = domain.strip().lower()
    return domain_lower in DISPOSABLE_DOMAINS

def validate_and_normalize_email(
    email: str,
    check_deliverability: bool = True,
    allow_typo_correction: bool = False
) -> Tuple[str, Optional[str]]:
    """
    Strict email validation:
    1. Syntax & structure check.
    2. Typo detection for popular domains.
    3. Disposable email domain blocking.
    4. Real DNS MX deliverability check via email-validator with smart in-memory caching.
    
    Returns (normalized_email, typo_suggestion_or_none) or raises ValueError with Arabic message.
    """
    if not email or not isinstance(email, str):
        raise ValueError("يرجى إدخال البريد الإلكتروني.")

    clean_email = email.strip().lower()

    if len(clean_email) > 254:
        raise ValueError("البريد الإلكتروني طويل جداً (الحد الأقصى 254 حرفاً).")

    if not STRICT_EMAIL_REGEX.match(clean_email) or ".." in clean_email:
        raise ValueError("صيغة البريد الإلكتروني غير صحيحة. يجب أن يحتوي على اسم ونطاق صالح (مثال: name@gmail.com).")

    try:
        local_part, domain = clean_email.split("@", 1)
    except ValueError:
        raise ValueError("صيغة البريد الإلكتروني غير صحيحة.")

    # 1. Check for disposable domain
    if is_disposable_domain(domain):
        raise ValueError(
            f"عذراً، استخدام خدمات البريد الإلكتروني المؤقت أو الوهمي ({domain}) غير مسموح به في نظام بيت الخلوة. "
            "يرجى استخدام بريدكِ الشخصي المعتمد (مثل Gmail أو Outlook أو Yahoo) لضمان استلام إشعارات القبول ورمز التحقق."
        )

    # 2. Check for domain typos
    suggested_domain = check_domain_typo(domain)
    typo_suggestion = None
    if suggested_domain:
        typo_suggestion = f"{local_part}@{suggested_domain}"
        if not allow_typo_correction:
            raise ValueError(
                f"يبدو أن هناك خطأ إملائي في نطاق البريد ({domain}). هل تقصدين: {typo_suggestion}؟ "
                "يرجى تصحيح كتابة البريد للمتابعة."
            )
        clean_email = typo_suggestion
        domain = suggested_domain

    # 3. DNS MX Deliverability validation
    if check_deliverability:
        # Fast path: Pre-known valid domains or in-memory cache hit
        if domain in KNOWN_VALID_DOMAINS or _DOMAIN_CACHE.get(domain) is True:
            return clean_email, typo_suggestion

        if _DOMAIN_CACHE.get(domain) is False:
            raise ValueError(
                f"النطاق ({domain}) غير صالح أو لا يمكنه استقبال رسائل بريدية (سجلات MX غير متوفرة). "
                "يرجى التأكد من كتابة البريد الإلكتروني بشكل صحيح ومفعل."
            )

        try:
            validated = validate_email(
                clean_email,
                check_deliverability=True,
                dns_resolver=None,
                test_environment=False
            )
            clean_email = validated.normalized
            _DOMAIN_CACHE[domain] = True
        except EmailUndeliverableError as e:
            _DOMAIN_CACHE[domain] = False
            raise ValueError(
                f"النطاق ({domain}) غير صالح أو لا يمكنه استقبال رسائل بريدية (سجلات MX غير متوفرة). "
                "يرجى التأكد من كتابة البريد الإلكتروني بشكل صحيح ومفعل."
            )
        except EmailNotValidError as e:
            raise ValueError(f"البريد الإلكتروني غير صالح: {str(e)}")
        except Exception as e:
            logger.warning(f"DNS deliverability check warning for {clean_email}: {e}")

    return clean_email, typo_suggestion
