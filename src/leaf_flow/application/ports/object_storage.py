from typing import BinaryIO, Protocol


class ObjectStorage(Protocol):
    def put_file_obj(
        self,
        *,
        key: str,
        file_obj: BinaryIO,
        content_type: str,
        cache_control: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> None: ...

    def put_bytes(
        self,
        *,
        key: str,
        data: bytes,
        content_type: str,
        cache_control: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> None: ...

    def get_stream(self, *, key: str) -> BinaryIO: ...

    def delete(self, *, key: str) -> None: ...

    def exists(self, *, key: str) -> bool: ...
