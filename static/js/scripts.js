// Configuração da API
const isLocalhost = window.location.hostname === 'localhost';

const API_BASE_URL = isLocalhost ? 'http://localhost:8000' : 'https://over-the-board.onrender.com';

// Estado da aplicação
let currentSection = 'home';
let apiData = {};

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    updateClock();
    checkApiHealth();
    getCacheStats();
});

// Inicialização da aplicação
function initializeApp() {
    showSection('home');
    updateClock();
    setInterval(updateClock, 1000);
}

// Event Listeners
function setupEventListeners() {
    // Navegação
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const section = e.currentTarget.dataset.section;
            showSection(section);
        });
    });

    // Enter key nos inputs
    document.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const activeSection = document.querySelector('.section.active');
            if (activeSection) {
                const sectionId = activeSection.id;
                switch(sectionId) {
                    case 'tournaments':
                        searchTournaments();
                        break;
                    case 'players':
                        searchPlayers();
                        break;
                    case 'news':
                        searchNews();
                        break;
                    case 'announcements':
                        searchAnnouncements();
                        break;
                }
            }
        }
    });
}

// Navegação entre seções
function showSection(sectionName) {
    // Remove classe active de todas as seções
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Remove classe active de todos os botões de navegação
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Adiciona classe active na seção atual
    document.getElementById(sectionName).classList.add('active');
    
    // Adiciona classe active no botão correspondente
    document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');
    
    // Fechar menu mobile se estiver aberto
    const navbarCollapse = document.getElementById('navbarNav');
    if (navbarCollapse && navbarCollapse.classList.contains('show')) {
        const bsCollapse = new bootstrap.Collapse(navbarCollapse, {
            toggle: false
        });
        bsCollapse.hide();
    }
    
    currentSection = sectionName;
}

// Utilitários
function updateClock() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('pt-BR', { 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
    });
    document.getElementById('currentTime').textContent = timeString;
}

function showLoading() {
    document.getElementById('loadingOverlay').classList.add('show');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('show');
}

function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.5rem;" data-i18n="">
            <i class="fas fa-${getToastIcon(type)}" data-i18n=""></i>
            <span data-i18n="">${message}</span>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Remove o toast após 5 segundos
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

function getToastIcon(type) {
    switch(type) {
        case 'success': return 'check-circle';
        case 'error': return 'exclamation-circle';
        case 'warning': return 'exclamation-triangle';
        default: return 'info-circle';
    }
}

// API Calls
async function makeApiCall(endpoint, params = {}) {
    try {
        const url = new URL(`${API_BASE_URL}${endpoint}`);
        Object.keys(params).forEach(key => {
            if (params[key] !== '' && params[key] !== null && params[key] !== undefined) {
                url.searchParams.append(key, params[key]);
            }
        });

        console.log('Making API call to:', url.toString());
        
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Atualiza o painel admin com a resposta
        document.getElementById('apiResponse').textContent = JSON.stringify(data, null, 2);
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        document.getElementById('apiResponse').textContent = `Erro: ${error.message}`;
        throw error;
    }
}

// Health Check
let currentLanguage = 'en'; // Defina o idioma atual globalmente

async function checkApiHealth() {
  try {
    const health = await makeApiCall('/health');

    const apiStatus = document.getElementById('apiStatus');
    apiStatus.setAttribute('data-i18n', 'home.online');

    const healthStatus = document.getElementById('healthStatus');
    healthStatus.innerHTML = `
      <span class="status-dot healthy"></span>
      <span class="status-text" data-i18n="admin.statusTitle"></span>
    `;

    showToast('API está funcionando corretamente', 'success');
  } catch (error) {
    const apiStatus = document.getElementById('apiStatus');
    apiStatus.setAttribute('data-i18n', 'home.offline');

    const healthStatus = document.getElementById('healthStatus');
    healthStatus.innerHTML = `
      <span class="status-dot error"></span>
      <span class="status-text" data-i18n="admin.statusTitle"></span>
    `;

    showToast('Erro ao conectar com a API', 'error');
  }

  // Reaplica a tradução com base no idioma atual
  await loadLocale(currentLanguage);
}


