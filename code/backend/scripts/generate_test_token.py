"""Generate test auth token for frontend testing."""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from jose import jwt

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test user data
test_users = [
    {
        "name": "Test User (普通用户)",
        "email": "test@example.com",
        "password": "Test123456",
        "user_id": "test-user-id",
    },
    {
        "name": "Admin User (管理员)",
        "email": "admin@bingomarket.com",
        "password": "Admin123456",
        "user_id": "admin-user-id",
    },
]

SECRET_KEY = "your-secret-key-change-in-production-min-32-chars"
ALGORITHM = "HS256"

print("=" * 60)
print("TEST TOKENS FOR FRONTEND")
print("=" * 60)

for user in test_users:
    # Create token
    expire = datetime.utcnow() + timedelta(days=365)
    payload = {"exp": expire, "sub": user["user_id"], "email": user["email"]}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    role = "admin" if "Admin" in user["name"] else "user"
    full_name = user["name"].split()[0]
    user_json = f'{{"email":"{user["email"]}","full_name":"{full_name}","role":"{role}"}}'

    print(f"\n{user['name']}:")
    print(f"  Email: {user['email']}")
    print(f"  Password: {user['password']}")
    print(f"  Token: {token[:50]}...")
    print()
    print("  Browser Console Command:")
    print(f'  localStorage.setItem("token", "{token}");')
    print(f'  localStorage.setItem("user", \'{user_json}\');')
    print()

print("=" * 60)
print("Usage: Copy the localStorage commands to browser console")
print("       Then refresh the page")
print("=" * 60)
