from pydantic import BaseModel


class ExtendedBaseModel(BaseModel):

    class Config:
        populate_by_name = True
