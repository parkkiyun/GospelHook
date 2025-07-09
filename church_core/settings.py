"""
Django settings for church_core project.
"""
import environ
from pathlib import Path
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# django-environ setup
env = environ.Env(
    DEBUG=(bool, False)
)
environ.Env.read_env(BASE_DIR / '.env')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 3rd Party Apps
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'simple_history',
    'rolepermissions',

    # Local Apps
    'church.apps.ChurchConfig',
    'users.apps.UsersConfig',
    'members.apps.MembersConfig',
    'groups.apps.GroupsConfig',
    'attendance.apps.AttendanceConfig',
    'prayers.apps.PrayersConfig',
    'carelog.apps.CarelogConfig',
    'bulletins.apps.BulletinsConfig',
    'education.apps.EducationConfig',
    'worship.apps.WorshipConfig',
    'announcements.apps.AnnouncementsConfig',
    'volunteering.apps.VolunteeringConfig',
    'utils.apps.UtilsConfig',
    'reports.apps.ReportsConfig',
    'offerings.apps.OfferingsConfig',
    'surveys.apps.SurveysConfig',
    'bible.apps.BibleConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware', # django-simple-history
]

ROOT_URLCONF = 'church_core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'church_core.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Custom User Model
AUTH_USER_MODEL = 'users.User'


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'EXCEPTION_HANDLER': 'church_core.exceptions.custom_exception_handler',
}

# DRF Spectacular (API Docs)
SPECTACULAR_SETTINGS = {
    'TITLE': 'GospelHook API',
    'DESCRIPTION': '교회 교적부 시스템 백엔드 API 문서',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# Simple JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

# Role Permissions
ROLEPERMISSIONS_MODULE = 'church_core.roles'

# Celery Configuration
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='amqp://guest:guest@localhost:5672//')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='rpc://')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Seoul'

# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    'send-birthday-notifications-daily': {
        'task': 'utils.tasks.send_birthday_notifications',
        'schedule': timedelta(days=1), # 매일 실행
    },
    'auto-promote-members-annually': {
        'task': 'utils.tasks.auto_promote_members',
        'schedule': timedelta(days=365), # 매년 1월 1일 실행 (정확한 날짜는 Celery Beat 설정에서 추가 조정 필요)
    },
}
