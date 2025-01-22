from django.contrib import admin
from .models import Room, Opening, RoomCalculation

# Регистрирует модель Room (Комната) в админ-панели
@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    # Указывает какие поля будут отображаться в списке комнат:
    # название, ширина, длина, высота, пользователь и дата создания
    list_display = ('name', 'width', 'length', 'height', 'user', 'created_at')
    
    # Добавляет фильтры по пользователю и дате создания в боковой панели
    list_filter = ('user', 'created_at')
    
    # Добавляет поиск по названию комнаты и имени пользователя
    search_fields = ('name', 'user__username')

# Регистрирует модель Opening (Проемы) в админ-панели
@admin.register(Opening)
class OpeningAdmin(admin.ModelAdmin):
    # Указывает поля для отображения в списке проемов:
    # тип проема (окно/дверь), комната, ширина и высота
    list_display = ('opening_type', 'room', 'width', 'height')
    
    # Добавляет фильтры по типу проема и пользователю комнаты
    list_filter = ('opening_type', 'room__user')

# Регистрирует модель RoomCalculation (Расчеты комнаты) в админ-панели
@admin.register(RoomCalculation)
class RoomCalculationAdmin(admin.ModelAdmin):
    # Указывает поля для отображения в списке расчетов:
    # комната, дата расчета, общая площадь стен, площадь пола/потолка, площадь проемов
    list_display = ('room', 'calculated_at', 'total_wall_area', 'total_floor_ceiling_area', 'openings_area')
    
    # Добавляет фильтры по дате расчета и пользователю комнаты
    list_filter = ('calculated_at', 'room__user')
    
    # Делает поле даты расчета доступным только для чтения (нельзя изменить)
    readonly_fields = ('calculated_at',)