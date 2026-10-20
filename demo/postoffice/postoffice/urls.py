from django.urls import path

from letters import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("api/letters/", views.post_letters, name="post_letters"),
    path("api/stats/", views.stats, name="stats"),
    path("health/", views.health, name="health"),
]
