from django.shortcuts import render,render_to_response, redirect
from django.http import HttpResponse
from .models import User,Student
import cgi
import os
import json
import calendar
from django.utils import timezone
from django.conf import settings
from django.template import RequestContext, loader
import reportlab
from reportlab.pdfbase import pdfmetrics  
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer  
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.rl_config import defaultPageSize
from reportlab.pdfgen import canvas
from django.core.urlresolvers import reverse
from datetime import datetime
from io import BytesIO
from django.contrib import messages
from .models import Document,Courses,StudentMarks,Dictionary
from .forms import DocumentForm,CourseForm,StudentForm
from django.core.context_processors import csrf
from django.contrib.auth import logout
from django.core.mail import EmailMessage
from StringIO import StringIO
from zipfile import ZipFile

glob_studentID = ''

#login check decorator
def login_check(meth):
    def inner(request):
        try:
            if request.session["user"] != None:
                return meth(request)
            else:
                return redirect('/sis')
        except KeyError:
            return redirect('/sis/')
    return inner


def index(request):
	# return HttpResponse('what is this')
	# args = {}
	# args.update(csrf(request))
	# return render(request, "myIndex.html", args)
	return render(request, "myIndex.html")

def login(request):
	args = {}
	args.update(csrf(request))
	name = request.POST.get('username')
	password = request.POST.get('password')
	user = User.objects.filter(username = name, password = password)
	if (not user):
		args["invalid"] = True
		return render_to_response("myIndex.html",args)
		# return redirect('/sis/')
	else:
		request.session["user"] = name
		s_list = Student.objects.all()
		s_dic = {}
		s_dic = {"students" : s_list}
		return render(request,('home.html',args), s_dic)
		# return render_to_response("home.html", args, s_dict)

@login_check
def changepassword(request):
    args = {}
    args.update(csrf(request))
    password = request.POST.get('oldpassword')
    password1 = request.POST.get('password1')
    password2 = request.POST.get('password2')
    s_list = Student.objects.all()
    s_dic = {}
    s_dic = {"students" : s_list}
    try:
        user = User.objects.get(password = password)
        if (not user):
            args["invalid"] = True
            return render_to_response("myIndex.html",args)
        else:
            if password1 == password2:
                user.password = password1
                user.save()
                return render_to_response("myIndex.html",args)
            else:
                return render(request,('home.html',args), s_dic)
    except User.DoesNotExist:
        s_list = Student.objects.all()
        s_dic = {}
        s_dic = {"students" : s_list}
        return render(request,('home.html',args), s_dic)

@login_check
def Gradingsystem(request):
    args = {}
    print "hi"
    args.update(csrf(request))
    batchId = request.POST.get('batchId')
    print batchId
    grades = request.POST.get('grades')
    dictionary = Dictionary()
    dictionary.year = batchId
    dictionary.grade_string = grades
    dictionary.save()
    s_list = Student.objects.all()
    s_dic = {}
    s_dic = {"students" : s_list}
    return render(request,('home.html',args), s_dic)


def logout_page(request):
    global glob_studentID
    glob_studentID = ''
    request.session["user"] = None
    # del request.session['user']
    logout(request)
    return redirect('/sis/')

# validating and storing the data of uploaded student details csv file
@login_check
def list(request):
    # Handle file upload
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            docfile = request.FILES['docfile']
            if docfile.name.endswith('.csv'):
                for row in docfile:
                    student = Student()
                    row = row.split(",")
                    student.SID = row[0]
                    student.firstname = row[1]
                    student.lastname = row[2]
                    student.emailid = row[3]
                    student.phnum = row[4]
                    student.yearofjoining = row[5]
                    student.yearofpassing = row[6]
                    student.batchNo = row[7]
                    student.save()

                # Redirect to the document list after POST
                s_list = Student.objects.all()
                Success = 'Successfully_uploaded'
                s_dic = {}
                s_dic = {"students" : s_list,"Success": Success}
                return render(request,('home.html',{'form': form}), s_dic)
            else:
                return HttpResponse('Please upload only .csv format file. Go back and upload again with correct format')
    else:
        form = DocumentForm()  # A empty, unbound form

    # Load documents for the list page
    students = Student.objects.all()
    return render_to_response(
        'DocUpload.html',
        {'documents': students, 'form': form},
        context_instance=RequestContext(request)
    )

# validating and storing the data of uploaded couerses list csv file
@login_check
def courseList(request):
    # Handle file upload
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            coursefile = request.FILES['coursefile']
            if coursefile.name.endswith('.csv'):
                for row in coursefile:
                    course = Courses()
                    row = row.split(",")
                    course.CID = row[0]
                    course.CName = row[1]
                    course.year = row[2]
                    course.term = row[3]
                    course.credits = row[4]
                    course.save()

                # Redirect to the document list after POST
                s_list = Student.objects.all()
                Success = 'Successfully_uploaded'
                s_dic = {}
                s_dic = {"students" : s_list,"Success": Success}
                return render(request,('home.html',{'form': form}), s_dic)
            else:
                return HttpResponse('Please upload only .csv format file. Go back and upload again with correct format')
            # return HttpResponseRedirect(reverse('myproject.myapp.views.list'))
    else:
        form = CourseForm()  # A empty, unbound form

    # Load documents for the list page
    courses = Courses.objects.all()

    # # Render list page with the documents and the form
    # return HttpResponse('Fialure in uploading the student details')
    return render_to_response(
        'CoursesUpload.html',
        {'documents': courses, 'form': form},
        context_instance=RequestContext(request)
    )

