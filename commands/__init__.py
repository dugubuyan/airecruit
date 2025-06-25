# from .optimize_resume import optimize_resume
from .summarize_resume import summarize_resume
from .generate_cover_letter import generate_cover_letter
from .resume_filters import resume_to_sql_filters
from .recommendation import generate_recommendation
from .contact_extractor import extract_contact_and_send

__all__ = [
    # 'optimize_resume',
    'summarize_resume',
    'generate_cover_letter',
    'resume_to_sql_filters',
    'generate_recommendation',
    'extract_contact_and_send',
    'send_email'
]

WORK_COMMANDS = [
    # 'optimize',
    'summarize',
    'cover-letter',
    'filters',
    'recommend',
    'contact'
]
