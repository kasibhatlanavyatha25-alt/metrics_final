import os
import re
import math
from typing import Dict, List, Any, Optional

try:
    import javalang
    from javalang.tree import ClassDeclaration, InterfaceDeclaration, MethodDeclaration, ConstructorDeclaration, FieldDeclaration
except ImportError:
    javalang = None

PRIMITIVE_TYPES = {
    'int', 'long', 'short', 'byte', 'char', 'float', 'double', 'boolean',
    'void', 'Integer', 'Long', 'Short', 'Byte', 'Character', 'Float', 'Double', 'Boolean',
    'String', 'Object'
}

class JavaClassMetrics:
    def __init__(self, class_name: str, package_name: str, file_path: str):
        self.class_name = class_name
        self.package_name = package_name or "(default)"
        self.file_path = file_path
        self.loc = 0
        self.wmc = 0
        self.cbo = 0
        self.rfc = 0
        self.lcom = 0.0
        self.dit = 1
        self.noc = 0
        self.cyclomatic_complexity = 1
        self.num_methods = 0
        self.num_fields = 0
        self.num_public_methods = 0
        self.num_static_methods = 0
        self.super_class = None
        self.interfaces = []
        self.field_names = set()
        self.methods_field_access = [] # list of sets of field names accessed per method
        self.invoked_methods = set()
        self.coupled_types = set()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "class_name": self.class_name,
            "package_name": self.package_name,
            "file_path": self.file_path,
            "loc": self.loc,
            "wmc": self.wmc,
            "cbo": self.cbo,
            "rfc": self.rfc,
            "lcom": round(self.lcom, 4),
            "dit": self.dit,
            "noc": self.noc,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "num_methods": self.num_methods,
            "num_fields": self.num_fields,
            "num_public_methods": self.num_public_methods,
            "num_static_methods": self.num_static_methods,
        }

def compute_code_loc(code_str: str) -> int:
    lines = code_str.splitlines()
    loc = 0
    in_block_comment = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if in_block_comment:
            if '*/' in stripped:
                in_block_comment = False
                after = stripped.split('*/', 1)[1].strip()
                if after:
                    loc += 1
            continue
        if stripped.startswith('/*'):
            if '*/' in stripped:
                after = stripped.split('*/', 1)[1].strip()
                if after:
                    loc += 1
            else:
                in_block_comment = True
            continue
        if stripped.startswith('//'):
            continue
        loc += 1
    return max(1, loc)

def compute_cyclomatic_complexity_text(code_chunk: str) -> int:
    """Calculates McCabe Cyclomatic Complexity using decision tokens."""
    complexity = 1
    # Control flow keywords
    patterns = [
        r'\bif\b',
        r'\bwhile\b',
        r'\bfor\b',
        r'\bcase\b',
        r'\bcatch\b',
        r'\bthrow\b',
        r'&&',
        r'\|\|',
        r'\?', # ternary
    ]
    for p in patterns:
        complexity += len(re.findall(p, code_chunk))
    return complexity