# validating and storing the data of uploaded student marks list csv file
@login_check
def studentMarkslist(request):
    # Handle file upload
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            studmarksfile = request.FILES['studmarksfile']
            if studmarksfile.name.endswith('.csv'):
                for row in studmarksfile:
                    studmarks = StudentMarks()
                    row = row.split(",")
                    studmarks.SID = row[0]
                    studmarks.CID = row[1]
                    studmarks.grade = row[2]
                    studmarks.description = row[3]
                    studmarks.save()

                # Redirect to the document list after POST
                s_list = Student.objects.all()
                Success = 'Successfully_uploaded'
                s_dic = {}
                s_dic = {"students" : s_list,"Success": Success}
                return render(request,('home.html',{'form': form}), s_dic)
            else:
                return HttpResponse('Please upload only .csv format file. Go back and upload again with correct format')
            # return HttpResponseRedirect(reverse('myproject.myapp.views.list'))
    else:
        form = StudentForm()  # A empty, unbound form

    # Load documents for the list page
    studmarkslist = StudentMarks.objects.all()

    # # Render list page with the documents and the form
    # return HttpResponse('Fialure in uploading the student details')
    return render_to_response(
        'StudentMarksUpload.html',
        {'documents': studmarkslist, 'form': form},
        context_instance=RequestContext(request)
    )

@login_check
def studentInfo(request):
    global glob_studentID
    args = {}
    args.update(csrf(request))
    if 'searchID' in request.POST:
        message = request.POST.get('searchID')
        glob_studentID = ''
        glob_studentID += message
        print glob_studentID
        try:
            student = Student.objects.get(SID = message)
            # print student.emailid
            s_dic = {}
            s_list = Student.objects.all()
            s_dic = {"students" : s_list,"student":student}
            return render(request,("home.html",args),s_dic)
        except Student.DoesNotExist:
            s_dic = {}
            s_list = Student.objects.all()
            s_dic = {"students" : s_list}
            return render(request,("home.html",args),s_dic)
    else:
        message = ''
        message = glob_studentID
        print glob_studentID
        try:
            student = Student.objects.get(SID = message)
            # print student.emailid
            s_dic = {}
            s_list = Student.objects.all()
            s_dic = {"students" : s_list,"student":student}
            return render(request,("home.html",args),s_dic)
        except Student.DoesNotExist:
            s_dic = {}
            s_list = Student.objects.all()
            s_dic = {"students" : s_list}
            return render(request,("home.html",args),s_dic)
    # print "check1"
    # return redirect('/sis/')

@login_check
def batchInfo(request):
    args = {}
    args.update(csrf(request))
    global glob_studentID
    print glob_studentID+"----"
    if glob_studentID:
        try:
            stud = glob_studentID[:4]
            print stud
            all_studs = Student.objects.filter(SID__startswith = stud)
            stud_dic = {}
            stud_list = Student.objects.all()
            stud_dic = {"students" : stud_list, "all_studs":all_studs,"pid":glob_studentID}
            return render(request,("home.html",args), stud_dic)
        except Student.DoesNotExist:
            stud_dic = {}
            stud_list = Student.objects.all();
            return render(request,("home.html", args), stud_dic)
    else:
        message = 'Enter a number in the Search bar'
        return HttpResponse(message)

@login_check
def markssheet(request):
    args = {}
    args.update(csrf(request))
    global glob_studentID
    print glob_studentID
    if glob_studentID:
        try:
            stud = Student.objects.get(SID = glob_studentID)
            grade_details = StudentMarks.objects.filter(SID = glob_studentID)
            print grade_details
            a_list = []
            b_list = []
            c_list = []
            for j in grade_details:
                credits_details = Courses.objects.filter(CID=j.CID)
                print credits_details[0]


                a_list.append(credits_details[0])
                credits = credits_details[0].credits
                print credits
                b_list.append(credits)
                print j.grade
                c_list.append(j.grade)
                

            stud_id = glob_studentID
            students_ids=Student.objects.all()
            count = 0
            today = datetime.now()
            for st in students_ids:
                if stud_id in st.SID:
                    count = count + 1
            if count > 0:
                stud_details = Student.objects.filter(SID = stud_id)
       
            gsid = glob_studentID
            if gsid.startswith('12'):
                print "ho"
                year_num = gsid[2:4]
                year_num = "20" + year_num
                print year_num
            else:
                year_num = gsid[:4]
                print year_num
            
            gd = Dictionary.objects.get(year=year_num)
            string = gd.grade_string
            print string
            checklist = string.split(',')
            print checklist
            dic = {}
            fullstring = ''
            for i, val in enumerate(checklist):
                opt = val
                mylist = opt.split(':')
                fullstring = fullstring + mylist[0] + ' ' + '= ' + mylist[1] +'; '
                dic[mylist[0]] = mylist[1]
            
            print dic
            print fullstring
            fullstring = fullstring[:-2]
            print fullstring
            # gradeDictionary={'EX':10.0,'A+':9.5,'A':9.0,'B+':8.5,'B':8.0,'B-':7.5,'C':7.0,'Ex':10.0,'A-':9.0}
            # "EX = 10.0; A+ = 9.5; A = 9.0; B+ = 8.5; B = 8.0; C = 7.0"
            gradeDictionary = dic
            print 'hi'
            grade_details = StudentMarks.objects.filter(SID = stud_details[0].SID)
            GPA = 0
            CGPA = 0
            sum_of_credits = 0
            temp = 0
            for j in grade_details:
                if j.grade == 'F':
                    sum_of_credits = 0
                    return HttpResponse('student has a F grade')
                # print j.grade
                grade = gradeDictionary[j.grade.upper()]
                # print grade
                grade = float(grade)
                credits_details = Courses.objects.filter(CID=j.CID)

                credits = credits_details[0].credits
                
                sum_of_credits = sum_of_credits + credits
                GPA = GPA + (grade*credits)

            for j in grade_details:
                if j.grade == 'F':
                    sum_of_credits = 0
                    return HttpResponse('student has a F grade')

                grade = gradeDictionary[j.grade.upper()]
                credits_details = Courses.objects.filter(CID=j.CID)
                credits = credits_details[0].credits
                    
            if not sum_of_credits == 0:
                CGPA = GPA/sum_of_credits   

            stud_details = Student.objects.filter(SID = stud_id)
            grade_details= StudentMarks.objects.filter(SID = stud_details[0].SID)
            temp = 0
            for j in grade_details:
                if j.grade == 'F':
                    sum_of_credits = 0
                    return HttpResponse('student has a F grade')
                grade = gradeDictionary[j.grade.upper()]
                credits_details = Courses.objects.filter(CID=j.CID)
                credits = credits_details[0].credits
            if not sum_of_credits == 0:
                CGPA = GPA/sum_of_credits

            print "CGPA:"
            CGPA = str(round(CGPA,1))
            # CGPA = 5
            res = zip(a_list,b_list,c_list)
            stud_dic = {}
            stud_list = Student.objects.all()
            senddict = {"name": stud,"result":res,"students": stud_list,"id":glob_studentID,"CGPA":CGPA}
            return render(request,("home.html",args),senddict)
            # return HttpResponse(stud)
        except Student.DoesNotExist:
            stud_dic = {}
            stud_list = Student.objects.all();
            return render(request,("home.html", args), stud_dic)
        except Dictionary.DoesNotExist:
            stud_dic = {}
            stud_list = Student.objects.all();
            return render(request,("home.html", args), stud_dic)
    else:
        message = 'Enter a number in the Search bar'
        return HttpResponse(message)

