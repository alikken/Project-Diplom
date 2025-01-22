document.addEventListener('DOMContentLoaded', function() {
    // Управление вкладками
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Удаляем активный класс у всех кнопок и контента
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Добавляем активный класс нажатой кнопке
            button.classList.add('active');

            // Показываем соответствующий контент
            const tabId = button.dataset.tab;
            document.getElementById(`${tabId}-content`).classList.add('active');
        });
    });
});

async function useTemplate(templateId) {
    try {
        window.location.href = `/calculator/?template=${templateId}`;
    } catch (error) {
        console.error('Error:', error);
        alert('Ошибка при переходе к шаблону');
    }
}


// Функция для удаления шаблона
async function deleteTemplate(templateId) {
    if (!confirm('Вы уверены, что хотите удалить этот шаблон?')) {
        return;
    }

    try {
        const csrftoken = getCookie('csrftoken');
        const response = await fetch(`/delete-template/${templateId}/`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            }
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();
        if (data.success) {
            // Удаляем карточку шаблона из DOM
            const templateCard = document.querySelector(`[data-template-id="${templateId}"]`);
            if (templateCard) {
                templateCard.remove();
            }
            
            // Если шаблонов больше нет, показываем сообщение
            const templatesGrid = document.querySelector('.templates-grid');
            if (templatesGrid.children.length === 0) {
                templatesGrid.innerHTML = `
                    <div class="no-templates">
                        <p>У вас пока нет сохраненных шаблонов</p>
                    </div>
                `;
            }
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Ошибка при удалении шаблона');
    }
}

// Функция получения CSRF-токена
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

function toggleEdit(fieldId) {
    const input = document.getElementById(fieldId);
    const button = input.nextElementSibling.querySelector('.material-icons');
    
    if (input.readOnly) {
        input.readOnly = false;
        input.focus();
        button.textContent = 'close';
        input.dataset.originalValue = input.value;
    } else {
        input.readOnly = true;
        button.textContent = 'edit';
        input.value = input.dataset.originalValue;
    }
}

// Функция для переключения видимости пароля
function togglePasswordVisibility(fieldId) {
    const input = document.getElementById(fieldId);
    const icon = input.nextElementSibling.querySelector('.material-icons');
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.textContent = 'visibility_off';
    } else {
        input.type = 'password';
        icon.textContent = 'visibility';
    }
}

// Обработка формы профиля
document.getElementById('profileForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    
    try {
        const response = await fetch('/update-profile/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: formData.get('username'),
                email: formData.get('email')
            })
        });

        const data = await response.json();
        
        if (data.success) {
            showMessage('success', 'Профиль успешно обновлен');
        } else {
            showMessage('error', data.error);
        }
    } catch (error) {
        showMessage('error', 'Произошла ошибка при обновлении профиля');
    }
});

// Обработка формы смены пароля
document.getElementById('passwordForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    
    try {
        const response = await fetch('/change-password/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                current_password: formData.get('current_password'),
                new_password: formData.get('new_password'),
                confirm_password: formData.get('confirm_password')
            })
        });

        const data = await response.json();
        
        if (data.success) {
            showMessage('success', 'Пароль успешно изменен');
            e.target.reset();
        } else {
            showMessage('error', data.error);
        }
    } catch (error) {
        showMessage('error', 'Произошла ошибка при смене пароля');
    }
});

// Функция для отображения сообщений
function showMessage(type, text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `${type}-message`;
    messageDiv.textContent = text;
    
    // Удаляем предыдущие сообщения
    document.querySelectorAll('.error-message, .success-message')
        .forEach(el => el.remove());
    
    // Добавляем новое сообщение
    document.querySelector('.profile-info').insertBefore(
        messageDiv,
        document.querySelector('.profile-section')
    );
    
    // Удаляем сообщение через 5 секунд
    setTimeout(() => messageDiv.remove(), 5000);
}