def extract_metrics_with_regex_fallback(file_path: str, code_content: str) -> List[JavaClassMetrics]:
    """Robust regex-based fallback extractor for Java files when AST parsing fails on newer syntax."""
    results = []
    
    # Extract package
    pkg_match = re.search(r'^\s*package\s+([\w\.]+);', code_content, re.MULTILINE)
    package_name = pkg_match.group(1) if pkg_match else ""

    # Extract imports for CBO
    imports = re.findall(r'^\s*import\s+([\w\.]+);', code_content, re.MULTILINE)
    imported_classes = {imp.split('.')[-1] for imp in imports if not imp.startswith('java.lang')}

    # Match class declarations
    class_pattern = re.compile(
        r'(?:public|protected|private|abstract|static|final|\s)*class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w\s,]+))?\s*\{',
        re.MULTILINE
    )
    
    classes_found = list(class_pattern.finditer(code_content))
    if not classes_found:
        # Check for interfaces or records or enums
        alt_pattern = re.compile(r'(?:public|protected|private|\s)*(?:interface|enum|record)\s+(\w+)', re.MULTILINE)
        for m in alt_pattern.finditer(code_content):
            c_name = m.group(1)
            metrics = JavaClassMetrics(c_name, package_name, file_path)
            metrics.loc = compute_code_loc(code_content)
            metrics.cyclomatic_complexity = 1
            metrics.wmc = 1
            metrics.cbo = min(len(imported_classes), 10)
            metrics.rfc = 1
            results.append(metrics)
        if not results:
            # Single synthetic class matching filename
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            metrics = JavaClassMetrics(base_name, package_name, file_path)
            metrics.loc = compute_code_loc(code_content)
            metrics.wmc = compute_cyclomatic_complexity_text(code_content)
            metrics.cyclomatic_complexity = metrics.wmc
            metrics.cbo = min(len(imported_classes), 10)
            metrics.rfc = metrics.wmc
            results.append(metrics)
        return results

    for match in classes_found:
        c_name = match.group(1)
        super_name = match.group(2)
        implements_str = match.group(3)
        
        metrics = JavaClassMetrics(c_name, package_name, file_path)
        metrics.loc = compute_code_loc(code_content)
        metrics.super_class = super_name

        # DIT approximation
        metrics.dit = 2 if super_name and super_name != 'Object' else 1

        # Fields
        field_matches = re.findall(r'(?:private|protected|public)\s+([\w\<\>\[\]]+)\s+(\w+)\s*(?:=|;)', code_content)
        metrics.num_fields = len(field_matches)
        for f_type, f_name in field_matches:
            metrics.field_names.add(f_name)
            base_t = re.sub(r'[\<\>\[\]]', '', f_type)
            if base_t not in PRIMITIVE_TYPES:
                metrics.coupled_types.add(base_t)

        # Methods
        method_pattern = re.compile(
            r'(public|protected|private)?\s+(?:static\s+)?([\w\<\>\[\]]+)\s+(\w+)\s*\(([^)]*)\)\s*(?:throws\s+[\w\s,]+)?\s*\{'
        )
        methods = list(method_pattern.finditer(code_content))
        metrics.num_methods = len(methods)
        
        total_wmc = 0
        method_field_shares = []

        for m in methods:
            visibility = m.group(1) or ""
            ret_type = m.group(2)
            m_name = m.group(3)
            params = m.group(4)
            
            if 'public' in visibility:
                metrics.num_public_methods += 1
            if 'static' in m.group(0):
                metrics.num_static_methods += 1

            if ret_type not in PRIMITIVE_TYPES:
                metrics.coupled_types.add(ret_type)

            # Params
            param_types = re.findall(r'(\w+)\s+\w+', params)
            for pt in param_types:
                if pt not in PRIMITIVE_TYPES:
                    metrics.coupled_types.add(pt)

            total_wmc += 1

        metrics.wmc = max(1, total_wmc)
        metrics.cyclomatic_complexity = compute_cyclomatic_complexity_text(code_content)
        
        # Coupled types + imports
        metrics.coupled_types.update(imported_classes)
        metrics.cbo = len(metrics.coupled_types)

        # RFC = methods in class + external invocations
        invocations = set(re.findall(r'\b(\w+)\s*\(', code_content))
        metrics.rfc = metrics.num_methods + len(invocations - {m.group(3) for m in methods})

        # LCOM (Lack of Cohesion of Methods) Henderson-Sellers approximation
        if metrics.num_methods > 1 and metrics.num_fields > 0:
            # Henderson-Sellers LCOM = (M - sum(mF)/F) / (M - 1)
            # where sum(mF) is total field accesses across methods
            # Default normalized between 0 (cohesive) and 1 (lacks cohesion)
            m = metrics.num_methods
            f = metrics.num_fields
            # Count field appearances in code
            field_access_sum = sum(code_content.count(fn) for fn in metrics.field_names)
            avg_field_access = field_access_sum / (f * m)
            lcom_hs = max(0.0, min(1.0, (1.0 - avg_field_access)))
            metrics.lcom = lcom_hs
        else:
            metrics.lcom = 0.0

        results.append(metrics)

    return results

