import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_SECRET_FILE = os.getenv("CLIENT_SECRET_FILE")
TOKEN_FILE = os.getenv("TOKEN_FILE")
SCOPES = [os.getenv("SCOPES")]