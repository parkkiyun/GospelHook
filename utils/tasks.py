"""
GospelHook 자동화 태스크 모듈
Celery를 이용한 백그라운드 작업들
"""
from celery import shared_task
from django.utils import timezone
from datetime import date, timedelta
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_birthday_notifications():
    """
    오늘 생일인 교인들에게 생일 축하 알림 발송
    교회 관리자들에게 알림
    """
    from members.models import Member
    from users.models import ChurchUser
    from announcements.models import Announcement, PushLog
    
    today = date.today()
    birthday_members = Member.objects.filter(
        birth_date__month=today.month,
        birth_date__day=today.day
    ).select_related('church')
    
    total_sent = 0
    
    for member in birthday_members:
        try:
            church = member.church
            
            # 교회 관리자들에게 알림
            church_admins = ChurchUser.objects.filter(
                church=church,
                role__in=['CHURCH_ADMIN', 'CHURCH_STAFF']
            ).select_related('user')
            
            # 생일 축하 공지사항 생성
            announcement = Announcement.objects.create(
                church=church,
                title=f"🎉 {member.name}님 생일을 축하합니다!",
                content=f"오늘은 {member.name}님의 생일입니다. 함께 축하해주세요!",
                visible_roles=['CHURCH_ADMIN', 'CHURCH_STAFF', 'MEMBER'],
                push_enabled=True
            )
            
            # 관리자들에게 푸시 알림 로그 생성
            for church_admin in church_admins:
                PushLog.objects.create(
                    announcement=announcement,
                    user=church_admin.user,
                    status='SENT'
                )
                total_sent += 1
                
            logger.info(f"Birthday notification sent for {member.name} in {church.name}")
            
        except Exception as e:
            logger.error(f"Failed to send birthday notification for {member.name}: {str(e)}")
    
    logger.info(f"Birthday notifications completed. Total sent: {total_sent}")
    return f"Birthday notifications sent to {total_sent} recipients"


@shared_task
def auto_promote_members():
    """
    연령에 따른 교인 자동 승급
    아동부 -> 청소년부 -> 청년부 -> 장년부
    """
    from members.models import Member
    from groups.models import Group, GroupMember
    
    today = date.today()
    promoted_count = 0
    
    # 승급 규칙 정의
    promotion_rules = [
        {'from_age': 13, 'to_age': 19, 'from_type': 'CHILDREN', 'to_type': 'YOUTH'},
        {'from_age': 20, 'to_age': 29, 'from_type': 'YOUTH', 'to_type': 'YOUNG_ADULT'},
        {'from_age': 30, 'to_age': None, 'from_type': 'YOUNG_ADULT', 'to_type': 'ADULT'},
    ]
    
    for rule in promotion_rules:
        # 승급 대상 찾기 (생년월일 기반 나이 계산)
        members_to_promote = Member.objects.filter(
            birth_date__isnull=False
        )
        
        for member in members_to_promote:
            # 나이 계산
            age = today.year - member.birth_date.year
            if today < member.birth_date.replace(year=today.year):
                age -= 1
            
            # 승급 조건 확인
            if age >= rule['from_age'] and (rule['to_age'] is None or age <= rule['to_age']):
                try:
                    # 현재 소속 그룹 확인
                    current_group_membership = GroupMember.objects.filter(
                        member=member,
                        group__group_type=rule['from_type'],
                        is_active=True
                    ).first()
                    
                    if current_group_membership:
                        # 승급할 그룹 찾기
                        target_group = Group.objects.filter(
                            church=member.church,
                            group_type=rule['to_type'],
                            management_type='AUTO',
                            is_active=True
                        ).first()
                        
                        if target_group and not target_group.is_full:
                            # 기존 그룹에서 제외
                            current_group_membership.is_active = False
                            current_group_membership.save()
                            
                            # 새 그룹에 추가
                            GroupMember.objects.create(
                                group=target_group,
                                member=member,
                                role='MEMBER',
                                joined_date=today,
                                is_active=True
                            )
                            
                            promoted_count += 1
                            logger.info(
                                f"Promoted {member.name} from {rule['from_type']} to {rule['to_type']}"
                            )
                            
                except Exception as e:
                    logger.error(f"Failed to promote {member.name}: {str(e)}")
    
    logger.info(f"Auto promotion completed. Total promoted: {promoted_count}")
    return f"Auto promoted {promoted_count} members"


