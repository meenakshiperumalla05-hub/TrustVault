
from getpass import getpass

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.security import hash_password


def main():
    db = SessionLocal()

    try:
        email = input("Admin email: ").strip().lower()
        existing = db.query(User).filter(User.email == email).first()

        if existing:
            print(f"Existing account: {existing.full_name}")
            print(f"Current role: {existing.role.value}")

            confirmation = input(
                "Type PROMOTE to assign Admin role: "
            ).strip()

            if confirmation != "PROMOTE":
                print("Cancelled. No changes made.")
                return

            existing.role = UserRole.ADMIN
            db.commit()
            print("Existing account successfully promoted to Admin.")
            return

        full_name = input("Admin full name: ").strip()
        password = getpass("Admin password (minimum 12 characters): ")

        if len(password) < 12:
            print("Password must contain at least 12 characters.")
            return

        admin = User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
            is_active=True,
        )

        db.add(admin)
        db.commit()
        print(f"Admin account created. User ID: {admin.id}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
