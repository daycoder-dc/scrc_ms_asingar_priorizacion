from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from .config.settings import Settings
from .app.controllers import asignacion_controller

settings = Settings()

app = FastAPI(
    root_path="/api/v1"
)

app.add_middleware(
    GZipMiddleware, 
    compresslevel=5
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "PUT", "POST", "PATCH", "DELETE"],
    allow_headers=["*"]
)

app.include_router(asignacion_controller.router)

@app.get("/")
async def root():
    return Response(status_code=status.HTTP_200_OK)