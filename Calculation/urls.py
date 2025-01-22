from django.urls import path
from .views import (
    about_view,
    change_password,
    delete_current_template,
    delete_template,
    export_to_excel,
    export_to_pdf,
    get_template,
    home,
    login_view,
    register_view,
    logout_view,
    profile_view,
    material_calculator_view,
    add_material,
    get_material_form,
    save_calculation,
    get_saved_calculations,
    delete_calculation,
    save_template,
    update_profile
)

auth_urlpatterns = [
    path('login/', login_view, name='login'),
    path('registration/', register_view, name='registration'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
]

urlpatterns = [
    path('', home, name='home'),
    path('home/', home, name='home'),
    path('calculator/', material_calculator_view, name='calculator'),
    path('add-material/', add_material, name='add_material'),
    path('get-material-form/<str:material_type>/', get_material_form, name='get_material_form'),
    path('save-calculation/', save_calculation, name='save_calculation'),
    path('get-saved-calculations/', get_saved_calculations, name='get_saved_calculations'),
    path('delete-calculation/<int:calculation_id>/', delete_calculation, name='delete_calculation'),
    path('calculate-materials/', material_calculator_view, name='calculate_materials'),
    path('export-to-pdf/', export_to_pdf, name='export_to_pdf'),
    path('export-to-excel/', export_to_excel, name='export_to_excel'),
    path('save-template/', save_template, name='save_template'),
    path('get-template/<int:template_id>/', get_template, name='get_template'),
    path('delete-template/<int:template_id>/', delete_template, name='delete_template'),
    path('delete-current-template/', delete_current_template, name='delete_current_template'),
    path('about/', about_view, name='about'),
    path('update-profile/', update_profile, name='update_profile'),
    path('change-password/', change_password, name='change_password'),
] + auth_urlpatterns