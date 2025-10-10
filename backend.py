from flask import Flask, render_template, request
import os
import docx2txt
import PyPDF2
# pandas is imported but not used in the current logic, kept for future expansion
import pandas as pd 
import re

# --- Configuration ---
app = Flask(__name__, template_folder='templates', static_folder='static')
# A better practice is to use an absolute path or relative to the script location
# For simplicity, we use the relative path 'uploads'
app.config['UPLOAD_FOLDER'] = 'uploads' 

# Example required skills for the job description
REQUIRED_SKILLS = ['Python', 'Machine Learning', 'Data Science', 'SQL', 'Flask', 'HTML', 'CSS', 'JavaScript']
# Set a clear threshold
SHORTLISTING_THRESHOLD = 60

# --- Helper Functions for Resume Processing ---

def extract_text_from_pdf(file_path):
    """Extracts text content from a PDF file."""
    try:
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() if page.extract_text() else ""
            return text
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
        return ""

def extract_text_from_docx(file_path):
    """Extracts text content from a DOCX file."""
    try:
        # docx2txt handles .docx files well
        return docx2txt.process(file_path)
    except Exception as e:
        print(f"Error reading DOCX {file_path}: {e}")
        return ""

def extract_email(text):
    """Extracts the first valid email address from the text."""
    # Pattern for common email format
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return emails[0] if emails else "Email Not Found"

def extract_skills(text):
    """Finds required skills present in the resume text."""
    text_lower = text.lower()
    skills_found = [skill for skill in REQUIRED_SKILLS if skill.lower() in text_lower]
    return skills_found

def calculate_score(candidate_skills):
    """Calculates the match percentage based on required skills."""
    matched_skills = set(candidate_skills).intersection(set(REQUIRED_SKILLS))
    
    if not REQUIRED_SKILLS:
        return 0.00
        
    score = (len(matched_skills) / len(REQUIRED_SKILLS)) * 100
    return round(score, 2)

# --- Flask Routes ---

@app.route("/", methods=['GET', 'POST'])
def index():
    """Handles file upload, processing, and rendering the results page."""
    results = []
    
    if request.method == 'POST':
        # Check if files were uploaded
        files = request.files.getlist("resumes")
        
        for file in files:
            # Skip if the file is empty or has no filename
            if not file or not file.filename:
                continue

            filename = file.filename
            
            # 1. Save the file
            # Create the upload directory if it doesn't exist (important for the first run)
            upload_dir = app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)

            # 2. Extract Text
            if filename.lower().endswith('.pdf'):
                text = extract_text_from_pdf(filepath)
            elif filename.lower().endswith(('.docx', '.doc')):
                text = extract_text_from_docx(filepath)
            else:
                # Handle unsupported file types gracefully
                text = ""

            # 3. Analyze Text
            email = extract_email(text)
            skills = extract_skills(text)
            score = calculate_score(skills)
            
            status = "Shortlisted" if score >= SHORTLISTING_THRESHOLD else "Rejected"
            
            # Use os.path.splitext to safely get the filename without the extension
            candidate_name = os.path.splitext(filename)[0]

            # 4. Store Results
            results.append({
                "Name": candidate_name,
                "Email": email,
                "Skills": ", ".join(skills) if skills else "None Found",
                "Score": f"{score}%", # Format score for display
                "Status": status
            })
            
            # OPTIONAL: Clean up the uploaded file after processing
            # os.remove(filepath) 
            
    # Render the HTML template, passing the results list
    return render_template("index.html", results=results)

# --- Application Entry Point ---

if __name__ == "__main__":
    # Ensure the upload folder exists before starting the server
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Run the application in debug mode
    app.run(debug=True)