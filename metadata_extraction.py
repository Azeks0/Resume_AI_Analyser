# metadata_extractor.py

import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
from integration import ResumeMetadata, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dataset_praser import ResumeProcessor

load_dotenv()

# DB setup
DATABASE_URL = f"postgresql+psycopg2://{os.getenv('PGUSER')}:{os.getenv('PGPASSWORD')}@{os.getenv('PGHOST')}:{os.getenv('PGPORT')}/{os.getenv('PGDATABASE')}"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

# Gemini setup
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash-latest")

def extract_metadata(resume_id, resume_text):
    prompt = f"""
Extract the following metadata from this resume in JSON format:
- job_title: Most recent or main job title
- skills: list of technical or relevant skills
- years_experience: estimated total experience in years ( give only number no text)
- location: city or country if mentioned

Resume:
\"\"\"
{resume_text[:3000]}
\"\"\"
Respond ONLY with valid JSON without ```json .
"""

    try:
        response = model.generate_content(prompt)

        if not response or not hasattr(response, "text"):
            print(f"⚠️ Empty or malformed response for resume {resume_id}")
            return None

        raw = response.text.strip()

        # Try to parse JSON, fallback if needed
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            print(f"⚠️ Invalid JSON returned by Gemini for resume {resume_id}:\n{raw}")
            return None

        return {
            "resume_id": resume_id,
            "job_title": data.get("job_title"),
            "skills": data.get("skills", []),
            "years_experience": data.get("years_experience", 0),
            "location": data.get("location")
        }

    except Exception as e:
        print(f"❌ Error extracting metadata for resume {resume_id}: {e}")
        return None

def extract_all_metadata():
    processor = ResumeProcessor()
    resumes = processor.loader.load_resumes()

    session = Session()
    for resume in resumes[:16]:  # ✅ Limit to first 50
        print(f"🔍 Extracting metadata for Resume {resume['id']}...")
        metadata = extract_metadata(resume['id'], resume['text'])
        if metadata:
            record = ResumeMetadata(**metadata)
            session.add(record)

    session.commit()
    session.close()
    print("✅ All metadata saved to database.")

if __name__ == "__main__":
    extract_all_metadata()

