"""
Gemini AI Career Navigation Service (LangGraph + Gemini)
Uses LangGraph to orchestrate Gemini API for career recommendations & insights
"""

import os
import json
import sys
import atexit
from typing import Dict, List, Any
import re

from dotenv import load_dotenv

# Configure logging to use stderr for logs
import logging
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger(__name__)

# LangChain + LangGraph imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not found in environment variables")
    # Don't raise an exception here, we'll handle it more gracefully later
    # by providing a fallback response

# Gracefully handle gRPC shutdown
def _cleanup_grpc():
    """Cleanup function to properly shut down gRPC connections"""
    try:
        import grpc
        grpc.aio.shutdown_channel = True
    except:
        pass

atexit.register(_cleanup_grpc)


# ----------------------------------------------------
# Define state (shared between graph nodes)
# ----------------------------------------------------
class CareerState(dict):
    """
    A dictionary-like state to hold skills, preferences, and AI outputs
    """


# ----------------------------------------------------
# Initialize Gemini Model via LangChain wrapper
# ----------------------------------------------------
gemini_model = None  # Initialize to None in case all model loading fails

if GEMINI_API_KEY:
    try:
        gemini_model = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            api_key=GEMINI_API_KEY,
            temperature=0.7,
        )
        logger.info("Using Gemini 1.5 Flash model")
    except Exception as e:
        logger.error(f"Failed to load gemini-1.5-flash: {e}")
        try:
            gemini_model = ChatGoogleGenerativeAI(
                model="gemini-1.5-pro",
                api_key=GEMINI_API_KEY,
                temperature=0.7,
            )
            logger.info("Using Gemini 1.5 Pro model")
        except Exception as e2:
            logger.error(f"Failed to load gemini-1.5-pro: {e2}")
            # Final fallback
            try:
                gemini_model = ChatGoogleGenerativeAI(
                    model="gemini-pro",
                    api_key=GEMINI_API_KEY,
                    temperature=0.7,
                )
                logger.info("Using Gemini Pro model")
            except Exception as e3:
                logger.error(f"Failed to load any Gemini model: {e3}")
else:
    logger.error("No Gemini API key found, model will not be available")


# ----------------------------------------------------
# Prompt templates
# ----------------------------------------------------
def build_career_prompt(state: CareerState) -> str:
    skills_text = ", ".join(state.get("current_skills", []))
    target_job = state.get("target_job", "Not specified")
    timeframe = state.get("timeframe_months", 6)
    
    return f"""
You are a career advisor AI specialized in {target_job} career paths.

CANDIDATE PROFILE:
Current Skills: {skills_text}
Target Role: {target_job}
Timeframe: {timeframe} months

1. Provide a detailed career transition plan with:
   - Key learning phases
   - Required skills to acquire
   - Timeline of milestones
   - Resources and recommendations

2. Create a Mermaid flowchart (using 'flowchart TD' syntax) that visualizes this career path.

The flowchart should:
- Show progression from current skills to target job
- Include key learning phases and milestones
- Use different node shapes for different activities
- Use descriptive labels

Respond in JSON format with:
{{
  "plan": "Detailed career transition plan in markdown format",
  "mermaid_code": "The mermaid flowchart code without markdown code block tags"
}}

Make the mermaid code valid and properly formatted.
"""


def build_learning_prompt(state: CareerState) -> str:
    skills_text = ", ".join(state.get("current_skills", []))
    target_job = state.get("target_job", "Not specified")
    timeframe = state.get("timeframe_months", 6)
    
    return f"""
Create a learning path for someone with skills in {skills_text} who wants to become a {target_job} in {timeframe} months.

Respond in JSON format with:
{{
  "learning_path": {{
    "total_duration": "{timeframe} months",
    "phases": [
      {{
        "phase_number": 1,
        "title": "Foundation Building",
        "duration": "1-2 months",
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
        "projects": ["project1"],
        "milestones": ["milestone1"]
      }}
    ]
  }}
}}
"""


