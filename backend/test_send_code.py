import asyncio
from app.db.database import async_session
from app.services import auth_service

async def test_email():
    async with async_session() as db:
        try:
            res = await auth_service.send_code(db, "test@example.com", "register")
            print("SUCCESS:", res)
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_email())
