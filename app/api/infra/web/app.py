from contextlib import asynccontextmanager
from fastapi import FastAPI
from .routes import router
from api.infra.container.dependecies import Container

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    container = app.container
    semantic_anchor = container.semantic_anchor()
    if not semantic_anchor.initialize():
        raise Exception("Falha ao inicializar SemanticAnchor")
    yield
    # Shutdown (adicionar limpeza se necessário no futuro)

def create_app() -> FastAPI:
    # Criar e configurar o container
    container = Container()
    
    container.wire(packages=["api"])
    
    # Criar aplicação FastAPI com lifespan
    app = FastAPI(
        title="Medical Assistant API", 
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Anexar container à aplicação
    app.container = container
    
    # Incluir rotas
    app.include_router(router)
    
    return app

app = create_app()