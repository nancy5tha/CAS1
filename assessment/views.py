from django.shortcuts import render, redirect
from reportlab.lib.pagesizes import A5
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from django.http import HttpResponse
from .models import (
    AcademicYear,
    Student,
    Assessment,
    ExamTerm,
    Subject,
    Profile,
    ClassSubject,
)
from django.contrib.auth.decorators import login_required
import csv
from io import TextIOWrapper
from django.core.paginator import Paginator
from django.db.models import Q
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def dashboard(request):
    profile = Profile.objects.get(user=request.user)
    if profile.role == "Admin":
        return redirect("admin_dashboard")
    elif profile.role == "Teacher":
        return redirect("teacher_dashboard")


@login_required
def admin_dashboard(request):
    terms = ExamTerm.objects.all()
    grades = Student.objects.values_list("grade", flat=True).distinct()
    secs = Student.objects.values_list("sec", flat=True).distinct()

    if (
        request.GET.get("term_id")
        and request.GET.get("grade")
        and request.GET.get("sec")
    ):
        term_id = request.GET["term_id"]
        grade = request.GET["grade"]
        sec = request.GET["sec"]
        return redirect("class_report_card_pdf", term_id=term_id, grade=grade, sec=sec)

    return render(
        request,
        "admin_dashboard.html",
        {
            "terms": terms,
            "grades": grades,
            "secs": secs,
        },
    )


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

    # ✅ Bulk CSV Upload
    if request.method == "POST" and "upload_csv" in request.POST:
        csv_file = request.FILES.get("csv_file")
        if csv_file:
            # Decode file to text
            file_data = TextIOWrapper(csv_file.file, encoding="utf-8")
            reader = csv.DictReader(file_data)

            for row in reader:
                name = row.get("name")
                roll = row.get("roll")
                grade = row.get("grade")
                sec = row.get("sec")

                if name and roll and grade and sec:
                    Student.objects.update_or_create(
                        roll=roll, grade=grade, sec=sec, defaults={"name": name}
                    )

            return redirect("manage_students")

    # ✅ Add new student if POST
    if request.method == "POST":
        name = request.POST.get("name")
        roll = request.POST.get("roll")
        grade = request.POST.get("grade")
        sec = request.POST.get("sec")

        if name and roll and grade and sec:
            Student.objects.create(name=name, roll=roll, grade=grade, sec=sec)
            return redirect("manage_students")  # refresh page after adding

    # ✅ Search filter
    query = request.GET.get("search")
    students_list = Student.objects.all().order_by("grade", "sec", "roll")

    if query:
        students_list = students_list.filter(
            Q(name__icontains=query)
            | Q(roll__icontains=query)
            | Q(grade__icontains=query)
            | Q(sec__icontains=query)
        )

    # ✅ Pagination
    paginator = Paginator(students_list, 10)  # 20 students per page
    page_number = request.GET.get("page")
    students = paginator.get_page(page_number)

    return render(
        request, "manage_students.html", {"students": students, "query": query}
    )


