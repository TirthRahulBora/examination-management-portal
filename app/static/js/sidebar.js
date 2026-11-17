/**
 * Examination Management Portal (EMP) — Responsive & Collapsible Sidebar Controller
 */
document.addEventListener('DOMContentLoaded', function () {
  const sidebar = document.getElementById('sidebar');
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebarCollapseBtn = document.getElementById('sidebarCollapseBtn');
  const backdrop = document.getElementById('sidebarBackdrop');

  if (!sidebar) return;

  // Restore saved state on desktop (>= 992px)
  const isDesktop = () => window.innerWidth >= 992;
  const savedState = localStorage.getItem('emp_sidebar_collapsed');

  if (isDesktop() && savedState === 'true') {
    sidebar.classList.add('collapsed');
  }

  // Initialize tooltips on sidebar nav links
  let tooltipInstances = [];
  function updateTooltips() {
    tooltipInstances.forEach(t => t.dispose());
    tooltipInstances = [];

    if (sidebar.classList.contains('collapsed') && isDesktop()) {
      const navLinks = sidebar.querySelectorAll('.nav-link[data-tooltip-text]');
      navLinks.forEach(link => {
        const text = link.getAttribute('data-tooltip-text');
        if (text && window.bootstrap) {
          const t = new bootstrap.Tooltip(link, {
            title: text,
            placement: 'right',
            trigger: 'hover'
          });
          tooltipInstances.push(t);
        }
      });
    }
  }

  // Toggle Collapse on Desktop / Drawer on Mobile
  function toggleSidebar() {
    if (isDesktop()) {
      sidebar.classList.toggle('collapsed');
      const isCollapsed = sidebar.classList.contains('collapsed');
      localStorage.setItem('emp_sidebar_collapsed', isCollapsed ? 'true' : 'false');
      updateTooltips();
    } else {
      sidebar.classList.toggle('sidebar-open');
      if (backdrop) {
        backdrop.classList.toggle('d-none', !sidebar.classList.contains('sidebar-open'));
      }
    }
  }

  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', toggleSidebar);
  }

  if (sidebarCollapseBtn) {
    sidebarCollapseBtn.addEventListener('click', function () {
      if (isDesktop()) {
        sidebar.classList.toggle('collapsed');
        const isCollapsed = sidebar.classList.contains('collapsed');
        localStorage.setItem('emp_sidebar_collapsed', isCollapsed ? 'true' : 'false');
        updateTooltips();
      }
    });
  }

  if (backdrop) {
    backdrop.addEventListener('click', function () {
      sidebar.classList.remove('sidebar-open');
      backdrop.classList.add('d-none');
    });
  }

  // Window resize handler
  window.addEventListener('resize', function () {
    if (isDesktop()) {
      if (backdrop) backdrop.classList.add('d-none');
      sidebar.classList.remove('sidebar-open');
      const isCollapsed = localStorage.getItem('emp_sidebar_collapsed') === 'true';
      sidebar.classList.toggle('collapsed', isCollapsed);
    } else {
      sidebar.classList.remove('collapsed');
    }
    updateTooltips();
  });

  // Initial tooltips setup
  updateTooltips();

  // Keyboard shortcut: Ctrl + [ or Cmd + [ toggles sidebar
  document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === '[') {
      e.preventDefault();
      toggleSidebar();
    }
  });
});
