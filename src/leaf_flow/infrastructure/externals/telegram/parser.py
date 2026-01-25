import json
from urllib.parse import parse_qsl

from leaf_flow.application.auth.exceptions import InvalidInitData
from leaf_flow.application.dto.telegram import TelegramUserData


def parse_telegram_init_data(init_data: str) -> TelegramUserData:
    data = dict(parse_qsl(init_data))
    raw = json.loads(data["user"])

    if not raw:
        raise InvalidInitData("INVALID_INIT_DATA")

    return TelegramUserData(
        telegram_id=raw["id"],
        first_name=raw["first_name"],
        last_name=raw.get("last_name"),
        username=raw.get("username"),
        language_code=raw.get("language_code"),
        photo_url=raw.get("photo_url")
    )


def parse_telegram_widget_data(widget_data: dict) -> TelegramUserData:
    return TelegramUserData(
        telegram_id=widget_data["id"],
        first_name=widget_data["first_name"],
        last_name=widget_data.get("last_name"),
        username=widget_data.get("username"),
        language_code=widget_data.get("language_code"),
        photo_url=widget_data.get("photo_url")
    )
