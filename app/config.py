import os


class Settings:
    ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "localhost")
    ELASTICSEARCH_PORT = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
    ELASTICSEARCH_INDEX = "recipes"

    API_TITLE = "Dishcovery API"
    API_VERSION = "1.0.0"


settings = Settings()
