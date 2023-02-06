from pydantic import BaseModel

from .companies import Company


class Database(BaseModel):
    companies: list[Company]
