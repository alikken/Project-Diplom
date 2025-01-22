# Django imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from django.http import JsonResponse, FileResponse, HttpResponse
from django.views.decorators.http import require_http_methods

# Python standard library
import json
import os
from datetime import datetime
from io import BytesIO

# Third party imports - ReportLab
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import xlsxwriter

# Local imports - Forms
from .forms import (
    ArmstrongCeilingForm, BrickForm, CustomUserCreationForm,
    CustomAuthenticationForm, DryWallForm, FloorScreedForm,
    GrillatoCeilingForm, StretchCeilingForm, ThermoPanelForm,
    MaterialTypeForm, WallpaperForm, PaintForm, LaminateForm, TileForm
)

# Local imports - Models
from .models import (
    ArmstrongCeilingMaterial, BrickMaterial, DryWallMaterial,
    FloorScreedMaterial, GrillatoCeilingMaterial, Room, Opening,
    StretchCeilingMaterial, Template, TemplateMaterial,
    ThermoPanelMaterial, User, MaterialCalculation,
    WallpaperMaterial, PaintMaterial, LaminateMaterial, TileMaterial
)

########################## LOGIN ############################################
def login_view(request):
    """
    Функция обрабатывает форму аутентификации (CustomAuthenticationForm),
    аутентифицирует пользователя и, если данные верны, 
    перенаправляет на главную страницу, отображая сообщение об успешном входе.
    В противном случае выводит сообщение об ошибке.
    """
    # Проверяем, что метод запроса — POST (переданы данные из формы)
    if request.method == 'POST':
        # Создаём объект формы аутентификации с данными из запроса
        form = CustomAuthenticationForm(request, data=request.POST)

        # Проверяем, валидна ли форма (корректность логина и пароля)
        if form.is_valid():
            # Получаем введённые пользователем данные
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # Пытаемся аутентифицировать пользователя
            user = authenticate(username=username, password=password)

            if user is not None:
                # Если пользователь прошёл аутентификацию, выполняем вход
                login(request, user)
                # Сообщаем об успешном входе
                messages.success(request, f'Добро пожаловать, {username}!')
                # Перенаправляем пользователя на главную страницу
                return redirect('home')
            else:
                # Пользователь или пароль неверны — сообщаем об ошибке
                messages.error(request, 'Неверное имя пользователя или пароль.')
        else:
            # Если форма не прошла валидацию — сообщаем об ошибке
            messages.error(request, 'Неверное имя пользователя или пароль.')
    else:
        # Если метод не POST, отображаем пустую форму для входа
        form = CustomAuthenticationForm()

    # Рендерим шаблон входа, передавая в контекст форму
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    """
    Функция производит выход пользователя из системы 
    и перенаправляет его на главную страницу.
    """
    # Вызываем встроенную функцию Django для очистки сессии и выходa пользователя
    logout(request)
    # Перенаправляем на главную страницу
    return redirect('home')



########################## REGISTRATION ############################################
def register_view(request):
    """
    Функция обрабатывает форму регистрации (CustomUserCreationForm),
    создаёт нового пользователя в системе и, при успешной регистрации,
    автоматически выполняет вход пользователя и перенаправляет на главную страницу.
    В случае ошибки — уведомляет пользователя соответствующим сообщением.
    """
    # Проверяем, что метод запроса — POST (переданы данные из формы)
    if request.method == 'POST':
        # Создаём объект формы регистрации с данными из запроса
        form = CustomUserCreationForm(request.POST)

        # Проверяем, валидна ли форма (соответствие требованиям полей, паролей и т.д.)
        if form.is_valid():
            # Если форма валидна, сохраняем нового пользователя
            user = form.save()
            # Выполняем вход только что зарегистрированного пользователя
            login(request, user)
            # Сообщаем об успешной регистрации
            messages.success(request, 'Регистрация успешна!')
            # Перенаправляем на главную страницу
            return redirect('home')
        else:
            # Если форма не прошла валидацию, сообщаем об ошибке
            messages.error(request, 'Ошибка регистрации. Пожалуйста, проверьте данные.')
    else:
        # Если метод не POST, отображаем пустую форму регистрации
        form = CustomUserCreationForm()

    # Рендерим шаблон регистрации, передавая в контекст форму
    return render(request, 'register.html', {'form': form})




########################## PROFILE VIEWS ############################################
@login_required
def profile_view(request):
    """
    Отображает страницу профиля пользователя, в которой выводится 
    список сохранённых шаблонов комнат (Template), принадлежащих 
    текущему пользователю. 
   
    Параметры:
      request (HttpRequest): Запрос, в котором хранится 
      информация о пользователе и т.д. 

    Возвращает:
      HttpResponse: HTML-страница 'profile.html' с данными 
      о пользователе и его шаблонах.
    """
    # Получаем все шаблоны, принадлежащие текущему пользователю,
    # с предварительной загрузкой связанных объектов (room, materials, openings)
    saved_templates = (
        Template.objects
        .filter(user=request.user)
        .select_related('room')
        .prefetch_related('materials', 'room__openings')
        .order_by('-created_at')
    )

    # Подготавливаем данные для каждого шаблона, чтобы удобнее было 
    # выводить их на странице. Формируем список словарей:
    templates_data = []
    for template in saved_templates:
        room = template.room  # Получаем связанную комнату
        data = {
            'id': template.id,
            'name': room.name,  # Используем имя комнаты как имя шаблона
            'length': room.length,
            'width': room.width,
            'height': room.height,
            # Преобразуем дату создания в человекочитаемый формат (день.месяц.год часы:минуты)
            'created_at': template.created_at.strftime('%d.%m.%Y %H:%M'),
            'materials_count': template.materials.count(),  # Количество материалов
            'openings_count': room.openings.count(),        # Количество проёмов
            # Вычисляем общую площадь пола/потолка и округляем до 2 знаков
            'total_area': round(room.calculate_floor_ceiling_area(), 2)
        }
        templates_data.append(data)

    # Рендерим шаблон 'profile.html', передавая в контекст:
    # - объект пользователя request.user
    # - список подготовленных данных о шаблонах
    return render(request, 'profile.html', {
        'user': request.user,
        'templates': templates_data
    })

