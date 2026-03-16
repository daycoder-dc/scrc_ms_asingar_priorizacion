from fastapi import APIRouter, Depends, status, Response
from src.app.models import asignacion_model
from typing import Annotated
from src.config import token

router = APIRouter(
    prefix="/asignacion",
    tags=["asignacion"],
    dependencies=[Depends(token.get_token_header)],
    responses={404: {"description": "Not Found"}}
)

@router.get("/")
async def root():
    return Response(status_code=status.HTTP_200_OK)

@router.post("/pmu/registrar")
async def registra_pmu(model: Annotated[dict, Depends(asignacion_model.registra_pmu)]):
    return model

@router.get("/pmu/verificar")
async def verificar_pmu(model: Annotated[dict, Depends(asignacion_model.verificar_pmu)]):
    return model
