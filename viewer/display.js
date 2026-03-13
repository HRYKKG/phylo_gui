(function () {
  var app = window.PhyloApp;

  app.captureZoomState = function () {
    var appState = app.state;
    var zoomTransform = null;
    var svgNode = appState.display && appState.display.svg && appState.display.svg.node
      ? appState.display.svg.node()
      : null;

    if (svgNode && svgNode.__zoom && isFinite(svgNode.__zoom.k)) {
      zoomTransform = svgNode.__zoom;
    } else if (appState.display && appState.display.currentZoomTransform && isFinite(appState.display.currentZoomTransform.k)) {
      zoomTransform = appState.display.currentZoomTransform;
    }

    appState.currentZoom = zoomTransform ? zoomTransform.k : 1;
    if (appState.display) {
      appState.display.currentZoomTransform = zoomTransform;
    }
  };

  app.sanitizeRenderedLabels = function () {
    var container = document.getElementById("tree-container");

    if (!container) {
      return;
    }

    container.querySelectorAll("g.internal-node .phylotree-node-text").forEach(function (text) {
      var raw = (text.textContent || "").trim();
      if (/^__/.test(raw)) {
        text.textContent = "";
        text.style.display = "none";
      } else {
        text.style.display = "";
      }
    });
  };

  app.installDisplayBindings = function () {
    var appState = app.state;

    if (!appState.display) {
      throw new Error("Tree display is not initialized.");
    }

    if (appState.display.zoomBehavior && appState.display.zoomBehavior.filter) {
      appState.display.zoomBehavior.filter(function (event) {
        return Boolean(event) && event.type === "wheel";
      });
    }

    appState.display.handle_node_click = function (node, event) {
      if (appState.selectionMode === "rectangle") {
        return;
      }
      if (event && event.stopPropagation) {
        event.stopPropagation();
      }
      appState.activeNodeName = node && node.data ? node.data.name : null;
      app.syncPanels();
      if (node) {
        app.setStatus("Active node: " + app.formatValue(node.data && node.data.name), false);
      } else {
        app.setStatus("Active node cleared.", false);
      }
    };

    appState.display.selectionCallback(function (selectedNodes) {
      appState.selectedLeafNames = (selectedNodes || [])
        .filter(app.isLeaf)
        .map(function (node) {
          return node.data.name;
        });
      app.assignViewerNodeIds();
      appState.selectedBranchNodeIds = app.computeSelectedBranchNodeIds();
      app.syncPanels();
    });

    if (appState.display.svg && appState.display.svg.on) {
      appState.display.svg.on("mousedown.zoom", null);
      appState.display.svg.on("dblclick.zoom", null);
      appState.display.svg.on("touchstart.zoom", null);
      appState.display.svg.on("touchmove.zoom", null);
      appState.display.svg.on("touchend.zoom", null);
      appState.display.svg.on("touchcancel.zoom", null);
      appState.display.svg.on("dragstart.viewer-disable", function (event) {
        event.preventDefault();
      });
      appState.display.svg.on("selectstart.viewer-disable", function (event) {
        event.preventDefault();
      });
      appState.display.svg.on("mousedown.viewer-disable", function (event) {
        if (event.button === 0) {
          event.preventDefault();
        }
      });
      appState.display.svg.on("wheel.viewer-state", function () {
        window.requestAnimationFrame(app.captureZoomState);
      });
    }
  };
})();
