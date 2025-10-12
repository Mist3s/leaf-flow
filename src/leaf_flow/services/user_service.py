from leaf_flow.infrastructure.db.uow import UoW

async def create_user(email: str, name: str | None, uow: UoW):
    user = await uow.users.add(uow.users.model(email=email, name=name))
    await uow.commit()
    return user
