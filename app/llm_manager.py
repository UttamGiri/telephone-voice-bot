"""Manages LLM context and detects when to inject full résumé."""
import re
import json
from app.resume_context import get_full_resume


def search_resume_for_context(query: str, full_resume: str) -> str:
    """Search resume_full.txt for relevant information based on user query."""
    query_lower = query.lower()
    lines = full_resume.split('\n')
    
    # Extract all words from query (excluding common words)
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'what', 'who', 'where', 'when', 'how', 'why', 'tell', 'me', 'about', 'you', 'your', 'yourself', 'do', 'does', 'did'}
    query_words = [w for w in query_lower.split() if w not in stop_words and len(w) > 2]
    
    relevant_lines = []
    score_map = {}  # Track relevance scores
    
    # First pass: find lines that contain query words
    for i, line in enumerate(lines):
        if not line.strip() or len(line.strip()) < 5:
            continue
            
        line_lower = line.lower()
        score = 0
        
        # Count how many query words appear in this line
        for word in query_words:
            if word in line_lower:
                score += 1
                # Bonus for exact word match
                if f' {word} ' in f' {line_lower} ' or line_lower.startswith(word) or line_lower.endswith(word):
                    score += 2
        
        # Also check for section headers
        if line.strip().endswith(':') or (line.strip().isupper() and len(line.strip()) < 50):
            score += 1
        
        if score > 0:
            score_map[i] = score
            relevant_lines.append((score, line.strip()))
    
    # Sort by relevance score (highest first)
    relevant_lines.sort(key=lambda x: x[0], reverse=True)
    
    # Extract top relevant lines
    if relevant_lines:
        # Get top 15 most relevant lines
        top_lines = [line for score, line in relevant_lines[:15]]
        context = '\n'.join(top_lines)
        print(f"🔍 Found {len(top_lines)} relevant lines from resume")
        return context
    
    # If no matches, return key sections (summary, skills, experience)
    print("⚠️  No direct matches - returning key resume sections")
    key_sections = []
    current_section = None
    
    for line in lines:
        line_stripped = line.strip()
        # Capture section headers
        if line_stripped.endswith(':') or (line_stripped.isupper() and len(line_stripped) < 50):
            current_section = line_stripped
            if any(keyword in line_stripped.lower() for keyword in ['summary', 'skill', 'experience', 'professional']):
                key_sections.append(line_stripped)
        # Capture lines from key sections
        elif current_section and any(keyword in current_section.lower() for keyword in ['summary', 'skill', 'experience']):
            if line_stripped and len(line_stripped) > 10:
                key_sections.append(line_stripped)
                if len(key_sections) >= 10:
                    break
    
    if key_sections:
        return '\n'.join(key_sections[:10])
    
    # Fallback: return first 500 chars
    return full_resume[:500]


def get_context_for_query(query: str) -> str:
    """Get relevant context from resume_full.txt based on user query."""
    full_resume = get_full_resume()
    context = search_resume_for_context(query, full_resume)
    return context


def should_load_full_resume(transcript: str) -> bool:
    """Detect user interest in detailed Uttam information."""
    keywords = [
        "more about uttam",
        "uttam's experience",
        "uttam work history",
        "uttam background",
        "projects uttam",
        "detailed resume",
        "full resume",
        "tell me more about uttam",
        "uttam's projects",
        "uttam's skills",
        "about uttam",
        "who is uttam",
        "uttam giri"
    ]
    transcript_lower = transcript.lower()
    return any(keyword in transcript_lower for keyword in keywords)

def is_uttam_question(transcript: str) -> bool:
    """Detect if question is about Uttam (basic or detailed)."""
    if not transcript:
        return False
    
    transcript_lower = transcript.lower()
    
    # More comprehensive keyword detection
    uttam_keywords = [
        "uttam", "uttam giri", "uttam's", 
        "you", "your", "yourself",  # Since AI speaks as Uttam
        "what do you", "who are you", "tell me about you",
        "your skills", "your experience", "your background",
        "what are you", "where do you", "what can you"
    ]
    
    # Check if transcript contains Uttam keywords
    matches = any(keyword in transcript_lower for keyword in uttam_keywords)
    
    # Also check if it's a question (contains question words)
    question_words = ["what", "who", "where", "when", "how", "why", "tell me", "describe"]
    is_question = any(word in transcript_lower for word in question_words)
    
    # If it's a question, assume it might be about Uttam (since AI is Uttam)
    return matches or is_question


async def inject_full_resume(ws):
    """Inject detailed résumé into the Realtime model context dynamically."""
    full_resume = get_full_resume()
    event = {
        "type": "response.create",
        "response": {
            "modalities": ["audio"],
            "instructions": f"Here is Uttam's detailed résumé:\n\n{full_resume}",
            "voice": "cove"  # Voice belongs in response.create
        }
    }
    await ws.send(json.dumps(event))
    print("📄 Full résumé injected into session.")

