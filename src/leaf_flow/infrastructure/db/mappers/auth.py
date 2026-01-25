from leaf_flow.domain.entities.auth import RefreshTokenEntity
from leaf_flow.infrastructure.db.models import RefreshToken as RefreshTokenModel


def map_refresh_token_model_to_entity(m: RefreshTokenModel) -> RefreshTokenEntity:
    return RefreshTokenEntity(
        id=m.id,
        user_id=m.user_id,
        token=m.token,
        expires_at=m.expires_at,
        revoked=m.revoked,
        revoked_at=getattr(m, "revoked_at", None),
    )