@shared_task
def generate_attendance_reminders():
    """
    출석 독려 알림 생성
    최근 4주간 출석률이 낮은 교인들에게 알림
    """
    from members.models import Member
    from attendance.models import Attendance
    from announcements.models import Announcement
    
    four_weeks_ago = date.today() - timedelta(weeks=4)
    reminder_count = 0
    
    # 교회별로 처리
    from church.models import Church
    churches = Church.objects.filter(is_active=True)
    
    for church in churches:
        # 최근 4주간 출석률 계산
        members = Member.objects.filter(church=church)
        
        for member in members:
            recent_attendances = Attendance.objects.filter(
                member=member,
                date__gte=four_weeks_ago,
                status__in=['present', 'late']
            ).count()
            
            total_services = Attendance.objects.filter(
                member=member,
                date__gte=four_weeks_ago
            ).count()
            
            if total_services > 0:
                attendance_rate = (recent_attendances / total_services) * 100
                
                # 출석률이 50% 미만인 경우 독려 알림
                if attendance_rate < 50:
                    try:
                        # 관리자용 알림 생성
                        Announcement.objects.create(
                            church=church,
                            title=f"📢 {member.name}님 출석 독려 필요",
                            content=f"{member.name}님의 최근 4주 출석률이 {attendance_rate:.1f}%입니다. 관심과 돌봄이 필요합니다.",
                            visible_roles=['CHURCH_ADMIN', 'CHURCH_STAFF'],
                            push_enabled=False
                        )
                        reminder_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to create attendance reminder for {member.name}: {str(e)}")
    
    logger.info(f"Attendance reminders completed. Total created: {reminder_count}")
    return f"Created {reminder_count} attendance reminders"


@shared_task
def cleanup_old_push_logs():
    """
    오래된 푸시 알림 로그 정리 (3개월 이상)
    """
    from announcements.models import PushLog
    
    three_months_ago = timezone.now() - timedelta(days=90)
    deleted_count, _ = PushLog.objects.filter(
        sent_at__lt=three_months_ago
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} old push logs")
    return f"Cleaned up {deleted_count} old push logs"


@shared_task
def send_push_notification(push_log_id):
    """실제 푸시 알림 발송"""
    from announcements.models import PushLog
    
    try:
        push_log = PushLog.objects.get(id=push_log_id)
        
        # TODO: 실제 푸시 알림 발송 로직 구현 (Firebase FCM 등)
        logger.info(f"Sending push notification: {push_log.announcement.title} to {push_log.user.username}")
        
        # 발송 성공 시 상태 업데이트
        push_log.status = 'SENT'
        push_log.save()
        
        return f"Push notification sent to {push_log.user.username}"
        
    except PushLog.DoesNotExist:
        logger.error(f"PushLog with ID {push_log_id} not found")
        return f"PushLog {push_log_id} not found"


@shared_task
def check_system_health():
    """
    시스템 상태 점검
    데이터베이스 연결, 외부 서비스 상태 등 확인
    """
    health_status = {
        'database': False,
        'disk_usage': 0,
        'memory_usage': 0,
        'timestamp': timezone.now().isoformat()
    }
    
    try:
        # 데이터베이스 연결 테스트
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status['database'] = True
            
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
    
    # 시스템 리소스 체크
    try:
        import psutil
        health_status['disk_usage'] = psutil.disk_usage('/').percent
        health_status['memory_usage'] = psutil.virtual_memory().percent
        
    except ImportError:
        logger.warning("psutil not available for system resource monitoring")
    except Exception as e:
        logger.error(f"System resource check failed: {str(e)}")
    
    # 중요한 문제가 있는 경우 알림
    if not health_status['database']:
        logger.critical("Database connection failed!")
    
    if health_status['disk_usage'] > 85:
        logger.warning(f"High disk usage: {health_status['disk_usage']}%")
    
    if health_status['memory_usage'] > 85:
        logger.warning(f"High memory usage: {health_status['memory_usage']}%")
    
    logger.info(f"System health check completed: {health_status}")
    return health_status