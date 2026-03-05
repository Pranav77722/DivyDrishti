# teacher/attendance_records.py - OPTIMIZED VERSION

import io
import json
import base64
import numpy as np
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from PIL import Image
from scipy.spatial.distance import cosine
from deepface import DeepFace
import logging
import time

logger = logging.getLogger(__name__)

# Attendance Blueprint with URL prefix
attendance_session_bp = Blueprint(
    "attendance_session",
    __name__,
    url_prefix="/api/attendance"
)

# ----------------- OPTIMIZED Helper Functions ----------------- #

def read_image_from_base64_optimized(image_b64: str, target_size=(640, 480)):
    """Convert base64 image to RGB numpy array with optimization"""
    if image_b64.startswith("data:"):
        image_b64 = image_b64.split(",", 1)[1]
    
    image_bytes = base64.b64decode(image_b64)
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
    # Resize large images to reduce processing time
    if img.width > target_size[0] or img.height > target_size[1]:
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
    
    return np.array(img)

def detect_faces_optimized(rgb_image, detector):
    """Detect faces using preloaded MTCNN detector"""
    # Skip detection if image is too small
    if rgb_image.shape[0] < 50 or rgb_image.shape[1] < 50:
        return []
    
    detections = detector.detect_faces(rgb_image)
    faces = []
    
    for d in detections:
        if d["confidence"] > 0.85:  # Slightly lower threshold for better detection
            x, y, w, h = d["box"]
            x, y = max(0, x), max(0, y)
            if w > 40 and h > 40:  # Lower minimum size for better detection
                face_rgb = rgb_image[y:y+h, x:x+w]
                faces.append({
                    "box": (x, y, w, h), 
                    "face": face_rgb, 
                    "confidence": d["confidence"]
                })
    
    return faces

def extract_embedding_optimized(face_rgb):
    """Extract embedding using preloaded DeepFace model"""
    try:
        if face_rgb.shape[0] < 40 or face_rgb.shape[1] < 40:
            return None
            
        # Resize face to standard size
        face_pil = Image.fromarray(face_rgb.astype("uint8")).resize((160, 160))
        face_array = np.array(face_pil)
        
        # Use DeepFace with optimized parameters
        rep = DeepFace.represent(
            face_array, 
            model_name="Facenet512", 
            detector_backend="skip",
            enforce_detection=False  # Skip additional detection for speed
        )
        return np.array(rep[0]["embedding"], dtype=np.float32)  # Use float32 for speed
        
    except Exception as e:
        logger.error(f"Embedding extraction error: {e}")
        return None

def get_attendance_collection():
    """Get the attendance collection from app config"""
    db = current_app.config.get("DB")
    return db.collection("attendance_sessions")

# Enhanced embedding cache for attendance sessions
class AttendanceEmbeddingCache:
    def __init__(self):
        self.cached_embeddings = {}
        self.last_update = {}
        self.cache_duration = 5  # 5 seconds for testing purposes
    
    def get_session_embeddings(self, students_col, session_filter):
        """Get cached embeddings for specific session filters"""
        cache_key = str(sorted(session_filter.items()))
        current_time = time.time()
        
        if (cache_key not in self.cached_embeddings or 
            current_time - self.last_update.get(cache_key, 0) > self.cache_duration):
            
            logger.info(f"Refreshing attendance embedding cache for {session_filter}")
            
            # Fetch students matching the session filter
            # Filter manually to support Firestore
            all_students_docs = students_col.stream() if hasattr(students_col, 'stream') else students_col.get()
            students = []
            for sdoc in all_students_docs:
                s_dict = sdoc.to_dict()
                match = True
                for k, v in session_filter.items():
                    if k == "embeddings" and isinstance(v, dict):
                        # Simple check for embeddings exists
                        if not s_dict.get("embeddings") and not s_dict.get("embedding"):
                            match = False
                            break
                    elif s_dict.get(k) != v:
                        match = False
                        break
                if match:
                    students.append(s_dict)
            
            # Process embeddings - handle both old and new embedding formats
            session_embeddings = []
            for student in students:
                # Handle multiple embedding formats
                embeddings_raw = student.get('embeddings') or student.get('embedding')
                # Handle JSON string format (Firestore doesn't allow nested arrays)
                if isinstance(embeddings_raw, str):
                    embeddings = json.loads(embeddings_raw)
                else:
                    embeddings = embeddings_raw
                if embeddings:
                    if isinstance(embeddings, list) and len(embeddings) > 0:
                        # Multiple embeddings - average them
                        if isinstance(embeddings[0], list):
                            avg_embedding = np.mean(embeddings, axis=0).astype(np.float32)
                        else:
                            avg_embedding = np.array(embeddings, dtype=np.float32)
                    else:
                        # Single embedding
                        avg_embedding = np.array(embeddings, dtype=np.float32)
                    
                    session_embeddings.append({
                        'embedding': avg_embedding,
                        'studentId': student.get('studentId'),
                        'studentName': student.get('studentName'),
                        'department': student.get('department'),
                        'year': student.get('year'),
                        'division': student.get('division')
                    })
            
            self.cached_embeddings[cache_key] = session_embeddings
            self.last_update[cache_key] = current_time
            logger.info(f"Cached {len(session_embeddings)} student embeddings for session")
        
        return self.cached_embeddings[cache_key]

