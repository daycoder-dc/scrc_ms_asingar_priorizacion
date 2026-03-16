from fastapi import UploadFile, status, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.config import database
from typing import Annotated
from fastapi import Depends
from loguru import logger
from io import BytesIO

import polars as pl

async def task(file: UploadFile, session: Session) -> None:
    file = await file.read()
    file_buffer = BytesIO(file)
    df_pmu = pl.read_excel(file_buffer)

    logger.info("Archivo excel leido ✔️")

    # step 1: Limpiar la tabla con registros actuales.

    stmt = text("""
        UPDATE pmu_priorizacion_cliente
        SET eliminado = :eliminado
        WHERE fecha_registro::DATE = CURRENT_DATE;
    """)

    session.execute(stmt, [{"eliminado": True}])
    session.commit()

    logger.info("PMU eliminada ✔️")

    # step 2: normalizar columnas e insertar en la tabla.

    map_columns = {
        "Prioridad": "prioridad",
        "Cuenta": "cuenta",
        "Numero de la Os": "numero_os",
        "Tipo_Orden": "tipo_orden",
        "Tipo_Brigada": "tipo_brigada",
        "Tipo_Actividad": "tipo_actividad",
        "Fecha_Asignación_Cliente": "fecha_asignacion_cliente"
    }

    df_pmu = df_pmu.rename(map_columns)

    df_pmu = df_pmu.with_columns(
        pl.col("prioridad").fill_nan(None),
        pl.col("cuenta").fill_nan(None),
        pl.col("numero_os").fill_nan(None),
        pl.col("tipo_orden").str.strip_chars().str.to_lowercase(),
        pl.col("tipo_brigada").str.strip_chars().str.to_lowercase().str.normalize("NFD").str.replace(r"[\u0300-\u036f]", ""),
        pl.col("tipo_actividad").str.strip_chars().str.to_lowercase().str.normalize("NFD").str.replace(r"[\u0300-\u036f]", "")
    )

    df_pmu.write_database(
        table_name="pmu_priorizacion_cliente",
        connection=database.db_uri,
        engine=database.db_engine,
        if_table_exists="append"
    )

    logger.info("PMU registrado. ✔️")

    # step 3: Procesar Maestro para el cruze con el PMU

    stmt = text("""
        SELECT md.id, md.nic, md.priorizacion
        FROM maestro_db md
        WHERE md.eliminado = :eliminado
        -- AND md.fecha_registro::date = current_date;
    """)

    db_master = session.execute(stmt, [{"eliminado": False}]).mappings().all()

    logger.info("Mestro_DB consultado. ✔️")

    if len(db_master) > 0:
        logger.info("Maestro listo para operar ✔️")

        df_master = pl.DataFrame(db_master)
        df_pmu = df_pmu.select(["cuenta", "prioridad"]).unique(subset=["cuenta"], keep="first")

        df_master = df_master.drop("priorizacion").join(
            df_pmu,
            left_on="nic",
            right_on="cuenta",
            how="left"
        ).rename({"prioridad":"priorizacion"}).with_columns(
            pl.col("priorizacion").fill_null(3)
        )

        logger.info("Maestro cruzado ✔️")

        df_master.write_database(
            table_name="temp_maestro_db",
            connection=database.db_uri,
            engine=database.db_engine,
            if_table_exists="replace"
        )

        logger.info("Tabla temporar maestro_db creada ✔️")

        update_stmt = text("""
            UPDATE maestro_db
            SET priorizacion = temp.priorizacion
            FROM temp_maestro_db temp
            WHERE maestro_db.nic = temp.nic;
        """)

        try:
            session.execute(update_stmt)
            session.commit()

            logger.info("Maestro actualizado ✔️")

            session.execute(text("DROP TABLE temp_maestro_db;"))
            session.commit()

            logger.info("Tabla temp maestro eliminada ✔️")
        except Exception as e:
            session.rollback()
            logger.error(f"Error: actualización asignacion: {e}")

        return None

    logger.info("Maestro pendiente. ✖️")
    return None

async def registra_pmu(file: UploadFile, session: Annotated[Session, Depends(database.get_session)], bgtask: BackgroundTasks):
    bgtask.add_task(task, file, session)

    return JSONResponse(
        content=jsonable_encoder(
            {"status": "procesando"}
        ),
        status_code=status.HTTP_200_OK
    )
