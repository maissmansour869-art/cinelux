from django.apps import AppConfig
from django.conf import settings
from django.core.management import call_command
from django.db.models.signals import post_migrate


class CataloguesConfig(AppConfig):
    name = "catalogues"

    def ready(self):
        post_migrate.connect(auto_seed_cinelux, sender=self, dispatch_uid="catalogues.auto_seed_cinelux")


def auto_seed_cinelux(sender, **kwargs):
    if not getattr(settings, "CINELUX_AUTO_SEED", True):
        return
    call_command("seed_cinelux", verbosity=0)
