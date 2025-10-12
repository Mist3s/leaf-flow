from sqlalchemy.orm import Session
from ..models.users import User
from .base import Repository

class UserRepository(Repository[User]):
    def __init__(self, session: Session):
        super().__init__(session, User)
