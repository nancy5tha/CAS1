from django.shortcuts import render, redirect
from .models import AcademicYear, Student, Assessment, ExamTerm, Subject, Profile
from django.contrib.auth.decorators import login_required


def dashboard(request):
    profile = Profile.objects.get(user=request.user)
    if profile.role == "Admin":
        return redirect("admin_dashboard")
    elif profile.role == "Teacher":
        return redirect("teacher_dashboard")


def admin_dashboard(request):
    return render(request, "admin_dashboard.html")


@login_required
def teacher_dashboard(request):
    grades = Student.objects.values_list("grade", flat=True).distinct()
    secs = Student.objects.values_list("sec", flat=True).distinct()
    terms = ExamTerm.objects.all()
    subjects = Subject.objects.all()

    return render(
        request,
        "teacher_dashboard.html",
        {
            "grades": grades,
            "secs": secs,
            "terms": terms,
            "subjects": subjects,
        },
    )



# ✅ Single student report card
def student_report_card(request, student_id, term_id):
    student = Student.objects.get(id=student_id)
    term = ExamTerm.objects.get(id=term_id)
    assessments = Assessment.objects.filter(student=student, term=term)

    grand_total = sum(a.total for a in assessments)
    avg = grand_total / len(assessments) if assessments else 0

    return render(
        request,
        "report_card.html",
        {
            "student": student,
            "term": term,
            "assessments": assessments,
            "grand_total": grand_total,
            "average": avg,
        },
    )


@login_required
def manage_years(request):
    profile = Profile.objects.get(user=request.user)
    if profile.role != "Admin":
        return redirect("teacher_dashboard")
    years = AcademicYear.objects.all()
    return render(request, "manage_years.html", {"years": years})


@login_required
def manage_terms(request):
    profile = Profile.objects.get(user=request.user)
    if profile.role != "Admin":
        return redirect("teacher_dashboard")
    terms = ExamTerm.objects.all()
    return render(request, "manage_terms.html", {"terms": terms})


@login_required
def manage_students(request):
    profile = Profile.objects.get(user=request.user)
    if profile.role != "Admin":
        return redirect("teacher_dashboard")
    students = Student.objects.all()
    return render(request, "manage_students.html", {"students": students})


@login_required
def add_assessment(request):
    years = AcademicYear.objects.all()
    terms = ExamTerm.objects.all()
    subjects = Subject.objects.all()
    grades = Student.objects.values_list("grade", flat=True).distinct()
    secs = Student.objects.values_list("sec", flat=True).distinct()

    students = None
    assessment_map = {}

    # Initialize variables so they exist on GET
    year = None
    term = None
    subject = None
    grade = None
    sec = None

    if request.method == "POST":
        year_id = request.POST.get("year")
        term_id = request.POST.get("term")
        subject_id = request.POST.get("subject")
        grade = request.POST.get("grade")
        sec = request.POST.get("sec")

        if year_id and term_id and subject_id and grade and sec:
            year = AcademicYear.objects.get(id=year_id)
            term = ExamTerm.objects.get(id=term_id)
            subject = Subject.objects.get(id=subject_id)

            # Save marks
            if "save_all" in request.POST:
                students = Student.objects.filter(grade=grade, sec=sec)
                for student in students:
                    viva = int(request.POST.get(f"viva_{student.id}", 0))
                    project = int(request.POST.get(f"project_{student.id}", 0))
                    homework = int(request.POST.get(f"homework_{student.id}", 0))
                    mcqs = int(request.POST.get(f"mcqs_{student.id}", 0))
                    classwork = int(request.POST.get(f"classwork_{student.id}", 0))

                    Assessment.objects.update_or_create(
                        student=student,
                        year=year,
                        term=term,
                        subject=subject,
                        defaults={
                            "viva": viva,
                            "project": project,
                            "homework": homework,
                            "mcqs": mcqs,
                            "classwork": classwork,
                        },
                    )
                return redirect("teacher_dashboard")

            # Load students + existing marks
            students = Student.objects.filter(grade=grade, sec=sec)
            assessments = Assessment.objects.filter(
                year=year, term=term, subject=subject, student__in=students
            )
            assessment_map = {a.student_id: a for a in assessments}

    return render(
        request,
        "add_assessment.html",
        {
            "years": years,
            "terms": terms,
            "subjects": subjects,
            "grades": grades,
            "secs": secs,
            "students": students,
            "assessment_map": assessment_map,
            "selected_year": year,
            "selected_term": term,
            "selected_subject": subject,
            "selected_grade": grade,
            "selected_sec": sec,
        },
    )



# ✅ Class report card
@login_required
def class_report_card(request, term_id, grade, sec, subject_id):
    term = ExamTerm.objects.get(id=term_id)
    subject = Subject.objects.get(id=subject_id)

    students = Student.objects.filter(grade=grade, sec=sec)
    assessments = Assessment.objects.filter(
        term=term, subject=subject, student__in=students
    )
    assessment_map = {a.student_id: a for a in assessments}

    return render(
        request,
        "report_card_list.html",
        {
            "term": term,
            "subject": subject,
            "students": students,
            "assessment_map": assessment_map,
        },
    )
