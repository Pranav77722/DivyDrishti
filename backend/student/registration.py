from flask import Blueprint, request, jsonify, current_app
import time
import json
import base64
import numpy as np
from PIL import Image
import io
from deepface import DeepFace
import logging

student_registration_bp = Blueprint("student_registration", __name__)
logger = logging.getLogger(__name__)


def read_image_from_bytes(b):
    img = Image.open(io.BytesIO(b)).convert('RGB')
    return np.array(img)


def detect_faces_rgb(rgb_image):
    """Detect faces using the app's shared MTCNN detector."""
    from flask import current_app
    detector = current_app.config.get("MTCNN_DETECTOR")
    if detector is None:
        raise RuntimeError("MTCNN detector not available")

    detections = detector.detect_faces(rgb_image)
    faces = []
    for d in detections:
        if d['confidence'] > 0.9:
            x, y, w, h = d['box']
            x, y = max(0, x), max(0, y)
            if w > 50 and h > 50:
                face_rgb = rgb_image[y:y+h, x:x+w]
                faces.append({'box': (x, y, w, h), 'face': face_rgb, 'confidence': d['confidence']})
    return faces


def extract_embedding(face_rgb):
    try:
        face_pil = Image.fromarray(face_rgb.astype('uint8')).resize((160, 160))
        face_array = np.array(face_pil)
        rep = DeepFace.represent(face_array, model_name='Facenet512', detector_backend='skip')
        return np.array(rep[0]['embedding'], dtype=float)
    except Exception as e:
        print(f"Embedding error: {e}")
        return None


@student_registration_bp.route('/api/register-student', methods=['POST'])
def register_student():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON data"}), 400

        db = current_app.config.get("DB")
        students_col = db.students

        # Check required fields
        required_fields = ['studentName', 'studentId', 'department', 'year', 'division', 'semester', 'email', 'phoneNumber', 'images']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"success": False, "error": f"{field} is required"}), 400

        # Check uniqueness of studentId
        logger.info(f"Checking if student ID {data['studentId']} exists...")
        existing_by_id = list(students_col.where('studentId', '==', data['studentId']).limit(1).get())
        if existing_by_id:
            return jsonify({"success": False, "error": "Student ID already exists"}), 400

        # Check uniqueness of email
        logger.info(f"Checking if email {data['email']} exists...")
        existing_by_email = list(students_col.where('email', '==', data['email']).limit(1).get())
        if existing_by_email:
            return jsonify({"success": False, "error": "Email already registered"}), 400

        # Validate images
        images = data.get('images')
        if not isinstance(images, list) or len(images) != 5:
            return jsonify({"success": False, "error": "Exactly 5 images are required"}), 400

        logger.info(f"Processing {len(images)} images for face detection...")
        embeddings = []
        for idx, img_b64 in enumerate(images):
            try:
                if img_b64.startswith("data:"):
                    img_b64 = img_b64.split(",", 1)[1]
                rgb = read_image_from_bytes(base64.b64decode(img_b64))
                logger.info(f"Image {idx+1}: decoded successfully, shape={rgb.shape}")
            except Exception as e:
                logger.error(f"Image {idx} decode error: {e}")
                return jsonify({"success": False, "error": f"Invalid image data at index {idx}"}), 400

            faces = detect_faces_rgb(rgb)
            logger.info(f"Image {idx+1}: detected {len(faces)} face(s)")
            if len(faces) != 1:
                return jsonify({"success": False, "error": f"Ensure exactly one face in each image (failed at image {idx+1})"}), 400

            emb = extract_embedding(faces[0]['face'])
            if emb is None:
                return jsonify({"success": False, "error": f"Failed to extract face features for image {idx+1}"}), 500
            embeddings.append(emb.tolist())
            logger.info(f"Image {idx+1}: embedding extracted (dim={len(emb)})")

        student_data = {
            "studentId": data['studentId'],
            "studentName": data['studentName'],
            "department": data['department'],
            "year": data['year'],
            "division": data['division'],
            "semester": data['semester'],
            "email": data['email'],
            "phoneNumber": data['phoneNumber'],
            "status": "active",
            "embeddings": json.dumps(embeddings),
            "face_registered": True,
            "created_at": time.time(),
            "updated_at": time.time()
        }

        # Add document to Firestore
        logger.info("Writing student data to Firestore...")
        try:
            _, doc_ref = students_col.add(student_data)
            logger.info(f"✅ Student registered: {data['studentId']}, doc_id={doc_ref.id}")
            return jsonify({"success": True, "studentId": data['studentId'], "record_id": doc_ref.id})
        except Exception as db_err:
            logger.error(f"❌ Firestore write failed: {type(db_err).__name__}: {db_err}")
            return jsonify({"success": False, "error": f"Database error: {str(db_err)}"}), 500

    except Exception as e:
        logger.error(f"❌ Registration error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500


@student_registration_bp.route('/api/students/count', methods=['GET'])
def get_student_count():
    db = current_app.config.get("DB")
    # Count documents by getting all document IDs (lightweight)
    docs = db.students.select([]).get()
    count = len(list(docs))
    return jsonify({"success": True, "count": count})


@student_registration_bp.route('/api/students/departments', methods=['GET'])
def get_departments():
    db = current_app.config.get("DB")
    # Get distinct departments - Firestore doesn't have distinct(), so we fetch all and dedupe
    docs = db.students.select(['department']).get()
    departments = list(set(doc.to_dict().get('department', '') for doc in docs if doc.to_dict().get('department')))
    return jsonify({"success": True, "departments": departments, "count": len(departments)})
