// Dashboard Chart Handler and Data Management
class DashboardManager {
    constructor() {
        this.data = null;
        this.charts = {};
        this.filteredData = [];
        this.init();
    }

    async init() {
        try {
            await this.loadData();
            this.hideLoading();
            this.setupEventListeners();
            this.renderSummaryCards();
            this.renderCharts();
            this.renderTable();
            this.updateLastUpdated();
        } catch (error) {
            console.error('Error initializing dashboard:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    async loadData() {
        try {
            // Try to load from local JSON file first
            const response = await fetch('data/processed/dashboard.json');
            if (response.ok) {
                this.data = await response.json();
            } else {
                // Fallback to sample data if JSON file doesn't exist
                this.data = this.generateSampleData();
            }
            this.filteredData = this.data.transactions || [];
        } catch (error) {
            console.warn('Could not load dashboard.json, using sample data');
            this.data = this.generateSampleData();
            this.filteredData = this.data.transactions || [];
        }
    }

    generateSampleData() {
        // Generate sample data for development/demo purposes
        const categories = ['payment', 'transfer', 'deposit', 'withdrawal', 'airtime'];
        const statuses = ['success', 'failed', 'pending'];
        const transactions = [];

        for (let i = 0; i < 100; i++) {
            const date = new Date();
            date.setDate(date.getDate() - Math.floor(Math.random() * 30));
            
            transactions.push({
                id: i + 1,
                date: date.toISOString(),
                phone: `+256${Math.floor(Math.random() * 1000000000).toString().padStart(9, '0')}`,
                amount: Math.random() * 1000 + 10,
                category: categories[Math.floor(Math.random() * categories.length)],
                status: statuses[Math.floor(Math.random() * statuses.length)]
            });
        }

        return {
            summary: {
                totalTransactions: transactions.length,
                totalVolume: transactions.reduce((sum, t) => sum + t.amount, 0),
                averageTransaction: transactions.reduce((sum, t) => sum + t.amount, 0) / transactions.length,
                activeUsers: new Set(transactions.map(t => t.phone)).size
            },
            transactions: transactions,
            categories: categories,
            lastUpdated: new Date().toISOString()
        };
    }

    hideLoading() {
        const loading = document.getElementById('loading');
        if (loading) {
            loading.style.display = 'none';
        }
    }

    showError(message) {
        this.hideLoading();
        const main = document.querySelector('main');
        main.innerHTML = `
            <div class="error-message">
                <h3>Error</h3>
                <p>${message}</p>
                <button onclick="location.reload()">Retry</button>
            </div>
        `;
    }

    setupEventListeners() {
        // Search functionality
        const searchInput = document.getElementById('search-input');
        searchInput.addEventListener('input', (e) => {
            this.filterData();
        });

        // Category filter
        const categoryFilter = document.getElementById('category-filter');
        this.populateCategoryFilter();
        categoryFilter.addEventListener('change', (e) => {
            this.filterData();
        });
    }

    populateCategoryFilter() {
        const categoryFilter = document.getElementById('category-filter');
        const categories = [...new Set(this.data.transactions.map(t => t.category))];
        
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category.charAt(0).toUpperCase() + category.slice(1);
            categoryFilter.appendChild(option);
        });
    }

    filterData() {
        const searchTerm = document.getElementById('search-input').value.toLowerCase();
        const categoryFilter = document.getElementById('category-filter').value;

        this.filteredData = this.data.transactions.filter(transaction => {
            const matchesSearch = !searchTerm || 
                transaction.phone.toLowerCase().includes(searchTerm) ||
                transaction.category.toLowerCase().includes(searchTerm) ||
                transaction.status.toLowerCase().includes(searchTerm);
            
            const matchesCategory = !categoryFilter || transaction.category === categoryFilter;

            return matchesSearch && matchesCategory;
        });

        this.renderTable();
    }

    renderSummaryCards() {
        const summary = this.data.summary;
        
        document.getElementById('total-transactions').textContent = summary.totalTransactions.toLocaleString();
        document.getElementById('total-volume').textContent = `$${summary.totalVolume.toFixed(2)}`;
        document.getElementById('avg-transaction').textContent = `$${summary.averageTransaction.toFixed(2)}`;
        document.getElementById('active-users').textContent = summary.activeUsers.toLocaleString();
    }

    renderCharts() {
        this.renderVolumeChart();
        this.renderCategoryChart();
    }

    renderVolumeChart() {
        const ctx = document.getElementById('volume-chart').getContext('2d');
        
        // Group transactions by date
        const volumeByDate = {};
        this.data.transactions.forEach(transaction => {
            const date = new Date(transaction.date).toISOString().split('T')[0];
            volumeByDate[date] = (volumeByDate[date] || 0) + transaction.amount;
        });

        const dates = Object.keys(volumeByDate).sort();
        const volumes = dates.map(date => volumeByDate[date]);

        this.charts.volumeChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates.map(date => new Date(date).toLocaleDateString()),
                datasets: [{
                    label: 'Transaction Volume ($)',
                    data: volumes,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(0);
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    renderCategoryChart() {
        const ctx = document.getElementById('category-chart').getContext('2d');
        
        // Count transactions by category
        const categoryCount = {};
        this.data.transactions.forEach(transaction => {
            categoryCount[transaction.category] = (categoryCount[transaction.category] || 0) + 1;
        });

        const categories = Object.keys(categoryCount);
        const counts = Object.values(categoryCount);
        const colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe'];

        this.charts.categoryChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: categories.map(cat => cat.charAt(0).toUpperCase() + cat.slice(1)),
                datasets: [{
                    data: counts,
                    backgroundColor: colors.slice(0, categories.length),
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    renderTable() {
        const tbody = document.querySelector('#transactions-table tbody');
        tbody.innerHTML = '';

        // Show only first 50 transactions for performance
        const displayData = this.filteredData.slice(0, 50);

        displayData.forEach(transaction => {
            const row = document.createElement('tr');
            
            const statusClass = `status-${transaction.status}`;
            
            row.innerHTML = `
                <td>${new Date(transaction.date).toLocaleDateString()}</td>
                <td>${this.maskPhoneNumber(transaction.phone)}</td>
                <td>$${transaction.amount.toFixed(2)}</td>
                <td>${transaction.category.charAt(0).toUpperCase() + transaction.category.slice(1)}</td>
                <td><span class="${statusClass}">${transaction.status.charAt(0).toUpperCase() + transaction.status.slice(1)}</span></td>
            `;
            
            tbody.appendChild(row);
        });

        if (displayData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">No transactions found</td></tr>';
        }
    }

    maskPhoneNumber(phone) {
        // Mask middle digits for privacy: +256XXXX1234 -> +256****1234
        if (phone.length > 8) {
            return phone.slice(0, 4) + '****' + phone.slice(-4);
        }
        return phone;
    }

    updateLastUpdated() {
        const lastUpdatedElement = document.getElementById('last-updated');
        const lastUpdated = new Date(this.data.lastUpdated);
        lastUpdatedElement.textContent = lastUpdated.toLocaleString();
    }

    // Method to refresh data (can be called by external refresh button)
    async refresh() {
        const loading = document.getElementById('loading');
        loading.style.display = 'flex';
        
        await this.loadData();
        this.renderSummaryCards();
        
        // Destroy existing charts before recreating
        Object.values(this.charts).forEach(chart => chart.destroy());
        this.charts = {};
        
        this.renderCharts();
        this.renderTable();
        this.updateLastUpdated();
        
        loading.style.display = 'none';
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new DashboardManager();
});

// Export for potential use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardManager;
}
