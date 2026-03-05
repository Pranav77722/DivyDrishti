# student/demo_session.py - OPTIMIZED VERSION (Firebase Firestore)
import json
from flask import Blueprint, request, jsonify, current_app
import time
import base64
import numpy as np
from PIL import Image
import io
from deepface import DeepFace
from scipy.spatial.distance import cosine
import logging
import threading

logger = logging.getLogger(__name__)

demo_session_bp = Blueprint("demo_session", __name__)


def read_image_from_bytes_optimized(b, target_size=(640, 480)):
    """Optimized image reading with size constraints"""
    img = Image.open(io.BytesIO(b)).convert('RGB')
    if img.size[0] > target_size[0] or img.size[1] > target_size[1]:
        img.thumbnail(target_size, Image.LANCZOS)
    return np.array(img)


def detect_faces_rgb_optimized(rgb_image, detector):
    """Optimized face detection using preloaded MTCNN detector"""
    if detector is None:
        raise RuntimeError("MTCNN detector not available")

    detections = detector.detect_faces(rgb_image)
    faces = []
    for d in detections:
        if d['confidence'] > 0.9:
            x, y, w, h = d['box']
            x, y = max(0, x), max(0, y)
            h_img, w_img = rgb_image.shape[:2]
            x2 = min(x + w, w_img)
            y2 = min(y + h, h_img)
            if (x2 - x) > 50 and (y2 - y) > 50:
                face_rgb = rgb_image[y:y2, x:x2]
                faces.append({
                    'box': (x, y, x2 - x, y2 - y),
                    'face': face_rgb,
                    'confidence': d['confidence']
                })
    return faces


def extract_embedding_optimized(face_rgb):
    """Optimized embedding extraction using preloaded model"""
    try:
        face_pil = Image.fromarray(face_rgb.astype('uint8')).resize((160, 160))
        face_array = np.array(face_pil)
        rep = DeepFace.represent(
            face_array,
            model_name='Facenet512',
            detector_backend='skip',
            enforce_detection=False
        )
        return np.array(rep[0]['embedding'], dtype=float)
    except Exception as e:
        logger.error(f"Embedding extraction error: {e}")
        return None


# In-memory cache for student embeddings (optional optimization)
class EmbeddingCache:
    def __init__(self):
        self.student_embeddings = None
        self.last_update = 0
        self.cache_duration = 5  # 5 seconds for demo purposes
        self.lock = threading.Lock()

    def get_embeddings(self, students_col):
        """Get cached embeddings from Firestore students collection."""
        current_time = time.time()

        with self.lock:
            if self.student_embeddings is not None and (current_time - self.last_update) < self.cache_duration:
                return self.student_embeddings

            logger.info("Refreshing embedding cache from Firestore...")
            # Fetch students with face data from Firestore
            docs = list(students_col.where('face_registered', '==', True).get())

            student_embeddings = []
            for doc in docs:
                data = doc.to_dict()
                embeddings_raw = data.get('embeddings', [])
                # Handle JSON string format (Firestore doesn't allow nested arrays)
                if isinstance(embeddings_raw, str):
                    embeddings = json.loads(embeddings_raw)
                else:
                    embeddings = embeddings_raw
                if embeddings:
                    student_embeddings.append({
                        '_id': doc.id,
                        'studentId': data.get('studentId'),
                        'studentName': data.get('studentName'),
                        'department': data.get('department'),
                        'year': data.get('year'),
                        'division': data.get('division'),
                        'embeddings': embeddings
                    })

            self.student_embeddings = student_embeddings
            self.last_update = current_time
            logger.info(f"Cached {len(student_embeddings)} student embeddings")
            return self.student_embeddings


# Global embedding cache instance
embedding_cache = EmbeddingCache()


def find_best_match_optimized(query_embedding, students_col, threshold=0.6):
    """Optimized database search with caching"""
    student_embeddings = embedding_cache.get_embeddings(students_col)

    best_match = None
    min_distance = float('inf')

    for student in student_embeddings:
        for stored_emb in student.get('embeddings', []):
            distance = cosine(query_embedding, stored_emb)
            if distance < min_distance:
                min_distance = distance
                best_match = student

    if min_distance < threshold:
        return best_match, min_distance
    return None, min_distance


