(function () {
  var app = window.PhyloApp;

  function getSelectionModeNote() {
    if (app.state.selectionMode === "rectangle") {
      return "Rectangle mode: drag across leaves to select them.";
    }
    return "Browse mode: click nodes to inspect them.";
  }

  app.syncSelectedNodePanel = function () {
    var appState = app.state;
    var node = app.getActiveNode();
    var card = document.getElementById("selected-node-card");
    var empty = document.getElementById("selected-node-empty");
    var details = document.getElementById("selected-node-details");
    var branchLength = node && appState.tree && appState.tree.branch_length_accessor
      ? appState.tree.branch_length_accessor(node)
      : null;
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
    document.getElementById("selected-node-name").textContent = app.formatValue(node.data && node.data.name);
    document.getElementById("selected-node-type").textContent = app.getNodeType(node);
    document.getElementById("selected-node-branch-length").textContent = app.formatValue(branchLength);
    document.getElementById("selected-node-depth").textContent = app.formatValue(node.depth);
    document.getElementById("selected-node-children").textContent = app.formatValue(childCount);
    document.getElementById("selected-node-leaf-count").textContent = app.formatValue(app.getLeafCount(node));
  };

  app.syncActionButtons = function () {
    var appState = app.state;
    var activeNode = app.getActiveNode();
    var toggleCollapseButton = document.getElementById("toggle-collapse-button");
    var selectDescendantsButton = document.getElementById("select-descendants-button");
    var clearActiveNodeButton = document.getElementById("clear-active-node-button");
    var clearSelectedLeavesButton = document.getElementById("clear-selected-leaves-button");
    var copySelectedLeavesButton = document.getElementById("copy-selected-leaves-button");
    var saveSelectionJsonButton = document.getElementById("save-selection-json-button");
    var rectangleToggleButton = document.getElementById("rectangle-select-toggle");

    if (toggleCollapseButton) {
      toggleCollapseButton.disabled = !activeNode || app.isLeaf(activeNode);
      toggleCollapseButton.textContent = activeNode && activeNode.collapsed ? "Expand Subtree" : "Collapse Subtree";
    }
    if (selectDescendantsButton) {
      selectDescendantsButton.disabled = !activeNode || app.isLeaf(activeNode);
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
      rectangleToggleButton.textContent =
        appState.selectionMode === "rectangle" ? "Rectangle Select: On" : "Rectangle Select: Off";
      rectangleToggleButton.classList.toggle("is-active", appState.selectionMode === "rectangle");
    }
  };

  app.syncSelectedLeavesPanel = function () {
    var appState = app.state;
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
  };

  app.syncLeafHighlightClasses = function () {
    var appState = app.state;
    var container = document.getElementById("tree-container");
    var selected = new Set(appState.selectedLeafNames);
    var boxSelected = new Set(appState.boxSelectedNodeIds);
    var selectedBranches = new Set(appState.selectedBranchNodeIds);
    var activeNode = app.getActiveNode();
    var activeNodeId = activeNode && activeNode._viewerNodeId ? activeNode._viewerNodeId : null;

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
  };

  app.syncPanels = function () {
    var appState = app.state;
    var modeNote = document.getElementById("selection-mode-note");
    var fontIndicator = document.getElementById("font-size-indicator");

    app.syncSelectedNodePanel();
    app.syncActionButtons();
    app.syncSelectedLeavesPanel();
    app.syncLeafHighlightClasses();
    if (fontIndicator) {
      fontIndicator.textContent = "Text " + (appState.fontSizePx || 10) + "px";
    }
    if (modeNote) {
      modeNote.textContent = getSelectionModeNote();
    }
  };
})();
