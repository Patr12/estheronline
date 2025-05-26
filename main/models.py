from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    """Custom user model manager with email as the unique identifier"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser, PermissionsMixin):
    """Custom User Model with enhanced security and permissions"""
    
    ROLES = (
        ('ADMIN', 'Administrator'),
        ('PASTOR', 'Pastor'),
        ('LEADER', 'Ministry Leader'),
        ('MEMBER', 'Church Member'),
        ('GUEST', 'Guest'),
    )
    
    username = None
    email = models.EmailField(_('email address'), unique=True)
    full_name = models.CharField(_('full name'), max_length=255)
    role = models.CharField(max_length=20, choices=ROLES, default='MEMBER')
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    
    objects = CustomUserManager()
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return f"{self.full_name} ({self.email})"

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)  # Ya awali yenye null
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)  # Ya awali yenye null
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    
    class Meta:
        abstract = True


class Schedule(BaseModel):
    DAY_CHOICES = [
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
        ('SUN', 'Sunday'),
    ]
    
    title = models.CharField(max_length=100)
    time = models.TimeField()
    day = models.CharField(max_length=3, choices=DAY_CHOICES)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    responsible_person = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='schedules')
    
    class Meta:
        ordering = ['day', 'time']
        verbose_name = _('schedule')
        verbose_name_plural = _('schedules')
        indexes = [
            models.Index(fields=['day']),
            models.Index(fields=['time']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['day', 'time', 'title'], name='unique_schedule')
        ]
    
    def __str__(self):
        return f"{self.get_day_display()} - {self.title} at {self.time}"

class Donation(BaseModel):
    DONATION_TYPES = [
        ('TITHE', 'Tithe'),
        ('OFFERING', 'Offering'),
        ('DONATION', 'General Donation'),
        ('BUILDING', 'Building Fund'),
        ('MISSION', 'Missions Fund'),
    ]
    
    donor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='donations', blank=True, null=True)
    donation_type = models.CharField(max_length=20, choices=DONATION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    reference_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    is_recurring = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=20, choices=[
        
        ('Mobile', 'Mobile'),        
        ('BANK', 'Bank Transfer'),
    ], default='Mobile')
    card_number = models.CharField(max_length=20, blank=True, null=True)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name = _('donation')
        verbose_name_plural = _('donations')
        indexes = [
            models.Index(fields=['donor']),
            models.Index(fields=['donation_type']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.donor.full_name} - {self.get_donation_type_display()} ({self.amount})"

class Event(BaseModel):
    title = models.CharField(max_length=100)
    start_date = models.DateTimeField( null=True, blank=True)
    end_date = models.DateTimeField(blank=True, null=True)
    description = models.TextField()
    location = models.CharField(max_length=200,  null=True, blank=True)
    image = models.ImageField(upload_to='events/', null=True, blank=True)
    attendees = models.ManyToManyField(User, through='EventAttendance', related_name='events')
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = _('event')
        verbose_name_plural = _('events')
        indexes = [
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.start_date.date()})"

class EventAttendance(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    registration_date = models.DateTimeField(auto_now_add=True)
    attended = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('event', 'user')
        verbose_name = _('event attendance')
        verbose_name_plural = _('event attendances')

class Blog(BaseModel):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('ARCHIVED', 'Archived'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique_for_date='published_at', blank=True, null=True)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.PROTECT, related_name='blogs', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    published_at = models.DateTimeField(null=True, blank=True)
    featured_image = models.ImageField(upload_to='blog/', null=True, blank=True)
    
    class Meta:
        ordering = ['-published_at']
        verbose_name = _('blog')
        verbose_name_plural = _('blogs')
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status']),
            models.Index(fields=['author']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.status == 'PUBLISHED' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=100)
    subscribed_at = models.DateTimeField(auto_now_add=True,  null=True, blank=True)
    is_active = models.BooleanField(default=True)
    subscription_type = models.CharField(max_length=20, choices=[
        ('NEWSLETTER', 'Newsletter'),
        ('EVENTS', 'Events'),
        ('BOTH', 'Both'),
    ], default='BOTH')
    
    class Meta:
        ordering = ['-subscribed_at']
        verbose_name = _('subscriber')
        verbose_name_plural = _('subscribers')
    
    def __str__(self):
        return f"{self.full_name} ({self.email})"

class Teaching(BaseModel):
    MEDIA_TYPES = [
        ('VIDEO', 'Video'),
        ('AUDIO', 'Audio'),
        ('DOCUMENT', 'Document'),
    ]
    
    title = models.CharField(max_length=255)
    preacher = models.ForeignKey(User, on_delete=models.PROTECT, related_name='teachings')
    description = models.TextField()
    teaching_date = models.DateField()
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    media_file = models.FileField(
        upload_to='teachings/',
        validators=[FileExtensionValidator(allowed_extensions=['mp4', 'mp3', 'pdf', 'docx'])]
    )
    duration = models.DurationField(null=True, blank=True)
    category = models.CharField(max_length=50, blank=True)
    views = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-teaching_date']
        verbose_name = _('teaching')
        verbose_name_plural = _('teachings')
        indexes = [
            models.Index(fields=['preacher']),
            models.Index(fields=['teaching_date']),
            models.Index(fields=['media_type']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.preacher.full_name}"

class Message(BaseModel):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    attachment = models.FileField(
        upload_to='chat_attachments/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'pdf', 'docx'])]
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('message')
        verbose_name_plural = _('messages')
        indexes = [
            models.Index(fields=['sender']),
            models.Index(fields=['recipient']),
            models.Index(fields=['is_read']),
        ]
    
    def __str__(self):
        return f"Message from {self.sender} to {self.recipient}"

class ChatGroup(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(User, through='GroupMembership', related_name='chat_groups')
    is_private = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _('chat group')
        verbose_name_plural = _('chat groups')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    def admin_count(self):
        """Returns the number of admins in this group"""
        return self.memberships.filter(role='ADMIN').count()

class GroupMembership(models.Model):
    ROLES = [
        ('ADMIN', 'Admin'),
        ('MODERATOR', 'Moderator'),
        ('MEMBER', 'Member'),
    ]
    
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLES, default='MEMBER')
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('group', 'user')
        verbose_name = _('group membership')
        verbose_name_plural = _('group memberships')
    
    def __str__(self):
        return f"{self.user} in {self.group} as {self.role}"

class GroupMessage(BaseModel):
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    attachment = models.FileField(
        upload_to='group_attachments/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'pdf', 'docx'])]
    )
    
    class Meta:
        ordering = ['created_at']
        verbose_name = _('group message')
        verbose_name_plural = _('group messages')
        indexes = [
            models.Index(fields=['group']),
            models.Index(fields=['sender']),
        ]
    
    def __str__(self):
        return f"Message in {self.group} by {self.sender}"
    
class GroupRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name='requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('group', 'user')
    
    def __str__(self):
        return f"{self.user.username} request to {self.group.name} ({self.status})"    