@login_required
@require_http_methods(["POST"])
def save_template(request):
    """
    Обрабатывает POST-запрос с данными комнаты, проёмов и материалов в формате JSON.
    В результате:
      1. Создаётся объект Room (связан с текущим пользователем).
      2. Создаются объекты Opening для каждого проёма, указанного в данных.
      3. Создаётся объект Template, привязанный к пользователю и созданной комнате.
      4. Создаются объекты TemplateMaterial для каждого материала из JSON-данных.
      5. Возвращается JSON-ответ с ID созданного шаблона (или сообщением об ошибке).

    Параметры:
      request (HttpRequest): 
        - Ожидается, что тело запроса содержит JSON-данные:
          {
            "room": {
                "name": "Название комнаты",
                "width": ...,
                "length": ...,
                "height": ...
            },
            "openings": [
                {"type": "...", "width": ..., "height": ...},
                ...
            ],
            "materials": [
                {"type": "...", "some_other_key": "..."},
                ...
            ]
          }

    Возвращает:
      JsonResponse:
        - При успехе: { "success": True, "template_id": <ID шаблона> }
        - При ошибке: { "success": False, "error": "Сообщение об ошибке" }
    """
    try:
        # Шаг 1: Считываем и парсим JSON-данные из тела запроса
        data = json.loads(request.body)
        
        # Шаг 2: Создаём объект Room на основе переданных данных
        room_data = data['room']
        room = Room.objects.create(
            user=request.user,
            name=room_data['name'],
            width=float(room_data['width']),
            length=float(room_data['length']),
            height=float(room_data['height'])
        )
        
        # Шаг 3: Создаём объекты Opening (проёмы) для этой комнаты
        for opening_data in data['openings']:
            Opening.objects.create(
                room=room,
                opening_type=opening_data['type'],
                width=float(opening_data['width']),
                height=float(opening_data['height'])
            )
        
        # Шаг 4: Создаём шаблон (Template), связанный с пользователем и созданной комнатой
        template = Template.objects.create(
            user=request.user,
            name=room_data['name'],
            room=room
        )
        
        # Шаг 5: Создаём объекты TemplateMaterial для каждого материала
        for material_data in data['materials']:
            TemplateMaterial.objects.create(
                template=template,
                material_type=material_data['type'],
                data=material_data
            )
        
        # При успешном сохранении всех данных возвращаем ID созданного шаблона
        return JsonResponse({
            'success': True,
            'template_id': template.id
        })
        
    except Exception as e:
        # При возникновении любой ошибки возвращаем сообщение об ошибке
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

    
@login_required
def get_template(request, template_id):
    """
    Возвращает в формате JSON данные о конкретном шаблоне (Template),
    принадлежащем текущему пользователю (request.user).

    Процесс:
      1. Ищется объект Template по переданному идентификатору (template_id) и пользователю.
         Если объект не найден, бросается исключение Template.DoesNotExist.
      2. Извлекаются связанные данные:
         - Room (с размерами и названием).
         - Opening (список проёмов: их тип, ширина, высота).
         - Materials (список материалов из TemplateMaterial).
      3. Формируется JSON-ответ, содержащий поля "room", "openings", "materials".
         При успехе возвращается { "success": True, "template": {...} }.
         При ошибке — { "success": False, "error": "Сообщение об ошибке" }.

    Параметры:
      request (HttpRequest): Запрос от клиента.
      template_id (int): Идентификатор шаблона, который нужно найти.

    Возвращает:
      JsonResponse: JSON с данными о шаблоне или сообщением об ошибке.
    """
    try:
        # Пытаемся получить Template с указанным ID, принадлежащий текущему пользователю.
        template = get_object_or_404(Template, id=template_id, user=request.user)
        
        # Извлекаем связанную комнату
        room = template.room
        # Составляем список проёмов (opening_type, width, height)
        openings = list(room.openings.values('opening_type', 'width', 'height'))
        
        # Сформируем список материалов (включая данные, сохранённые в поле data)
        materials = []
        for material in template.materials.all():
            # material.data может быть строкой, 
            # поэтому при необходимости декодируем JSON
            material_data = material.data
            if isinstance(material_data, str):
                material_data = json.loads(material_data)
            materials.append({
                'material_type': material.material_type,
                'data': material_data
            })
        
        # Формируем итоговый словарь с информацией о комнате, проёмах и материалах
        template_data = {
            'room': {
                'name': room.name,
                'width': room.width,
                'length': room.length,
                'height': room.height
            },
            'openings': openings,
            'materials': materials
        }
        
        # При успешной загрузке данных отправляем их обратно в JSON-ответе
        return JsonResponse({
            'success': True,
            'template': template_data
        })
        
    except Template.DoesNotExist:
        # Если шаблон не найден — возвращаем сообщение об ошибке со статусом 404
        return JsonResponse({
            'success': False,
            'error': 'Шаблон не найден'
        }, status=404)
    except Exception as e:
        # Ловим любые другие ошибки и возвращаем их в формате JSON
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    
@login_required
@require_http_methods(["DELETE"])
def delete_template(request, template_id):
    """
    Удаляет шаблон (Template) с указанным идентификатором, принадлежащий
    текущему пользователю (request.user). 

    Параметры:
      request (HttpRequest): 
        - Запрос, который ожидает метод DELETE.
      template_id (int): 
        - Идентификатор шаблона, который следует удалить.

    Возвращает:
      JsonResponse:
        - При успехе: { "success": True, "message": "Шаблон успешно удален" }
        - При ошибке:  { "success": False, "error": "Описание ошибки" }
    """
    try:
        # Пытаемся получить шаблон по ID, принадлежащий текущему пользователю.
        # Если не найдём — будет возвращён HTTP-ответ с кодом 404.
        template = get_object_or_404(Template, id=template_id, user=request.user)
        
        # Удаляем найденный шаблон
        template.delete()
        
        # Возвращаем JSON-ответ об успешном удалении
        return JsonResponse({
            'success': True,
            'message': 'Шаблон успешно удален'
        })
        
    except Exception as e:
        # В случае любой ошибки возвращаем её описание в формате JSON
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@require_http_methods(["DELETE"])
def delete_current_template(request):
    try:
        template_id = request.GET.get('template_id')
        if not template_id:
            raise ValueError('Template ID is required')
            
        template = get_object_or_404(Template, id=template_id, user=request.user)
        template.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Шаблон успешно удален'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    
