import uuid
from django.template.loader import get_template
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from xhtml2pdf import pisa
import pandas as pd
from main.chat import get_conversations
from django.core.exceptions import ValidationError
from .models import *
from .forms import *
from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils.translation import activate, get_language
from django.urls import reverse


def set_language(request):
    if request.method == 'POST':
        language_code = request.POST.get('language')
        next_url = request.POST.get('next', '/')

        if language_code in dict(settings.LANGUAGES):
            activate(language_code)
            request.session[settings.LANGUAGE_COOKIE_NAME] = language_code

            response = HttpResponseRedirect(next_url)
            response.set_cookie(
                settings.LANGUAGE_COOKIE_NAME,
                language_code,
                max_age=365 * 24 * 60 * 60,
            )
            return response
    return HttpResponseRedirect('/')
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        if not email or not password:
            messages.error(request, 'Tafadhali jaza barua pepe na nenosiri')
            return redirect('login_view')

        try:
            user = authenticate(request, email=email, password=password)
            if user:
                login(request, user)
                messages.success(request, 'Umefanikiwa kuingia!')
                next_url = request.GET.get('next', 'home')
                return redirect(next_url if next_url.startswith('/') else 'home')
            else:
                messages.error(request, 'Barua pepe au nenosiri si sahihi')
        except Exception:
            messages.error(request, 'Hitilafu fulani imetokea, tafadhali jaribu tena')
        return redirect('login_view')

    return render(request, 'main/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        try:
            if form.is_valid():
                user = form.save()  # ← hakikisha hii inapata user
                print("User Created:", user)
                if user:
                    login(request, user)  # ← hakikisha login inafanyika
                    messages.success(request, 'Usajili umekamilika kikamilifu!')
                    return redirect('login_view')
                else:
                    messages.error(request, 'Haikuweza kujiandikisha, tafadhali jaribu tena')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field.capitalize()}: {error}")
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Hitilafu fulani imetokea wakati wa usajili: {str(e)}')
        return redirect('register')
    else:
        form = UserRegistrationForm()
    return render(request, 'main/register.html', {'form': form})


@login_required
def profile_view(request):
    return render(request, 'main/profile.html')

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out')
    return redirect('login_view')

# Main Views
def home(request):
    now = timezone.now()
    # Get all upcoming events
    upcoming_events = Event.objects.filter(
        start_date__gte=timezone.now()
    ).order_by('start_date')
    past_events = Event.objects.filter(start_date__lt=now).order_by('-start_date')
    
    # Get latest teachings
    latest_teachings = Teaching.objects.filter(
        media_type='VIDEO'
    ).order_by('-teaching_date')[:3]
    
    # Get latest blog posts
    latest_blogs = Blog.objects.filter(
        status='PUBLISHED'
    ).order_by('-published_at')[:3]
    
    context = {
        'upcoming_events': upcoming_events,
        'latest_teachings': latest_teachings,
        'past_events': past_events,
        'latest_blogs': latest_blogs,
    }
    return render(request, 'main/home.html', context)

