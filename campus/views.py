from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import Group
from django.http import HttpResponse
from django.core.mail import EmailMessage

from .forms import (
    Student_SignUpForm, UsdForm, dispstuForm,
    company_SignUpForm, ccdForm, jobposForm
)
from campus.models import stu_details, comp_details, job_pos, applied_jobs


# ---------------------------------------------------------------------
# 🏠 Common Views
# ---------------------------------------------------------------------
def home(request):
    return render(request, 'campus/home.html')


def pagelogout(request):
    logout(request)
    return redirect('/')


# ---------------------------------------------------------------------
# 🎓 STUDENT AUTH & DASHBOARD
# ---------------------------------------------------------------------
def student_login(request):
    if request.user.is_authenticated and request.user.groups.filter(name='student').exists():
        return render(request, 'campus/stulog.html')

    form = AuthenticationForm(data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)

        if user.groups.filter(name='student').exists():
            return render(request, 'campus/stulog.html')
        else:
            logout(request)
            messages.error(request, "Invalid credentials for student account.")

    return render(request, 'campus/student_login.html', {'form': form})


def student_register(request):
    form = Student_SignUpForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        group, _ = Group.objects.get_or_create(name='student')
        user.groups.add(group)

        user = authenticate(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password1']
        )
        login(request, user)
        return redirect('/student/student_login/')
    return render(request, 'campus/register.html', {'form': form})


@login_required
def usd(request):
    if not request.user.groups.filter(name='student').exists():
        return HttpResponse("<h1>Unauthorized access</h1>")

    stu = request.user.username
    post = stu_details.objects.filter(username=stu).first()
    if not post:
        messages.error(request, "No student details found. Please contact admin.")
        return redirect("home")

    form = UsdForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        # Update details
        for field in form.cleaned_data:
            setattr(post, field, form.cleaned_data[field])
        post.save()
        messages.success(request, "Details updated successfully!")
        return redirect("student_dashboard")

    return render(request, 'campus/usd.html', {'form': form, 'post': post})


@login_required
def dispstu(request):
    if not request.user.groups.filter(name='student').exists():
        return HttpResponse("<h1>Unauthorized access</h1>")
    stu = request.user.username
    post = stu_details.objects.filter(username=stu)
    return render(request, 'campus/dispstu.html', {'form': dispstuForm(), 'post': post})


# ---------------------------------------------------------------------
# 🏢 COMPANY AUTH & DASHBOARD
# ---------------------------------------------------------------------
def company_login(request):
    if request.user.is_authenticated and request.user.groups.filter(name='company').exists():
        return render(request, 'campus/comlog.html')

    form = AuthenticationForm(data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)

        if user.groups.filter(name='company').exists():
            return render(request, 'campus/comlog.html')
        else:
            logout(request)
            messages.error(request, "Invalid credentials for company account.")

    return render(request, 'campus/company_login.html', {'form': form})


def company_register(request):
    form = company_SignUpForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        group, _ = Group.objects.get_or_create(name='company')
        user.groups.add(group)

        comp_details.objects.create(
            username=form.cleaned_data['username'],
            company_name=form.cleaned_data['company_name'],
            email=form.cleaned_data['email'],
            est_year=form.cleaned_data['est_year'],
            type=form.cleaned_data['type'],
            about=form.cleaned_data['about'],
            hr_name=form.cleaned_data['hr_name'],
            hr_phn=form.cleaned_data['hr_phn'],
            headquaters=form.cleaned_data['headquaters'],
        )

        user = authenticate(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password1']
        )
        login(request, user)
        return redirect('/')
    return render(request, 'campus/register1.html', {'form': form})


@login_required
def ccd(request):
    if not request.user.groups.filter(name='company').exists():
        return HttpResponse("<h1>Unauthorized access</h1>")

    stu = request.user.username
    post = comp_details.objects.filter(username=stu).first()

    form = ccdForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        for field in form.cleaned_data:
            setattr(post, field, form.cleaned_data[field])
        post.save()
        messages.success(request, "Company details updated!")
        return render(request, 'campus/comlog.html')

    return render(request, 'campus/ccd.html', {'form': form, 'post': post})


# ---------------------------------------------------------------------
# 💼 JOB MANAGEMENT
# ---------------------------------------------------------------------
@login_required
def jobpos(request):
    if not request.user.groups.filter(name='company').exists():
        return HttpResponse("<h1>Unauthorized access</h1>")

    form = jobposForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Job position added successfully!")
        return render(request, 'campus/comlog.html')

    company_name = comp_details.objects.filter(username=request.user.username).first().company_name
    safe_name = "_".join(company_name.split())
    return render(request, 'campus/jobpos.html', {'form': form, 'x': request.user.username, 'y': safe_name})