########################## HOME VIEW ############################################
def home(request):
    return render(request, 'home.html')

def about_view(request):
    return render(request, 'about.html')

########################## CALCULATOR VIEWS ############################################
MATERIAL_TYPES = {
    'wallpaper': 'Обои',
    'paint': 'Краска',
    'laminate': 'Ламинат',
    'tile': 'Плитка',
    'drywall': 'Гипсокартон',
    'brick': 'Кирпич',
    'floor_screed': 'Стяжка пола',
    'thermo_panel': 'Термопанели',
    'stretch_ceiling': 'Натяжные потолки',
    'armstrong': 'Армстронг',
    'grillato': 'Грильято'
}

@login_required
@require_http_methods(["GET", "POST"])
def material_calculator_view(request):
    """
    Представляет собой универсальную вью-функцию для расчёта материалов
    по заданным параметрам комнаты и выбранным типам материалов. 
    Работает в двух режимах (GET и POST):

    1. GET-запрос:
       - Возвращает HTML-страницу 'calculator.html' с формами для ввода данных о комнате
         и материалах, необходимых для расчёта.

    2. POST-запрос:
       - Принимает JSON-данные из request.body:
         {
           "room": {"name": str, "width": float, "length": float, "height": float},
           "openings": [
             {"type": str, "width": float, "height": float},
             ...
           ],
           "materials": [
             {"type": "wallpaper", "price": float, ...},
             {"type": "paint", "price": float, ...},
             ...
           ]
         }
       - Создаёт объекты Room и Opening на основе переданных данных.
       - Для каждого выбранного материала вызывает соответствующий класс (material_map),
         который выполняет расчёт количества материала, цены и пр.
       - Возвращает JSON с результатами расчёта:
         {
           "success": True,
           "room_id": <ID созданной комнаты>,
           "calculations": [
             {
               "type": <тип материала>,
               "name": <человекочитаемое название материала>,
               "quantity": <количество>,
               "unit": <единица измерения>,
               "area": <объём/площадь>,
               "price": <итоговая стоимость>
             },
             ...
           ]
         }
       - В случае ошибки:
         {
           "success": False,
           "error": <Сообщение об ошибке>
         }

    Параметры:
      request (HttpRequest): Запрос от клиента. Может быть GET или POST.

    Возвращает:
      - GET: HttpResponse (рендерит 'calculator.html')
      - POST: JsonResponse (JSON-объект с результатами расчёта или сообщением об ошибке)
    """
    if request.method == 'POST':
        try:
            # Парсим JSON-данные из тела запроса
            data = json.loads(request.body)

            # Извлекаем данные комнаты
            room_data = data.get('room', {})
            materials_data = data.get('materials', [])

            # Создаём объект Room, связанный с текущим пользователем
            # При этом парсим float-параметры ширины, длины и высоты
            room = Room.objects.create(
                user=request.user,
                name=room_data.get('name', 'Новая комната'),
                width=float(room_data['width']),
                length=float(room_data['length']),
                height=float(room_data['height'])
            )

            # Создаём проёмы (Opening), если они переданы
            for opening_data in data.get('openings', []):
                Opening.objects.create(
                    room=room,
                    opening_type=opening_data['type'],
                    width=float(opening_data['width']),
                    height=float(opening_data['height'])
                )

            # Подготавливаем сопоставление типа материала с соответствующим классом
            material_map = {
                'wallpaper': WallpaperMaterial,
                'paint': PaintMaterial,
                'laminate': LaminateMaterial,
                'tile': TileMaterial,
                'drywall': DryWallMaterial,
                'brick': BrickMaterial,
                'floor_screed': FloorScreedMaterial,
                'thermo_panel': ThermoPanelMaterial,
                'stretch_ceiling': StretchCeilingMaterial,
                'armstrong': ArmstrongCeilingMaterial,
                'grillato': GrillatoCeilingMaterial
            }

            # Список, куда будем складывать результаты расчёта материалов
            calculations = []

            for material_data in materials_data:
                # Извлекаем тип материала и удаляем этот ключ из словаря, 
                # чтобы при инициализации класса не возникло конфликтов
                material_type = material_data.pop('type', None)
                if not material_type:
                    continue  # Если тип не указан, пропускаем

                # Находим соответствующий класс материала
                material_class = material_map.get(material_type)
                if not material_class:
                    continue  # Если нет такого класса, пропускаем

                try:
                    # Если в данных не указано название, 
                    # берём человекочитаемое название из словаря MATERIAL_TYPES
                    if 'name' not in material_data:
                        material_data['name'] = MATERIAL_TYPES.get(material_type, 'Неизвестный материал')

                    # Инициализируем класс материала, передавая параметры из material_data
                    material = material_class(**material_data)
                    # Вызываем метод расчёта, передавая нашу комнату
                    result = material.calculate_quantity(room)

                    # Добавляем результат в общий список
                    calculations.append({
                        'type': material_type,
                        'name': MATERIAL_TYPES.get(material_type, 'Неизвестный материал'),
                        'quantity': result['quantity'],  # кол-во материала
                        'unit': result.get('unit', ''),  # единица измерения (если предусмотрено в расчётах)
                        'area': result['area'],         # общая площадь или объём для расчёта
                        'price': float(material_data['price']) * result['quantity']  # итоговая стоимость
                    })
                except Exception as e:
                    # Если произошла ошибка при расчёте, выводим её в консоль для отладки
                    print(f"Error calculating {material_type}: {str(e)}")
                    continue

            # Возвращаем JSON-ответ с успехом и списком рассчитанных материалов
            return JsonResponse({
                'success': True,
                'room_id': room.id,
                'calculations': calculations
            })

        except Exception as e:
            # Возвращаем ошибку в случае любого исключения
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

    # Если метод GET — рендерим HTML-шаблон 'calculator.html' с формами для каждого типа материала
    return render(request, 'calculator.html', {
        'material_type_form': MaterialTypeForm(),
        'material_forms': {
            'wallpaper': WallpaperForm(),
            'paint': PaintForm(),
            'laminate': LaminateForm(),
            'tile': TileForm(),
            'drywall': DryWallForm(),
            'brick': BrickForm(),
            'floor_screed': FloorScreedForm(),
            'thermo_panel': ThermoPanelForm(),
            'stretch_ceiling': StretchCeilingForm(),
            'armstrong': ArmstrongCeilingForm(),
            'grillato': GrillatoCeilingForm()
        }
    })


