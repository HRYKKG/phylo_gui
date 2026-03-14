(function () {
  var app = window.PhyloApp;

  app.applyDevToolsVisibility = function () {
    var appState = app.state;
    var toggleButton = document.getElementById("dev-tools-toggle");

    document.documentElement.dataset.devMode = appState.devModeEnabled ? "on" : "off";
    document.querySelectorAll("[data-dev-only]").forEach(function (element) {
      element.hidden = !appState.devModeEnabled;
    });

    if (toggleButton) {
      toggleButton.textContent = appState.devModeEnabled ? "Dev Tools: On" : "Dev Tools: Off";
      toggleButton.classList.toggle("is-active", appState.devModeEnabled);
    }
  };

  app.bindDevToolsToggle = function () {
    var toggleButton = document.getElementById("dev-tools-toggle");

    if (toggleButton) {
      toggleButton.onclick = function () {
        app.state.devModeEnabled = !app.state.devModeEnabled;
        app.applyDevToolsVisibility();
      };
    }

    app.applyDevToolsVisibility();
  };
})();
