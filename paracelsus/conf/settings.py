from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    project_name: str = "paracelsus"
    debug: bool = False
