let allTickets = [];

const filters = {
    search: '',
    category: '',
    status: '',
    priority: '',
    sentiment: ''
};

const plotlyLayout = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: {
        family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        color: '#475569',
        size: 12
    },
    margin: { t: 25, r: 20, l: 35, b: 35 },
    xaxis: { gridcolor: '#f1f5f9', zerolinecolor: '#e2e8f0' },
    yaxis: { gridcolor: '#f1f5f9', zerolinecolor: '#e2e8f0' }
};

const escapeHtml = (str) => {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
};

const updateKPIs = (data) => {
    const total = data.total || 0;
    const newCount = data.status?.new || 0;
    const highCount = data.priority?.high || 0;
    const negCount = data.sentiment?.negative || 0;
    const negPercent = total > 0 ? Math.round((negCount / total) * 100) : 0;

    document.getElementById('kpi-total').textContent = total;
    document.getElementById('kpi-new').textContent = newCount;
    document.getElementById('kpi-high').textContent = highCount;
    document.getElementById('kpi-sentiment').textContent = negPercent + '%';
    document.getElementById('kpi-backlog').textContent = data.backlog ?? 0;
    document.getElementById('kpi-csat').textContent = data.csat_avg ? `${data.csat_avg} / 5` : 'N/A';
    document.getElementById('kpi-mttr').textContent = `${data.mttr ?? 0} мин`;
    document.getElementById('kpi-sla').textContent = `${data.sla_compliance ?? 100}%`;
};

const renderHypotheses = (hypotheses) => {
    const container = document.getElementById('hypotheses-list');
    if (!hypotheses || hypotheses.length === 0) {
        container.innerHTML = '<div class="empty-hint">Система работает стабильно. Аномалий не обнаружено.</div>';
        return;
    }

    container.innerHTML = hypotheses.map(h => `
        <div class="hypothesis-item">
            <span class="hypo-dot"></span>
            <p>${escapeHtml(h)}</p>
        </div>
    `).join('');
};

const renderCharts = (charts) => {
    const config = { responsive: true, displayModeBar: false };

    if (charts.category_chart) {
        const catData = JSON.parse(charts.category_chart);
        Plotly.react('chart-category', catData.data, { ...catData.layout, ...plotlyLayout, margin: { t: 10, r: 10, l: 10, b: 10 } }, config);
    }

    if (charts.sentiment_chart) {
        const sentData = JSON.parse(charts.sentiment_chart);
        Plotly.react('chart-sentiment', sentData.data, { ...sentData.layout, ...plotlyLayout }, config);
    }

    if (charts.timeline_chart) {
        const timeData = JSON.parse(charts.timeline_chart);
        Plotly.react('chart-timeline', timeData.data, { ...timeData.layout, ...plotlyLayout }, config);
    }

    if (charts.tags_chart) {
        const tagsData = JSON.parse(charts.tags_chart);
        Plotly.react('chart-tags', tagsData.data, { ...tagsData.layout, ...plotlyLayout }, config);
    }
};

const loadAnalytics = async () => {
    const params = new URLSearchParams();
    if (filters.category) params.append('category', filters.category);
    if (filters.status) params.append('status', filters.status);
    if (filters.priority) params.append('priority', filters.priority);
    if (filters.sentiment) params.append('sentiment', filters.sentiment);

    try {
        const res = await fetch(`/analytics/summary?${params.toString()}`);
        if (!res.ok) return;
        const data = await res.json();

        updateKPIs(data);
        renderHypotheses(data.hypotheses || []);
        renderCharts(data.charts || {});
    } catch (err) {
        console.error(err);
    }
};

const dictCategory = {
    'bug': 'Баг',
    'ui_ux': 'Интерфейс',
    'complaint': 'Жалоба',
    'feature_request': 'Идея / Фича',
    'question': 'Вопрос',
    'other': 'Другое'
};

const dictPriority = {
    'high': 'Высокий',
    'mid': 'Средний',
    'low': 'Низкий'
};

const dictSentiment = {
    'positive': 'Позитивный',
    'neutral': 'Нейтральный',
    'negative': 'Негативный'
};

