import re

from context import SequenceRecord


def _split_header(header_text: str):
    if not header_text:
        raise ValueError("Encountered an empty FASTA header.")
    parts = header_text.split(maxsplit=1)
    seq_id = parts[0]
    description = parts[1] if len(parts) > 1 else ""
    return seq_id, description


def parse_fasta_records(fasta_text: str):
    records = []
    header = None
    seq_lines = []

    for raw_line in fasta_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if header is not None:
                seq_id, description = _split_header(header)
                records.append(
                    SequenceRecord(
                        seq_id=seq_id,
                        header=header,
                        description=description,
                        sequence="".join(seq_lines),
                    )
                )
            header = line[1:].strip()
            seq_lines = []
            continue
        if header is None:
            raise ValueError("FASTA text must start with a header line beginning with '>'.")
        seq_lines.append(line)

    if header is not None:
        seq_id, description = _split_header(header)
        records.append(
            SequenceRecord(
                seq_id=seq_id,
                header=header,
                description=description,
                sequence="".join(seq_lines),
            )
        )

    return records


def select_records_by_ids(records, selected_ids):
    selected_set = set(selected_ids)
    return [record for record in records if record.seq_id in selected_set]


def format_fasta_records(records):
    lines = []
    for record in records:
        lines.append(">" + record.header)
        sequence = record.sequence or ""
        for index in range(0, len(sequence), 80):
            lines.append(sequence[index:index + 80])
    return "\n".join(lines) + ("\n" if lines else "")


_LEAF_LABEL_PATTERN = re.compile(r"(?<=[(,])([^'():;,]+|'.*?')(?=[:),;])")


def extract_leaf_labels_from_newick(newick_text: str):
    labels = []
    for match in _LEAF_LABEL_PATTERN.finditer(newick_text):
        label = match.group(1).strip()
        if not label:
            continue
        if len(label) >= 2 and label[0] == "'" and label[-1] == "'":
            label = label[1:-1]
        labels.append(label)
    return labels


def build_leaf_label_map(records, tree_text: str):
    seq_ids = [record.seq_id for record in records]
    seq_id_set = set(seq_ids)
    sorted_seq_ids = sorted(seq_ids, key=len, reverse=True)
    label_map = {}

    for label in extract_leaf_labels_from_newick(tree_text):
        if label in seq_id_set:
            label_map[label] = label
            continue
        for seq_id in sorted_seq_ids:
            if not label.startswith(seq_id):
                continue
            suffix = label[len(seq_id):]
            if suffix.startswith("<") and suffix.endswith(">"):
                label_map[label] = seq_id
                break

    return label_map