def help(request):
    args={}
    return render_to_response('help.html',args)

@login_check
def Transcript(request):
    print "tarun"
    from reportlab.lib import colors  
    from reportlab.lib.units import inch
    # Create the HttpResponse object with the appropriate PDF headers.
    global glob_studentID
    print glob_studentID
    if glob_studentID != '':
        stud_id = glob_studentID
        filename = glob_studentID
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename={0}.pdf'.format(filename)
        buffer=BytesIO()
        # p= canvas.Canvas("filename.pdf")
        
        p = canvas.Canvas(buffer)
        # Create the PDF object, using the response object as its "file."

       
        # Draw things on the PDF. Here's where the PDF generation happens.
        # See the ReportLab documentation for the full list of functionality.
        students_ids=Student.objects.all()
        count = 0
        today = datetime.now()
        for st in students_ids:
            if stud_id in st.SID:
                count = count + 1
        if count > 0:
            try:
                stud_details = Student.objects.filter(SID = stud_id)
                p.setFont('Times-Bold',7)
                p.drawString(20,690,"MSIT")
                p.drawString(20,680, str(stud_details[0].yearofjoining)+"-"+str(stud_details[0].yearofpassing))
                p.drawString(20,670,"Date Of Issue:")
                p.drawString(20,660,today.strftime("%d-%B-%Y"))
                p.setFont('Times-Bold',7)
                p.drawString(20,650,"Consolidated Mark Sheet")
                p.setFont('Times-Bold',11)
                p.drawString(115,690,"Name:" )
                p.setFont('Times-Bold',12)
                p.drawString(149,690,stud_details[0].firstname+" "+stud_details[0].lastname)
                p.setFont('Times-Roman',10)
                p.drawString(465,690,"Roll No: ")
                p.setFont('Times-Bold',10)
                p.drawString(501, 690, stud_details[0].SID)
                p.setFont('Times-BoldItalic',11)
                p.drawString(115,670,"MASTER OF SCIENCE IN INFORMATION TECHNOLOGY")
                p.setFont('Times-Roman',10)
                p.drawString(115,650,"CGPA:")
                p.drawString(115,630,"Credits Obtained:")
                p.drawString(445,640,"PercentageRange:")
                p.drawString(395,630,"Required Credits for Completion:")
                p.setFont('Times-Bold',9)
                p.drawString(115, 600, "Code")
                p.drawString(235, 600, "Course Name")
                p.drawString(435, 600, "Grade")
                p.drawString(485, 600, "Credits")
                p.drawString(115, 580,"First Year")
                p.setFont('Times-Roman',9)
                print glob_studentID
                gsid = glob_studentID
                if gsid.startswith('12'):
                    print "ho"
                    year_num = gsid[2:4]
                    year_num = "20" + year_num
                    print year_num
                else:
                    year_num = gsid[:4]
                    print year_num
                
                gd = Dictionary.objects.get(year=year_num)
                string = gd.grade_string
                print string
                checklist = string.split(',')
                print checklist
                dic = {}
                fullstring = ''
                for i, val in enumerate(checklist):
                	opt = val
                	mylist = opt.split(':')
                	fullstring = fullstring + mylist[0] + ' ' + '= ' + mylist[1] +'; '
                	dic[mylist[0]] = mylist[1]
                print dic
                print fullstring
                fullstring = fullstring[:-2]
                print fullstring
                # gradeDictionary={'EX':10.0,'A+':9.5,'A':9.0,'B+':8.5,'B':8.0,'B-':7.5,'C':7.0,'Ex':10.0,'A-':9.0}
                # "EX = 10.0; A+ = 9.5; A = 9.0; B+ = 8.5; B = 8.0; C = 7.0"
                gradeDictionary = dic
                print 'hi'
                grade_details = StudentMarks.objects.filter(SID = stud_details[0].SID)
                GPA = 0
                CGPA = 0
                sum_of_credits = 0
                temp = 0
                for j in grade_details:
                    if j.grade == 'F':
                        sum_of_credits = 0
                        return HttpResponse('student has a F grade')
                    print j.grade
                    grade = gradeDictionary[j.grade.upper()]
                    print "coool"
                    print grade
                    grade = float(grade)
                    credits_details = Courses.objects.filter(CID=j.CID)

                    credits = credits_details[0].credits
                    
                    sum_of_credits = sum_of_credits + credits
                    GPA = GPA + (grade*credits)

                    if credits_details[0].year == 1 and 'SS' not in credits_details[0].CID :
                        p.drawString(445, (560-temp), j.grade)
                        p.drawString(115, (560-temp), credits_details[0].CID)
                        p.drawString(170, (560-temp), credits_details[0].CName)
                        p.drawString(505, (560-temp), str(credits))
                        # p.drawString(460, 650, str(credits))
                        temp = temp + 15

                p.setFont('Times-Bold',9)
                p.drawString(115,(560-temp),"Second Year")
                p.setFont('Times-Roman',9)
                temp = temp + 15
                for j in grade_details:
                    if j.grade == 'F':
                        sum_of_credits = 0
                        return HttpResponse('student has a F grade')

                    grade = gradeDictionary[j.grade.upper()]
                    
                    credits_details = Courses.objects.filter(CID=j.CID)

                    credits = credits_details[0].credits

                    if credits_details[0].year == 2 and 'SS' not in credits_details[0].CID :
                        p.drawString(445, (560-temp), j.grade)
                        p.drawString(115, (560-temp), credits_details[0].CID)
                        p.drawString(170, (560-temp), credits_details[0].CName)
                        p.drawString(505, (560-temp), str(credits))
                        # p.drawString(460, 650, str(credits))
                        temp = temp + 15


                p.drawString(190, 630, str(sum_of_credits))
                p.drawString(530, 630, str(sum_of_credits))
                if not sum_of_credits == 0:
                    CGPA = GPA/sum_of_credits
                    p.drawString(150,650,str(round(CGPA,1)))
                
                # canvas.drawCentredString(2.75*inch, 2.5*inch, "Font size examples")
                if CGPA == 10.0 :
                    p.drawString(520,640,"96-100") 
                if CGPA >= 9.0 and CGPA <10.0:
                    p.drawString(520,640,"91-95")
                if CGPA >= 8.0 and CGPA < 9.0:
                    p.drawString(520,640,"86-90")
                if CGPA >= 7.0 and CGPA < 8.0:
                    p.drawString(520,640,"81-85")
                if CGPA >= 6.0 and CGPA < 7.0:
                    p.drawString(520,640,"76-80")
                if CGPA >= 5.0 and CGPA < 6.0:
                    p.drawString(520,640,"70-75")
                if CGPA < 5.0:
                    p.drawString(520,640,"<70")

                temp = temp + 80
                p.setFont('Times-Bold',10)
                p.drawString(400,560-temp,"Coordinator MSIT Division")

                temp = temp + 140
                p.setFont('Times-Italic',9)
                p.drawString(115,70,"CGPA: Cumulative Grade Point Average")
                temp = temp + 15
                p.drawString(115,50,fullstring)

                p.showPage()

                stud_details = Student.objects.filter(SID = stud_id)
                p.setFont('Times-Bold',7)
                p.drawString(20,690,"MSIT")
                p.drawString(20,680, str(stud_details[0].yearofjoining)+"-"+str(stud_details[0].yearofpassing))
                p.drawString(20,670,"Date Of Issue:")
                p.drawString(20,660,today.strftime("%d-%B-%Y"))
                p.setFont('Times-Bold',7)
                p.drawString(20,650,"Consolidated Marks Sheet")
                p.setFont('Times-Bold',11)
                p.drawString(115,690,"Name:" )
                p.setFont('Times-Bold',12)
                p.drawString(149,690,stud_details[0].firstname+" "+stud_details[0].lastname)
                p.setFont('Times-Roman',10)
                p.drawString(465,690,"Roll No: ")
                p.setFont('Times-Bold',10)
                p.drawString(501, 690, stud_details[0].SID)
                p.setFont('Times-BoldItalic',11)
                p.drawString(115,670,"MASTER OF SCIENCE IN INFORMATION TECHNOLOGY")
                p.setFont('Times-Roman',10)
                p.drawString(115,650,"CGPA:")
                p.drawString(115,630,"Credits Obtained:")
                p.drawString(445,640,"PercentageRange:")
                p.drawString(395,630,"Required Credits for Completion:")
                p.setFont('Times-Bold',9)
                p.drawString(115, 600, "Code")
                p.drawString(235, 600, "Course Name")
                p.drawString(435, 600, "Grade")
                p.drawString(485, 600, "Credits")
                
                # gradeDictionary={'EX':10.0,'A+':9.5,'A':9.0,'B+':8.5,'B':8.0,'B-':7.5,'C':7.0,'Ex':10.0,'A-':9.0}
                
                p.drawString(115, 580, "Soft Skills")
                p.setFont('Times-Roman',9)


                grade_details= StudentMarks.objects.filter(SID = stud_details[0].SID)
                temp = 0
                for j in grade_details:
                    if j.grade == 'F':
                        sum_of_credits = 0
                        return HttpResponse('student has a F grade')

                    grade = gradeDictionary[j.grade.upper()]
                    
                    credits_details = Courses.objects.filter(CID=j.CID)

                    credits = credits_details[0].credits

                    if 'SS' in credits_details[0].CID :
                        p.drawString(445, (560-temp), j.grade)
                        p.drawString(115, (560-temp), credits_details[0].CID)
                        p.drawString(170, (560-temp), credits_details[0].CName)
                        p.drawString(505, (560-temp), str(credits))
                        # p.drawString(460, 650, str(credits))
                        temp = temp + 15

                p.setFont('Times-Roman',9)
                p.drawString(190, 630, str(sum_of_credits))
                p.drawString(530, 630, str(sum_of_credits))
                if not sum_of_credits == 0:
                    CGPA = GPA/sum_of_credits
                    p.drawString(150,650,str(round(CGPA,1)))
                
                # canvas.drawCentredString(2.75*inch, 2.5*inch, "Font size examples")
                if CGPA == 10.0 :
                    p.drawString(520,640,"96-100") 
                if CGPA >= 9.0 and CGPA <10.0:
                    p.drawString(520,640,"91-95")
                if CGPA >= 8.0 and CGPA < 9.0:
                    p.drawString(520,640,"86-90")
                if CGPA >= 7.0 and CGPA < 8.0:
                    p.drawString(520,640,"81-85")
                if CGPA >= 6.0 and CGPA < 7.0:
                    p.drawString(520,640,"76-80")
                if CGPA >= 5.0 and CGPA < 6.0:
                    p.drawString(520,640,"70-75")
                if CGPA < 5.0:
                    p.drawString(520,640,"<70")


                temp = temp + 80
                p.setFont('Times-Bold',11)
                p.drawString(400,560-temp,"Coordinator MSIT Division")

                temp = temp + 250
                p.setFont('Times-Italic',9)
                p.drawString(115,70,"CGPA: Cumulative Grade Point Average")
                temp = temp + 15
                p.drawString(115,50,fullstring)

                p.showPage()
                p.save()
                pdf= buffer.getvalue()
                buffer.close()
                response.write(pdf)
                return response
            except Student.DoesNotExist:
                stud_dic = {}
                stud_list = Student.objects.all()
                senddict = {"students": stud_list}
                return render(request,("home.html",args),senddict)
        else:
            return HttpResponse("Student id not found")
    else:
        args = {}
        args.update(csrf(request))
        stud_dic = {}
        stud_list = Student.objects.all()
        senddict = {"students": stud_list}
        return render(request,("home.html",args),senddict)