const dictStatus = {
    'new': 'Новый',
    'in progress': 'В работе',
    'closed': 'Закрыт'
};

const showToast = (message, type = 'info') => {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(8px)';
        toast.style.transition = 'all 0.2s ease';
        setTimeout(() => toast.remove(), 200);
    }, 2800);
};

const debounce = (fn, ms) => {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), ms);
    };
};

const renderTicketsTable = () => {
    const tbody = document.getElementById('tickets-tbody');
    const tableCount = document.getElementById('table-count');

    const filtered = allTickets.filter(t => {
        if (filters.category && t.category !== filters.category) return false;
        if (filters.status && t.status !== filters.status) return false;
        if (filters.priority && t.priority !== filters.priority) return false;
        if (filters.sentiment && t.sentiment !== filters.sentiment) return false;
        if (filters.search) {
            const q = filters.search.toLowerCase();
            const match = (t.title && t.title.toLowerCase().includes(q)) ||
                          (t.description && t.description.toLowerCase().includes(q)) ||
                          (t.user_login && t.user_login.toLowerCase().includes(q)) ||
                          (t.tags && t.tags.toLowerCase().includes(q));
            if (!match) return false;
        }
        return true;
    });

    tableCount.textContent = `Записей: ${filtered.length}`;

    if (filtered.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="empty-td" style="text-align:center; padding: 28px; color: var(--text-muted);">Обращения по выбранным критериям не найдены</td></tr>';
        return;
    }

    tbody.innerHTML = filtered.map(t => {
        const dateStr = t.created_at ? new Date(t.created_at).toLocaleDateString('ru-RU', {
            day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
        }) : '-';

        const statusClass = (t.status || '').replace(' ', '-');
        const catLabel = dictCategory[t.category] || t.category || '-';
        const priorityLabel = dictPriority[t.priority] || t.priority || '-';
        const sentimentLabel = dictSentiment[t.sentiment] || t.sentiment || '-';
        const statusLabel = dictStatus[t.status] || t.status || '-';

        return `
            <tr>
                <td>#${t.id}</td>
                <td><strong>@${escapeHtml(t.user_login)}</strong></td>
                <td>
                    <div class="ticket-title">${escapeHtml(t.title)}</div>
                    <div class="ticket-desc">${escapeHtml(t.description || '')}</div>
                </td>
                <td><span class="badge badge-cat">${escapeHtml(catLabel)}</span></td>
                <td>${t.tags ? `<span class="badge badge-tag">${escapeHtml(t.tags)}</span>` : '-'}</td>
                <td><span class="badge badge-${t.priority}">${escapeHtml(priorityLabel)}</span></td>
                <td><span class="badge badge-${t.sentiment}">${escapeHtml(sentimentLabel)}</span></td>
                <td><span class="badge badge-${statusClass}">${escapeHtml(statusLabel)}</span></td>
                <td class="date-cell">${dateStr}</td>
                <td>
                    <div class="action-btns">
                        ${t.status !== 'closed' ? `
                            <button class="btn-action close" aria-label="Закрыть тикет #${t.id}" title="Закрыть тикет" onclick="updateTicketStatus(${t.id}, 'closed')">&#10003;</button>
                        ` : ''}
                        ${t.status === 'new' ? `
                            <button class="btn-action progress" aria-label="Взять в работу тикет #${t.id}" title="Взять в работу" onclick="updateTicketStatus(${t.id}, 'in progress')">&rarr;</button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `;
    }).join('');
};

const loadTickets = async () => {
    try {
        const res = await fetch('/tickets/');
        if (!res.ok) return;
        allTickets = await res.json();
        renderTicketsTable();
    } catch (err) {
        console.error(err);
    }
};

const loadDashboard = async () => {
    await loadAnalytics();
    await loadTickets();
};

window.updateTicketStatus = async (id, newStatus) => {
    try {
        const res = await fetch(`/tickets/${id}?status=${newStatus}`, { method: 'PATCH' });
        if (res.ok) {
            const statusLabel = dictStatus[newStatus] || newStatus;
            showToast(`Тикет #${id}: статус изменен на «${statusLabel}»`, 'success');
            await loadDashboard();
        } else {
            showToast(`Ошибка обновления тикета #${id}`, 'info');
        }
    } catch (err) {
        console.error(err);
        showToast('Ошибка сети при обновлении статуса', 'info');
    }
};

