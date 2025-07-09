from django.contrib import admin
from .models import Announcement, PushLog

admin.site.register(Announcement)
admin.site.register(PushLog)