@login_required
def add_assessment(request):

    years = AcademicYear.objects.all()
    terms = ExamTerm.objects.all()
    grades = Student.objects.values_list("grade", flat=True).distinct()
    secs = Student.objects.values_list("sec", flat=True).distinct()

    students = None
    assessment_map = {}
    subjects = Subject.objects.none()

    year = None
    term = None
    grade = None
    sec = None
    selected_subject = None

    if request.method == "POST":

        year_id = request.POST.get("year")
        term_id = request.POST.get("term")
        grade = request.POST.get("grade")
        sec = request.POST.get("sec")
        subject_id = request.POST.get("subject")

        # YEAR
        if year_id:
            year = AcademicYear.objects.get(id=year_id)

        # TERM
        if term_id:
            term = ExamTerm.objects.get(id=term_id)

        # SUBJECTS (GRADE wise)
        if grade:
            subjects = Subject.objects.filter(grade=grade)

        # STUDENTS
        if grade and sec:
            students = Student.objects.filter(grade=grade, sec=sec)

        # SELECTED SUBJECT
        if subject_id:
            selected_subject = Subject.objects.get(id=subject_id)

        # SAVE DATA
        if (
            "save_all" in request.POST
            and students
            and selected_subject
            and year
            and term
        ):

            for student in students:

                Assessment.objects.update_or_create(
                    student=student,
                    year=year,
                    term=term,
                    subject=selected_subject,
                    defaults={
                        "viva": int(
                            request.POST.get(
                                f"viva_{student.id}_{selected_subject.id}", 0
                            )
                            or 0
                        ),
                        "project": int(
                            request.POST.get(
                                f"project_{student.id}_{selected_subject.id}", 0
                            )
                            or 0
                        ),
                        "homework": int(
                            request.POST.get(
                                f"homework_{student.id}_{selected_subject.id}", 0
                            )
                            or 0
                        ),
                        "mcqs": int(
                            request.POST.get(
                                f"mcqs_{student.id}_{selected_subject.id}", 0
                            )
                            or 0
                        ),
                        "classwork": int(
                            request.POST.get(
                                f"classwork_{student.id}_{selected_subject.id}", 0
                            )
                            or 0
                        ),
                    },
                )

        # LOAD EXISTING MARKS (IMPORTANT FIX)
        if students and selected_subject and year and term:

            assessments = Assessment.objects.filter(
                student__in=students, subject=selected_subject, year=year, term=term
            )

            assessment_map = {a.student_id: a for a in assessments}

    return render(
        request,
        "add_assessment.html",
        {
            "years": years,
            "terms": terms,
            "grades": grades,
            "secs": secs,
            "subjects": subjects,
            "students": students,
            "assessment_map": assessment_map,
            "selected_year": year,
            "selected_term": term,
            "selected_grade": grade,
            "selected_sec": sec,
            "selected_subject": selected_subject,
        },
    )


# Register Algerian font
pdfmetrics.registerFont(TTFont("Algerian", "static/fonts/ALGER.TTF"))


# ✅ Class report card
@login_required
def class_report_card(request, term_id, grade, sec, subject_id):

    term = ExamTerm.objects.get(id=term_id)
    subject = Subject.objects.get(id=subject_id)

    students = Student.objects.filter(grade=grade, sec=sec)

    assessments = Assessment.objects.filter(
        term=term, subject=subject, student__in=students
    )

    # 🔥 IMPORTANT FIX: safe key mapping
    assessment_map = {}

    for a in assessments:
        assessment_map[a.student_id] = a

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


def break_long_words(text, max_len=7):
    if text is None:
        return ""
    return "\n".join([text[i : i + max_len] for i in range(0, len(text), max_len)])


