from fastapi import APIRouter, File, UploadFile

from app.integrations.outbound import proxy_media_upload
from app.schemas.vehicle_schema import MediaUploadResponse

router = APIRouter()


@router.post("/upload", response_model=MediaUploadResponse)
def media_upload(file: UploadFile = File(...)) -> MediaUploadResponse:
    raw = file.file.read()
    url = proxy_media_upload(raw, file.filename or "upload", file.content_type)
    return MediaUploadResponse(url=url)
