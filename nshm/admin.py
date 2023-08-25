from django.contrib import admin

from .models import (
    SeismicHazardModel,
    SourceLogicTree, 
    SourceLogicTreeComponent,
    SourceLogicTreeWeightedComponent
)

class SeismicHazardModelAdmin(admin.ModelAdmin):
    fields = ["version", "notes", "source_logic_tree" ]

class SourceLogicTreeAdmin(admin.ModelAdmin):
    fields = ["version", "notes"]

class SourceLogicTreeComponentAdmin(admin.ModelAdmin):
    fields = ["tag", "notes", "inversion_toshi_id", "background_toshi_id", "tectonic_region", "group" ]

class SourceLogicTreeWeightedComponentAdmin(admin.ModelAdmin):
    fields = ["weight", "source_logic_tree", "source_logic_tree_component"]

admin.site.register(SeismicHazardModel, SeismicHazardModelAdmin)
admin.site.register(SourceLogicTree, SourceLogicTreeAdmin)
admin.site.register(SourceLogicTreeComponent, SourceLogicTreeComponentAdmin)
admin.site.register(SourceLogicTreeWeightedComponent, SourceLogicTreeWeightedComponentAdmin)