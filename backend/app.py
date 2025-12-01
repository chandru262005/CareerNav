from flask import Flask, request, jsonify
import os
import time
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file FIRST
load_dotenv()

from utils.resume_extractor import extract_resume_text, clean_extracted_text, extract_basic_info
from utils.gemini_service import GeminiService
from config import get_config, check_config

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load configuration
config = get_config()
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

UPLOAD_FOLDER = config.UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Check configuration on startup
print("Checking configuration...")
config_valid = check_config()

# Check Gemini API Key
gemini_key_present = bool(os.getenv('GEMINI_API_KEY'))
print(f"GEMINI_API_KEY present in environment: {gemini_key_present}")
if not gemini_key_present:
    print("WARNING: GEMINI_API_KEY not found. AI features will be disabled.")
    print("Please set GEMINI_API_KEY environment variable to enable AI recommendations.")

# Initialize Gemini service
try:
    if config_valid and gemini_key_present:
        gemini_service = GeminiService()
        print("Gemini AI service initialized successfully")
    else:
        print("Configuration issues detected. AI features may not work properly.")
        gemini_service = None
except Exception as e:
    print(f"Warning: Gemini AI service failed to initialize: {str(e)}")
    print("AI-powered features will be disabled")
    gemini_service = None

@app.route('/', methods=['GET'])
def st():
    return "Hii"

@app.route('/process', methods=['POST'])
def process_resume():
    file = request.files.get('resume')
    industries = request.form.get('industries')
    goals = request.form.get('goals')
    location = request.form.get('location')

    if not file:
        return jsonify({'error': 'No resume uploaded'}), 400

    # Save file temporarily
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    try:
        # Extract text from resume
        extracted_text = extract_resume_text(file_path)
        
        if not extracted_text:
            return jsonify({'error': 'Could not extract text from resume'}), 400
        
        # Clean the extracted text
        clean_text = clean_extracted_text(extracted_text)
        
        # Extract basic information
        basic_info = extract_basic_info(clean_text, extracted_text)
        
        print("Industries:", industries)
        print("Goals:", goals)
        print("Location:", location)
        print("Extracted resume length:", len(clean_text))
        print("Skills found:", len(basic_info.get('skills', [])))
        print("Skills by category:", basic_info.get('skills_summary', {}))

        # Prepare preferences for AI analysis
        preferences = {
            "industries": industries or "Not specified",
            "goals": goals or "Not specified", 
            "location": location or "Not specified"
        }

        # Generate AI-powered recommendations if service is available
        ai_recommendations = {}
        if gemini_service:
            try:
                # Generate career recommendations
                career_recs = gemini_service.generate_career_recommendations(
                    skills_by_category=basic_info.get('skills_summary', {}),
                    preferences=preferences,
                    experience_level="intermediate"  # Could be determined from resume analysis
                )
                ai_recommendations['career_recommendations'] = career_recs

                # Generate skill improvement suggestions
                skill_suggestions = gemini_service.suggest_skill_improvements(
                    current_skills=basic_info.get('skills', []),
                   target_roles=[role.get('title', '') for role in career_recs.get('recommended_roles', [])[:3]] if career_recs else ['Software Developer'],
                    preferences=preferences
                )
                ai_recommendations['skill_improvements'] = skill_suggestions

                # Analyze resume for gaps
                resume_analysis = gemini_service.analyze_resume_gaps(
                    skills_by_category=basic_info.get('skills_summary', {}),
                    preferences=preferences,
                    extracted_text=clean_text
                )
                ai_recommendations['resume_analysis'] = resume_analysis

                # Generate learning path for top recommended role
                top_role = career_recs.get('recommended_roles', [{}])[0].get('title', 'Software Developer') if career_recs else 'Software Developer'
                learning_path = gemini_service.generate_learning_path(
                    current_skills=basic_info.get('skills', []),
                    target_role=top_role,
                    learning_preference="balanced"
                )
                ai_recommendations['learning_path'] = learning_path

                print("AI recommendations generated successfully")
            except Exception as e:
                print(f"Error generating AI recommendations: {str(e)}")
                ai_recommendations['error'] = str(e)

        # Enhanced response with extracted information
        response = {
            "summary": "Resume processed successfully with AI analysis",
            "extracted_info": {
                "text_length": len(clean_text),
                "email": basic_info.get('email'),
                "detected_skills": basic_info.get('skills', []),
                "skills_by_category": basic_info.get('skills_summary', {}),
                "total_skills_found": len(basic_info.get('skills', [])),
                "has_experience_keywords": len(basic_info.get('experience_keywords', [])) > 0,
                "has_education_keywords": len(basic_info.get('education_keywords', [])) > 0,
                "experience_entries": basic_info.get('experience_entries', []),
                "project_entries": basic_info.get('project_entries', []),
                "experience_keywords": basic_info.get('experience_keywords', [])
            },
            "preferences": {
                "industries": industries,
                "goals": goals,
                "location": location
            },
            "ai_insights": ai_recommendations,
    
        }
        
    except Exception as e:
        print(f"Error processing resume: {str(e)}")
        return jsonify({'error': f'Error processing resume: {str(e)}'}), 500
    
    finally:
        # Clean up - remove the uploaded file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Warning: Could not remove file {file_path}: {str(e)}")

    return jsonify(response)

