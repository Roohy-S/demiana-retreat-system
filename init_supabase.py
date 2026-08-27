import asyncio
import sys
from sqlalchemy import text
from app.config import settings
from app.database import engine, Base, AsyncSessionLocal
import app.models # Ensure all models are imported
from seed_data import seed_database

async def check_and_initialize_supabase():
    db_url = settings.async_database_url
    print("=================================================================")
    print("  نظام بيت الخلوة بدير القديسة دميانة – أداة تهيئة سوبابيز  ")
    print("  Demiana Retreat System - Supabase Initialization Tool  ")
    print("=================================================================")
    
    if "sqlite" in db_url:
        print("[!] تنبيه: لم يتم العثور على رابط DATABASE_URL في ملف .env")
        print("[!] النظام مضبوط حالياً على العمل بقاعدة بيانات محلية SQLite.")
        print("[*] لربط Supabase، يرجى فتح ملف .env ووضع رابط الاتصال، مثال:")
        print("    DATABASE_URL=postgresql://postgres.xxx:pass@aws-0-eu-central-1.pooler.supabase.com:6543/postgres")
        print("-----------------------------------------------------------------")
        choice = input("هل ترغب في تهيئة قاعدة البيانات المحلية الآن؟ (y/n): ")
        if choice.lower() != 'y':
            print("تم الإلغاء.")
            return

    print(f"[*] جاري الاتصال بقاعدة البيانات...")
    try:
        async with engine.begin() as conn:
            # Test query
            result = await conn.execute(text("SELECT version();"))
            db_version = result.scalar()
            print(f"[SUCCESS] تم الاتصال بقاعدة البيانات بنجاح!")
            print(f"[*] إصدار المحرك: {db_version}")
            
            print("[*] جاري إنشاء هيكل الجداول والقيود الأمنية (18 جدولاً)...")
            await conn.run_sync(Base.metadata.create_all)
            print("[SUCCESS] تم إنشاء وتحديث كافة الجداول بنجاح في Supabase!")

    except Exception as e:
        print(f"[ERROR] فشل الاتصال بقاعدة البيانات:")
        print(f"        {str(e)}")
        print("\nيرجى التأكد من:")
        print("1. صحة كلمة المرور المكتوبة في رابط DATABASE_URL.")
        print("2. إتاحة الاتصال في إعدادات Network Restrictions بمشروع Supabase.")
        sys.exit(1)

    print("\n[*] جاري بذر الحسابات الافتراضية، الإعدادات، وفترات الخلوة...")
    try:
        await seed_database()
        print("\n[FINISHED] اكتملت تهيئة وبذر سوبابيز بنجاح تام! المنصة جاهزة للعمل والمشاركة.")
    except Exception as e:
        print(f"[ERROR] خطأ أثناء بذر البيانات الأولية: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_and_initialize_supabase())
