from pydantic import BaseModel


class Settings(BaseModel):
    directory_api_base_url: str = "https://hospital-directory.onrender.com"
    max_hospitals_per_csv: int = 20
    request_timeout_seconds: float = 20.0


settings = Settings()
