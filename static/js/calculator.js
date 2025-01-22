document.addEventListener('DOMContentLoaded', function() {
    // Проверяем наличие параметра template в URL
    const urlParams = new URLSearchParams(window.location.search);
    const templateId = urlParams.get('template');
    
    if (templateId) {
        loadTemplateData(templateId);
    }
});


// Глобальные переменные
let materials = new Map(); // Хранение материалов в формате Map для легкого доступа по ID
let openings = []; // Массив проемов

// Константы для типов материалов
const MATERIAL_TYPES = {
    wallpaper: 'Обои',
    paint: 'Краска',
    laminate: 'Ламинат',
    tile: 'Плитка',
    drywall: 'Гипсокартон',
    brick: 'Кирпич',
    floor_screed: 'Стяжка пола',
    thermo_panel: 'Термопанели',
    stretch_ceiling: 'Натяжные потолки',
    armstrong: 'Армстронг',
    grillato: 'Грильято'
};


// Функция для отображения выпадающего списка материалов
function toggleMaterialDropdown() {
    const materialsList = document.querySelector('.materials-dropdown');
    if (!materialsList) {
        // Создаем выпадающий список если его нет
        const dropdown = document.createElement('div');
        dropdown.className = 'materials-dropdown';
        
        // Создаем кнопки для каждого типа материала
        dropdown.innerHTML = Object.entries(MATERIAL_TYPES).map(([type, name]) => `
            <div class="material-option" onclick="addMaterialCard('${type}')">
                ${name}
            </div>
        `).join('');
        
        // Добавляем список после кнопки добавления
        const addButton = document.querySelector('.material-add-wrapper');
        addButton.appendChild(dropdown);
    } else {
        materialsList.remove();
    }
}

// Функция для создания карточки материала
function addMaterialCard(materialType, existingData = null) {
    const materialId = Math.floor(Date.now() / 1000); // Используем timestamp в секундах как ID
    const materialsList = document.getElementById('materialsList');
    
    const card = document.createElement('div');
    card.className = 'material-card';
    card.dataset.id = materialId;
    card.dataset.type = materialType;
    
    card.innerHTML = `
        <div class="material-header">
            <h3>${MATERIAL_TYPES[materialType]}</h3>
            <button type="button" class="delete-button" onclick="removeMaterial('${materialId}')">×</button>
        </div>
        <div class="material-content">
            ${getMaterialFields(materialType)}
        </div>
    `;
    
    materialsList.appendChild(card);
    
    // Закрываем выпадающий список материалов
    const dropdown = document.querySelector('.materials-dropdown');
    if (dropdown) dropdown.remove();
    
    // Если есть существующие данные, заполняем их
    if (existingData) {
        Object.entries(existingData).forEach(([key, value]) => {
            const input = card.querySelector(`[name="${key}"]`);
            if (input && value !== null && value !== undefined) {
                input.value = value;
                updateMaterialData(input);
            }
        });
    }
    
    // Добавляем материал в Map
    materials.set(materialId, {
        type: materialType,
        id: materialId,
        name: MATERIAL_TYPES[materialType],
        ...(existingData || {})
    });
}

