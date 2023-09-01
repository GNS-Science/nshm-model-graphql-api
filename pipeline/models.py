from django.db import models

# Create your models here.
from nshm.models import SeismicHazardModel

# class HazardSolution(models.Model):
#     solution_id = models.CharField(max_length=50, null=False)
#     created = models.DateTimeField(auto_now=False, auto_now_add=False)
#     vs30 = models.SmallIntegerField()
#     notes = models.TextField(null=True, blank=True)
#     location_lists = models.ManyToManyField(
#         LocationList, related_name='hazard_solutions')
#     slt_components = models.ManyToManyField(
#         SourceLogicTreeWeightedComponent,
#         related_name='hazard_solutions')


class OpenquakeHazardTask(models.Model):
    general_task_id = models.CharField(max_length=50, null=False)
    date = models.DateField(auto_now=False, auto_now_add=False)
    config_info = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    part_of = models.ForeignKey(
        SeismicHazardModel,
        related_name="hazard_tasks",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return self.general_task_id
