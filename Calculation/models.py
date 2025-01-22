# models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from django.forms import ValidationError
# from decimal import Decimal
import math

class Room(models.Model):
    """Модель комнаты стандартной прямоугольной формы"""
    name = models.CharField('Название', max_length=100, default='Комната')
    width = models.FloatField('Ширина (м)', validators=[MinValueValidator(0.1)])
    length = models.FloatField('Длина (м)', validators=[MinValueValidator(0.1)])
    height = models.FloatField('Высота (м)', validators=[MinValueValidator(0.1)])
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def calculate_floor_ceiling_area(self):
        """Расчет площади пола/потолка"""
        return self.width * self.length
    
    def calculate_walls_area(self):
        """Расчет общей площади стен без проемов"""
        total_walls_area = 2 * (self.width + self.length) * self.height
        total_openings_area = sum(opening.calculate_area() for opening in self.openings.all())
        
        # Проверяем, чтобы площадь проемов не превышала 90% площади стен
        max_openings_area = total_walls_area * 0.9
        if total_openings_area > max_openings_area:
            raise ValueError('Общая площадь проемов превышает допустимую (90% от площади стен)')
            
        return max(0, total_walls_area - total_openings_area)
    
    def __str__(self):
        return f"Комната {self.name} ({self.width}x{self.length}x{self.height}м)"

    class Meta:
        verbose_name = 'Комната'
        verbose_name_plural = 'Комнаты'

class Opening(models.Model):
    """Модель для окон и дверей"""
    OPENING_TYPES = [
        ('window', 'Окно'),
        ('door', 'Дверь')
    ]
    
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='openings')
    opening_type = models.CharField('Тип проема', max_length=20, choices=OPENING_TYPES)
    width = models.FloatField('Ширина (м)', validators=[MinValueValidator(0.1)])
    height = models.FloatField('Высота (м)', validators=[MinValueValidator(0.1)])
    
    def clean(self):
        if not self.room:
            return
            
        # Проверка размеров проема относительно размеров комнаты
        if self.width > max(self.room.width, self.room.length):
            raise ValidationError('Ширина проема не может быть больше максимального размера стены')
            
        if self.height > self.room.height:
            raise ValidationError('Высота проема не может быть больше высоты комнаты')
    
    def calculate_area(self):
        """Расчет площади проема"""
        return self.width * self.height
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.get_opening_type_display()} {self.width}x{self.height}м"

    class Meta:
        verbose_name = 'Проем'
        verbose_name_plural = 'Проемы'

class RoomCalculation(models.Model):
    """Модель для сохранения расчетов"""
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='calculations')
    calculated_at = models.DateTimeField(auto_now_add=True)
    total_wall_area = models.FloatField('Общая площадь стен', default=0)
    total_floor_ceiling_area = models.FloatField('Общая площадь пола и потолка', default=0)
    openings_area = models.FloatField('Площадь проемов', default=0)
    
    def calculate(self):
        """Выполнение расчетов"""
        self.total_wall_area = self.room.calculate_walls_area()
        self.total_floor_ceiling_area = self.room.calculate_floor_ceiling_area()
        self.openings_area = sum(opening.calculate_area() for opening in self.room.openings.all())
        self.save()
    
    def __str__(self):
        return f"Расчет для {self.room.name} от {self.calculated_at.strftime('%d.%m.%Y %H:%M')}"

    class Meta:
        verbose_name = 'Расчет'
        verbose_name_plural = 'Расчеты'

class BaseMaterial(models.Model):
    """Базовый класс для всех материалов"""
    name = models.CharField('Название', max_length=100)
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    class Meta:
        abstract = True

    def calculate_quantity(self, room):
        """Базовый метод расчета количества материала"""
        raise NotImplementedError("Subclasses must implement calculate_quantity()")

