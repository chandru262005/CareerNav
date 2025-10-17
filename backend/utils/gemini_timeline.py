import os
import json
import re
import sys
import requests
from dotenv import load_dotenv
import google.generativeai as genai

# -----------------------------------
# Load Environment Variables
# -----------------------------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")

# ===================================================================
# 🔹 Function 1 — DETAILED AI-GENERATED TIMELINE (Gemini)
# ===================================================================
def create_ai_career_timeline(current_skills, target_job, timeframe_months, additional_context=None):
    """
    Generate a detailed, AI-based career timeline using Gemini API.
    Returns an intelligent, structured plan with multiple phases, skills, projects, and tips.
    """
    if not GEMINI_API_KEY:
        return {"error": "GEMINI_API_KEY not set"}

    context_text = ""
    if additional_context:
        if additional_context.get("projects"):
            context_text += f"\nProjects: {json.dumps(additional_context['projects'], indent=2)}"
        if additional_context.get("experience"):
            context_text += f"\nExperience: {json.dumps(additional_context['experience'], indent=2)}"
        if additional_context.get("education"):
            context_text += f"\nEducation: {json.dumps(additional_context['education'], indent=2)}"

    skills_text = ", ".join(current_skills) if current_skills else "various technical skills"

    prompt = f"""
    Create a step-by-step career roadmap to become a {target_job} in {timeframe_months} months.
    Current skills: {skills_text}
    {context_text}

    Format output as VALID JSON with:
    {{
      "summary": "...",
      "timeline": [
        {{
          "title": "Phase name",
          "description": "Detailed explanation",
          "duration_weeks": number,
          "skills": ["Skill 1", "Skill 2"],
          "projects": ["Project 1", "Project 2"],
          "milestones": ["Milestone 1", "Milestone 2"]
        }}
      ],
      "tips": ["Tip 1", "Tip 2"],
      "interview_prep": ["Question 1", "Question 2"],
      "common_pitfalls": ["Pitfall 1", "Pitfall 2"]
    }}
    """

    try:
        response = model.generate_content(prompt)
        raw_text = response.text
        json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        result = json.loads(json_match.group()) if json_match else json.loads(raw_text)
        return result
    except Exception as e:
        return {"error": f"Gemini generation failed: {e}"}


# ===================================================================
# 🔹 Function 2 — YOUTUBE VIDEO RECOMMENDATIONS (YouTube API)
# ===================================================================
def create_youtube_career_timeline(current_skills, target_job, timeframe_months, additional_context=None):
    """
    Fetch YouTube video recommendations based on skills and target job.
    Returns a list of videos with title, channel, views, and duration.
    """
    if not YOUTUBE_API_KEY:
        return {"error": "YOUTUBE_API_KEY not set"}

    skills_text = ", ".join(current_skills) if current_skills else "various technical skills"

    # Generate search terms based on current skills and target job
    search_terms = [
        f"{target_job} tutorial",
        f"{target_job} course",
        f"{target_job} full course",
        f"learn {target_job}",
        f"{target_job} for beginners",
    ]
    
    # Add skill-specific searches for ALL skills with better keywords
    for skill in current_skills:  # Search for all provided skills
        search_terms.append(f"{skill} {target_job}")
        search_terms.append(f"learn {skill} for {target_job}")
        search_terms.append(f"{skill} tutorial {target_job}")
        search_terms.append(f"{skill} course {target_job}")

    # Fetch videos (20+ minutes duration, any view count)
    videos = search_youtube_videos(search_terms, min_views=0, min_duration_minutes=20, max_results=6)

    result = {
        "title": f"Learning Path for {target_job}",
        "summary": f"Top YouTube video recommendations to help you transition to {target_job}",
        "youtube_resources": videos,
        "tips": [
            "Watch full-length, comprehensive tutorials to build deep knowledge",
            "Take detailed notes and pause frequently to understand concepts",
            "Practice coding along with the tutorials in real-time",
            "Build projects after completing each major section",
            "Join communities and engage with other learners"
        ]
    }
    return result


