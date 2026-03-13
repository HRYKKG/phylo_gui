(function () {
  var app = window.PhyloApp;

  app.fitTreeToViewport = function (options) {
    var appState = app.state;
    var container = document.getElementById("tree-container");
    var svgSelection;
    var svgNode;
    var treeGroup;
    var bbox;
    var containerWidth;
    var containerHeight;
    var padding;
    var scaleX;
    var scaleY;
    var scale;
    var translateX;
    var translateY;
    var baseTransform;
    var transform;
    var opts = options || {};

    if (!appState.display || !appState.display.svg || !appState.display.zoomBehavior || !container) {
      app.captureZoomState();
      return;
    }

    svgSelection = appState.display.svg;
    svgNode = svgSelection.node ? svgSelection.node() : null;
    treeGroup = svgSelection.select ? svgSelection.select(".phylotree-container") : null;
    if (!svgNode || !treeGroup || !treeGroup.node || !treeGroup.node()) {
      app.captureZoomState();
      return;
    }

    bbox = treeGroup.node().getBBox();
    if (!bbox || !isFinite(bbox.width) || !isFinite(bbox.height) || bbox.width <= 0 || bbox.height <= 0) {
      app.captureZoomState();
      return;
    }

    containerWidth = Math.max(container.clientWidth || 0, 1);
    containerHeight = Math.max(container.clientHeight || 0, 1);
    padding = (appState.renderProfile && appState.renderProfile.fitPadding) || 32;

    scaleX = (containerWidth - padding * 2) / bbox.width;
    scaleY = (containerHeight - padding * 2) / bbox.height;
    scale = Math.min(scaleX, scaleY);
    if (!isFinite(scale) || scale <= 0) {
      app.captureZoomState();
      return;
    }
    if (opts.onlyShrink) {
      scale = Math.min(scale, 1);
    }

    baseTransform = appState.display.baseTransform || { x: 0, y: 0 };
    translateX = padding + (containerWidth - padding * 2 - bbox.width * scale) / 2 - (bbox.x + baseTransform.x) * scale;
    translateY = padding + (containerHeight - padding * 2 - bbox.height * scale) / 2 - (bbox.y + baseTransform.y) * scale;

    if (window.d3 && window.d3.zoomIdentity) {
      transform = window.d3.zoomIdentity.translate(translateX, translateY).scale(scale);
    } else {
      transform = (svgNode && svgNode.__zoom) || appState.display.currentZoomTransform;
      if (!transform || !transform.scale || !transform.translate || !isFinite(transform.k) || transform.k === 0) {
        app.captureZoomState();
        return;
      }
      transform = transform.scale(1 / transform.k).translate(-transform.x, -transform.y).translate(translateX, translateY).scale(scale);
    }
    appState.display.currentZoomTransform = transform;
    svgSelection.call(appState.display.zoomBehavior.transform, transform);
    window.requestAnimationFrame(app.captureZoomState);
  };

  app.bindZoomControls = function () {
    var appState = app.state;
    var zoomInButton = document.getElementById("zoom-in-button");
    var zoomOutButton = document.getElementById("zoom-out-button");
    var fitTreeButton = document.getElementById("fit-tree-button");
    var resetViewButton = document.getElementById("reset-view-button");
    var fontSizeSlider = document.getElementById("font-size-slider");

    if (zoomInButton) {
      zoomInButton.onclick = function () {
        if (appState.display && appState.display.zoomBehavior && appState.display.svg) {
          appState.display.svg.call(appState.display.zoomBehavior.scaleBy, 1.2);
          window.requestAnimationFrame(app.captureZoomState);
        }
      };
    }

    if (zoomOutButton) {
      zoomOutButton.onclick = function () {
        if (appState.display && appState.display.zoomBehavior && appState.display.svg) {
          appState.display.svg.call(appState.display.zoomBehavior.scaleBy, 1 / 1.2);
          window.requestAnimationFrame(app.captureZoomState);
        }
      };
    }

    if (fitTreeButton) {
      fitTreeButton.onclick = function () {
        app.fitTreeToViewport({ onlyShrink: false });
        app.setStatus("Tree fit to viewport.", false);
      };
    }

    if (resetViewButton) {
      resetViewButton.onclick = function () {
        if (appState.display) {
          appState.display.currentZoomTransform = null;
          appState.display.update();
          app.applyRenderProfileToSvg();
          app.fitTreeToViewport({ onlyShrink: true });
          app.setStatus("View reset.", false);
        }
      };
    }

    if (fontSizeSlider) {
      fontSizeSlider.value = String(appState.fontSizePx || 10);
      fontSizeSlider.oninput = function () {
        appState.fontSizePx = parseFloat(fontSizeSlider.value) || 10;
        app.applyRenderProfileToSvg();
        app.syncPanels();
        app.setStatus("Text size adjusted.", false);
      };
    }

    var rectangleToggleButton = document.getElementById("rectangle-select-toggle");
    if (rectangleToggleButton) {
      rectangleToggleButton.onclick = function () {
        var container = document.getElementById("tree-container");
        appState.selectionMode = appState.selectionMode === "rectangle" ? "browse" : "rectangle";
        if (container) {
          container.classList.toggle("is-rectangle-mode", appState.selectionMode === "rectangle");
        }
        app.clearSelectionBox();
        app.syncPanels();
        app.setStatus(
          appState.selectionMode === "rectangle" ? "Rectangle selection mode enabled." : "Browse mode enabled.",
          false
        );
      };
    }
  };
})();
