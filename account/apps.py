from django.apps import AppConfig


class AccountConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'account'

    # This function is the only new thing in this file
    # it just imports the signal file when the app is ready
    def ready(self):
        import account.signals