from django.contrib import admin

from .models import (
    GMCMLogicTree,
    HazardSolution,
    LocationList,
    SeismicHazardModel,
    SourceLogicTree,
    SourceLogicTreeSource,
    SourceLogicTreeBranch,
)


class SeismicHazardModelAdmin(admin.ModelAdmin):
    fields = ["version", "notes", "source_logic_tree", "gmcm_logic_tree"]
    list_display = ["version", "notes", "source_logic_tree", "gmcm_logic_tree"]


class SourceLogicTreeAdmin(admin.ModelAdmin):
    fields = ["version", "notes"]


class GMCMLogicTreeAdmin(admin.ModelAdmin):
    fields = ["version", "notes"]


class SourceLogicTreeSourceAdmin(admin.ModelAdmin):
    fields = [
        "tag",
        "notes",
        "inversion_toshi_id",
        "background_toshi_id",
        "tectonic_region",
        "group",
    ]
    list_display = ["tag", "notes", "tectonic_region", "group"]
    list_filter = ["tectonic_region", "group"]


class SourceLogicTreeBranchAdmin(admin.ModelAdmin):
    fields = ["weight", "source_logic_tree", "source_logic_tree_component"]


class LocationListAdmin(admin.ModelAdmin):
    fields = ["list_id", "notes", "length"]


class HazardSolutionAdmin(admin.ModelAdmin):
    fields = [
        "solution_id",
        "created",
        "vs30",
        "notes",
        "location_lists",
        "slt_components",
    ]
    list_display = ["solution_id", "created", "vs30", "notes"]
    list_filter = ["vs30", "created"]


admin.site.register(SeismicHazardModel, SeismicHazardModelAdmin)
admin.site.register(SourceLogicTree, SourceLogicTreeAdmin)
admin.site.register(GMCMLogicTree, GMCMLogicTreeAdmin)
admin.site.register(SourceLogicTreeSource, SourceLogicTreeSourceAdmin)
admin.site.register(
    SourceLogicTreeBranch, SourceLogicTreeBranchAdmin
)

admin.site.register(LocationList, LocationListAdmin)
admin.site.register(HazardSolution, HazardSolutionAdmin)