// Cache Stats
async function getCacheStats() {
    try {
        const stats = await makeApiCall('/cache/stats');
        const cacheSize = stats.cache_size || 0;

        // Verificação de segurança para o elemento 'cacheSize'
        const cacheSizeElement = document.getElementById('cacheSize');
        if (cacheSizeElement) {
            cacheSizeElement.textContent = cacheSize;
        }

        // Verificação de segurança para o elemento 'adminCacheSize'
        const adminCacheSizeElement = document.getElementById('adminCacheSize');
        if (adminCacheSizeElement) {
            adminCacheSizeElement.textContent = cacheSize;
        }
    } catch (error) {
        // Tratar o erro de forma segura, evitando que o erro se propague para o console do navegador
        const cacheSizeElement = document.getElementById('cacheSize');
        if (cacheSizeElement) {
            cacheSizeElement.textContent = 'Error';
        }

        const adminCacheSizeElement = document.getElementById('adminCacheSize');
        if (adminCacheSizeElement) {
            adminCacheSizeElement.textContent = 'Error';
        }
        console.error('Erro ao obter estatísticas de cache:', error);
    }
}

// Clear Cache
async function clearCache() {
    if (!confirm('Tem certeza que deseja limpar o cache?')) {
        return;
    }
    
    try {
        showLoading();
        await fetch(`${API_BASE_URL}/cache/clear`, { method: 'DELETE' });
        await getCacheStats();
        showToast('Cache limpo com sucesso', 'success');
    } catch (error) {
        showToast('Erro ao limpar cache', 'error');
    } finally {
        hideLoading();
    }
}

// Search Functions
async function searchTournaments() {
    const year = document.getElementById('tournamentYear').value;
    const month = document.getElementById('tournamentMonth').value;
    const limit = document.getElementById('tournamentLimit').value;
    
    try {
        showLoading();
        const response_tournaments = await makeApiCall('/tournaments', {
            federation: 'cbx',
            year: year,
            month: month,
            limit: limit
        });
        
        const tournaments = response_tournaments.cbx;

        displayTournaments(tournaments);
        showToast(`${tournaments.length} torneios encontrados`, 'success');
    } catch (error) {
        showToast('Erro ao buscar torneios', 'error');
        document.getElementById('tournamentsResults').innerHTML = `
            <div class="empty-state" data-i18n="">
                <i class="fas fa-exclamation-triangle" data-i18n=""></i>
                <p data-i18n="js.tournament.error.none">Erro ao carregar torneios: ${error.message}</p>
            </div>
        `;
    } finally {
        hideLoading();
    }
}

async function searchPlayers() {
    const state = document.getElementById('playerUF').value;
    const pages = document.getElementById('playerPages').value;
    
    try {
        showLoading();
        const response_players = await makeApiCall('/players', {
            state: state,
            pages: pages
        });

        const players = response_players.cbx;
        
        displayPlayers(players);
        showToast(`${players.length} jogadores encontrados`, 'success');
    } catch (error) {
        showToast('Erro ao buscar jogadores', 'error');
        document.getElementById('playersResults').innerHTML = `
            <div class="empty-state" data-i18n="">
                <i class="fas fa-exclamation-triangle" data-i18n=""></i>
                <p data-i18n="js.player.error.none">Erro ao carregar jogadores: ${error.message}</p>
            </div>
        `;
    } finally {
        hideLoading();
    }
}

async function searchNews() {
    const pages = document.getElementById('newsPages').value;
    
    try {
        showLoading();
        const news = await makeApiCall('/news', {
            paginas: pages
        });
        
        displayNews(news);
        showToast(`${news.length} notícias encontradas`, 'success');
    } catch (error) {
        showToast('Erro ao buscar notícias', 'error');
        document.getElementById('newsResults').innerHTML = `
            <div class="empty-state" data-i18n="">
                <i class="fas fa-exclamation-triangle" data-i18n=""></i>
                <p data-i18n="js.news.error.none">Erro ao carregar notícias: ${error.message}</p>
            </div>
        `;
    } finally {
        hideLoading();
    }
}

