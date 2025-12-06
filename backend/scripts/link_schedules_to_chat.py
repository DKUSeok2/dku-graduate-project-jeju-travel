"""
채팅 세션과 일정을 연결하는 Mock 데이터 스크립트
기존 일정에 대해 채팅 세션을 생성하고 연결합니다.
"""
import asyncio
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db_session, ChatSession
from src.models.user import User
from src.models.schedule import Schedule


async def link_schedules_to_chat_sessions():
    """기존 일정에 채팅 세션을 생성하고 연결"""
    async for db in get_db_session():
        print("🔗 일정과 채팅 세션 연결 시작...")

        # chat_session_id가 없는 일정 조회
        result = await db.execute(
            select(Schedule, User)
            .join(User, Schedule.user_id == User.id)
            .where(Schedule.chat_session_id == None)
        )
        schedules_and_users = result.all()

        if not schedules_and_users:
            print("✅ 연결할 일정이 없습니다.")
            return

        print(f"📋 {len(schedules_and_users)}개의 일정을 발견했습니다.")

        for schedule, user in schedules_and_users:
            print(f"\n📝 일정 '{schedule.title}' 처리 중...")

            # 1. 채팅 세션 생성
            session_id = str(uuid.uuid4())
            
            # 일정 제목에서 대화 제목 생성
            chat_title = f"{schedule.title}"
            
            # 채팅 메시지 생성 (chat_history가 있으면 사용, 없으면 기본 메시지)
            messages = schedule.chat_history if schedule.chat_history else [
                {
                    "role": "assistant",
                    "content": "안녕하세요! 🍊\n제주 여행 계획을 도와드릴게요.\n\n어떤 여행을 원하시나요?",
                    "timestamp": datetime.utcnow().isoformat()
                },
                {
                    "role": "user",
                    "content": f"{schedule.title} 일정을 추천해주세요.",
                    "timestamp": datetime.utcnow().isoformat()
                },
                {
                    "role": "assistant",
                    "content": f"좋습니다! {schedule.title}을 계획해드리겠습니다 🎉",
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]

            # 채팅 세션 객체 생성
            chat_session = ChatSession(
                user_id=user.id,
                session_id=session_id,
                title=chat_title,
                messages=messages,
                context={
                    "schedule_id": schedule.id,
                    "schedule_title": schedule.title
                },
                is_active=True,
                created_at=schedule.created_at,
                updated_at=schedule.updated_at
            )

            db.add(chat_session)

            # 2. 일정에 chat_session_id 연결
            schedule.chat_session_id = session_id

            print(f"   ✅ 채팅 세션 생성: {session_id}")
            print(f"   ✅ 일정 '{schedule.title}'에 연결 완료")

        try:
            await db.commit()
            print(f"\n🎉 {len(schedules_and_users)}개의 일정이 성공적으로 채팅 세션에 연결되었습니다!")
        except Exception as e:
            await db.rollback()
            print(f"\n❌ 오류 발생: {e}")

        print("\n✨ 완료!")


if __name__ == "__main__":
    asyncio.run(link_schedules_to_chat_sessions())


