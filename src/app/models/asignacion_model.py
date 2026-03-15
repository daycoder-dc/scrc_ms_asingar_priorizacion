from fastapi import UploadFile, status, Response, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlmodel import text, Session
from src.config import database
from typing import Annotated
from fastapi import Depends
from loguru import logger
from io import BytesIO

import polars as pl

async def task_register_pmu(file: UploadFile):
    file = await file.read()
    file_buffer = BytesIO(file)
    df = pl.read_excel(file_buffer)

    map_columns = {
        "Prioridad": "prioridad",
        "Cuenta": "cuenta",
        "Numero de la Os": "numero_os",
        "Tipo_Orden": "tipo_orden",
        "Tipo_Brigada": "tipo_brigada",
        "Tipo_Actividad": "tipo_actividad",
        "Fecha_Asignación_Cliente": "fecha_asignacion_cliente"
    }

    df = df.rename(map_columns)

    df = df.with_columns(
        pl.col("prioridad").fill_nan(None),
        pl.col("cuenta").fill_nan(None),
        pl.col("numero_os").fill_nan(None),
        pl.col("tipo_orden").str.strip_chars().str.to_lowercase(),
        pl.col("tipo_brigada").str.strip_chars().str.to_lowercase().str.normalize("NFD").str.replace(r"[\u0300-\u036f]", ""),
        pl.col("tipo_actividad").str.strip_chars().str.to_lowercase().str.normalize("NFD").str.replace(r"[\u0300-\u036f]", "")
    )

    df.write_database(table_name="pmu_priorizacion_cliente", connection=database.db_uri, engine=database.db_engine, if_table_exists="append")

    logger.info("datos insertados.")

async def registra_pmu(file: UploadFile, bg_task: BackgroundTasks):
    bg_task.add_task(task_register_pmu, file)
    return Response(status_code=status.HTTP_200_OK)

async def delete_pmu(session: Annotated[Session, Depends(database.get_session)]):
    stmt = text("""
        UPDATE pmu_priorizacion_cliente
        SET eliminado = :eliminado
        WHERE fecha_registro::DATE = CURRENT_DATE;
    """)

    session.execute(stmt, [{"eliminado": True}])
    session.commit()

    logger.info("PMU eliminada")

    return JSONResponse(
        content=jsonable_encoder({"status": "eliminado"}),
        status_code=status.HTTP_202_ACCEPTED
    ) 

async def count_pmu(session: Annotated[Session, Depends(database.get_session)]):
    result = session.execute(text("SELECT COUNT(*) FROM pmu_priorizacion_cliente")).mappings().all()

    logger.info("PMU Total:", reuslt[0])

    return JSONResponse(
        content=jsonable_encoder(result), 
        status_code=status.HTTP_200_OK
    )