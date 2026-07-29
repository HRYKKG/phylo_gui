import unittest

from fasta_utils import parse_fasta_records


class ParseFastaRecordsTests(unittest.TestCase):
    def test_empty_input_is_rejected(self):
        for fasta_text in ("", "   ", "\n\t\n"):
            with self.subTest(fasta_text=repr(fasta_text)):
                with self.assertRaisesRegex(ValueError, "FASTA input is empty"):
                    parse_fasta_records(fasta_text)

    def test_nonempty_fasta_is_parsed(self):
        records = parse_fasta_records(">seq1\nACGT\n")

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].seq_id, "seq1")
        self.assertEqual(records[0].sequence, "ACGT")


if __name__ == "__main__":
    unittest.main()
