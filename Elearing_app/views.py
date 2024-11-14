from datetime import timezone
from django.core.mail import EmailMessage
from django.utils import timezone
from django.shortcuts import render, redirect,get_object_or_404,HttpResponse
from django.contrib.auth import authenticate, login, logout
from Elearing_app.models import *
from django.contrib import messages
from django.contrib.auth.hashers import make_password,check_password
import random
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import logout
from functools import wraps
import razorpay
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from datetime import timedelta
import string
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from django.template import Context
from django.template.loader import render_to_string
from io import BytesIO


def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Assuming you are storing the user's email in session after login
        if request.session.get('email'):
            return view_func(request, *args, **kwargs)
        else:
            return redirect('login')
    return wrapper

def home(request):
    trending_courses = Course.objects.order_by('-purchased_by')[:8]
    context = {
        'trending_courses': trending_courses,
        # Add any other context data for the home page
    }
    return render(request, 'home.html', context)

def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        if Customer.objects.filter(email=email).exists():
            user = Customer.objects.get(email=email)
            if check_password(password, user.password):
                # Store the email in session after successful login
                request.session['email'] = email
                request.session['phone'] = user.phone
                request.session['name'] = user.name
                return redirect('home')  # Redirect to the home page after login
            else:
                messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Email not found. Please register first.')

    return render(request, 'login.html')

# Step 1: OTP Generation Helper Function
def generate_otp():
    return random.randint(100000, 999999)