def class_report_card_pdf(request, term_id, grade, sec):
    term = ExamTerm.objects.get(id=term_id)
    students = Student.objects.filter(grade=grade, sec=sec)
    # class_subjects = ClassSubject.objects.filter(grade=grade).select_related("subject")
    subjects = Subject.objects.filter(grade=grade)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="report_card_{grade}{sec}.pdf"'

    p = canvas.Canvas(response, pagesize=A5)
    width, height = A5

    for student in students:
        # Header
        p.setFont("Algerian", 16)
        p.drawCentredString(width / 2, height - 40, "Ujjwal Shishu Niketan Academy")
        p.setFont("Helvetica", 9)
        p.drawCentredString(
            width / 2, height - 55, "Sahidpath, Panga, Kirtipur-5, Kathmandu"
        )
        p.drawCentredString(width / 2, height - 68, "Phone No.: 4330300, 4333529")
        p.setFont("Helvetica-Bold", 10)
        p.drawCentredString(
            width / 2, height - 85, f"{term.name} Examination - {term.year}"
        )
        p.setFont("Helvetica", 9)
        p.drawCentredString(
            width / 2, height - 98, "CAS (Continuous Assessment System)"
        )

        # Student info
        p.setFont("Helvetica-Bold", 9)
        p.drawString(40, height - 140, f"Name: {student.name}")
        p.drawString(200, height - 140, f"Grade: {grade}")
        p.drawString(300, height - 140, f"Sec: {sec}")
        p.drawString(350, height - 140, f"Roll No: {student.roll}")

        # Table header
        y = height - 180
        p.setFont("Helvetica-Bold", 9)

        if grade in ["NINE", "TEN"]:
            headers = [
                "S.N",
                "Subjects",
                "F.M",
                "MCQ",
                "Regularity",
                "Activities",
                "Project",
                "Total",
            ]
            # Balanced spacing for 8 columns
            x_positions = [40, 70, 140, 180, 220, 270, 310, 350]
        else:
            headers = [
                "S.N",
                "Subjects",
                "F.M",
                "MCQ",
                "Viva",
                "Regularity",
                "Activities",
                "Project",
                "Total",
            ]
            # Balanced spacing for 9 columns
            x_positions = [40, 70, 120, 160, 200, 240, 290, 330, 360]
        # for i, header in enumerate(headers):
        #     p.drawString(x_positions[i], y, header)
        # y -= 15
        # p.line(35, y + 10, width - 35, y + 10)
          # Draw headers with word break
        max_header_height = 15
        for i, header in enumerate(headers):
            if len(header) > 8:
                first = header[:8]
                second = header[8:]
                p.drawString(x_positions[i], y, first)
                p.drawString(x_positions[i], y - 10, second)
                max_header_height = 30   # two lines → more space
            else:
                p.drawString(x_positions[i], y, header)

        y -=  max_header_height
        p.line(35, y + 15, width - 35, y + 15)

        # Table rows
        p.setFont("Helvetica", 9)
        sn = 1
        for subject in subjects:
            assessment = Assessment.objects.filter(
                student=student, term=term, subject=subject
            ).first()
            mcq = assessment.mcqs if assessment else 0
            viva = assessment.viva if assessment else 0
            hw = assessment.homework if assessment else 0
            discipline = assessment.classwork if assessment else 0
            project = assessment.project if assessment else 0
            total = assessment.total if assessment else 0

            if grade in ["NINE", "TEN"]:
                row_data = [
                    sn,
                    subject.name,
                    subject.full_marks,
                    mcq,
                    hw,
                    discipline,
                    project,
                    total,
                ]
            else:
                row_data = [
                    sn,
                    subject.name,
                    subject.full_marks,
                    mcq,
                    viva,
                    hw,
                    discipline,
                    project,
                    total,
                ]
            for i, val in enumerate(row_data):
                p.drawString(x_positions[i], y, str(val))
            # ✅ Horizontal line after each row
            p.line(35, y - 2, width - 35, y - 2)
            y -= 15
            sn += 1

        # ✅ Fixed footer position
        footer_y = 120  # distance from bottom of page

        p.line(35, footer_y + 20, width - 35, footer_y + 20)
        p.setFont("Helvetica", 9)

        p.drawString(50, footer_y, "Guardian Sign")
        p.drawString(width / 2 - 30, footer_y, "School Seal")
        p.drawString(width - 120, footer_y, "Class Teacher")
        # ✅ Note line below signatures
        note_y = footer_y - 15
        p.setFont("Helvetica-Oblique", 8)  # italic small font
        p.drawCentredString(
            width / 2, note_y, "Submit this report card duly signed by guardian."
        )

        p.showPage()

    p.save()
    return response


@login_required
def edit_student(request, student_id):
    student = Student.objects.get(id=student_id)
    if request.method == "POST":
        student.name = request.POST.get("name")
        student.roll = request.POST.get("roll")
        student.grade = request.POST.get("grade")
        student.sec = request.POST.get("sec")
        student.save()
        return redirect("manage_students")
    return render(request, "edit_student.html", {"student": student})


@login_required
def delete_student(request, student_id):
    student = Student.objects.get(id=student_id)
    student.delete()
    return redirect("manage_students")


@login_required
def manage_subjects(request):
    profile = Profile.objects.get(user=request.user)
    if profile.role != "Admin":
        return redirect("teacher_dashboard")

    # ✅ Add new subject
    if request.method == "POST":
        name = request.POST.get("name")
        grade = request.POST.get("grade")
        full_marks = request.POST.get("full_marks")

        if name and grade and full_marks:
            Subject.objects.create(name=name, grade=grade, full_marks=int(full_marks))
            return redirect("manage_subjects")
    # ✅ Sort subjects by grade ascending
    subjects = Subject.objects.all().order_by("grade", "name")

    # ✅ Pagination (10 subjects per page)
    paginator = Paginator(subjects, 10)
    page_number = request.GET.get("page")
    subjects = paginator.get_page(page_number)

    return render(request, "manage_subjects.html", {"subjects": subjects})


@login_required
def edit_subject(request, subject_id):
    subject = Subject.objects.get(id=subject_id)
    if request.method == "POST":
        subject.name = request.POST.get("name")
        subject.grade = request.POST.get("grade")
        subject.full_marks = request.POST.get("full_marks")
        subject.save()
        return redirect("manage_subjects")
    return render(request, "edit_subject.html", {"subject": subject})


@login_required
def delete_subject(request, subject_id):
    subject = Subject.objects.get(id=subject_id)
    subject.delete()
    return redirect("manage_subjects")