# ===================================================================
# 🔹 Helper Function: YouTube API Search with Filtering
# ===================================================================
def search_youtube_videos(search_terms, max_results=6, min_views=0, min_duration_minutes=20, language="en"):
    """
    Fetch top YouTube videos for given search terms with views and duration.
    """
    if not YOUTUBE_API_KEY:
        return []

    all_videos = []
    
    for term in search_terms:
        try:
            # First API call to get video IDs
            search_url = "https://www.googleapis.com/youtube/v3/search"
            search_params = {
                "part": "snippet",
                "q": term,
                "key": YOUTUBE_API_KEY,
                "maxResults": 10,
                "type": "video",
                "relevanceLanguage": language,
                "order": "relevance"
            }
            
            resp = requests.get(search_url, search_params, timeout=10)
            if resp.status_code != 200:
                continue

            data = resp.json()
            video_ids = [item["id"]["videoId"] for item in data.get("items", [])]
            
            if not video_ids:
                continue
            
            # Second API call to get statistics and contentDetails
            stats_url = "https://www.googleapis.com/youtube/v3/videos"
            stats_params = {
                "part": "statistics,contentDetails,snippet",
                "id": ",".join(video_ids),
                "key": YOUTUBE_API_KEY
            }
            
            stats_resp = requests.get(stats_url, stats_params, timeout=10)
            if stats_resp.status_code != 200:
                continue
            
            stats_data = stats_resp.json()
            
            # Process and filter videos
            for item in stats_data.get("items", []):
                try:
                    vid = item["id"]
                    views_str = item.get("statistics", {}).get("viewCount", "0")
                    views = int(views_str) if views_str else 0
                    duration = item.get("contentDetails", {}).get("duration", "")
                    title = item["snippet"]["title"]
                    
                    # Parse duration and convert to minutes
                    duration_minutes = parse_iso_duration_to_minutes(duration)
                    
                    # Apply filters
                    if views >= min_views and duration_minutes >= min_duration_minutes:
                        duration_readable = parse_iso_duration(duration)
                        views_formatted = format_view_count(views)
                        
                        all_videos.append({
                            "title": title,
                            "channel": item["snippet"]["channelTitle"],
                            "url": f"https://www.youtube.com/watch?v={vid}",
                            "views": views_formatted,
                            "duration": duration_readable,
                            "views_raw": views
                        })
                except Exception:
                    pass
                    
        except Exception:
            pass

    # Sort by views (descending) and remove duplicates
    seen_urls = set()
    unique_videos = []
    
    for video in sorted(all_videos, key=lambda x: x["views_raw"], reverse=True):
        if video["url"] not in seen_urls:
            unique_videos.append(video)
            seen_urls.add(video["url"])
            if len(unique_videos) >= 10:  # Fetch best 10 videos
                break
    
    # Remove the raw views field before returning
    for video in unique_videos:
        del video["views_raw"]
    
    return unique_videos


def parse_iso_duration(duration):
    """Convert ISO 8601 duration to readable format."""
    # Example: PT1H30M45S -> 1h 30m 45s
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    match = re.match(pattern, duration)
    if not match:
        return ""
    
    hours, minutes, seconds = match.groups()
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds:
        parts.append(f"{seconds}s")
    
    return " ".join(parts) if parts else ""


def parse_iso_duration_to_minutes(duration):
    """Convert ISO 8601 duration to total minutes."""
    # Example: PT1H30M45S -> 90.75 minutes
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    match = re.match(pattern, duration)
    if not match:
        return 0
    
    hours, minutes, seconds = match.groups()
    total_minutes = 0
    if hours:
        total_minutes += int(hours) * 60
    if minutes:
        total_minutes += int(minutes)
    if seconds:
        total_minutes += int(seconds) / 60
    
    return total_minutes


def format_view_count(views):
    """Format view count as human-readable (e.g., 1.3M, 500K)."""
    if views >= 1000000:
        # Format as millions (e.g., 1.3M, 2.5M)
        millions = views / 1000000
        if millions >= 10:
            return f"{int(millions)}M"
        else:
            return f"{millions:.1f}M".rstrip('0').rstrip('.')
    elif views >= 1000:
        # Format as thousands (e.g., 500K, 250K)
        thousands = views / 1000
        if thousands >= 100:
            return f"{int(thousands)}K"
        else:
            return f"{thousands:.0f}K"
    else:
        return str(views)


# ===================================================================
# 🔹 Run as Script
# ===================================================================
if __name__ == "__main__":
    try:
        current_skills = json.loads(sys.argv[1])
        target_job = sys.argv[2]
        timeframe_months = int(sys.argv[3])
        mode = sys.argv[4] if len(sys.argv) > 4 else "ai"  # choose "ai" or "youtube"

        if mode == "ai":
            result = create_ai_career_timeline(current_skills, target_job, timeframe_months)
        else:
            result = create_youtube_career_timeline(current_skills, target_job, timeframe_months)

        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
