import os
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from pgvector.sqlalchemy import Vector
from dataset_praser import ResumeProcessor  # import your previous module

# -----------------------------
# 1. Configure DB connection
# -----------------------------
from dotenv import load_dotenv
load_dotenv()

import os

DB_USER = os.getenv("PGUSER")
DB_PASSWORD = os.getenv("PGPASSWORD")
DB_HOST = os.getenv("PGHOST")
DB_PORT = os.getenv("PGPORT")
DB_NAME = os.getenv("PGDATABASE")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


from sqlalchemy.dialects.postgresql import ARRAY



# -----------------------------
# 2. SQLAlchemy setup
# -----------------------------
Base = declarative_base()


class ResumeMetadata(Base):
    __tablename__ = 'resume_metadata'

    id = Column(Integer, primary_key=True, autoincrement=True)
    resume_id = Column(Integer)
    job_title = Column(String)
    skills = Column(ARRAY(String))
    years_experience = Column(Integer)
    location = Column(String)
    

class ResumeChunk(Base):
    __tablename__ = 'resume_chunks'

    id = Column(Integer, primary_key=True)
    resume_id = Column(Integer)
    category = Column(String(100))
    chunk_id = Column(Integer)
    text = Column(Text)
    embedding = Column(Vector(384))  # 384-dimensional vector for MiniLM

# -----------------------------
# 3. Store chunks in DB
# -----------------------------
def store_chunks_in_db(chunks):
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    for chunk in chunks:
        record = ResumeChunk(
            resume_id=chunk["resume_id"],
            category=chunk["category"],
            chunk_id=chunk["chunk_id"],
            text=chunk["text"],
            embedding=chunk["embedding"].tolist()  # convert tensor to list
        )
        session.add(record)

    session.commit()
    session.close()
    print(f"✅ Inserted {len(chunks)} chunks into PostgreSQL.")


# -----------------------------
# 4. Search for top‑K matches
# -----------------------------
def search_similar_chunks(query_text, top_k=5):
    from sentence_transformers import SentenceTransformer
    from sqlalchemy import text

    model = SentenceTransformer('all-MiniLM-L6-v2')
    query_embedding = model.encode(query_text).tolist()

    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    query_sql = text("""
        SELECT id, resume_id, category, chunk_id, text, embedding <#> CAST(:query AS vector) AS distance
        FROM resume_chunks
        ORDER BY embedding <#> CAST(:query AS vector)
        LIMIT :top_k
    """)

    results = session.execute(query_sql, {"query": query_embedding, "top_k": top_k}).fetchall()

    session.close()

    return results

# -----------------------------
# 5. Run insert and/or search
# -----------------------------
if __name__ == "__main__":
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "insert"

    if mode == "insert":
        from nltk import download
        download("punkt")  # Ensure tokenizer works
        processor = ResumeProcessor()
        chunks = processor.process()
        store_chunks_in_db(chunks)

    elif mode == "search":
        query = input("Enter a job description or query: ")
        results = search_similar_chunks(query)
        for res in results:
            print(f"[Resume {res.resume_id}] ({res.category}) — Distance: {res.distance:.4f}\n{res.text[:300]}...\n")