# Global cache instance for attendance
attendance_cache = AttendanceEmbeddingCache()

def find_best_match_optimized_attendance(query_embedding, students_col, session_doc, threshold=0.6):
    """Optimized student matching for attendance with session-specific filtering"""
    # Build filter for students in this session's class
    student_filter = {"embeddings": {"$exists": True, "$ne": None}}
    
    # Add session-specific filters
    if session_doc.get("department"):
        student_filter["department"] = session_doc.get("department")
    if session_doc.get("year"):
        student_filter["year"] = session_doc.get("year")
    if session_doc.get("division"):
        student_filter["division"] = session_doc.get("division")
    
    # Get cached embeddings for this session
    cached_embeddings = attendance_cache.get_session_embeddings(students_col, student_filter)
    
    if not cached_embeddings:
        return None, float('inf')
    
    best_match = None
    min_distance = float('inf')
    
    # Vectorized comparison for speed
    for student_data in cached_embeddings:
        stored_embedding = student_data['embedding']
        distance = cosine(query_embedding, stored_embedding)
        
        if distance < min_distance:
            min_distance = distance
            best_match = student_data
    
    return best_match if min_distance < threshold else None, min_distance

# ----------------- OPTIMIZED Routes ----------------- #

@attendance_session_bp.route("/create_session", methods=["POST"])
def create_session():
    """Create a new attendance session"""
    data = request.json
    db = current_app.config.get("DB")
    students_col = db.students

    # Build base session document
    session_doc = {
        "date": data.get("date"),
        "subject": data.get("subject"),
        "department": data.get("department"),
        "year": data.get("year"),
        "division": data.get("division"),
        "duration": data.get("duration", "60"),
        "teacher_name": data.get("teacher_name", ""),
        "teacher_id": data.get("teacher_id", ""),
        "created_at": datetime.now(),
        "finalized": False,
        "ended_at": None,
        "students": []
    }

    # Prepopulate session with all students in that class
    student_filter = {}
    if data.get("department"): student_filter["department"] = data.get("department")
    if data.get("year"): student_filter["year"] = data.get("year")
    if data.get("division"): student_filter["division"] = data.get("division")

    try:
        # Manually filter for Firestore since find() is MongoDB-specific
        all_students_docs = students_col.stream() if hasattr(students_col, 'stream') else students_col.get()
        students = []
        for sdoc in all_students_docs:
            s_dict = sdoc.to_dict()
            match = True
            for k, v in student_filter.items():
                if s_dict.get(k) != v:
                    match = False
                    break
            if match:
                students.append(s_dict)
                
        for s in students:
            sid = s.get("studentId") or s.get("student_id")
            name = s.get("studentName") or s.get("student_name")
            session_doc["students"].append({
                "student_id": sid,
                "student_name": name,
                "present": False,
                "marked_at": None
            })
        
        logger.info(f"Created session with {len(students)} students preloaded")
        
    except Exception as e:
        logger.error(f"Error preloading students: {e}")
        # Continue with empty students list

    collection = get_attendance_collection()
    time_, doc_ref = collection.add(session_doc)
    session_id = doc_ref.id
    return jsonify({"session_id": session_id, "students_count": len(session_doc["students"])})

