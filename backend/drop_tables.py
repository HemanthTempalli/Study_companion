import asyncio
import asyncpg
from app.core.config import settings

async def drop_all():
    conn = await asyncpg.connect(settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"))
    
    # Get all tables in public schema
    tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    table_names = [t['table_name'] for t in tables]
    
    if table_names:
        # Drop all tables cascadingly
        drop_query = "DROP TABLE IF EXISTS {} CASCADE;".format(", ".join([f'"{name}"' for name in table_names]))
        print(f"Dropping tables: {', '.join(table_names)}")
        await conn.execute(drop_query)
        print("All tables dropped successfully.")
    else:
        print("No tables found to drop.")
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(drop_all())
