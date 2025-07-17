import os
from typing import List, Dict

import pandas as pd
import kagglehub
import nltk
from nltk.tokenize import TreebankWordTokenizer
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
import os
import fitz  # PyMuPDF
from typing import List, Dict




class DatasetDownloader:
    def __init__(self, dataset_id: str = "gauravduttakiit/resume-dataset"):
        self.dataset_id = dataset_id

    def get_csv_path(self) -> str:
        print("📦 Downloading Kaggle resume dataset...")
        path = kagglehub.dataset_download(self.dataset_id)
        print(f"✅ Dataset downloaded to: {path}")

        for fname in os.listdir(path):
            if fname.endswith('.csv'):
                return os.path.join(path, fname)

        raise FileNotFoundError("No CSV file found in the Kaggle dataset.")



class ResumeCSVLoader:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path

    def load_resumes(self) -> List[Dict]:
        df = pd.read_csv(self.csv_path)
        resumes = []
        for idx, row in df.iterrows():
            resumes.append({
                "id": idx,
                "category": row.get("Category", "").strip(),
                "text": str(row.get("Resume", "")).strip()
            })
        return resumes


class PDFResumeLoader:
    def __init__(self, folder_path: str = "generated_resumes"):
        self.folder_path = folder_path

    def load_resumes(self) -> List[Dict]:
        resumes = []
        for idx, fname in enumerate(os.listdir(self.folder_path)):
            if fname.endswith(".pdf"):
                path = os.path.join(self.folder_path, fname)
                text = self._extract_text(path)
                resumes.append({
                    "id": idx,
                    "category": "PDF", 
                    "text": text.strip()
                })
        return resumes

    def _extract_text(self, pdf_path: str) -> str:
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()
        return full_text
    

class TextChunker:
    def __init__(self, chunk_size: int = 300, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.tokenizer = TreebankWordTokenizer()

    def chunk_text(self, text: str) -> List[str]:
        tokens = self.tokenizer.tokenize(text)
        chunks = []
        i = 0
        while i < len(tokens):
            chunk = tokens[i:i + self.chunk_size]
            chunks.append(" ".join(chunk))
            i += self.chunk_size - self.overlap
        return chunks



class EmbeddingGenerator:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)

    def embed_chunks(self, chunks: List[str]):
        return self.model.encode(chunks, convert_to_tensor=True)


class ResumeProcessor:
    def __init__(self, source: str = "csv"):
        if source == "csv":
            downloader = DatasetDownloader()
            csv_path = downloader.get_csv_path()
            self.loader = ResumeCSVLoader(csv_path)
        elif source == "pdf":
            self.loader = PDFResumeLoader("generated_resumes")
        else:
            raise ValueError("Source must be 'csv' or 'pdf'.")

        self.chunker = TextChunker()
        self.embedder = EmbeddingGenerator()

    def process(self):
        all_chunks = []
        resumes = self.loader.load_resumes()

        for resume in tqdm(resumes, desc="🔍 Processing Resumes"):
            chunks = self.chunker.chunk_text(resume["text"])
            if not chunks:
                continue

            embeddings = self.embedder.embed_chunks(chunks)

            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                all_chunks.append({
                    "resume_id": resume["id"],
                    "category": resume["category"],
                    "chunk_id": i,
                    "text": chunk,
                    "embedding": embedding
                })

        return all_chunks


if __name__ == "__main__":
    nltk.download("punkt")  

    processor = ResumeProcessor()
    chunks = processor.process()

    print(f"\n✅ Processed {len(chunks)} chunks from {len(set(c['resume_id'] for c in chunks))} resumes.")
