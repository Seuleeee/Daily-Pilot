import pytest


@pytest.mark.asyncio
async def test_mongodb_crud(mongo_collection):
    print("🟡 MongoDB: inserting document")
    await mongo_collection.insert_one({"name": "test용 입력값"})

    print("🟡 MongoDB: finding inserted document")
    doc = await mongo_collection.find_one({"name": "test용 입력값"})
    assert doc and doc["name"] == "test용 입력값"
    print(f"✅ MongoDB: found -> {doc}")

    print("🟡 MongoDB: updating document")
    await mongo_collection.update_one({"name": "test용 입력값"}, {"$set": {"name": "값 없데이트"}})
    doc = await mongo_collection.find_one({"name": "값 없데이트"})
    assert doc and doc["name"] == "값 없데이트"
    print(f"✅ MongoDB: updated -> {doc}")

    print("🟡 MongoDB: deleting document")
    await mongo_collection.delete_one({"name": "값 없데이트"})
    doc = await mongo_collection.find_one({"name": "값 없데이트"})
    assert doc is None
    print("✅ MongoDB: delete successful")
