"""
سكريبت إنشاء قاعدة البيانات والمستخدم الأول
"""
import asyncio
import sys
sys.path.insert(0, '/app')

from sqlalchemy import text
from app.database import engine, Base
from app.models import User, Organization, Request, Assignment
from app.core.constants import UserRole, UserStatus
from app.core.security import hash_password


async def init_database():
    """إنشاء الجداول"""
    print("🔄 جاري إنشاء الجداول...")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ تم إنشاء الجداول بنجاح")


async def create_admin_user():
    """إنشاء مستخدم إدارة افتراضي"""
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # التحقق من وجود مستخدم إدارة
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.role == UserRole.ADMIN)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print("⚠️  يوجد مستخدم إدارة بالفعل")
            return
        
        # إنشاء مستخدم إدارة
        admin = User(
            email="admin@ksar.ma",
            password_hash=hash_password("admin123"),
            full_name="مدير النظام",
            phone="0600000000",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
        )
        session.add(admin)
        await session.commit()
        
        print("✅ تم إنشاء مستخدم الإدارة:")
        print("   📧 البريد: admin@ksar.ma")
        print("   🔑 كلمة المرور: admin123")
        print("   ⚠️  يرجى تغيير كلمة المرور فوراً!")


async def create_sample_organization():
    """إنشاء مؤسسة نموذجية"""
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # إنشاء مستخدم للمؤسسة
        org_user = User(
            email="org@ksar.ma",
            password_hash=hash_password("org123"),
            full_name="جمعية الإحسان",
            phone="0611111111",
            role=UserRole.ORGANIZATION,
            status=UserStatus.ACTIVE,
        )
        session.add(org_user)
        await session.flush()
        
        # إنشاء المؤسسة
        from app.core.constants import OrganizationStatus
        org = Organization(
            user_id=org_user.id,
            name="جمعية الإحسان للأعمال الخيرية",
            description="جمعية خيرية تعمل على مساعدة المحتاجين",
            contact_phone="0611111111",
            contact_email="org@ksar.ma",
            service_types=["food", "clothes", "blankets"],
            coverage_areas=["المدينة القديمة", "حي السلام"],
            status=OrganizationStatus.ACTIVE,
        )
        session.add(org)
        await session.commit()
        
        print("✅ تم إنشاء مؤسسة نموذجية:")
        print("   📧 البريد: org@ksar.ma")
        print("   🔑 كلمة المرور: org123")


async def main():
    print("=" * 50)
    print("   🏥 KSAR - إعداد قاعدة البيانات")
    print("=" * 50)
    
    await init_database()
    await create_admin_user()
    await create_sample_organization()
    
    print("=" * 50)
    print("   ✅ تم الإعداد بنجاح!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
