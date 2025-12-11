/**
 * MCP工厂 - 主JavaScript文件
 */

// 全局API基础URL
const API_BASE = '';

/**
 * 发送API请求
 */
async function apiRequest(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        return await response.json();
    } catch (error) {
        console.error('API请求失败:', error);
        return { success: false, error: error.message };
    }
}

/**
 * 显示通知
 */
function showNotification(message, type = 'info', duration = 3000) {
    // 移除已存在的通知
    const existing = document.querySelector('.notification');
    if (existing) existing.remove();
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <span class="notification-icon">${getNotificationIcon(type)}</span>
        <span class="notification-message">${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    // 添加样式（如果不存在）
    if (!document.getElementById('notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            .notification {
                position: fixed;
                top: 24px;
                right: 24px;
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 16px 24px;
                background: var(--bg-tertiary, #1a2234);
                border: 1px solid var(--border-color, rgba(75, 85, 99, 0.3));
                border-radius: 12px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
                z-index: 10000;
                transform: translateX(120%);
                transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }
            .notification.show { transform: translateX(0); }
            .notification-info { border-left: 4px solid var(--accent-primary, #00f5d4); }
            .notification-success { border-left: 4px solid #10b981; }
            .notification-error { border-left: 4px solid #ef4444; }
            .notification-warning { border-left: 4px solid #f59e0b; }
            .notification-icon { font-size: 1.25rem; }
            .notification-message { color: var(--text-primary, #f0f4f8); }
        `;
        document.head.appendChild(style);
    }
    
    // 显示动画
    requestAnimationFrame(() => {
        notification.classList.add('show');
    });
    
    // 自动隐藏
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

function getNotificationIcon(type) {
    const icons = {
        'info': 'ℹ️',
        'success': '✅',
        'error': '❌',
        'warning': '⚠️'
    };
    return icons[type] || icons.info;
}

/**
 * 显示加载状态
 */
function showLoading(container, message = '加载中...') {
    if (typeof container === 'string') {
        container = document.getElementById(container);
    }
    if (!container) return;
    
    container.innerHTML = `
        <div class="loading-state">
            <div class="spinner"></div>
            <p>${message}</p>
        </div>
    `;
}

/**
 * 显示空状态
 */
function showEmpty(container, message = '暂无数据', icon = '📭') {
    if (typeof container === 'string') {
        container = document.getElementById(container);
    }
    if (!container) return;
    
    container.innerHTML = `
        <div class="empty-state">
            <div class="empty-icon">${icon}</div>
            <p>${message}</p>
        </div>
    `;
}

/**
 * 显示错误状态
 */
function showError(container, message = '发生错误') {
    if (typeof container === 'string') {
        container = document.getElementById(container);
    }
    if (!container) return;
    
    container.innerHTML = `
        <div class="error-state">
            <div class="error-icon">❌</div>
            <p>${message}</p>
        </div>
    `;
}

/**
 * 格式化日期
 */
function formatDate(dateString) {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    // 小于1分钟
    if (diff < 60000) return '刚刚';
    // 小于1小时
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
    // 小于24小时
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
    // 小于7天
    if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`;
    
    // 其他情况显示完整日期
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
}

/**
 * 复制到剪贴板
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showNotification('已复制到剪贴板', 'success');
        return true;
    } catch (err) {
        // 降级方案
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showNotification('已复制到剪贴板', 'success');
        return true;
    }
}

/**
 * 防抖函数
 */
function debounce(func, wait = 300) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * 节流函数
 */
function throttle(func, limit = 300) {
    let inThrottle;
    return function executedFunction(...args) {
        if (!inThrottle) {
            func(...args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * 检查系统状态
 */
async function checkSystemStatus() {
    try {
        const response = await apiRequest('/api/status');
        return response.status === 'running';
    } catch {
        return false;
    }
}

/**
 * 加载GitHub组织仓库
 */
async function loadGitHubRepos(org = 'BACH-AI-Tools') {
    try {
        const response = await apiRequest(`/api/projects/github-org?org=${org}`);
        if (response.success) {
            return response.data;
        }
        return [];
    } catch {
        return [];
    }
}

/**
 * 初始化页面
 */
document.addEventListener('DOMContentLoaded', function() {
    // 检查系统状态
    checkSystemStatus().then(running => {
        const statusDot = document.querySelector('.status-dot');
        if (statusDot) {
            if (running) {
                statusDot.classList.add('running');
            } else {
                statusDot.classList.remove('running');
            }
        }
    });
    
    // 添加导航活动状态
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
});

// 导出到全局
window.MCPFactory = {
    apiRequest,
    showNotification,
    showLoading,
    showEmpty,
    showError,
    formatDate,
    copyToClipboard,
    debounce,
    throttle,
    checkSystemStatus,
    loadGitHubRepos
};