@login_required
def viewpos(request):
    if not request.user.groups.filter(name='company').exists():
        return HttpResponse("<h1>Unauthorized access</h1>")

    jobs = job_pos.objects.filter(username=request.user.username)
    message = "No vacancies posted" if not jobs else ""
    return render(request, 'campus/viewpos.html', {'y': jobs, 's': message})


@login_required
def deletevacan(request):
    if not request.user.groups.filter(name='company').exists():
        return HttpResponse("<h1>Unauthorized access</h1>")

    if request.method == "POST":
        jobid = request.POST.get("jobid")
        job = job_pos.objects.filter(job_id=jobid).first()
        if not job:
            return render(request, 'campus/jobdelete.html', {'s': "Wrong job ID, try again"})

        applied_jobs.objects.filter(job_id=job).delete()
        job.delete()
        messages.success(request, "Job deleted successfully!")
        return render(request, 'campus/comlog.html')

    return render(request, 'campus/jobdelete.html')


# ---------------------------------------------------------------------
# 🎯 JOB APPLICATIONS (Students)
# ---------------------------------------------------------------------
@login_required
def applyjob(request):
    if not request.user.groups.filter(name='student').exists():
        return HttpResponse("<h1>Unauthorized access</h1>")

    s = ""
    y = []
    if request.method == "POST":
        salary = request.POST.get("salary")
        bond = request.POST.get("years")
        branch = stu_details.objects.filter(username=request.user.username).first().branch.lower()

        branch_map = {
            "it": "information_technology",
            "cse": "cse",
            "me": "mech",
            "ce": "civil",
            "eee": "eee",
            "ece": "ece",
            "ch": "chemical"
        }

        if branch in branch_map:
            filter_kwargs = {
                "salary__gte": salary,
                "bond_years__lte": bond,
                branch_map[branch]: "yes"
            }
            y = job_pos.objects.filter(**filter_kwargs).order_by('salary')

        s = "No vacancies for this preference" if not y else ""
    return render(request, 'campus/applyjob.html', {'y': y, 's': s})


@login_required
def apply(request, opt):
    if not request.user.groups.filter(name='student').exists():
        return HttpResponse("<h1>Unauthorized access</h1>")

    if request.method == "POST":
        student = request.user.username
        company = job_pos.objects.filter(job_id=opt).first().username
        applied_jobs.objects.create(student_id=student, company_id=company, job_id=opt)
        return HttpResponse("<h1>Application submitted successfully!</h1>")

    company_username = job_pos.objects.filter(job_id=opt).first().username
    company_data = comp_details.objects.filter(username=company_username).first()
    return render(request, 'campus/compdisp.html', {'post': company_data})


# ---------------------------------------------------------------------
# 📨 COMPANY SELECT STUDENTS & SEND MAIL
# ---------------------------------------------------------------------
@login_required
def selectstu(request):
    if not request.user.groups.filter(name='company').exists():
        return HttpResponse("<h1>Unauthorized access</h1>")

    y, s = [], ""
    if request.method == "POST":
        jobid = request.POST.get("jobid")
        company = request.user.username

        if not job_pos.objects.filter(job_id=jobid, username=company).exists():
            return render(request, 'campus/sstu.html', {'s': "Enter correct job ID"})

        applied_list = applied_jobs.objects.filter(job_id=jobid, company_id=company).values('student_id')
        if not applied_list:
            return render(request, 'campus/sstu.html', {'s': "No applicants found"})

        tenth = request.POST.get("tenth")
        twth = request.POST.get("twth")
        btech = request.POST.get("btech")

        for student in applied_list:
            candidates = stu_details.objects.filter(
                class_10_cgpa__gte=tenth,
                class_12_percentage__gte=twth,
                cgpa_Btech__gte=btech,
                username=student['student_id']
            )
            if candidates.exists():
                y.extend(candidates)

        s = "No candidates met the requirements" if not y else ""
    return render(request, 'campus/sstu.html', {'y': y, 's': s})


@login_required
def stumail(request, opt):
    if not request.user.groups.filter(name='company').exists():
        return HttpResponse("<h1>Unauthorized access</h1>")

    if request.method == "POST":
        student = stu_details.objects.filter(username=opt).first()
        company = comp_details.objects.filter(username=request.user.username).first()

        subject = f"Call Letter from {company.company_name}"
        body = f"Congratulations {student.name}! You are selected for the interview. Further details will be shared by your Placement Officer."
        EmailMessage(subject, body, to=[student.email]).send()

        return HttpResponse("<h1>Email sent successfully!</h1>")

    student = stu_details.objects.filter(username=opt).first()
    return render(request, 'campus/showstudent.html', {'post': student})
