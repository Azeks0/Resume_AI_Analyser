import os
import subprocess
from jinja2 import Template
from faker import Faker
import random

# ===== CONFIGURATION =====
NUM_RESUMES = 20  # Change this to generate more/less
OUTPUT_DIR = "generated_resumes"
TEMPLATE_FILE = "resume_template.tex"
# ==========================

# Create output folder if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initialize Faker
fake = Faker()

# Load LaTeX template
with open(TEMPLATE_FILE, 'r') as f:
    latex_template = Template(f.read())

# Generate resumes
for i in range(1, NUM_RESUMES + 1):
    name = fake.name()
    email = fake.email()
    phone = fake.phone_number()
    linkedin = f"linkedin.com/in/{name.lower().replace(' ', '')}"
    job_title = fake.job()
    company = fake.company()
    location = fake.city()
    dates = f"{random.randint(2019, 2022)}–Present"
    job_description = fake.sentence(nb_words=10)
    degree = "B.Sc. in Computer Science"
    university = f"{fake.last_name()} University"
    graduation_date = fake.date(pattern="%B %Y")

    data = {
        "name": name,
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "job_title": job_title,
        "company": company,
        "location": location,
        "dates": dates,
        "job_description": job_description,
        "degree": degree,
        "university": university,
        "graduation_date": graduation_date
    }

    # Render LaTeX
    tex_code = latex_template.render(data)
    tex_filename = os.path.join(OUTPUT_DIR, f"resume_{i}.tex")

    # Write .tex file
    with open(tex_filename, "w") as f:
        f.write(tex_code)

    subprocess.run([
        "/Library/TeX/texbin/pdflatex",
        "-output-directory", OUTPUT_DIR,
        tex_filename
    ], check=False)


    # Clean up aux/log/tex
    for ext in [".aux", ".log", ".tex"]:
        path = os.path.join(OUTPUT_DIR, f"resume_{i}{ext}")
        if os.path.exists(path):
            os.remove(path)

    print(f"✅ Saved resume_{i}.pdf in {OUTPUT_DIR}/")
