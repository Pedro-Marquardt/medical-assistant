from fastapi import FastAPI
from .routes import router
from api.infra.container.dependecies import Container

def create_app() -> FastAPI:
    # Criar e configurar o container
    container = Container()
    
    container.wire(packages=["api"])
    
    # Criar aplicação FastAPI
    app = FastAPI(title="Medical Assistant API", version="1.0.0")
    
    # Anexar container à aplicação
    app.container = container
    
    # Incluir rotas
    app.include_router(router)
    
    return app

app = create_app()