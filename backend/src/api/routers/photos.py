"""
Schedule Photos Router - 일정 사진 업로드 API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel
from datetime import datetime
import os
from uuid import uuid4

from src.auth.dependencies import get_current_user
from src.database import get_db_session
from src.models.user import User
from src.models.schedule import Schedule
from src.models.schedule_photo import SchedulePhoto

router = APIRouter(prefix="/api/schedules", tags=["Schedule Photos"])

# 업로드 디렉토리 설정
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads", "schedule_photos")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 허용 확장자 및 최대 크기
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


class PhotoResponse(BaseModel):
    id: int
    schedule_id: int
    user_id: int
    url: str
    caption: Optional[str]
    day: Optional[int]
    order_in_day: Optional[int]
    created_at: str

    class Config:
        from_attributes = True


@router.get("/{schedule_id}/photos", response_model=List[PhotoResponse])
async def get_schedule_photos(
    schedule_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """
    일정의 사진 목록 조회
    """
    # 일정 존재 확인
    schedule_res = await db.execute(
        select(Schedule).where(Schedule.id == schedule_id)
    )
    schedule = schedule_res.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다")

    result = await db.execute(
        select(SchedulePhoto)
        .where(SchedulePhoto.schedule_id == schedule_id)
        .order_by(SchedulePhoto.day, SchedulePhoto.order_in_day, SchedulePhoto.created_at)
    )
    photos = result.scalars().all()
    
    return [
        PhotoResponse(
            id=photo.id,
            schedule_id=photo.schedule_id,
            user_id=photo.user_id,
            url=photo.url,
            caption=photo.caption,
            day=photo.day,
            order_in_day=photo.order_in_day,
            created_at=photo.created_at.isoformat(),
        )
        for photo in photos
    ]


@router.post("/{schedule_id}/photos", response_model=PhotoResponse)
async def upload_schedule_photo(
    schedule_id: int,
    file: UploadFile = File(...),
    caption: Optional[str] = Form(None),
    day: Optional[int] = Form(None),
    order_in_day: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    일정에 사진 업로드
    """
    # 일정 존재 확인
    res = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = res.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다")
    
    # 공유된 추천코스는 사진 업로드 불가
    if schedule.is_public:
        raise HTTPException(status_code=403, detail="공유된 코스에는 사진을 업로드할 수 없습니다")
    
    # 작성자만 업로드 가능
    if schedule.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="사진을 업로드할 권한이 없습니다")

    # 파일 확장자 검증
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"허용되지 않는 파일 형식입니다. 허용: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 파일 크기 검증
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="파일 크기는 5MB 이하여야 합니다")

    # 파일 저장
    filename = f"{uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(contents)

    # URL 생성 (정적 파일 서빙 경로)
    url = f"/uploads/schedule_photos/{filename}"

    # DB 저장
    photo = SchedulePhoto(
        schedule_id=schedule_id,
        user_id=current_user.id,
        url=url,
        caption=caption,
        day=day,
        order_in_day=order_in_day,
        created_at=datetime.utcnow(),
    )
    db.add(photo)
    await db.commit()
    await db.refresh(photo)

    return PhotoResponse(
        id=photo.id,
        schedule_id=photo.schedule_id,
        user_id=photo.user_id,
        url=photo.url,
        caption=photo.caption,
        day=photo.day,
        order_in_day=photo.order_in_day,
        created_at=photo.created_at.isoformat(),
    )


@router.delete("/{schedule_id}/photos/{photo_id}", status_code=204)
async def delete_schedule_photo(
    schedule_id: int,
    photo_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    사진 삭제
    """
    # 일정 확인
    schedule_res = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = schedule_res.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다")
    
    # 공유된 추천코스는 사진 삭제 불가
    if schedule.is_public:
        raise HTTPException(status_code=403, detail="공유된 코스의 사진은 삭제할 수 없습니다")
    
    res = await db.execute(
        select(SchedulePhoto).where(
            SchedulePhoto.id == photo_id,
            SchedulePhoto.schedule_id == schedule_id
        )
    )
    photo = res.scalar_one_or_none()
    if not photo:
        raise HTTPException(status_code=404, detail="사진을 찾을 수 없습니다")
    
    if photo.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="삭제 권한이 없습니다")

    # 파일 삭제
    filename = photo.url.split("/")[-1]
    filepath = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    # DB에서 삭제
    await db.execute(delete(SchedulePhoto).where(SchedulePhoto.id == photo_id))
    await db.commit()