const initFilters = () => {
    const searchInput = document.getElementById('filter-search');
    const catSelect = document.getElementById('filter-category');
    const statusSelect = document.getElementById('filter-status');
    const prioritySelect = document.getElementById('filter-priority');
    const sentSelect = document.getElementById('filter-sentiment');
    const resetBtn = document.getElementById('reset-filters-btn');

    const triggerUpdate = () => {
        filters.search = searchInput.value.trim();
        filters.category = catSelect.value;
        filters.status = statusSelect.value;
        filters.priority = prioritySelect.value;
        filters.sentiment = sentSelect.value;

        renderTicketsTable();
        loadAnalytics();
    };

    const debouncedSearch = debounce(triggerUpdate, 250);

    searchInput.addEventListener('input', debouncedSearch);
    catSelect.addEventListener('change', triggerUpdate);
    statusSelect.addEventListener('change', triggerUpdate);
    prioritySelect.addEventListener('change', triggerUpdate);
    sentSelect.addEventListener('change', triggerUpdate);

    resetBtn.addEventListener('click', () => {
        searchInput.value = '';
        catSelect.value = '';
        statusSelect.value = '';
        prioritySelect.value = '';
        sentSelect.value = '';
        triggerUpdate();
        showToast('Фильтры сброшены', 'info');
    });
};

const initModal = () => {
    const modal = document.getElementById('ticket-modal');
    const openBtn = document.getElementById('open-modal-btn');
    const closeBtn = document.getElementById('close-modal-btn');
    const cancelBtn = document.getElementById('cancel-modal-btn');
    const form = document.getElementById('new-ticket-form');

    const open = () => modal.classList.add('active');
    const close = () => {
        modal.classList.remove('active');
        form.reset();
    };

    openBtn.addEventListener('click', open);
    closeBtn.addEventListener('click', close);
    cancelBtn.addEventListener('click', close);

    // Закрытие по клику на оверлей или по Escape
    modal.addEventListener('click', (e) => {
        if (e.target === modal) close();
    });
    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) close();
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) submitBtn.disabled = true;

        const payload = {
            user_login: document.getElementById('form-user-login').value.trim(),
            description: document.getElementById('form-description').value.trim(),
            details: document.getElementById('form-details').value.trim() || null,
            status: 'new'
        };

        try {
            const res = await fetch('/new_ticket', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                close();
                showToast('Обращение успешно создано!', 'success');
                await loadDashboard();
            } else {
                showToast('Ошибка при создании обращения', 'info');
            }
        } catch (err) {
            console.error(err);
            showToast('Сетевая ошибка при отправке', 'info');
        } finally {
            if (submitBtn) submitBtn.disabled = false;
        }
    });
};

const initExport = () => {
    const exportBtn = document.getElementById('export-csv-btn');
    exportBtn.addEventListener('click', () => {
        if (!allTickets.length) {
            showToast('Нет данных для экспорта', 'info');
            return;
        }

        const headers = ['ID', 'User', 'Title', 'Category', 'Priority', 'Sentiment', 'Status', 'Date', 'Tags'];
        const rows = allTickets.map(t => [
            t.id,
            `"${t.user_login || ''}"`,
            `"${(t.title || '').replace(/"/g, '""')}"`,
            t.category,
            t.priority,
            t.sentiment,
            t.status,
            t.created_at || '',
            `"${t.tags || ''}"`
        ]);

        const csv = '\uFEFF' + [headers.join(';'), ...rows.map(r => r.join(';'))].join('\n');
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'tickets.csv';
        link.click();
        showToast('CSV-отчет успешно выгружен', 'success');
    });
};

document.addEventListener('DOMContentLoaded', () => {
    initFilters();
    initModal();
    initExport();
    loadDashboard();
});
