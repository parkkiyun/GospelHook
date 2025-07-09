# 📘 교회 교적부 시스템 백엔드 개발 가이드
버전: v2.2 (내용 복원 및 상세화)
작성자: 박기윤
작성일: 2025.07.09

---

## ✅ 프로젝트 개요

이 시스템은 교회의 교인 정보, 출석, 기도제목, 예배, 교육, 공지사항, 봉사 신청 등 **사역 전반을 통합 관리**할 수 있는 백오피스입니다.
Django 기반으로 개발되며, **다중 교회가 사용할 수 있는 멀티 테넌시 구조**, **직책 기반 권한 관리**, **자동 부서 이동**, **알림 자동화** 등 실무에 최적화된 기능을 포함합니다.

---

## 🧱 기술 스택

| 항목 | 선택 |
|------|------|
| 언어 | Python 3.11 |
| 프레임워크 | Django 4.x, Django REST Framework |
| DB | PostgreSQL |
| 인증 | JWT 기반 토큰 인증 (SimpleJWT) |
| 미디어 저장 | AWS S3 또는 로컬 MEDIA_ROOT |
| 배포 | AWS EC2 + RDS / Railway / PythonAnywhere 등 |

---

## 🚀 로컬 개발 환경 설정 (Local Development Setup)

개발을 시작하기 위해 다음 단계를 따르세요.

1.  **저장소 복제**
    ```bash
    git clone <repository_url>
    cd GospelHook
    ```

2.  **가상 환경 생성 및 활성화**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # macOS / Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **라이브러리 설치**
    ```bash
    pip install -r requirements.txt
    ```

4.  **환경 변수 설정**
    - 프로젝트 루트의 `.env.example` 파일을 복사하여 `.env` 파일을 생성합니다.
    - `.env` 파일 내의 각 변수 값을 자신의 개발 환경에 맞게 수정합니다.
    ```bash
    cp .env.example .env
    ```
    **`.env.example` 예시:**
    ```ini
    SECRET_KEY='your-super-secret-key'
    DEBUG=True
    DATABASE_URL='postgres://user:password@localhost:5432/gospelhook_db'
    # AWS_ACCESS_KEY_ID=''
    # AWS_SECRET_ACCESS_KEY=''
    # AWS_STORAGE_BUCKET_NAME=''
    ```

5.  **데이터베이스 마이그레이션**
    ```bash
    python manage.py migrate
    ```

6.  **최초 관리자(Superuser) 생성**
    ```bash
    python manage.py createsuperuser
    ```

7.  **개발 서버 실행**
    ```bash
    python manage.py runserver
    ```
    서버 실행 후 `http://127.0.0.1:8000/` 주소로 접속하여 확인할 수 있습니다.

---

## 🗂 핵심 앱 구조 제안

```
church_core/
├── church/               # 교회 정보 및 설정
├── members/              # 교인 모델 (프로필 사진 포함)
├── groups/               # 부서, 구역, 찬양대 등
├── users/                # 사용자 및 권한
├── attendance/           # 예배 출석
├── prayers/              # 기도제목
├── carelog/              # 생활소식, 병문안 등
├── bulletins/            # 주보 업로드/열람
├── worship/              # 예배 기록
├── education/            # 교육 프로그램/신청
├── announcements/        # 공지사항 / 알림
├── surveys/              # 설문/피드백
├── volunteering/         # 봉사 신청
├── utils/                # 자동 진급, 생일 알림 등
```

---

## 🧾 상세 모델 정의 (Detailed Model Definition)

Django 모델 필드를 기준으로 상세 속성을 정의합니다.

- `church = models.ForeignKey(Church, on_delete=models.CASCADE)`는 모든 모델에 공통으로 포함됩니다.

| 모델 | 필드 | 타입 | 설명 |
| :--- | :--- | :--- | :--- |
| **Church** | `name` | `CharField(max_length=100)` | 교회 이름 |
| | `timezone` | `CharField(max_length=50, default='Asia/Seoul')` | 시간대 |
| | `settings` | `JSONField(default=dict)` | 교회별 커스텀 설정 |
| **Member** | `name` | `CharField(max_length=50)` | 교인 이름 |
| | `gender` | `CharField(choices=[('M', '남'), ('F', '여')])` | 성별 |
| | `birth_date` | `DateField(null=True)` | 생년월일 |
| | `profile_image`| `ImageField(upload_to='profiles/')` | 프로필 사진 |
| | `group` | `ForeignKey(Group, on_delete=models.SET_NULL, null=True)` | 소속 부서/그룹 |
| **User** | `email` | `EmailField(unique=True)` | 사용자 이메일 (ID) |
| | `role` | `CharField(choices=[('ADMIN', '교역자'), ...])` | 직책(권한) |
| | `related_member`| `OneToOneField(Member, on_delete=models.SET_NULL, null=True)` | 연결된 교인 정보 |
| **Group** | `name` | `CharField(max_length=100)` | 그룹 이름 |
| | `type` | `CharField(choices=[('AUTO', '자동'), ('MANUAL', '수동')])` | 그룹 유형 |
| **Attendance**| `member` | `ForeignKey(Member, on_delete=models.CASCADE)` | 출석 대상 교인 |
| | `status` | `CharField(choices=[('PRESENT', '출석'), ...])` | 출석 상태 |
| | `worship_type`| `CharField(max_length=50)` | 대상 예배 (주일, 수요 등) |
| **CareLog** | `member` | `ForeignKey(Member, on_delete=models.CASCADE)` | 대상 교인 |
| | `type` | `CharField(choices=[('PRAYER', '기도'), ...])` | 기록 종류 |
| | `content` | `TextField()` | 상세 내용 |

