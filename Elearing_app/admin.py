from django.contrib import admin
from .models import *

admin.site.register(Customer)
admin.site.register(Course)
admin.site.register(Payment)
admin.site.register(CourseResource)
admin.site.register(UserProgress)
admin.site.register(TestQuestion)
admin.site.register(UserTestAttempt)
