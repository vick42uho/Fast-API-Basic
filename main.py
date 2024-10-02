from fastapi import FastAPI, HTTPException
import asyncpg
import logging

# PostgreSQL connection settings
DATABASE_URL = 'postgresql://postgres.eyfycqdqpslpnpecmoet:n75tjdrbgajdfgq3ogzdfn@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres'

app = FastAPI()

# Logger configuration
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)

# Initialize connection pool for PostgreSQL
@app.on_event("startup")
async def startup():
    try:
        app.pool = await asyncpg.create_pool(DATABASE_URL)
        logger.info("PostgreSQL pool connection established.")
    except Exception as e:
        logger.error(f"Error creating PostgreSQL connection pool: {e}")
        raise HTTPException(status_code=500, detail="Could not connect to the database")

@app.on_event("shutdown")
async def shutdown():
    await app.pool.close()
    logger.info("PostgreSQL pool connection closed.")

# Endpoint to fetch departments
@app.get("/departments")
async def read_departments():
    query = """
    SELECT id_department, name_department, code_department 
    FROM tb_department 
    WHERE del_flag = 'N' 
    ORDER BY id_department ASC
    """
    try:
        async with app.pool.acquire() as connection:
            departments = await connection.fetch(query)
            return [
                {
                    "id_department": department["id_department"],
                    "name_department": department["name_department"],
                    "code_department": department["code_department"]
                }
                for department in departments
            ]
    except Exception as e:
        logger.error(f"Error fetching departments: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
