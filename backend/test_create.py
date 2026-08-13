import asyncio
from app.services.orchestrator.factory import orchestrator

async def test_create():
    try:
        info = await orchestrator.create(image="alpine", snapshot_id=None)
        print("Success:", info.id)
    except Exception as e:
        print("Error:", e)

asyncio.run(test_create())
