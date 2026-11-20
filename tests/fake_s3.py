"""A small in-memory S3 client for the migration tests (listing, get, copy, delete)."""
import io
import json


class _Paginator:
    def __init__(self, client):
        self.client = client

    def paginate(self, Bucket, Prefix, Delimiter=None):
        contents = []
        for key, (size, etag, _) in sorted(self.client.objects.items()):
            if not key.startswith(Prefix):
                continue
            if Delimiter and Delimiter in key[len(Prefix):]:
                continue
            contents.append({"Key": key, "Size": size, "ETag": f'"{etag}"'})
        yield {"Contents": contents}


class FakeS3:
    def __init__(self):
        self.objects: dict[str, tuple[int, str, bytes]] = {}
        self.deleted: list[str] = []

    def put(self, key, body=b"x", etag=None):
        if isinstance(body, dict):
            body = json.dumps(body).encode()
        self.objects[key] = (len(body), etag or f"e{hash(body) & 0xffff:x}", body)

    def get_paginator(self, name):
        return _Paginator(self)

    def get_object(self, Bucket, Key):
        return {"Body": io.BytesIO(self.objects[Key][2])}

    def delete_object(self, Bucket, Key):
        self.deleted.append(Key)
        self.objects.pop(Key, None)