# Teaching Views
@login_required
def teachings(request):
    query = request.GET.get('q', '')
    media_type = request.GET.get('media_type', '')
    
    teachings = Teaching.objects.all()
    
    if query:
        teachings = teachings.filter(
            Q(title__icontains=query) |
            Q(preacher__full_name__icontains=query) |
            Q(description__icontains=query)
        )
    
    if media_type:
        teachings = teachings.filter(media_type=media_type)
    
    # Pagination
    paginator = Paginator(teachings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'teachings': page_obj,
        'query': query,
        'media_type': media_type,
        'media_types': Teaching.MEDIA_TYPES,
    }
    return render(request, 'main/teachings.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def export_teachings_pdf(request):
    teachings = Teaching.objects.all().select_related('preacher')
    template = get_template('main/teachings_pdf.html')
    html = template.render({'teachings': teachings})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="teachings.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    
    return response

@login_required
@user_passes_test(lambda u: u.is_staff)
def export_teachings_excel(request):
    teachings = Teaching.objects.all().select_related('preacher')
    
    data = [{
        'Title': t.title,
        'Preacher': t.preacher.full_name,
        'Description': t.description[:100] + '...' if len(t.description) > 100 else t.description,
        'Date': t.teaching_date.strftime('%Y-%m-%d'),
        'Type': t.get_media_type_display(),
        'File': request.build_absolute_uri(t.media_file.url) if t.media_file else '',
    } for t in teachings]
    
    df = pd.DataFrame(data)
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="teachings.xlsx"'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    
    return response

# Schedule Views
def schedule_view(request):
    days = Schedule.DAY_CHOICES
    schedules = {}
    
    for day_code, day_name in days:
        day_schedules = Schedule.objects.filter(day=day_code).order_by('time')
        if day_schedules.exists():
            schedules[day_name] = day_schedules
    
    context = {
        'schedules': schedules,
        'days': days,
    }
    return render(request, 'main/schedule.html', context)

# Donation Views
@login_required
def donation_view(request):
    if request.method == 'POST':
        form = DonationForm(request.POST, user=request.user)
        if form.is_valid():
            with transaction.atomic():
                donation = form.save(commit=False)
                donation.donor = request.user
                donation.save()
            messages.success(request, 'Thank you for your donation!')
            return redirect('donation-list')
    else:
        form = DonationForm(user=request.user)

    return render(request, 'main/donation.html', {'form': form})


@login_required
def donation_list(request):
    donations = Donation.objects.all().order_by('-date')
    context = {'donations': donations}
    return render(request, 'main/donation_list.html', context)


@login_required
def add_donation(request):
    if request.method == 'POST':
        form = DonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            payment_method = form.cleaned_data['payment_method']

            # Handle extra payment info
            if 'bank' in payment_method.lower():
                donation.card_number = request.POST.get('card_number', '')
            elif 'mobile' in payment_method.lower():
                donation.mobile_number = request.POST.get('mobile_number', '')
            
            donation.save()
            return redirect('donation_list')
    else:
        form = DonationForm()

    return render(request, 'main/add_donation.html', {'form': form})

@login_required
def donation_detail(request, pk):
    try:
        donation = Donation.objects.get(pk=pk, donor=request.user)
    except Donation.DoesNotExist:
        messages.error(request, "Donation not found or you don't have permission to view it.")
        return redirect('donation_list')
        
    return render(request, 'main/donation_detail.html', {'donation': donation})

@login_required
def edit_donation(request, pk):
    donation = get_object_or_404(Donation, pk=pk, donor=request.user)
    if request.method == 'POST':
        form = DonationForm(request.POST, instance=donation)
        if form.is_valid():
            form.save()
            messages.success(request, 'Donation updated successfully!')
            return redirect('donation_detail', pk=donation.pk)
    else:
        form = DonationForm(instance=donation)
    
    # Make sure to pass both form and donation to the template
    return render(request, 'main/edit_donation.html', {
        'form': form,
        'donation': donation  # This was missing
    })

@login_required
def delete_donation(request, pk):
    donation = get_object_or_404(Donation, pk=pk, donor=request.user)
    if request.method == 'POST':
        donation.delete()
        messages.success(request, 'Donation deleted successfully!')
        return redirect('donation_list')
    return render(request, 'main/delete_donation.html', {'donation': donation})

# Event Views
def events_view(request):
    now = timezone.now()
    upcoming_events = Event.objects.filter(start_date__gte=now).order_by('start_date')
    past_events = Event.objects.filter(start_date__lt=now).order_by('-start_date')
    
    context = {
        'upcoming_events': upcoming_events,
        'past_events': past_events,
    }
    return render(request, 'main/events.html', context)

@login_required
def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    is_attending = event.attendees.filter(id=request.user.id).exists()
    
    if request.method == 'POST':
        if not is_attending:
            EventAttendance.objects.create(event=event, user=request.user)
            messages.success(request, 'You have registered for this event')
        else:
            EventAttendance.objects.filter(event=event, user=request.user).delete()
            messages.info(request, 'You have canceled your registration')
        return redirect('event-detail', pk=pk)
    
    context = {
        'event': event,
        'is_attending': is_attending,
        'attendees_count': event.attendees.count(),
    }
    return render(request, 'main/event_detail.html', context)

# Blog Views
def blog_view(request):
    blogs = Blog.objects.filter(status='PUBLISHED').order_by('-published_at')
    context = {'blogs': blogs}
    return render(request, 'main/blog.html', context)

@login_required
def blog_detail(request, slug):
    blog = get_object_or_404(Blog, slug=slug)
    
    if blog.status != 'PUBLISHED' and not request.user.is_staff:
        raise PermissionDenied
    
    context = {'blog': blog}
    return render(request, 'main/blog_detail.html', context)

# Chat Views
@login_required
def chat_home(request):
    # Get all conversations where the user is either sender or recipient
    conversations = Message.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user))
    
    # Get unique users the current user has chatted with
    chat_partners = User.objects.filter(
        Q(sent_messages__recipient=request.user) | 
        Q(received_messages__sender=request.user)
    ).distinct()
    
    # Get the latest message for each conversation
    conversations = []
    for partner in chat_partners:
        last_message = Message.objects.filter(
            Q(sender=request.user, recipient=partner) |
            Q(sender=partner, recipient=request.user)
        ).order_by('-created_at').first()
        
        if last_message:
            conversations.append({
                'user': partner,
                'last_message': last_message,
                'unread_count': Message.objects.filter(
                    sender=partner,
                    recipient=request.user,
                    is_read=False
                ).count()
            })
    
    # Sort conversations by most recent message
    conversations.sort(key=lambda x: x['last_message'].created_at, reverse=True)
    
    context = {'conversations': conversations}
    return render(request, 'main/chat.html', context)


