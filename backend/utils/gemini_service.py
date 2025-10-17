"""
Gemini AI Service for Career Navigation
Handles AI-powered career recommendations and insights
"""

import google.generativeai as genai
import os
import json
import atexit
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Gracefully handle gRPC shutdown
def _cleanup_grpc():
    """Cleanup function to properly shut down gRPC connections"""
    try:
        import grpc
        # Signal graceful shutdown for gRPC
        grpc.aio.shutdown_channel = True
    except:
        pass

atexit.register(_cleanup_grpc)

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=self.api_key)
        # Use gemini-2.0-flash model which is stable and widely available
        # Fallback to gemini-pro-latest if needed
        try:
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            print("Using Gemini 2.0 Flash model")
        except Exception as e:
            print(f"Failed to load gemini-2.0-flash: {e}, falling back to gemini-pro-latest")
            self.model = genai.GenerativeModel('gemini-pro-latest')
            print("Using Gemini Pro Latest model")
    
    def generate_career_recommendations(self, 
                                      skills_by_category: Dict[str, List[str]], 
                                      preferences: Dict[str, str],
                                      experience_level: str = "intermediate") -> Dict[str, Any]:
        """
        Generate comprehensive career recommendations based on skills and preferences
        """
        prompt = self._build_career_recommendation_prompt(
            skills_by_category, preferences, experience_level
        )
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_career_response(response.text)
        except Exception as e:
            print(f"Error generating career recommendations: {str(e)}")
            return self._get_fallback_recommendations()
    
    def suggest_skill_improvements(self, 
                                 current_skills: List[str],
                                 target_roles: List[str],
                                 preferences: Dict[str, str]) -> Dict[str, Any]:
        """
        Suggest skills to improve based on target roles and current skill set
        """
        prompt = self._build_skill_improvement_prompt(
            current_skills, target_roles, preferences
        )
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_skill_response(response.text)
        except Exception as e:
            print(f"Error generating skill suggestions: {str(e)}")
            return self._get_fallback_skills()
    
    def analyze_resume_gaps(self,
                           skills_by_category: Dict[str, List[str]],
                           preferences: Dict[str, str],
                           extracted_text: str) -> Dict[str, Any]:
        """
        Analyze resume for gaps and improvement suggestions
        """
        prompt = self._build_resume_analysis_prompt(
            skills_by_category, preferences, extracted_text
        )
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_analysis_response(response.text)
        except Exception as e:
            print(f"Error analyzing resume: {str(e)}")
            return self._get_fallback_analysis()
    
    def generate_learning_path(self,
                             current_skills: List[str],
                             target_role: str,
                             learning_preference: str = "balanced") -> Dict[str, Any]:
        """
        Generate a personalized learning path for career advancement
        """
        prompt = self._build_learning_path_prompt(
            current_skills, target_role, learning_preference
        )
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_learning_response(response.text)
        except Exception as e:
            print(f"Error generating learning path: {str(e)}")
            return self._get_fallback_learning_path()
    
    def _build_career_recommendation_prompt(self, 
                                          skills_by_category: Dict[str, List[str]], 
                                          preferences: Dict[str, str],
                                          experience_level: str) -> str:
        """Build prompt for career recommendations"""
        skills_text = self._format_skills_for_prompt(skills_by_category)
        
        prompt = f"""
As a career advisor AI, analyze the following information and provide comprehensive career recommendations:

CANDIDATE PROFILE:
Experience Level: {experience_level}
Skills by Category: {skills_text}

PREFERENCES:
- Target Industries: {preferences.get('industries', 'Not specified')}
- Career Goals: {preferences.get('goals', 'Not specified')}
- Preferred Location: {preferences.get('location', 'Not specified')}

Please provide recommendations in the following JSON format:
{{
  "recommended_roles": [
    {{
      "title": "Role Title",
      "match_percentage": 85,
      "required_skills": ["skill1", "skill2"],
      "missing_skills": ["skill3", "skill4"],
      "salary_range": "$70,000 - $90,000",
      "growth_potential": "High",
      "industry": "Technology",
      "reasoning": "Explanation of why this role fits in two lines"
    }}
  ],
  "industry_insights": {{
    "trending_industries": ["Industry1", "Industry2"],
    "growth_sectors": ["Sector1", "Sector2"],
    "recommendations": "Industry-specific advice"
  }},
  "next_steps": [
    "Actionable step 1",
    "Actionable step 2"
  ],
  "confidence_score": 0.85
}}

Focus on roles that match the candidate's current skills while considering their preferences and growth potential.
"""
        return prompt
    
    def _build_skill_improvement_prompt(self, 
                                      current_skills: List[str],
                                      target_roles: List[str],
                                      preferences: Dict[str, str]) -> str:
        """Build prompt for skill improvement suggestions"""
        
        prompt = f"""
As a career development expert, analyze the skill gap between current abilities and target roles:

CURRENT SKILLS: {', '.join(current_skills)}
TARGET ROLES: {', '.join(target_roles)}
PREFERENCES: {preferences}

Provide skill improvement recommendations in this JSON format:
{{
  "skill_gaps": [
    {{
      "skill": "Skill Name",
      "importance": "High/Medium/Low",
      "current_level": "Beginner/Intermediate/Advanced",
      "target_level": "Intermediate/Advanced/Expert",
      "learning_priority": 1,
      "estimated_time": "2-3 months",
      "resources": ["resource1", "resource2"]
    }}
  ],
  "learning_path": [
    {{
      "phase": "Phase 1",
      "duration": "1-2 months",
      "skills_to_focus": ["skill1", "skill2"],
      "milestones": ["milestone1", "milestone2"]
    }}
  ],
  "certifications": [
    {{
      "name": "Certification Name",
      "provider": "Provider",
      "relevance": "High",
      "estimated_cost": "$200-$500"
    }}
  ],
  "practice_projects": [
    "Project idea 1",
    "Project idea 2"
  ]
}}
"""
        return prompt
    
    def _build_resume_analysis_prompt(self,
                                    skills_by_category: Dict[str, List[str]],
                                    preferences: Dict[str, str],
                                    extracted_text: str) -> str:
        """Build prompt for resume analysis"""
        skills_text = self._format_skills_for_prompt(skills_by_category)
    
        
        prompt = f"""
As a professional resume reviewer, analyze this resume and provide improvement suggestions:

DETECTED SKILLS: {skills_text}
CAREER PREFERENCES: {preferences}

Provide analysis in this JSON format:
{{
  "overall_score": 75,
  "strengths": [
    "Strength 1",
    "Strength 2"
  ],
  "weaknesses": [
    "Weakness 1",
    "Weakness 2"
  ],
  "missing_sections": [
    "Section 1",
    "Section 2"
  ],
  "skill_presentation": {{
    "well_presented": ["skill1", "skill2"],
    "needs_improvement": ["skill3", "skill4"],
    "missing_keywords": ["keyword1", "keyword2"]
  }},
  "suggestions": [
    {{
      "category": "Content",
      "priority": "High",
      "suggestion": "Specific improvement suggestion"
    }}
  ],
  "ats_compatibility": {{
    "score": 80,
    "issues": ["issue1", "issue2"],
    "improvements": ["improvement1", "improvement2"]
  }}
}}
"""
        return prompt
    
    def _build_learning_path_prompt(self,
                                  current_skills: List[str],
                                  target_role: str,
                                  learning_preference: str) -> str:
        """Build prompt for learning path generation"""
        
        prompt = f"""
Create a personalized learning path for career advancement:

CURRENT SKILLS: {', '.join(current_skills)}
TARGET ROLE: {target_role}
LEARNING PREFERENCE: {learning_preference} (practical/theoretical/balanced)

Generate a learning path in this JSON format
(give me only the free courses):
{{
  "learning_path": {{
    "total_duration": "6-12 months",
    "phases": [
      {{
        "phase_number": 1,
        "title": "Foundation Building",
        "duration": "2-3 months",
        "skills": ["skill1", "skill2"],
        "resources": [
          {{
            "type": "course",
            "name": "Course Name",
            "provider": "Platform",
            "duration": "4 weeks",
            "cost": "Free"
          }}
        ],
        "projects": ["project1", "project2"],
        "milestones": ["milestone1", "milestone2"]
      }}
    ]
  }},
  "alternative_paths": [
    {{
      "path_name": "Fast Track",
      "duration": "3-6 months",
      "focus": "Intensive practical learning"
    }}
  ],
  "budget_breakdown": {{
    "free_resources": 60,
    "paid_courses": 40,
    "estimated_total": "$200-$800"
  }},
  "success_metrics": [
    "Metric 1",
    "Metric 2"
  ]
}}
"""
        return prompt
    
    def _format_skills_for_prompt(self, skills_by_category: Dict[str, List[str]]) -> str:
        """Format skills by category for prompt inclusion"""
        if not skills_by_category:
            return "No categorized skills detected"
        
        formatted = []
        for category, skills in skills_by_category.items():
            # Filter out None values and empty strings
            valid_skills = [str(s) for s in skills if s is not None and s != '']
            if valid_skills:
                formatted.append(f"{category}: {', '.join(valid_skills)}")
        
        return "; ".join(formatted) if formatted else "No valid skills detected"
    
    def _parse_career_response(self, response_text: str) -> Dict[str, Any]:
        """Parse career recommendation response"""
        try:
            # Clean the response text and extract JSON
            cleaned_response = self._clean_json_response(response_text)
            return json.loads(cleaned_response)
        except:
            return self._get_fallback_recommendations()
    
    def _parse_skill_response(self, response_text: str) -> Dict[str, Any]:
        """Parse skill improvement response"""
        try:
            cleaned_response = self._clean_json_response(response_text)
            return json.loads(cleaned_response)
        except:
            return self._get_fallback_skills()
    
    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse resume analysis response"""
        try:
            cleaned_response = self._clean_json_response(response_text)
            return json.loads(cleaned_response)
        except:
            return self._get_fallback_analysis()
    
    def _parse_learning_response(self, response_text: str) -> Dict[str, Any]:
        """Parse learning path response"""
        try:
            cleaned_response = self._clean_json_response(response_text)
            return json.loads(cleaned_response)
        except:
            return self._get_fallback_learning_path()
    
    def _clean_json_response(self, response_text: str) -> str:
        """Clean and extract JSON from response text"""
        # Remove markdown code blocks
        response_text = response_text.replace('```json', '').replace('```', '')
        
        # Find JSON object bounds
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx != -1 and end_idx != -1:
            return response_text[start_idx:end_idx]
        
        return response_text.strip()
    
    def _get_fallback_recommendations(self) -> Dict[str, Any]:
        """Fallback career recommendations when AI fails"""
        return {
            "recommended_roles": [
                {
                    "title": "Software Developer",
                    "match_percentage": 70,
                    "required_skills": ["Programming", "Problem Solving"],
                    "missing_skills": ["Advanced Frameworks"],
                    "salary_range": "$60,000 - $80,000",
                    "growth_potential": "High",
                    "industry": "Technology",
                    "reasoning": "Based on detected technical skills"
                }
            ],
            "industry_insights": {
                "trending_industries": ["Technology", "Healthcare"],
                "growth_sectors": ["AI/ML", "Cloud Computing"],
                "recommendations": "Focus on emerging technologies"
            },
            "next_steps": [
                "Identify specific role requirements",
                "Develop missing skills",
                "Build a portfolio"
            ],
            "confidence_score": 0.6
        }
    
    def _get_fallback_skills(self) -> Dict[str, Any]:
        """Fallback skill suggestions when AI fails"""
        return {
            "skill_gaps": [
                {
                    "skill": "Communication",
                    "importance": "High",
                    "current_level": "Intermediate",
                    "target_level": "Advanced",
                    "learning_priority": 1,
                    "estimated_time": "1-2 months",
                    "resources": ["Online courses", "Practice groups"]
                }
            ],
            "learning_path": [
                {
                    "phase": "Foundation",
                    "duration": "1-2 months",
                    "skills_to_focus": ["Core skills"],
                    "milestones": ["Complete basic training"]
                }
            ],
            "certifications": [],
            "practice_projects": ["Personal project", "Open source contribution"]
        }
    
    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """Fallback resume analysis when AI fails"""
        return {
            "overall_score": 65,
            "strengths": ["Technical skills present", "Experience documented"],
            "weaknesses": ["Could be more specific", "Missing quantified achievements"],
            "missing_sections": [],
            "skill_presentation": {
                "well_presented": [],
                "needs_improvement": [],
                "missing_keywords": []
            },
            "suggestions": [
                {
                    "category": "Content",
                    "priority": "Medium",
                    "suggestion": "Add more specific examples and achievements"
                }
            ],
            "ats_compatibility": {
                "score": 70,
                "issues": [],
                "improvements": ["Use more keywords", "Improve formatting"]
            }
        }
    
    def _get_fallback_learning_path(self) -> Dict[str, Any]:
        """Fallback learning path when AI fails"""
        return {
            "learning_path": {
                "total_duration": "3-6 months",
                "phases": [
                    {
                        "phase_number": 1,
                        "title": "Skill Development",
                        "duration": "2-3 months",
                        "skills": ["Core competencies"],
                        "resources": [
                            {
                                "type": "course",
                                "name": "Online Training",
                                "provider": "Various",
                                "duration": "Flexible",
                                "cost": "Free"
                            }
                        ],
                        "projects": ["Practice project"],
                        "milestones": ["Complete training"]
                    }
                ]
            },
            "alternative_paths": [],
            "budget_breakdown": {
                "free_resources": 80,
                "paid_courses": 20,
                "estimated_total": "$0-$200"
            },
            "success_metrics": ["Skill improvement", "Project completion"]
        }
