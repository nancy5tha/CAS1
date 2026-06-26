from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.shortcuts import redirect


# def home(request):
    # return redirect("/assessment/login/")


urlpatterns = [
    # path("", home),
    path('', lambda request: redirect('/assessment/login/')),
    # Authentication
    path(
        "login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="/assessment/login/"),
        name="logout",
    ),
    # Dashboards
    path("dashboard/", views.dashboard, name="dashboard"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("teacher-dashboard/", views.teacher_dashboard, name="teacher_dashboard"),
    # Admin-only
    path("manage-years/", views.manage_years, name="manage_years"),
    path("manage-terms/", views.manage_terms, name="manage_terms"),
    path("manage-students/", views.manage_students, name="manage_students"),
    path("students/edit/<int:student_id>/", views.edit_student, name="edit_student"),
    path(
        "students/delete/<int:student_id>/", views.delete_student, name="delete_student"
    ),
    path("manage-subjects/", views.manage_subjects, name="manage_subjects"),
    path("subjects/edit/<int:subject_id>/", views.edit_subject, name="edit_subject"),
    path(
        "subjects/delete/<int:subject_id>/", views.delete_subject, name="delete_subject"
    ),
    # Teacher-only
    path("add-assessment/", views.add_assessment, name="add_assessment"),
    # Reports
    # ✅ Single student report card
    path(
        "report-card/student/<int:student_id>/<int:term_id>/",
        views.student_report_card,
        name="student_report_card",
    ),
    # ✅ Class report card
    path(
        "report-card/class/<int:term_id>/<str:grade>/<str:sec>/<int:subject_id>/",
        views.class_report_card,
        name="class_report_card",
    ),
    path(
        "report-card/pdf/<int:term_id>/<str:grade>/<str:sec>/",
        views.class_report_card_pdf,
        name="class_report_card_pdf",
    ),
]