@login_required
@require_http_methods(["POST"])
def add_material(request):
    """
    Обрабатывает POST-запрос для добавления данных о материале к расчёту 
    (без сохранения в БД). Возвращает информацию о созданном материале 
    в формате JSON.

    Ожидаемые данные в запросе (JSON):
    {
      "type": "wallpaper" | "paint" | "laminate" | "tile",
      "name": "...",
      "price": "...",
      ...  (другие поля, требуемые формой)
    }

    Процесс:
      1. Считываем JSON-данные из request.body и извлекаем 'type'.
      2. Определяем форму (FormClass) на основе 'type' через словарь form_map.
      3. Инициализируем форму, проверяем валидность.
      4. Если форма валидна, создаём экземпляр материала (commit=False), 
         чтобы не сохранять в БД, но получить актуальные поля.
      5. Возвращаем JSON с информацией о материале, 
         включая все поля, кроме 'name' и 'price' (которые передаются отдельно).
      6. При ошибке — возвращаем JSON со статусом 400 и сообщением об ошибке.

    Возвращает:
      JsonResponse:
        - При успехе: 
          {
            "success": True,
            "material": {
              "type": <тип материала>,
              "name": <название материала>,
              "price": <цена>,
              <другие поля из формы>
            }
          }
        - При ошибке: 
          {
            "success": False,
            "errors": <Ошибки валидации формы> (если есть)
            "error": <Сообщение об ошибке> (если возникло исключение)
          }
    """
    try:
        # Считываем и парсим JSON-данные
        data = json.loads(request.body)
        
        # Извлекаем тип материала из переданных данных
        material_type = data.get('type')
        
        # Словарь с сопоставлением типа материала и соответствующей формой
        form_map = {
            'wallpaper': WallpaperForm,
            'paint': PaintForm,
            'laminate': LaminateForm,
            'tile': TileForm
        }
        
        # Получаем класс формы на основе типа материала
        FormClass = form_map.get(material_type)
        if not FormClass:
            # Если тип не поддерживается или не передан, вызываем ошибку
            raise ValueError('Неверный тип материала')
            
        # Инициализируем форму данными из запроса
        form = FormClass(data)
        
        # Проверяем валидность формы
        if form.is_valid():
            # Создаём объект материала без сохранения в базу (commit=False)
            material = form.save(commit=False)
            # Собираем информацию о материале для ответа (без сохранения)
            return JsonResponse({
                'success': True,
                'material': {
                    'type': material_type,
                    'name': material.name,
                    'price': str(material.price),
                    # Добавляем остальные поля формы, кроме name и price
                    **{
                        field: getattr(material, field)
                        for field in form.fields
                        if field not in ['name', 'price']
                    }
                }
            })
        else:
            # Если форма не прошла валидацию — отправляем ошибки обратно
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    except Exception as e:
        # В случае любой другой ошибки возвращаем сообщение об ошибке
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@require_http_methods(["GET"])
def get_material_form(request, material_type):
    """
    Возвращает форму в формате JSON для конкретного типа материала, чтобы
    можно было динамически отображать поля формы на странице (например, через Ajax).

    Параметры:
      request (HttpRequest): Запрос, который вызывается методом GET.
      material_type (str): Тип материала (например, 'wallpaper', 'paint', 'laminate', 'tile').

    Возвращает:
      JsonResponse:
        - При успехе (если тип материала корректный):
          {
            "success": True,
            "fields": {
              "<имя_поля>": {
                "label": <строка_метки>,
                "html": <HTML_строка_для_рендеринга_поля>,
                "help_text": <текст_подсказки>
              },
              ...
            }
          }
        - При ошибке (если тип материала не найден):
          {
            "success": False,
            "error": "Неверный тип материала"
          }
    """
    # Отображаемые формы для соответствующих типов материалов
    form_map = {
        'wallpaper': WallpaperForm,
        'paint': PaintForm,
        'laminate': LaminateForm,
        'tile': TileForm
    }
    
    # Определяем класс формы на основе переданного типа материала
    FormClass = form_map.get(material_type)
    if not FormClass:
        # Если класс формы не найден, возвращаем ошибку
        return JsonResponse({
            'success': False,
            'error': 'Неверный тип материала'
        }, status=400)
    
    # Инициализируем пустую форму
    form = FormClass()
    
    # Собираем данные о каждом поле формы в словарь
    # (метка, HTML-строка поля, help_text для подсказок)
    fields_html = {}
    for field_name, field in form.fields.items():
        fields_html[field_name] = {
            'label': field.label,
            'html': str(form[field_name]),
            'help_text': field.help_text
        }
    
    # Возвращаем JSON с информацией о полях формы
    return JsonResponse({
        'success': True,
        'fields': fields_html
    })


