from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Customer(models.Model):
    name = models.CharField(max_length=100,null=False)
    email = models.EmailField(unique=True,null=False)
    phone = models.CharField(max_length=20,null=False)
    password = models.CharField(max_length=100,null=False)
    reset_code = models.CharField(max_length=6, null=True, blank=True)
    reset_code_expires_at = models.DateTimeField(null=True, blank=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.email

class Course(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # Default 0% discount
    active = models.BooleanField(default=True)  # To mark if the course is currently active or not
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)  # Image upload
    course_length = models.PositiveIntegerField(help_text='Course length in hours')
    purchased_by = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name
    
    def get_final_price(self):
        return self.price - (self.price * self.discount / 100)


class CourseResource(models.Model):
    RESOURCE_TYPES = [
        ('video', 'Video'),
        ('document', 'Document'),
        ('image', 'Image'),
        ('link', 'Link'),
    ]

    course = models.ForeignKey(Course, related_name='resources', on_delete=models.CASCADE)
    resource_type = models.CharField(max_length=10, choices=RESOURCE_TYPES)
    resource_file = models.FileField(upload_to='course_resources/', blank=True, null=True)
    resource_link = models.URLField(blank=True, null=True)
    resource_name = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.resource_name} ({self.get_resource_type_display()})'

class Payment(models.Model):
    user = models.ForeignKey(Customer, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.name} - {self.course.name} - {self.amount}"
    
class TestQuestion(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    question_text = models.TextField()
    option1 = models.CharField(max_length=255)
    option2 = models.CharField(max_length=255)
    option3 = models.CharField(max_length=255)
    option4 = models.CharField(max_length=255)
    correct_option = models.IntegerField()  # Use numbers to indicate the correct option (1-4)
    
class UserTestAttempt(models.Model):
    user = models.ForeignKey(Customer, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    passed = models.BooleanField(default=False)

class UserProgress(models.Model):
    user = models.ForeignKey(Customer, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    resources_viewed = models.ManyToManyField(CourseResource, blank=True)
    completed = models.BooleanField(default=False)
    
    def check_completion(self):
        total_resources = self.course.resources.count()
        if self.resources_viewed.count() == total_resources:
            self.completed = True
        else:
            self.completed = False
        self.save()

class ContactUs(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} - {self.email}"