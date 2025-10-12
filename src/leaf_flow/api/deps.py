from fastapi import Depends
from leaf_flow.infrastructure.db.uow import UoW, get_uow

def uow_dep(uow: UoW = Depends(get_uow)) -> UoW:
    return uow
