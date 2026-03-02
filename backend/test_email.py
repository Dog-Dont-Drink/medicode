import asyncio
import sys
from app.services.email_service import send_verification_email

async def main():
    email = "971425843@qq.com"
    code = "123456"
    purpose = "register"
    print(f"Sending to {email}...")
    success = await send_verification_email(email, code, purpose)
    if success:
        print("SUCCESS")
        sys.exit(0)
    else:
        print("FAILED")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
