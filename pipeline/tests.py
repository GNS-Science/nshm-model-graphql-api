from django.utils import timezone

from pipeline.models import OpenquakeHazardTask


# models test
class TestOpenquakeHazardTask:
    def create_oht(
        self, general_task_id="only a test", notes="yes, this is only a test"
    ):
        return OpenquakeHazardTask(
            general_task_id=general_task_id, notes=notes, date=timezone.now()
        )

    def test_oht_creation(self):
        w = self.create_oht()
        assert isinstance(w, OpenquakeHazardTask)
        assert str(w) == w.general_task_id
