# Kipaji Chetu – AI-Powered Personalized Learning Platform

**Kipaji Chetu** (Swahili for *"Our Talent"*) is an open-source adaptive learning system designed to help teachers personalize education and support students with diverse needs. It uses AI to generate real-time questions, provides instant feedback, and offers text-to-speech and speech-to-text accessibility – all while giving teachers a clear dashboard of class performance.

---

## The Problem

In many classrooms, especially in under-resourced settings, a single teacher manages 40+ students. It’s challenging to:

* Identify struggling students before exams.
* Adapt content to each student’s pace.
* Support learners with disabilities or language barriers.
* Spend hours grading and compiling reports.

Teachers need a tool that works **with** them, not against them.

---

## Our Solution

Kipaji Chetu addresses these challenges by:

* **Personalizing questions** in real time based on each student’s performance.
* **Providing instant AI-powered feedback** that explains correct answers and offers hints.
* **Ensuring accessibility** with text-to-speech (TTS) and speech-to-text (STT).
* **Empowering teachers** with a live dashboard showing struggling students, hardest topics, and class averages – without manual grading.

---

## Key Features

| Area                   | Features                                                                                                                                                 |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Student Experience** | Secure login with student ID, topic selection, adaptive multiple-choice questions, instant AI feedback, session progress bar.                            |
| **Accessibility**      | Text-to-Speech (Edge-TTS) for questions and feedback, Speech-to-Text (Groq Whisper) for voice answers, simplified explanation mode.                      |
| **Teacher Dashboard**  | Real-time class average, list of struggling students (score <50%), most difficult topics, at-risk student flags, test panels for TTS/STT.                |
| **AI Integration**     | Dynamic question generation via Groq (Llama 3), adaptive difficulty based on recent performance, feedback and simplification with context-aware prompts. |
| **Scalability**        | Async FastAPI backend, PostgreSQL with Aiven, Docker containerization, ready for cloud deployment.                                                       |

---

## Technology Stack

| Component            | Technology                                   |
| -------------------- | -------------------------------------------- |
| **Backend**          | FastAPI (async), SQLAlchemy, Pydantic        |
| **Database**         | PostgreSQL (Aiven)                           |
| **AI / LLM**         | Groq (Llama 3.3-70B, Llama 3.1-8B)           |
| **Text-to-Speech**   | Microsoft Edge-TTS                           |
| **Speech-to-Text**   | Groq Whisper                                 |
| **Frontend**         | Static HTML, Bootstrap, Chart.js, vanilla JS |
| **Containerization** | Docker, docker-compose                       |
| **Deployment**       | Render (web service), Aiven (PostgreSQL)     |
| **Version Control**  | Git, GitHub                                  |

---

## Architecture Overview

```
┌──────────────┐ ┌───────────────┐ ┌───────────────┐
│ Frontend     │▶│ FastAPI       │▶│ PostgreSQL    │
│ (static)     │ │ (async)       │ │ (Aiven)      │
└──────────────┘ └─────┬─────────┘ └───────────────┘
                        │
                        ▼
               ┌─────────────────┐
               │ Groq (LLMs)     │
               │ Edge-TTS        │
               └─────────────────┘
```

* **Frontend:** Serves static HTML, JS, and CSS.
* **Backend:** Exposes REST endpoints for student login, question fetching, answer submission, teacher reports, TTS, and STT.
* **Database:** Stores students, topics, quizzes, attempts, feedback logs, and performance metrics.
* **External Services:** Provide AI question generation (Groq) and voice synthesis (Edge-TTS).

---

## Getting Started

### Prerequisites

* Docker & Docker Compose (or Python 3.10+ for local development)
* Aiven PostgreSQL instance (or local PostgreSQL)
* Groq API key (free tier available)

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/kipaji-chetu.git
cd kipaji-chetu
```

2. **Set up environment variables**

Copy `.env.example` to `.env` and fill in your credentials:

```
DB_HOST=your-aiven-host
DB_PORT=your-port
DB_NAME=your-db-name
DB_USER=your-user
DB_PASSWORD=your-password
SCHEMA=kipaji
GROQ_API_KEY=your-groq-key
DATABASE_URL_ASYNC=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}?sslmode=require
DATABASE_URL_SYNC=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}?sslmode=require
```

3. **Run with Docker**

```bash
docker-compose up --build
```

The app will be available at [http://localhost:8000](http://localhost:8000).

4. **Initialize the database**

```bash
docker exec -it kipaji_app python scripts/init_db.py
docker exec -it kipaji_app python scripts/seed_data.py
```

### Access the Interfaces

* Landing page: `/`
* Student portal: `/static/student.html`
* Teacher dashboard: `/static/teacher-dashboard.html`
* API docs: `/docs`

### API Endpoints (Summary)

| Method | Endpoint                                   | Description                  |
| ------ | ------------------------------------------ | ---------------------------- |
| GET    | /api/students/{id}                         | Get student details          |
| GET    | /api/topics                                | List all topics              |
| GET    | /api/next-question/{student_id}/{topic_id} | Fetch adaptive question      |
| POST   | /api/submit-answer                         | Submit answer, get feedback  |
| GET    | /api/teacher-report                        | Get class analytics          |
| GET    | /api/tts?text=...                          | Text-to-speech audio         |
| POST   | /api/stt                                   | Speech-to-text transcription |

Full interactive documentation is available at `/docs`.

---

## Deployment

The application is deployed on Render using Docker, with an Aiven PostgreSQL database.

Live demo: [https://kipaji-chetu-learning.onrender.com](https://kipaji-chetu-learning.onrender.com)

**Deploy your own:**

1. Fork the repository
2. Create a Render Web Service connected to your fork
3. Set environment variables (as in `.env.example`)
4. Render will automatically build and run the Docker container
5. Run the database initialization commands via Render’s shell

---

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/AmazingFeature`
3. Commit your changes: `git commit -m 'Add some AmazingFeature'`
4. Push to the branch: `git push origin feature/AmazingFeature`
5. Open a Pull Request

---

## License

Distributed under the MIT License. See `LICENSE` for more information.

---

## Contact

* Project Link: [GitHub](https://github.com/yourusername/kipaji-chetu)
* Live Demo: [https://kipaji-chetu-learning.onrender.com](https://kipaji-chetu-learning.onrender.com)

