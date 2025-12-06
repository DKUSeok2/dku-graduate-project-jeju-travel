"""
Schedule Comments Router - 일정 댓글 API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime

from src.auth.dependencies import get_current_user
from src.database import get_db_session
from src.models.user import User
from src.models.schedule import Schedule
from src.models.schedule_comment import ScheduleComment

router = APIRouter(prefix="/api/schedules", tags=["Schedule Comments"])


class CommentCreate(BaseModel):
    content: str
    parent_id: Optional[int] = None


class CommentResponse(BaseModel):
    id: int
    schedule_id: int
    user_id: int
    user_name: str
    content: str
    parent_id: Optional[int]
    is_deleted: bool
    created_at: str

    class Config:
        from_attributes = True


@router.get("/{schedule_id}/comments", response_model=List[CommentResponse])
async def get_comments(
    schedule_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """
    일정의 댓글 목록 조회
    """
    # 일정 존재 확인
    schedule_res = await db.execute(
        select(Schedule).where(Schedule.id == schedule_id)
    )
    schedule = schedule_res.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다")

    result = await db.execute(
        select(ScheduleComment, User)
        .join(User, ScheduleComment.user_id == User.id)
        .where(ScheduleComment.schedule_id == schedule_id)
        .order_by(ScheduleComment.created_at)
    )
    rows = result.all()
    return [
        CommentResponse(
            id=comment.id,
            schedule_id=comment.schedule_id,
            user_id=comment.user_id,
            user_name=user.name,
            content="삭제된 댓글입니다" if comment.is_deleted else comment.content,
            parent_id=comment.parent_id,
            is_deleted=comment.is_deleted,
            created_at=comment.created_at.isoformat(),
        )
        for comment, user in rows
    ]


@router.post("/{schedule_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    schedule_id: int,
    data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    일정에 댓글 작성
    """
    # 일정 존재 + 공개 여부 체크
    schedule_res = await db.execute(
        select(Schedule).where(Schedule.id == schedule_id)
    )
    schedule = schedule_res.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다")
    
    # 비공개 일정에는 작성자만 댓글 가능
    if not schedule.is_public and schedule.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="비공개 일정에는 댓글을 달 수 없습니다")

    # 대댓글인 경우 부모 댓글 존재 확인
    if data.parent_id:
        parent_res = await db.execute(
            select(ScheduleComment).where(
                ScheduleComment.id == data.parent_id,
                ScheduleComment.schedule_id == schedule_id
            )
        )
        parent = parent_res.scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=404, detail="부모 댓글을 찾을 수 없습니다")

    comment = ScheduleComment(
        schedule_id=schedule_id,
        user_id=current_user.id,
        content=data.content,
        parent_id=data.parent_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return CommentResponse(
        id=comment.id,
        schedule_id=comment.schedule_id,
        user_id=comment.user_id,
        user_name=current_user.name,
        content=comment.content,
        parent_id=comment.parent_id,
        is_deleted=comment.is_deleted,
        created_at=comment.created_at.isoformat(),
    )


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    댓글 삭제 (soft delete)
    """
    res = await db.execute(
        select(ScheduleComment).where(ScheduleComment.id == comment_id)
    )
    comment = res.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다")
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="삭제 권한이 없습니다")

    comment.is_deleted = True
    comment.content = ""  # 실제 내용은 비워둠
    comment.updated_at = datetime.utcnow()
    await db.commit()