async function searchAnnouncements() {
    const pages = document.getElementById('announcementPages').value;
    
    try {
        showLoading();
        const announcements = await makeApiCall('/announcements', {
            paginas: pages
        });
        
        displayAnnouncements(announcements);
        showToast(`${announcements.length} comunicados encontrados`, 'success');
    } catch (error) {
        showToast('Erro ao buscar comunicados', 'error');
        document.getElementById('announcementsResults').innerHTML = `
            <div class="empty-state" data-i18n="">
                <i class="fas fa-exclamation-triangle" data-i18n=""></i>
                <p data-i18n="js.announcements.error.none">Erro ao carregar comunicados: ${error.message}</p>
            </div>
        `;
    } finally {
        hideLoading();
    }
}

// Display Functions
function displayTournaments(tournaments) {
    const container = document.getElementById('tournamentsResults');
    
    if (!tournaments || tournaments.length === 0) {
        container.innerHTML = `
            <div class="empty-state" data-i18n="">
                <i class="fas fa-trophy" data-i18n=""></i>
                <p data-i18n="js.tournament.error.none">Nenhum torneio encontrado</p>
            </div>
        `;
        return;
    }
    
    const cardsHTML = tournaments.map(tournament => `
        <div class="card tournament-card" data-i18n="">
            <div class="card-header" data-i18n="">
                <div class="card-title">${tournament.name || 'Nome não disponível'}</div>
                <div class="tournament-meta" data-i18n="">
                    ${tournament.id ? `<span class="tournament-badge" data-i18n="">ID: ${tournament.id}</span>` : ''}
                    ${tournament.status ? `<span class="tournament-badge status" data-i18n="">${tournament.status}</span>` : ''}
                </div>
            </div>
            <div class="card-body" data-i18n="">
                <div class="tournament-details" data-i18n="">
                    ${tournament.period ? `<p data-i18n=""><strong data-i18n="js.tournament.period">Período:</strong> ${tournament.period}</p>` : ''}
                    ${tournament.location ? `<p data-i18n=""><strong data-i18n="js.tournament.location">Local:</strong> ${tournament.location}</p>` : ''}
                    ${tournament.organizer ? `<p data-i18n=""><strong data-i18n="js.tournament.organizer">Organizador:</strong> ${tournament.organizer}</p>` : ''}
                    ${tournament.time_control ? `<p data-i18n=""><strong data-i18n="js.tournament.timeControl">Ritmo:</strong> ${tournament.time_control}</p>` : ''}
                    ${tournament.total_players ? `<p data-i18n=""><strong data-i18n="js.tournament.totalPlayers">Total de Jogadores:</strong> ${tournament.total_players}</p>` : ''}
                    ${tournament.fide_players ? `<p data-i18n=""><strong data-i18n="js.tournament.fidePlayers">Jogadores FIDE:</strong> ${tournament.fide_players}</p>` : ''}
                    ${tournament.rating ? `<p data-i18n=""><strong data-i18n="js.tournament.rating">Rating:</strong> ${tournament.rating}</p>` : ''}
                    ${tournament.observation ? `<p data-i18n=""><strong data-i18n="js.tournament.observation">Observações:</strong> ${tournament.observation}</p>` : ''}
                    ${tournament.regulation && tournament.regulation !== 'https://www.cbx.org.br' ? 
                        `<p data-i18n=""><a href="${tournament.regulation}" target="_blank" class="news-link" data-i18n="js.tournament.regulation">Ver Regulamento</a></p>` : ''}
                </div>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = `<div class="card-grid" data-i18n="">${cardsHTML}</div>`;
}

function displayPlayers(players) {
    const container = document.getElementById('playersResults');
    
    if (!players || players.length === 0) {
        container.innerHTML = `
            <div class="empty-state" data-i18n="">
                <i class="fas fa-users" data-i18n=""></i>
                <p data-i18n="js.player.error.none">Nenhum jogador encontrado</p>
            </div>
        `;
        return;
    }
    
    const cardsHTML = players.map(player => `
        <div class="card player-card" data-i18n="">
            <div class="card-header" data-i18n="">
                <div class="card-title" data-i18n="js.player.error.name">${player.name || 'Nome não disponível'} </div>
            </div>
            <div class="card-body" data-i18n="">
                <div class="player-details" data-i18n="">
                    ${player.country ? `<p data-i18n=""><strong data-i18n="js.player.country">País:</strong> ${player.country}</p>` : ''}
                    ${player.state ? `<p data-i18n=""><strong data-i18n="js.player.state">UF:</strong> ${player.state}</p>` : ''}
                    ${player.birthday ? `<p data-i18n=""><strong data-i18n="js.player.birthday">Nascimento:</strong> ${player.birthday}</p>` : ''}
                    ${player.local_id ? `<p data-i18n=""><strong data-i18n="js.player.localId">ID CBX:</strong> ${player.local_id}</p>` : ''}
                    ${player.fide_id ? `<p data-i18n=""><strong data-i18n="js.player.fideId">ID FIDE:</strong> ${player.fide_id}</p>` : ''}
                    ${player.classical ? `<p data-i18n=""><strong data-i18n="js.player.classical">Clássico:</strong> ${player.classical}</p>` : ''}
                    ${player.rapid ? `<p data-i18n=""><strong data-i18n="js.player.rapid">Rápido:</strong> ${player.rapid}</p>` : ''}
                    ${player.blitz ? `<p data-i18n=""><strong data-i18n="js.player.blitz">Blitz:</strong> ${player.blitz}</p>` : ''}
                    ${player.local_profile && player.local_profile !== 'https://www.cbx.org.br/jogador/' ? 
                        `<p data-i18n=""><a href="${player.local_profile}" target="_blank" class="news-link" data-i18n="js.player.profile">Ver Perfil</a></p>` : ''}
                </div>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = `<div class="card-grid" data-i18n="">${cardsHTML}</div>`;
}

function displayNews(news) {
    const container = document.getElementById('newsResults');
    
    if (!news || news.length === 0) {
        container.innerHTML = `
            <div class="empty-state" data-i18n="">
                <i class="fas fa-newspaper" data-i18n=""></i>
                <p data-i18n="js.news.error.none">Nenhuma notícia encontrada</p>
            </div>
        `;
        return;
    }
    
    const cardsHTML = news.map(item => `
        <div class="card news-card" data-i18n="">
            <div class="card-header" data-i18n="">
                <div class="card-title" data-i18n="js.news.error.name">${item.title || 'Título não disponível'}</div>
                ${item.date_text ? `<div class="news-date" data-i18n="">${item.date_text}</div>` : ''}
            </div>
            <div class="card-body" data-i18n="">
                ${item.link ? `<a href="${item.link}" target="_blank" class="news-link" data-i18n="js.news.link">Ler notícia completa</a>` : ''}
            </div>
        </div>
    `).join('');
    
    container.innerHTML = `<div class="card-grid" data-i18n="">${cardsHTML}</div>`;
}

function displayAnnouncements(announcements) {
    const container = document.getElementById('announcementsResults');
    
    if (!announcements || announcements.length === 0) {
        container.innerHTML = `
            <div class="empty-state" data-i18n="">
                <i class="fas fa-bullhorn" data-i18n=""></i>
                <p data-i18n="js.announcements.error.none">Nenhum comunicado encontrado</p>
            </div>
        `;
        return;
    }
    
    const cardsHTML = announcements.map(item => `
        <div class="card announcement-card" data-i18n="">
            <div class="card-header" data-i18n="">
                <div class="card-title" data-i18n="js.announcements.error.name">${item.title || 'Título não disponível'}</div>
                ${item.date_text ? `<div class="announcement-date" data-i18n="">${item.date_text}</div>` : ''}
            </div>
            <div class="card-body" data-i18n="">
                ${item.link ? `<a href="${item.link}" target="_blank" class="announcement-link" data-i18n="js.announcements.link">Ler comunicado completo</a>` : ''}
            </div>
        </div>
    `).join('');
    
    container.innerHTML = `<div class="card-grid" data-i18n="">${cardsHTML}</div>`;
}

// Admin Functions
async function checkHealth() {
    await checkApiHealth();
}

// The next line of code were causing a headache, so I'll comment them out for now.
// Refresh cache stats periodically
// setInterval(getCacheStats, 30000); // A cada 30 segundos

// Auto-refresh API status
// setInterval(checkApiHealth, 60000); // A cada 1 minuto