// Получение HTML полей для разных типов материалов
function getMaterialFields(type) {
    const commonFields = `
        <div class="form-group">
            <label>Цена</label>
            <input type="number" class="form-input" name="price" min="0" step="0.01" oninput="updateMaterialData(this)">
        </div>
    `;
    
    const specificFields = {
        wallpaper: `
            <div class="form-group">
                <label>Ширина рулона (м)</label>
                <input type="number" class="form-input" name="width" min="0.1" step="0.01" oninput="updateMaterialData(this)">
            </div>
            <div class="form-group">
                <label>Длина рулона (м)</label>
                <input type="number" class="form-input" name="length" min="0.1" step="0.01" oninput="updateMaterialData(this)">
            </div>
            <div class="form-group">
                <label>Раппорт (м)</label>
                <input type="number" class="form-input" name="pattern_repeat" min="0" step="0.01" value="0" oninput="updateMaterialData(this)">
            </div>
        `,
        paint: `
            <div class="form-group">
                <label>Расход на м² (л)</label>
                <input type="number" class="form-input" name="coverage" min="0.1" step="0.01" oninput="updateMaterialData(this)">
            </div>
            <div class="form-group">
                <label>Количество слоев</label>
                <input type="number" class="form-input" name="layers" min="1" value="1" oninput="updateMaterialData(this)">
            </div>
        `,
        laminate: `
            <div class="form-group">
                <label>Длина доски (м)</label>
                <input type="number" class="form-input" name="length" min="0.1" step="0.01" oninput="updateMaterialData(this)">
            </div>
            <div class="form-group">
                <label>Ширина доски (м)</label>
                <input type="number" class="form-input" name="width" min="0.1" step="0.01" oninput="updateMaterialData(this)">
            </div>
            <div class="form-group">
                <label>Штук в упаковке</label>
                <input type="number" class="form-input" name="pieces_per_pack" min="1" step="1" oninput="updateMaterialData(this)">
            </div>
        `,
        tile: `
            <div class="form-group">
                <label>Длина плитки (м)</label>
                <input type="number" class="form-input" name="length" min="0.1" step="0.01" oninput="updateMaterialData(this)">
            </div>
            <div class="form-group">
                <label>Ширина плитки (м)</label>
                <input type="number" class="form-input" name="width" min="0.1" step="0.01" oninput="updateMaterialData(this)">
            </div>
            <div class="form-group">
                <label>Штук в упаковке</label>
                <input type="number" class="form-input" name="pieces_per_pack" min="1" step="1" oninput="updateMaterialData(this)">
            </div>
        `,
        drywall: `
            <div class="form-group">
                <label>Длина листа (м)</label>
                <input type="number" class="form-input" name="length" min="0.1" step="0.01" oninput="updateMaterialData(this)">
            </div>
            <div class="form-group">
                <label>Ширина листа (м)</label>
                <input type="number" class="form-input" name="width" min="0.1" step="0.01" oninput="updateMaterialData(this)">
            </div>
            <div class="form-group">
                <label>Толщина (мм)</label>
                <input type="number" class="form-input" name="thickness" min="0.1" step="0.1" oninput="updateMaterialData(this)">
            </div>
        `,
        brick: `
            <div class="form-group">
                <label>Длина кирпича (мм)</label>
                <input type="number" class="form-input" name="length" min="0.1" step="0.1" oninput="updateMaterialData(this)">
            </div>
            <div class="form-group">
                <label>Ширина кирпича (мм)</label>
                <input type="number" class="form-input" name="width" min="0.1" step="0.1" oninput="updateMaterialData(this)">
            </div>
            <div class="form-group">
                <label>Высота кирпича (мм)</label>
                <input type="number" class="form-input" name="height" min="0.1" step="0.1" oninput="updateMaterialData(this)">
            </div>
            <div class="form-group">
                <label>Толщина шва (мм)</label>
                <input type="number" class="form-input" name="mortar_thickness" min="5" step="1" value="10" oninput="updateMaterialData(this)">
            </div>
        `,
        floor_screed: `
            <div class="form-group">
                <label>Толщина стяжки (мм)</label>
                <input type="number" class="form-input" name="thickness" min="20" step="1" oninput="updateMaterialData(this)">
            </div>
        `,
        thermo_panel: `
            <div class="form-group">
                <label>Длина панели (м)</label>
                <input type="number" class="form-input" name="length" min="0.1" step="0.01" oninput="updateMaterialData(this)">
            </div>
            <div class="form-group">
                <label>Ширина панели (м)</label>
                <input type="number" class="form-input" name="width" min="0.1" step="0.01" oninput="updateMaterialData(this)">
            </div>
            <div class="form-group">
                <label>Толщина (мм)</label>
                <input type="number" class="form-input" name="thickness" min="1" step="1" oninput="updateMaterialData(this)">
            </div>
        `,
        stretch_ceiling: `
            <div class="form-group">
                <label>Тип материала</label>
                <select class="form-input" name="material_type" oninput="updateMaterialData(this)">
                    <option value="pvc">ПВХ</option>
                    <option value="textile">Тканевый</option>
                </select>
            </div>
        `,
        armstrong: `
            <div class="form-group">
                <label>Размер плиты (мм)</label>
                <input type="number" class="form-input" name="panel_size" min="300" step="1" value="600" oninput="updateMaterialData(this)">
            </div>
        `,
        grillato: `
            <div class="form-group">
                <label>Размер ячейки (мм)</label>
                <input type="number" class="form-input" name="cell_size" min="30" step="1" oninput="updateMaterialData(this)">
            </div>
            <div class="form-group">
                <label>Высота решетки (мм)</label>
                <input type="number" class="form-input" name="height" min="30" step="1" oninput="updateMaterialData(this)">
            </div>
        `
    };
    
    return commonFields + specificFields[type];
}


