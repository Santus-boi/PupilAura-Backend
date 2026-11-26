"""
Django settings for config project.
"""

from pathlib import Path
import os
import dj_database_url  # NEW: Required for Render database
from dotenv import load_dotenv

# ==============================================================
# BASE DIRECTORY
# ==============================================================
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ==============================================================
# SECURITY
# ==============================================================
SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = ["*"]

# NEW: Allow any domain to submit forms (fixes CSRF error on phone)
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "https://*.onrender.com",  # Allows Render domains
    "https://*.trycloudflare.com",
]

# ==============================================================
# APPLICATIONS
# ==============================================================
INSTALLED_APPS = [
    "daphne",
    "channels",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    
    # Your apps
    "accounts", "learning", "enrollments", "assessments", "student",
    "tech", "exam_prep", "admin_dashboard", "payments", 
    "ai_services", "play_learn", "community",
]

# ==============================================================
# MIDDLEWARE
# ==============================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # NEW: For serving static files
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ==============================================================
# URL CONFIGURATION & TEMPLATES
# ==============================================================
ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ==============================================================
# WSGI AND ASGI APPLICATIONS
# ==============================================================
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ==============================================================
# DATABASE (UPDATED FOR RENDER)
# ==============================================================
# This automatically uses the DATABASE_URL from Render, or your local .env
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL", "postgres://user:pass@localhost:5432/dbname"),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# ==============================================================
# PASSWORD VALIDATION
# ==============================================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ==============================================================
# INTERNATIONALIZATION
# ==============================================================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ==============================================================
# STATIC & MEDIA FILES
# ==============================================================
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"  # NEW: Required for Render
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage" # NEW

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ==============================================================
# EMAIL
# ==============================================================
MAILERS = {
    "default": {"BACKEND": "django.core.mail.backends.console.EmailBackend"},
}

# ==============================================================
# DJANGO CHANNELS (UPDATED FOR RENDER)
# ==============================================================
# Render free tier doesn't have Redis. Using InMemory for now.
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# ==============================================================
# CUSTOM USER MODEL
# ==============================================================
AUTH_USER_MODEL = "accounts.User"

# ==============================================================
# AI PROVIDER (Keep as is, API key can be added later)
# ==============================================================
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")
AI_TIMEOUT_SECONDS = int(os.getenv("AI_TIMEOUT_SECONDS", "45"))
AI_MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES", "2"))
AI_COST_PER_1K_PROMPT_TOKENS = float(os.getenv("AI_COST_PROMPT", "0.00015"))
AI_COST_PER_1K_COMPLETION_TOKENS = float(os.getenv("AI_COST_COMPLETION", "0.0006"))
AI_MONTHLY_BUDGET_PER_ADMIN = float(os.getenv("AI_MONTHLY_BUDGET", "5.0"))

# ==============================================================
# PAYMENT GATEWAYS
# ==============================================================
PAYSTACK_PUBLIC_KEY = os.getenv("PAYSTACK_PUBLIC_KEY", "")
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY", "")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# ==============================================================
# PAYMENT REDIRECTS AND DEFAULTS
# ==============================================================
PAYMENT_SUCCESS_URL = "payments:success"
PAYMENT_CANCEL_URL = "payments:cancel"
PAYMENT_DEFAULT_CURRENCY = "NGN"
PAYMENT_DEFAULT_DURATION_DAYS = 90

# ==============================================================
# LOGIN
# ==============================================================
LOGIN_URL = "accounts:user_login"
LOGIN_REDIRECT_URL = "student_dashboard"

# ==============================================================
# SITE URL
# ==============================================================
SITE_URL = os.getenv("SITE_URL", "http://localhost:8000")

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'