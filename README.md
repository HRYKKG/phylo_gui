# Phylogenetic Analysis Pipeline GUI

This project provides a simple GUI-based pipeline for phylogenetic analysis using TkEasyGUI. The pipeline supports the following steps:

- **Sequence Alignment:** Run MAFFT for multiple sequence alignment.
- **Alignment Trimming:** Use TrimAl to remove poorly aligned regions.
- **Phylogenetic Tree Construction:** Execute IQTREE to estimate the phylogenetic tree.
- **Tree Visualization & Post-Processing:** View and post-process the resulting tree using ETE3.

## Environment Setup Using Conda

We recommend using conda/mamba to set up the project environment. The following instructions assume that you have conda installed and that you will create an environment named `phylo_gui`.

### 1. Create an environment

```bash
mamba create -n phylo_gui 
mamba activate phylo_gui
```
### 2. Install Python Dependencies

Install the required Python packages via pip (for TKEasyGUI) and conda/mamba:
```bash
pip install TKEasyGui
mamba install -c conda-forge ete3
```

### 3. Install External Tools via Conda

MAFFT, TrimAl, and IQTREE are available from the Bioconda channel. Install them as follows:

```bash
mamba install -c bioconda mafft trimal iqtree
```
Note: Make sure you have configured conda/mamba to use the bioconda channel. If not, follow the Bioconda installation instructions.

### 4. Download the project
Clone the repository (this will download all files and the dat folder):
```bash
git clone https://github.com/HRYKKG/phylo_gui.git
cd phylo_gui
```
If needed, make the main script executable:
```bash
chmod +x phylo_gui.py
```


## Usage
Run the main script under the proper environment:
```bash
python phylo_gui.py 
```

**A portal window will appear where you can:**
- Load a FASTA file.
- Perform sequence alignment using MAFFT.
- Trim the alignment using TrimAl.
- Construct phylogenetic trees using IQTREE.
- View and post-process the results (e.g., view tree, add gene names, download results).

Each step is handled through separate options and result windows for a clear, step-by-step workflow.


## Citation
Please cite the programs that you executed via this pipeline:
  - MAFFT: https://mafft.cbrc.jp/alignment/software/
  - Trimal: https://vicfero.github.io/trimal/
  - IQTREE: http://www.iqtree.org/

