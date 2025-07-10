# GospelHook - 교회 통합 관리 시스템

교회의 교인 정보, 출석, 기도제목, 예배, 교육, 공지사항, 봉사 신청 등 사역 전반을 통합 관리하는 백오피스 시스템입니다.

## 주요 기능

- 🏛️ **다중 교회 지원**: 멀티 테넌시 구조로 여러 교회가 하나의 시스템을 사용 가능
- 👥 **교인 관리**: 교인 정보, 가족 관계, 부서 배정 자동화
- 📊 **출석 관리**: 예배별 출석 체크 및 통계
- 🙏 **기도 제목**: 교인별 기도 제목 관리 및 공유
- 📢 **공지사항**: 교회 공지사항 및 알림 시스템
- 🎓 **교육 프로그램**: 교육 과정 관리 및 신청
- 🤝 **봉사 신청**: 봉사 활동 관리 및 신청
- 📈 **통계 리포트**: 다양한 교회 활동 통계 제공

## 기술 스택

- **백엔드**: Python 3.11, Django 4.x, Django REST Framework
- **데이터베이스**: PostgreSQL (개발: SQLite3)
- **인증**: JWT (SimpleJWT)
- **비동기 작업**: Celery + Redis
- **파일 저장**: AWS S3 / 로컬 스토리지
- **API 문서**: drf-spectacular (Swagger/ReDoc)

## 빠른 시작

### 요구사항

- Python 3.11 이상
- pip 또는 Poetry
- Redis (Celery 사용 시)

### 설치 및 실행

1. 저장소 클론
```bash
git clone https://github.com/yourusername/GospelHook.git
cd GospelHook
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 열어 필요한 값들을 설정하세요
```

5. 데이터베이스 마이그레이션
```bash
python manage.py migrate
```

6. 슈퍼유저 생성
```bash
python manage.py createsuperuser
```

7. 개발 서버 실행
```bash
python manage.py runserver
```

8. API 문서 확인
- Swagger UI: http://localhost:8000/api/schema/swagger-ui/
- ReDoc: http://localhost:8000/api/schema/redoc/

## 프로젝트 구조

```
GospelHook/
├── church_core/        # 프로젝트 설정 및 공통 모듈
├── church/            # 교회 정보 및 설정
├── users/             # 사용자 및 권한 관리
├── members/           # 교인 정보 관리
├── groups/            # 부서, 구역, 찬양대 등
├── attendance/        # 예배 출석 관리
├── prayers/           # 기도 제목 관리
├── carelog/           # 생활소식, 병문안 등
├── bulletins/         # 주보 업로드/열람
├── worship/           # 예배 기록
├── education/         # 교육 프로그램
├── announcements/     # 공지사항/알림
├── surveys/           # 설문/피드백
├── volunteering/      # 봉사 신청
├── offerings/         # 헌금 기록
├── bible/             # 성경 관련 기능
├── reports/           # 통계 리포트
└── utils/             # 유틸리티 (자동화 작업 등)
```

## 권한 시스템

- **슈퍼관리자**: 전체 시스템 관리
- **교회 관리자**: 소속 교회 전체 관리
- **교회 스태프**: 특정 기능 관리
- **일반 교인**: 개인 정보 조회 및 제한적 기능 사용

## 개발 가이드

자세한 개발 가이드는 [Guide.md](./Guide.md) 파일을 참조하세요.

### 테스트 실행

```bash
pytest
```

### 코드 스타일 검사

```bash
flake8 .
black . --check
```

## 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 문의

프로젝트 관리자 - 박기윤

프로젝트 링크: [https://github.com/yourusername/GospelHook](https://github.com/yourusername/GospelHook)