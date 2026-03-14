(function () {
  var app = window.PhyloApp;

  function init() {
    app.ensureContainer();
    app.initDevTools();
    app.bindZoomControls();
    app.bindNodeActions();
    try {
      app.setStatus("Rendering tree...", false);
      app.renderTree(window.__TREE_VIEWER_DATA__ && window.__TREE_VIEWER_DATA__.newick);
    } catch (error) {
      app.setStatus(error.message, true);
      throw error;
    }
  }

  window.addEventListener("DOMContentLoaded", init);
})();
