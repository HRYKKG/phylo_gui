(function () {
  window.PhyloApp = {
    state: {
      tree: null,
      display: null,
      renderProfile: null,
      fontSizePx: 10,
      nodeRadiusPx: 3,
      devModeEnabled: Boolean(window.__TREE_VIEWER_DATA__ && window.__TREE_VIEWER_DATA__.devMode),
      activeNodeName: null,
      selectedLeafNames: [],
      boxSelectedNodeIds: [],
      selectedBranchNodeIds: [],
      selectionMode: "browse",
      selectionDrag: null,
      dragBindingsInstalled: false,
    },
  };

  var app = window.PhyloApp;

  app.ensureContainer = function () {
    var root = document.getElementById("viewer-root");
    if (!root) {
      throw new Error("Viewer root container was not found.");
    }
    return root;
  };

  app.setStatus = function (text, isError) {
    if (window.__viewerReport) {
      window.__viewerReport(text, isError);
    }
  };

  app.formatValue = function (value) {
    if (value === null || value === undefined || value === "") {
      return "N/A";
    }
    return String(value);
  };

  app.getActiveNode = function () {
    var appState = app.state;
    if (!appState.tree || !appState.activeNodeName) {
      return null;
    }
    return appState.tree.getNodeByName(appState.activeNodeName);
  };
})();
