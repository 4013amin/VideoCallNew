from pathlib import Path
import dj_database_url
import os

# 1. تنظیم مسیر اصلی
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. تنظیمات امنیتی
SECRET_KEY = 'django-insecure-z99pomn$%biaz+4i@vaopd2wp(%+-^s&1jbbhc!4=iylhf_6#k'
DEBUG = False 
ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = ["https://*.liara.run"] 

# 3. دیتابیس (فقط یکبار و مستقیم)
# نکته: این دیتابیس طبق گفته شما بعد از 5 ساعت پاک می‌شود
DATABASES = {
    'default': dj_database_url.parse('postgresql://root:xHVrK8gRWtg03ubVT7YO3HRJ@videocallnewdb:5432/postgres')
}

# 4. اپلیکیشن‌ها
INSTALLED_APPS = [
    'daphne', 
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users',
    'videocall',
    'channels'
]

# 5. میانی‌افزارها (WhiteNoise برای استاتیک)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Video.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# 6. تنظیمات ASGI برای ویدیو کال
ASGI_APPLICATION = 'Video.asgi.application'

# 7. تنظیمات ردیس (بسیار مهم)
# توجه: باید در لیارا یک Redis بسازید و لینک آن را اینجا بگذارید
# اگر ردیس ندارید، بخش else را فعلاً مثل if کنید تا خطا ندهد (اما مچینگ کار نخواهد کرد)
if DEBUG:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }
else:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                # لینک ردیس لیارا را اینجا بگذارید (مثال: redis://:pass@host:port)
                "hosts": [('redis://YOUR_REDIS_URL_HERE')], 
            },
        },
    }

# 8. تنظیمات فایل‌های استاتیک
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# 9. بقیه تنظیمات
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'