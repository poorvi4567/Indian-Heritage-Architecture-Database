from django.contrib import admin
from .models import Monument, Location, ArchitecturalStyle, Period

admin.site.register(Monument)
admin.site.register(Location)
admin.site.register(ArchitecturalStyle)
admin.site.register(Period)
