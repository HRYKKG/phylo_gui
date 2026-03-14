(function () {
  var app = window.PhyloApp;

  app.summarizeInput = function (newick) {
    var summary = document.getElementById("viewer-summary");
    if (summary) {
      summary.textContent = "Newick length: " + newick.length + " characters";
    }
  };

  app.createTree = function (newick) {
    if (!window.phylotree || !window.phylotree.phylotree) {
      throw new Error("phylotree.js did not load correctly.");
    }
    return new window.phylotree.phylotree(newick);
  };

  app.applyRenderProfileToSvg = function () {
    var appState = app.state;
    var container = document.getElementById("tree-container");
    var profile = appState.renderProfile;
    var leafFontSize = appState.fontSizePx || 10;
    var nodeRadius = appState.nodeRadiusPx || (profile && profile.nodeRadius) || 3;
    var internalFontSize;

    if (!container || !profile) {
      return;
    }

    internalFontSize = Math.max(2, Math.round(leafFontSize * (profile.internalFontRatio || 0.85) * 10) / 10);

    container.querySelectorAll("svg text").forEach(function (text) {
      var isInternalLabel = Boolean(text.closest && text.closest("g.internal-node"));
      var targetFontSize = isInternalLabel ? internalFontSize : leafFontSize;
      text.style.fontSize = targetFontSize + "px";
    });

    container.querySelectorAll("g.internal-node circle").forEach(function (circle) {
      circle.setAttribute("r", String(nodeRadius));
    });
  };

  app.renderTree = function (newick) {
    var appState = app.state;
    var data = window.__TREE_VIEWER_DATA__;
    var container = document.getElementById("tree-container");
    var title = document.getElementById("viewer-title");
    var display;
    var svgNode;
    var width;
    var height;

    if (!data || !newick) {
      throw new Error("Viewer data is missing Newick input.");
    }
    if (title) {
      title.textContent = data.title || "Interactive Tree Viewer";
      document.title = title.textContent;
    }

    container.innerHTML = "";
    app.summarizeInput(newick);
    appState.tree = app.createTree(newick);
    appState.renderProfile = app.getRenderProfile();
    appState.fontSizePx = 10;
    appState.nodeRadiusPx = appState.renderProfile.nodeRadius || 3;
    if (appState.tree.internalNames) {
      appState.tree.internalNames(function (node) {
        return Boolean(app.getDisplayLabel(node)) && !app.isLeaf(node);
      });
    }
    if (appState.tree.nodeLabel) {
      appState.tree.nodeLabel(function (node) {
        return app.getDisplayLabel(node);
      });
    }
    width = Math.max(container.clientWidth || 0, 960);
    height = Math.max(container.clientHeight || 0, 640);

    display = appState.tree.render({
      container: "#tree-container",
      width: width,
      height: height,
      selectable: true,
      collapsible: true,
      brush: false,
      zoom: true,
      "internal-names": true,
      "show-menu": false,
      "show-scale": true,
      "left-right-spacing": "fit-to-size",
      "top-bottom-spacing": "fit-to-size",
    });
    display.update();
    svgNode = display.show();
    if (!svgNode) {
      throw new Error("phylotree.js did not return an SVG node.");
    }
    container.appendChild(svgNode);
    app.applyRenderProfileToSvg();
    app.assignViewerNodeIds();
    app.sanitizeRenderedLabels();
    app.ensureSelectionBox();
    app.disableTreeCanvasDrag();

    appState.display = display;
    appState.selectedLeafNames = [];
    appState.boxSelectedNodeIds = [];
    appState.selectedBranchNodeIds = [];
    app.installDisplayBindings();
    app.fitTreeToViewport({ onlyShrink: true });
    app.syncPanels();
    window.__PHYLO_TREE__ = appState.tree;
    app.setStatus("Tree rendered successfully. Right-panel actions are active.", false);
  };

  app.refreshBindingsAfterTreeMutation = function (statusText) {
    var appState = app.state;
    appState.display = appState.tree.display || appState.display;
    appState.boxSelectedNodeIds = [];
    appState.selectedBranchNodeIds = [];
    app.assignViewerNodeIds();
    app.sanitizeRenderedLabels();
    app.applyRenderProfileToSvg();
    app.installDisplayBindings();
    app.captureZoomState();
    app.updateSelectedLeafStateFromDisplay();
    app.syncPanels();
    app.setStatus(statusText, false);
  };
})();
