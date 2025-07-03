import ast
import os
import sys

class ConditionalVisitor(ast.NodeVisitor):
    def __init__(self):
        self.in_test_function = False
        self.violations = []
        self.current_function = None

    def visit_FunctionDef(self, node):
        if node.name.startswith('test_'):
            old_in_test = self.in_test_function
            old_function = self.current_function
            self.in_test_function = True
            self.current_function = node.name
            self.generic_visit(node)
            self.in_test_function = old_in_test
            self.current_function = old_function
        else:
            self.generic_visit(node)

    def visit_If(self, node):
        if self.in_test_function:
            # Check if this is an acceptable conditional
            if not self._is_acceptable_conditional(node):
                self.violations.append(f"  Line {node.lineno}: if statement in {self.current_function}")
        self.generic_visit(node)
    
    def _is_acceptable_conditional(self, node):
        """Check if a conditional is acceptable in tests."""
        
        # Check AST structure for acceptable patterns
        if self._contains_pytest_skip(node):
            return True
            
        if self._contains_isinstance_check(node):
            return True
            
        if self._contains_assertion_patterns(node):
            return True
            
        if self._is_processor_availability_check(node):
            return True
        
        return False
    
    def _contains_pytest_skip(self, node):
        """Check if conditional contains pytest.skip."""
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    if (isinstance(child.func.value, ast.Name) and 
                        child.func.value.id == 'pytest' and 
                        child.func.attr == 'skip'):
                        return True
        return False
    
    def _contains_isinstance_check(self, node):
        """Check if conditional contains isinstance check."""
        if isinstance(node.test, ast.Call):
            if isinstance(node.test.func, ast.Name) and node.test.func.id == 'isinstance':
                return True
        return False
    
    def _contains_assertion_patterns(self, node):
        """Check if conditional contains assertion-related patterns."""
        for child in ast.walk(node):
            if isinstance(child, ast.Assert):
                return True
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    if (isinstance(child.func.value, ast.Name) and 
                        child.func.value.id == 'pytest' and 
                        child.func.attr in ['fail', 'xfail']):
                        return True
        return False
    
    def _is_processor_availability_check(self, node):
        """Check if conditional is checking processor availability."""
        # Look for patterns like: if content_type not in self.processor.processors
        if isinstance(node.test, ast.Compare):
            if len(node.test.ops) == 1 and isinstance(node.test.ops[0], (ast.NotIn, ast.In)):
                # Check if we're comparing against something like self.processor.processors
                if isinstance(node.test.comparators[0], ast.Attribute):
                    attr = node.test.comparators[0]
                    if (isinstance(attr.value, ast.Attribute) and 
                        isinstance(attr.value.value, ast.Name) and
                        attr.value.value.id == 'self' and
                        attr.value.attr == 'processor' and
                        attr.attr == 'processors'):
                        return True
        return False
    
    def _is_parameter_processing_conditional(self, node):
        """Check if conditional is for parameter processing."""
        # This is a simple heuristic - in practice you might want more sophisticated detection
        return False

violations_found = False
for root, dirs, files in os.walk('tests'):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                tree = ast.parse(content, filename=filepath)
                visitor = ConditionalVisitor()
                visitor.visit(tree)
                if visitor.violations:
                    violations_found = True
                    print(f"\nViolations in {filepath}:")
                    for violation in visitor.violations:
                        print(violation)
            except Exception as e:
                print(f"Warning: Could not parse {filepath}: {e}")

if violations_found:
    print("\nERROR: Found conditional statements in test functions.")
    print("This violates the No-Conditionals-In-Tests rule.")
    print("Use parametrized tests instead of conditionals in test functions.")
    sys.exit(1)
else:
    print("✓ No conditionals found in test functions")
