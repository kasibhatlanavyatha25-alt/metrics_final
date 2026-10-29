import logging
import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
import javalang
from javalang.tree import (
    ClassDeclaration,
    MethodDeclaration,
    ConstructorDeclaration,
    IfStatement,
    ForStatement,
    WhileStatement,
    DoStatement,
    SwitchStatementCase,
    CatchClause,
    TernaryExpression,
    BinaryOperation,
    FieldDeclaration,
    FormalParameter,
    Creator,
    MemberReference,
    ReferenceType,
)
from app.models.schemas import MetricVector

logger = logging.getLogger("software_dna.metrics")

PRIMITIVES_AND_BASIC_TYPES: Set[str] = {
    "int", "long", "double", "float", "boolean", "byte", "char", "short", "void",
    "String", "Integer", "Long", "Double", "Float", "Boolean", "Byte", "Character", "Short",
    "Object", "System", "Thread", "Exception", "RuntimeException", "Throwable", "Math",
    "Class", "Void", "StringBuilder", "StringBuffer", "Iterable", "Comparable", "AutoCloseable",
    "List", "Map", "Set", "Collection", "ArrayList", "HashMap", "HashSet",
}


def calculate_loc(source_code: str) -> int:
    """
    Counts non-empty, non-comment source lines.
    """
    lines = source_code.splitlines()
    loc = 0
    in_block_comment = False

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        if in_block_comment:
            if "*/" in line:
                in_block_comment = False
                after_comment = line.split("*/", 1)[1].strip()
                if after_comment and not after_comment.startswith("//"):
                    loc += 1
            continue

        if line.startswith("/*"):
            if "*/" in line:
                after_comment = line.split("*/", 1)[1].strip()
                if after_comment and not after_comment.startswith("//"):
                    loc += 1
            else:
                in_block_comment = True
            continue

        if line.startswith("//"):
            continue

        loc += 1

    return max(1, loc)


def calculate_method_cyclomatic_complexity(method_node: MethodDeclaration | ConstructorDeclaration) -> int:
    """
    CC(method) = 1 + number of decision constructs (if, for, while, do, case, catch, ternary ?:, logical &&/||).
    """
    complexity = 1

    if not method_node.body:
        return complexity

    for path, node in method_node:
        if isinstance(node, (IfStatement, ForStatement, WhileStatement, DoStatement, SwitchStatementCase, CatchClause, TernaryExpression)):
            complexity += 1
        elif isinstance(node, BinaryOperation):
            if hasattr(node, "operator") and node.operator in ("&&", "||"):
                complexity += 1

    return complexity


def extract_class_fields(class_node: ClassDeclaration) -> List[str]:
    """Extract declared attribute names in the class."""
    field_names = []
    for field in class_node.fields:
        for declarator in field.declarators:
            field_names.append(declarator.name)
    return field_names


def calculate_cbo(class_node: ClassDeclaration, class_name: str, compilation_unit: javalang.tree.CompilationUnit) -> int:
    """
    CBO: Count unique external classes/types referenced.
    Exclude primitives, java.lang basics, and the class itself.
    """
    referenced_types: Set[str] = set()

    # 1. Imports
    if compilation_unit and compilation_unit.imports:
        for imp in compilation_unit.imports:
            parts = imp.path.split(".")
            simple_name = parts[-1]
            if simple_name not in PRIMITIVES_AND_BASIC_TYPES and simple_name != class_name:
                referenced_types.add(simple_name)

    # 2. Reference Types in Fields, Methods, Parameters, Return Types
    for _, ref_type in class_node.filter(ReferenceType):
        name = ref_type.name
        if name and name not in PRIMITIVES_AND_BASIC_TYPES and name != class_name:
            referenced_types.add(name)

    # 3. Object creations: new Foo(...)
    for _, creator in class_node.filter(Creator):
        if creator.type and creator.type.name:
            name = creator.type.name
            if name not in PRIMITIVES_AND_BASIC_TYPES and name != class_name:
                referenced_types.add(name)

    return len(referenced_types)


