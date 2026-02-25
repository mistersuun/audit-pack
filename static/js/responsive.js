/**
 * RESPONSIVE.JS - Mobile Menu & Responsive Behavior
 * Handles hamburger menu toggle, sidebar off-canvas, and mobile interactions
 */

(function() {
    'use strict';

    // ─── DOM Elements ───
    const hamburgerBtn = document.querySelector('.hamburger-btn');
    const sidebar = document.querySelector('.sidebar');
    const body = document.body;
    const html = document.documentElement;

    // ─── Mobile breakpoint (matches CSS media query) ───
    const MOBILE_BREAKPOINT = 768;

    /**
     * Check if viewport is in mobile range
     */
    function isMobile() {
        return window.innerWidth <= MOBILE_BREAKPOINT;
    }

    /**
     * Hamburger Menu Toggle
     */
    function toggleSidebar(e) {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }

        if (!sidebar) return;

        const isOpen = sidebar.classList.contains('open');

        if (isOpen) {
            closeSidebar();
        } else {
            openSidebar();
        }
    }

    /**
     * Open sidebar
     */
    function openSidebar() {
        if (!sidebar) return;

        sidebar.classList.add('open');
        body.classList.add('sidebar-open');
        html.style.overflow = 'hidden'; // Prevent body scroll when sidebar is open
    }

    /**
     * Close sidebar
     */
    function closeSidebar() {
        if (!sidebar) return;

        sidebar.classList.remove('open');
        body.classList.remove('sidebar-open');
        html.style.overflow = ''; // Re-enable body scroll
    }

    /**
     * Close sidebar when clicking outside on mobile
     */
    function handleOutsideClick(e) {
        if (!isMobile()) return;
        if (!sidebar || !sidebar.classList.contains('open')) return;

        // If click is outside sidebar, close it
        if (!sidebar.contains(e.target) && e.target !== hamburgerBtn) {
            closeSidebar();
        }
    }

    /**
     * Close sidebar after clicking a menu item
     */
    function handleMenuItemClick(e) {
        if (!isMobile()) return;

        const target = e.target;
        const isLink = target.tagName === 'A' || target.closest('a');

        if (isLink && !target.closest('.menu-parent')) {
            // Regular link clicked (not an expandable menu parent)
            setTimeout(closeSidebar, 100);
        }
    }

    /**
     * Handle window resize - close sidebar if resizing back to desktop
     */
    function handleWindowResize() {
        if (!isMobile() && sidebar && sidebar.classList.contains('open')) {
            closeSidebar();
        }
    }

    /**
     * Enhance menu group toggle for mobile
     */
    function enhanceMenuGroupToggle() {
        const menuParents = document.querySelectorAll('.menu-parent');

        menuParents.forEach(parent => {
            parent.addEventListener('click', function(e) {
                const group = this.closest('.menu-group');
                if (!group) return;

                // On mobile, just toggle the group (don't navigate)
                if (isMobile()) {
                    e.preventDefault();
                    group.classList.toggle('open');
                }
            });
        });
    }

    /**
     * Initialize sidebar state based on viewport
     */
    function initSidebarState() {
        if (!sidebar) return;

        if (isMobile()) {
            closeSidebar();
            if (hamburgerBtn) {
                hamburgerBtn.style.display = 'flex';
            }
        } else {
            sidebar.classList.remove('open');
            body.classList.remove('sidebar-open');
            html.style.overflow = '';
            if (hamburgerBtn) {
                hamburgerBtn.style.display = 'none';
            }
        }
    }

    /**
     * Fix viewport height on mobile (address safari vh bug)
     */
    function fixViewportHeight() {
        // Get actual viewport height
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
    }

    /**
     * Setup horizontal scroll indicators for tables and tabs
     */
    function setupScrollIndicators() {
        const scrollables = document.querySelectorAll('.table-responsive, .rj-native .tabs-container');

        scrollables.forEach(container => {
            function updateScrollButtons() {
                const isScrollable = container.scrollWidth > container.clientWidth;
                container.classList.toggle('is-scrollable', isScrollable);

                if (isScrollable) {
                    const isAtStart = container.scrollLeft === 0;
                    const isAtEnd = container.scrollLeft >= container.scrollWidth - container.clientWidth - 5;

                    container.classList.toggle('scroll-at-start', isAtStart);
                    container.classList.toggle('scroll-at-end', isAtEnd);
                }
            }

            updateScrollButtons();
            container.addEventListener('scroll', updateScrollButtons);
            window.addEventListener('resize', updateScrollButtons);
        });
    }

    /**
     * Add visual feedback for form inputs on mobile
     */
    function enhanceFormInputs() {
        const inputs = document.querySelectorAll('.form-control, input, select, textarea');

        inputs.forEach(input => {
            // Add focus class for styling
            input.addEventListener('focus', function() {
                this.classList.add('is-focused');
            });

            input.addEventListener('blur', function() {
                this.classList.remove('is-focused');
            });

            // Add filled class if input has value
            input.addEventListener('input', function() {
                this.classList.toggle('is-filled', this.value.length > 0);
            });

            // Check initial state
            if (input.value.length > 0) {
                input.classList.add('is-filled');
            }
        });
    }

    /**
     * Keyboard navigation improvements
     */
    function setupKeyboardNavigation() {
        // Close sidebar with Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && sidebar && sidebar.classList.contains('open')) {
                closeSidebar();
                if (hamburgerBtn) {
                    hamburgerBtn.focus();
                }
            }
        });
    }

    /**
     * Initialize all responsive features
     */
    function init() {
        // Hamburger button click handler
        if (hamburgerBtn) {
            hamburgerBtn.addEventListener('click', toggleSidebar);
        }

        // Outside click to close sidebar
        document.addEventListener('click', handleOutsideClick);

        // Menu item click to close sidebar
        const sidebarMenu = document.querySelector('.sidebar-menu');
        if (sidebarMenu) {
            sidebarMenu.addEventListener('click', handleMenuItemClick, true);
        }

        // Window resize handler
        window.addEventListener('resize', handleWindowResize);
        window.addEventListener('resize', fixViewportHeight);

        // Initial state setup
        initSidebarState();
        fixViewportHeight();
        enhanceMenuGroupToggle();
        setupScrollIndicators();
        enhanceFormInputs();
        setupKeyboardNavigation();

        // Re-initialize on visibility change (tab switch, etc.)
        document.addEventListener('visibilitychange', function() {
            if (!document.hidden) {
                fixViewportHeight();
                initSidebarState();
            }
        });
    }

    /**
     * Public API for external scripts
     */
    window.ResponsiveUI = {
        toggleSidebar: toggleSidebar,
        openSidebar: openSidebar,
        closeSidebar: closeSidebar,
        isMobile: isMobile,
        getBreakpoint: function() {
            return MOBILE_BREAKPOINT;
        }
    };

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
