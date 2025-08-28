from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.management.color import color_style


class Command(BaseCommand):
    help = 'Check security settings and environment configuration'

    def handle(self, *args, **options):
        style = color_style()
        
        self.stdout.write(style.SUCCESS("\n=== Security Configuration Check ===\n"))
        
        # Environment
        self.stdout.write(f"Environment: {settings.ENVIRONMENT}")
        self.stdout.write(f"Is Production: {settings.IS_PRODUCTION}")
        self.stdout.write(f"Is Staging: {settings.IS_STAGING}")
        self.stdout.write(f"Is Development: {settings.IS_DEVELOPMENT}")
        
        # Debug Mode
        self.stdout.write(f"\nDebug Mode: {settings.DEBUG}")
        if settings.IS_PRODUCTION and settings.DEBUG:
            self.stdout.write(style.ERROR("⚠️  WARNING: Debug is enabled in production!"))
        elif not settings.IS_PRODUCTION and settings.DEBUG:
            self.stdout.write(style.SUCCESS("✓ Debug is enabled for development/staging"))
        elif settings.IS_PRODUCTION and not settings.DEBUG:
            self.stdout.write(style.SUCCESS("✓ Debug is disabled in production"))
        
        # Allowed Hosts
        self.stdout.write(f"\nAllowed Hosts: {settings.ALLOWED_HOSTS}")
        if '*' in settings.ALLOWED_HOSTS and settings.IS_PRODUCTION:
            self.stdout.write(style.ERROR("⚠️  WARNING: Wildcard in ALLOWED_HOSTS in production!"))
        elif '*' in settings.ALLOWED_HOSTS and not settings.IS_PRODUCTION:
            self.stdout.write(style.WARNING("⚠️  Wildcard in ALLOWED_HOSTS (OK for development)"))
        else:
            self.stdout.write(style.SUCCESS("✓ ALLOWED_HOSTS properly configured"))
        
        # Security Settings
        self.stdout.write("\n=== Security Headers ===")
        security_settings = [
            ('SECURE_SSL_REDIRECT', 'SSL Redirect'),
            ('SESSION_COOKIE_SECURE', 'Secure Session Cookie'),
            ('CSRF_COOKIE_SECURE', 'Secure CSRF Cookie'),
            ('SECURE_BROWSER_XSS_FILTER', 'XSS Filter'),
            ('SECURE_CONTENT_TYPE_NOSNIFF', 'Content Type Nosniff'),
            ('SESSION_COOKIE_HTTPONLY', 'HTTP Only Session Cookie'),
            ('CSRF_COOKIE_HTTPONLY', 'HTTP Only CSRF Cookie'),
        ]
        
        for setting, description in security_settings:
            value = getattr(settings, setting, False)
            if value:
                self.stdout.write(style.SUCCESS(f"✓ {description}: {value}"))
            else:
                if settings.IS_PRODUCTION:
                    self.stdout.write(style.ERROR(f"✗ {description}: {value}"))
                else:
                    self.stdout.write(style.WARNING(f"⚠️  {description}: {value} (OK for development)"))
        
        # HSTS Settings
        if hasattr(settings, 'SECURE_HSTS_SECONDS'):
            self.stdout.write(f"\n=== HSTS Configuration ===")
            self.stdout.write(f"HSTS Seconds: {settings.SECURE_HSTS_SECONDS}")
            self.stdout.write(f"Include Subdomains: {getattr(settings, 'SECURE_HSTS_INCLUDE_SUBDOMAINS', False)}")
            self.stdout.write(f"Preload: {getattr(settings, 'SECURE_HSTS_PRELOAD', False)}")
        
        # Secret Key
        self.stdout.write("\n=== Secret Key ===")
        if settings.SECRET_KEY:
            if 'change' in settings.SECRET_KEY.lower() or 'development' in settings.SECRET_KEY.lower():
                if settings.IS_PRODUCTION:
                    self.stdout.write(style.ERROR("⚠️  WARNING: Using development secret key in production!"))
                else:
                    self.stdout.write(style.WARNING("⚠️  Using development secret key (OK for development)"))
            else:
                self.stdout.write(style.SUCCESS("✓ Secret key is configured"))
        else:
            self.stdout.write(style.ERROR("✗ Secret key is not set!"))
        
        # Summary
        self.stdout.write("\n=== Summary ===")
        if settings.IS_PRODUCTION:
            if not settings.DEBUG and settings.SECRET_KEY and '*' not in settings.ALLOWED_HOSTS:
                self.stdout.write(style.SUCCESS("✓ Production security configuration looks good!"))
            else:
                self.stdout.write(style.ERROR("⚠️  Production security configuration needs attention!"))
        else:
            self.stdout.write(style.SUCCESS(f"✓ {settings.ENVIRONMENT.title()} environment configuration is appropriate"))