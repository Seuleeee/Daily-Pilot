import pytest


@pytest.mark.asyncio
async def test_redis_crud(redis_client):
    print("🟡 Redis: setting key")
    await redis_client.set("test_key", "test_value")
    value = await redis_client.get("test_key")
    assert value == "test_value"
    print(f"✅ Redis: get -> {value}")

    print("🟡 Redis: updating key")
    await redis_client.set("test_key", "updated")
    value = await redis_client.get("test_key")
    assert value == "updated"
    print(f"✅ Redis: updated -> {value}")

    print("🟡 Redis: deleting key")
    await redis_client.delete("test_key")
    value = await redis_client.get("test_key")
    assert value is None
    print("✅ Redis: delete successful")