@login_required
@require_http_methods(["POST"])
def save_calculation(request):
    """
    Сохраняет результаты расчёта материалов в базе данных для конкретной комнаты (Room).
    
    Ожидаемые данные в request.body (JSON):
      {
        "room_id": <int>,
        "calculations": [
          {
            "material_type": <str>,
            "material_id": <int>,
            "quantity": <float>,
            "area": <float>,
            "price": <float>
          },
          ...
        ]
      }

    Шаги:
      1. Извлекаем ID комнаты (room_id) из полученных данных и проверяем,
         что комната принадлежит текущему пользователю.
      2. Для каждого объекта из списка calculations создаём запись в 
         модели MaterialCalculation (привязываем её к комнате).
      3. Формируем и возвращаем JSON-ответ с информацией о сохранённых расчётах.
    
    Параметры:
      request (HttpRequest): Запрос, содержащий JSON-данные с информацией о расчёте.

    Возвращает:
      JsonResponse:
        - При успехе:
          {
            "success": True,
            "calculations": [
              {
                "id": <ID сохранённого расчёта>,
                "material_type": <str>,
                "quantity": <float>,
                "area": <float>,
                "price": <str>
              },
              ...
            ]
          }
        - При ошибке:
          {
            "success": False,
            "error": <Сообщение об ошибке>
          }
    """
    try:
        # Шаг 1: Считываем и парсим JSON-данные из тела запроса
        data = json.loads(request.body)
        room_id = data.get('room_id')

        # Получаем комнату, которая принадлежит текущему пользователю
        room = get_object_or_404(Room, id=room_id, user=request.user)

        # Список для сохранённых расчётов, чтобы вернуть их в ответе
        calculations = []

        # Шаг 2: Создаём записи в MaterialCalculation для каждого элемента в calculations
        for calc_data in data.get('calculations', []):
            # Создаём объект в БД
            calculation = MaterialCalculation.objects.create(
                room=room,
                material_type=calc_data['material_type'],
                material_id=calc_data.get('material_id', 0),  # если material_id не передан — используем 0
                quantity=calc_data['quantity'],
                area=calc_data['area'],
                price=calc_data['price']
            )

            # Формируем структуру для возврата данных по каждому расчёту
            calculations.append({
                'id': calculation.id,
                'material_type': calculation.material_type,
                'quantity': calculation.quantity,
                'area': calculation.area,
                'price': str(calculation.price)  # приводим к строке для единообразия
            })

        # Шаг 3: Возвращаем JSON, подтверждающий успешное сохранение расчётов
        return JsonResponse({
            'success': True,
            'calculations': calculations
        })

    except Exception as e:
        # При возникновении любой ошибки возвращаем её описание
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@require_http_methods(["GET"])
def get_saved_calculations(request):
    """
    Возвращает все ранее сохранённые расчёты материалов (MaterialCalculation) 
    для комнат, принадлежащих текущему пользователю. 

    Процесс:
      1. Извлекаем из базы все записи MaterialCalculation, связанные 
         с комнатами (Room), которые принадлежат request.user.
      2. Сортируем их по полю calculated_at в порядке убывания (новые сверху).
      3. Формируем список словарей, содержащих ключевую информацию по каждому расчёту:
         - ID расчёта
         - Название комнаты (room_name)
         - Тип материала (material_type)
         - Количество (quantity)
         - Площадь/объём (area)
         - Цена (price), приводим к строке
         - Дата/время расчёта (calculated_at), форматируем как YYYY-MM-DD HH:MM:SS
      4. Возвращаем этот список в формате JSON: 
         {
           "success": True,
           "calculations": [ ... ]
         }

    Возвращает:
      JsonResponse:
        - При успехе:
          {
            "success": True,
            "calculations": [
              {
                "id": <int>,
                "room_name": <str>,
                "material_type": <str>,
                "quantity": <float>,
                "area": <float>,
                "price": <str>,
                "calculated_at": <str>
              },
              ...
            ]
          }
        - При ошибке:
          {
            "success": False,
            "error": <str>
          }
    """
    try:
        # Получаем все записи MaterialCalculation для комнат текущего пользователя,
        # сортируя по дате расчёта в порядке убывания
        calculations = MaterialCalculation.objects.filter(
            room__user=request.user
        ).order_by('-calculated_at')
        
        # Формируем результирующий список расчётов
        results = []
        for calc in calculations:
            results.append({
                'id': calc.id,
                'room_name': calc.room.name,
                'material_type': calc.material_type,
                'quantity': calc.quantity,
                'area': calc.area,
                'price': str(calc.price),
                # Форматируем дату-время расчёта в удобочитаемый формат
                'calculated_at': calc.calculated_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Возвращаем успешный ответ с данными о расчётах
        return JsonResponse({
            'success': True,
            'calculations': results
        })
        
    except Exception as e:
        # При возникновении любой ошибки возвращаем её описание
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@require_http_methods(["DELETE"])
def delete_calculation(request, calculation_id):
    """
    Удаляет сохранённый расчёт (MaterialCalculation) с указанным идентификатором (calculation_id),
    принадлежащий комнате текущего пользователя (request.user).

    Параметры:
      request (HttpRequest): Запрос, ожидающий метод DELETE.
      calculation_id (int): Идентификатор расчёта, который необходимо удалить.

    Возвращает:
      JsonResponse:
        - При успехе:
          {
            "success": True,
            "message": "Расчет успешно удален"
          }
        - При ошибке:
          {
            "success": False,
            "error": <сообщение об ошибке>
          }
    """
    try:
        # Пытаемся получить объект MaterialCalculation, который связан с пользователем через room
        calculation = get_object_or_404(
            MaterialCalculation,
            id=calculation_id,
            room__user=request.user
        )

        # Удаляем найденную запись
        calculation.delete()

        # Возвращаем сообщение об успешном удалении
        return JsonResponse({
            'success': True,
            'message': 'Расчет успешно удален'
        })

    except Exception as e:
        # Если возникла какая-либо ошибка, возвращаем её описание
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
def update_profile(request):
    """
    Обрабатывает запрос на обновление профиля текущего пользователя (username, email).
    Работает только с методом POST; данные принимаются в формате JSON из request.body.
    
    Ожидаемые данные (JSON):
      {
        "username": <новое_имя_пользователя>,
        "email": <новый_email>
      }

    Логика:
      1. Если метод запроса не POST, возвращаем ошибку (JSON).
      2. Парсим входные данные из JSON.
      3. Проверяем, изменился ли username. 
         - Если пользователь вводит новый username и он уже существует в БД, возвращаем ошибку.
         - Иначе устанавливаем его пользователю.
      4. Проверяем, изменился ли email.
         - Если пользователь вводит новый email и он уже занят в БД, возвращаем ошибку.
         - Иначе устанавливаем его пользователю.
      5. Сохраняем пользователя и возвращаем JSON-ответ об успехе.

    Возвращает:
      JsonResponse:
        - При успехе:
          {
            "success": True
          }
        - При ошибке:
          {
            "success": False,
            "error": <описание ошибки>
          }
    """
    # Проверяем метод запроса (должен быть POST)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        # Парсим JSON-данные из тела запроса
        data = json.loads(request.body)
        user = request.user

        # Проверяем уникальность нового username (если он действительно изменился)
        if data['username'] != user.username:
            if User.objects.filter(username=data['username']).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Это имя пользователя уже занято'
                })
            user.username = data['username']
            
        # Проверяем уникальность нового email (если он действительно изменился)
        if data['email'] != user.email:
            if User.objects.filter(email=data['email']).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Этот email уже используется'
                })
            user.email = data['email']
        
        # Сохраняем изменения в БД
        user.save()
        
        # Возвращаем успех
        return JsonResponse({'success': True})
        
    except Exception as e:
        # При возникновении любой ошибки возвращаем её описание
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def change_password(request):
    """
    Обрабатывает запрос на смену пароля для текущего пользователя. 
    Принимает данные в формате JSON:
      {
        "current_password": <str>,
        "new_password": <str>,
        "confirm_password": <str>
      }

    Шаги:
      1. Допускается только метод POST; если не POST, возвращаем ошибку.
      2. Парсим входные данные (JSON).
      3. Проверяем корректность текущего пароля (current_password).
      4. Проверяем совпадение нового пароля (new_password) и его подтверждения (confirm_password).
      5. Устанавливаем новый пароль пользователю и сохраняем изменения.
      6. Возвращаем JSON-ответ об успехе или ошибке.

    Возвращает:
      JsonResponse:
        - При успехе:
          {
            "success": True
          }
        - При ошибке:
          {
            "success": False,
            "error": "Сообщение об ошибке"
          }
    """
    # Разрешаем только POST-запросы
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        # Парсим JSON-данные
        data = json.loads(request.body)
        user = request.user
        
        # Проверяем, что введённый текущий пароль корректен
        if not check_password(data['current_password'], user.password):
            return JsonResponse({
                'success': False,
                'error': 'Неверный текущий пароль'
            })
            
        # Проверяем совпадение нового пароля и его подтверждения
        if data['new_password'] != data['confirm_password']:
            return JsonResponse({
                'success': False,
                'error': 'Пароли не совпадают'
            })
            
        # Устанавливаем новый пароль
        user.set_password(data['new_password'])
        user.save()
        
        # Возвращаем JSON-ответ об успехе
        return JsonResponse({'success': True})
        
    except Exception as e:
        # Если в процессе возникла ошибка — возвращаем описание
        return JsonResponse({'success': False, 'error': str(e)})


