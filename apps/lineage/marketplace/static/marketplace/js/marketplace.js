/**
 * MARKETPLACE.JS - Ultra Gamer Style
 * Efeitos visuais épicos para marketplace de personagens
 * Versão: 2.0 - Gaming Edition
 */

(function() {
    'use strict';

    // Main initialization
    document.addEventListener('DOMContentLoaded', function() {
        initMarketplace();
        initGamerEffects();
    });

    /**
     * Initialize marketplace functionality
     */
    function initMarketplace() {
        initConfirmations();
        initFilters();
        initCharacterPreview();
        initFormValidations();
        initCardHoverEffects();
        
        console.log('🎮 Marketplace Gaming Edition initialized');
    }

    /**
     * Initialize gamer visual effects
     */
    function initGamerEffects() {
        // Efeito de partículas nos cards ao hover
        const cards = document.querySelectorAll('.character-card');
        cards.forEach(card => {
            card.addEventListener('mouseenter', function(e) {
                createParticles(e.currentTarget);
            });
        });

        // Efeito nos botões
        const buttons = document.querySelectorAll('.btn-primary, .btn-success');
        buttons.forEach(btn => {
            btn.addEventListener('click', function(e) {
                createRipple(e);
                createButtonParticles(e);
            });
        });

        // Animação dos badges
        animateStatusBadges();
    }

    /**
     * Create particle effect
     * @param {HTMLElement} element - Element to create particles from
     */
    function createParticles(element) {
        const rect = element.getBoundingClientRect();
        const particleCount = 8;

        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.className = 'marketplace-particle';
            
            const angle = (Math.PI * 2 * i) / particleCount;
            const velocity = 50 + Math.random() * 50;
            const x = Math.cos(angle) * velocity;
            const y = Math.sin(angle) * velocity;
            
            particle.style.cssText = `
                position: absolute;
                width: 6px;
                height: 6px;
                background: linear-gradient(135deg, #6f42c1, #0dcaf0);
                border-radius: 50%;
                pointer-events: none;
                box-shadow: 0 0 10px rgba(111, 66, 193, 0.8);
                --x: ${x}px;
                --y: ${y}px;
            `;
            
            element.appendChild(particle);
            
            particle.style.animation = 'particleFloat 1.5s ease-out forwards';
            
            setTimeout(() => particle.remove(), 1500);
        }
    }

    /**
     * Create ripple effect on button click
     * @param {Event} e - Click event
     */
    function createRipple(e) {
        const button = e.currentTarget;
        const ripple = document.createElement('span');
        const rect = button.getBoundingClientRect();
        
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;
        
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: radial-gradient(circle, rgba(255, 255, 255, 0.6) 0%, transparent 70%);
            border-radius: 50%;
            transform: scale(0);
            animation: rippleEffect 0.6s ease-out;
            pointer-events: none;
        `;
        
        button.appendChild(ripple);
        setTimeout(() => ripple.remove(), 600);
    }

    /**
     * Create particles on button click
     * @param {Event} e - Click event
     */
    function createButtonParticles(e) {
        const rect = e.currentTarget.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        
        for (let i = 0; i < 12; i++) {
            const particle = document.createElement('div');
            const angle = (Math.PI * 2 * i) / 12;
            const velocity = 80 + Math.random() * 40;
            
            particle.style.cssText = `
                position: fixed;
                left: ${centerX}px;
                top: ${centerY}px;
                width: 8px;
                height: 8px;
                background: linear-gradient(135deg, #0dcaf0, #6f42c1);
                border-radius: 50%;
                pointer-events: none;
                box-shadow: 0 0 15px rgba(13, 202, 240, 0.9);
                z-index: 9999;
            `;
            
            document.body.appendChild(particle);
            
            const x = Math.cos(angle) * velocity;
            const y = Math.sin(angle) * velocity;
            
            particle.animate([
                { transform: 'translate(0, 0) scale(1)', opacity: 1 },
                { transform: `translate(${x}px, ${y}px) scale(0)`, opacity: 0 }
            ], {
                duration: 1000,
                easing: 'cubic-bezier(0, 0.9, 0.3, 1)'
            });
            
            setTimeout(() => particle.remove(), 1000);
        }
    }

    /**
     * Animate status badges
     */
    function animateStatusBadges() {
        const badges = document.querySelectorAll('.status-badge');
        badges.forEach((badge, index) => {
            setTimeout(() => {
                badge.style.animation = 'pulse 2.5s infinite';
            }, index * 100);
        });
    }

    /**
     * Initialize card hover effects
     */
    function initCardHoverEffects() {
        const cards = document.querySelectorAll('.character-card');
        
        cards.forEach(card => {
            card.addEventListener('mousemove', function(e) {
                const rect = this.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                const centerX = rect.width / 2;
                const centerY = rect.height / 2;
                
                const rotateX = (y - centerY) / 20;
                const rotateY = (centerX - x) / 20;
                
                this.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-12px) scale(1.03)`;
            });
            
            card.addEventListener('mouseleave', function() {
                this.style.transform = '';
            });
        });
    }

    /**
     * Initialize confirmation dialogs
     */
    function initConfirmations() {
        // Cancel sale confirmations
        const cancelForms = document.querySelectorAll('form[action*="cancel"]');
        cancelForms.forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                showGamerConfirm(
                    '⚔️ Cancelar Venda',
                    'Deseja realmente cancelar esta venda? Esta ação não pode ser desfeita.',
                    () => {
                        showLoading('🔄 Cancelando venda...');
                        form.submit();
                    }
                );
            });
        });

        // Buy confirmations
        const buyForms = document.querySelectorAll('form[action*="buy"]');
        buyForms.forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                const price = form.closest('.reports-card')?.querySelector('.price-amount')?.textContent || '0.00';
                showGamerConfirm(
                    '🛒 Confirmar Compra',
                    `Você está prestes a comprar este personagem por ${price}. Confirma?`,
                    () => {
                        showLoading('💎 Processando compra...');
                        form.submit();
                    }
                );
            });
        });
    }

    /**
     * Show gamer-style confirmation dialog
     * @param {string} title - Dialog title
     * @param {string} message - Dialog message
     * @param {Function} onConfirm - Callback on confirm
     */
    function showGamerConfirm(title, message, onConfirm) {
        const overlay = document.createElement('div');
        overlay.className = 'gamer-confirm-overlay';
        overlay.innerHTML = `
            <div class="gamer-confirm-box">
                <div class="gamer-confirm-header">
                    <h3>${title}</h3>
                </div>
                <div class="gamer-confirm-body">
                    <p>${message}</p>
                </div>
                <div class="gamer-confirm-actions">
                    <button class="btn-confirm-yes">✓ Confirmar</button>
                    <button class="btn-confirm-no">✗ Cancelar</button>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        // Add styles dynamically
        const style = document.createElement('style');
        style.textContent = `
            .gamer-confirm-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.85);
                backdrop-filter: blur(10px);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
                animation: fadeIn 0.3s ease;
            }
            .gamer-confirm-box {
                background: linear-gradient(135deg, #1a1a2e, #121220);
                border: 3px solid;
                border-image: linear-gradient(135deg, #6f42c1, #e83e8c, #0dcaf0) 1;
                border-radius: 20px;
                padding: 0;
                max-width: 500px;
                box-shadow: 0 0 40px rgba(111, 66, 193, 0.6), 0 0 60px rgba(13, 202, 240, 0.4);
                animation: popIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            }
            .gamer-confirm-header {
                background: linear-gradient(135deg, #6f42c1, #e83e8c);
                padding: 1.5rem;
                border-radius: 17px 17px 0 0;
            }
            .gamer-confirm-header h3 {
                color: white;
                font-family: 'Orbitron', sans-serif;
                font-size: 1.5rem;
                margin: 0;
                text-transform: uppercase;
                letter-spacing: 2px;
                text-shadow: 0 0 15px rgba(255, 255, 255, 0.6);
            }
            .gamer-confirm-body {
                padding: 2rem;
                color: #e0e0e0;
                font-family: 'Orbitron', sans-serif;
                font-size: 1.1rem;
                text-align: center;
            }
            .gamer-confirm-actions {
                padding: 1.5rem;
                display: flex;
                gap: 1rem;
                border-top: 2px solid rgba(111, 66, 193, 0.3);
            }
            .btn-confirm-yes, .btn-confirm-no {
                flex: 1;
                padding: 1rem;
                border: none;
                border-radius: 12px;
                font-family: 'Orbitron', sans-serif;
                font-weight: 700;
                font-size: 1rem;
                text-transform: uppercase;
                letter-spacing: 1.5px;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .btn-confirm-yes {
                background: linear-gradient(135deg, #10b981, #059669);
                color: white;
                box-shadow: 0 0 20px rgba(16, 185, 129, 0.5);
            }
            .btn-confirm-yes:hover {
                transform: scale(1.05);
                box-shadow: 0 0 30px rgba(16, 185, 129, 0.7);
            }
            .btn-confirm-no {
                background: linear-gradient(135deg, #6c757d, #495057);
                color: white;
                box-shadow: 0 0 15px rgba(108, 117, 125, 0.5);
            }
            .btn-confirm-no:hover {
                transform: scale(1.05);
                box-shadow: 0 0 25px rgba(108, 117, 125, 0.7);
            }
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            @keyframes popIn {
                0% { transform: scale(0.5); opacity: 0; }
                100% { transform: scale(1); opacity: 1; }
            }
            @keyframes rippleEffect {
                to { transform: scale(4); opacity: 0; }
            }
            @keyframes particleFloat {
                0% { transform: translate(0, 0) scale(1); opacity: 1; }
                100% { transform: translate(var(--x), var(--y)) scale(0); opacity: 0; }
            }
        `;
        document.head.appendChild(style);

        // Event listeners
        overlay.querySelector('.btn-confirm-yes').addEventListener('click', () => {
            createFireworks(overlay);
            setTimeout(() => {
                overlay.remove();
                if (onConfirm) onConfirm();
            }, 300);
        });

        overlay.querySelector('.btn-confirm-no').addEventListener('click', () => {
            overlay.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => overlay.remove(), 300);
        });

        // Add fadeOut animation
        const fadeOutStyle = document.createElement('style');
        fadeOutStyle.textContent = '@keyframes fadeOut { to { opacity: 0; } }';
        document.head.appendChild(fadeOutStyle);
    }

    /**
     * Create fireworks effect
     * @param {HTMLElement} element - Element to create fireworks in
     */
    function createFireworks(element) {
        for (let i = 0; i < 20; i++) {
            setTimeout(() => {
                const firework = document.createElement('div');
                const x = Math.random() * 100 - 50;
                const y = Math.random() * 100 - 50;
                
                firework.style.cssText = `
                    position: absolute;
                    left: 50%;
                    top: 50%;
                    width: 8px;
                    height: 8px;
                    background: ${['#6f42c1', '#e83e8c', '#0dcaf0'][Math.floor(Math.random() * 3)]};
                    border-radius: 50%;
                    box-shadow: 0 0 15px currentColor;
                    pointer-events: none;
                `;
                
                element.appendChild(firework);
                
                firework.animate([
                    { transform: 'translate(0, 0) scale(1)', opacity: 1 },
                    { transform: `translate(${x}px, ${y}px) scale(0)`, opacity: 0 }
                ], {
                    duration: 800,
                    easing: 'cubic-bezier(0, 0.9, 0.3, 1)'
                });
                
                setTimeout(() => firework.remove(), 800);
            }, i * 30);
        }
    }

    /**
     * Initialize filters
     */
    function initFilters() {
        const filterForm = document.getElementById('filterForm');
        if (!filterForm) return;

        // Level filter
        const minLevel = document.getElementById('minLevel');
        const maxLevel = document.getElementById('maxLevel');
        
        if (minLevel && maxLevel) {
            minLevel.addEventListener('change', function() {
                if (parseInt(maxLevel.value) < parseInt(minLevel.value)) {
                    maxLevel.value = minLevel.value;
                }
                highlightFilter(this);
            });

            maxLevel.addEventListener('change', function() {
                if (parseInt(maxLevel.value) < parseInt(minLevel.value)) {
                    minLevel.value = maxLevel.value;
                }
                highlightFilter(this);
            });
        }

        // Price filter
        const minPrice = document.getElementById('minPrice');
        const maxPrice = document.getElementById('maxPrice');
        
        if (minPrice && maxPrice) {
            minPrice.addEventListener('change', function() {
                if (parseFloat(maxPrice.value) < parseFloat(minPrice.value)) {
                    maxPrice.value = minPrice.value;
                }
                highlightFilter(this);
            });

            maxPrice.addEventListener('change', function() {
                if (parseFloat(maxPrice.value) < parseFloat(minPrice.value)) {
                    minPrice.value = maxPrice.value;
                }
                highlightFilter(this);
            });
        }

        // Apply filters
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            showLoading('🔍 Aplicando filtros...');
            setTimeout(() => applyFilters(), 500);
        });
    }

    /**
     * Highlight filter input
     * @param {HTMLElement} input - Input element
     */
    function highlightFilter(input) {
        input.style.boxShadow = '0 0 20px rgba(13, 202, 240, 0.6)';
        input.style.borderColor = '#0dcaf0';
        setTimeout(() => {
            input.style.boxShadow = '';
            input.style.borderColor = '';
        }, 1000);
    }

    /**
     * Apply filters
     */
    function applyFilters() {
        const form = document.getElementById('filterForm');
        if (!form) return;

        const formData = new FormData(form);
        const params = new URLSearchParams(formData);
        
        window.location.href = `${window.location.pathname}?${params.toString()}`;
    }

    /**
     * Initialize character preview
     */
    function initCharacterPreview() {
        const characterSelect = document.getElementById('character_select');
        if (!characterSelect) return;

        characterSelect.addEventListener('change', function() {
            const charId = this.value;
            if (charId) {
                loadCharacterPreview(charId);
            } else {
                hideCharacterPreview();
            }
        });
    }

    /**
     * Load character preview
     * @param {string} charId - Character ID
     */
    function loadCharacterPreview(charId) {
        const preview = document.getElementById('character_preview');
        if (!preview) return;

        preview.style.display = 'block';
        preview.innerHTML = `
            <div class="text-center">
                <i class="fas fa-spinner fa-spin fa-2x" style="color: #0dcaf0; text-shadow: 0 0 20px rgba(13, 202, 240, 0.8);"></i>
                <p style="margin-top: 1rem; color: #cbd5e1; font-family: 'Orbitron', sans-serif;">⚡ Carregando dados do personagem...</p>
            </div>
        `;

        // Simulate loading
        setTimeout(() => {
            preview.innerHTML = `
                <div class="character-preview-content" style="text-align: center;">
                    <i class="fas fa-user-shield fa-3x mb-3" style="color: #0dcaf0; text-shadow: 0 0 25px rgba(13, 202, 240, 0.9);"></i>
                    <h5 style="color: #fff; font-family: 'Orbitron', sans-serif; margin-bottom: 1rem;">
                        ✨ Preview do Personagem
                    </h5>
                    <p style="color: #a8a8a8; font-family: 'Orbitron', sans-serif;">
                        ID do Personagem: <strong style="color: #0dcaf0;">${charId}</strong>
                    </p>
                    <p class="small" style="color: #94a3b8; margin-top: 1rem;">
                        💡 Os detalhes completos serão carregados após a seleção
                    </p>
                </div>
            `;
            preview.style.animation = 'popIn 0.4s ease-out';
        }, 800);
    }

    /**
     * Hide character preview
     */
    function hideCharacterPreview() {
        const preview = document.getElementById('character_preview');
        if (preview) {
            preview.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => {
                preview.style.display = 'none';
                preview.innerHTML = '';
            }, 300);
        }
    }

    /**
     * Initialize form validations
     */
    function initFormValidations() {
        const sellForm = document.getElementById('sellForm');
        if (!sellForm) return;

        const charSelect = document.getElementById('character_select');
        const priceInput = document.getElementById('price');
        const notesInput = document.getElementById('notes');

        // Character selection validation
        if (charSelect) {
            charSelect.addEventListener('change', function() {
                if (this.value) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                    createSuccessParticles(this);
                }
            });
        }

        // Price validation with visual feedback
        if (priceInput) {
            priceInput.addEventListener('input', function() {
                const price = parseFloat(this.value);
                if (price > 0) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                    this.style.boxShadow = '0 0 20px rgba(16, 185, 129, 0.5)';
                } else {
                    this.classList.remove('is-valid');
                    this.classList.add('is-invalid');
                    this.style.boxShadow = '0 0 20px rgba(239, 68, 68, 0.5)';
                }
            });

            priceInput.addEventListener('blur', function() {
                this.style.boxShadow = '';
            });
        }

        // Notes character limit with visual counter
        if (notesInput) {
            const maxLength = 500;
            const counterContainer = document.createElement('div');
            counterContainer.className = 'character-counter';
            counterContainer.style.cssText = `
                text-align: right;
                margin-top: 0.5rem;
                font-family: 'Orbitron', sans-serif;
                font-weight: 600;
            `;
            notesInput.parentNode.appendChild(counterContainer);

            function updateCounter() {
                const remaining = maxLength - notesInput.value.length;
                const percentage = (notesInput.value.length / maxLength) * 100;
                
                let color = '#0dcaf0';
                if (percentage > 80) color = '#f59e0b';
                if (percentage > 95) color = '#ef4444';
                
                counterContainer.innerHTML = `
                    <span style="color: ${color}; text-shadow: 0 0 10px ${color};">
                        ${notesInput.value.length} / ${maxLength} caracteres
                    </span>
                `;

                if (remaining < 0) {
                    notesInput.value = notesInput.value.substring(0, maxLength);
                    updateCounter();
                }
            }

            notesInput.addEventListener('input', updateCounter);
            updateCounter();
        }

        // Form submission with epic effect
        sellForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            let isValid = true;

            if (charSelect && !charSelect.value) {
                charSelect.classList.add('is-invalid');
                isValid = false;
            }

            if (priceInput && parseFloat(priceInput.value) <= 0) {
                priceInput.classList.add('is-invalid');
                isValid = false;
            }

            if (!isValid) {
                showNotification('❌ Preencha todos os campos obrigatórios!', 'error');
                shakeElement(sellForm);
                return;
            }

            showGamerConfirm(
                '🎯 Listar Personagem',
                'Seu personagem será listado no marketplace. Confirma?',
                () => {
                    showLoading('🚀 Listando personagem...');
                    sellForm.submit();
                }
            );
        });
    }

    /**
     * Create success particles
     * @param {HTMLElement} element - Element to create particles from
     */
    function createSuccessParticles(element) {
        const rect = element.getBoundingClientRect();
        for (let i = 0; i < 6; i++) {
            const particle = document.createElement('div');
            particle.style.cssText = `
                position: fixed;
                left: ${rect.right - 20}px;
                top: ${rect.top + rect.height / 2}px;
                width: 6px;
                height: 6px;
                background: #10b981;
                border-radius: 50%;
                box-shadow: 0 0 10px #10b981;
                pointer-events: none;
                z-index: 9999;
            `;
            
            document.body.appendChild(particle);
            
            const x = (Math.random() - 0.5) * 60;
            const y = (Math.random() - 0.5) * 60;
            
            particle.animate([
                { transform: 'translate(0, 0) scale(1)', opacity: 1 },
                { transform: `translate(${x}px, ${y}px) scale(0)`, opacity: 0 }
            ], {
                duration: 1000,
                easing: 'ease-out'
            });
            
            setTimeout(() => particle.remove(), 1000);
        }
    }

    /**
     * Shake element animation
     * @param {HTMLElement} element - Element to shake
     */
    function shakeElement(element) {
        element.style.animation = 'shake 0.5s ease';
        
        if (!document.getElementById('shake-animation')) {
            const style = document.createElement('style');
            style.id = 'shake-animation';
            style.textContent = `
                @keyframes shake {
                    0%, 100% { transform: translateX(0); }
                    10%, 30%, 50%, 70%, 90% { transform: translateX(-10px); }
                    20%, 40%, 60%, 80% { transform: translateX(10px); }
                }
            `;
            document.head.appendChild(style);
        }
        
        setTimeout(() => {
            element.style.animation = '';
        }, 500);
    }

    /**
     * Show loading overlay with epic design
     * @param {string} message - Loading message
     */
    function showLoading(message = '⚡ Processando...') {
        const overlay = document.createElement('div');
        overlay.id = 'marketplace-loading';
        overlay.innerHTML = `
            <div class="loading-spinner-container">
                <div class="loading-spinner-ring"></div>
                <div class="loading-spinner-ring"></div>
                <div class="loading-spinner-ring"></div>
                <i class="fas fa-dragon fa-3x loading-icon"></i>
                <p class="loading-text">${message}</p>
            </div>
        `;
        
        const style = document.createElement('style');
        style.textContent = `
            #marketplace-loading {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.9);
                backdrop-filter: blur(10px);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
                animation: fadeIn 0.3s ease;
            }
            .loading-spinner-container {
                position: relative;
                width: 200px;
                height: 200px;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-direction: column;
            }
            .loading-spinner-ring {
                position: absolute;
                width: 150px;
                height: 150px;
                border-radius: 50%;
                border: 4px solid transparent;
                animation: spin 2s linear infinite;
            }
            .loading-spinner-ring:nth-child(1) {
                border-top-color: #6f42c1;
                animation-duration: 1.5s;
            }
            .loading-spinner-ring:nth-child(2) {
                border-right-color: #e83e8c;
                animation-duration: 2s;
            }
            .loading-spinner-ring:nth-child(3) {
                border-bottom-color: #0dcaf0;
                animation-duration: 2.5s;
            }
            .loading-icon {
                color: #fff;
                text-shadow: 0 0 20px rgba(111, 66, 193, 0.8);
                animation: pulse 2s infinite;
                z-index: 1;
            }
            .loading-text {
                color: #fff;
                font-family: 'Orbitron', sans-serif;
                font-size: 1.2rem;
                font-weight: 700;
                margin-top: 6rem;
                text-shadow: 0 0 15px rgba(13, 202, 240, 0.8);
                letter-spacing: 1px;
            }
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        `;
        
        if (!document.getElementById('loading-styles')) {
            style.id = 'loading-styles';
            document.head.appendChild(style);
        }
        
        document.body.appendChild(overlay);
    }

    /**
     * Hide loading overlay
     */
    function hideLoading() {
        const overlay = document.getElementById('marketplace-loading');
        if (overlay) {
            overlay.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => overlay.remove(), 300);
        }
    }

    /**
     * Show notification with gaming style
     * @param {string} message - Message
     * @param {string} type - Type (success, error, warning, info)
     */
    function showNotification(message, type = 'info') {
        const colors = {
            success: { bg: '#10b981', shadow: 'rgba(16, 185, 129, 0.6)' },
            error: { bg: '#ef4444', shadow: 'rgba(239, 68, 68, 0.6)' },
            warning: { bg: '#f59e0b', shadow: 'rgba(245, 158, 11, 0.6)' },
            info: { bg: '#0dcaf0', shadow: 'rgba(13, 202, 240, 0.6)' }
        };
        
        const color = colors[type] || colors.info;
        
        const notification = document.createElement('div');
        notification.className = 'gamer-notification';
        notification.innerHTML = `
            <div class="gamer-notification-content">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'} me-2"></i>
                <span>${message}</span>
            </div>
        `;
        
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, ${color.bg}, rgba(0, 0, 0, 0.8));
            color: white;
            padding: 1.25rem 2rem;
            border-radius: 15px;
            box-shadow: 0 0 30px ${color.shadow};
            font-family: 'Orbitron', sans-serif;
            font-weight: 700;
            z-index: 10001;
            animation: slideInRight 0.5s ease-out;
            border: 2px solid ${color.bg};
        `;
        
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideInRight {
                from { transform: translateX(400px); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOutRight {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(400px); opacity: 0; }
            }
        `;
        if (!document.getElementById('notification-animations')) {
            style.id = 'notification-animations';
            document.head.appendChild(style);
        }
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.5s ease-out';
            setTimeout(() => notification.remove(), 500);
        }, 4000);
    }

    /**
     * Format price
     * @param {number} price - Price value
     * @param {string} currency - Currency
     * @returns {string} Formatted price
     */
    function formatPrice(price, currency = 'BRL') {
        const symbols = {
            'BRL': 'R$',
            'USD': '$',
            'EUR': '€'
        };

        const symbol = symbols[currency] || currency;
        return `${symbol} ${parseFloat(price).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }

    // Export to global scope
    window.MarketplaceJS = {
        formatPrice,
        showLoading,
        hideLoading,
        showNotification,
        createParticles,
        createFireworks
    };

})();
