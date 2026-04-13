<h1 align="center">Assignment Solver Backend 📝</h1>
<p align="center">
  <img src="https://img.shields.io/badge/Framework-Django-092E20?style=for-the-badge&logo=django&logoColor=white" />
  <img src="https://img.shields.io/badge/Language-Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
</p>

## 📖 Overview
The foundational backend REST API for the **Assignment Solver** ecosystem. It is engineered using Python and Django to autonomously process problem inputs from clients, execute specific procedural logic/algorithms, and return comprehensive solutions.

## ✨ Features
- **API First**: Designed to connect seamlessly with custom client applications (such as the Flutter frontend app).
- **Processing Engine**: Efficient viewsets and models dedicated to evaluating and parsing assignments.
- **Security**: Django's native authentication layers integrated.

## 🛠️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Imranxhah/assignment-solver-backend.git
   cd assignment-solver-backend
   ```

2. **Initialize Env & Dependencies:**
   ```bash
   python -m venv env
   source env/bin/activate 
   pip install -r requirements.txt
   ```

3. **Run Migrations & Start:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py runserver
   ```

---
*Created by [Imranxhah](https://github.com/Imranxhah)*