// Обновите также функцию updateMaterialData
function updateMaterialData(input) {
    const card = input.closest('.material-card');
    const materialId = card.dataset.id;
    const material = materials.get(materialId) || { 
        type: card.dataset.type, 
        id: materialId,
        name: MATERIAL_TYPES[card.dataset.type]
    };
    
    // Обрабатываем значение в зависимости от типа поля
    let value;
    if (input.type === 'number') {
        value = input.value !== '' ? parseFloat(input.value) : null;
    } else if (input.type === 'select-one') {
        value = input.value;
    } else {
        value = input.value;
    }
    
    // Если значение числовое и отрицательное или 0, делаем его null
    if (typeof value === 'number' && value <= 0) {
        value = null;
    }
    
    material[input.name] = value;
    materials.set(materialId, material);
    
    // Подсветка поля ошибки
    if (value === null || (typeof value === 'number' && (isNaN(value) || value <= 0))) {
        input.classList.add('input-error');
    } else {
        input.classList.remove('input-error');
    }
}


// Удаление материала
function removeMaterial(materialId) {
    const card = document.querySelector(`.material-card[data-id="${materialId}"]`);
    if (card && confirm('Удалить материал?')) {
        materials.delete(materialId);
        card.remove();
    }
}

// Расчет количества материалов
function validateAndPrepareMaterial(material) {
    const requiredFields = {
        wallpaper: {
            fields: ['price', 'width', 'length'],
            defaults: { pattern_repeat: 0 }
        },
        paint: {
            fields: ['price', 'coverage', 'layers'],
            defaults: { layers: 1 }
        },
        laminate: {
            fields: ['price', 'length', 'width', 'pieces_per_pack'],
            defaults: {}
        },
        tile: {
            fields: ['price', 'length', 'width', 'pieces_per_pack'],
            defaults: {}
        },
        drywall: {
            fields: ['price', 'length', 'width', 'thickness'],
            defaults: {}
        },
        brick: {
            fields: ['price', 'length', 'width', 'height'],
            defaults: { mortar_thickness: 10 }
        },
        floor_screed: {
            fields: ['price', 'thickness'],
            defaults: {}
        },
        thermo_panel: {
            fields: ['price', 'length', 'width', 'thickness'],
            defaults: {}
        },
        stretch_ceiling: {
            fields: ['price', 'material_type'],
            defaults: {}
        },
        armstrong: {
            fields: ['price', 'panel_size'],
            defaults: {}
        },
        grillato: {
            fields: ['price', 'cell_size', 'height'],
            defaults: {}
        }
    };

    const config = requiredFields[material.type];
    if (!config) return null;

    // Проверяем обязательные поля
    const isValid = config.fields.every(field => {
        const value = material[field];
        return value !== undefined && 
               value !== null && 
               value !== '' && 
               !(typeof value === 'number' && (isNaN(value) || value <= 0));
    });

    if (!isValid) return null;

    // Подготавливаем материал для отправки - исключаем служебные поля
    const preparedMaterial = {
        type: material.type
    };

    // Копируем только нужные поля
    config.fields.forEach(field => {
        preparedMaterial[field] = material[field];
    });

    // Добавляем значения по умолчанию
    Object.entries(config.defaults).forEach(([key, value]) => {
        if (preparedMaterial[key] === undefined) {
            preparedMaterial[key] = value;
        }
    });

    return preparedMaterial;
}

// Обновленная функция расчета материалов
function calculateMaterials() {
    if (!validateForm()) return;
    
    const roomData = getRoomData();
    const validMaterials = [];
    
    materials.forEach((material, id) => {
        const validatedMaterial = validateAndPrepareMaterial(material);
        if (validatedMaterial) {
            validMaterials.push(validatedMaterial);
        }
    });

    if (validMaterials.length === 0) {
        alert('Нет корректно заполненных материалов для расчета');
        return;
    }

    const requestData = {
        room: roomData,
        materials: validMaterials,
        openings: openings
    };

    // Добавим отладочный вывод
    console.log('Отправляемые данные:', requestData);

    // Отправляем данные на сервер
    fetch('/calculate-materials/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || 'Ошибка при расчете');
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Полученные данные:', data); // Отладочный вывод
        if (data.success && data.calculations) {
            displayResults(data.calculations);
            document.getElementById('resultsSection').style.display = 'block';
        } else {
            throw new Error('Нет данных для отображения');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Произошла ошибка при расчете: ' + error.message);
    });
}


