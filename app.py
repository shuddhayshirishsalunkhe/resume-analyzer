# app.py

import streamlit as st
import PyPDF2
import re
import nltk
from sklearn.feature_extraction.text import CountVectorizer
from nltk.corpus import stopwords

nltk.download("stopwords")

# --- Function to extract text from PDF ---
def extract_text_from_pdf(uploaded_file):
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + " "
    return text

# --- Function to clean text ---
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return text

# --- Analyzer Function ---
def analyze_resume(resume_text, job_desc):
    resume_text = clean_text(resume_text)
    job_desc = clean_text(job_desc)

    cv = CountVectorizer(stop_words=stopwords.words("english"))
    cv.fit_transform([resume_text, job_desc])

    resume_words = set(resume_text.split())
    job_words = set(job_desc.split())
    matched_words = resume_words.intersection(job_words)
    missing_words = job_words - resume_words

    match_score = (len(matched_words) / len(job_words)) * 100 if job_words else 0

    return match_score, matched_words, missing_words

# --- Streamlit UI ---
st.title("📄 AI Resume Analyzer")
st.write("Upload your resume and paste a job description to see how well you match!")

uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
job_desc = st.text_area("Paste Job Description")

if uploaded_file and job_desc:
    resume_text = extract_text_from_pdf(uploaded_file)
    score, matched, missing = analyze_resume(resume_text, job_desc)

    st.success(f"✅ Resume Match Score: {round(score, 2)} %")
    st.write("**Matched Skills:**", ", ".join(matched) if matched else "None")
    st.write("**Missing Skills:**", ", ".join(missing) if missing else "None")
