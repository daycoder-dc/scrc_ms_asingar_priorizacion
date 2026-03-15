from fastapi import APIRouter, Depends, status, Response
from typing import Annotated
from src.config import token
from src.app.models import asignacion_model

router = APIRouter(
    prefix="/asignacion",
    tags=["asignacion"],
    dependencies=[Depends(token.get_token_header)],
    responses={404: {"description": "Not Found"}}
)

@router.get("/")
async def root():
    return Response(status_code=status.HTTP_200_OK)

@router.post("/registrar/pmu")
async def registra_pmu(model: Annotated[dict, Depends(asignacion_model.registra_pmu)]):
    return model

@router.delete("/eliminar/pmu")
async def delete_pmu(model: Annotated[Response, Depends(asignacion_model.delete_pmu)]):
    return model