def calculate_lcom_henderson_sellers(class_node: ClassDeclaration) -> float:
    """
    Henderson-Sellers Lack of Cohesion in Methods:
    LCOM* = ( (1/a) * sum(mu(A_j)) - m ) / (1 - m)
    where:
      m = number of methods
      a = number of attributes
      mu(A_j) = number of methods accessing attribute A_j
    Range: 0.0 (high cohesion) to 1.0 (low cohesion)
    """
    fields = extract_class_fields(class_node)
    a = len(fields)
    methods = [m for m in class_node.methods if m.body]
    m = len(methods)

    if m <= 1 or a == 0:
        return 0.0

    field_access_counts: Dict[str, int] = {f: 0 for f in fields}

    for method in methods:
        accessed_in_this_method: Set[str] = set()
        for _, member_ref in method.filter(MemberReference):
            if member_ref.member in field_access_counts:
                accessed_in_this_method.add(member_ref.member)
        
        # Also check variable expressions that match field names
        for f in fields:
            if f in accessed_in_this_method:
                field_access_counts[f] += 1

    sum_mu = sum(field_access_counts.values())
    avg_mu = sum_mu / a

    lcom = (avg_mu - m) / (1.0 - m)
    # Clamp between 0.0 and 1.0
    lcom_clamped = max(0.0, min(1.0, float(lcom)))
    return round(lcom_clamped, 2)


def extract_metrics_from_ast(compilation_unit: javalang.tree.CompilationUnit, source_code: str) -> Dict[str, MetricVector]:
    """
    Extracts M(c, t) = [LOC, CC, WMC, CBO, LCOM] for all classes in compilation unit.
    """
    results: Dict[str, MetricVector] = {}
    total_loc = calculate_loc(source_code)

    if not compilation_unit or not compilation_unit.types:
        return results

    for type_decl in compilation_unit.types:
        if not isinstance(type_decl, ClassDeclaration):
            continue

        class_name = type_decl.name
        
        # Method-level complexities
        method_complexities = []
        for method in type_decl.methods:
            cc = calculate_method_cyclomatic_complexity(method)
            method_complexities.append(cc)

        for constructor in type_decl.constructors:
            cc = calculate_method_cyclomatic_complexity(constructor)
            method_complexities.append(cc)

        max_cc = max(method_complexities) if method_complexities else 1
        wmc = sum(method_complexities) if method_complexities else 1
        cbo = calculate_cbo(type_decl, class_name, compilation_unit)
        lcom = calculate_lcom_henderson_sellers(type_decl)

        results[class_name] = MetricVector(
            loc=total_loc,
            cc=max_cc,
            wmc=wmc,
            cbo=cbo,
            lcom=lcom,
        )
        logger.debug(f"[MetricsEngine] Extracted {class_name}: LOC={total_loc}, CC={max_cc}, WMC={wmc}, CBO={cbo}, LCOM={lcom}")

    return results


import ast