@login_required
def send_message(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        recipient_id = request.POST.get('recipient')
        content = request.POST.get('content')
        
        try:
            recipient = User.objects.get(id=recipient_id)
            message = Message.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content
            )
            return JsonResponse({
                'status': 'success',
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'timestamp': message.created_at.strftime('%b %d, %Y %I:%M %p'),  # Changed from timestamp to created_at
                    'sender': request.user.username
                }
            })
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Recipient not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required
def chat_home(request):
    # Get all conversations with last message and unread count
    conversations = []
    users = User.objects.filter(
        Q(sent_messages__recipient=request.user) |
        Q(received_messages__sender=request.user)
    ).distinct()
    
    for user in users:
        last_message = Message.objects.filter(
            Q(sender=request.user, recipient=user) |
            Q(sender=user, recipient=request.user)
        ).order_by('-created_at').first()
        
        unread_count = Message.objects.filter(
            sender=user,
            recipient=request.user,
            is_read=False
        ).count()
        
        conversations.append({
            'user': user,
            'last_message': last_message,
            'unread_count': unread_count
        })
    
    # Get user's groups
    groups = ChatGroup.objects.filter(members=request.user)
    
    context = {
        'conversations': sorted(
            conversations,
            key=lambda x: x['last_message'].created_at if x['last_message'] else timezone.now(),
            reverse=True
        ),
        'groups': groups,
    }
    return render(request, 'main/chat.html', context)

@login_required
def chat_detail(request, user_id):
    other_user = get_object_or_404(User, pk=user_id)
    
    # Mark messages as read
    Message.objects.filter(
        sender=other_user,
        recipient=request.user,
        is_read=False
    ).update(is_read=True)
    
    messages = Message.objects.filter(
        Q(sender=request.user, recipient=other_user) |
        Q(sender=other_user, recipient=request.user)
    ).order_by('created_at')
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.recipient = other_user
            message.save()
            
            # Return JSON for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': {
                        'content': message.content,
                        'created_at': message.created_at.strftime('%b %d, %Y %I:%M %p'),
                        'sender': request.user.get_full_name()
                    }
                })
            
            return redirect('chat-detail', user_id=user_id)
    else:
        form = MessageForm()
    
    context = {
        'other_user': other_user,
        'messages': messages,
        'form': form,
    }
    return render(request, 'main/chat_detail.html', context)