def extract_metrics_from_ast(file_path: str, code_content: str) -> List[JavaClassMetrics]:
    """Uses javalang AST parsing with full structural resolution."""
    if not javalang:
        return extract_metrics_with_regex_fallback(file_path, code_content)

    try:
        tree = javalang.parse.parse(code_content)
    except Exception:
        # If AST parsing fails due to modern features, fallback safely
        return extract_metrics_with_regex_fallback(file_path, code_content)

    package_name = tree.package.name if tree.package else ""
    imports = {imp.path.split('.')[-1] for imp in tree.imports if not imp.path.startswith('java.lang')}

    results = []
    
    # Process classes
    for path, node in tree.filter(ClassDeclaration):
        class_name = node.name
        metrics = JavaClassMetrics(class_name, package_name, file_path)
        metrics.loc = compute_code_loc(code_content)

        # Superclass & DIT
        if node.extends:
            metrics.super_class = node.extends.name
            metrics.dit = 2 if node.extends.name != 'Object' else 1
            if node.extends.name not in PRIMITIVE_TYPES:
                metrics.coupled_types.add(node.extends.name)

        # Implements
        if node.implements:
            for iface in node.implements:
                metrics.interfaces.append(iface.name)
                if iface.name not in PRIMITIVE_TYPES:
                    metrics.coupled_types.add(iface.name)

        # Fields
        for field in node.fields:
            field_type = field.type.name if hasattr(field.type, 'name') else str(field.type)
            if field_type not in PRIMITIVE_TYPES:
                metrics.coupled_types.add(field_type)
            for declarator in field.declarators:
                metrics.field_names.add(declarator.name)
                metrics.num_fields += 1

        # Methods
        methods = list(node.methods)
        constructors = list(node.constructors)
        all_callables = methods + constructors
        metrics.num_methods = len(all_callables)

        total_wmc = 0
        methods_field_access = []

        for m in all_callables:
            if hasattr(m, 'modifiers') and m.modifiers:
                if 'public' in m.modifiers:
                    metrics.num_public_methods += 1
                if 'static' in m.modifiers:
                    metrics.num_static_methods += 1

            if hasattr(m, 'return_type') and m.return_type:
                rt_name = m.return_type.name if hasattr(m.return_type, 'name') else str(m.return_type)
                if rt_name not in PRIMITIVE_TYPES:
                    metrics.coupled_types.add(rt_name)

            if hasattr(m, 'parameters') and m.parameters:
                for param in m.parameters:
                    pt_name = param.type.name if hasattr(param.type, 'name') else str(param.type)
                    if pt_name not in PRIMITIVE_TYPES:
                        metrics.coupled_types.add(pt_name)

            # Method complexity
            m_complexity = 1
            accessed_fields = set()

            if m.body:
                for _, sub_node in m.filter(javalang.tree.IfStatement):
                    m_complexity += 1
                for _, sub_node in m.filter(javalang.tree.WhileStatement):
                    m_complexity += 1
                for _, sub_node in m.filter(javalang.tree.ForStatement):
                    m_complexity += 1
                for _, sub_node in m.filter(javalang.tree.CatchClause):
                    m_complexity += 1
                for _, sub_node in m.filter(javalang.tree.SwitchStatement):
                    m_complexity += 1
                for _, sub_node in m.filter(javalang.tree.MethodInvocation):
                    metrics.invoked_methods.add(sub_node.member)
                for _, sub_node in m.filter(javalang.tree.MemberReference):
                    if sub_node.member in metrics.field_names:
                        accessed_fields.add(sub_node.member)

            total_wmc += m_complexity
            methods_field_access.append(accessed_fields)

        metrics.wmc = max(1, total_wmc)
        metrics.cyclomatic_complexity = compute_cyclomatic_complexity_text(code_content)
        
        # CBO: coupled types + relevant imports
        metrics.coupled_types.update(imports)
        metrics.cbo = len(metrics.coupled_types)

        # RFC = methods in class + distinct external method invocations
        metrics.rfc = metrics.num_methods + len(metrics.invoked_methods)

        # LCOM: Henderson-Sellers LCOM metric
        # LCOM* = ( (1/F) * sum(mF) - M ) / (1 - M)
        m_count = metrics.num_methods
        f_count = metrics.num_fields
        if m_count > 1 and f_count > 0:
            sum_mf = sum(len(f_set) for f_set in methods_field_access)
            if sum_mf == 0:
                metrics.lcom = 1.0 # No field sharing
            else:
                avg_f = sum_mf / f_count
                lcom_val = (avg_f - m_count) / (1 - m_count)
                metrics.lcom = max(0.0, min(1.0, 1.0 - (sum_mf / (m_count * f_count))))
        else:
            metrics.lcom = 0.0

        results.append(metrics)

    if not results:
        return extract_metrics_with_regex_fallback(file_path, code_content)

    return results

