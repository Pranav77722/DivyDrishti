# 👁️ DivyDrishti — Attendance Management System using Face Recognition

<p align="center">
  <img src="AMS.ico" alt="DivyDrishti Logo" width="80"/>
</p>

<p align="center">
  <b>A smart, face-recognition-powered attendance system for educational institutions.</b><br/>
  Built with Next.js · Flask · Firebase · DeepFace · OpenCV
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Frontend-Next.js%2015-black?logo=next.js" />
  <img src="https://img.shields.io/badge/Backend-Flask-blue?logo=flask" />
  <img src="https://img.shields.io/badge/Database-Firebase-orange?logo=firebase" />
  <img src="https://img.shields.io/badge/AI-DeepFace%20%7C%20MTCNN-green" />
  <img src="https://img.shields.io/badge/Language-TypeScript%20%7C%20Python-purple" />
</p>

---

## 📌 Overview

**DivyDrishti** is a full-stack attendance management system that uses **real-time face recognition** to automatically mark student attendance. Teachers can start sessions and the system identifies registered students through a live camera feed. Admins and teachers can view reports and manage records — all without manual roll calls.

---

## ✨ Features

- 🎥 **Real-time Face Recognition** — Automatically identifies students using a live camera
- 🔐 **Role-based Authentication** — Separate portals for Students, Teachers, and Admins
- 📊 **Attendance Dashboard** — View, filter, and export attendance records
- ☁️ **Firebase Backend** — Firestore for data storage, Firebase Auth for authentication
- 📸 **Student Registration** — Register face data for new students with image capture
- 📅 **Session Management** — Teachers can start/stop attendance sessions per subject
- 📱 **Responsive UI** — Works on desktop and mobile browsers

---

## 🏗️ Project Structure

```
DivyDrishti/
├── backend/                    # Flask REST API
│   ├── app.py                  # Main Flask application & routes
│   ├── firebase_config.py      # Firebase Admin SDK setup
│   ├── recognition.py          # Face recognition logic (DeepFace + MTCNN)
│   ├── auth/                   # Authentication routes
│   ├── student/                # Student-related API endpoints
│   ├── teacher/                # Teacher-related API endpoints
│   ├── requirements.txt        # Python dependencies
│   └── serviceAccountKey.json  # Firebase service account (⚠️ keep private)
│
├── frontend/                   # Next.js 15 App (TypeScript)
│   ├── app/
│   │   ├── page.tsx            # Landing page
│   │   ├── signin/             # Sign in page
│   │   ├── signup/             # Sign up page
│   │   ├── dashboard/          # Admin dashboard
│   │   ├── student/            # Student portal (view attendance, demo session)
│   │   ├── teacher/            # Teacher portal (start session, dashboard)
│   │   └── components/         # Shared UI components (CameraCapture, Navbar, etc.)
│   └── package.json
│
├── attendance.py               # Legacy attendance script
├── takeImage.py                # Script to capture training images
├── trainImage.py               # Script to train face recognition model
├── haarcascade_frontalface_default.xml  # OpenCV face detection model
└── requirements.txt            # Root Python dependencies
```

---

## 🧰 Tech Stack

| Layer       | Technology                                      |
|-------------|------------------------------------------------|
| Frontend    | Next.js 15, TypeScript, React, CSS              |
| Backend     | Python, Flask, Flask-CORS, Flask-Bcrypt         |
| Database    | Firebase Firestore                              |
| Auth        | Firebase Authentication                         |
| Face AI     | DeepFace, MTCNN, OpenCV, NumPy, SciPy          |
| Deployment  | (Configurable — Vercel for frontend, any Python host for backend) |

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** v18+
- **Python** 3.9+
- A **Firebase** project with Firestore enabled
- A `serviceAccountKey.json` from your Firebase project settings

---

### 🔧 Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file in `backend/` with:
```env
FLASK_ENV=development
SECRET_KEY=your_secret_key
```

Place your `serviceAccountKey.json` inside the `backend/` folder.

Start the Flask server:
```bash
python app.py
```

The backend will run at `http://localhost:5000`

---

### 🖥️ Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will run at `http://localhost:3000`

---

## 🧪 Face Recognition Flow

1. **Register** — Student registers and captures face images via the camera
2. **Train** — Face embeddings are generated and stored in Firebase using DeepFace + MTCNN
3. **Detect** — During a session, the camera feed is analyzed frame-by-frame
4. **Match** — Each detected face is compared against stored embeddings
5. **Mark** — Matched students are automatically marked **Present** in Firestore

---

## 👥 User Roles

| Role    | Capabilities                                                      |
|---------|-------------------------------------------------------------------|
| Student | View own attendance, participate in demo session                  |
| Teacher | Start/stop sessions, view class attendance, manage subjects       |
| Admin   | Full access — manage students, teachers, view all records         |

---

## 🔒 Security Notes

> ⚠️ **Never commit `serviceAccountKey.json` to a public repository.**
> Add it to `.gitignore` to keep your Firebase credentials private.

```gitignore
backend/serviceAccountKey.json
.env
```

---

## 📸 Screenshots

> Screenshots available in the `Project Snap/` folder.

---

## 📄 License

This project is for educational purposes. Feel free to fork and build upon it.

---

## 🙌 Contributors

- **Rahul Patel** — [GitHub](https://github.com/Patelrahul4884)
- **Pranav** — [GitHub](https://github.com/Pranav77722)

---

<p align="center">Made with ❤️ for smarter classrooms</p>
