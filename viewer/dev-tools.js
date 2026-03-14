(function () {
  var app = window.PhyloApp;

  app.applyDevToolsVisibility = function () {
    var appState = app.state;

    document.documentElement.dataset.devMode = appState.devModeEnabled ? "on" : "off";
    document.querySelectorAll("[data-dev-only]").forEach(function (element) {
      element.hidden = !appState.devModeEnabled;
    });
  };

  app.setDevToolsEnabled = function (enabled) {
    app.state.devModeEnabled = Boolean(enabled);
    app.applyDevToolsVisibility();
  };

  app.initDevTools = function () {
    app.applyDevToolsVisibility();
  };
})();
