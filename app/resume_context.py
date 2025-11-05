"""Manages résumé context for the voice assistant."""
import os

SHORT_RESUME = """
Uttam Giri is an AWS Certified Solutions Architect and AI Practitioner.

Uttam Giri's expertise includes:
- Java development
- Kubernetes multi-cluster deployments  
- Istio service mesh
- AWS cloud automation
- OpenAI Realtime API integration
- Amazon Connect voice AI systems

Uttam Giri builds voice AI systems using OpenAI Realtime and Amazon Connect.
Uttam Giri works with cloud infrastructure and AI technologies.
"""


def get_short_resume():
    """Return short résumé for fast context injection."""
    return SHORT_RESUME.strip()


def get_full_resume():
    """Load detailed résumé text if user asks for more detail."""
    resume_path = os.path.join(os.path.dirname(__file__), "..", "resume_full.txt")
    if os.path.exists(resume_path):
        with open(resume_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "Full résumé not available. Please contact for detailed information."