*(나머지 모델들도 위와 같은 형식으로 구체화 필요)*

---

## 🏛️ 멀티 테넌시 아키텍처 (Multi-tenancy Architecture)

이 시스템은 **Shared Database, Shared Schema** 방식을 채택하여 멀티 테넌시를 구현합니다. 이 방식은 개발 효율성과 비용 효율성이 가장 뛰어납니다.

- **구현 전략**: 모든 데이터 모델(Member, Group 등)에 `church (ForeignKey)` 필드를 포함하여 데이터를 구분합니다.
- **데이터 격리**: 사용자의 요청에서 `church_id`를 추출하여, 모든 데이터베이스 쿼리(QuerySet)가 해당 교회의 데이터에만 접근하도록 필터링하는 로직을 API의 기본 권한 클래스 또는 믹스인(Mixin)에 구현합니다. 이를 통해 데이터 유출 위험을 원천적으로 차단하고 안정성을 확보합니다.

---

## 🌐 API 엔드포인트 명세 (API Endpoint Specification)

API는 버전 관리를 위해 URL에 `v1`을 포함하며, 멀티 테넌시 데이터 격리를 위해 `church_id`를 경로 파라미터로 사용합니다.

| 기능 | HTTP Method | URL | 주요 역할 |
| :--- | :--- | :--- | :--- |
| **인증 (Auth)** | `POST` | `/api/v1/auth/token/` | 로그인 (Access/Refresh 토큰 발급) |
| | `POST` | `/api/v1/auth/token/refresh/` | Access 토큰 갱신 |
| | `GET` | `/api/v1/auth/me/` | 내 정보 확인 |
| **교회 (Church)** | `GET` | `/api/v1/churches/{church_id}/` | 소속 교회 정보 조회 |
| **교인 (Member)** | `GET`, `POST` | `/api/v1/churches/{church_id}/members/` | 교인 목록 조회, 신규 교인 등록 |
| | `GET`, `PUT`, `PATCH`, `DELETE` | `/api/v1/churches/{church_id}/members/{member_id}/` | 특정 교인 정보 조회, 수정, 삭제 |
| **그룹 (Group)** | `GET`, `POST` | `/api/v1/churches/{church_id}/groups/` | 그룹(부서, 구역 등) 목록 조회, 생성 |
| | `GET`, `PUT`, `DELETE` | `/api/v1/churches/{church_id}/groups/{group_id}/` | 특정 그룹 정보 수정, 삭제 |
| **출석 (Attendance)** | `GET`, `POST` | `/api/v1/churches/{church_id}/attendance/` | 출석 기록 조회, 생성 |
| **기도제목 (Prayer)** | `GET`, `POST` | `/api/v1/churches/{church_id}/prayers/` | 기도제목 목록 조회, 생성 |
| **심방/소식 (CareLog)**| `GET`, `POST` | `/api/v1/churches/{church_id}/care-logs/` | 심방/소식 기록 조회, 생성 |
| **주보 (Bulletin)** | `GET`, `POST` | `/api/v1/churches/{church_id}/bulletins/` | 주보 목록 조회, 업로드 |
| **교육 (Education)** | `GET`, `POST` | `/api/v1/churches/{church_id}/education/programs/` | 교육 프로그램 조회, 생성 |
| **공지 (Announcement)**| `GET`, `POST` | `/api/v1/churches/{church_id}/announcements/` | 공지사항 목록 조회, 생성 |
| **통계 (Statistics)** | `GET` | `/api/v1/churches/{church_id}/stats/attendance/` | 출석 통계 리포트 |

---

## 🔑 상세 인증 흐름 (Detailed Authentication Flow)

본 시스템은 JWT(JSON Web Token)를 사용하여 인증을 처리하며, 상세 흐름은 다음과 같습니다.

