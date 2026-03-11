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