def analyze_java_repository(repo_path: str) -> Dict[str, Any]:
    """Scans all Java/Python source files in repository path and extracts class, package, and project level metrics."""
    java_files = []
    py_files = []
    for root, _, files in os.walk(repo_path):
        if '.git' in root or 'node_modules' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.startswith('.'):
                continue
            f_path = os.path.join(root, file)
            if file.endswith('.java'):
                java_files.append(f_path)
            elif file.endswith(('.py', '.ts', '.tsx')):
                py_files.append(f_path)

    class_metrics_list: List[JavaClassMetrics] = []
    files_to_scan = java_files if java_files else py_files
    
    for src_file in files_to_scan:
        try:
            with open(src_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            c_metrics = extract_metrics_from_ast(src_file, content)
            class_metrics_list.extend(c_metrics)
        except Exception as e:
            # Ensure resilient parsing on edge files
            continue

    # Compute NOC (Number of Children) and inheritance tree depth across project
    class_map = {cm.class_name: cm for cm in class_metrics_list}
    for cm in class_metrics_list:
        if cm.super_class and cm.super_class in class_map:
            class_map[cm.super_class].noc += 1
            # Calculate true DIT
            depth = 1
            curr = cm
            visited = set()
            while curr.super_class and curr.super_class in class_map and curr.super_class not in visited:
                visited.add(curr.class_name)
                depth += 1
                curr = class_map[curr.super_class]
            cm.dit = depth

    # Aggregations
    total_classes = len(class_metrics_list)
    packages = {cm.package_name for cm in class_metrics_list}
    
    total_loc = sum(cm.loc for cm in class_metrics_list)
    total_methods = sum(cm.num_methods for cm in class_metrics_list)
    total_fields = sum(cm.num_fields for cm in class_metrics_list)
    
    avg_loc = total_loc / max(1, total_classes)
    avg_wmc = sum(cm.wmc for cm in class_metrics_list) / max(1, total_classes)
    avg_cbo = sum(cm.cbo for cm in class_metrics_list) / max(1, total_classes)
    avg_rfc = sum(cm.rfc for cm in class_metrics_list) / max(1, total_classes)
    avg_lcom = sum(cm.lcom for cm in class_metrics_list) / max(1, total_classes)
    avg_dit = sum(cm.dit for cm in class_metrics_list) / max(1, total_classes)
    avg_noc = sum(cm.noc for cm in class_metrics_list) / max(1, total_classes)
    avg_complexity = sum(cm.cyclomatic_complexity for cm in class_metrics_list) / max(1, total_classes)

    project_summary = {
        "total_java_files": len(java_files),
        "total_classes": total_classes,
        "total_packages": len(packages),
        "total_loc": total_loc,
        "avg_loc": round(avg_loc, 2),
        "avg_wmc": round(avg_wmc, 2),
        "avg_cbo": round(avg_cbo, 2),
        "avg_rfc": round(avg_rfc, 2),
        "avg_lcom": round(avg_lcom, 4),
        "avg_dit": round(avg_dit, 2),
        "avg_noc": round(avg_noc, 2),
        "avg_complexity": round(avg_complexity, 2),
        "total_methods": total_methods,
        "total_fields": total_fields
    }

    return {
        "classes": [cm.to_dict() for cm in class_metrics_list],
        "project": project_summary
    }
