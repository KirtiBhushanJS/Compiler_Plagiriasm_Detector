import re

class CanonicalNode:
    def __init__(self, node_type: str):
        self.node_type = node_type
        self.children = []

class CToCanonicalParser:
    def parse(self, code: str) -> CanonicalNode:
        root = CanonicalNode("BLOCK")
        
        code = re.sub(r'//.*', '', code)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        
        code = re.sub(r'for\s*\([^)]+\)', 'for', code)
        code = re.sub(r'while\s*\([^)]+\)', 'while', code)
        
        tokens = re.finditer(r'\b(for|while|if|return)\b|(=|\+|\-|\*|/)', code)
        
        for match in tokens:
            val = match.group(0)
            if val in ['for', 'while']:
                root.children.append(CanonicalNode("LOOP"))
            elif val == 'if':
                root.children.append(CanonicalNode("BRANCH"))
            elif val == 'return':
                root.children.append(CanonicalNode("RETURN"))
            elif val == '=':
                root.children.append(CanonicalNode("ASSIGN"))
            elif val in ['+', '-', '*', '/']:
                root.children.append(CanonicalNode("BIN_OP"))
                
        return root