@demo_session_bp.route('/api/demo/recognize', methods=['POST'])
def demo_recognize_optimized():
    """OPTIMIZED face recognition endpoint using preloaded models"""
    start_time = time.time()

    try:
        # Get preloaded detector from app config
        detector = current_app.config.get("MTCNN_DETECTOR")
        if detector is None:
            return jsonify({"success": False, "error": "Face detection model not ready"}), 503

        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({"success": False, "error": "Image data required"}), 400

        image_b64 = data['image']
        if image_b64.startswith("data:"):
            image_b64 = image_b64.split(",", 1)[1]

        # Read and process image
        rgb_image = read_image_from_bytes_optimized(base64.b64decode(image_b64))

        # Detect faces
        faces = detect_faces_rgb_optimized(rgb_image, detector)

        if not faces:
            return jsonify({
                "success": True,
                "recognized": False,
                "message": "No face detected",
                "faces_found": 0,
                "processing_time": round(time.time() - start_time, 3)
            })

        # Process first/best face
        best_face = max(faces, key=lambda f: f['confidence'])
        embedding = extract_embedding_optimized(best_face['face'])

        if embedding is None:
            return jsonify({
                "success": True,
                "recognized": False,
                "message": "Could not extract face features",
                "faces_found": len(faces),
                "processing_time": round(time.time() - start_time, 3)
            })

        # Search for match using Firestore
        db = current_app.config.get("DB")
        students_col = db.students
        threshold = current_app.config.get("THRESHOLD", 0.6)

        match, distance = find_best_match_optimized(embedding, students_col, threshold)

        processing_time = round(time.time() - start_time, 3)

        if match:
            return jsonify({
                "success": True,
                "recognized": True,
                "student": {
                    "studentId": match.get('studentId'),
                    "studentName": match.get('studentName'),
                    "department": match.get('department'),
                    "year": match.get('year'),
                    "division": match.get('division')
                },
                "confidence": round(1 - distance, 4),
                "faces_found": len(faces),
                "processing_time": processing_time
            })
        else:
            return jsonify({
                "success": True,
                "recognized": False,
                "message": "Face not recognized",
                "confidence": round(1 - distance, 4) if distance < float('inf') else 0,
                "faces_found": len(faces),
                "processing_time": processing_time
            })

    except Exception as e:
        logger.error(f"Demo recognition error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@demo_session_bp.route('/api/demo/session', methods=['POST'])
def create_demo_session():
    """Create a new demo session"""
    try:
        db = current_app.config.get("DB")
        demo_col = db.demo_sessions

        data = request.get_json() or {}

        session_doc = {
            "created_at": time.time(),
            "user_email": data.get('email', 'anonymous'),
            "status": "active",
            "recognitions": []
        }

        _, doc_ref = demo_col.add(session_doc)

        return jsonify({
            "success": True,
            "session_id": doc_ref.id
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@demo_session_bp.route('/api/demo/session/<session_id>/log', methods=['POST'])
def log_recognition(session_id):
    """Log recognition result to session"""
    try:
        db = current_app.config.get("DB")
        demo_col = db.demo_sessions

        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Data required"}), 400

        doc_ref = demo_col.document(session_id)
        doc = doc_ref.get()
        if not doc.exists:
            return jsonify({"success": False, "error": "Session not found"}), 404

        # Add recognition log entry using array union
        from google.cloud.firestore_v1 import ArrayUnion
        doc_ref.update({
            "recognitions": ArrayUnion([{
                "timestamp": time.time(),
                "recognized": data.get('recognized', False),
                "student_id": data.get('studentId'),
                "confidence": data.get('confidence', 0)
            }])
        })

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@demo_session_bp.route('/api/demo/model-status', methods=['GET'])
def model_status():
    """Check model status endpoint"""
    try:
        model_manager = current_app.config.get("MODEL_MANAGER")
        if model_manager and model_manager.is_ready():
            return jsonify({
                "success": True,
                "models_ready": True,
                "detector": "MTCNN",
                "recognizer": "Facenet512",
                "database": "firebase_firestore"
            })
        else:
            return jsonify({
                "success": True,
                "models_ready": False,
                "message": "Models are still loading"
            })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500