# Step 2: Register View with OTP Sending and Verification
def register_view(request):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        phone = request.POST['phone']
        password = request.POST['password']

        # Check if email is already registered
        if Customer.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
        else:
            # Step 3: Generate and Send OTP
            otp = generate_otp()

            # Store OTP in session temporarily
            request.session['name'] = name
            request.session['email'] = email
            request.session['phone'] = phone
            request.session['password'] = make_password(password)
            request.session['otp'] = otp  # Store OTP for verification

            # Sending OTP to email (or you can use SMS with Twilio, etc.)
            send_mail(
                'Your OTP for Registration',
                f'Your OTP for account registration is {otp}.',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

            # Redirect to OTP verification page
            return redirect('otp_verification')

    return render(request, 'register.html')

# Step 4: OTP Verification View
def otp_verification_view(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')

        # Retrieve OTP from session
        saved_otp = request.session.get('otp')

        if str(entered_otp) == str(saved_otp):
            # OTP is correct, proceed with registration
            name = request.session.get('name')
            email = request.session.get('email')
            phone = request.session.get('phone')
            password = request.session.get('password')

            # Create the user
            user = Customer.objects.create(
                name=name,
                email=email,
                phone=phone,
                password=password
            )
            user.save()

            # Clear session data
            # del request.session['name']
            # del request.session['email']
            # del request.session['phone']
            del request.session['password']
            del request.session['otp']

            messages.success(request, 'Account created successfully. You can log in now.')
            return redirect('login')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')

    return render(request, 'otp_verification.html')

@login_required
def profile_view(request):
    try:
        user = Customer.objects.get(email=request.session['email'])
    except Customer.DoesNotExist:
        return redirect('login')

    return render(request, 'profile.html', {'user': user})

def logout_view(request):
    try:
        del request.session['email']
        request.session.flush()
    except KeyError:
        pass
    return redirect('home')

def course_list_view(request):
    courses = Course.objects.filter(active=True)

    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        courses = courses.filter(name__icontains=search_query)

    # Handle sorting
    sort_by = request.GET.get('sort', 'name')
    if sort_by in ['name', 'price', 'course_length']:
        courses = courses.order_by(sort_by)

    context = {
        'courses': courses,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    return render(request, 'course_list.html', context)

def course_detail_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    context = {
        'course': course
    }
    return render(request, 'course_detail.html', context)

def create_razorpay_order(course_id):
    # Get the course
    course = get_object_or_404(Course, id=course_id)
    
    # Razorpay client
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    # Payment details
    amount = int(course.get_final_price() * 100)  # Amount is in paise
    currency = 'INR'

    # Razorpay Order
    order = client.order.create({
        'amount': amount,
        'currency': currency,
        'payment_capture': 1
    })

    # Return order ID and details
    return order

@login_required
def enroll_course_view(request, course_id):
    user_email = request.session['email']
    course = get_object_or_404(Course, id=course_id)
    user_detail = get_object_or_404(Customer, email=user_email)

    if Payment.objects.filter(course=course, user=user_detail).exists():
        messages.error(request, 'You have already enrolled in this course.')
        return redirect('course_study', course_id=course_id)
    
    order = create_razorpay_order(course_id)
    context = {
        'course': course,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'order_id': order['id'],
        'amount': order['amount'],
        'currency': order['currency'],
        'user_detail': user_detail
    }
    return render(request, 'payment.html', context)

@csrf_exempt
def payment_success_view(request):
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id')
        order_id = request.POST.get('razorpay_order_id')
        signature = request.POST.get('razorpay_signature')

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            })

            # Payment is successful, update database, enroll student, etc.
            return HttpResponse("Payment Successful")

        except razorpay.errors.SignatureVerificationError:
            return HttpResponse("Payment Failed")

    return HttpResponse("Invalid Request")

# def payment_success(request, course_id, order_id):
    # Get the course based on the course_id
    course = get_object_or_404(Course, id=course_id)

    # Update course's purchased_by count
    course.purchased_by += 1
    course.save()

    # Create a new Payment record for the user
    Payment.objects.create(
        user=request.user,
        course=course,
        amount=course.get_final_price(),
        payment_date=timezone.now(),
    )

    # Redirect to the 'My Courses' page where user can see the course they purchased
    return redirect('my_courses')


@login_required
def my_courses(request):
    try:
        user = Customer.objects.get(email=request.session['email'])
    except Customer.DoesNotExist:
        return redirect('login')

    if user:
        purchased_courses = Payment.objects.filter(user=user)  # Fetch courses purchased by the logged-in user
    else:
        purchased_courses = []  # Or handle the case when the user is not found

    context = {'purchased_courses': purchased_courses}
    return render(request, 'my_courses.html', context)


@login_required
def course_study(request, course_id, resource_id=None):
    course = get_object_or_404(Course, id=course_id)
    user = get_object_or_404(Customer,email=request.session['email'])
    user_progress, created = UserProgress.objects.get_or_create(user=user, course=course)
    
    selected_resource = None
    if resource_id:
        selected_resource = get_object_or_404(CourseResource, id=resource_id)
        if selected_resource not in user_progress.resources_viewed.all():
            user_progress.resources_viewed.add(selected_resource)
        user_progress.check_completion()

    show_test_link = user_progress.completed

    context = {
        'course': course,
        'selected_resource': selected_resource,
        'user_progress': user_progress,
        'show_test_link': show_test_link,
    }
    return render(request, 'course_study.html', context)

@csrf_exempt
def razorpay_callback(request):
    if request.method == "POST":
        try:
            course_id = request.GET.get('course_id')
            user_email = request.GET.get('user_email')
            # Fetch the course and user instances
            course = get_object_or_404(Course, id=course_id)
            course.purchased_by += 1
            course.save()

            # Create a new Payment record for the user
            Payment.objects.create(
                user= get_object_or_404(Customer,email=user_email),
                course=course,
                amount=course.get_final_price(),
                payment_date=timezone.now(),
            )

            return redirect('my_courses')
        except Course.DoesNotExist:
            return HttpResponse("No Course matches the given query.", status=404)

    return redirect('home')

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST['email']

        # Check if the email exists in Customer
        user = None
        try:
            user = Customer.objects.get(email=email)
        except Customer.DoesNotExist:
            messages.error(request, "Email not found!")
            return redirect('forgot_password')

        # Generate a random reset code
        reset_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        # Save the reset code and expiration time (valid for 2 minutes)
        user.reset_code = reset_code
        user.reset_code_expires_at = timezone.now() + timedelta(minutes=2)
        user.save()

        # Send the reset code via email
        try:
            send_mail(
                'Password Reset Code',
                f'Your password reset code is: {reset_code}. It will expire in 2 minutes.',
                'ravitank267@gmail.com',
                [email],
                fail_silently=False,
            )
        except Exception as e:
            messages.error(request, f"Error sending email: {e}")
            return redirect('forgot_password')

        messages.success(request, "A reset code has been sent to your email.")
        return redirect('verify_reset_code')

    return render(request, 'forgot_password.html')

def verify_reset_code(request):
    if request.method == 'POST':
        reset_code = request.POST['reset_code']

        # Check for valid reset code in Customer
        user = None
        try:
            user = Customer.objects.get(reset_code=reset_code, reset_code_expires_at__gt=timezone.now())
        except Customer.DoesNotExist:
            messages.error(request, "Invalid or expired reset code!")
            return redirect('verify_reset_code')

        # If reset code is valid, proceed to reset password form
        return redirect('reset_password', user_id=user.id)

    return render(request, 'verify_reset_code.html')

def reset_password(request, user_id):
    # Try to find the user in Customer
    user = None
    try:
        user = Customer.objects.get(id=user_id)
    except Customer.DoesNotExist:
        messages.error(request, "User not found!")
        return redirect('login')

    if request.method == 'POST':
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('reset_password', user_id=user_id)

        # Update the user's password
        user.set_password(new_password)  # Set hashed password using the model's set_password method
        user.reset_code = None  # Clear the reset code
        user.reset_code_expires_at = None  # Clear the expiration time
        user.save()

        messages.success(request, "Password has been reset successfully!")
        return redirect('login')

    return render(request, 'reset_password.html', {'user_id': user_id})

@login_required
def course_test(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    questions = TestQuestion.objects.filter(course=course)
    
    if request.method == 'POST':
        score = 0
        for question in questions:
            selected_option = request.POST.get(f'question_{question.id}')
            if int(selected_option) == question.correct_option:
                score += 1
        
        passed = score >= 6
        user = get_object_or_404(Customer, email=request.session['email'])
        UserTestAttempt.objects.create(user=user, course=course, score=score, passed=passed)
        
        if passed:
            # Call function to generate certificate and send email
            generate_certificate_pdf(user, course)
        
        return render(request, 'test_result.html', {'score': score, 'passed': passed, 'user': user, 'course': course})

    return render(request, 'course_test.html', {'course': course, 'questions': questions})

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from datetime import datetime
from io import BytesIO

def generate_certificate_pdf(user, course):
    user_name = user.name  # Get the user's name from the 'user' object
    course_name = course.name  # Get the course's name from the 'course' object

    # Create a BytesIO buffer to store the PDF in memory
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # Set up the dimensions for the certificate
    width, height = letter  # 612x792 points
    margin = 40
    c.setPageSize((800, 600))  # Certificate size

    # Background and Border
    c.setStrokeColor(colors.HexColor("#4A90E2"))
    c.setLineWidth(10)
    c.rect(margin, margin, 720, 520, fill=0)

    # Title "Certificate of Completion"
    c.setFont("Helvetica-Bold", 48)
    c.setFillColor(colors.HexColor("#4A90E2"))
    c.drawString(100, 490, "Certificate of Completion")

    # Subtitle "Presented to"
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(colors.black)
    c.drawString(100, 430, "Presented to")

    # Recipient's Name
    c.setFont("Helvetica-Bold", 32)
    c.drawString(100, 370, user_name)

    # Course Name
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(colors.HexColor("#4A90E2"))
    c.drawString(100, 320, f"Course: {course_name}")

    # Certification Statement
    c.setFont("Helvetica", 18)
    c.setFillColor(colors.black)
    c.drawString(100, 270, "This certifies that the above-named individual has completed the course.")

    # Completion Date
    completion_date = datetime.now().strftime('%B %d, %Y')
    c.drawString(100, 230, f"Date of Completion: {completion_date}")

    # Signature
    c.setFont("Helvetica-Bold", 20)
    c.drawString(100, 150, "Authorized Signature")

    # Thank You Message
    c.setFont("Helvetica", 18)
    c.drawString(100, 100, "Thank you for your dedication and hard work!")

    # Save the PDF to the buffer
    c.save()

    # Seek to the beginning of the BytesIO buffer
    buffer.seek(0)

    return buffer

def certificate_view(request, user_id, course_id):
    # Fetch user and course instances
    user = get_object_or_404(Customer, id=user_id)
    course = get_object_or_404(Course, id=course_id)

    # Generate the certificate PDF in memory
    pdf_buffer = generate_certificate_pdf(user, course)

    # Send the certificate via email
    send_certificate_email(user, course, pdf_buffer)

    # Display success message
    messages.success(request, 'Your certificate has been sent to your email!')

    # Redirect to a success page (you can customize this)
    return redirect('my_courses')

def send_certificate_email(user, course, pdf_buffer):
    # Create an email
    subject = 'Your Course Completion Certificate'
    message = f'Dear {user.name},\n\nCongratulations on completing the course: {course.name}!\n\nPlease find your certificate attached.\n\nBest regards,\nYour Team'
    email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

    # Attach the PDF from the buffer
    email.attach(f'{user.name}_certificate.pdf', pdf_buffer.read(), 'application/pdf')

    # Send the email
    email.send()

def about(request):
    return render(request, 'about.html')

def contact_us(request):
    if request.method == 'POST':

        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        if name and email and message:
            ContactUs.objects.create(name=name, email=email, message=message)

            send_mail(
                'New Contact Us Message',
                f"Message from {name} ({email}):\n\n{message}",
                email,
                ['ravitank267@gmail.com'],
                fail_silently=False,
            )

            # Show success message
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('contact')
        else:
            messages.error(request, 'Please fill in all fields.')
    
    return render(request, 'contact.html')

def policy(request):
    return render(request, 'policy.html')

def t_and_c(request):
    return render(request, 't_and_c.html')