class WallpaperMaterial(BaseMaterial):
    """Модель для обоев"""
    UNIT_CHOICES = [
        ('roll', 'Рулон'),
    ]
    
    width = models.FloatField('Ширина рулона (м)', validators=[MinValueValidator(0.1)])
    length = models.FloatField('Длина рулона (м)', validators=[MinValueValidator(0.1)])
    pattern_repeat = models.FloatField('Раппорт (м)', default=0, validators=[MinValueValidator(0)])
    unit = models.CharField('Единица измерения', max_length=10, choices=UNIT_CHOICES, default='roll')
    
    def calculate_quantity(self, room):
        """
        Расчет количества рулонов обоев для комнаты
        """
        # Общая площадь стен
        wall_area = room.calculate_walls_area()
        
        # Количество полос обоев по ширине стен
        strips = math.ceil(wall_area / (self.width * self.length))
        
        # Учет подгонки рисунка
        if self.pattern_repeat > 0:
            strips_with_pattern = math.ceil(room.height / self.pattern_repeat) * strips
        else:
            strips_with_pattern = strips
            
        # Добавляем запас 10%
        total_strips = math.ceil(strips_with_pattern * 1.1)
        
        return {
            'quantity': total_strips,
            'unit': self.get_unit_display(),
            'area': wall_area,
            'price': total_strips * self.price
        }

class PaintMaterial(BaseMaterial):
    """Модель для краски"""
    UNIT_CHOICES = [
        ('liter', 'Литр'),
    ]
    
    coverage = models.FloatField('Расход на м² (л)', validators=[MinValueValidator(0.1)])
    layers = models.IntegerField('Количество слоев', default=1, validators=[MinValueValidator(1)])
    unit = models.CharField('Единица измерения', max_length=10, choices=UNIT_CHOICES, default='liter')
    
    def calculate_quantity(self, room):
        """
        Расчет количества краски для комнаты
        """
        wall_area = room.calculate_walls_area()
        base_volume = wall_area * self.coverage * self.layers
        
        # Добавляем запас 5%
        total_volume = base_volume * 1.05
        
        return {
            'quantity': math.ceil(total_volume),
            'unit': self.get_unit_display(),
            'area': wall_area,
            'price': math.ceil(total_volume) * self.price
        }

class LaminateMaterial(BaseMaterial):
    """Модель для ламината"""
    UNIT_CHOICES = [
        ('pack', 'Упаковка'),
    ]
    
    length = models.FloatField('Длина доски (м)', validators=[MinValueValidator(0.1)])
    width = models.FloatField('Ширина доски (м)', validators=[MinValueValidator(0.1)])
    pieces_per_pack = models.IntegerField('Штук в упаковке', validators=[MinValueValidator(1)])
    unit = models.CharField('Единица измерения', max_length=10, choices=UNIT_CHOICES, default='pack')
    
    def calculate_quantity(self, room):
        """
        Расчет количества упаковок ламината для комнаты
        """
        floor_area = room.calculate_floor_ceiling_area()
        
        # Площадь одной упаковки
        pack_area = self.length * self.width * self.pieces_per_pack
        
        # Количество упаковок с учетом запаса 7%
        total_packs = math.ceil((floor_area * 1.07) / pack_area)
        
        return {
            'quantity': total_packs,
            'unit': self.get_unit_display(),
            'area': floor_area,
            'price': total_packs * self.price
        }

class TileMaterial(BaseMaterial):
    """Модель для плитки"""
    UNIT_CHOICES = [
        ('piece', 'Штука'),
    ]
    
    length = models.FloatField('Длина плитки (м)', validators=[MinValueValidator(0.1)])
    width = models.FloatField('Ширина плитки (м)', validators=[MinValueValidator(0.1)])
    pieces_per_pack = models.IntegerField('Штук в упаковке', validators=[MinValueValidator(1)])
    unit = models.CharField('Единица измерения', max_length=10, choices=UNIT_CHOICES, default='piece')
    
    def calculate_quantity(self, room):
        """
        Расчет количества плитки для комнаты
        """
        wall_area = room.calculate_walls_area()
        
        # Площадь одной плитки
        tile_area = self.length * self.width
        
        # Количество плиток с учетом запаса 10%
        total_tiles = math.ceil((wall_area * 1.10) / tile_area)
        
        # Округляем до целого числа упаковок
        total_packs = math.ceil(total_tiles / self.pieces_per_pack)
        
        return {
            'quantity': total_packs * self.pieces_per_pack,
            'unit': self.get_unit_display(),
            'area': wall_area,
            'price': total_packs * self.price,
            'packs': total_packs
        }

