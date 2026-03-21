from dependency_injector import containers, providers
from api.infra.database.chroma.connection import ChromaDatabase


class Container(containers.DeclarativeContainer):
    
    # Database providers
    chroma_database = providers.Singleton(
        ChromaDatabase
    )