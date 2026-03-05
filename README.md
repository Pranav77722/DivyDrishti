# 👁️ DivyDrishti — Face Recognition Attendance System

<p align="center">
  <b>Smart Attendance System for Indian Engineering Colleges</b><br/>
  No more proxy attendance. No more manual registers. 🎓
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Frontend-Next.js%2015-black?logo=next.js" />
  <img src="https://img.shields.io/badge/Backend-Flask-blue?logo=flask" />
  <img src="https://img.shields.io/badge/Database-Firebase-orange?logo=firebase" />
  <img src="https://img.shields.io/badge/AI-DeepFace%20%7C%20MTCNN-green" />
  <img src="https://img.shields.io/badge/Made%20in-India%20🇮🇳-orange" />
</p>

---

## 📌 About the Project

**DivyDrishti** is a college attendance management system built specifically for **Indian engineering colleges**. It uses **AI-based face recognition** to automatically mark attendance — no more proxy bunkings, no more manual entry in registers!

Designed keeping in mind the **75% attendance requirement** enforced by most Indian universities (GTU, Mumbai University, VTU, RGPV, AKTU, etc.), this system helps faculty and HODs track defaulters easily.

---

## 🎯 Key Features

- 📷 **Auto Attendance via Face Recognition** — Marks present/absent automatically using camera
- � **Proxy Detection** — Only registered students' faces get marked
- 🧑‍🏫 **Separate Portals** — Student, Teacher (Faculty), and Admin (HOD/Principal)
- 📊 **Attendance Reports** — Subjectwise attendance, defaulter list generation
- ☁️ **Firebase Cloud** — Data stored securely on cloud, no local server crashes
- 📱 **Mobile Friendly UI** — Works on college lab PCs and mobile browsers
- � **75% Tracker** — Students can see if they are falling short of attendance

---

## 🏫 Who Is This For?

| User | Role in College |
|------|----------------|
| �‍🎓 Student | View own attendance, check shortfall, join sessions |
| 👨‍🏫 Teacher / Faculty | Start class sessions, view classwise attendance |
| 🏛️ Admin / HOD | Full control — manage students, faculty, all reports |

---

## 🏗️ Project Structure

```
DivyDrishti/
├── backend/                    # Python Flask API (Server)
│   ├── app.py                  # Main Flask app
│   ├── firebase_config.py      # Firebase setup
│   ├── recognition.py          # Face recognition (DeepFace + MTCNN)
│   ├── auth/                   # Login / Signup routes
│   ├── student/                # Student APIs (view attendance, register)
│   ├── teacher/                # Faculty APIs (start session, reports)
│   └── requirements.txt        # Python packages
│
├── frontend/                   # Next.js Frontend (Website)
│   └── app/
│       ├── page.tsx            # Home / Landing Page
│       ├── signin/             # Login Page
│       ├── signup/             # Registration Page
│       ├── student/            # Student Dashboard
│       ├── teacher/            # Faculty Dashboard
│       └── components/         # Reusable UI components
│
├── takeImage.py                # Capture student face photos
├── trainImage.py               # Train face recognition model
└── haarcascade_frontalface_default.xml  # OpenCV model
```

---

## 🧰 Tech Stack

| Part | Technology Used |
|------|----------------|
| Frontend | Next.js 15, TypeScript, React |
| Backend | Python 3, Flask, Flask-CORS |
| Database | Firebase Firestore (Cloud) |
| Authentication | Firebase Auth |
| Face Recognition | DeepFace, MTCNN, OpenCV, NumPy |

---

## 🚀 How to Run (Local Setup)

### ✅ Requirements
- Python 3.9+
- Node.js 18+
- Firebase project (free tier works)

---

### Step 1 — Clone the Repo
```bash
git clone https://github.com/Pranav77722/DivyDrishti.git
cd DivyDrishti
```

---

### Step 2 — Backend Setup (Flask)
```bash
cd backend
pip install -r requirements.txt
python app.py
```
> Backend runs on `http://localhost:5000`

---

### Step 3 — Frontend Setup (Next.js)
```bash
cd frontend
npm install
npm run dev
```
> Frontend runs on `http://localhost:3000`

Open your browser and go to 👉 **http://localhost:3000**

---

## � How Face Recognition Works

```
Student Registers → Face Photos Captured → Embeddings Stored in Firebase
        ↓
Faculty Starts Session → Camera Detects Faces → Matches with Database
        ↓
Attendance Auto-Marked ✅ (No manual entry needed!)
```

---

## ⚠️ Important Notes

> 🔒 **Never push `serviceAccountKey.json` to GitHub!** Add it to `.gitignore`.

> 📶 Needs a **decent internet connection** for Firebase.

> 💡 Works best in **good lighting** for accurate face detection.

> 📁 Student face photos must be captured during **registration** before using the system.

---

## 📸 Project Screenshots

> See the `Project Snap/` folder for screenshots.

---

## 👨‍� Developers

| Name | GitHub |
|------|--------|
| Rahul Patel | [@Patelrahul4884](https://github.com/Patelrahul4884) |
| Pranav | [@Pranav77722](https://github.com/Pranav77722) |

---

## 📄 License

Free to use for educational and college project purposes. ⭐ Star the repo if it helped!

---

<p align="center">🇮🇳 Built for Indian Engineering Students | Say No to Proxy! 🚫</p>