class MaterialCalculation(models.Model):
    """Модель для хранения результатов расчета"""
    room = models.ForeignKey('Room', on_delete=models.CASCADE, related_name='material_calculations')
    material_type = models.CharField('Тип материала', max_length=20)
    material_id = models.IntegerField('ID материала')
    quantity = models.FloatField('Количество')
    area = models.FloatField('Площадь')
    price = models.DecimalField('Стоимость', max_digits=10, decimal_places=2)
    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Расчет материала'
        verbose_name_plural = 'Расчеты материалов'

class DryWallMaterial(BaseMaterial):
    """Модель для гипсокартона"""
    UNIT_CHOICES = [
        ('sheet', 'Лист'),
    ]
    
    length = models.FloatField('Длина листа (м)', validators=[MinValueValidator(0.1)])
    width = models.FloatField('Ширина листа (м)', validators=[MinValueValidator(0.1)])
    thickness = models.FloatField('Толщина (мм)', validators=[MinValueValidator(0.1)])
    unit = models.CharField('Единица измерения', max_length=10, choices=UNIT_CHOICES, default='sheet')
    
    def calculate_quantity(self, room):
        """Расчет количества листов гипсокартона"""
        wall_area = room.calculate_walls_area()
        sheet_area = self.length * self.width
        
        # Добавляем запас 10%
        total_sheets = math.ceil((wall_area * 1.1) / sheet_area)
        
        return {
            'quantity': total_sheets,
            'unit': self.get_unit_display(),
            'area': wall_area,
            'price': total_sheets * self.price
        }

class BrickMaterial(BaseMaterial):
    """Модель для кирпича"""
    UNIT_CHOICES = [
        ('piece', 'Штука'),
    ]
    
    length = models.FloatField('Длина кирпича (мм)', validators=[MinValueValidator(0.1)])
    width = models.FloatField('Ширина кирпича (мм)', validators=[MinValueValidator(0.1)])
    height = models.FloatField('Высота кирпича (мм)', validators=[MinValueValidator(0.1)])
    mortar_thickness = models.FloatField('Толщина шва (мм)', default=10)
    unit = models.CharField('Единица измерения', max_length=10, choices=UNIT_CHOICES, default='piece')
    
    def calculate_quantity(self, room):
        """Расчет количества кирпичей"""
        wall_area = room.calculate_walls_area()
        
        # Переводим размеры в метры
        brick_length = self.length / 1000
        brick_height = self.height / 1000
        mortar = self.mortar_thickness / 1000
        
        # Площадь одного кирпича с учетом раствора
        brick_area = (brick_length + mortar) * (brick_height + mortar)
        
        # Количество кирпичей с запасом 5%
        total_bricks = math.ceil((wall_area / brick_area) * 1.05)
        
        return {
            'quantity': total_bricks,
            'unit': self.get_unit_display(),
            'area': wall_area,
            'price': total_bricks * self.price
        }

class FloorScreedMaterial(BaseMaterial):
    """Модель для стяжки пола"""
    UNIT_CHOICES = [
        ('cubic_meter', 'м³'),
    ]
    
    thickness = models.FloatField('Толщина стяжки (мм)', validators=[MinValueValidator(0.1)])
    unit = models.CharField('Единица измерения', max_length=15, choices=UNIT_CHOICES, default='cubic_meter')
    
    def calculate_quantity(self, room):
        """Расчет объема стяжки"""
        floor_area = room.calculate_floor_ceiling_area()
        
        # Переводим толщину в метры и считаем объем
        volume = floor_area * (self.thickness / 1000)
        
        # Добавляем запас 10%
        total_volume = volume * 1.1
        
        return {
            'quantity': round(total_volume, 2),
            'unit': self.get_unit_display(),
            'area': floor_area,
            'price': round(total_volume * self.price, 2)
        }