@app.route('/extract-skills', methods=['POST'])
def extract_skills():
    """
    Endpoint specifically for extracting skills from a resume without generating AI recommendations
    """
    file = request.files.get('resume')
    
    if not file:
        return jsonify({'error': 'No resume file provided'}), 400

    # Create upload directory if it doesn't exist
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
        
    # Save the file temporarily
    filename = f"resume-{int(time.time() * 1000)}.pdf"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    
    try:
        # Extract text from the resume
        extracted_text = extract_resume_text(file_path)
        clean_text = clean_extracted_text(extracted_text)
        
        # Extract basic information
        basic_info = extract_basic_info(clean_text, extracted_text)
        
        # Create a response with just the extracted skills
        response = {
            'skills': basic_info.get('skills', []),
            'skills_by_category': basic_info.get('skills_summary', {}),
            'total_skills_found': len(basic_info.get('skills', [])),
            'extracted_info': {
                'email': basic_info.get('email', ''),
                'detected_skills': basic_info.get('skills', []),
            }
        }
        
    except Exception as e:
        print(f"Error extracting skills: {str(e)}")
        return jsonify({'error': f'Error extracting skills: {str(e)}'}), 500
    
    finally:
        # Clean up - remove the uploaded file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Warning: Could not remove file {file_path}: {str(e)}")

    return jsonify(response)

