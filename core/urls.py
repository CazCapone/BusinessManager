from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('', include('Website.urls')),
    path('admin/', admin.site.urls),
]