##########################EXPORT TO PDF|EXCEL ############################################
@login_required
@require_http_methods(["POST"])
def export_to_pdf(request):
    """
    Экспортирует результаты расчёта материалов в формате PDF-файла. 
    Ожидает POST-запрос с JSON-данными в теле (request.body).

    Формат входных данных (JSON):
      {
        "room": {
          "name": <str>,
          "length": <float>,
          "width": <float>,
          "height": <float>
        },
        "calculations": [
          {
            "materialName": <str>,
            "area": <float>,
            "quantity": <float>,
            "price": <float>
          },
          ...
        ],
        "summary": {
          "totalArea": <float>,
          "totalPrice": <float>
        }
      }

    Шаги:
      1. Регистрируется шрифт DejaVuSerif (поддерживающий кириллицу).
      2. Извлекается JSON из тела запроса и парсится в Python-словарь.
      3. Создаётся буфер BytesIO для формирования PDF.
      4. Конфигурируется объект SimpleDocTemplate с размером страницы letter и отступами.
      5. Настраиваются стили (getSampleStyleSheet) с использованием зарегистрированного шрифта.
      6. Формируется список Paragraph, Table и т.п. для построения структуры PDF:
         - Заголовок с названием комнаты
         - Информация о размерах комнаты
         - Таблица (Table) с результатами расчётов (материал, площадь, количество, стоимость)
         - Итоговая строка (Итого) с общей площадью и суммарной стоимостью
         - Дата расчёта
      7. Документ создаётся методом build(elements).
      8. Возвращается FileResponse с бинарным контентом PDF (attachment).
    
    Возвращает:
      FileResponse: 
        - Готовый PDF-файл со всеми расчётами.
      HttpResponse с кодом 400 при возникновении ошибки.
    """
    try:
        # Шаг 1: Регистрируем шрифт DejaVuSerif, который поддерживает кириллицу.
        font_path = os.path.join('static', 'fonts', 'DejaVuSerif.ttf')
        pdfmetrics.registerFont(TTFont('DejaVuSerif', font_path))

        # Шаг 2: Извлекаем и парсим JSON-данные из тела запроса
        raw_data = request.body.decode('utf-8')
        data = json.loads(raw_data)

        # Шаг 3: Создаём буфер для записи PDF
        buffer = BytesIO()

        # Шаг 4: Конфигурируем документ (размер letter, отступы)
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Шаг 5: Настраиваем стили
        styles = getSampleStyleSheet()
        styles['Title'].fontName = 'DejaVuSerif'
        styles['Normal'].fontName = 'DejaVuSerif'
        styles['Heading2'].fontName = 'DejaVuSerif'

        elements = []

        # Формируем заголовок
        title_text = f"Расчет материалов для комнаты '{data['room']['name']}'"
        title = Paragraph(title_text, styles['Title'])
        elements.append(title)

        # Информация о комнате
        room_info = [
            Paragraph("Размеры комнаты:", styles['Heading2']),
            Paragraph(f"Длина: {data['room']['length']} м", styles['Normal']),
            Paragraph(f"Ширина: {data['room']['width']} м", styles['Normal']),
            Paragraph(f"Высота: {data['room']['height']} м", styles['Normal']),
        ]
        elements.extend(room_info)

        # Подзаголовок для результатов расчета
        elements.append(Paragraph("Результаты расчета:", styles['Heading2']))

        # Таблица результатов
        table_data = [['Материал', 'Площадь (м²)', 'Количество', 'Стоимость']]
        for calc in data['calculations']:
            table_data.append([
                calc['materialName'],
                f"{calc['area']:.2f}",
                calc['quantity'],
                calc['price']
            ])

        # Итоговая строка (общая площадь и цена)
        table_data.append([
            'Итого:',
            f"{data['summary']['totalArea']:.2f}",
            '',
            data['summary']['totalPrice']
        ])

        # Создаём таблицу и указываем стили
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSerif'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)

        # Добавляем дату расчета
        elements.append(Paragraph(
            f"\nДата расчета: {datetime.now().strftime('%d.%m.%Y')}",
            styles['Normal']
        ))

        # Шаг 7: Генерируем PDF
        doc.build(elements)

        # Возвращаемся в начало буфера, чтобы сформировать ответ
        buffer.seek(0)

        # Шаг 8: Отправляем FileResponse с PDF-файлом
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=f'calculation_report_{datetime.now().strftime("%Y%m%d")}.pdf'
        )

    except Exception as e:
        # При любой ошибке вернём её текст
        return HttpResponse(str(e), status=400)

