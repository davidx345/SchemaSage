from main import SessionLocal, User, pwd_context

def create_admin_user(username: str, password: str):
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print("User already exists.")
            return
        hashed_password = pwd_context.hash(password)
        admin_user = User(username=username, hashed_password=hashed_password, is_admin=True)
        db.add(admin_user)
        db.commit()
        print(f"Admin user '{username}' created successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    # CHANGE THESE VALUES
    username = "davidayo2603@gmail.com"
    password = "ayodele3579"
    create_admin_user(username, password)