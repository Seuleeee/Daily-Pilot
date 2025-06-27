import pytest
from sqlalchemy import text


@pytest.mark.asyncio
async def test_postgres_crud(pg_session):
    print("🟡 PostgreSQL: creating table")
    await pg_session.execute(text("CREATE TABLE IF NOT EXISTS test_table (id SERIAL PRIMARY KEY, name TEXT);"))

    print("🟡 PostgreSQL: inserting row")
    await pg_session.execute(text("INSERT INTO test_table (name) VALUES ('테스트 입력값');"))
    await pg_session.commit()

    print("🟡 PostgreSQL: selecting inserted row")
    result = await pg_session.execute(text("SELECT name FROM test_table WHERE name='테스트 입력값';"))
    name = result.scalar()
    assert name == "테스트 입력값"
    print(f"✅ PostgreSQL: selected -> {name}")

    print("🟡 PostgreSQL: updating row")
    await pg_session.execute(text("UPDATE test_table SET name='업데이트 된 입력값' WHERE name='테스트 입력값';"))
    await pg_session.commit()

    result = await pg_session.execute(text("SELECT name FROM test_table WHERE name='업데이트 된 입력값';"))
    name = result.scalar()
    assert name == "업데이트 된 입력값"
    print(f"✅ PostgreSQL: updated -> {name}")

    print("🟡 PostgreSQL: deleting row")
    await pg_session.execute(text("DELETE FROM test_table WHERE name='업데이트 된 입력값';"))
    await pg_session.commit()

    result = await pg_session.execute(text("SELECT name FROM test_table WHERE name='업데이트 된 입력값';"))
    assert result.scalar() is None
    print("✅ PostgreSQL: delete successful")
    print("🟢 PostgreSQL CRUD test completed successfully")