@login_required
def create_group(request):
    if request.method == 'POST':
        form = ChatGroupForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            group = form.save(commit=False)
            group.creator = request.user
            group.save()
            
            # Add creator as admin
            GroupMembership.objects.create(
                group=group,
                user=request.user,
                role='ADMIN'
            )
            
            # Add selected members
            for member in form.cleaned_data['members']:
                GroupMembership.objects.create(
                    group=group,
                    user=member,
                    role='MEMBER'
                )
            
            messages.success(request, 'Group created successfully!')
            return redirect('group-chat', group_id=group.id)
    else:
        form = ChatGroupForm(user=request.user)
    
    context = {'form': form}
    return render(request, 'main/create_group.html', context)


@login_required
def group_chat(request, group_id):
    group = get_object_or_404(ChatGroup, pk=group_id)
    membership = get_object_or_404(GroupMembership, group=group, user=request.user)
    
    # Get admin count and pass to template
    admin_count = GroupMembership.objects.filter(group=group, role='ADMIN').count()
    
    messages = group.messages.all().order_by('created_at')
    
    if request.method == 'POST':
        form = GroupMessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.group = group
            message.sender = request.user
            message.save()
            return redirect('group-chat', group_id=group_id)
    else:
        form = GroupMessageForm()
    
    context = {
        'group': group,
        'messages': messages,
        'form': form,
        'membership': membership,
        'admin_count': admin_count,
    }
    return render(request, 'main/group_chat.html', context)

@login_required
def leave_group(request, group_id):
    group = get_object_or_404(ChatGroup, pk=group_id)
    membership = get_object_or_404(GroupMembership, group=group, user=request.user)
    
    if membership.role == 'ADMIN' and group.admin_count() == 1:
        # Last admin - delete the group
        group.delete()
        messages.success(request, f"You've left and the group '{group.name}' has been deleted.")
    else:
        # Regular member or admin with other admins remaining
        membership.delete()
        messages.success(request, f"You've left the group '{group.name}'.")
    
    return redirect('chat-home')
@login_required
def manage_group(request, group_id):
    group = get_object_or_404(ChatGroup, pk=group_id)
    membership = get_object_or_404(GroupMembership, group=group, user=request.user)
    
    # Only admins can manage the group
    if membership.role != 'ADMIN':
        messages.error(request, "You don't have permission to manage this group")
        return redirect('group-chat', group_id=group_id)
    
    members = GroupMembership.objects.filter(group=group).select_related('user')
    pending_requests = GroupRequest.objects.filter(group=group, status='PENDING')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        
        if action == 'remove_member':
            user = get_object_or_404(User, pk=user_id)
            if user != request.user:  # Can't remove yourself
                GroupMembership.objects.filter(group=group, user=user).delete()
                messages.success(request, f"{user.get_full_name()} has been removed from the group")
        
        elif action == 'promote_to_admin':
            user = get_object_or_404(User, pk=user_id)
            membership = GroupMembership.objects.get(group=group, user=user)
            membership.role = 'ADMIN'
            membership.save()
            messages.success(request, f"{user.get_full_name()} has been promoted to admin")
        
        elif action == 'demote_to_member':
            user = get_object_or_404(User, pk=user_id)
            membership = GroupMembership.objects.get(group=group, user=user)
            membership.role = 'MEMBER'
            membership.save()
            messages.success(request, f"{user.get_full_name()} has been demoted to member")
        
        elif action == 'update_group':
            form = ChatGroupForm(request.POST, request.FILES, instance=group, user=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, "Group details updated successfully")
        
        return redirect('manage-group', group_id=group_id)
    
    else:
        form = ChatGroupForm(instance=group, user=request.user)
    
    context = {
        'group': group,
        'members': members,
        'pending_requests': pending_requests,
        'form': form,
    }
    return render(request, 'main/manage_group.html', context)

@login_required
def check_messages(request):
    unread = Message.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'unread': unread})