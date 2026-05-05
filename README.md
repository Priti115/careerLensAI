<<<<<<< HEAD
# CareerLensAI

CareerLensAI is a modular AI-powered resume analysis backend. It accepts PDF,
raw text, or JSON resume input and returns a full career analysis response with
top-3 job role predictions, job description generation, skill gaps, resume
score, structure feedback, learning resources, and improvement suggestions.

No database is used in the current backend. Model artifacts and optional vectors
are stored locally under `models/` and local files.

## Backend Structure

- `app.py`: FastAPI application that combines the full resume analysis pipeline.
- `.env.example`: optional LLM and frontend CORS configuration.
- `frontend/`: browser demo for text/PDF resume analysis with a floating career chatbot.
- `scripts/smoke_test_api.py`: command-line smoke test for a running API.
- `postman/CareerLensAI.postman_collection.json`: ready-to-import Postman API tests.
- `modules/data_preprocessing.py`: resume cleaning plus raw text and JSON input normalization.
- `modules/resume_parser.py`: PDF text extraction and structured resume field parsing.
- `modules/job_prediction.py`: loads `tfidf.pkl`, `clf.pkl`, and `encoder.pkl`; returns top-3 roles.
- `modules/model_trainer.py`: trains TF-IDF + balanced classifier from `dataset/finalData.csv`.
- `modules/description_generator.py`: prompt-based role context generation for internal analysis.
- `modules/skill_gap.py`: compares extracted skills with expected role skills.
- `modules/resume_score.py`: scores resume quality from 0 to 100 and returns structure feedback.
- `modules/recommendations.py`: suggests YouTube, Coursera, Udemy, and Infosys Springboard learning links.
- `modules/vector_store.py`: optional local pickle storage for vector artifacts.
- `notebooks/model_training.ipynb`: leakage-safe TF-IDF + balanced classifier training notebook.
- `models/`: local model artifacts.
- `dataset/finalData.csv`: the single training dataset used by this project.

## Critical Model Fixes

- Prediction returns the top 3 roles instead of only one.
- Training uses only `dataset/finalData.csv`.
- The training module splits train/test data before fitting TF-IDF to avoid data leakage.
- Class imbalance is handled with a balanced calibrated SVM.
- CSV validation requires the industry-ready final schema: `Category` and `Resume_clean`.
- API prediction reranks the trained model with role-skill and role-description matching to reduce irrelevant roles.

## Train Model

```bash
python -m modules.model_trainer
```

This reads:

```text
dataset/finalData.csv
```

And writes:

```text
models/tfidf.pkl
models/clf.pkl
models/encoder.pkl
models/model_metrics.json
```

Retrain after every dataset change. The trainer uses word TF-IDF plus
character TF-IDF with a balanced calibrated SVM, then the API reranks model
scores with role-skill and role-description profile matching.

## Run Locally

Windows PowerShell:

```powershell
.\run_backend.ps1
```

Manual setup:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Optional LLM setup:

```bash
copy .env.example .env
```

Then add your `OPENAI_API_KEY`. Without a key, the backend still works with a
local fallback job description generator.

Open:

```text
http://127.0.0.1:8000/docs
```

Demo frontend:

```text
http://127.0.0.1:8000/demo/
```

Smoke test:

```bash
python scripts/smoke_test_api.py
```

Postman:

1. Open Postman.
2. Click `Import`.
3. Select `postman/CareerLensAI.postman_collection.json`.
4. Run `Health Check`.
5. Run `Analyze Resume Text`.
6. For `Analyze Resume PDF`, choose a PDF in the `file` form-data field first.
7. Run `AI Career Chat` after analysis if you want chatbot guidance.

## Example API Usage

PDF upload:

```bash
curl -X POST "http://127.0.0.1:8000/analyze/resume" \
  -F "file=@resume.pdf"
```

Raw text:

```bash
curl -X POST "http://127.0.0.1:8000/analyze/text" \
  -H "Content-Type: application/json" \
  -d "{\"resume\":\"Python SQL machine learning projects with 3 years experience\"}"
```

## Current Project Policy

The project intentionally has no database layer right now. Legacy MongoDB files,
duplicate datasets, checkpoints, duplicate root notebooks, and unused XGBoost
artifacts were removed so the backend remains clean and easy to connect to a
frontend.
=======
# CareerLens AI

CareerLens AI is being organized as a full resume-analysis pipeline, not only a category classifier.

## Notebook flow

- [1_Resume_File_Extraction_And_Structuring.ipynb](C:/Users/Lenovo/Documents/all_projects/careerLensAI/1_Resume_File_Extraction_And_Structuring.ipynb): extract text from uploaded PDF and Word resumes, clean it, parse relevant fields, and save a separate structured dataset
- [2_Dataset_Cleaning_And_Database.ipynb](C:/Users/Lenovo/Documents/all_projects/careerLensAI/2_Dataset_Cleaning_And_Database.ipynb): clean the labeled training datasets, structure resume fields, and store the processed training data in SQLite
- [3_Catagory_Prediction.ipynb](C:/Users/Lenovo/Documents/all_projects/careerLensAI/3_Catagory_Prediction.ipynb): train the category prediction model from the processed training data
- [4_Profile_Match_And_Skill_Gap.ipynb](C:/Users/Lenovo/Documents/all_projects/careerLensAI/4_Profile_Match_And_Skill_Gap.ipynb): estimate percentage match across multiple target profiles and list missing skills under each profile
- [5_Recommendations_For_Top_Profiles.ipynb](C:/Users/Lenovo/Documents/all_projects/careerLensAI/5_Recommendations_For_Top_Profiles.ipynb): recommend courses, certifications, tutorials, and projects for the highest-match profiles

## Core files

- [resume_extraction.py](C:/Users/Lenovo/Documents/all_projects/careerLensAI/resume_extraction.py): reusable rule-based extraction logic for mixed resume text
- [resume_analysis.db](C:/Users/Lenovo/Documents/all_projects/careerLensAI/resume_analysis.db): local SQLite database for processed resumes and analysis results
- [dataset](C:/Users/Lenovo/Documents/all_projects/careerLensAI/dataset): training datasets and generated CSV outputs
- [uploads](C:/Users/Lenovo/Documents/all_projects/careerLensAI/uploads): place new user-uploaded resumes here for PDF or Word extraction

## Extracted fields

The extractor can create structured columns from a single resume text field:

- `name`
- `email`
- `phone`
- `skills`
- `education`
- `experience`
- `estimated_experience_years`
- `certifications`
- `projects`
- `linkedin`
- `github`

## Current design idea

The final system can combine all notebook outputs into one application flow:

1. user uploads a resume
2. text is extracted and stored
3. category prediction runs
4. multi-profile match percentages are calculated
5. skill gaps are identified for likely profiles
6. recommendations are generated for top-matching profiles

Extraction works best on `Resume_raw` before aggressive cleaning removes punctuation and line breaks.
>>>>>>> cdafa2b33b90018d8ca0f5fce1da52d75e6a4bf0