@attendance_session_bp.route("/end_session", methods=["POST"])
def end_session():
    """Finalize an attendance session with enhanced logging"""
    data = request.get_json()
    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400

    try:
        collection = get_attendance_collection()
        db = current_app.config.get("DB")
        students_col = db.students

        doc_ref = collection.document(session_id)
        doc = doc_ref.get()
        if not doc.exists:
            return jsonify({"error": "Session not found"}), 404
            
        session_doc = doc.to_dict()

        # Build map of existing student tracking
        session_students = session_doc.get("students", [])
        student_tracker = { s.get("student_id"): s for s in session_students }
        
        present_students = set(
            s.get("student_id") for s in session_students if s.get("present")
        )

        # Get all students in that class
        student_filter = {}
        if session_doc.get("department"): student_filter["department"] = session_doc.get("department")
        if session_doc.get("year"): student_filter["year"] = session_doc.get("year")
        if session_doc.get("division"): student_filter["division"] = session_doc.get("division")

        all_students = list(students_col.where(**{k: '==' for k in student_filter.keys()}).get()) if False else []
        # Wait, the students_col is FirestoreDB wrapper, so we can't use list(find(...)) easily.
        # Actually in firebase_config.py Query is usually done via chained wheres.
        # Let's just fetch all students first and filter in Python to be safe.
        
        all_students_docs = students_col.stream() if hasattr(students_col, 'stream') else students_col.get()
        all_students = []
        for sdoc in all_students_docs:
            s_dict = sdoc.to_dict()
            match = True
            for k, v in student_filter.items():
                if s_dict.get(k) != v:
                    match = False
                    break
            if match:
                all_students.append(s_dict)
        
        # Mark absent students
        absent_count = 0
        for s in all_students:
            sid = s.get("studentId") or s.get("student_id")
            sname = s.get("studentName") or s.get("student_name")
            
            if sid not in present_students:
                if sid in student_tracker:
                    student_tracker[sid]["present"] = False
                    student_tracker[sid]["marked_at"] = None
                else:
                    student_tracker[sid] = {
                        "student_id": sid, 
                        "student_name": sname, 
                        "present": False, 
                        "marked_at": None
                    }
                absent_count += 1

        # Mark session as finalized
        updated_students_list = list(student_tracker.values())
        doc_ref.update({
            "students": updated_students_list,
            "finalized": True,
            "ended_at": datetime.now()
        })

        logger.info(f"Session finalized: {len(present_students)} present, {absent_count} absent")

        return jsonify({
            "success": True,
            "statistics": {
                "present_count": len(present_students),
                "absent_count": absent_count,
                "total_students": len(all_students)
            }
        })

    except Exception as e:
        logger.error(f"Error ending session: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@attendance_session_bp.route("/real-mark", methods=["POST"])
def mark_attendance_with_duplicate_prevention():
    """Attendance marking with enhanced duplicate prevention"""
    start_time = time.time()
    
    # Check if models are ready
    model_manager = current_app.config.get("MODEL_MANAGER")
    if not model_manager or not model_manager.is_ready():
        return jsonify({"error": "Face recognition models not initialized"}), 503
    
    detector = model_manager.get_detector()
    
    data = request.get_json()
    session_id = data.get("session_id")
    image_b64 = data.get("image")

    if not session_id or not image_b64:
        return jsonify({"error": "Missing session_id or image"}), 400

    try:
        # Use same image processing as demo
        rgb = read_image_from_base64_optimized(image_b64)
        faces = detect_faces_optimized(rgb, detector)

        if len(faces) == 0:
            return jsonify({"message": "No faces detected", "faces": []})

        # Validate session
        collection = get_attendance_collection()
        doc_ref = collection.document(session_id)
        doc = doc_ref.get()
        if not doc.exists:
            return jsonify({"error": "Session not found"}), 404
            
        session_doc = doc.to_dict()
        if session_doc.get("finalized"):
            return jsonify({"error": "Session already finalized"}), 400

        # GET LIST OF ALREADY MARKED STUDENTS IN THIS SESSION
        session_students = session_doc.get("students", [])
        student_tracker = { s.get("student_id"): s for s in session_students }
        already_present_students = set(
            s.get("student_id") for s in session_students if s.get("present") == True
        )
        
        logger.info(f"Session {session_id} already has {len(already_present_students)} students marked present")

        # Recognition logic (same as demo session)
        db = current_app.config.get("DB")
        students_col = db.students
        threshold = float(current_app.config.get("THRESHOLD", 0.6))
        
        # Search ALL students (same as demo session)
        # Handle Firestore stream vs get
        all_students_docs = students_col.stream() if hasattr(students_col, 'stream') else students_col.get()
        students = []
        for sdoc in all_students_docs:
            s_dict = sdoc.to_dict()
            if "embeddings" in s_dict and s_dict["embeddings"] is not None:
                students.append(s_dict)

        results = []
        modified_attendance = False

        for f in faces:
            emb = extract_embedding_optimized(f["face"])
            if emb is None:
                results.append({
                    "match": None, 
                    "distance": None, 
                    "box": f["box"],
                    "error": "Failed to extract embedding"
                })
                continue

            # EXACT SAME MATCHING LOGIC AS DEMO SESSION
            best, min_d = None, float("inf")
            for student in students:
                stored_embeddings_raw = student.get("embeddings", [])
                # Handle JSON string format
                if isinstance(stored_embeddings_raw, str):
                    stored_embeddings = json.loads(stored_embeddings_raw)
                else:
                    stored_embeddings = stored_embeddings_raw
                if not stored_embeddings:
                    continue
                
                # Average multiple embeddings
                if isinstance(stored_embeddings, list) and len(stored_embeddings) > 0:
                    avg_embedding = np.mean(stored_embeddings, axis=0)
                else:
                    avg_embedding = np.array(stored_embeddings)
                
                d = cosine(emb, avg_embedding)
                if d < min_d:
                    min_d = d
                    best = student

            if min_d < threshold and best:
                student_id = best.get("studentId")
                student_name = best.get("studentName")

                # CHECK FOR DUPLICATE BEFORE MARKING
                if student_id in already_present_students:
                    # Student already marked present in this session
                    results.append({
                        "match": {"user_id": student_id, "name": student_name},
                        "distance": round(float(min_d), 4),
                        "confidence": round((1 - min_d) * 100, 1),
                        "box": f["box"],
                        "already_marked": True,
                        "status": "duplicate",
                        "message": f"{student_name} is already marked present in this session"
                    })
                    logger.info(f"Duplicate detection: {student_name} ({student_id}) already present")
                    continue

                # MARK ATTENDANCE (Student not yet marked)
                if student_id in student_tracker:
                    student_tracker[student_id]["present"] = True
                    student_tracker[student_id]["marked_at"] = datetime.now()
                else:
                    student_tracker[student_id] = {
                        "student_id": student_id,
                        "student_name": student_name,
                        "present": True,
                        "marked_at": datetime.now()
                    }
                modified_attendance = True

                already_present_students.add(student_id)
                results.append({
                    "match": {"user_id": student_id, "name": student_name},
                    "distance": round(float(min_d), 4),
                    "confidence": round((1 - min_d) * 100, 1),
                    "box": f["box"],
                    "already_marked": False,
                    "status": "marked_present",
                    "message": f"{student_name} marked present successfully"
                })
                logger.info(f"✅ Marked {student_name} ({student_id}) as present")

            else:
                # No match found
                results.append({
                    "match": None, 
                    "distance": round(float(min_d), 4) if min_d != float('inf') else None,
                    "confidence": round((1 - min_d) * 100, 1) if min_d != float('inf') else None,
                    "box": f["box"],
                    "status": "no_match",
                    "message": "Face not recognized"
                })
                
        if modified_attendance:
            updated_students_list = list(student_tracker.values())
            doc_ref.update({"students": updated_students_list})

        processing_time = time.time() - start_time
        
        # Return comprehensive response
        return jsonify({
            "message": "Recognition processed", 
            "faces": results, 
            "processing_time": round(processing_time, 3),
            "session_info": {
                "session_id": session_id,
                "total_present_now": len(already_present_students),
                "faces_detected": len(faces),
                "duplicates_prevented": sum(1 for r in results if r.get("status") == "duplicate")
            }
        })

    except Exception as e:
        logger.error(f"Attendance error: {e}")
        return jsonify({"error": str(e)}), 500

# Health check for attendance models
@attendance_session_bp.route("/models/status", methods=["GET"])
def attendance_model_status():
    """Check model status for attendance system"""
    model_manager = current_app.config.get("MODEL_MANAGER")
    
    if not model_manager:
        return jsonify({
            "success": False,
            "error": "Model manager not available"
        }), 500
    
    return jsonify({
        "success": True,
        "models_ready": model_manager.is_ready(),
        "health_check": model_manager.health_check(),
        "cache_info": {
            "embedding_cache_active": True,
            "cache_duration": "10 minutes"
        },
        "timestamp": time.time()
    })
