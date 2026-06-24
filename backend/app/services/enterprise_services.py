import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext

# Security
SECRET_KEY = "enterprise_secret_key"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    def verify_password(self, plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password):
        return pwd_context.hash(password)

class SonarService:
    def get_metrics(self, project_key: str):
        """
        Simulates fetching metrics from SonarQube.
        """
        return {
            "bugs": 0,
            "vulnerabilities": 0,
            "code_smells": 5,
            "coverage": "94.2%",
            "duplicated_lines": "0.5%"
        }

auth_service = AuthService()
sonar_service = SonarService()
