
from getpass import getpass

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.security import hash_password


def main():
    print("\n=== TrustVault Owner Account Setup ===\n")

    full_name = input("Enter owner name: ").strip()
    email = input("Enter owner email: ").strip().lower()
    password = getpass("Enter owner password: ")
    confirm_password = getpass("Confirm password: ")

    if not full_name or not email:
        print("Name and email are required.")
        return

    if len(password) < 8:
        print("Password must contain at least 8 characters.")
        return

    if password != confirm_password:
        print("Passwords do not match.")
        return

    db = SessionLocal()

    try:
        existing_user = db.query(User).filter(
            User.email == email
        ).first()

        if existing_user:
            print("This email is already registered. No changes made.")
            return

        user = User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.OWNER,
            is_active=True
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        print("\nOwner account created successfully!")
        print(f"User ID: {user.id}")
        print(f"Email: {user.email}")
        print(f"Role: {user.role.value}")

    except Exception as error:
        db.rollback()
        print(f"Account creation failed: {error}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