@app.route('/extract-resume', methods=['POST'])
def extract_resume():
    """
    Endpoint specifically for extracting text content from resume
    """
    file = request.files.get('resume')
    
    if not file:
        return jsonify({'error': 'No resume uploaded'}), 400
    
    # Check file extension
    allowed_extensions = ['.pdf', '.docx', '.doc']
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        return jsonify({'error': f'Unsupported file format. Allowed: {", ".join(allowed_extensions)}'}), 400
    
    # Save file temporarily
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    
    try:
        # Extract text from resume
        extracted_text = extract_resume_text(file_path)
        
        if not extracted_text:
            return jsonify({'error': 'Could not extract text from resume. The file might be corrupted or contain only images.'}), 400
        
        # Clean the extracted text
        clean_text = clean_extracted_text(extracted_text)

        # Extract basic information
        basic_info = extract_basic_info(clean_text, extracted_text)
        
        response = {
            "success": True,
            "file_info": {
                "filename": file.filename,
                "file_type": file_extension,
                "text_length": len(clean_text)
            },
            "extracted_content": {
                "full_text": clean_text,
                "basic_info": {
                    "email": basic_info.get('email'),
                    "skills": basic_info.get('skills', []),
                    "skills_by_category": basic_info.get('skills_summary', {}),
                    "experience_keywords": basic_info.get('experience_keywords', []),
                    "education_keywords": basic_info.get('education_keywords', [])
                }
            },
            "analysis": {
                "has_contact_info": bool(basic_info.get('email')),
                "skills_detected": len(basic_info.get('skills', [])),
                "appears_complete": len(clean_text) > 200,
                "top_skill_categories": list(basic_info.get('skills_summary', {}).keys())[:3],
                "has_technical_background": len(basic_info.get('skills', [])) > 5
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error extracting resume: {str(e)}")
        return jsonify({'error': f'Error extracting resume: {str(e)}'}), 500
    
    finally:
        # Clean up - remove the uploaded file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Warning: Could not remove file {file_path}: {str(e)}")

@app.route('/ai/career-recommendations', methods=['POST'])
def get_career_recommendations():
    """
    Endpoint for getting AI-powered career recommendations
    """
    if not gemini_service:
        return jsonify({'error': 'AI service not available'}), 503
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    skills_by_category = data.get('skills_by_category', {})
    preferences = data.get('preferences', {})
    experience_level = data.get('experience_level', 'intermediate')
    
    try:
        print(f"Received request - Skills: {skills_by_category}, Preferences: {preferences}")
        
        recommendations = gemini_service.generate_career_recommendations(
            skills_by_category=skills_by_category,
            preferences=preferences,
            experience_level=experience_level
        )
        
        print(f"Generated recommendations successfully")
        
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
        
    except Exception as e:
        print(f"ERROR in career recommendations: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error generating recommendations: {str(e)}'}), 500

@app.route('/ai/skill-analysis', methods=['POST'])
def analyze_skills():
    """
    Endpoint for AI-powered skill gap analysis and improvement suggestions
    """
    if not gemini_service:
        return jsonify({'error': 'AI service not available'}), 503
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    current_skills = data.get('current_skills', [])
    target_roles = data.get('target_roles', [])
    preferences = data.get('preferences', {})
    
    try:
        skill_analysis = gemini_service.suggest_skill_improvements(
            current_skills=current_skills,
            target_roles=target_roles,
            preferences=preferences
        )
        
        return jsonify({
            'success': True,
            'analysis': skill_analysis
        })
        
    except Exception as e:
        return jsonify({'error': f'Error analyzing skills: {str(e)}'}), 500

@app.route('/ai/resume-analysis', methods=['POST'])
def analyze_resume_ai():
    """
    Endpoint for AI-powered resume analysis
    """
    if not gemini_service:
        return jsonify({'error': 'AI service not available'}), 503
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    skills_by_category = data.get('skills_by_category', {})
    preferences = data.get('preferences', {})
    resume_text = data.get('resume_text', '')
    
    if not resume_text:
        return jsonify({'error': 'Resume text is required'}), 400
    
    try:
        analysis = gemini_service.analyze_resume_gaps(
            skills_by_category=skills_by_category,
            preferences=preferences,
            extracted_text=resume_text
        )
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        return jsonify({'error': f'Error analyzing resume: {str(e)}'}), 500

@app.route('/ai/learning-path', methods=['POST'])
def generate_learning_path():
    """
    Endpoint for generating personalized learning paths
    """
    if not gemini_service:
        return jsonify({'error': 'AI service not available'}), 503
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    current_skills = data.get('current_skills', [])
    target_role = data.get('target_role', '')
    learning_preference = data.get('learning_preference', 'balanced')
    
    if not target_role:
        return jsonify({'error': 'Target role is required'}), 400
    
    try:
        learning_path = gemini_service.generate_learning_path(
            current_skills=current_skills,
            target_role=target_role,
            learning_preference=learning_preference
        )
        
        return jsonify({
            'success': True,
            'learning_path': learning_path
        })
        
    except Exception as e:
        return jsonify({'error': f'Error generating learning path: {str(e)}'}), 500

@app.route('/ai/status', methods=['GET'])
def ai_service_status():
    """
    Check if AI service is available and working
    """
    if not gemini_service:
        return jsonify({
            'available': False,
            'message': 'AI service not initialized'
        })
    
    try:
        # Test with a simple request
        test_response = gemini_service.generate_career_recommendations(
            skills_by_category={'technical': ['python']},
            preferences={'industries': 'technology'},
            experience_level='intermediate'
        )
        
        return jsonify({
            'available': True,
            'message': 'AI service is working',
            'api_configured': bool(os.getenv('GEMINI_API_KEY'))
        })
        
    except Exception as e:
        return jsonify({
            'available': False,
            'message': f'AI service error: {str(e)}',
            'api_configured': bool(os.getenv('GEMINI_API_KEY'))
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
