from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    elasticsearch_url: str = "http://localhost:9200"
    documents_index: str = "taxonomy_documents"
    taxonomy_index: str = "taxonomy_paths"
    locations_index: str = "facility_locations"
    maintenance_issues_index: str = "maintenance_issues"
    ontology_dir: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
