(function () {
  var app = window.PhyloApp;

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

  app.computeSelectedBranchNodeIds = function () {
    var appState = app.state;
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
  };

  app.assignViewerNodeIds = function () {
    var appState = app.state;
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
  };

  app.applyLeafSelection = function (names, sourceLabel, boxSelectedNodeIds) {
    var appState = app.state;
    if (!appState.display) {
      return;
    }
    appState.boxSelectedNodeIds = boxSelectedNodeIds || [];
    appState._suppressSelectionCallback = true;
    appState.display.clearSelection();
    if (names.length > 0) {
      appState.display.selectNodes(names);
    }
    appState._suppressSelectionCallback = false;
    appState.selectedLeafNames = names.slice();
    app.assignViewerNodeIds();
    appState.selectedBranchNodeIds = app.computeSelectedBranchNodeIds();
    app.syncPanels();
    app.setStatus(names.length + " leaves selected" + (sourceLabel ? " via " + sourceLabel : "") + ".", false);
  };

  app.updateSelectedLeafStateFromDisplay = function () {
    var appState = app.state;
    var selection = appState.display && appState.display.getSelection ? appState.display.getSelection() : [];
    appState.selectedLeafNames = selection
      .filter(app.isLeaf)
      .map(function (node) {
        return node.data.name;
      });
    app.assignViewerNodeIds();
    appState.selectedBranchNodeIds = app.computeSelectedBranchNodeIds();
    app.syncPanels();
  };
})();
