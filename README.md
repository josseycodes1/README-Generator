# ReadMe Generator

## Project Overview

ReadMe Generator is a web-based tool that automatically generates accurate, high-quality `README.md` files for software projects by analyzing real repository files.

Users simply paste a GitHub repository URL, and the system clones and parses the repository in the background to generate a README that reflects the actual project setup, dependencies, and structure.

**No sign-up.**  
**No login.**  
**Just paste a repo and generate a README.**

---

## Core Goals

- Zero-friction usage (no authentication)
- Accurate, non-generic README generation
- Support for multiple languages and frameworks
- Mandatory file-structure visualization
- Copyable and downloadable README output
- Asynchronous backend processing for performance

---

## Tech Stack

### Backend
- Django
- Django REST Framework
- Celery
- Redis
- PostgreSQL
- Python

### Frontend (to be built later)
- Next.js
- Tailwind CSS

---

##  Basic Installation (Backend)

### Prerequisites

Ensure the following are installed on your system:

- Python 3.10+
- PostgreSQL
- Redis
- Git
- pip / virtualenv

---

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/readme-generator.git
cd readme-generator
````

---

### 2️⃣ Create & Activate Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows
```

---

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Environment Variables

Create a `.env` file in the root directory:

```env
DEBUG=True
SECRET_KEY=your-secret-key

DB_NAME=readme_generator
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

REDIS_URL=redis://127.0.0.1:6379/0
```

---

### 5️⃣ Database Setup

```bash
python manage.py migrate
```

---

### 6️⃣ Run Redis Server

```bash
redis-server
```

---

### 7️⃣ Start Celery Worker

```bash
celery -A config worker -l info
```

---

### 8️⃣ Run Django Server

```bash
python manage.py runserver
```

The backend API will be available at:

```
http://127.0.0.1:8000/
```

---

## 🔄 How README Generation Works

1. User submits a GitHub repository URL
2. Django creates a generation job
3. Celery clones the repository
4. Files are read and parsed:

   * Dependencies
   * Environment variables
   * Framework configs
5. File tree is generated
6. README markdown is assembled
7. Result is returned to the frontend

---

## File Structure (Mandatory Output)

Every generated README includes a directory tree like:

```text
project-root/
├── backend/
│   ├── settings.py
│   ├── urls.py
│   └── models.py
├── frontend/
│   ├── pages/
│   └── components/
└── requirements.txt
```

---

## Output

* README is rendered on screen
* Fully editable
* Can be copied directly
* Downloadable as `README.md`

---

## Backend Architecture

### Core Apps

* `generator` — job creation & status tracking
* `analysis` — repo parsing & data extraction
* `readme` — markdown generation engine

---

## Roadmap

* Frontend UI with Next.js
* Template selection
* README editing UI
* GitHub push support
* Private repo support

```