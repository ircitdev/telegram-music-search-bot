#!/usr/bin/env python3
"""Script to update dashboard index.html with enhanced settings page."""
import re

DASHBOARD_PATH = '/root/uspmusic-bot/dashboard/index.html'

# New JavaScript for config page
NEW_JS = '''
        // Config Page - Enhanced with categories
        const CONFIG_CATEGORIES = {
            bot: ['BOT_TOKEN', 'BOT_USERNAME', 'ADMIN_IDS'],
            paths: ['TEMP_DIR', 'CACHE_DIR', 'LOGS_DIR', 'DATABASE_PATH'],
            limits: ['MAX_FILE_SIZE', 'MAX_DURATION', 'LOG_LEVEL', 'RATE_LIMIT_REQUESTS', 'RATE_LIMIT_PERIOD', 'FREE_DAILY_LIMIT'],
            features: ['ENABLE_CACHE', 'ENABLE_STATS', 'ENABLE_INLINE'],
            apis: ['AUDD_API_KEY', 'LASTFM_API_KEY', 'API_KEYS'],
            payments: ['CRYPTOBOT_TOKEN', 'YOOMONEY_WALLET', 'YOOMONEY_SECRET', 'YOOMONEY_NOTIFICATION_URL', 'YOOKASSA_SHOP_ID', 'YOOKASSA_SECRET_KEY'],
            channel: ['CHANNEL_ID', 'CHANNEL_POST_HOUR'],
            other: ['SENTRY_DSN']
        };

        const CONFIG_LABELS = {
            'BOT_TOKEN': 'Токен бота',
            'BOT_USERNAME': 'Username бота',
            'ADMIN_IDS': 'ID админов (через запятую)',
            'TEMP_DIR': 'Временная директория',
            'CACHE_DIR': 'Директория кэша',
            'LOGS_DIR': 'Директория логов',
            'DATABASE_PATH': 'Путь к базе данных',
            'MAX_FILE_SIZE': 'Макс. размер файла (байт)',
            'MAX_DURATION': 'Макс. длительность (сек)',
            'LOG_LEVEL': 'Уровень логирования',
            'RATE_LIMIT_REQUESTS': 'Лимит запросов',
            'RATE_LIMIT_PERIOD': 'Период лимита (сек)',
            'FREE_DAILY_LIMIT': 'Дневной лимит (free)',
            'ENABLE_CACHE': 'Включить кэш',
            'ENABLE_STATS': 'Включить статистику',
            'ENABLE_INLINE': 'Включить inline',
            'AUDD_API_KEY': 'AudD API Key',
            'LASTFM_API_KEY': 'LastFM API Key',
            'API_KEYS': 'Внешние API ключи',
            'CRYPTOBOT_TOKEN': 'CryptoBot Token',
            'YOOMONEY_WALLET': 'YooMoney кошелёк',
            'YOOMONEY_SECRET': 'YooMoney секретный ключ',
            'YOOMONEY_NOTIFICATION_URL': 'YooMoney Webhook URL',
            'YOOKASSA_SHOP_ID': 'YooKassa Shop ID',
            'YOOKASSA_SECRET_KEY': 'YooKassa Secret Key',
            'CHANNEL_ID': 'ID канала',
            'CHANNEL_POST_HOUR': 'Час автопостинга (0-23)',
            'SENTRY_DSN': 'Sentry DSN'
        };

        const CONFIG_TYPES = {
            'MAX_FILE_SIZE': 'number',
            'MAX_DURATION': 'number',
            'RATE_LIMIT_REQUESTS': 'number',
            'RATE_LIMIT_PERIOD': 'number',
            'FREE_DAILY_LIMIT': 'number',
            'CHANNEL_POST_HOUR': 'number',
            'ENABLE_CACHE': 'boolean',
            'ENABLE_STATS': 'boolean',
            'ENABLE_INLINE': 'boolean',
            'BOT_TOKEN': 'password',
            'CRYPTOBOT_TOKEN': 'password',
            'YOOMONEY_SECRET': 'password',
            'YOOKASSA_SECRET_KEY': 'password',
            'AUDD_API_KEY': 'password',
            'LASTFM_API_KEY': 'password',
            'SENTRY_DSN': 'password'
        };

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text || '';
            return div.innerHTML;
        }

        function renderConfigItem(key, value) {
            const label = CONFIG_LABELS[key] || key;
            const type = CONFIG_TYPES[key] || 'text';
            const inputId = 'config_' + key;
            const escapedValue = escapeHtml(value);

            let inputHtml = '';
            if (type === 'boolean') {
                const isChecked = value === 'true' || value === true || value === '1';
                inputHtml = `<label class="toggle-switch">
                    <input type="checkbox" id="${inputId}" ${isChecked ? 'checked' : ''} onchange="updateConfigBool('${key}', this.checked)">
                    <span class="toggle-slider"></span>
                    <span class="toggle-label">${isChecked ? 'Включено' : 'Выключено'}</span>
                </label>`;
            } else if (type === 'password') {
                inputHtml = `<div class="password-field">
                    <input type="password" id="${inputId}" value="${escapedValue}" data-key="${key}">
                    <button type="button" class="toggle-password" onclick="togglePassword('${inputId}')">👁</button>
                    <button type="button" class="btn-save" onclick="saveConfigField('${key}')">💾</button>
                </div>`;
            } else if (type === 'number') {
                inputHtml = `<div class="number-field">
                    <input type="number" id="${inputId}" value="${escapedValue}" data-key="${key}">
                    <button type="button" class="btn-save" onclick="saveConfigField('${key}')">💾</button>
                </div>`;
            } else {
                inputHtml = `<div class="text-field">
                    <input type="text" id="${inputId}" value="${escapedValue}" data-key="${key}">
                    <button type="button" class="btn-save" onclick="saveConfigField('${key}')">💾</button>
                </div>`;
            }

            return `<div class="config-item"><label for="${inputId}">${label}</label>${inputHtml}</div>`;
        }

        async function loadConfig() {
            try {
                const data = await fetchAPI('/config');
                const config = data.config;

                // Clear all grids
                ['Bot', 'Paths', 'Limits', 'Features', 'Apis', 'Payments', 'Channel', 'Other'].forEach(cat => {
                    const grid = document.getElementById('configGrid' + cat);
                    if (grid) grid.innerHTML = '';
                });

                // Categorize and render
                const categorized = new Set();

                Object.entries(CONFIG_CATEGORIES).forEach(([category, keys]) => {
                    const gridId = 'configGrid' + category.charAt(0).toUpperCase() + category.slice(1);
                    const grid = document.getElementById(gridId);
                    if (!grid) return;

                    const items = keys.filter(key => config.hasOwnProperty(key)).map(key => {
                        categorized.add(key);
                        return renderConfigItem(key, config[key]);
                    });

                    grid.innerHTML = items.join('');
                });

                // Uncategorized items go to Other
                const otherGrid = document.getElementById('configGridOther');
                if (otherGrid) {
                    const otherItems = Object.entries(config)
                        .filter(([key]) => !categorized.has(key))
                        .map(([key, value]) => renderConfigItem(key, value));

                    if (otherItems.length > 0) {
                        otherGrid.innerHTML += otherItems.join('');
                    }
                }
            } catch (e) {
                console.error('Config error:', e);
            }
        }

        function togglePassword(inputId) {
            const input = document.getElementById(inputId);
            input.type = input.type === 'password' ? 'text' : 'password';
        }

        async function saveConfigField(key) {
            const input = document.getElementById('config_' + key);
            if (!input) return;

            try {
                await fetchAPI('/config/update', {
                    method: 'POST',
                    body: JSON.stringify({ key, value: input.value })
                });
                showNotification('Сохранено: ' + (CONFIG_LABELS[key] || key), 'success');
            } catch (e) {
                showNotification('Ошибка: ' + e.message, 'error');
            }
        }

        async function updateConfigBool(key, checked) {
            try {
                await fetchAPI('/config/update', {
                    method: 'POST',
                    body: JSON.stringify({ key, value: checked ? 'true' : 'false' })
                });
                const label = document.querySelector('#config_' + key).parentElement.querySelector('.toggle-label');
                if (label) label.textContent = checked ? 'Включено' : 'Выключено';
                showNotification('Сохранено: ' + (CONFIG_LABELS[key] || key), 'success');
            } catch (e) {
                showNotification('Ошибка: ' + e.message, 'error');
            }
        }

        function showNotification(message, type) {
            const notification = document.createElement('div');
            notification.className = 'notification ' + type;
            notification.textContent = message;
            document.body.appendChild(notification);

            setTimeout(() => notification.classList.add('show'), 10);
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        }

        async function updateConfig(key, value) {
            try {
                await fetchAPI('/config/update', {
                    method: 'POST',
                    body: JSON.stringify({ key, value })
                });
                showNotification('Сохранено: ' + key, 'success');
            } catch (e) {
                showNotification('Ошибка: ' + e.message, 'error');
            }
        }

        async function reloadBot() {
            if (!confirm('Перезагрузить бота? Это прервёт все текущие операции.')) return;
            showNotification('Перезагрузка не реализована. Выполните: systemctl restart musicbot', 'error');
        }
'''

def main():
    # Read current file
    with open(DASHBOARD_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find and replace old loadConfig and related functions
    old_pattern = r'// Config Page\s*\n\s*async function loadConfig\(\).*?function reloadBot\(\).*?\n\s*\}'

    match = re.search(old_pattern, content, flags=re.DOTALL)
    if match:
        content = content[:match.start()] + NEW_JS + content[match.end():]
        print(f"Replaced JS functions at position {match.start()}-{match.end()}")
    else:
        print("Pattern not found, JS functions might already be updated")

    # Save
    with open(DASHBOARD_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f'Dashboard updated successfully. New size: {len(content)} bytes')

if __name__ == '__main__':
    main()