# ----------------------------------------------------
# Graph Nodes (functions)
# ----------------------------------------------------
def generate_career_recommendations(state: CareerState) -> CareerState:
    """Node: generate career recommendations"""
    
    # Check if model is available
    if gemini_model is None:
        logger.error("Gemini model is not available")
        state["career_plan"] = generate_fallback_plan(state)
        return state
    
    prompt = build_career_prompt(state)
    
    try:
        # Log that we're invoking the model
        logger.info(f"Invoking Gemini model for career recommendations")
        resp = gemini_model.invoke(prompt)
        
        if resp is None:
            raise ValueError("Model returned None response")
        
        content = resp.content
        
        # Log the response size for debugging
        logger.info(f"Model response received, length: {len(content)}")
        
        # Try to extract JSON from the response
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            json_str = json_match.group(0)
            career_plan = json.loads(json_str)
        else:
            # If no JSON found, create structured data from text
            career_plan = {
                "plan": content,
                "mermaid_code": extract_mermaid_code(content)
            }
        
        state["career_plan"] = career_plan
    except Exception as e:
        logger.error(f"Error parsing career recommendations: {str(e)}")
        state["career_plan"] = generate_fallback_plan(state)
    
    return state


def generate_learning_path(state: CareerState) -> CareerState:
    """Node: generate learning path"""
    
    # Check if model is available
    if gemini_model is None:
        logger.error("Gemini model is not available for learning path generation")
        state["learning_path"] = {"error": "Model not available"}
        return state
    
    prompt = build_learning_prompt(state)
    
    try:
        # Log that we're invoking the model
        logger.info(f"Invoking Gemini model for learning path")
        resp = gemini_model.invoke(prompt)
        
        if resp is None:
            raise ValueError("Model returned None response")
            
        content = resp.content
        
        # Log the response size for debugging
        logger.info(f"Learning path response received, length: {len(content)}")
        
        # Try to extract JSON from the response
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            json_str = json_match.group(0)
            learning_path = json.loads(json_str)
        else:
            # If no JSON found, create structured data
            logger.warning("No JSON found in learning path response")
            learning_path = {"error": "Failed to parse learning path"}
        
        state["learning_path"] = learning_path
    except Exception as e:
        logger.error(f"Error parsing learning path: {str(e)}")
        state["learning_path"] = {"error": "Failed to parse learning path"}
    
    return state


# ----------------------------------------------------
# Helper functions
# ----------------------------------------------------
def extract_mermaid_code(text):
    """Extract Mermaid flowchart code from text"""
    mermaid_match = re.search(r'```mermaid\s+(.*?)\s+```', text, re.DOTALL)
    if mermaid_match:
        return mermaid_match.group(1).strip()
    
    # Try without mermaid tag
    flowchart_match = re.search(r'```\s*(flowchart\s+TD.*?)```', text, re.DOTALL)
    if flowchart_match:
        return flowchart_match.group(1).strip()
    
    # Try just finding a flowchart
    raw_flowchart = re.search(r'(flowchart\s+TD.*?)(?:```|$)', text, re.DOTALL)
    if raw_flowchart:
        return raw_flowchart.group(1).strip()
    
    return ""


def generate_fallback_plan(state):
    """Generate a fallback career plan"""
    skills_text = ", ".join(state.get("current_skills", []))
    target_job = state.get("target_job", "Not specified")
    timeframe = state.get("timeframe_months", 6)
    
    # Create a simple Mermaid flowchart
    mermaid_code = f"""flowchart TD
    A[Current Skills: {skills_text}] --> B[Skill Development]
    B --> C[Project Building]
    C --> D[Networking & Job Prep]
    D --> E[Target Job: {target_job}]
    
    style A fill:#f9f,stroke:#333,stroke-width:2px
    style E fill:#bbf,stroke:#333,stroke-width:2px
    """
    
    # Create a simple plan text
    plan_text = f"""
# Career Transition Plan: From Current Skills to {target_job}

## Overview
This {timeframe}-month plan will help you transition from your current skillset ({skills_text}) to becoming a {target_job}.

## Phase 1: Skill Development ({timeframe // 3} months)
* Identify core skills needed for {target_job}
* Take online courses on platforms like Coursera, Udemy, or LinkedIn Learning
* Join relevant communities to learn from peers

## Phase 2: Project Building ({timeframe // 3} months)
* Create portfolio projects that demonstrate your skills
* Contribute to open source if applicable
* Document your work and learning process

## Phase 3: Networking & Job Preparation ({timeframe // 3} months)
* Update your resume and online profiles
* Connect with professionals in your target field
* Prepare for interviews and apply for positions

## Key Milestones
1. Month 1: Complete skills assessment and learning plan
2. Month {timeframe // 2}: Finish first major portfolio project
3. Month {timeframe}: Ready to apply for {target_job} positions
    """
    
    return {
        "plan": plan_text,
        "mermaid_code": mermaid_code
    }


