document.addEventListener('DOMContentLoaded', function () {
  const toggleBtn = document.getElementById('theme-toggle-btn');
  const themeStyle = document.getElementById('theme-style');
  const themeIcon = document.getElementById('theme-icon');

  function setTheme(isDark) {
    themeStyle.href = isDark ? "/static/dark.css" : "/static/light.css";
    localStorage.setItem("theme", isDark ? "dark" : "light");
    themeIcon.className = isDark ? "bi bi-moon-stars-fill" : "bi bi-sun-fill";
  }

  const savedTheme = localStorage.getItem("theme");
  let isDark = savedTheme === "dark";
  setTheme(isDark);

  toggleBtn.addEventListener("click", function () {
    isDark = !isDark;
    setTheme(isDark);
  });

  // Auto dismiss floating alerts after 3 seconds
  const alerts = document.querySelectorAll('.floating-alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      bsAlert.close();
    }, 3000);
  });
});
