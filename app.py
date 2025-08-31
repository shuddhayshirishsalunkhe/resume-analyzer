# app.py
import streamlit as st
import PyPDF2
import re
from rapidfuzz import fuzz

# --------- CONFIG ---------
# Fuzzy threshold (0-100). Increase to be stricter, decrease to be looser.
FUZZY_THRESHOLD = 75

# Canonical skills list (IT + non-IT). Expand this list as needed.
SKILLS = {
    "python", "java", "c++", "c#", "machine learning", "deep learning",
    "data science", "sql", "nosql", "excel", "powerpoint", "presentation",
    "communication", "leadership", "project management", "tensorflow", "pytorch",
    "cloud", "aws", "gcp", "azure", "nlp", "natural language processing",
    "docker", "kubernetes", "rest api", "api development", "flask", "django",
    "spring boot", "react", "javascript", "html", "css", "typescript",
    "tableau", "power bi", "git", "linux", "data structures", "algorithms",
    "testing", "qa", "agile", "scrum", "product management", "ms office",
    "sales", "marketing", "seo", "social media", "content writing",
    "graphic design", "photoshop", "illustrator", "crm", "salesforce",
    "negotiation", "market research", "event management"
}

# Synonyms / alternate terms mapping -> map many variations to canonical skill
SYNONYMS = {
    "ml": "machine learning",
    "deep-learning": "deep learning",
    "deep learning": "deep learning",
    "ai": "machine learning",
    "artificial intelligence": "machine learning",
    "python3": "python",
    "py": "python",
    "js": "javascript",
    "aws cloud": "aws",
    "amazon web services": "aws",
    "google cloud": "gcp",
    "gcp cloud": "gcp",
    "db": "sql",
    "rest": "rest api",
    "restful": "rest api",
    "nlp": "nlp",
    "natural-language-processing": "nlp",
    "product-manager": "product management",
    "ppt": "powerpoint"
}

# Preprocess synonyms keys to lower
SYNONYMS = {k.lower(): v.lower() for k, v in SYNONYMS.items()}

# Normalize skill set to lowercase
SKILLS = set(s.lower() for s in SKILLS)

# --------- HELPERS ---------
def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    # replace punctuation with spaces
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    # collapse multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def apply_synonyms(text: str) -> str:
    # replace occurrences of synonyms with canonical
    # use word boundaries to avoid partial replacements
    for alt, canon in SYNONYMS.items():
        pattern = r'\b' + re.escape(alt) + r'\b'
        text = re.sub(pattern, canon, text)
    return text

def extract_text_from_pdf(uploaded_file) -> str:
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + " "
        return text
    except Exception as e:
        return ""

def extract_skills_from_text(text: str) -> set:
    """
    Detect skills from text using:
      1) exact phrase matching (word boundaries)
      2) fuzzy matching against whole text (if exact not found)
    """
    text = normalize_text(text)
    text = apply_synonyms(text)

    found = set()

    # First try exact phrase matching for each skill
    for skill in SKILLS:
        # build regex for phrase match; handle multi-word skills
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text):
            found.add(skill)

    # For skills not found, try fuzzy matching against the whole text
    remaining = SKILLS - found
    if remaining:
        for skill in remaining:
            score = fuzz.partial_ratio(skill, text)  # compares skill vs text
            if score >= FUZZY_THRESHOLD:
                found.add(skill)

    return found

def analyze_resume(resume_text: str, job_desc: str):
    resume_text = normalize_text(resume_text)
    job_desc = normalize_text(job_desc)

    # apply synonyms mapping to both
    resume_text = apply_synonyms(resume_text)
    job_desc = apply_synonyms(job_desc)

    resume_skills = extract_skills_from_text(resume_text)
    job_skills = extract_skills_from_text(job_desc)

    # If job description didn't include any recognized skills from our list,
    # fall back to extracting candidate skills from job_desc by keyword heuristics:
    if not job_skills:
        # as fallback, split jd into words and take intersection with SKILLS
        for skill in SKILLS:
            if skill in job_desc:
                job_skills.add(skill)

    matched = resume_skills.intersection(job_skills)
    missing = job_skills - resume_skills

    score = (len(matched) / len(job_skills) * 100) if job_skills else 0.0
    return round(score, 2), sorted(list(matched)), sorted(list(missing)), sorted(list(resume_skills))

# --------- STREAMLIT UI ---------
st.set_page_config(page_title="AI Resume Analyzer (Skill-aware)", layout="centered")
st.title("📄 AI Resume Analyzer — Skill-aware (Improved)")

st.markdown(
    "Upload your resume (PDF) and paste a job description. "
    "This version matches **skills** (with synonyms & fuzzy matching), not random keywords."
)

uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
job_desc = st.text_area("Paste Job Description", height=200)

if st.button("Analyze") or (uploaded_file and job_desc):
    if not uploaded_file:
        st.error("Please upload a resume PDF first.")
    elif not job_desc.strip():
        st.error("Please paste a job description.")
    else:
        raw_resume = extract_text_from_pdf(uploaded_file)
        if not raw_resume:
            st.error("Could not read PDF. Try a different file.")
        else:
            score, matched, missing, resume_skills = analyze_resume(raw_resume, job_desc)

            st.success(f"✅ Resume Match Score: {score} %")
            st.markdown("**Matched Skills (found in resume):**")
            if matched:
                st.write(", ".join(matched))
            else:
                st.write("None")

            st.markdown("**Missing Skills (required by JD but not in resume):**")
            if missing:
                st.write(", ".join(missing))
            else:
                st.write("None — Nice!")

            st.markdown("**All skills detected in your resume (from skill-list):**")
            st.write(", ".join(resume_skills) if resume_skills else "None detected")

            st.info("Tip: You can expand the `SKILLS` and `SYNONYMS` lists in app.py to include more domain-specific keywords you care about.")

