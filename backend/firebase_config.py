# firebase_config.py - Firebase Admin SDK initialization
import os
import json
import logging
import firebase_admin
from firebase_admin import credentials, firestore

logger = logging.getLogger(__name__)

_db = None


def initialize_firebase():
    """Initialize Firebase Admin SDK with service account credentials."""
    global _db

    if _db is not None:
        return _db

    try:
        # Try service account key file first
        key_path = os.getenv("FIREBASE_KEY_PATH", "serviceAccountKey.json")

        if os.path.exists(key_path):
            cred = credentials.Certificate(key_path)
            logger.info(f"Using Firebase service account key from: {key_path}")
        elif os.getenv("FIREBASE_CREDENTIALS_JSON"):
            # Alternatively, use JSON string from environment variable
            cred_dict = json.loads(os.getenv("FIREBASE_CREDENTIALS_JSON"))
            cred = credentials.Certificate(cred_dict)
            logger.info("Using Firebase credentials from environment variable")
        else:
            raise FileNotFoundError(
                f"Firebase service account key not found at '{key_path}'. "
                "Please download it from Firebase Console -> Project Settings -> "
                "Service Accounts -> Generate New Private Key, and save it as "
                "'backend/serviceAccountKey.json'"
            )

        firebase_admin.initialize_app(cred)
        _db = firestore.client()
        logger.info("✅ Firebase Firestore initialized successfully")
        return _db

    except Exception as e:
        logger.error(f"❌ Firebase initialization failed: {e}")
        raise


def get_db():
    """Get the Firestore client. Initializes Firebase if not already done."""
    global _db
    if _db is None:
        return initialize_firebase()
    return _db


def doc_to_dict(doc):
    """Convert a Firestore DocumentSnapshot to a dict with '_id' field.

    This mimics MongoDB's document format so existing code can keep using doc['_id'].
    """
    if not doc.exists:
        return None
    data = doc.to_dict()
    data['_id'] = doc.id
    return data


def query_results_to_list(query_results):
    """Convert Firestore query results to a list of dicts with '_id' field."""
    results = []
    for doc in query_results:
        data = doc.to_dict()
        data['_id'] = doc.id
        results.append(data)
    return results


class FirestoreDB:
    """Wrapper that provides MongoDB-like collection access syntax.

    Usage:
        db = FirestoreDB(firestore_client)
        db.students  -> returns a CollectionReference for 'students'
        db.collection('students')  -> same as above
    """

    def __init__(self, client):
        self._client = client

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        return self._client.collection(name)

    def collection(self, name):
        return self._client.collection(name)
