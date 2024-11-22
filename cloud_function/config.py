import os


class Config:
    def __init__(self):
        self.db_host = os.getenv("POSTGRES_HOST")
        self.db_user = os.getenv("POSTGRES_USER")
        self.db_password = os.getenv("POSTGRES_PASSWORD")
        self.db_name = os.getenv("POSTGRES_DB")
        self.db_port = os.getenv("POSTGRES_PORT")
        self.activity_days = int(os.getenv("ACTIVITY_DAYS", 30))
        self.github_token = os.getenv("GITHUB_TOKEN")

        self.db_url = (f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:"
                       f"{self.db_port}/{self.db_name}?sslmode=require")