def studentlogin(request):
    args = {}
    args.update(csrf(request))
    studentnum = request.POST.get('studentname')
    s = Student.objects.filter(SID = studentnum)
    if (not s):
        args["wrong"] = True
        return render_to_response("myIndex.html",args)
    else:
        try:
            stu = Student.objects.get(SID = studentnum)
            frommail = stu.emailid
            from reportlab.lib import colors
            from reportlab.lib.units import inch
            # Create the HttpResponse object with the appropriate PDF headers.
            stud_id = studentnum
            filename = studentnum
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename={0}.pdf'.format(filename)
            buffer=BytesIO()
            
            p = canvas.Canvas(buffer)

            students_ids=Student.objects.all()
            count = 0
            today = datetime.now()
            for st in students_ids:
                if stud_id in st.SID:
                    count = count + 1
            if count > 0:
                stud_details = Student.objects.filter(SID = stud_id)
                p.setFont('Times-Bold',7)
                p.drawString(20,690,"MSIT")
                p.drawString(20,680, str(stud_details[0].yearofjoining)+"-"+str(stud_details[0].yearofpassing))
                p.drawString(20,670,"Date Of Issue:")
                p.drawString(20,660,today.strftime("%d-%B-%Y"))
                p.setFont('Times-Bold',7)
                p.drawString(20,650,"Consolidated Mark Sheet")
                p.setFont('Times-Bold',11)
                p.drawString(115,690,"Name:" )
                p.setFont('Times-Bold',12)
                p.drawString(149,690,stud_details[0].firstname+" "+stud_details[0].lastname)
                p.setFont('Times-Roman',10)
                p.drawString(465,690,"Roll No: ")
                p.setFont('Times-Bold',10)
                p.drawString(501, 690, stud_details[0].SID)
                p.setFont('Times-BoldItalic',11)
                p.drawString(115,670,"MASTER OF SCIENCE IN INFORMATION TECHNOLOGY")
                p.setFont('Times-Roman',10)
                p.drawString(115,650,"CGPA:")
                p.drawString(115,630,"Credits Obtained:")
                p.drawString(445,640,"PercentageRange:")
                p.drawString(395,630,"Required Credits for Completion:")
                p.setFont('Times-Bold',9)
                p.drawString(115, 600, "Code")
                p.drawString(235, 600, "Course Name")
                p.drawString(435, 600, "Grade")
                p.drawString(485, 600, "Credits")
                p.drawString(115, 580,"First Year")
                p.setFont('Times-Roman',9)
                print stud_id
                gsid = stud_id
                if gsid.startswith('12'):
                    print "ho"
                    year_num = gsid[2:4]
                    year_num = "20" + year_num
                    print year_num
                else:
                    year_num = gsid[:4]
                    print year_num
                
                gd = Dictionary.objects.get(year=year_num)

                string = gd.grade_string
                print string
                checklist = string.split(',')
                print checklist
                dic = {}
                fullstring = ''
                for i, val in enumerate(checklist):
                    opt = val
                    mylist = opt.split(':')
                    fullstring = fullstring + mylist[0] + ' ' + '= ' + mylist[1] +'; '
                    dic[mylist[0]] = mylist[1]
                print dic
                print fullstring
                fullstring = fullstring[:-2]
                print fullstring
                # gradeDictionary={'EX':10.0,'A+':9.5,'A':9.0,'B+':8.5,'B':8.0,'B-':7.5,'C':7.0,'Ex':10.0,'A-':9.0}
                # "EX = 10.0; A+ = 9.5; A = 9.0; B+ = 8.5; B = 8.0; C = 7.0"
                gradeDictionary = dic
                print 'hi'
                grade_details = StudentMarks.objects.filter(SID = stud_details[0].SID)
                GPA = 0
                CGPA = 0
                sum_of_credits = 0
                temp = 0
                for j in grade_details:
                    if j.grade == 'F':
                        sum_of_credits = 0
                        return HttpResponse('student has a F grade')
                    print j.grade
                    grade = gradeDictionary[j.grade.upper()]
                    print grade
                    grade = float(grade)
                    credits_details = Courses.objects.filter(CID=j.CID)

                    credits = credits_details[0].credits
                    
                    sum_of_credits = sum_of_credits + credits
                    GPA = GPA + (grade*credits)

                    if credits_details[0].year == 1 and 'SS' not in credits_details[0].CID :
                        p.drawString(445, (560-temp), j.grade)
                        p.drawString(115, (560-temp), credits_details[0].CID)
                        p.drawString(170, (560-temp), credits_details[0].CName)
                        p.drawString(505, (560-temp), str(credits))
                        # p.drawString(460, 650, str(credits))
                        temp = temp + 15

                p.setFont('Times-Bold',9)
                p.drawString(115,(560-temp),"Second Year")
                p.setFont('Times-Roman',9)
                temp = temp + 15
                for j in grade_details:
                    if j.grade == 'F':
                        sum_of_credits = 0
                        return HttpResponse('student has a F grade')

                    grade = gradeDictionary[j.grade.upper()]
                    
                    credits_details = Courses.objects.filter(CID=j.CID)

                    credits = credits_details[0].credits

                    if credits_details[0].year == 2 and 'SS' not in credits_details[0].CID :
                        p.drawString(445, (560-temp), j.grade)
                        p.drawString(115, (560-temp), credits_details[0].CID)
                        p.drawString(170, (560-temp), credits_details[0].CName)
                        p.drawString(505, (560-temp), str(credits))
                        # p.drawString(460, 650, str(credits))
                        temp = temp + 15


                p.drawString(190, 630, str(sum_of_credits))
                p.drawString(530, 630, str(sum_of_credits))
                if not sum_of_credits == 0:
                    CGPA = GPA/sum_of_credits
                    p.drawString(150,650,str(round(CGPA,1)))
                
                # canvas.drawCentredString(2.75*inch, 2.5*inch, "Font size examples")
                if CGPA == 10.0 :
                    p.drawString(520,640,"96-100") 
                if CGPA >= 9.0 and CGPA <10.0:
                    p.drawString(520,640,"91-95")
                if CGPA >= 8.0 and CGPA < 9.0:
                    p.drawString(520,640,"86-90")
                if CGPA >= 7.0 and CGPA < 8.0:
                    p.drawString(520,640,"81-85")
                if CGPA >= 6.0 and CGPA < 7.0:
                    p.drawString(520,640,"76-80")
                if CGPA >= 5.0 and CGPA < 6.0:
                    p.drawString(520,640,"70-75")
                if CGPA < 5.0:
                    p.drawString(520,640,"<70")

                temp = temp + 80
                p.setFont('Times-Bold',10)
                p.drawString(400,560-temp,"Student generated Transcript")

                temp = temp + 140
                p.setFont('Times-Italic',9)
                p.drawString(115,70,"CGPA: Cumulative Grade Point Average")
                temp = temp + 15
                p.drawString(115,50,fullstring)

                p.showPage()

                stud_details = Student.objects.filter(SID = stud_id)
                p.setFont('Times-Bold',7)
                p.drawString(20,690,"MSIT")
                p.drawString(20,680, str(stud_details[0].yearofjoining)+"-"+str(stud_details[0].yearofpassing))
                p.drawString(20,670,"Date Of Issue:")
                p.drawString(20,660,today.strftime("%d-%B-%Y"))
                p.setFont('Times-Bold',7)
                p.drawString(20,650,"Consolidated Marks Sheet")
                p.setFont('Times-Bold',11)
                p.drawString(115,690,"Name:" )
                p.setFont('Times-Bold',12)
                p.drawString(149,690,stud_details[0].firstname+" "+stud_details[0].lastname)
                p.setFont('Times-Roman',10)
                p.drawString(465,690,"Roll No: ")
                p.setFont('Times-Bold',10)
                p.drawString(501, 690, stud_details[0].SID)
                p.setFont('Times-BoldItalic',11)
                p.drawString(115,670,"MASTER OF SCIENCE IN INFORMATION TECHNOLOGY")
                p.setFont('Times-Roman',10)
                p.drawString(115,650,"CGPA:")
                p.drawString(115,630,"Credits Obtained:")
                p.drawString(445,640,"PercentageRange:")
                p.drawString(395,630,"Required Credits for Completion:")
                p.setFont('Times-Bold',9)
                p.drawString(115, 600, "Code")
                p.drawString(235, 600, "Course Name")
                p.drawString(435, 600, "Grade")
                p.drawString(485, 600, "Credits")
                
                # gradeDictionary={'EX':10.0,'A+':9.5,'A':9.0,'B+':8.5,'B':8.0,'B-':7.5,'C':7.0,'Ex':10.0,'A-':9.0}
                
                p.drawString(115, 580, "Soft Skills")
                p.setFont('Times-Roman',9)


                grade_details= StudentMarks.objects.filter(SID = stud_details[0].SID)
                temp = 0
                for j in grade_details:
                    if j.grade == 'F':
                        sum_of_credits = 0
                        return HttpResponse('student has a F grade')

                    grade = gradeDictionary[j.grade.upper()]
                    
                    credits_details = Courses.objects.filter(CID=j.CID)

                    credits = credits_details[0].credits

                    if 'SS' in credits_details[0].CID :
                        p.drawString(445, (560-temp), j.grade)
                        p.drawString(115, (560-temp), credits_details[0].CID)
                        p.drawString(170, (560-temp), credits_details[0].CName)
                        p.drawString(505, (560-temp), str(credits))
                        # p.drawString(460, 650, str(credits))
                        temp = temp + 15

                p.setFont('Times-Roman',9)
                p.drawString(190, 630, str(sum_of_credits))
                p.drawString(530, 630, str(sum_of_credits))
                if not sum_of_credits == 0:
                    CGPA = GPA/sum_of_credits
                    p.drawString(150,650,str(round(CGPA,1)))
                
                # canvas.drawCentredString(2.75*inch, 2.5*inch, "Font size examples")
                if CGPA == 10.0 :
                    p.drawString(520,640,"96-100") 
                if CGPA >= 9.0 and CGPA <10.0:
                    p.drawString(520,640,"91-95")
                if CGPA >= 8.0 and CGPA < 9.0:
                    p.drawString(520,640,"86-90")
                if CGPA >= 7.0 and CGPA < 8.0:
                    p.drawString(520,640,"81-85")
                if CGPA >= 6.0 and CGPA < 7.0:
                    p.drawString(520,640,"76-80")
                if CGPA >= 5.0 and CGPA < 6.0:
                    p.drawString(520,640,"70-75")
                if CGPA < 5.0:
                    p.drawString(520,640,"<70")


                temp = temp + 80
                p.setFont('Times-Bold',11)
                p.drawString(400,560-temp,"Student generated Transcript")

                temp = temp + 250
                p.setFont('Times-Italic',9)
                p.drawString(115,70,"CGPA: Cumulative Grade Point Average")
                temp = temp + 15
                p.drawString(115,50,fullstring)

                p.showPage()
                p.save()
                pdf= buffer.getvalue()
                buffer.close()
            msg = EmailMessage("Hi", "This is your transcript", to=[frommail])
            pdfname = stud_id + ".pdf"
            msg.attach(pdfname, pdf, 'application/pdf')
            msg.content_subtype = "html"
            msg.send()
            stat = 'Your transcript has been sent to your registered mail. Please check your mail for transcript'
            sts = {"status" : stat}
        except Dictionary.DoesNotExist:
            return render(request,("myIndex.html",args),sts)
        return render(request,("myIndex.html",args),sts)

