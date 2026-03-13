(function () {
  var app = window.PhyloApp;

  app.bindNodeActions = function () {
    var appState = app.state;
    var toggleCollapseButton = document.getElementById("toggle-collapse-button");
    var selectDescendantsButton = document.getElementById("select-descendants-button");
    var clearActiveNodeButton = document.getElementById("clear-active-node-button");
    var clearSelectedLeavesButton = document.getElementById("clear-selected-leaves-button");
    var copySelectedLeavesButton = document.getElementById("copy-selected-leaves-button");
    var saveSelectionJsonButton = document.getElementById("save-selection-json-button");

    if (toggleCollapseButton) {
      toggleCollapseButton.onclick = function () {
        var activeNode = app.getActiveNode();
        var action;
        if (!activeNode || app.isLeaf(activeNode) || !appState.display) {
          return;
        }
        action = activeNode.collapsed ? "expanded" : "collapsed";
        appState.display.toggleCollapse(activeNode).update();
        app.refreshBindingsAfterTreeMutation(
          "Subtree " + action + " for " + app.formatValue(activeNode.data && activeNode.data.name) + "."
        );
      };
    }

    if (selectDescendantsButton) {
      selectDescendantsButton.onclick = function () {
        var activeNode = app.getActiveNode();
        var leafNames;
        if (!activeNode || app.isLeaf(activeNode) || !appState.display) {
          return;
        }
        leafNames = appState.display.selectAllDescendants(activeNode, true, false).map(function (node) {
          return node.data.name;
        });
        app.applyLeafSelection(leafNames, "active node descendants", []);
      };
    }

    if (clearActiveNodeButton) {
      clearActiveNodeButton.onclick = function () {
        appState.activeNodeName = null;
        app.syncPanels();
        app.setStatus("Active node cleared.", false);
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
        app.syncPanels();
        app.setStatus("Selected leaves cleared.", false);
      };
    }

    if (copySelectedLeavesButton) {
      copySelectedLeavesButton.onclick = function () {
        if (!navigator.clipboard || appState.selectedLeafNames.length === 0) {
          return;
        }
        navigator.clipboard.writeText(appState.selectedLeafNames.slice().sort().join("\n")).then(function () {
          app.setStatus("Selected leaf names copied to clipboard.", false);
        }).catch(function (error) {
          app.setStatus("Failed to copy leaf names: " + error, true);
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
        }).then(function () {
          app.setStatus("Selection sent to GUI.", false);
        }).catch(function (error) {
          app.setStatus("Failed to send selection to GUI: " + error, true);
        });
      };
    }
  };
})();
