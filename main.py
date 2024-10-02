from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, Column, Integer, String, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres.eyfycqdqpslpnpecmoet:n75tjdrbgajdfgq3ogzdfn@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Updated Department model to match the query
class Department(Base):
    __tablename__ = "tb_department"
    id_department = Column(Integer, primary_key=True, index=True)
    name_department = Column(String, index=True)
    code_department = Column(String, index=True)
    del_flag = Column(String, index=True)

# Create tables (in development; for production, manage migrations separately)
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def home_root():
    return {"message": "Success"}

@app.get("/deploy")
async def deploy_info(): 
    return {"message": "Vercel Deployment"}

@app.get("/departments")
async def get_departments(db: Session = Depends(get_db)):
    query = text("""
        SELECT id_department, name_department, code_department 
        FROM tb_department 
        WHERE del_flag = 'N' 
        ORDER BY id_department ASC
    """)
    result = db.execute(query)
    departments = [{"id": row.id_department, "name": row.name_department, "code": row.code_department} 
                   for row in result]
    return {"departments": departments}