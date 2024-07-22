from django.urls import path
from . import views 
urlpatterns = [
    path('',views.index,name="index"),
    path('signup/',views.signup,name="signup"),
    path('log_in/',views.log_in,name="log_in"),
    path('log_out/',views.user_logout,name="log_out"),
    path('generate-blog/',views.generate_blog,name="generate_blog")
]
