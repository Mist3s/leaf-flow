from leaf_flow_core.entities.user import UserEntity
from leaf_flow_core.models.users import User as UserModel


def map_user_model_to_entity(user: UserModel) -> UserEntity:
    return UserEntity(
        id=user.id,
        first_name=user.first_name,
        telegram_id=user.telegram_id,
        email=user.email,
        last_name=user.last_name,
        username=user.username,
        language_code=user.language_code,
        photo_url=user.photo_url,
    )
