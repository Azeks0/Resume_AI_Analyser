DOCUMENTATION
AI RESUME ANALYZER
VOINEA ANDREI



This is the documentation for the full implementation of the AI Resume analyzer combining the backend written in python  as well as the frontend written in next,js and typescript.

The structure of the implementation is as follows:

DATASET:
In order to test the outcome of our implementation, we first need to have a database of resumes to test it on.
 
For this I firstly choose a public resume dataset from kaggle containing tubular data of txt resumes stored in a csv.
https://www.kaggle.com/datasets/gauravduttakiit/resume-dataset/data

By the requirements, the workflow should work for both txt and pdf files and for pdf it was a lot more challenging finding datasets that fit the requirements.

To solve this step, I went on to create synthetic pdf resumes based on a generic LaTeX template combined with randomly generated characteristics that were then inserted in the template.


Data_praser.py is responsible for downloading, loading, parsing, and vectorizing resume data. It supports processing both CSV datasets and PDF resumes from a local folder.


Integration.py handles the integration with a PostgreSQL database using SQLAlchemy and pgvector for storing and retrieving resume chunk embeddings. It also includes functionality to search for similar resume chunks based on a query.

generate_resumes.py is responsible for creating a set of synthetic PDF resumes using a LaTeX template and the Faker library for realistic data generation.



CHATBOT:

RAG_chatbot.py implements a Retrieval-Augmented Generation (RAG) chatbot that uses the stored resume embeddings to answer questions about job descriptions. It integrates with the integration,py module for searching similar chunks and uses Google's Gemini API for generating responses.


API: 

metadata_api.py sets up a FastAPI web API that exposes endpoints for:

-- Retrieving resume metadata based on various filters.

-- Interacting with the RAG chatbot for job description analysis.

-- Uploading new PDF resumes for processing and indexing into the database.


DEPIDENCES

Python, next.js and typescript must be installed.


# Create a virtual environment 
```
python3 -m venv venv
```
# Activate the virtual environment
# On macOS/Linux:
```
source venv/bin/activate
```
# On Windows:
```
venv\Scripts\activate

```

# Install the required packages
```
pip install pandas kagglehub nltk sentence-transformers pymupdf tqdm sqlalchemy psycopg2-binary pgvector python-dotenv google-generativeai fastapi uvicorn jinja2 faker python-multipart
```
.env file should be included in the base directory with the following structure:
```
PGUSER=
PGPASSWORD=
PGHOST=
PGPORT=
PGDATABASE=
GOOGLE_API_KEY=
```
How to start the backend and the frontend:

in the base directory run the command: 
```
uvicorn metadata_api:app --reload
```
navigate into the frontend folder and run:
```
npm run dev
```
Free tier notes:

the database is hosted on aiven and dbeaver was used to work with it, for both of them the free version.

for the ChatBot Google Gemini API was used on the free version.

The data used was either public or randomly generated.






