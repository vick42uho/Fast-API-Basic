from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
import uvicorn
from typing import List, Dict, Optional
from datetime import datetime
import logging
from pydantic import BaseModel

# ตั้งค่า logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI application
app = FastAPI()


# PostgreSQL connection settings
DATABASE_URL = 'postgresql://postgres.eyfycqdqpslpnpecmoet:n75tjdrbgajdfgq3ogzdfn@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres'



# Function to create database connection pool
async def get_pool():
    logger.info("Creating database pool...")
    return await asyncpg.create_pool(DATABASE_URL, statement_cache_size=0)

# Event handler for starting up the application
@app.on_event("startup")
async def startup():
    try:
        app.pool = await get_pool()
        logger.info("Database pool created successfully.")
    except Exception as e:
        logger.error(f"Error creating database pool: {e}")
        raise

# Event handler for shutting down the application
@app.on_event("shutdown")
async def shutdown():
    logger.info("Closing database pool...")
    await app.pool.close()
    logger.info("Database pool closed.")

# Model for Building response
class BuildingResponse(BaseModel):
    id: int
    name: str
    floors: List[str]

# Model for Section
class Section(BaseModel):
    id_section:int
    code_section:str
    name_section: str
    del_flag: str
    created_at: Optional[datetime] = None

class Division(BaseModel):
    id_division:int
    code_division:str
    name_division:str
    del_flag: str
    created_at: Optional[datetime] = None
    code_section:str

    # Middleware for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # แก้ไขตาม Origin ของเว็บแอปพลิเคชันของคุณ
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------Query API Building & Floor Yanhee------------------------------------
@app.get("/buildings", response_model=List[BuildingResponse])
async def read_buildings():
    query = """
    SELECT b.id_building AS id, b.building_name AS name, 
       ARRAY_AGG(f.floor_name ORDER BY f.id_floor) AS floors
    FROM tb_building b
    JOIN tb_floors f ON b.id_building = f.id_building
    WHERE b.del_flag = 'N' AND f.del_flag = 'N'
    GROUP BY b.id_building, b.building_name
    ORDER BY b.id_building;
    """
    try:
        async with app.pool.acquire() as connection:
            buildings = await connection.fetch(query)
            return [BuildingResponse(id=building['id'], name=building['name'], floors=building['floors']) for building in buildings]
    except Exception as e:
        logger.error(f"Error fetching buildings: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# ----------------------------------------------------------------------------------------------------

# ------------------------------------Query API CRUD-Section------------------------------------------

@app.get("/read/section", response_model=List[Section])
async def read_sections():
    query = """
    SELECT id_section, code_section , name_section , del_flag , created_at FROM tb_section WHERE del_flag = 'N'
    ORDER BY id_section asc
    """
    try:
        async with app.pool.acquire() as connection:
            sections = await connection.fetch(query)
            return [Section(**section) 
                    for section in sections]
    except Exception as e:
        logger.error(f"Error fetching sections: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Create a new section
@app.post("/create/section", response_model=Section)
async def create_section(section: Section):
    query = """
    INSERT INTO public.tb_section (code_section, name_section, created_at, del_flag)
    VALUES ($1, $2, NOW(), $3)
    RETURNING id_section, code_section, name_section, created_at, del_flag
    """
    try:
        async with app.pool.acquire() as connection:
            created_section = await connection.fetchrow(query, section.code_section, section.name_section, section.del_flag)
            return Section(**created_section)
    except Exception as e:
        logger.error(f"Error creating section: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Read a single section by ID
@app.get("/read/section/{id_section}", response_model=Section)
async def read_section(id_section: int):
    query = "SELECT id_section , code_section , name_section, del_flag, created_at FROM public.tb_section WHERE id_section = $1 and del_flag = 'N'"
    try:
        async with app.pool.acquire() as connection:
            section = await connection.fetchrow(query, id_section)
            if section is None:
                raise HTTPException(status_code=404, detail="Section not found")
            return Section(**section)
    except Exception as e:
        logger.error(f"Error fetching section: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Update a section by ID
@app.put("/update/section/{id_section}", response_model=Section)
async def update_section(id_section: int, section: Section):
    query = """
    UPDATE public.tb_section
    SET name_section = $1, del_flag = $2, created_at = NOW() , code_section = $3
    WHERE id_section = $4
    RETURNING id_section, code_section , name_section, del_flag, created_at
    """
    try:
        async with app.pool.acquire() as connection:
            updated_section = await connection.fetchrow(query, section.name_section, section.del_flag, section.code_section , id_section)
            if updated_section is None:
                raise HTTPException(status_code=404, detail="Section not found")
            return Section(**updated_section)
    except Exception as e:
        logger.error(f"Error updating section: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Delete a section by ID
@app.delete("/delete/section/{id_section}", response_model=Dict[str, str])
async def delete_section(id_section: int):
    query = "UPDATE public.tb_section SET del_flag = 'Y' WHERE id_section = $1"
    try:
        async with app.pool.acquire() as connection:
            result = await connection.execute(query, id_section)
            if result == "DELETE 0":
                raise HTTPException(status_code=404, detail="Section not found")
            return {"message": "Section deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting section: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
# ----------------------------------------------------------------------------------------------------

# -----------------------------------Query API CRUD-Division------------------------------------------

@app.get("/read/division", response_model=List[Division])
async def read_divisions():
    query = """
    select id_division , code_division , name_division , code_section , del_flag , created_at
    from tb_division where del_flag = 'N'
    order by id_division asc   
    """
    try:
        async with app.pool.acquire() as connection:
            divisions = await connection.fetch(query)
            return [Division(**division) 
                    for division in divisions]
    except Exception as e:
        logger.error(f"Error fetching sections: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
# Create a new division    
@app.post("/create/division",response_model=Division)
async def create_division(division: Division):
    query = """
    INSERT INTO public.tb_division (code_division , name_division , del_flag , created_at , code_section ) VALUES ($1 , $2 , $3 , NOW() , $4)
    RETURNING id_division , code_division , name_division , del_flag , created_at , code_section
    """
    try:
        async with app.pool.acquire() as connection:
            created_division = await connection.fetchrow(query, division.code_division, division.name_division, division.del_flag , division.code_section)
            return Division(**created_division)
    except Exception as e:
        logger.error(f"Error creating division: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Read a single section by ID
@app.get("/read/division/{id_division}", response_model=Division)
async def read_division(id_division: int):
    query = """
    select id_division , code_division , name_division , T1.code_section , T2.id_section , 
    T1.del_flag , T1.created_at
    from tb_division as T1 
    LEFT JOIN public.tb_section as T2 on T1.code_section = T2.code_section 
    where T2.id_section = $1 and T1.del_flag = 'N'  
    """
    try:
        async with app.pool.acquire() as connection:
            division = await connection.fetchrow(query, id_division)
            if division is None:
                raise HTTPException(status_code=404, detail="division not found")
            return Division(**division)
    except Exception as e:
        logger.error(f"Error fetching division: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Update a division by ID
@app.put("/update/division/{id_division}", response_model=Division)
async def update_division(id_division: int, division: Division):
    query = """
    update public.tb_division 
	set code_division = $1 , name_division = $2, , del_flag = $3 , created_at = now()
	where id_division = $4
	returning id_division , code_division  , name_division , del_flag , created_at , code_section 
    """
    try:
        async with app.pool.acquire() as connection:
            updated_division = await connection.fetchrow(query, division.code_section , division.name_division, division.del_flag, division.code_section , id_division)
            if updated_division is None:
                raise HTTPException(status_code=404, detail="Division not found")
            return Division(**updated_division)
    except Exception as e:
        logger.error(f"Error updating division: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Delete a division by ID
@app.delete("/delete/division/{id_division}", response_model=Dict[str, str])
async def delete_division(id_division: int):
    query = "UPDATE public.tb_division SET del_flag = 'Y' WHERE id_division = $1"
    try:
        async with app.pool.acquire() as connection:
            result = await connection.execute(query, id_division)
            if result == "DELETE 0":
                raise HTTPException(status_code=404, detail="Division not found")
            return {"message": "Division deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting division: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
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

# ----------------------------------------------------------------------------------------------------
# Run the FastAPI application with Uvicorn
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=5555)
