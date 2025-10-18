from sqlalchemy.orm import Session
from leaf_flow.infrastructure.db.models.users import User
from leaf_flow.infrastructure.db.repositories.base import Repository

class UserRepository(Repository[User]):
    def __init__(self, session: Session):
        super().__init__(session, User)
