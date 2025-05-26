from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('profile_view/', views.profile_view, name='profile_view'),
    path('teachings/', views.teachings, name='teachings'),
    path('export/pdf/', views.export_teachings_pdf, name='export_teachings_pdf'),
    path('export/excel/', views.export_teachings_excel, name='export_teachings_excel'),
   path('schedule/', views.schedule_view, name='schedule'),
    path('donation/', views.donation_view, name='donation'),
     path('add_donation/', views.add_donation, name='add_donation'),
    path('donation_list', views.donation_list, name='donation_list'),
    path('donations/<int:pk>/', views.donation_detail, name='donation_detail'),
     path('donations/<int:pk>/edit/', views.edit_donation, name='edit_donation'),
    path('donations/<int:pk>/delete/', views.delete_donation, name='delete_donation'),
    path('events/', views.events_view, name='events'),
    path('blog/', views.blog_view, name='blog'),
    path('login_view/', views.login_view, name='login_view'),
    path('logout_view/', views.logout_view, name='logout_view'),
    path('register/', views.register_view, name='register'),
    # function ya cahrt kwenye system yetu 
 path('chat/<int:user_id>/', views.chat_detail, name='chat-detail'),
    path('groups/create/', views.create_group, name='create-group'),
    path('groups/<int:group_id>/', views.group_chat, name='group-chat'),
    path('groups/<int:group_id>/manage/', views.manage_group, name='manage-group'),
    path('chat/', views.chat_home, name='chat-home'),
    path('groups/<int:group_id>/leave/', views.leave_group, name='leave-group'),
    path('api/check-messages/', views.check_messages, name='check-messages'),
     # Password reset routes
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
