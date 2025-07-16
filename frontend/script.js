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
            // Simulate API call
            const startTime = performance.now();
            const results = await this.simulateSearch(query);
            const endTime = performance.now();
            
            this.searchResults = results;
            this.displayResults(results);
            this.updateStats(results.length, Math.round(endTime - startTime));
            
        } catch (error) {
            this.showToast('Search failed. Please try again.', 'error');
            console.error('Search error:', error);
        } finally {
            this.isSearching = false;
            this.hideLoading();
        }
    }

    async simulateSearch(query) {
        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, 200 + Math.random() * 500));
        
        // Mock search results
        const mockResults = this.generateMockResults(query);
        
        // Filter by current filter
        return this.filterResults(mockResults, this.currentFilter);
    }

    generateMockResults(query) {
        const fileTypes = {
            documents: ['.txt', '.pdf', '.doc', '.docx', '.md', '.rtf'],
            images: ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'],
            videos: ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'],
            code: ['.js', '.ts', '.py', '.java', '.cpp', '.c', '.cs', '.php', '.go', '.rs']
        };

        const paths = [
            'C:\\Users\\Documents\\Projects',
            'C:\\Users\\Desktop\\Work',
            'C:\\Program Files\\Development',
            'D:\\Data\\Archives',
            'C:\\Users\\Downloads',
            'C:\\Users\\Pictures',
            'C:\\Users\\Videos',
            'C:\\dev\\repositories'
        ];

        const results = [];
        const resultCount = Math.floor(Math.random() * 50) + 10;

        for (let i = 0; i < resultCount; i++) {
            const allExtensions = Object.values(fileTypes).flat();
            const extension = allExtensions[Math.floor(Math.random() * allExtensions.length)];
            const path = paths[Math.floor(Math.random() * paths.length)];
            const filename = this.generateFilename(query, extension);
            
            results.push({
                name: filename,
                path: `${path}\\${filename}`,
                extension: extension,
                size: Math.floor(Math.random() * 1024 * 1024 * 100), // Random size up to 100MB
                modified: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000),
                type: this.getFileType(extension)
            });
        }

        return results.sort((a, b) => {
            // Sort by relevance (how well the filename matches the query)
            const aRelevance = this.calculateRelevance(a.name, query);
            const bRelevance = this.calculateRelevance(b.name, query);
            return bRelevance - aRelevance;
        });
    }

    generateFilename(query, extension) {
        const queryWords = query.toLowerCase().split(' ');
        const randomWords = ['project', 'file', 'document', 'data', 'backup', 'draft', 'final', 'v2', 'updated'];
        
        // Sometimes include query words in filename
        let filename = '';
        if (Math.random() > 0.3) {
            filename = queryWords[Math.floor(Math.random() * queryWords.length)];
            if (Math.random() > 0.5) {
                filename += '_' + randomWords[Math.floor(Math.random() * randomWords.length)];
            }
        } else {
            filename = randomWords[Math.floor(Math.random() * randomWords.length)];
        }
        
        // Add random suffix sometimes
        if (Math.random() > 0.7) {
            filename += '_' + Math.floor(Math.random() * 100);
        }
        
        return filename + extension;
    }

    calculateRelevance(filename, query) {
        const lowerFilename = filename.toLowerCase();
        const lowerQuery = query.toLowerCase();
        
        if (lowerFilename.includes(lowerQuery)) return 100;
        
        const queryWords = lowerQuery.split(' ');
        let relevance = 0;
        
        queryWords.forEach(word => {
            if (lowerFilename.includes(word)) {
                relevance += 50;
            }
        });
        
        return relevance;
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
        const icon = this.getFileIcon(result.extension);
        const size = this.formatFileSize(result.size);
        const date = this.formatDate(result.modified);

        return `
            <div class="result-item" data-type="${result.type}">
                <div class="result-header">
                    <div class="file-icon">
                        <i class="${icon}"></i>
                    </div>
                    <div class="file-name">${result.name}</div>
                </div>
                <div class="file-path">${result.path}</div>
                <div class="file-meta">
                    <span><i class="fas fa-hdd"></i> ${size}</span>
                    <span><i class="fas fa-calendar"></i> ${date}</span>
                    <span><i class="fas fa-tag"></i> ${result.type}</span>
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
        document.getElementById('indexedFiles').textContent = (Math.floor(Math.random() * 1000000) + 100000).toLocaleString();
        
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
        this.showToast(`Opening: ${file.name}`, 'info');
        // In a real implementation, this would interact with the MCP server
        console.log('Opening file:', file);
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
        // Add some demo stats on load
        setTimeout(() => {
            this.updateStats(0, 0);
        }, 1000);
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
    app.showToast('Settings panel coming soon!', 'info');
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