class ThermoPanelMaterial(BaseMaterial):
    """Модель для термопанелей"""
    UNIT_CHOICES = [
        ('panel', 'Панель'),
    ]
    
    length = models.FloatField('Длина панели (м)', validators=[MinValueValidator(0.1)])
    width = models.FloatField('Ширина панели (м)', validators=[MinValueValidator(0.1)])
    thickness = models.FloatField('Толщина (мм)', validators=[MinValueValidator(0.1)])
    unit = models.CharField('Единица измерения', max_length=15, choices=UNIT_CHOICES, default='panel')
    
    def calculate_quantity(self, room):
        """Расчет количества термопанелей"""
        wall_area = room.calculate_walls_area()
        panel_area = self.length * self.width
        
        # Добавляем запас 7%
        total_panels = math.ceil((wall_area * 1.07) / panel_area)
        
        return {
            'quantity': total_panels,
            'unit': self.get_unit_display(),
            'area': wall_area,
            'price': total_panels * self.price
        }

class StretchCeilingMaterial(BaseMaterial):
    """Модель для натяжных потолков"""
    UNIT_CHOICES = [
        ('square_meter', 'м²'),
    ]
    
    material_type = models.CharField('Тип материала', max_length=50)  # ПВХ, тканевые и т.д.
    unit = models.CharField('Единица измерения', max_length=15, choices=UNIT_CHOICES, default='square_meter')
    
    def calculate_quantity(self, room):
        """Расчет площади натяжного потолка"""
        ceiling_area = room.calculate_floor_ceiling_area()
        
        # Добавляем запас 5% для подворота
        total_area = ceiling_area * 1.05
        
        return {
            'quantity': round(total_area, 2),
            'unit': self.get_unit_display(),
            'area': ceiling_area,
            'price': round(total_area * self.price, 2)
        }

class ArmstrongCeilingMaterial(BaseMaterial):
    """Модель для потолка армстронг"""
    UNIT_CHOICES = [
        ('panel', 'Плита'),
    ]
    
    panel_size = models.FloatField('Размер плиты (мм)', validators=[MinValueValidator(0.1)])
    unit = models.CharField('Единица измерения', max_length=15, choices=UNIT_CHOICES, default='panel')
    
    def calculate_quantity(self, room):
        """Расчет количества плит армстронг"""
        ceiling_area = room.calculate_floor_ceiling_area()
        
        # Переводим размер плиты в метры и считаем площадь
        panel_area = (self.panel_size / 1000) ** 2
        
        # Добавляем запас 5%
        total_panels = math.ceil((ceiling_area * 1.05) / panel_area)
        
        return {
            'quantity': total_panels,
            'unit': self.get_unit_display(),
            'area': ceiling_area,
            'price': total_panels * self.price
        }

class GrillatoCeilingMaterial(BaseMaterial):
    """Модель для потолка грильято"""
    UNIT_CHOICES = [
        ('square_meter', 'м²'),
    ]
    
    cell_size = models.FloatField('Размер ячейки (мм)', validators=[MinValueValidator(0.1)])
    height = models.FloatField('Высота решетки (мм)', validators=[MinValueValidator(0.1)])
    unit = models.CharField('Единица измерения', max_length=15, choices=UNIT_CHOICES, default='square_meter')
    
    def calculate_quantity(self, room):
        """Расчет площади потолка грильято"""
        ceiling_area = room.calculate_floor_ceiling_area()
        
        # Добавляем запас 3%
        total_area = ceiling_area * 1.03
        
        return {
            'quantity': round(total_area, 2),
            'unit': self.get_unit_display(),
            'area': ceiling_area,
            'price': round(total_area * self.price, 2)
        }
    
class Template(models.Model):
    """Модель для сохранения шаблонов расчетов"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='templates')
    name = models.CharField('Название', max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    room = models.OneToOneField(Room, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Шаблон {self.name} ({self.created_at.strftime('%d.%m.%Y')})"

    class Meta:
        verbose_name = 'Шаблон'
        verbose_name_plural = 'Шаблоны'
        ordering = ['-created_at']

class TemplateMaterial(models.Model):
    """Модель для сохранения материалов в шаблоне"""
    template = models.ForeignKey(Template, on_delete=models.CASCADE, related_name='materials')
    material_type = models.CharField('Тип материала', max_length=50)
    data = models.JSONField('Данные материала')
    
    def __str__(self):
        return f"{self.get_material_type_display()} для {self.template.name}"

    class Meta:
        verbose_name = 'Материал шаблона'
        verbose_name_plural = 'Материалы шаблонов'