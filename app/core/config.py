from dotenv import load_dotenv
import os

load_dotenv()

ENV = os.getenv("ENV", "dev")
DATABASE_URL = os.getenv("DATABASE_URL", "")
JWT_SECRET_KEY= os.getenv("JWT_SECRET_KEY", "")
JWT_ALGORITHM= os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES= int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS"))

# CORS
ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "")
