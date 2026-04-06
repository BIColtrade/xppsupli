(function () {
  function initSidebar() {
    var sidebar = document.querySelector(".sidebar");
    if (!sidebar) {
      return;
    }
    var toggle = sidebar.querySelector(".sidebar__toggle");
    var icon = sidebar.querySelector(".sidebar__toggle-icon");
    if (!toggle) {
      return;
    }

    var expandedIcon = toggle.getAttribute("data-expanded-icon") || "\u276E";
    var collapsedIcon = toggle.getAttribute("data-collapsed-icon") || "\u276F";

    toggle.addEventListener("click", function () {
      var collapsed = sidebar.classList.toggle("is-collapsed");
      toggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
      toggle.setAttribute(
        "aria-label",
        collapsed ? "Expandir sidebar" : "Contraer sidebar"
      );
      if (icon) {
        icon.textContent = collapsed ? collapsedIcon : expandedIcon;
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSidebar);
  } else {
    initSidebar();
  }
})();
