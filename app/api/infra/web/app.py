from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    
    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",  
            "http://localhost:5174",  
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://localhost:3000", 
            "http://127.0.0.1:3000"
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Incluir rotas
    app.include_router(router)
    
    return app

app = create_app()