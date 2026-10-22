from fastapi import HTTPException


class UploadBodyLimit:
    """Bound multipart spooling as well as the final stored file."""

    def __init__(self, app, max_bytes: int):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "POST" or scope["path"].rstrip("/") != "/api/files":
            return await self.app(scope, receive, send)
        size = 0

        async def limited_receive():
            nonlocal size
            message = await receive()
            size += len(message.get("body", b""))
            if size > self.max_bytes:
                raise HTTPException(413, "Upload request is too large.")
            return message

        await self.app(scope, limited_receive, send)
