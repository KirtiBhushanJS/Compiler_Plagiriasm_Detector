import ast
from c_parser import CanonicalNode

class PyToCanonicalParser:
    def parse(self, code: str) -> CanonicalNode:
        root = CanonicalNode("BLOCK")
        try:
            parsed_ast = ast.parse(code)
        except SyntaxError:
            return root
            
        # ast.walk is unordered. We MUST use NodeVisitor for sequential execution order.
        visitor = OrderedASTVisitor(root)
        visitor.visit(parsed_ast)
        return root

class OrderedASTVisitor(ast.NodeVisitor):
    """Visits Python AST nodes in strict sequential order to match C's linear flow."""
    def __init__(self, root_node):
        self.root = root_node

    def visit_Assign(self, node):
        self.root.children.append(CanonicalNode("ASSIGN"))
        self.generic_visit(node)

    def visit_For(self, node):
        self.root.children.append(CanonicalNode("LOOP"))
        self.generic_visit(node)

    def visit_While(self, node):
        self.root.children.append(CanonicalNode("LOOP"))
        self.generic_visit(node)

    def visit_If(self, node):
        self.root.children.append(CanonicalNode("BRANCH"))
        self.generic_visit(node)

    def visit_Return(self, node):
        self.root.children.append(CanonicalNode("RETURN"))
        self.generic_visit(node)

    def visit_BinOp(self, node):
        self.root.children.append(CanonicalNode("BIN_OP"))
        self.generic_visit(node)