// Получение данных комнаты
function getRoomData() {
    return {
        name: document.getElementById('roomName').value,
        width: parseFloat(document.getElementById('roomWidth').value),
        length: parseFloat(document.getElementById('roomLength').value),
        height: parseFloat(document.getElementById('roomHeight').value),
        openings: openings
    };
}

// Валидация размеров комнаты
function validateRoomDimensions() {
    const width = parseFloat(document.getElementById('roomWidth').value);
    const length = parseFloat(document.getElementById('roomLength').value);
    const height = parseFloat(document.getElementById('roomHeight').value);
    const name = document.getElementById('roomName').value.trim();

    if (!name) {
        alert('Введите название комнаты');
        return false;
    }
    
    if (isNaN(width) || isNaN(length) || isNaN(height)) {
        alert('Заполните все размеры комнаты числовыми значениями');
        return false;
    }
    
    if (width <= 0 || length <= 0 || height <= 0) {
        alert('Размеры комнаты должны быть больше нуля');
        return false;
    }
    
    return true;
}

// Валидация размеров проема
function validateOpeningDimensions(width, height) {
    const roomWidth = parseFloat(document.getElementById('roomWidth').value);
    const roomLength = parseFloat(document.getElementById('roomLength').value);
    const roomHeight = parseFloat(document.getElementById('roomHeight').value);
    
    if (isNaN(width) || width <= 0) {
        alert('Введите корректную ширину проема');
        return false;
    }
    
    if (isNaN(height) || height <= 0) {
        alert('Введите корректную высоту проема');
        return false;
    }
    
    if (width > Math.max(roomWidth, roomLength)) {
        alert('Ширина проема не может быть больше ширины комнаты');
        return false;
    }
    
    if (height > roomHeight) {
        alert('Высота проема не может быть больше высоты комнаты');
        return false;
    }
    
    // Проверка общей площади проемов
    const totalOpeningsArea = openings.reduce((sum, opening) => 
        sum + (opening.width * opening.height), 0) + (width * height);
    
    const wallArea = 2 * (roomWidth + roomLength) * roomHeight;
    if (totalOpeningsArea > wallArea * 0.9) {
        alert('Общая площадь проемов не может превышать 90% площади стен');
        return false;
    }
    
    return true;
}

// Валидация формы
function validateForm() {
    if (!validateRoomDimensions()) {
        return false;
    }
    
    if (materials.size === 0) {
        alert('Добавьте хотя бы один материал');
        return false;
    }
    
    return true;
}
// Валидация данных материала
function validateMaterial(material) {
    // Пропускаем проверку если материал не определен
    if (!material || !material.type) {
        return false;
    }

    const requiredFields = {
        wallpaper: ['price', 'width', 'length'],
        paint: ['price', 'coverage', 'layers'],
        laminate: ['price', 'length', 'width', 'pieces_per_pack'],
        tile: ['price', 'length', 'width', 'pieces_per_pack'],
        drywall: ['price', 'length', 'width', 'thickness'],
        brick: ['price', 'length', 'width', 'height', 'mortar_thickness'],
        floor_screed: ['price', 'thickness'],
        thermo_panel: ['price', 'length', 'width', 'thickness'],
        stretch_ceiling: ['price', 'material_type'],
        armstrong: ['price', 'panel_size'],
        grillato: ['price', 'cell_size', 'height']
    };
    
    const fields = requiredFields[material.type];
    if (!fields) {
        return false;
    }

    // Проверяем наличие обязательных полей
    for (const field of fields) {
        const value = material[field];
        if (value === undefined || value === null || value === '' || 
            (typeof value === 'number' && (isNaN(value) || value <= 0))) {
            return false;
        }
    }

    return true;
}

