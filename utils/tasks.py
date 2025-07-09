from celery import shared_task
from datetime import date
from members.models import Member
from users.models import User
from announcements.models import PushLog

@shared_task
def send_birthday_notifications():
    today = date.today()
    # 오늘 생일인 교인 필터링 (월, 일만 비교)
    birthday_members = Member.objects.filter(
        birth_date__month=today.month,
        birth_date__day=today.day
    )

    if birthday_members.exists():
        message = f"오늘({today}) 생일인 교인: "
        for member in birthday_members:
            message += f"{member.name} "
        # TODO: 실제 알림 (이메일, 푸시 알림 등) 발송 로직 구현
        print(f"[Birthday Notification] {message}")
    else:
        print(f"[Birthday Notification] 오늘 생일인 교인이 없습니다.")

@shared_task
def auto_promote_members():
    # TODO: 자동 진급 로직 구현
    # 예: 매년 1월 1일, 연령 기준에 따라 부서 이동
    print("[Auto Promote] 자동 진급 작업 실행.")

    # 예시: 모든 교인을 대상으로 연령 기반 그룹 재할당
    # for member in Member.objects.all():
    #     # member.birth_date를 기반으로 연령 계산
    #     age = today.year - member.birth_date.year - ((today.month, today.day) < (member.birth_date.month, member.birth_date.day))
    #     # 해당 연령에 맞는 그룹 찾기
    #     target_group = Group.objects.filter(age_min__lte=age, age_max__gte=age, church=member.church).first()
    #     if target_group and member.group != target_group:
    #         member.group = target_group
    #         member.save()

    print("[Auto Promote] 자동 진급 작업 완료.")

@shared_task
def send_push_notification(push_log_id):
    try:
        push_log = PushLog.objects.get(id=push_log_id)
        # TODO: 실제 푸시 알림 발송 로직 구현 (Firebase, FCM 등 연동)
        print(f"[Push Notification] Sending push for Announcement '{push_log.announcement.title}' to user '{push_log.user.username}'. Status: {push_log.status}")
        # 발송 성공 시 상태 업데이트
        # push_log.status = PushLog.PushStatus.SENT
        # push_log.save()
    except PushLog.DoesNotExist:
        print(f"[Push Notification] PushLog with ID {push_log_id} not found.")