def bulkTranscript(request):
    global glob_studentID
    if glob_studentID:
        try:
            stud = glob_studentID[:4]
            all_studs = Student.objects.filter(SID__startswith = stud )
            stud_dic = {}
            stud_list = Student.objects.all()
            fname = []
            in_memory = StringIO()
            for stud in all_studs:
                print all_studs
                from reportlab.lib import colors
                from reportlab.lib.units import inch
                # Create the HttpResponse object with the appropriate PDF headers.
                stud_id = stud.SID
                print " again--> ; "+stud_id
                filename = stud.SID
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename={0}.pdf'.format(filename)
                buffer = BytesIO()
                p = canvas.Canvas(buffer)
                students_ids=Student.objects.all()
                count = 0
                today = datetime.now()
                for st in students_ids:
                    if stud_id in st.SID:
                        count = count + 1
                if count > 0:
                    stud_details = Student.objects.filter(SID = stud_id)
                    p.setFont('Times-Bold',7)
                    p.drawString(20,690,"MSIT")
                    p.drawString(20,680, str(stud_details[0].yearofjoining)+"-"+str(stud_details[0].yearofpassing))
                    p.drawString(20,670,"Date Of Issue:")
                    p.drawString(20,660,today.strftime("%d-%B-%Y"))
                    p.setFont('Times-Bold',7)
                    p.drawString(20,650,"Consolidated Mark Sheet")
                    p.setFont('Times-Bold',11)
                    p.drawString(115,690,"Name:" )
                    p.setFont('Times-Bold',12)
                    p.drawString(149,690,stud_details[0].firstname+" "+stud_details[0].lastname)
                    p.setFont('Times-Roman',10)
                    p.drawString(465,690,"Roll No: ")
                    p.setFont('Times-Bold',10)
                    p.drawString(501, 690, stud_details[0].SID)
                    p.setFont('Times-BoldItalic',11)
                    p.drawString(115,670,"MASTER OF SCIENCE IN INFORMATION TECHNOLOGY")
                    p.setFont('Times-Roman',10)
                    p.drawString(115,650,"CGPA:")
                    p.drawString(115,630,"Credits Obtained:")
                    p.drawString(445,640,"PercentageRange:")
                    p.drawString(395,630,"Required Credits for Completion:")
                    p.setFont('Times-Bold',9)
                    p.drawString(115, 600, "Code")
                    p.drawString(235, 600, "Course Name")
                    p.drawString(435, 600, "Grade")
                    p.drawString(485, 600, "Credits")
                    p.drawString(115, 580,"First Year")
                    p.setFont('Times-Roman',9)
                    print stud_id
                    gsid = stud_id
                    if gsid.startswith('12'):
                        print "ho"
                        year_num = gsid[2:4]
                        year_num = "20" + year_num
                        print year_num
                    else:
                        year_num = gsid[:4]
                        print year_num
                    gd = Dictionary.objects.get(year=year_num)
                    string = gd.grade_string
                    print string
                    checklist = string.split(',')
                    print checklist
                    dic = {}
                    fullstring = ''
                    for i, val in enumerate(checklist):
                        opt = val
                        mylist = opt.split(':')
                        fullstring = fullstring + mylist[0] + ' ' + '= ' + mylist[1] +'; '
                        dic[mylist[0]] = mylist[1]
                    # print dic
                    # print fullstring
                    fullstring = fullstring[:-2]
                    # print fullstring
                    # gradeDictionary={'EX':10.0,'A+':9.5,'A':9.0,'B+':8.5,'B':8.0,'B-':7.5,'C':7.0,'Ex':10.0,'A-':9.0}
                    # "EX = 10.0; A+ = 9.5; A = 9.0; B+ = 8.5; B = 8.0; C = 7.0"
                    gradeDictionary = dic
                    print 'hi'
                    grade_details = StudentMarks.objects.filter(SID = stud_details[0].SID)
                    GPA = 0
                    CGPA = 0
                    sum_of_credits = 0
                    temp = 0
                    for j in grade_details:
                        if j.grade == 'F':
                            sum_of_credits = 0
                            return HttpResponse('student has a F grade')
                        # print j.grade
                        grade = gradeDictionary[j.grade.upper()]
                        # print grade
                        grade = float(grade)
                        credits_details = Courses.objects.filter(CID=j.CID)

                        credits = credits_details[0].credits
                        
                        sum_of_credits = sum_of_credits + credits
                        GPA = GPA + (grade*credits)

                        if credits_details[0].year == 1 and 'SS' not in credits_details[0].CID :
                            p.drawString(445, (560-temp), j.grade)
                            p.drawString(115, (560-temp), credits_details[0].CID)
                            p.drawString(170, (560-temp), credits_details[0].CName)
                            p.drawString(505, (560-temp), str(credits))
                            # p.drawString(460, 650, str(credits))
                            temp = temp + 15

                    p.setFont('Times-Bold',9)
                    p.drawString(115,(560-temp),"Second Year")
                    p.setFont('Times-Roman',9)
                    temp = temp + 15
                    for j in grade_details:
                        if j.grade == 'F':
                            sum_of_credits = 0
                            return HttpResponse('student has a F grade')

                        grade = gradeDictionary[j.grade.upper()]
                        
                        credits_details = Courses.objects.filter(CID=j.CID)

                        credits = credits_details[0].credits

                        if credits_details[0].year == 2 and 'SS' not in credits_details[0].CID :
                            p.drawString(445, (560-temp), j.grade)
                            p.drawString(115, (560-temp), credits_details[0].CID)
                            p.drawString(170, (560-temp), credits_details[0].CName)
                            p.drawString(505, (560-temp), str(credits))
                            # p.drawString(460, 650, str(credits))
                            temp = temp + 15

                    p.drawString(190, 630, str(sum_of_credits))
                    p.drawString(530, 630, str(sum_of_credits))
                    if not sum_of_credits == 0:
                        CGPA = GPA/sum_of_credits
                        p.drawString(150,650,str(round(CGPA,1)))
                    
                    # canvas.drawCentredString(2.75*inch, 2.5*inch, "Font size examples")
                    if CGPA == 10.0 :
                        p.drawString(520,640,"96-100") 
                    if CGPA >= 9.0 and CGPA <10.0:
                        p.drawString(520,640,"91-95")
                    if CGPA >= 8.0 and CGPA < 9.0:
                        p.drawString(520,640,"86-90")
                    if CGPA >= 7.0 and CGPA < 8.0:
                        p.drawString(520,640,"81-85")
                    if CGPA >= 6.0 and CGPA < 7.0:
                        p.drawString(520,640,"76-80")
                    if CGPA >= 5.0 and CGPA < 6.0:
                        p.drawString(520,640,"70-75")
                    if CGPA < 5.0:
                        p.drawString(520,640,"<70")

                    temp = temp + 80
                    p.setFont('Times-Bold',10)
                    p.drawString(400,560-temp,"Coordinator MSIT Division")

                    temp = temp + 140
                    p.setFont('Times-Italic',9)
                    p.drawString(115,70,"CGPA: Cumulative Grade Point Average")
                    temp = temp + 15
                    p.drawString(115,50,fullstring)

                    p.showPage()

                    stud_details = Student.objects.filter(SID = stud_id)
                    p.setFont('Times-Bold',7)
                    p.drawString(20,690,"MSIT")
                    p.drawString(20,680, str(stud_details[0].yearofjoining)+"-"+str(stud_details[0].yearofpassing))
                    p.drawString(20,670,"Date Of Issue:")
                    p.drawString(20,660,today.strftime("%d-%B-%Y"))
                    p.setFont('Times-Bold',7)
                    p.drawString(20,650,"Consolidated Marks Sheet")
                    p.setFont('Times-Bold',11)
                    p.drawString(115,690,"Name:" )
                    p.setFont('Times-Bold',12)
                    p.drawString(149,690,stud_details[0].firstname+" "+stud_details[0].lastname)
                    p.setFont('Times-Roman',10)
                    p.drawString(465,690,"Roll No: ")
                    p.setFont('Times-Bold',10)
                    p.drawString(501, 690, stud_details[0].SID)
                    p.setFont('Times-BoldItalic',11)
                    p.drawString(115,670,"MASTER OF SCIENCE IN INFORMATION TECHNOLOGY")
                    p.setFont('Times-Roman',10)
                    p.drawString(115,650,"CGPA:")
                    p.drawString(115,630,"Credits Obtained:")
                    p.drawString(445,640,"PercentageRange:")
                    p.drawString(395,630,"Required Credits for Completion:")
                    p.setFont('Times-Bold',9)
                    p.drawString(115, 600, "Code")
                    p.drawString(235, 600, "Course Name")
                    p.drawString(435, 600, "Grade")
                    p.drawString(485, 600, "Credits")
                    
                    # gradeDictionary={'EX':10.0,'A+':9.5,'A':9.0,'B+':8.5,'B':8.0,'B-':7.5,'C':7.0,'Ex':10.0,'A-':9.0}
                    
                    p.drawString(115, 580, "Soft Skills")
                    p.setFont('Times-Roman',9)


                    grade_details= StudentMarks.objects.filter(SID = stud_details[0].SID)
                    temp = 0
                    for j in grade_details:
                        if j.grade == 'F':
                            sum_of_credits = 0
                            return HttpResponse('student has a F grade')

                        grade = gradeDictionary[j.grade.upper()]
                        
                        credits_details = Courses.objects.filter(CID=j.CID)

                        credits = credits_details[0].credits

                        if 'SS' in credits_details[0].CID :
                            p.drawString(445, (560-temp), j.grade)
                            p.drawString(115, (560-temp), credits_details[0].CID)
                            p.drawString(170, (560-temp), credits_details[0].CName)
                            p.drawString(505, (560-temp), str(credits))
                            # p.drawString(460, 650, str(credits))
                            temp = temp + 15

                    p.setFont('Times-Roman',9)
                    p.drawString(190, 630, str(sum_of_credits))
                    p.drawString(530, 630, str(sum_of_credits))
                    if not sum_of_credits == 0:
                        CGPA = GPA/sum_of_credits
                        p.drawString(150,650,str(round(CGPA,1)))
                    
                    # canvas.drawCentredString(2.75*inch, 2.5*inch, "Font size examples")
                    if CGPA == 10.0 :
                        p.drawString(520,640,"96-100") 
                    if CGPA >= 9.0 and CGPA <10.0:
                        p.drawString(520,640,"91-95")
                    if CGPA >= 8.0 and CGPA < 9.0:
                        p.drawString(520,640,"86-90")
                    if CGPA >= 7.0 and CGPA < 8.0:
                        p.drawString(520,640,"81-85")
                    if CGPA >= 6.0 and CGPA < 7.0:
                        p.drawString(520,640,"76-80")
                    if CGPA >= 5.0 and CGPA < 6.0:
                        p.drawString(520,640,"70-75")
                    if CGPA < 5.0:
                        p.drawString(520,640,"<70")


                    temp = temp + 80
                    p.setFont('Times-Bold',11)
                    p.drawString(400,560-temp,"Coordinator MSIT Division")

                    temp = temp + 250
                    p.setFont('Times-Italic',9)
                    p.drawString(115,70,"CGPA: Cumulative Grade Point Average")
                    temp = temp + 15
                    p.drawString(115,50,fullstring)

                    p.showPage()
                    p.save()
                    pdf= buffer.getvalue()
                    # fname = filename+".pdf"
                    fname.append(filename+".pdf")
                    in_memory = StringIO()
                # for file in zip.filelist:
                #     file.create_system = 0 
                print "stopping"
                print fname
                buffer.close()
                zip = ZipFile(in_memory,"a")
                for fpath in fname:
                    zip.writestr(fpath, pdf)

                zip.close()
                response = HttpResponse(content_type = "application/zip")
                response["Content-Disposition"] = "attachment; filename=bulk.zip"
                in_memory.seek(0)
                response.write(in_memory.read())
                return response

        except Student.DoesNotExist:
            stud_dic = {}
            stud_list = Student.objects.all();
            return render(request,("home.html", args), stud_dic)
    else:
        message = 'Enter a number in the Search bar'
        return HttpResponse(message)