from fastapi import FastAPI, Query, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from sqlalchemy import create_engine, any_
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import uuid
from fastapi import File
from integration import store_chunks_in_db
from dataset_praser import TextChunker, EmbeddingGenerator

# Import from your other Python files
from integration import ResumeMetadata, Base
from RAG_chatbot import answer_with_rag, ConversationManager  # ✅ Use your existing logic

# -------------------------
# Setup
# -------------------------
load_dotenv()

DATABASE_URL = f"postgresql+psycopg2://{os.getenv('PGUSER')}:{os.getenv('PGPASSWORD')}@{os.getenv('PGHOST')}:{os.getenv('PGPORT')}/{os.getenv('PGDATABASE')}"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

app = FastAPI(title="Resume Metadata API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Routes
# -------------------------
@app.get("/")
def root():
    return {"message": "Resume Analyzer API is running. Visit /docs for documentation."}

@app.get("/metadata")
def get_resumes(
    skills: Optional[List[str]] = Query(None),
    min_experience: Optional[int] = None,
    job_title: Optional[str] = None,
    location: Optional[str] = None
):
    session = Session()
    query = session.query(ResumeMetadata)

    if skills:
        for skill in skills:
            query = query.filter(skill == any_(ResumeMetadata.skills))

    if min_experience is not None:
        query = query.filter(ResumeMetadata.years_experience >= min_experience)

    if job_title:
        query = query.filter(ResumeMetadata.job_title.ilike(f"%{job_title}%"))

    if location:
        query = query.filter(ResumeMetadata.location.ilike(f"%{location}%"))

    results = query.all()
    session.close()

    return [
        {
            "resume_id": r.resume_id,
            "job_title": r.job_title,
            "skills": r.skills,
            "years_experience": r.years_experience,
            "location": r.location,
        }
        for r in results
    ]

sessions = {}

@app.post("/analyze")
async def analyze(input_text: str = Form(...), session_id: str = Form(None)):
    # Initialize or retrieve conversation
    if not session_id or session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = ConversationManager(max_history=3)
        is_new_session = True
    else:
        is_new_session = False
    
    conversation = sessions[session_id]
    conversation.add_message("user", input_text)
    
    # Determine if we should search for new resumes
    search_new = (
        is_new_session or 
        input_text.startswith('\\') or  # Metadata queries always search
        "new search" in input_text.lower() or
        not any(msg['role'] == 'assistant' for msg in conversation.history)
    )
    
    if input_text.startswith('\\'):
        try:
            # Extract the query part after backslash
            query_text = input_text[1:].strip()
            
            # Parse into filters (simple example - enhance as needed)
            filters = {}
            if 'skills=' in query_text:
                filters['skills'] = query_text.split('skills=')[1].split()[0].split(',')
            if 'min_exp=' in query_text:
                filters['min_experience'] = float(query_text.split('min_exp=')[1].split()[0])
            if 'title=' in query_text:
                filters['job_title'] = query_text.split('title=')[1].split()[0]
            if 'location=' in query_text:
                filters['location'] = query_text.split('location=')[1].split()[0]
            
            # Use the existing metadata endpoint logic
            session = Session()
            query = session.query(ResumeMetadata)
            
            if 'skills' in filters:
                for skill in filters['skills']:
                    query = query.filter(skill == any_(ResumeMetadata.skills))
            
            if 'min_experience' in filters:
                query = query.filter(ResumeMetadata.years_experience >= filters['min_experience'])
            
            if 'job_title' in filters:
                query = query.filter(ResumeMetadata.job_title.ilike(f"%{filters['job_title']}%"))
            
            if 'location' in filters:
                query = query.filter(ResumeMetadata.location.ilike(f"%{filters['location']}%"))
            
            results = query.limit(20).all()  # Limit results for chat
            session.close()
            
            if not results:
                result = "No matching resumes found in database."
            else:
                result = "\n".join([
                    f"{r.job_title} ({r.years_experience} yrs) | Skills: {', '.join(r.skills[:5])}" + 
                    (f" | Location: {r.location}" if r.location else "")
                    for r in results
                ])
                
        except Exception as e:
            result = f"❌ Error processing metadata query: {str(e)}\nTry format like: \\skills=python min_exp=5"
    else:
            result = answer_with_rag(
                input_text, 
                conversation,
                search_new=search_new  # Pass whether to search anew
            )
            result = result.replace("\n", " ").strip().replace("\"", " ").strip()
        
    conversation.add_message("assistant", result)
    return {"response": result, "session_id": session_id}
import random

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode("utf-8")

    resume_id = random.randint(1, 2_000_000_000)  # Replace UUID with safe int
    category = "Uploaded"

    chunker = TextChunker()
    chunks = chunker.chunk_text(text)
    if not chunks:
        return {"error": "Resume could not be chunked. Empty or invalid."}

    embedder = EmbeddingGenerator()
    embeddings = embedder.embed_chunks(chunks)

    chunk_records = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        chunk_records.append({
            "resume_id": resume_id,
            "category": category,
            "chunk_id": i,
            "text": chunk,
            "embedding": embedding
        })

    store_chunks_in_db(chunk_records)

    return {
        "message": f"✅ Resume uploaded and indexed",
        "resume_id": resume_id,
        "num_chunks": len(chunk_records)
    }


