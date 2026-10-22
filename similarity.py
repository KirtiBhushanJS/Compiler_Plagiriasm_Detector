from difflib import SequenceMatcher

class SimilarityEngine:
    def extract_sequence(self, node) -> list:
        # Converts the AST into a linear list of structural operations
        return [child.node_type for child in node.children]

    def compute_jaccard_similarity(self, tree_a, tree_b) -> float:
        seq_a = self.extract_sequence(tree_a)
        seq_b = self.extract_sequence(tree_b)

        if not seq_a and not seq_b:
            return 100.0
        if not seq_a or not seq_b:
            return 0.0

        # difflib calculates the Levenshtein-like contiguous matching subsequence ratio.
        # This is perfectly suited for structural code sequence alignment.
        matcher = SequenceMatcher(None, seq_a, seq_b)
        return matcher.ratio() * 100.0