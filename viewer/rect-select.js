(function () {
  var app = window.PhyloApp;

  app.ensureSelectionBox = function () {
    var container = document.getElementById("tree-container");
    var selectionBox = document.getElementById("selection-box");

    if (!container) {
      return null;
    }
    if (!selectionBox) {
      selectionBox = document.createElement("div");
      selectionBox.id = "selection-box";
      selectionBox.className = "selection-box";
      selectionBox.hidden = true;
      container.appendChild(selectionBox);
    }
    return selectionBox;
  };

  app.clearSelectionBox = function () {
    var selectionBox = app.ensureSelectionBox();
    if (selectionBox) {
      selectionBox.hidden = true;
      selectionBox.style.width = "0px";
      selectionBox.style.height = "0px";
    }
    app.state.selectionDrag = null;
  };

  function updateSelectionBox(left, top, width, height) {
    var selectionBox = app.ensureSelectionBox();
    if (!selectionBox) {
      return;
    }
    selectionBox.hidden = false;
    selectionBox.style.left = left + "px";
    selectionBox.style.top = top + "px";
    selectionBox.style.width = width + "px";
    selectionBox.style.height = height + "px";
  }

  function normalizeRect(startX, startY, currentX, currentY) {
    var left = Math.min(startX, currentX);
    var top = Math.min(startY, currentY);
    var width = Math.abs(currentX - startX);
    var height = Math.abs(currentY - startY);

    return {
      left: left,
      top: top,
      width: width,
      height: height,
      right: left + width,
      bottom: top + height,
    };
  }

  function rectsIntersect(a, b) {
    return !(a.right < b.left || a.left > b.right || a.bottom < b.top || a.top > b.bottom);
  }

  function collectLeafNamesInRectangle(viewportRect) {
    var container = document.getElementById("tree-container");
    var groups;
    var selectedNames = [];
    var selectedNodeIds = [];

    if (!container) {
      return { leafNames: selectedNames, internalNodeIds: selectedNodeIds };
    }

    groups = container.querySelectorAll("[data-node-name]");
    groups.forEach(function (group) {
      var groupRect = group.getBoundingClientRect();
      if (rectsIntersect(viewportRect, groupRect)) {
        selectedNames.push(group.getAttribute("data-node-name"));
      }
    });

    container.querySelectorAll("g.internal-node[data-viewer-node-id]").forEach(function (group) {
      var groupRect = group.getBoundingClientRect();
      if (rectsIntersect(viewportRect, groupRect)) {
        selectedNodeIds.push(group.getAttribute("data-viewer-node-id"));
      }
    });

    return { leafNames: selectedNames, internalNodeIds: selectedNodeIds };
  }

  function beginRectangleSelection(event) {
    var appState = app.state;
    var container = document.getElementById("tree-container");
    var bounds;

    if (appState.selectionMode !== "rectangle" || !container || event.button !== 0) {
      return;
    }

    bounds = container.getBoundingClientRect();
    appState.selectionDrag = {
      startX: event.clientX - bounds.left,
      startY: event.clientY - bounds.top,
      currentX: event.clientX - bounds.left,
      currentY: event.clientY - bounds.top,
      bounds: bounds,
    };
    updateSelectionBox(appState.selectionDrag.startX, appState.selectionDrag.startY, 0, 0);
    event.preventDefault();
  }

  function updateRectangleSelection(event) {
    var appState = app.state;
    var rect;

    if (!appState.selectionDrag) {
      return;
    }

    appState.selectionDrag.currentX = event.clientX - appState.selectionDrag.bounds.left;
    appState.selectionDrag.currentY = event.clientY - appState.selectionDrag.bounds.top;
    rect = normalizeRect(
      appState.selectionDrag.startX,
      appState.selectionDrag.startY,
      appState.selectionDrag.currentX,
      appState.selectionDrag.currentY
    );
    updateSelectionBox(rect.left, rect.top, rect.width, rect.height);
    event.preventDefault();
  }

  function finishRectangleSelection(event) {
    var appState = app.state;
    var drag = appState.selectionDrag;
    var localRect;
    var viewportRect;
    var selection;

    if (!drag) {
      return;
    }

    localRect = normalizeRect(drag.startX, drag.startY, drag.currentX, drag.currentY);
    viewportRect = {
      left: drag.bounds.left + localRect.left,
      top: drag.bounds.top + localRect.top,
      right: drag.bounds.left + localRect.right,
      bottom: drag.bounds.top + localRect.bottom,
    };

    app.clearSelectionBox();
    if (localRect.width < 4 && localRect.height < 4) {
      if (event) {
        event.preventDefault();
      }
      return;
    }

    selection = collectLeafNamesInRectangle(viewportRect);
    app.applyLeafSelection(selection.leafNames, "rectangle selection", selection.internalNodeIds);
    if (event) {
      event.preventDefault();
    }
  }

  app.disableTreeCanvasDrag = function () {
    var appState = app.state;
    var container = document.getElementById("tree-container");

    if (!container) {
      return;
    }

    container.ondragstart = function (event) {
      event.preventDefault();
      return false;
    };

    container.onselectstart = function (event) {
      event.preventDefault();
      return false;
    };

    container.onmousedown = function (event) {
      if (event.button !== 0) {
        return;
      }
      event.preventDefault();
    };

    if (!appState.dragBindingsInstalled) {
      container.addEventListener("mousedown", beginRectangleSelection);
      window.addEventListener("mousemove", updateRectangleSelection);
      window.addEventListener("mouseup", finishRectangleSelection);
      appState.dragBindingsInstalled = true;
    }
  };
})();
