from django.contrib import admin
from django.urls import path
from ui import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("submit_feedback/", views.submit_feedback, name="submit_feedback"),
    path("submit_question/", views.generate_audience, name="submit_question"),
    path("", views.index, name="index"),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0]
    )
