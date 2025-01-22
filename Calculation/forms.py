from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
# Импортирует все модели материалов из файла models.py
from .models import (ArmstrongCeilingMaterial, BrickMaterial, DryWallMaterial, 
                    FloorScreedMaterial, GrillatoCeilingMaterial, StretchCeilingMaterial, 
                    ThermoPanelMaterial, WallpaperMaterial, PaintMaterial, 
                    LaminateMaterial, TileMaterial)


# Создает форму регистрации пользователя, расширяя стандартную форму Django
class CustomUserCreationForm(UserCreationForm):
    # Добавляет поле для ввода email с обязательным заполнением
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',  # Добавляет CSS класс для стилизации
            'placeholder': 'Введите email'  # Добавляет подсказку в поле ввода
        })
    )
    
    # Добавляет поле для ввода имени пользователя
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Введите имя пользователя'
        })
    )
    
    # Добавляет поле для ввода пароля
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Введите пароль'
        })
    )
    
    # Добавляет поле для подтверждения пароля
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Подтвердите пароль'
        })
    )

    # Указывает модель и поля, которые будут использоваться в форме
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

# Создает форму авторизации, расширяя стандартную форму Django
class CustomAuthenticationForm(AuthenticationForm):
    # Настраивает поле для ввода имени пользователя
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Введите имя пользователя'
        })
    )
    
    # Настраивает поле для ввода пароля
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Введите пароль'
        })
    )

# Создает базовый класс формы для всех материалов
class BaseMaterialForm(forms.ModelForm):
    """Базовая форма для всех материалов"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляет CSS класс для всех полей формы
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

# Создает формы для каждого типа материала, наследуясь от базовой формы
class WallpaperForm(BaseMaterialForm):
    class Meta:
        model = WallpaperMaterial  # Указывает модель обоев
        # Определяет поля, которые будут в форме
        fields = ['name', 'price', 'width', 'length', 'pattern_repeat']
        widgets = {
            'pattern_repeat': forms.NumberInput(attrs={'step': '0.01'})  # Настраивает шаг для числового поля
        }

# Аналогично создаются формы для остальных материалов
class PaintForm(BaseMaterialForm):
    class Meta:
        model = PaintMaterial
        fields = ['name', 'price', 'coverage', 'layers']

class LaminateForm(BaseMaterialForm):
    class Meta:
        model = LaminateMaterial
        fields = ['name', 'price', 'length', 'width', 'pieces_per_pack']

class TileForm(BaseMaterialForm):
    class Meta:
        model = TileMaterial
        fields = ['name', 'price', 'length', 'width', 'pieces_per_pack']

class DryWallForm(BaseMaterialForm):
    class Meta:
        model = DryWallMaterial
        fields = ['name', 'price', 'length', 'width', 'thickness']

class BrickForm(BaseMaterialForm):
    class Meta:
        model = BrickMaterial
        fields = ['name', 'price', 'length', 'width', 'height', 'mortar_thickness']

class FloorScreedForm(BaseMaterialForm):
    class Meta:
        model = FloorScreedMaterial
        fields = ['name', 'price', 'thickness']

class ThermoPanelForm(BaseMaterialForm):
    class Meta:
        model = ThermoPanelMaterial
        fields = ['name', 'price', 'length', 'width', 'thickness']

class StretchCeilingForm(BaseMaterialForm):
    class Meta:
        model = StretchCeilingMaterial
        fields = ['name', 'price', 'material_type']

class ArmstrongCeilingForm(BaseMaterialForm):
    class Meta:
        model = ArmstrongCeilingMaterial
        fields = ['name', 'price', 'panel_size']

class GrillatoCeilingForm(BaseMaterialForm):
    class Meta:
        model = GrillatoCeilingMaterial
        fields = ['name', 'price', 'cell_size', 'height']


# Создает форму для выбора типа материала
class MaterialTypeForm(forms.Form):
    MATERIAL_CHOICES = [
        ('wallpaper', 'Обои'),
        ('paint', 'Краска'),
        ('laminate', 'Ламинат'),
        ('tile', 'Плитка'),
        ('drywall', 'Гипсокартон'),
        ('brick', 'Кирпич'),
        ('floor_screed', 'Стяжка пола'),
        ('thermo_panel', 'Термопанели'),
        ('stretch_ceiling', 'Натяжные потолки'),
        ('armstrong', 'Армстронг'),
        ('grillato', 'Грильято')
    ]
    # Создает поле выбора типа материала
    
    material_type = forms.ChoiceField(
        choices=MATERIAL_CHOICES,
        label='Тип материала',
        widget=forms.Select(attrs={'class': 'form-control'})
    )