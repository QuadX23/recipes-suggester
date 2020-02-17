from typing import List

from pydantic import BaseModel, Extra, constr, conint


class RecipeItem(BaseModel):
    item: constr(min_length=2)
    q: conint(gt=0)


class ItemsValidator(BaseModel):
    items: List[RecipeItem]

    class Config:
        extra = Extra.forbid
