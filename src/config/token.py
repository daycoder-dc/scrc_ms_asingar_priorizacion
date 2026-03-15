from typing import Annotated
from fastapi import Header, HTTPException, Depends, status
from src.config.settings import get_setting, Settings

async def get_token_header(x_api_key: Annotated[str, Header()], settings: Annotated[Settings, Depends(get_setting)]):
    if x_api_key != settings.app_api_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="403 FORBIDDEN")