@login_required
@require_http_methods(["POST"])
def export_to_excel(request):
    """
    Экспортирует результаты расчёта материалов в формате Excel (.xlsx). 
    Ожидает POST-запрос с JSON-данными в теле (request.body).

    Формат входных данных (JSON):
      {
        "room": {
          "name": <str>,
          "length": <float>,
          "width": <float>,
          "height": <float>
        },
        "calculations": [
          {
            "materialName": <str>,
            "area": <float>,
            "quantity": <float>,
            "price": <float>
          },
          ...
        ],
        "summary": {
          "totalArea": <float>,
          "totalPrice": <float>
        }
      }

    Шаги:
      1. Получаем данные из запроса и парсим JSON.
      2. Создаём объект BytesIO для формирования Excel-файла в памяти.
      3. С помощью xlsxwriter создаём Workbook и Worksheet.
      4. Настраиваем форматы (bold, header, cell) для оформления текста, заголовков и ячеек.
      5. Заполняем Excel-файл:
         - Заголовок (название расчёта + имя комнаты)
         - Информация о комнате (длина, ширина, высота)
         - Таблица результатов (материал, площадь, количество, стоимость)
         - Итоговая строка (общая площадь и общая стоимость)
      6. Закрываем Workbook, перематываем буфер и возвращаем FileResponse с Excel-файлом.

    Возвращает:
      FileResponse:
        - Готовый .xlsx-файл с данными о расчёте.
      HttpResponse (status=400):
        - При возникновении ошибки (причина ошибки в тексте ответа).
    """
    try:
        # Шаг 1: Извлекаем и парсим JSON-данные из тела запроса
        data = json.loads(request.body)

        # Шаг 2: Создаём буфер в памяти для Excel-файла
        buffer = BytesIO()
        
        # Шаг 3: Создаём Excel-файл (Workbook) и добавляем лист (Worksheet)
        workbook = xlsxwriter.Workbook(buffer)
        worksheet = workbook.add_worksheet()
        
        # Шаг 4: Определяем стили (форматы) для ячеек
        bold = workbook.add_format({'bold': True})
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#CCCCCC',
            'border': 1
        })
        cell_format = workbook.add_format({'border': 1})
        
        # Заголовок (первая строка, ячейка A1)
        worksheet.write(
            'A1',
            f"Расчет материалов для комнаты '{data['room']['name']}'",
            bold
        )
        
        # Информация о комнате (начиная с A3)
        worksheet.write('A3', 'Параметры комнаты:', bold)
        worksheet.write('A4', f"Длина: {data['room']['length']} м")
        worksheet.write('A5', f"Ширина: {data['room']['width']} м")
        worksheet.write('A6', f"Высота: {data['room']['height']} м")
        
        # Заголовки таблицы (начиная с 8-й строки)
        headers = ['Материал', 'Площадь (м²)', 'Количество', 'Стоимость']
        for col, header_text in enumerate(headers):
            worksheet.write(7, col, header_text, header_format)
        
        # Шаг 5: Заполняем таблицу расчетов (начиная с 9-й строки)
        row = 8
        for calc in data['calculations']:
            worksheet.write(row, 0, calc['materialName'], cell_format)
            worksheet.write(row, 1, f"{calc['area']:.2f}", cell_format)
            worksheet.write(row, 2, calc['quantity'], cell_format)
            worksheet.write(row, 3, calc['price'], cell_format)
            row += 1
        
        # Итоговая строка (пустая строка и затем запись итогов)
        worksheet.write(row + 1, 0, 'Итого:', bold)
        worksheet.write(row + 1, 1, f"{data['summary']['totalArea']:.2f}", bold)
        worksheet.write(row + 1, 3, data['summary']['totalPrice'], bold)
        
        # Настраиваем ширину столбцов
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:D', 15)
        
        # Закрываем Workbook, чтобы файл корректно записался в буфер
        workbook.close()
        
        # Перематываем буфер в начало
        buffer.seek(0)
        
        # Шаг 6: Возвращаем FileResponse с Excel-файлом
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=f'calculation_report_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )
        
    except Exception as e:
        # При возникновении любой ошибки вернём её описание
        return HttpResponse(str(e), status=400)

    

