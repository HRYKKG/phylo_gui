(function () {
  var app = window.PhyloApp;

  app.isLeaf = function (node) {
    return Boolean(node) && (!node.children || node.children.length === 0);
  };

  app.getNodeName = function (node) {
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
  };

  function isSyntheticInternalName(name) {
    return Boolean(name) && /^__/.test(String(name));
  }

  app.getDisplayLabel = function (node) {
    var name = app.getNodeName(node);
    if (!name) {
      return "";
    }
    if (!node.parent && name === "root") {
      return "Midpoint root";
    }
    if (!app.isLeaf(node) && isSyntheticInternalName(name)) {
      return "";
    }
    return name;
  };

  app.getNodeType = function (node) {
    if (!node) {
      return "None";
    }
    if (!node.parent) {
      return "Root";
    }
    return app.isLeaf(node) ? "Leaf" : "Internal";
  };

  app.getLeafCount = function (node) {
    var descendants;
    var count = 0;
    if (!node || !node.descendants) {
      return 0;
    }
    descendants = node.descendants();
    descendants.forEach(function (descendant) {
      if (app.isLeaf(descendant)) {
        count += 1;
      }
    });
    return count;
  };

  app.getLeafNamesUnderNode = function (node) {
    var names = [];

    if (!node || !node.descendants) {
      return names;
    }

    node.descendants().forEach(function (descendant) {
      if (app.isLeaf(descendant) && descendant.data && descendant.data.name !== undefined && descendant.data.name !== null) {
        names.push(String(descendant.data.name));
      }
    });

    return names;
  };

  app.getAllLeafNames = function () {
    var appState = app.state;

    if (!appState.tree || !appState.tree.nodes || !appState.tree.nodes.descendants) {
      return [];
    }

    return app.getLeafNamesUnderNode(appState.tree.nodes);
  };

  app.getRenderProfile = function () {
    return {
      nodeRadius: 3,
      fitPadding: 24,
      internalFontRatio: 0.85,
    };
  };
})();
