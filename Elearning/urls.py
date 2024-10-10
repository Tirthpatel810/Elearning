from django.contrib import admin
from django.urls import path
from Elearing_app import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('otp-verification/', views.otp_verification_view, name='otp_verification'), 
    path('profile/', views.profile_view, name='profile'),
    path('courses/', views.course_list_view, name='course_list'),
    path('courses/<int:course_id>/', views.course_detail_view, name='course_detail'),
    path('logout/', views.logout_view, name='logout'),
    path('enroll/<int:course_id>/', views.enroll_course_view, name='enroll_course'),
    path('payment/success/', views.payment_success_view, name='payment_success'),

    path('payment-success/<int:course_id>/<str:order_id>/', views.payment_success, name='payment_success'),
    path('razorpay-callback/', views.razorpay_callback, name='razorpay_callback'),
    path('my-courses/', views.my_courses, name='my_courses'),
    path('course-study/<int:course_id>/', views.course_study, name='course_study'),

    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-reset-code/', views.verify_reset_code, name='verify_reset_code'),
    path('reset-password/<int:user_id>/', views.reset_password, name='reset_password'),

    path('course-study/<int:course_id>/', views.course_study, name='course_study'),
    path('course-study/<int:course_id>/<int:resource_id>/', views.course_study, name='course_study_resource'),
    path('course-test/<int:course_id>/', views.course_test, name='course_test'),

    path('generate_certificate/<int:user_id>/<int:course_id>/', views.certificate_view, name='generate_certificate'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