1.  **로그인**: 사용자가 이메일/비밀번호를 `/api/v1/auth/token/`으로 전송합니다.
2.  **토큰 발급**: 서버는 인증 성공 시, `Access Token`(유효기간 1시간)과 `Refresh Token`(유효기간 1주일)을 발급하여 응답합니다.
3.  **API 요청**: 클라이언트는 발급받은 `Access Token`을 `Authorization: Bearer <token>` HTTP 헤더에 담아 API를 요청합니다.
4.  **토큰 검증**: 서버는 API 요청을 받을 때마다 헤더의 `Access Token`을 검증하여 사용자를 식별하고 권한을 확인합니다.
5.  **토큰 갱신**: `Access Token`이 만료되면(401 Unauthorized 에러 발생), 클라이언트는 보관하고 있던 `Refresh Token`을 `/api/v1/auth/token/refresh/`로 보내 새로운 `Access Token`을 발급받습니다.

---

## ⚠️ 에러 응답 형식 (Error Response Format)

API의 모든 에러 응답은 일관된 JSON 구조를 따릅니다.

**에러 응답 예시:**
```json
{
  "errors": [
    {
      "status_code": 400,
      "error_code": "VALIDATION_ERROR",
      "message": "입력값이 올바르지 않습니다.",
      "field_errors": {
        "email": ["유효한 이메일 주소를 입력하세요."],
        "birth_date": ["날짜 형식이 YYYY-MM-DD여야 합니다."]
      }
    }
  ]
}
```

---

## 🔐 권한(Role) 기반 접근 제어 (RBAC)

| 직책(Role) | 주요 권한 |
|------------|------------|
| 교역자 | 전체 교인 관리, 교육/예배 생성, 기도/출석 열람 |
| 구역장 | 구역 교인 관리, 출석 및 CareLog 기록 |
| 교사 | 담당 학생 출석 및 CareLog 기록, 교육 신청 |
| 성도 | 본인 정보 확인, 주보 열람, 교육 신청, 봉사 신청 |

→ 모든 API는 `role_required` 데코레이터 또는 커스텀 권한 클래스(`permissions.py`)로 제어

---

## 🔁 자동화 기능

- 생일 알림: 매일 `birth_date`가 오늘인 교인 → 담당자에게 알림
- 자동 진급: 매년 1월, `age_min/max` 조건 기반 부서 이동
- 새가족 관리: 등록 후 1/3개월 등 주기별 리마인드
- 예배 봉사 일정 등록: 찬양대/헌금위원 등 스케줄 자동 구성 (옵션)

---

## 🔔 알림 시스템

- 알림 모델 구성 (`Announcement` + `PushLog`)
- 앱 푸시 (Firebase) 또는 문자 API 연동
- 역할 기반 대상 설정 가능 (예: "찬양대원만 보기")

---

## 📊 통계/리포트 기능

- 예배 출석 통계 (일자별/부서별)
- 교육 신청/수료율
- CareLog 기록 추이
- 새가족 정착 현황

---

## ✅ 개발 단계 제안 (4단계 로드맵)

| 단계 | 기간 | 내용 |
|------|------|------|
| 1단계 | 주차 1~2 | 교회/회원/권한 구조 + 기본 API 구축 |
| 2단계 | 주차 3 | 출석, 기도, CareLog, 교육 API |
| 3단계 | 주차 4 | 예배기록, 주보, 알림, 자동화 구현 |
| 4단계 | 주차 5~6 | 관리자 UI, 통계, 테스트, 문서화

---

## 📎 추천 개발 라이브러리

- `django-environ`: 설정 관리
- `django-storages`: S3 연동
- `drf-yasg` 또는 `drf-spectacular`: Swagger 문서 자동화
- `django-simple-history`: 이력 관리
- `celery`: 생일 알림 등 자동작업 스케줄러
- `django-role-permissions`: RBAC 구현

---

## 🎯 테스트 및 배포 전략

- 테스트: Pytest + FactoryBoy + Mock
- API 문서 자동화: Swagger
- GitHub Actions 또는 Railway CI/CD 추천
- AWS S3 + PostgreSQL + EC2 조합 권장

---

## 📌 부가 기능 (선택적 확장)

- 헌금 기록 모듈 (접근 제한 강력 설정)
- 설문/피드백 기능
- 봉사/사역 신청 시스템
- 성경 본문 자동 입력 (Bible API 연동)

---

## 🧩 확장 가능성

- PWA or React Native 앱 연동 가능
- 멀티교회 SaaS 서비스화 가능 (교회별 도메인 운영)
- 교역자 맞춤 통계 리포트, 설교 히스토리, 일정 연동

---

## 📚 문서화 자료

- ERD 다이어그램 (draw.io/dbdiagram.io)
- API 명세서 (drf-spectacular)
- Figma UI 시안 (반응형 기준)
- 관리자 사용 매뉴얼 (PDF or Notion)

---

문의 및 피드백:  
박기윤 (담당자) / 2025년 6월 기준  
