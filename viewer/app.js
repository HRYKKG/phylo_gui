(function () {
  var appState = {
    tree: null,
    display: null,
    renderProfile: null,
    fontSizePx: 10,
    activeNodeName: null,
    selectedLeafNames: [],
    boxSelectedNodeIds: [],
    selectedBranchNodeIds: [],
    currentZoom: 1,
    selectionMode: "browse",
    selectionDrag: null,
    dragBindingsInstalled: false,
  };

  function ensureContainer() {
    var root = document.getElementById("viewer-root");
    if (!root) {
      throw new Error("Viewer root container was not found.");
    }
    return root;
  }

  function setStatus(text, isError) {
    if (window.__viewerReport) {
      window.__viewerReport(text, isError);
    }
  }

  function formatValue(value) {
    if (value === null || value === undefined || value === "") {
      return "N/A";
    }
    return String(value);
  }

  function isLeaf(node) {
    return Boolean(node) && (!node.children || node.children.length === 0);
  }

  function getNodeName(node) {
    if (!node) {
      return "";
    }
    if (node.data && node.data.name !== undefined && node.data.name !== null) {
      return String(node.data.name);
    }
    if (node.name !== undefined && node.name !== null) {
      return String(node.name);
    }
    return "";
  }

  function isSyntheticInternalName(name) {
    return Boolean(name) && /^__/.test(String(name));
  }

  function getDisplayLabel(node) {
    var name = getNodeName(node);

    if (!name) {
      return "";
    }
    if (!isLeaf(node) && isSyntheticInternalName(name)) {
      return "";
    }
    return name;
  }

  function getNodeType(node) {
    if (!node) {
      return "None";
    }
    if (!node.parent) {
      return "Root";
    }
    return isLeaf(node) ? "Leaf" : "Internal";
  }

  function getLeafCount(node) {
    var descendants;
    var count = 0;
    if (!node || !node.descendants) {
      return 0;
    }
    descendants = node.descendants();
    descendants.forEach(function (descendant) {
      if (isLeaf(descendant)) {
        count += 1;
      }
    });
    return count;
  }

  function getRenderProfile(tree) {
    return {
      nodeRadius: 3,
      fitPadding: 24,
      internalFontRatio: 0.85,
    };
  }

  function getActiveNode() {
    if (!appState.tree || !appState.activeNodeName) {
      return null;
    }
    return appState.tree.getNodeByName(appState.activeNodeName);
  }

  function findPairwiseMRCA(leftNode, rightNode) {
    var ancestors = new Set();
    var cursor = leftNode;

    while (cursor) {
      ancestors.add(cursor);
      cursor = cursor.parent;
    }

    cursor = rightNode;
    while (cursor) {
      if (ancestors.has(cursor)) {
        return cursor;
      }
      cursor = cursor.parent;
    }

    return null;
  }

  function computeSelectedBranchNodeIds() {
    var selectedNodes;
    var mrca;
    var branchNodeIds = new Set();

    if (!appState.tree || appState.selectedLeafNames.length === 0) {
      return [];
    }

    selectedNodes = appState.selectedLeafNames
      .map(function (name) {
        return appState.tree.getNodeByName(name);
      })
      .filter(Boolean);

    if (selectedNodes.length === 0) {
      return [];
    }

    mrca = selectedNodes[0];
    selectedNodes.slice(1).forEach(function (node) {
      mrca = findPairwiseMRCA(mrca, node) || mrca;
    });

    selectedNodes.forEach(function (node) {
      var cursor = node;
      while (cursor && cursor !== mrca) {
        if (cursor._viewerNodeId) {
          branchNodeIds.add(cursor._viewerNodeId);
        }
        cursor = cursor.parent;
      }
    });

    appState.boxSelectedNodeIds.forEach(function (nodeId) {
      branchNodeIds.add(nodeId);
    });

    return Array.from(branchNodeIds);
  }

  function getSelectionModeNote() {
    if (appState.selectionMode === "rectangle") {
      return "Rectangle mode: drag across leaves to select them.";
    }
    return "Browse mode: click nodes to inspect them.";
  }

  function summarizeInput(newick) {
    var summary = document.getElementById("viewer-summary");
    if (summary) {
      summary.textContent = "Newick length: " + newick.length + " characters";
    }
  }

  function createTree(newick) {
    if (!window.phylotree || !window.phylotree.phylotree) {
      throw new Error("phylotree.js did not load correctly.");
    }
    return new window.phylotree.phylotree(newick);
  }

  function syncSelectedNodePanel() {
    var node = getActiveNode();
    var card = document.getElementById("selected-node-card");
    var empty = document.getElementById("selected-node-empty");
    var details = document.getElementById("selected-node-details");
    var branchLength = node && appState.tree && appState.tree.branch_length_accessor ? appState.tree.branch_length_accessor(node) : null;
    var childCount = node && node.children ? node.children.length : 0;

    if (!card || !empty || !details) {
      return;
    }

    if (!node) {
      card.classList.add("is-empty");
      empty.hidden = false;
      details.hidden = true;
      return;
    }

    card.classList.remove("is-empty");
    empty.hidden = true;
    details.hidden = false;
    document.getElementById("selected-node-name").textContent = formatValue(node.data && node.data.name);
    document.getElementById("selected-node-type").textContent = getNodeType(node);
    document.getElementById("selected-node-branch-length").textContent = formatValue(branchLength);
    document.getElementById("selected-node-depth").textContent = formatValue(node.depth);
    document.getElementById("selected-node-children").textContent = formatValue(childCount);
    document.getElementById("selected-node-leaf-count").textContent = formatValue(getLeafCount(node));
  }

  function syncActionButtons() {
    var activeNode = getActiveNode();
    var toggleCollapseButton = document.getElementById("toggle-collapse-button");
    var selectDescendantsButton = document.getElementById("select-descendants-button");
    var clearActiveNodeButton = document.getElementById("clear-active-node-button");
    var clearSelectedLeavesButton = document.getElementById("clear-selected-leaves-button");
    var copySelectedLeavesButton = document.getElementById("copy-selected-leaves-button");
    var saveSelectionJsonButton = document.getElementById("save-selection-json-button");
    var rectangleToggleButton = document.getElementById("rectangle-select-toggle");

    if (toggleCollapseButton) {
      toggleCollapseButton.disabled = !activeNode || isLeaf(activeNode);
      toggleCollapseButton.textContent = activeNode && activeNode.collapsed ? "Expand Subtree" : "Collapse Subtree";
    }
    if (selectDescendantsButton) {
      selectDescendantsButton.disabled = !activeNode || isLeaf(activeNode);
    }
    if (clearActiveNodeButton) {
      clearActiveNodeButton.disabled = !activeNode;
    }
    if (clearSelectedLeavesButton) {
      clearSelectedLeavesButton.disabled = appState.selectedLeafNames.length === 0;
    }
    if (copySelectedLeavesButton) {
      copySelectedLeavesButton.disabled = appState.selectedLeafNames.length === 0;
    }
    if (saveSelectionJsonButton) {
      saveSelectionJsonButton.disabled = !(
        window.__TREE_VIEWER_DATA__ &&
        window.__TREE_VIEWER_DATA__.selectionApiUrl &&
        appState.selectedLeafNames.length > 0
      );
    }
    if (rectangleToggleButton) {
      rectangleToggleButton.textContent = appState.selectionMode === "rectangle" ? "Rectangle Select: On" : "Rectangle Select: Off";
      rectangleToggleButton.classList.toggle("is-active", appState.selectionMode === "rectangle");
    }
  }

  function syncSelectedLeavesPanel() {
    var card = document.getElementById("selected-leaves-card");
    var summary = document.getElementById("selected-leaves-summary");
    var list = document.getElementById("selected-leaf-list");
    var sortedLeafNames;

    if (!card || !summary || !list) {
      return;
    }

    list.innerHTML = "";
    if (appState.selectedLeafNames.length === 0) {
      card.classList.add("is-empty");
      summary.textContent = "No leaves selected.";
      list.hidden = true;
      return;
    }

    sortedLeafNames = appState.selectedLeafNames.slice().sort();
    card.classList.remove("is-empty");
    summary.textContent = sortedLeafNames.length + " leaves selected.";
    sortedLeafNames.forEach(function (name) {
      var item = document.createElement("li");
      item.textContent = name;
      list.appendChild(item);
    });
    list.hidden = false;
  }

  function syncLeafHighlightClasses() {
    var container = document.getElementById("tree-container");
    var selected = new Set(appState.selectedLeafNames);
    var boxSelected = new Set(appState.boxSelectedNodeIds);
    var selectedBranches = new Set(appState.selectedBranchNodeIds);
    var activeNode = getActiveNode();
    var activeNodeId = activeNode && activeNode._viewerNodeId ? activeNode._viewerNodeId : null;

    assignViewerNodeIds();
    if (!container) {
      return;
    }

    container.querySelectorAll("[data-node-name]").forEach(function (group) {
      var nodeName = group.getAttribute("data-node-name");
      group.classList.toggle("is-leaf-selected", selected.has(nodeName));
    });
    container.querySelectorAll("[data-viewer-node-id]").forEach(function (group) {
      var nodeId = group.getAttribute("data-viewer-node-id");
      group.classList.toggle("is-box-selected-node", boxSelected.has(nodeId));
      group.classList.toggle("is-active-node", activeNodeId === nodeId);
    });
    container.querySelectorAll("path.branch[data-viewer-target-node-id]").forEach(function (path) {
      var nodeId = path.getAttribute("data-viewer-target-node-id");
      path.classList.toggle("is-box-selected-branch", selectedBranches.has(nodeId));
      path.classList.toggle("is-active-node-branch", activeNodeId === nodeId);
    });
    sanitizeRenderedLabels();
  }

  function syncPanels() {
    var modeNote = document.getElementById("selection-mode-note");
    var fontIndicator = document.getElementById("font-size-indicator");

    syncSelectedNodePanel();
    syncActionButtons();
    syncSelectedLeavesPanel();
    syncLeafHighlightClasses();
    if (fontIndicator) {
      fontIndicator.textContent = "Text " + (appState.fontSizePx || 10) + "px";
    }
    if (modeNote) {
      modeNote.textContent = getSelectionModeNote();
    }
  }

  function captureZoomState() {
    var zoomTransform = null;
    var svgNode = appState.display && appState.display.svg && appState.display.svg.node ? appState.display.svg.node() : null;

    if (svgNode && svgNode.__zoom && isFinite(svgNode.__zoom.k)) {
      zoomTransform = svgNode.__zoom;
    } else if (appState.display && appState.display.currentZoomTransform && isFinite(appState.display.currentZoomTransform.k)) {
      zoomTransform = appState.display.currentZoomTransform;
    }

    appState.currentZoom = zoomTransform ? zoomTransform.k : 1;
    if (appState.display) {
      appState.display.currentZoomTransform = zoomTransform;
    }
  }

  function applyRenderProfileToSvg() {
    var container = document.getElementById("tree-container");
    var profile = appState.renderProfile;
    var leafFontSize = appState.fontSizePx || 10;
    var internalFontSize;

    if (!container || !profile) {
      return;
    }

    internalFontSize = Math.max(6, Math.round(leafFontSize * (profile.internalFontRatio || 0.85) * 10) / 10);

    container.querySelectorAll("svg text").forEach(function (text) {
      var isInternalLabel = Boolean(text.closest && text.closest("g.internal-node"));
      var targetFontSize = isInternalLabel ? internalFontSize : leafFontSize;

      text.style.fontSize = targetFontSize + "px";
    });

    container.querySelectorAll("g.internal-node circle").forEach(function (circle) {
      circle.setAttribute("r", String(profile.nodeRadius));
    });
  }

  function updateSelectedLeafStateFromDisplay() {
    var selection = appState.display && appState.display.getSelection ? appState.display.getSelection() : [];
    appState.selectedLeafNames = selection
      .filter(isLeaf)
      .map(function (node) {
        return node.data.name;
      });
    assignViewerNodeIds();
    appState.selectedBranchNodeIds = computeSelectedBranchNodeIds();
    syncPanels();
  }

  function clearSelectionBox() {
    var selectionBox = ensureSelectionBox();
    if (selectionBox) {
      selectionBox.hidden = true;
      selectionBox.style.width = "0px";
      selectionBox.style.height = "0px";
    }
    appState.selectionDrag = null;
  }

  function updateSelectionBox(left, top, width, height) {
    var selectionBox = ensureSelectionBox();
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

  function ensureSelectionBox() {
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
  }

  function sanitizeRenderedLabels() {
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
  }

  function collectLeafNamesInRectangle(viewportRect) {
    var container = document.getElementById("tree-container");
    var groups;
    var selectedNames = [];
    var selectedNodeIds = [];

    if (!container) {
      return {
        leafNames: selectedNames,
        internalNodeIds: selectedNodeIds,
      };
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

    return {
      leafNames: selectedNames,
      internalNodeIds: selectedNodeIds,
    };
  }

  function applyLeafSelection(names, sourceLabel, boxSelectedNodeIds) {
    if (!appState.display) {
      return;
    }
    appState.boxSelectedNodeIds = boxSelectedNodeIds || [];
    appState.display.clearSelection();
    if (names.length > 0) {
      appState.display.selectNodes(names);
    }
    assignViewerNodeIds();
    appState.selectedBranchNodeIds = computeSelectedBranchNodeIds();
    syncPanels();
    setStatus(names.length + " leaves selected" + (sourceLabel ? " via " + sourceLabel : "") + ".", false);
  }

  function assignViewerNodeIds() {
    var container = document.getElementById("tree-container");

    if (!container || !appState.tree || !appState.tree.nodes || !appState.tree.nodes.descendants) {
      return;
    }

    appState.tree.nodes.descendants().forEach(function (node, index) {
      node._viewerNodeId = String(index);
    });

    container.querySelectorAll("g.node, g.internal-node").forEach(function (group) {
      var node = group.__data__;
      if (node && node._viewerNodeId) {
        group.setAttribute("data-viewer-node-id", node._viewerNodeId);
      }
    });

    container.querySelectorAll("path.branch").forEach(function (path) {
      var edge = path.__data__;
      if (edge && edge.target && edge.target._viewerNodeId) {
        path.setAttribute("data-viewer-target-node-id", edge.target._viewerNodeId);
      }
    });
  }

  function beginRectangleSelection(event) {
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

    clearSelectionBox();
    if (localRect.width < 4 && localRect.height < 4) {
      if (event) {
        event.preventDefault();
      }
      return;
    }

    selection = collectLeafNamesInRectangle(viewportRect);
    applyLeafSelection(selection.leafNames, "rectangle selection", selection.internalNodeIds);
    if (event) {
      event.preventDefault();
    }
  }

  function disableTreeCanvasDrag() {
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
  }

  function installDisplayBindings() {
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
      syncPanels();
      if (node) {
        setStatus("Active node: " + formatValue(node.data && node.data.name), false);
      } else {
        setStatus("Active node cleared.", false);
      }
    };

    appState.display.selectionCallback(function (selectedNodes) {
      appState.selectedLeafNames = (selectedNodes || [])
        .filter(isLeaf)
        .map(function (node) {
          return node.data.name;
        });
      assignViewerNodeIds();
      appState.selectedBranchNodeIds = computeSelectedBranchNodeIds();
      syncPanels();
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
        window.requestAnimationFrame(captureZoomState);
      });
    }
  }

  function renderTree(newick) {
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
    summarizeInput(newick);
    appState.tree = createTree(newick);
    appState.renderProfile = getRenderProfile(appState.tree);
    appState.fontSizePx = 10;
    if (appState.tree.internalNames) {
      appState.tree.internalNames(function (node) {
        return Boolean(getDisplayLabel(node)) && !isLeaf(node);
      });
    }
    if (appState.tree.nodeLabel) {
      appState.tree.nodeLabel(function (node) {
        return getDisplayLabel(node);
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
    applyRenderProfileToSvg();
    assignViewerNodeIds();
    sanitizeRenderedLabels();
    ensureSelectionBox();
    disableTreeCanvasDrag();

    appState.display = display;
    appState.selectedLeafNames = [];
    appState.boxSelectedNodeIds = [];
    appState.selectedBranchNodeIds = [];
    installDisplayBindings();
    fitTreeToViewport({ onlyShrink: true });
    syncPanels();
    window.__PHYLO_TREE__ = appState.tree;
    setStatus("Tree rendered successfully. Right-panel actions are active.", false);
  }

  function refreshBindingsAfterTreeMutation(statusText) {
    appState.display = appState.tree.display || appState.display;
    appState.boxSelectedNodeIds = [];
    appState.selectedBranchNodeIds = [];
    assignViewerNodeIds();
    sanitizeRenderedLabels();
    applyRenderProfileToSvg();
    installDisplayBindings();
    captureZoomState();
    updateSelectedLeafStateFromDisplay();
    syncPanels();
    setStatus(statusText, false);
  }

  function bindZoomControls() {
    var zoomInButton = document.getElementById("zoom-in-button");
    var zoomOutButton = document.getElementById("zoom-out-button");
    var fitTreeButton = document.getElementById("fit-tree-button");
    var resetViewButton = document.getElementById("reset-view-button");
    var fontSizeSlider = document.getElementById("font-size-slider");

    if (zoomInButton) {
      zoomInButton.onclick = function () {
        if (appState.display && appState.display.zoomBehavior && appState.display.svg) {
          appState.display.svg.call(appState.display.zoomBehavior.scaleBy, 1.2);
          window.requestAnimationFrame(captureZoomState);
        }
      };
    }

    if (zoomOutButton) {
      zoomOutButton.onclick = function () {
        if (appState.display && appState.display.zoomBehavior && appState.display.svg) {
          appState.display.svg.call(appState.display.zoomBehavior.scaleBy, 1 / 1.2);
          window.requestAnimationFrame(captureZoomState);
        }
      };
    }

    if (fitTreeButton) {
      fitTreeButton.onclick = function () {
        fitTreeToViewport({ onlyShrink: false });
        setStatus("Tree fit to viewport.", false);
      };
    }

    if (resetViewButton) {
      resetViewButton.onclick = function () {
        if (appState.display) {
          appState.display.currentZoomTransform = null;
          appState.display.update();
          applyRenderProfileToSvg();
          fitTreeToViewport({ onlyShrink: true });
          setStatus("View reset.", false);
        }
      };
    }

    if (fontSizeSlider) {
      fontSizeSlider.value = String(appState.fontSizePx || 10);
      fontSizeSlider.oninput = function () {
        appState.fontSizePx = parseFloat(fontSizeSlider.value) || 10;
        applyRenderProfileToSvg();
        syncPanels();
        setStatus("Text size adjusted.", false);
      };
    }

    if (document.getElementById("rectangle-select-toggle")) {
      document.getElementById("rectangle-select-toggle").onclick = function () {
        var container = document.getElementById("tree-container");
        appState.selectionMode = appState.selectionMode === "rectangle" ? "browse" : "rectangle";
        if (container) {
          container.classList.toggle("is-rectangle-mode", appState.selectionMode === "rectangle");
        }
        clearSelectionBox();
        syncPanels();
        setStatus(appState.selectionMode === "rectangle" ? "Rectangle selection mode enabled." : "Browse mode enabled.", false);
      };
    }
  }

  function fitTreeToViewport(options) {
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
      captureZoomState();
      return;
    }

    svgSelection = appState.display.svg;
    svgNode = svgSelection.node ? svgSelection.node() : null;
    treeGroup = svgSelection.select ? svgSelection.select(".phylotree-container") : null;
    if (!svgNode || !treeGroup || !treeGroup.node || !treeGroup.node()) {
      captureZoomState();
      return;
    }

    bbox = treeGroup.node().getBBox();
    if (!bbox || !isFinite(bbox.width) || !isFinite(bbox.height) || bbox.width <= 0 || bbox.height <= 0) {
      captureZoomState();
      return;
    }

    containerWidth = Math.max(container.clientWidth || 0, 1);
    containerHeight = Math.max(container.clientHeight || 0, 1);
    padding = (appState.renderProfile && appState.renderProfile.fitPadding) || 32;

    scaleX = (containerWidth - padding * 2) / bbox.width;
    scaleY = (containerHeight - padding * 2) / bbox.height;
    scale = Math.min(scaleX, scaleY);
    if (!isFinite(scale) || scale <= 0) {
      captureZoomState();
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
        captureZoomState();
        return;
      }
      transform = transform.scale(1 / transform.k).translate(-transform.x, -transform.y).translate(translateX, translateY).scale(scale);
    }
    appState.display.currentZoomTransform = transform;
    svgSelection.call(appState.display.zoomBehavior.transform, transform);
    window.requestAnimationFrame(captureZoomState);
  }

  function bindNodeActions() {
    var toggleCollapseButton = document.getElementById("toggle-collapse-button");
    var selectDescendantsButton = document.getElementById("select-descendants-button");
    var clearActiveNodeButton = document.getElementById("clear-active-node-button");
    var clearSelectedLeavesButton = document.getElementById("clear-selected-leaves-button");
    var copySelectedLeavesButton = document.getElementById("copy-selected-leaves-button");
    var saveSelectionJsonButton = document.getElementById("save-selection-json-button");

    if (toggleCollapseButton) {
      toggleCollapseButton.onclick = function () {
        var activeNode = getActiveNode();
        var action;
        if (!activeNode || isLeaf(activeNode) || !appState.display) {
          return;
        }
        action = activeNode.collapsed ? "expanded" : "collapsed";
        appState.display.toggleCollapse(activeNode).update();
        syncPanels();
        setStatus("Subtree " + action + " for " + formatValue(activeNode.data && activeNode.data.name) + ".", false);
      };
    }

    if (selectDescendantsButton) {
      selectDescendantsButton.onclick = function () {
        var activeNode = getActiveNode();
        var leafNames;
        if (!activeNode || isLeaf(activeNode) || !appState.display) {
          return;
        }
        leafNames = appState.display.selectAllDescendants(activeNode, true, false).map(function (node) {
          return node.data.name;
        });
        applyLeafSelection(leafNames, "active node descendants", []);
      };
    }

    if (clearActiveNodeButton) {
      clearActiveNodeButton.onclick = function () {
        appState.activeNodeName = null;
        syncPanels();
        setStatus("Active node cleared.", false);
      };
    }

    if (clearSelectedLeavesButton) {
      clearSelectedLeavesButton.onclick = function () {
        if (appState.display) {
          appState.display.clearSelection();
        }
        appState.selectedLeafNames = [];
        appState.boxSelectedNodeIds = [];
        appState.selectedBranchNodeIds = [];
        syncPanels();
        setStatus("Selected leaves cleared.", false);
      };
    }

    if (copySelectedLeavesButton) {
      copySelectedLeavesButton.onclick = function () {
        if (!navigator.clipboard || appState.selectedLeafNames.length === 0) {
          return;
        }
        navigator.clipboard.writeText(appState.selectedLeafNames.slice().sort().join("\n")).then(function () {
          setStatus("Selected leaf names copied to clipboard.", false);
        }).catch(function (error) {
          setStatus("Failed to copy leaf names: " + error, true);
        });
      };
    }

    if (saveSelectionJsonButton) {
      saveSelectionJsonButton.onclick = function () {
        var viewerData = window.__TREE_VIEWER_DATA__ || {};
        var payload;

        if (!viewerData.selectionApiUrl || appState.selectedLeafNames.length === 0) {
          return;
        }

        payload = {
          selected_leaf_names: appState.selectedLeafNames.slice().sort(),
          selected_count: appState.selectedLeafNames.length,
          exported_at: new Date().toISOString(),
          title: viewerData.title || "Phylo GUI Tree Viewer",
        };

        fetch(viewerData.selectionApiUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        }).then(function (response) {
          if (!response.ok) {
            throw new Error("HTTP " + response.status);
          }
          return response.json();
        }).then(function (result) {
          setStatus("Selection sent to GUI.", false);
        }).catch(function (error) {
          setStatus("Failed to send selection to GUI: " + error, true);
        });
      };
    }
  }

  function init() {
    ensureContainer();
    bindZoomControls();
    bindNodeActions();
    try {
      setStatus("Rendering tree...", false);
      renderTree(window.__TREE_VIEWER_DATA__ && window.__TREE_VIEWER_DATA__.newick);
    } catch (error) {
      setStatus(error.message, true);
      throw error;
    }
  }

  window.addEventListener("DOMContentLoaded", init);
})();
