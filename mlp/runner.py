import tempfile
import shutil
from django.conf import settings
from django.test.runner import DiscoverRunner

class MLPRunner(DiscoverRunner):
    """
    Creates a temporary directory, runs the tests in there, then deletes it
    """
    def run_tests(self, *args, **kwargs):
        settings.MEDIA_ROOT = tempfile.mkdtemp(prefix="mlp_unit_test_tmp_dir_")
        super(MLPRunner, self).run_tests(*args, **kwargs)
        shutil.rmtree(settings.MEDIA_ROOT)
