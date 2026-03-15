# Phylo_GUI — Phylogenetic Analysis Pipeline GUI

Phylo_GUI provides a desktop GUI for end-to-end phylogenetic analysis. Built with TkEasyGUI, it wraps MAFFT, TrimAl, and IQ-TREE into a single step-by-step workflow and adds an interactive browser-based tree viewer.

## Features

- **Sequence Alignment** — Run MAFFT (`auto` / `linsi` / `ginsi` / `einsi` modes, configurable threads).
- **Alignment Trimming** — Use TrimAl (`automated1` / `gappyout` / `strict` / `strictplus` / `nogaps` modes).
- **Phylogenetic Tree Construction** — Execute IQ-TREE or IQ-TREE 3 with configurable UFboot, SH-aLRT, LBP, aBayes, and substitution model options.
- **Interactive Tree Viewer** — Midpoint-rooted tree opened in a local browser; supports zoom, node collapse, rectangle leaf selection, and sending selections back to the GUI.
- **Leaf Selection → Re-alignment** — Select a subtree or arbitrary leaf set in the viewer and open those sequences directly in the Alignment step.
- **Post-processing utilities** — Add *A. thaliana* gene names to leaf labels, copy / download Newick, download all IQ-TREE output files as a ZIP archive.

The interactive viewer can also be launched as a standalone script:

```bash
python interactive_tree_viewer.py --newick-file path/to/treefile
```

## Environment Setup Using Conda

We recommend using conda/mamba to set up the project environment.

### 1. Create and activate an environment

```bash
mamba create -n phylo_gui
mamba activate phylo_gui
```

### 2. Clone the repository

```bash
git clone https://github.com/HRYKKG/phylo_gui.git
cd phylo_gui
```

### 3. Install Python dependencies

```bash
pip install -r requirement.txt
```

### 4. Install external tools via Conda

MAFFT, TrimAl, and IQ-TREE are available from the Bioconda channel:

```bash
mamba install -c bioconda mafft trimal iqtree
```

> IQ-TREE 3 (`iqtree3`) is also supported and will be used automatically if `iqtree` is not found on `PATH`.

## Usage

```bash
python phylo_gui.py
```

A **Portal** window opens. From there:

1. Paste or load a FASTA file into the text area.
2. Click **Start Pipeline** to proceed through the following stages in order:
   - **Alignment** — configure MAFFT options and run, or skip.
   - **Trim** — configure TrimAl options and run, or skip.
   - **IQ-TREE** — configure analysis options and run.
3. After IQ-TREE completes, the **Result** window shows the Newick tree. From here you can:
   - **View Tree** — opens an interactive browser viewer with zoom, collapse, and leaf selection.
   - **Add Atha gene names** — annotate *A. thaliana* AGI codes with gene names.
   - **Download Newick / Download all files** — save results locally.
4. In the tree viewer, select leaves and click **Send to GUI** to open those sequences in a new Alignment step.

Each stage window also provides **Back** buttons to return to a previous step without losing context.

## Citation

Please cite the programs that you executed via this pipeline:

- MAFFT: https://mafft.cbrc.jp/alignment/software/
- TrimAl: https://vicfero.github.io/trimal/
- IQ-TREE: http://www.iqtree.org/

## Third-Party Browser Assets

The interactive viewer bundles the following upstream libraries in `vendor/`:

| Library | License |
|---|---|
| `phylotree.js` | MIT |
| `underscore` | MIT |
| `lodash` | MIT |

Each vendored dependency includes its upstream license text at `vendor/*/LICENSE`.
