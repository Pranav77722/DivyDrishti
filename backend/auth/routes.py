from flask import Blueprint, request, jsonify, current_app
from flask_bcrypt import Bcrypt
from firebase_config import doc_to_dict, query_results_to_list
import time

auth_bp = Blueprint("auth", __name__)
bcrypt = Bcrypt()

@auth_bp.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    user_type = data.get('userType', 'student')  # Default to student

    if not all([username, email, password]):
        return jsonify({"success": False, "error": "All fields required"}), 400

    db = current_app.config.get("DB")
    
    # Choose collection based on user type
    if user_type == 'teacher':
        auth_col = db.auth_teachers
        # Add additional teacher-specific fields
        employee_id = data.get('employeeId')
        department = data.get('department')
        
        if not employee_id:
            return jsonify({"success": False, "error": "Employee ID required for teachers"}), 400
    else:
        auth_col = db.auth_users
    
    # Check if email already exists in the appropriate collection
    existing_docs = auth_col.where('email', '==', email).limit(1).get()
    if len(list(existing_docs)) > 0:
        return jsonify({
            "success": False, 
            "error": f"Email already registered as {user_type}"
        }), 400

    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')

    # Prepare user document
    user_doc = {
        "username": username,
        "email": email,
        "password": hashed_pw,
        "userType": user_type,
        "status": "active",
        "created_at": time.time()
    }
    
    # Add type-specific fields
    if user_type == 'teacher':
        user_doc.update({
            "employeeId": employee_id,
            "department": department,
            "role": "teacher"
        })
    
    auth_col.add(user_doc)

    return jsonify({
        "success": True, 
        "message": f"{user_type.capitalize()} registered successfully"
    })

@auth_bp.route('/api/signin', methods=['POST'])
def api_signin():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    user_type = data.get('userType', 'student')  # Default to student

    if not all([email, password]):
        return jsonify({"success": False, "error": "Email and password required"}), 400

    db = current_app.config.get("DB")
    
    # Choose collection based on user type
    if user_type == 'teacher':
        auth_col = db.auth_teachers
        user_role = "teacher"
    else:
        auth_col = db.auth_users
        user_role = "student"
    
    # Find user in appropriate collection
    user_docs = list(auth_col.where('email', '==', email).limit(1).get())
    
    if not user_docs:
        return jsonify({
            "success": False, 
            "error": f"No {user_type} account found with this email"
        }), 401
    
    user_doc = user_docs[0]
    user = user_doc.to_dict()
    user['_id'] = user_doc.id
    
    # Check password
    if not bcrypt.check_password_hash(user['password'], password):
        return jsonify({
            "success": False, 
            "error": "Invalid password"
        }), 401
    
    # Check if account is active
    if user.get('status') == 'inactive':
        return jsonify({
            "success": False, 
            "error": "Account is deactivated. Contact administrator."
        }), 401

    # Prepare response based on user type
    user_info = {
        "_id": user['_id'],
        "username": user['username'],
        "email": user['email'],
        "userType": user_type,
        "role": user_role
    }
    
    # Add type-specific information
    if user_type == 'teacher':
        user_info.update({
            "employeeId": user.get('employeeId'),
            "department": user.get('department'),
            "name": user['username']  # Use username as display name for teachers
        })
        
        # Check if teacher has student record too (optional)
        student_docs = list(db.students.where('email', '==', email).limit(1).get())
        if student_docs:
            student_record = student_docs[0].to_dict()
            user_info['hasStudentRecord'] = True
            user_info['studentId'] = student_record.get('studentId')
    else:
        # For students, try to get student record
        student_docs = list(db.students.where('email', '==', email).limit(1).get())
        if student_docs:
            student_record = student_docs[0].to_dict()
            user_info.update({
                "studentId": student_record.get('studentId'),
                "studentName": student_record.get('studentName'),
                "department": student_record.get('department'),
                "hasStudentRecord": True
            })

    return jsonify({
        "success": True, 
        "message": f"Signed in successfully as {user_type}",
        "user": user_info,
        "userType": user_type
    })

@auth_bp.route('/api/logout', methods=['POST'])
def api_logout():
    # You can add logout logic here if needed (e.g., invalidate tokens)
    return jsonify({"success": True, "message": "Logged out successfully"})

# Additional route to check user type and permissions
@auth_bp.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    """Get current user's profile information"""
    user_email = request.headers.get('X-User-Email')
    user_type = request.headers.get('X-User-Type', 'student')
    
    if not user_email:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    
    db = current_app.config.get("DB")
    
    # Get user from appropriate collection
    if user_type == 'teacher':
        auth_col = db.auth_teachers
    else:
        auth_col = db.auth_users
    
    user_docs = list(auth_col.where('email', '==', user_email).limit(1).get())
    
    if not user_docs:
        return jsonify({"success": False, "error": "User not found"}), 404
    
    user_doc = user_docs[0]
    user = user_doc.to_dict()
    user['_id'] = user_doc.id
    # Exclude password from response
    user.pop('password', None)
    
    return jsonify({
        "success": True,
        "user": user
    })

# Route to switch user type (if user has both teacher and student accounts)
@auth_bp.route('/api/switch-role', methods=['POST'])
def switch_user_role():
    """Allow users to switch between teacher and student roles if they have both"""
    data = request.get_json()
    user_email = data.get('email')
    target_type = data.get('targetType')  # 'teacher' or 'student'
    
    if not all([user_email, target_type]):
        return jsonify({"success": False, "error": "Email and target type required"}), 400
    
    db = current_app.config.get("DB")
    
    # Check if user exists in target collection
    if target_type == 'teacher':
        target_col = db.auth_teachers
    else:
        target_col = db.auth_users
    
    target_docs = list(target_col.where('email', '==', user_email).limit(1).get())
    
    if not target_docs:
        return jsonify({
            "success": False, 
            "error": f"No {target_type} account found for this email"
        }), 404
    
    target_doc = target_docs[0]
    target_user = target_doc.to_dict()
    target_user['_id'] = target_doc.id
    
    # Return user info for the target role
    user_info = {
        "_id": target_user['_id'],
        "username": target_user['username'],
        "email": target_user['email'],
        "userType": target_type
    }
    
    if target_type == 'teacher':
        user_info.update({
            "employeeId": target_user.get('employeeId'),
            "department": target_user.get('department')
        })
    
    return jsonify({
        "success": True,
        "message": f"Switched to {target_type} role",
        "user": user_info,
        "userType": target_type
    })