def extract_python_metrics(source_code: str, file_path: str = "") -> Tuple[Optional[Any], Dict[str, MetricVector]]:
    """
    Parses Python source code into Python AST and extracts LOC, CC, WMC, CBO, LCOM.
    """
    total_loc = calculate_loc(source_code)
    results: Dict[str, MetricVector] = {}

    try:
        tree = ast.parse(source_code)
    except Exception as e:
        logger.debug(f"Python parse fallback for {file_path}: {e}")
        mod_name = Path(file_path).stem or "Module"
        return None, {mod_name: MetricVector(loc=total_loc, cc=1, wmc=1, cbo=0, lcom=0.0)}

    # Helper to calculate function CC
    def calc_py_func_cc(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
        cc = 1
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler, ast.With, ast.AsyncWith, ast.IfExp, ast.Assert)):
                cc += 1
            elif isinstance(node, ast.BoolOp):
                cc += len(node.values) - 1
            elif hasattr(ast, 'Match') and isinstance(node, ast.Match):
                cc += len(getattr(node, 'cases', []))
        return cc

    # Extract all classes in the module
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]

    # Collect imported external names for CBO
    imported_names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_names.add(node.module.split(".")[0])

    if not classes:
        # Standalone script/module
        mod_name = Path(file_path).stem or "Module"
        funcs = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if funcs:
            ccs = [calc_py_func_cc(f) for f in funcs]
            max_cc = max(ccs)
            wmc = sum(ccs)
        else:
            # Top-level script complexity
            top_cc = 1
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                    top_cc += 1
            max_cc = top_cc
            wmc = top_cc

        results[mod_name] = MetricVector(
            loc=total_loc,
            cc=max_cc,
            wmc=wmc,
            cbo=len(imported_names),
            lcom=0.0,
        )
        return tree, results

    for cls_node in classes:
        cls_name = cls_node.name
        methods = [n for n in cls_node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        
        if methods:
            ccs = [calc_py_func_cc(m) for m in methods]
            max_cc = max(ccs)
            wmc = sum(ccs)
        else:
            max_cc = 1
            wmc = 1

        # CBO: base classes + imported types + instantiated types
        class_refs = set(imported_names)
        for base in cls_node.bases:
            if isinstance(base, ast.Name):
                class_refs.add(base.id)

        # LCOM: self.<attr> accesses
        fields: Set[str] = set()
        method_field_access: Dict[str, Set[str]] = {}

        for m in methods:
            method_field_access[m.name] = set()
            for node in ast.walk(m):
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
                    fields.add(node.attr)
                    method_field_access[m.name].add(node.attr)

        m_count = len(methods)
        a_count = len(fields)
        if m_count <= 1 or a_count == 0:
            lcom = 0.0
        else:
            avg_access = sum(len(accs) for accs in method_field_access.values()) / a_count
            raw_lcom = (avg_access - m_count) / (1.0 - m_count)
            lcom = round(max(0.0, min(1.0, float(raw_lcom))), 2)

        results[cls_name] = MetricVector(
            loc=total_loc,
            cc=max_cc,
            wmc=wmc,
            cbo=len(class_refs),
            lcom=lcom,
        )

    return tree, results


def parse_and_extract_metrics(source_code: str, file_path: str = "") -> Tuple[Optional[Any], Dict[str, MetricVector]]:
    """Helper to parse raw Java or Python source string and calculate metric vectors."""
    if file_path.endswith((".py", ".pyw")):
        return extract_python_metrics(source_code, file_path)

    # TypeScript / JavaScript simple fallback extractor
    if file_path.endswith((".ts", ".tsx", ".js", ".jsx")):
        loc = calculate_loc(source_code)
        mod_name = Path(file_path).stem or "Component"
        # Fast regex-based decision count for TS/JS
        decisions = len(re.findall(r'\b(if|for|while|case|catch)\b|\?|&&|\|\|', source_code))
        cc = max(1, 1 + decisions // 2)
        wmc = max(1, decisions)
        imports = len(re.findall(r'\bimport\b', source_code))
        return None, {
            mod_name: MetricVector(loc=loc, cc=min(cc, 25), wmc=min(wmc, 40), cbo=imports, lcom=0.0)
        }

    # Java parsing via javalang
    try:
        tree = javalang.parse.parse(source_code)
        metrics = extract_metrics_from_ast(tree, source_code)
        return tree, metrics
    except Exception as ex:
        logger.error(f"[MetricsEngine] Parsing failed for {file_path}: {ex}")
        loc = calculate_loc(source_code)
        mod_name = Path(file_path).stem or "UnknownClass"
        return None, {
            mod_name: MetricVector(loc=loc, cc=1, wmc=1, cbo=0, lcom=0.0)
        }
