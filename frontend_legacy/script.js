// FastSearch MCP Frontend JavaScript
class FastSearchApp {
    constructor() {
        this.currentFilter = 'all';
        this.currentView = 'list';
        this.searchResults = [];
        this.isSearching = false;
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.updateStats();
        this.showWelcomeAnimation();
    }

    bindEvents() {
        // Search events
        const searchInput = document.getElementById('searchInput');
        const searchBtn = document.getElementById('searchBtn');
        
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });
        
        searchInput.addEventListener('input', (e) => {
            if (e.target.value.length === 0) {
                this.clearResults();
            }
        });
        
        searchBtn.addEventListener('click', () => {
            this.performSearch();
        });

        // Filter events
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.setFilter(e.currentTarget.dataset.filter);
            });
        });

        // View toggle events
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.setView(e.currentTarget.dataset.view);
            });
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K to focus search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                searchInput.focus();
                searchInput.select();
            }
        });
    }

    async performSearch() {
        const query = document.getElementById('searchInput').value.trim();
        
        if (!query) {
            this.showToast('Please enter a search term', 'warning');
            return;
        }

        if (this.isSearching) return;

        this.isSearching = true;
        this.showLoading();
        
        try {
            // Call the actual FastSearch API
            const results = await this.callFastSearchAPI(query);
            
            this.searchResults = results.results || [];
            this.displayResults(this.searchResults);
            this.updateStats(results.count || 0, results.search_time_ms || 0);
            
            if (!results.success) {
                this.showToast(results.message || 'Search completed with warnings', 'warning');
            } else {
                this.showToast(`Found ${results.count} files in ${results.search_time_ms}ms`, 'info');
            }
            
        } catch (error) {
            let errorMessage = 'Failed to connect to FastSearch server. ';
            
            if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                errorMessage += 'Make sure the FastSearch MCP server is running on port 3001.';
            } else if (error.message.includes('HTTP error')) {
                errorMessage += `Server returned error: ${error.message}`;
            } else {
                errorMessage += 'Please check the server connection and try again.';
            }
            
            this.showToast(errorMessage, 'error');
            console.error('FastSearch API error:', error);
            
            // Clear results on error
            this.clearResults();
        } finally {
            this.isSearching = false;
            this.hideLoading();
        }
    }

    async callFastSearchAPI(query) {
        // Call the actual FastSearch Web API
        const apiUrl = 'http://localhost:3001/api/search';
        
        const searchRequest = {
            pattern: query,
            max_results: 1000,
            filters: {
                exclude_dirs: this.currentFilter !== 'all' ? this.getExcludeDirs() : [],
                file_types: this.currentFilter !== 'all' ? this.getFileTypes() : []
            }
        };
        
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(searchRequest)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Transform the results to match our frontend format
        if (result.success && result.results) {
            result.results = result.results.map(file => {
                const extension = this.extractFileExtension(file.name);
                return {
                    name: file.name,
                    path: file.full_path,
                    extension: extension,
                    size: file.size || 0,
                    modified: file.modified > 0 ? new Date(file.modified * 1000) : new Date(), // Convert from Unix timestamp
                    type: this.getFileType(extension),
                    is_directory: file.is_directory || false
                };
            });
        }
        
        return result;
    }
    
    extractFileExtension(filename) {
        const lastDot = filename.lastIndexOf('.');
        return lastDot !== -1 ? filename.substring(lastDot) : '';
    }

    getExcludeDirs() {
        const excludeMap = {
            'documents': ['.git', 'node_modules', 'target', 'build'],
            'images': ['.git', 'node_modules', 'target', 'build', 'cache'],
            'videos': ['.git', 'node_modules', 'target', 'build', 'cache'],
            'code': ['node_modules', 'target', 'build', 'dist', '.git']
        };
        return excludeMap[this.currentFilter] || [];
    }
    
    getFileTypes() {
        const typeMap = {
            'documents': ['.txt', '.pdf', '.doc', '.docx', '.md', '.rtf'],
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'],
            'videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'],
            'code': ['.js', '.ts', '.py', '.java', '.cpp', '.c', '.cs', '.php', '.go', '.rs']
        };
        return typeMap[this.currentFilter] || [];
    }



    getFileType(extension) {
        const typeMap = {
            '.txt': 'documents', '.pdf': 'documents', '.doc': 'documents', '.docx': 'documents', '.md': 'documents', '.rtf': 'documents',
            '.jpg': 'images', '.jpeg': 'images', '.png': 'images', '.gif': 'images', '.bmp': 'images', '.svg': 'images', '.webp': 'images',
            '.mp4': 'videos', '.avi': 'videos', '.mkv': 'videos', '.mov': 'videos', '.wmv': 'videos', '.flv': 'videos', '.webm': 'videos',
            '.js': 'code', '.ts': 'code', '.py': 'code', '.java': 'code', '.cpp': 'code', '.c': 'code', '.cs': 'code', '.php': 'code', '.go': 'code', '.rs': 'code'
        };
        
        return typeMap[extension] || 'other';
    }

    filterResults(results, filter) {
        if (filter === 'all') return results;
        return results.filter(result => result.type === filter);
    }

    displayResults(results) {
        const container = document.getElementById('resultsContainer');
        const noResults = document.getElementById('noResults');
        const resultsTitle = document.getElementById('resultsTitle');

        if (results.length === 0) {
            container.innerHTML = '';
            noResults.classList.add('show');
            resultsTitle.textContent = 'No Results Found';
            return;
        }

        noResults.classList.remove('show');
        resultsTitle.textContent = `${results.length} Results Found`;
        
        container.innerHTML = results.map(result => this.createResultHTML(result)).join('');
        container.className = `results-container ${this.currentView}-view`;

        // Add click events to result items
        container.querySelectorAll('.result-item').forEach((item, index) => {
            item.addEventListener('click', () => this.openFile(results[index]));
        });

        // Animate results
        this.animateResults();
    }

    createResultHTML(result) {
        const icon = result.is_directory ? 'fas fa-folder' : this.getFileIcon(result.extension);
        const size = result.is_directory ? 'Folder' : this.formatFileSize(result.size);
        const date = this.formatDate(result.modified);
        const itemType = result.is_directory ? 'folder' : result.type;

        return `
            <div class="result-item" data-type="${itemType}">
                <div class="result-header">
                    <div class="file-icon" style="color: ${result.is_directory ? '#4CAF50' : '#2196F3'}">
                        <i class="${icon}"></i>
                    </div>
                    <div class="file-name">${result.name}</div>
                </div>
                <div class="file-path">${result.path}</div>
                <div class="file-meta">
                    <span><i class="fas fa-hdd"></i> ${size}</span>
                    <span><i class="fas fa-calendar"></i> ${date}</span>
                    <span><i class="fas fa-tag"></i> ${itemType}</span>
                </div>
            </div>
        `;
    }

    getFileIcon(extension) {
        const iconMap = {
            '.txt': 'fas fa-file-alt',
            '.pdf': 'fas fa-file-pdf',
            '.doc': 'fas fa-file-word', '.docx': 'fas fa-file-word',
            '.md': 'fab fa-markdown',
            '.jpg': 'fas fa-file-image', '.jpeg': 'fas fa-file-image', '.png': 'fas fa-file-image', '.gif': 'fas fa-file-image',
            '.mp4': 'fas fa-file-video', '.avi': 'fas fa-file-video', '.mkv': 'fas fa-file-video',
            '.js': 'fab fa-js-square', '.ts': 'fab fa-js-square',
            '.py': 'fab fa-python',
            '.java': 'fab fa-java',
            '.php': 'fab fa-php'
        };
        
        return iconMap[extension] || 'fas fa-file';
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    formatDate(date) {
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays} days ago`;
        if (diffDays < 30) return `${Math.ceil(diffDays / 7)} weeks ago`;
        if (diffDays < 365) return `${Math.ceil(diffDays / 30)} months ago`;
        return `${Math.ceil(diffDays / 365)} years ago`;
    }

    setFilter(filter) {
        this.currentFilter = filter;
        
        // Update active filter button
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === filter);
        });

        // Re-filter and display results if we have them
        if (this.searchResults.length > 0) {
            const filteredResults = this.filterResults(this.searchResults, filter);
            this.displayResults(filteredResults);
        }
    }

    setView(view) {
        this.currentView = view;
        
        // Update active view button
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === view);
        });

        // Update results container class
        const container = document.getElementById('resultsContainer');
        container.className = `results-container ${view}-view`;
    }

    updateStats(resultCount = 0, searchTime = 0) {
        document.getElementById('resultCount').textContent = resultCount.toLocaleString();
        document.getElementById('searchTime').textContent = `${searchTime}ms`;
        
        // Update performance indicator
        const performanceEl = document.getElementById('performance');
        if (searchTime < 50) {
            performanceEl.textContent = 'Ultra Fast';
            performanceEl.style.color = '#4CAF50';
        } else if (searchTime < 200) {
            performanceEl.textContent = 'Fast';
            performanceEl.style.color = '#2196F3';
        } else {
            performanceEl.textContent = 'Normal';
            performanceEl.style.color = '#FF9800';
        }
        
        // Load real server status on first load or when stats are updated
        this.loadServerStatus();
    }
    
    async loadServerStatus() {
        try {
            const response = await fetch('http://localhost:3001/api/status');
            if (response.ok) {
                const status = await response.json();
                if (status.success) {
                    document.getElementById('indexedFiles').textContent = status.indexed_files.toLocaleString();
                } else {
                    document.getElementById('indexedFiles').textContent = 'Unknown';
                }
            }
        } catch (error) {
            console.warn('Could not load server status:', error);
            document.getElementById('indexedFiles').textContent = 'Connecting...';
        }
    }

    showLoading() {
        document.getElementById('loading').classList.add('show');
        document.getElementById('resultsSection').style.opacity = '0.5';
    }

    hideLoading() {
        document.getElementById('loading').classList.remove('show');
        document.getElementById('resultsSection').style.opacity = '1';
    }

    clearResults() {
        document.getElementById('resultsContainer').innerHTML = '';
        document.getElementById('noResults').classList.remove('show');
        document.getElementById('resultsTitle').textContent = 'Search Results';
        this.searchResults = [];
        this.updateStats();
    }

    animateResults() {
        const items = document.querySelectorAll('.result-item');
        items.forEach((item, index) => {
            item.style.opacity = '0';
            item.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                item.style.transition = 'all 0.3s ease';
                item.style.opacity = '1';
                item.style.transform = 'translateY(0)';
            }, index * 50);
        });
    }

    openFile(file) {
        // For security reasons, we can't directly open files from a web interface
        // Instead, show the file location for the user to navigate to
        const message = file.is_directory ? 
            `Directory location: ${file.path}` : 
            `File location: ${file.path}`;
        
        this.showToast(message, 'info');
        
        // Copy file path to clipboard if possible
        if (navigator.clipboard) {
            navigator.clipboard.writeText(file.path).then(() => {
                setTimeout(() => {
                    this.showToast('File path copied to clipboard', 'info');
                }, 1000);
            }).catch(() => {
                console.log('Could not copy to clipboard');
            });
        }
        
        console.log('File details:', file);
    }

    showToast(message, type = 'info') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <i class="fas fa-${type === 'error' ? 'exclamation-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
            <span>${message}</span>
        `;
        
        // Add toast styles if not already added
        if (!document.querySelector('#toast-styles')) {
            const style = document.createElement('style');
            style.id = 'toast-styles';
            style.textContent = `
                .toast {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: white;
                    padding: 1rem 1.5rem;
                    border-radius: 8px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    z-index: 1001;
                    animation: slideInRight 0.3s ease;
                }
                .toast-error { border-left: 4px solid #f44336; }
                .toast-warning { border-left: 4px solid #ff9800; }
                .toast-info { border-left: 4px solid #2196f3; }
                @keyframes slideInRight {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(toast);
        
        // Remove toast after 3 seconds
        setTimeout(() => {
            toast.style.animation = 'slideInRight 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    showWelcomeAnimation() {
        // Initialize with real server stats and check connection
        this.checkServerConnection();
        this.updateStats(0, 0);
    }
    
    async checkServerConnection() {
        try {
            const response = await fetch('http://localhost:3001/api/health');
            if (response.ok) {
                const health = await response.json();
                if (health.status === 'healthy') {
                    this.showToast('✅ Connected to FastSearch MCP Server', 'info');
                    this.loadServerStatus();
                } else {
                    this.showToast('⚠️ FastSearch server is not ready', 'warning');
                }
            }
        } catch (error) {
            console.warn('Server connection check failed:', error);
            this.showToast('❌ Cannot connect to FastSearch server on localhost:3001', 'error');
            document.getElementById('indexedFiles').textContent = 'Server offline';
        }
    }
}

// Modal functions
function showAbout() {
    document.getElementById('aboutModal').classList.add('show');
}

function showHelp() {
    app.showToast('Help documentation coming soon!', 'info');
}

function showSettings() {
    const settingsInfo = `
    FastSearch MCP Server Settings:
    
    • Server URL: http://localhost:3001
    • Status: ${document.getElementById('indexedFiles').textContent === 'Server offline' ? 'Offline' : 'Connected'}
    • Indexed Files: ${document.getElementById('indexedFiles').textContent}
    
    To start the server, run:
    cargo run --release -- --web-api
    `;
    
    app.showToast(settingsInfo, 'info');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('show');
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new FastSearchApp();
    
    // Add some keyboard shortcuts info to search placeholder
    const isMac = navigator.platform.indexOf('Mac') > -1;
    const shortcut = isMac ? '⌘+K' : 'Ctrl+K';
    document.getElementById('searchInput').placeholder += ` (${shortcut} to focus)`;
});

// Close modals when clicking outside
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('show');
    }
}); 