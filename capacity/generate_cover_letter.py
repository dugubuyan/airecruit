from config import get_model
from litellm import completion

def generate_cover_letter(recipient, subject, body, template=None):
    print("generate_cover_letter::",recipient, subject, body)
