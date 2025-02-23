# Phylogenetic Analysis Pipeline GUI

This project provides a simple GUI-based pipeline for phylogenetic analysis using TkEasyGUI. The pipeline supports the following steps:

- **Sequence Alignment:** Run MAFFT for multiple sequence alignment.
- **Alignment Trimming:** Use TrimAl to remove poorly aligned regions.
- **Phylogenetic Tree Construction:** Execute IQTREE to estimate the phylogenetic tree.
- **Tree Visualization & Post-Processing:** View and post-process the resulting tree using ETE3.

## Environment Setup Using Conda

We recommend using conda to set up the project environment. The following instructions assume that you have conda installed and that you will create an environment named `phylo_gui`.

### 1. Create and Activate the `phylo_gui` Environment

Open a terminal and run:

```bash
conda create -n phylo_gui 
conda activate phylo_gui
```
### 2. Install Python Dependencies

Install the required Python packages via pip (or conda if available):
```bash
pip install tkeasygui ete3
```

### 3. Install External Tools via Conda

MAFFT, TrimAl, and IQTREE are available from the Bioconda channel. Install them as follows:

```bash
conda install -c bioconda mafft trimal iqtree
```
Note: Make sure you have configured conda to use the bioconda channel. If not, follow the Bioconda installation instructions.

### 4. Downlaod the project
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
Run the main script under ther proper environment:
```bash
python phylo_gui.py 
```

**A portal window will appear where you can:**
- Load a FASTA file.
- Perform sequence alignment using MAFFT.
- Trim the alignment using TrimAl.
- Construct phylogenetic trees using IQTREE.
- View and post-process the results (e.g., view tree, add gene names, download results).

Each step is handled through separate option and result windows for a clear, step-by-step workflow.



