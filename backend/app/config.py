from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    elasticsearch_url: str = "http://localhost:9200"
    documents_index: str = "taxonomy_documents"
    taxonomy_index: str = "taxonomy_paths"

    class Config:
        env_file = ".env"

settings = Settings()