// Отображение результатов
function displayResults(calculations) {
    const container = document.getElementById('calculationResults');
    const resultsSection = document.getElementById('resultsSection');
    
    if (!calculations || calculations.length === 0) {
        container.innerHTML = '<div class="no-results">Нет результатов для отображения</div>';
        return;
    }

    const resultsHTML = calculations.map(calc => {
        const materialName = calc.name;
        const quantity = typeof calc.quantity === 'number' ? calc.quantity.toFixed(2) : calc.quantity;
        const area = typeof calc.area === 'number' ? calc.area.toFixed(2) : calc.area;
        const price = typeof calc.price === 'number' ? calc.price.toFixed(2) : calc.price;
        
        return `
            <div class="result-card">
                <div class="result-title">${materialName}</div>
                <div class="result-details">
                    <div class="result-row">
                        <span>Площадь:</span>
                        <span>${area} м²</span>
                    </div>
                    <div class="result-row">
                        <span>Количество:</span>
                        <span>${quantity} ${calc.unit || ''}</span>
                    </div>
                    <div class="result-row">
                        <span>Стоимость:</span>
                        <span>${formatPrice(price)}</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = resultsHTML;
    
    // Рассчитываем общую сумму и площадь
    const totalPrice = calculations.reduce((sum, calc) => sum + parseFloat(calc.price), 0);
    const totalArea = calculations.reduce((sum, calc) => sum + parseFloat(calc.area), 0);

    const summaryHtml = `
        <div class="summary-card">
            <h3>Общий итог</h3>
            <div class="summary-details">
                <div class="summary-row">
                    <span>Общая площадь:</span>
                    <span>${totalArea.toFixed(2)} м²</span>
                </div>
                <div class="summary-row">
                    <span>Общая стоимость:</span>
                    <span>${formatPrice(totalPrice)}</span>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('totalSummary').innerHTML = summaryHtml;
    resultsSection.style.display = 'block';
}

// Подсчет общей суммы
function calculateTotalSummary(calculations) {
    const totalCost = calculations.reduce((sum, calc) => sum + parseFloat(calc.price), 0);
    const totalArea = calculations.reduce((sum, calc) => sum + calc.area, 0);
    
    const summaryHtml = `
        <div class="summary-card">
            <h3>Общий итог</h3>
            <div class="summary-details">
                <div class="summary-row">
                    <span>Общая площадь:</span>
                    <span>${totalArea.toFixed(2)} м²</span>
                </div>
                <div class="summary-row">
                    <span>Общая стоимость:</span>
                    <span>${formatPrice(totalCost)}</span>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('totalSummary').innerHTML = summaryHtml;
}


// Функции для работы с модальными окнами
function showOpeningsDialog() {
    if (!validateRoomDimensions()) {
        alert('Сначала введите размеры помещения');
        return;
    }
    showModal('openingsModal');
}

function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
        // Фокус на первое поле ввода
        const firstInput = modal.querySelector('input:not([type="hidden"]), select');
        if (firstInput) firstInput.focus();
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        // Очищаем поля формы при закрытии
        const form = modal.querySelector('form');
        if (form) form.reset();
    }
}

function addOpening() {
    const width = parseFloat(document.getElementById('openingWidth').value);
    const height = parseFloat(document.getElementById('openingHeight').value);
    const type = document.getElementById('openingType').value;
    
    if (!validateOpeningDimensions(width, height)) {
        return;
    }
    
    // Добавляем проем в массив
    openings.push({ type, width, height });
    updateOpeningsList();
    closeModal('openingsModal');
}

// Обновление списка проемов в интерфейсе
function updateOpeningsList() {
    const list = document.getElementById('openingsList');
    list.innerHTML = openings.map((opening, index) => `
        <div class="opening-item">
            <span class="opening-type">${opening.type === 'window' ? 'Окно' : 'Дверь'}</span>
            <div class="opening-dimensions">
                ${opening.width}м × ${opening.height}м
            </div>
            <button type="button" class="delete-button" onclick="removeOpening(${index})">×</button>
        </div>
    `).join('');
}

// Удаление проема
function removeOpening(index) {
    if (confirm('Удалить проем?')) {
        openings.splice(index, 1);
        updateOpeningsList();
    }
}

function validateMaterial(material) {
    const requiredFields = {
        wallpaper: ['price', 'width', 'length'],
        paint: ['price', 'coverage', 'layers'],
        laminate: ['price', 'length', 'width', 'pieces_per_pack'],
        tile: ['price', 'length', 'width', 'pieces_per_pack'],
        drywall: ['price', 'length', 'width', 'thickness'],
        brick: ['price', 'length', 'width', 'height', 'mortar_thickness'],
        floor_screed: ['price', 'thickness'],
        thermo_panel: ['price', 'length', 'width', 'thickness'],
        stretch_ceiling: ['price', 'material_type'],
        armstrong: ['price', 'panel_size'],
        grillato: ['price', 'cell_size', 'height']
    };
    
    const fields = requiredFields[material.type];
    if (!fields) {
        console.log('Unknown material type:', material.type);
        return false;
    }

    const missingFields = fields.filter(field => {
        const value = material[field];
        if (value === undefined || value === null || value === '' || 
            (typeof value === 'number' && (isNaN(value) || value <= 0))) {
            console.log(`Invalid field ${field} for material ${material.type}:`, value);
            return true;
        }
        return false;
    });

    if (missingFields.length > 0) {
        const fieldNames = {
            price: 'цена',
            width: 'ширина',
            length: 'длина',
            coverage: 'расход',
            layers: 'количество слоев',
            pieces_per_pack: 'штук в упаковке',
            thickness: 'толщина',
            height: 'высота',
            mortar_thickness: 'толщина шва',
            material_type: 'тип материала',
            panel_size: 'размер плиты',
            cell_size: 'размер ячейки'
        };
        
        const missingFieldsTranslated = missingFields.map(field => fieldNames[field] || field);
        alert(`Заполните следующие поля для ${MATERIAL_TYPES[material.type]}: ${missingFieldsTranslated.join(', ')}`);
        return false;
    }

    return true;
}
// Закрытие модальных окон при клике вне их области
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        closeModal(event.target.id);
    }
    
    // Закрытие выпадающего списка материалов при клике вне его
    if (!event.target.closest('.material-add-wrapper')) {
        const materialsList = document.querySelector('.materials-dropdown');
        if (materialsList) {
            materialsList.remove();
        }
    }
};

function formatPrice(price) {
    return new Intl.NumberFormat('ru-KZ', {
        style: 'currency',
        currency: 'KZT',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(price);
}

// Получение CSRF токена
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Функция для переключения видимости формул
function toggleFormulas() {
    const content = document.getElementById('formulasContent');
    const button = document.querySelector('.info-toggle');
    content.classList.toggle('active');
    button.classList.toggle('active');
}


// Функция для отображения модального окна с формулами
function showFormulasModal() {
    showModal('formulasModal');
}

function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
        // Если это модальное окно с формулами, перезапускаем MathJax
        if (modalId === 'formulasModal') {
            if (window.MathJax) {
                MathJax.Hub.Queue(["Typeset", MathJax.Hub]);
            }
        }
    }
}


// Функция для экспорта в PDF
async function exportToPDF() {
    const data = {
        room: getRoomData(),
        calculations: getCurrentCalculations(),
        summary: getCurrentSummary()
    };

    try {
        const response = await fetch('/export-to-pdf/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) throw new Error('Ошибка при создании PDF');

        // Создаем blob из ответа и скачиваем файл
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Расчет_${data.room.name}_${new Date().toLocaleDateString()}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при создании PDF');
    }
}

// Функция для экспорта в Excel
async function exportToExcel() {
    const data = {
        room: getRoomData(),
        calculations: getCurrentCalculations(),
        summary: getCurrentSummary()
    };

    try {
        const response = await fetch('/export-to-excel/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) throw new Error('Ошибка при создании Excel файла');

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Расчет_${data.room.name}_${new Date().toLocaleDateString()}.xlsx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при создании Excel файла');
    }
}

// Вспомогательные функции
function getCurrentCalculations() {
    // Получаем текущие результаты расчетов
    const resultCards = document.querySelectorAll('.result-card');
    return Array.from(resultCards).map(card => ({
        materialName: card.querySelector('.result-title').textContent,
        area: parseFloat(card.querySelector('.result-row:nth-child(1) span:last-child').textContent),
        quantity: card.querySelector('.result-row:nth-child(2) span:last-child').textContent,
        price: card.querySelector('.result-row:nth-child(3) span:last-child').textContent
    }));
}

function getCurrentSummary() {
    // Получаем итоговые данные
    const summaryCard = document.querySelector('.summary-card');
    return {
        totalArea: parseFloat(summaryCard.querySelector('.summary-row:first-child span:last-child').textContent),
        totalPrice: summaryCard.querySelector('.summary-row:last-child span:last-child').textContent
    };
}


let isTemplateSaved = false;

function toggleTemplate() {
    const starButton = document.getElementById('saveTemplate');
    const starPath = starButton.querySelector('path');
    
    if (!validateForm()) {
        alert('Пожалуйста, заполните все необходимые поля перед сохранением шаблона');
        return;
    }

    if (!isTemplateSaved) {
        saveTemplate();
    } else {
        const urlParams = new URLSearchParams(window.location.search);
        const templateId = urlParams.get('template');
        
        if (!templateId) {
            alert('Невозможно удалить шаблон');
            return;
        }
        
        fetch(`/delete-current-template/?template_id=${templateId}`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                isTemplateSaved = false;
                updateStarButton(false);
                alert('Шаблон удален');
            } else {
                throw new Error(data.error || 'Ошибка при удалении шаблона');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ошибка при удалении шаблона');
        });
    }
}

function saveTemplate() {
    const templateData = {
        room: getRoomData(),
        materials: Array.from(materials.values()),
        openings: openings
    };

    fetch('/save-template/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(templateData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            isTemplateSaved = true;
            updateStarButton(true);
            // Сохраняем ID шаблона в URL
            const url = new URL(window.location);
            url.searchParams.set('template', data.template_id);
            window.history.pushState({}, '', url);
            alert('Шаблон успешно сохранен');
        } else {
            throw new Error(data.error || 'Ошибка при сохранении шаблона');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ошибка при сохранении шаблона');
    });
}

function deleteTemplate() {
    fetch('/delete-current-template/', {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            isTemplateSaved = false;
            updateStarButton(false);
            alert('Шаблон удален');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ошибка при удалении шаблона');
    });
}

function updateStarButton(saved) {
    const starButton = document.getElementById('saveTemplate');
    const starPath = starButton.querySelector('path');
    
    if (saved) {
        starPath.setAttribute('fill', 'var(--accent-blue)');
    } else {
        starPath.setAttribute('fill', 'none');
        starPath.setAttribute('stroke', 'var(--accent-blue)');
    }
}

async function loadTemplateData(templateId) {
    try {
        const response = await fetch(`/get-template/${templateId}/`);
        if (!response.ok) {
            throw new Error('Ошибка при загрузке шаблона');
        }
        
        const data = await response.json();
        if (data.success) {
            // Заполняем данные комнаты
            const roomData = data.template.room;
            document.getElementById('roomName').value = roomData.name;
            document.getElementById('roomWidth').value = roomData.width;
            document.getElementById('roomLength').value = roomData.length;
            document.getElementById('roomHeight').value = roomData.height;
            
            // Очищаем существующие проемы
            openings = [];
            
            // Заполняем проемы
            data.template.openings.forEach(opening => {
                openings.push({
                    type: opening.opening_type,
                    width: opening.width,
                    height: opening.height
                });
            });
            updateOpeningsList();
            
            // Полностью очищаем существующие материалы и их отображение
            materials = new Map(); // Пересоздаем Map
            const materialsContainer = document.getElementById('materialsList');
            materialsContainer.innerHTML = ''; // Очищаем контейнер
            
            // Добавляем только материалы из шаблона
            if (data.template.materials && Array.isArray(data.template.materials)) {
                data.template.materials.forEach(materialEntry => {
                    // Проверяем наличие всех необходимых данных
                    const materialData = materialEntry.data;
                    if (materialData && Object.keys(materialData).length > 0) {
                        // Добавляем только если есть данные
                        addMaterialCard(materialEntry.material_type, materialData);
                    }
                });
            }
            
            // Обновляем состояние кнопки шаблона
            isTemplateSaved = true;
            updateStarButton(true);
            
        } else {
            throw new Error(data.error || 'Ошибка при загрузке данных шаблона');
        }
    } catch (error) {
        console.error('Error loading template:', error);
        alert('Не удалось загрузить шаблон. Пожалуйста, попробуйте еще раз.');
    }
}


// В calculator.js добавим функцию:
function preventInvalidInput(event) {
    // Разрешаем: цифры, точку, backspace, delete, стрелки для навигации
    const allowed = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.', 'Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab'];
    
    if (!allowed.includes(event.key)) {
        event.preventDefault();
    }
    
    // Предотвращаем ввод второй точки
    if (event.key === '.' && event.target.value.includes('.')) {
        event.preventDefault();
    }
}
