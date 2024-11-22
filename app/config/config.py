from pydantic_settings  import BaseSettings


class Settings(BaseSettings):
    host: str
    port: int = 5432
    user: str
    db: str
    password: str

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"

    class Config:
        env_file = "../../.env"
        env_prefix = "POSTGRES_"
