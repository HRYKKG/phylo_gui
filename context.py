from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SequenceRecord:
    seq_id: str
    header: str
    sequence: str
    description: str = ""


@dataclass
class TreeSelection:
    node_id: str | None = None
    leaf_ids: list[str] = field(default_factory=list)


@dataclass
class AnalysisContext:
    original_fasta_text: str = ""
    original_records: list[SequenceRecord] = field(default_factory=list)
    last_open_dir: Path | None = None

    alignment_output_text: str | None = None
    trim_output_text: str | None = None

    iqtree_output_dir: Path | None = None
    iqtree_prefix: str | None = None
    treefile_path: Path | None = None
    iqtree_report_path: Path | None = None
    tree_newick_text: str | None = None

    leaf_label_map: dict[str, str] = field(default_factory=dict)
    current_selection: TreeSelection = field(default_factory=TreeSelection)

    def clear_iqtree_outputs(self):
        self.iqtree_output_dir = None
        self.iqtree_prefix = None
        self.treefile_path = None
        self.iqtree_report_path = None
        self.tree_newick_text = None
        self.leaf_label_map.clear()
        self.current_selection = TreeSelection()

    def clear_trim_outputs(self):
        self.trim_output_text = None
        self.clear_iqtree_outputs()

    def clear_alignment_outputs(self):
        self.alignment_output_text = None
        self.clear_trim_outputs()

    def set_original_input(self, fasta_text: str, records: list[SequenceRecord]):
        self.original_fasta_text = fasta_text
        self.original_records = list(records)
        self.clear_alignment_outputs()

    def set_alignment_output(self, fasta_text: str):
        self.alignment_output_text = fasta_text
        self.clear_trim_outputs()

    def set_trim_output(self, fasta_text: str):
        self.trim_output_text = fasta_text
        self.clear_iqtree_outputs()

    def set_iqtree_output(
        self,
        *,
        output_dir: str,
        prefix: str,
        treefile_path: str,
        report_path: str | None,
        newick_text: str,
    ):
        self.iqtree_output_dir = Path(output_dir)
        self.iqtree_prefix = prefix
        self.treefile_path = Path(treefile_path)
        self.iqtree_report_path = Path(report_path) if report_path else None
        self.tree_newick_text = newick_text
        self.leaf_label_map.clear()
        self.current_selection = TreeSelection()

    def get_alignment_input_text(self) -> str:
        return self.original_fasta_text

    def get_trim_input_text(self) -> str:
        return self.alignment_output_text or self.original_fasta_text

    def get_iqtree_input_text(self) -> str:
        return self.trim_output_text or self.alignment_output_text or self.original_fasta_text
