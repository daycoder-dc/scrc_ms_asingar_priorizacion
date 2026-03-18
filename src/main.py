from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from .app.controllers import asignacion_controller
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi import FastAPI, status

app = FastAPI(
    title="scrc asignaciones",
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
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)

app.include_router(asignacion_controller.router)

@app.get("/")
async def root():
    response = {
        "service": "scrc_ms_asignar_priorizacion",
        "status": "running"
    }

    return JSONResponse(
        content=jsonable_encoder(response),
        status_code=status.HTTP_200_OK
    )
