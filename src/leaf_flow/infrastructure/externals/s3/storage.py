from typing import BinaryIO

from botocore.exceptions import ClientError

from leaf_flow.application.ports.object_storage import ObjectStorage
from leaf_flow.infrastructure.externals.s3.client import make_s3_client
from leaf_flow.config import settings


class S3ObjectStorage(ObjectStorage):
    def __init__(self) -> None:
        self._bucket = settings.S3_BUCKET
        self._client = make_s3_client()

    def put_file_obj(
        self,
        *,
        key: str,
        file_obj: BinaryIO,
        content_type: str,
        cache_control: str | None = None,
        metadata: dict[str, str] | None = None
    ) -> None:
        extra_args: dict[str, object] = {"ContentType": content_type}
        if cache_control:
            extra_args["CacheControl"] = cache_control
        if metadata:
            extra_args["Metadata"] = metadata

        self._client.upload_fileobj(
            Fileobj=file_obj,
            Bucket=self._bucket,
            Key=key,
            ExtraArgs=extra_args,
        )

    def put_bytes(
        self,
        *,
        key: str,
        data: bytes,
        content_type: str,
        cache_control: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> None:
        args: dict[str, object] = {
            "Bucket": self._bucket,
            "Key": key,
            "Body": data,
            "ContentType": content_type,
        }
        if cache_control:
            args["CacheControl"] = cache_control
        if metadata:
            args["Metadata"] = metadata

        self._client.put_object(**args)

    def get_stream(self, *, key: str) -> BinaryIO:
        obj = self._client.get_object(Bucket=self._bucket, Key=key)
        return obj["Body"]

    def delete(self, *, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)

    def exists(self, *, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code")
            if code in ("404", "NoSuchKey", "NotFound"):
                return False
            raise
