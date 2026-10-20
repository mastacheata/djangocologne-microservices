from django.urls import path

from mailboxes import views

urlpatterns = [
    path("", views.village, name="village"),
    path("api/deliveries/", views.receive, name="receive"),
    path("api/summary/", views.summary, name="summary"),
]