# ----------------------------------------------------
# Build LangGraph pipeline
# ----------------------------------------------------
def build_career_graph():
    """Build and return the LangGraph for career planning"""
    try:
        graph_builder = StateGraph(CareerState)
        
        # Add nodes
        graph_builder.add_node("career_recs", generate_career_recommendations)
        graph_builder.add_node("learning", generate_learning_path)
        
        # Define edges (flow of execution)
        graph_builder.set_entry_point("career_recs")
        graph_builder.add_edge("career_recs", "learning")
        graph_builder.add_edge("learning", END)
        
        # Compile graph
        return graph_builder.compile()
    except Exception as e:
        logger.error(f"Error building career graph: {str(e)}")
        # Return None so we can handle it gracefully
        return None


# ----------------------------------------------------
# Main function for CLI usage
# ----------------------------------------------------
def generate_career_plan(current_skills, target_job, timeframe_months):
    """Generate a career plan using LangGraph"""
    try:
        # Create initial state
        input_state = CareerState(
            current_skills=current_skills,
            target_job=target_job,
            timeframe_months=timeframe_months
        )
        
        # Build graph
        career_graph = build_career_graph()
        
        # Check if graph was created successfully
        if career_graph is None:
            logger.error("Failed to create LangGraph - using fallback plan")
            # Generate a simple fallback plan
            fallback_state = CareerState(
                current_skills=current_skills,
                target_job=target_job,
                timeframe_months=timeframe_months
            )
            fallback_plan = generate_fallback_plan(fallback_state)
            return {
                "plan": fallback_plan["plan"],
                "mermaid_code": fallback_plan["mermaid_code"],
                "learning_path": {},
                "full_response": {"error": "Failed to create LangGraph"}
            }
        
        # Invoke graph with input state
        try:
            logger.info("Invoking LangGraph")
            final_state = career_graph.invoke(input_state)
            logger.info("LangGraph execution completed")
        except Exception as graph_error:
            logger.error(f"Error executing LangGraph: {str(graph_error)}")
            # Use fallback plan on graph execution error
            fallback_state = CareerState(
                current_skills=current_skills,
                target_job=target_job,
                timeframe_months=timeframe_months
            )
            fallback_plan = generate_fallback_plan(fallback_state)
            return {
                "plan": fallback_plan["plan"],
                "mermaid_code": fallback_plan["mermaid_code"],
                "learning_path": {},
                "full_response": {"error": f"Error executing LangGraph: {str(graph_error)}"}
            }
        
        if final_state is None:
            raise ValueError("LangGraph returned None state")
        
        # Get results safely with default values
        career_plan = final_state.get("career_plan", {}) or {}  # Ensure we have a dict even if None
        learning_path = final_state.get("learning_path", {}) or {}
        
        # Safe access with defaults for nested values
        plan_text = "No plan generated"
        mermaid_code = ""
        learning_path_data = {}
        
        if career_plan:
            plan_text = career_plan.get("plan", plan_text)
            mermaid_code = career_plan.get("mermaid_code", mermaid_code)
        
        if learning_path:
            learning_path_data = learning_path.get("learning_path", learning_path_data)
        
        # Combine results for response
        result = {
            "plan": plan_text,
            "mermaid_code": mermaid_code,
            "learning_path": learning_path_data,
            "full_response": career_plan
        }
        
        return result
    except Exception as e:
        logger.error(f"Error in generate_career_plan: {str(e)}")
        # Return fallback result
        skills_text = ", ".join(current_skills) if current_skills else "various skills"
        return {
            "plan": f"Error generating plan for {target_job} with {skills_text}",
            "mermaid_code": f"flowchart TD\n    A[Current Skills] --> B[Target: {target_job}]",
            "full_response": {"error": str(e)}
        }


# ----------------------------------------------------
# Entry point for CLI usage
# ----------------------------------------------------
if __name__ == "__main__":
    try:
        # Parse command line arguments
        current_skills = json.loads(sys.argv[1])
        target_job = sys.argv[2]
        timeframe_months = int(sys.argv[3])
        
        logger.info(f"Generating career plan for {target_job} with timeframe {timeframe_months} months")
        
        # Generate plan
        result = generate_career_plan(current_skills, target_job, timeframe_months)
        
        # Output as JSON - this is the only output that should go to stdout
        print(json.dumps(result))
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        # Error response also goes to stdout but as properly formatted JSON
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
