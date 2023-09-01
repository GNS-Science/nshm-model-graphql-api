from django.db import models

# Create your models here.
TECTONIC_REGIONS = models.TextChoices("TectonicRegion", "CRUSTAL SUBDUCTION INTERFACE")
SLT_GROUP = models.TextChoices(
    "SourceLogicTreeGroup",
    (("SLAB", "Slab"), ("HIK", "Hikurangi"), ("PUY", "Puysegur"), ("CRU", "Crustal")),
)


class SourceLogicTree(models.Model):
    version = models.CharField(max_length=40)
    notes = models.TextField(
        help_text="users can search on this.. please add some useful text here",
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.version


class SourceLogicTreeComponent(models.Model):
    tag = models.CharField(max_length=50)
    notes = models.TextField(null=True, blank=True)
    inversion_toshi_id = models.CharField(max_length=50, null=False)
    background_toshi_id = models.CharField(max_length=50, null=True)
    tectonic_region = models.CharField(
        choices=TECTONIC_REGIONS.choices, null=False, max_length=10
    )
    group = models.CharField(choices=SLT_GROUP.choices, null=False, max_length=10)

    def __str__(self):
        return f"{self.tag} {self.tectonic_region}"


class SourceLogicTreeWeightedComponent(models.Model):
    weight = models.FloatField()
    source_logic_tree = models.ForeignKey(
        SourceLogicTree,
        related_name="slt_weighted_components",
        null=False,
        on_delete=models.CASCADE,
    )
    source_logic_tree_component = models.ForeignKey(
        SourceLogicTreeComponent,
        related_name="slt_weighted_components",
        null=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return f"{self.source_logic_tree_component.tag} {self.weight}"


class GMCMLogicTree(models.Model):
    version = models.CharField(max_length=30)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.version


class SeismicHazardModel(models.Model):
    version = models.CharField(max_length=30)
    notes = models.TextField(null=True, blank=True)
    source_logic_tree = models.ForeignKey(
        SourceLogicTree,
        related_name="seismic_hazard_models",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    gmcm_logic_tree = models.ForeignKey(
        GMCMLogicTree,
        related_name="seismic_hazard_models",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return self.version


class LocationList(models.Model):
    list_id = models.CharField(max_length=10)
    notes = models.TextField(null=True, blank=True)
    length = models.SmallIntegerField()

    def __str__(self):
        return self.list_id


class HazardSolution(models.Model):
    solution_id = models.CharField(max_length=50, null=False)
    created = models.DateTimeField(auto_now=False, auto_now_add=False)
    vs30 = models.SmallIntegerField()
    notes = models.TextField(null=True, blank=True)
    location_lists = models.ManyToManyField(
        LocationList, related_name="hazard_solutions"
    )
    slt_components = models.ManyToManyField(
        SourceLogicTreeWeightedComponent, related_name="hazard_solutions"
    )


# class OpenquakeHazardTask(models.Model):
#     general_task_id = models.CharField(max_length=50, null=False)
#     date = models.DateField(auto_now=False, auto_now_add=False)
#     config_info = models.TextField(null=True, blank=True)
#     notes = models.TextField(null=True, blank=True)
#     part_of = models.ForeignKey(
#         SeismicHazardModel, related_name='hazard_tasks',null=True, blank=True, on_delete=models.SET_NULL)

#     def __str__(self):
#         return self.general_task_id
