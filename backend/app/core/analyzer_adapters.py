import os
import re
import ast
import math
from abc import ABC, abstractmethod
from typing import Dict, List, Set, Optional, Tuple, Any

try:
    import javalang
    from javalang.tree import (
        ClassDeclaration, InterfaceDeclaration, MethodDeclaration, 
        ConstructorDeclaration, FieldDeclaration, IfStatement, 
        ForStatement, WhileStatement, DoStatement, SwitchStatementCase, 
        CatchClause, TernaryExpression, BinaryOperation
    )
except ImportError:
    javalang = None


class NormalizedMetric:
    """
    Unified, language-independent metric representation for a single class, 
    module, or source unit.
    """
    def __init__(
        self,
        class_name: str,
        package_name: str,
        file_path: str,
        language: str,
        loc: int = 0,
        cyclomatic_complexity: int = 1,
        wmc: int = 1,
        cbo: int = 0,
        rfc: int = 0,
        lcom: float = 0.0,
        dit: int = 1,
        noc: int = 0,
        num_methods: int = 0,
        num_fields: int = 0,
        num_public_methods: int = 0,
        num_static_methods: int = 0,
        super_class: Optional[str] = None,
        interfaces: Optional[List[str]] = None,
        field_names: Optional[Set[str]] = None,
        methods_field_access: Optional[List[Set[str]]] = None,
        invoked_methods: Optional[Set[str]] = None,
        coupled_types: Optional[Set[str]] = None,
        metric_availability: Optional[Dict[str, bool]] = None,
        unit_type: str = "class"
    ):
        self.class_name = class_name
        self.package_name = package_name or "(default)"
        self.file_path = file_path
        self.language = language
        self.loc = max(1, loc)
        self.cyclomatic_complexity = max(1, cyclomatic_complexity)
        self.wmc = max(1, wmc)
        self.cbo = max(0, cbo)
        self.rfc = max(0, rfc)
        self.lcom = max(0.0, min(1.0, float(lcom)))
        self.dit = max(1, dit)
        self.noc = max(0, noc)
        self.num_methods = max(0, num_methods)
        self.num_fields = max(0, num_fields)
        self.num_public_methods = max(0, num_public_methods)
        self.num_static_methods = max(0, num_static_methods)
        self.super_class = super_class
        self.interfaces = interfaces or []
        self.field_names = field_names or set()
        self.methods_field_access = methods_field_access or []
        self.invoked_methods = invoked_methods or set()
        self.coupled_types = coupled_types or set()
        self.unit_type = unit_type
        self.metric_availability = metric_availability or {
            "loc": True,
            "cyclomatic_complexity": True,
            "wmc": True,
            "cbo": True,
            "lcom": True,
            "dit": True,
            "noc": True,
            "rfc": True
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "class_name": self.class_name,
            "package_name": self.package_name,
            "file_path": self.file_path,
            "language": self.language,
            "unit_type": self.unit_type,
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
            "metric_availability": self.metric_availability
        }


def compute_generic_loc(code_str: str, comment_prefix: str = "#") -> int:
    """Computes non-empty, non-comment lines of code."""
    lines = code_str.splitlines()
    loc = 0
    in_block_comment = False
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        # Handle block comments if C/Java style
        if comment_prefix in ("//", "/*"):
            if in_block_comment:
                if "*/" in stripped:
                    in_block_comment = False
                    after = stripped.split("*/", 1)[1].strip()
                    if after:
                        loc += 1
                continue
            if stripped.startswith("/*"):
                if "*/" in stripped:
                    after = stripped.split("*/", 1)[1].strip()
                    if after:
                        loc += 1
                else:
                    in_block_comment = True
                continue
            if stripped.startswith("//"):
                continue
        elif comment_prefix == "#":
            # Python single line or docstring comment
            if stripped.startswith("#"):
                continue
        
        loc += 1
    return max(1, loc)


class LanguageAnalyzer(ABC):
    """Abstract Base Class for language-specific metric extraction."""
    
    @property
    @abstractmethod
    def language_name(self) -> str:
        pass

    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        pass

    def can_handle(self, file_path: str) -> bool:
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.supported_extensions

    @abstractmethod
    def analyze_source(self, file_path: str, source_code: str) -> List[NormalizedMetric]:
        """Parses AST of source code and extracts normalized metrics."""
        pass

    def analyze_file(self, file_path: str) -> List[NormalizedMetric]:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return self.analyze_source(file_path, content)
        except Exception:
            return []


class JavaAnalyzer(LanguageAnalyzer):
    """Java AST Metric Analyzer using javalang with regex fallback."""
    
    PRIMITIVE_TYPES = {
        'int', 'long', 'short', 'byte', 'char', 'float', 'double', 'boolean',
        'void', 'Integer', 'Long', 'Short', 'Byte', 'Character', 'Float', 'Double', 'Boolean',
        'String', 'Object', 'System', 'Thread', 'Math', 'List', 'Map', 'Set', 'Collection'
    }

    @property
    def language_name(self) -> str:
        return "Java"

    @property
    def supported_extensions(self) -> List[str]:
        return [".java"]

    def analyze_source(self, file_path: str, source_code: str) -> List[NormalizedMetric]:
        if not source_code.strip():
            return []
        
        results: List[NormalizedMetric] = []
        loc = compute_generic_loc(source_code, comment_prefix="//")
        
        # Package extraction
        pkg_match = re.search(r'^\s*package\s+([\w\.]+);', source_code, re.MULTILINE)
        package_name = pkg_match.group(1) if pkg_match else "(default)"
        
        if javalang:
            try:
                tree = javalang.parse.parse(source_code)
                for path, node in tree.filter(ClassDeclaration):
                    c_name = node.name
                    metric = NormalizedMetric(
                        class_name=c_name,
                        package_name=package_name,
                        file_path=file_path,
                        language="Java",
                        loc=loc
                    )
                    
                    # Superclass & interfaces
                    if node.extends:
                        metric.super_class = node.extends.name
                    if node.implements:
                        metric.interfaces = [i.name for i in node.implements]
                    
                    # Fields
                    for field in node.fields:
                        for declarator in field.declarators:
                            metric.field_names.add(declarator.name)
                            metric.num_fields += 1
                        if field.type and field.type.name not in self.PRIMITIVE_TYPES:
                            metric.coupled_types.add(field.type.name)
                    
                    # Methods & WMC
                    methods = node.methods + (node.constructors or [])
                    metric.num_methods = len(methods)
                    total_cc = 0
                    max_cc = 1
                    
                    for m in methods:
                        m_cc = 1
                        if hasattr(m, 'modifiers') and m.modifiers:
                            if 'public' in m.modifiers:
                                metric.num_public_methods += 1
                            if 'static' in m.modifiers:
                                metric.num_static_methods += 1
                        
                        # Return & parameter coupling
                        if hasattr(m, 'return_type') and m.return_type and m.return_type.name not in self.PRIMITIVE_TYPES:
                            metric.coupled_types.add(m.return_type.name)
                        for param in (m.parameters or []):
                            if param.type and param.type.name not in self.PRIMITIVE_TYPES:
                                metric.coupled_types.add(param.type.name)
                        
                        # CC calculation
                        if m.body:
                            for _, sub_node in m:
                                if isinstance(sub_node, (IfStatement, ForStatement, WhileStatement, DoStatement, SwitchStatementCase, CatchClause, TernaryExpression)):
                                    m_cc += 1
                                elif isinstance(sub_node, BinaryOperation) and hasattr(sub_node, 'operator') and sub_node.operator in ('&&', '||'):
                                    m_cc += 1
                                # Invoked methods for RFC
                                if hasattr(sub_node, 'member') and sub_node.member:
                                    metric.invoked_methods.add(sub_node.member)
                        
                        total_cc += m_cc
                        if m_cc > max_cc:
                            max_cc = m_cc
                    
                    metric.wmc = total_cc if total_cc > 0 else 1
                    metric.cyclomatic_complexity = max_cc
                    metric.cbo = len(metric.coupled_types)
                    metric.rfc = metric.num_methods + len(metric.invoked_methods)
                    
                    # LCOM calculation
                    m_count = metric.num_methods
                    f_count = len(metric.field_names)
                    if m_count <= 1 or f_count == 0:
                        metric.lcom = 0.0
                    else:
                        # Estimate field sharing
                        metric.lcom = round(min(1.0, max(0.0, 1.0 - (f_count / max(1, m_count * 2)))), 4)
                    
                    results.append(metric)
                if results:
                    return results
            except Exception:
                pass
        
        # Fallback regex-based Java parsing
        class_matches = re.findall(r'(?:public\s+|abstract\s+|final\s+)*class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w\s,]+))?', source_code)
        if not class_matches:
            # Single module representation
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            cc = 1 + len(re.findall(r'\b(if|while|for|case|catch)\b|&&|\|\|', source_code))
            results.append(NormalizedMetric(
                class_name=base_name,
                package_name=package_name,
                file_path=file_path,
                language="Java",
                loc=loc,
                cyclomatic_complexity=cc,
                wmc=cc,
                cbo=len(re.findall(r'import\s+[\w\.]+;', source_code)),
                rfc=cc + 2,
                lcom=0.1
            ))
            return results

        for c_match in class_matches:
            c_name = c_match[0]
            super_c = c_match[1] if c_match[1] else None
            decisions = len(re.findall(r'\b(if|while|for|case|catch)\b|&&|\|\|', source_code))
            method_matches = re.findall(r'(?:public|protected|private|static|\s)+[\w\<\>\[\]]+\s+(\w+)\s*\([^\)]*\)\s*\{', source_code)
            imports = re.findall(r'import\s+([\w\.]+);', source_code)
            
            m_count = max(1, len(method_matches))
            cc = 1 + decisions
            wmc = cc
            cbo = len(set(imports))
            
            results.append(NormalizedMetric(
                class_name=c_name,
                package_name=package_name,
                file_path=file_path,
                language="Java",
                loc=loc,
                cyclomatic_complexity=max(1, cc // m_count),
                wmc=wmc,
                cbo=cbo,
                rfc=m_count + cbo,
                lcom=0.15,
                super_class=super_c,
                num_methods=m_count
            ))
            
        return results


class PythonAnalyzer(LanguageAnalyzer):
    """Python AST Metric Analyzer using built-in ast module."""

    @property
    def language_name(self) -> str:
        return "Python"

    @property
    def supported_extensions(self) -> List[str]:
        return [".py", ".pyw"]

    def _calc_function_complexity(self, func_node: ast.AST) -> int:
        """Calculates Cyclomatic Complexity for Python function/method."""
        cc = 1
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.IfExp, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler, ast.With, ast.AsyncWith, ast.Assert)):
                cc += 1
            elif isinstance(node, ast.BoolOp):
                # Each binary boolean operand adds a branch (e.g. A and B and C)
                cc += max(1, len(node.values) - 1)
        return cc

    def analyze_source(self, file_path: str, source_code: str) -> List[NormalizedMetric]:
        if not source_code.strip():
            return []

        results: List[NormalizedMetric] = []
        loc = compute_generic_loc(source_code, comment_prefix="#")
        
        # Package / directory module
        rel_dir = os.path.dirname(file_path)
        package_name = rel_dir.replace(os.sep, ".").replace("/", ".").strip(".") or "(root)"
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        
        try:
            tree = ast.parse(source_code, filename=file_path)
        except Exception:
            # Fallback regex if syntax error (e.g. partial file or version discrepancy)
            decisions = len(re.findall(r'\b(if|elif|while|for|except|assert)\b|\band\b|\bor\b', source_code))
            imports = set(re.findall(r'^\s*(?:import|from)\s+([\w\.]+)', source_code, re.MULTILINE))
            cc = 1 + decisions
            results.append(NormalizedMetric(
                class_name=f"{base_name}",
                package_name=package_name,
                file_path=file_path,
                language="Python",
                loc=loc,
                cyclomatic_complexity=cc,
                wmc=cc,
                cbo=len(imports),
                rfc=cc + len(imports),
                lcom=0.0
            ))
            return results

        # Extract file-level imports for CBO
        file_imports: Set[str] = set()
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    file_imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    file_imports.add(node.module.split('.')[0])

        # Extract classes
        class_defs = [n for n in ast.iter_child_nodes(tree) if isinstance(n, ast.ClassDef)]
        
        if not class_defs:
            # Module-level metrics for script or functional module
            functions = [n for n in ast.iter_child_nodes(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            func_complexities = [self._calc_function_complexity(f) for f in functions]
            
            top_level_cc = 1
            for n in ast.iter_child_nodes(tree):
                if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if isinstance(n, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith)):
                        top_level_cc += 1
            
            total_wmc = sum(func_complexities) + top_level_cc
            max_cc = max(func_complexities) if func_complexities else top_level_cc
            
            results.append(NormalizedMetric(
                class_name=f"{base_name}",
                package_name=package_name,
                file_path=file_path,
                language="Python",
                unit_type="module",
                loc=loc,
                cyclomatic_complexity=max(1, max_cc),
                wmc=max(1, total_wmc),
                cbo=len(file_imports),
                rfc=len(functions) + len(file_imports),
                lcom=0.0,
                num_methods=len(functions),
                num_fields=0,
                metric_availability={
                    "loc": True,
                    "cyclomatic_complexity": True,
                    "wmc": True,
                    "cbo": True,
                    "lcom": True,
                    "dit": False, # Non-OO script
                    "noc": False,
                    "rfc": True
                }
            ))
            return results

        for c_node in class_defs:
            c_name = c_node.name
            super_name = None
            if c_node.bases:
                first_base = c_node.bases[0]
                if isinstance(first_base, ast.Name):
                    super_name = first_base.id
                elif isinstance(first_base, ast.Attribute):
                    super_name = first_base.attr

            # Extract methods and attributes
            methods = [n for n in c_node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            method_complexities = [self._calc_function_complexity(m) for m in methods]
            
            # Field analysis (self.<attr>)
            fields: Set[str] = set()
            method_field_map: List[Set[str]] = []
            invoked_calls: Set[str] = set()
            
            for m in methods:
                m_fields: Set[str] = set()
                for sub in ast.walk(m):
                    if isinstance(sub, ast.Attribute) and isinstance(sub.value, ast.Name) and sub.value.id == 'self':
                        m_fields.add(sub.attr)
                        fields.add(sub.attr)
                    elif isinstance(sub, ast.Call):
                        if isinstance(sub.func, ast.Name):
                            invoked_calls.add(sub.func.id)
                        elif isinstance(sub.func, ast.Attribute):
                            invoked_calls.add(sub.func.attr)
                method_field_map.append(m_fields)

            # LCOM calculation (Lack of Cohesion of Methods)
            # Henderson-Sellers / classic metric: 1 - sum(|F_i|)/(|M|*|F|)
            m_count = len(methods)
            f_count = len(fields)
            if m_count <= 1 or f_count == 0:
                lcom_val = 0.0
            else:
                sum_mf = sum(len(mf) for mf in method_field_map)
                lcom_val = max(0.0, min(1.0, 1.0 - (sum_mf / (m_count * f_count))))

            total_wmc = sum(method_complexities) if method_complexities else 1
            max_cc = max(method_complexities) if method_complexities else 1
            public_methods = [m for m in methods if not m.name.startswith('_')]
            static_methods = [m for m in methods if any(isinstance(d, ast.Name) and d.id in ('staticmethod', 'classmethod') for d in m.decorator_list)]

            metric = NormalizedMetric(
                class_name=c_name,
                package_name=package_name,
                file_path=file_path,
                language="Python",
                unit_type="class",
                loc=loc,
                cyclomatic_complexity=max(1, max_cc),
                wmc=max(1, total_wmc),
                cbo=len(file_imports),
                rfc=m_count + len(invoked_calls),
                lcom=round(lcom_val, 4),
                dit=2 if super_name and super_name != 'object' else 1,
                noc=0,
                num_methods=m_count,
                num_fields=f_count,
                num_public_methods=len(public_methods),
                num_static_methods=len(static_methods),
                super_class=super_name,
                field_names=fields,
                methods_field_access=method_field_map,
                invoked_methods=invoked_calls,
                coupled_types=file_imports
            )
            results.append(metric)

        return results


class JavaScriptTypeScriptAnalyzer(LanguageAnalyzer):
    """JavaScript & TypeScript AST Metric Analyzer."""

    @property
    def language_name(self) -> str:
        return "JavaScript/TypeScript"

    @property
    def supported_extensions(self) -> List[str]:
        return [".js", ".jsx", ".ts", ".tsx", ".mjs"]

    def analyze_source(self, file_path: str, source_code: str) -> List[NormalizedMetric]:
        if not source_code.strip():
            return []

        results: List[NormalizedMetric] = []
        loc = compute_generic_loc(source_code, comment_prefix="//")
        
        rel_dir = os.path.dirname(file_path)
        package_name = rel_dir.replace(os.sep, ".").replace("/", ".").strip(".") or "(root)"
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        ext = os.path.splitext(file_path)[1].lower()
        lang = "TypeScript" if ext in (".ts", ".tsx") else "JavaScript"

        # Imports extraction for CBO
        imports = set(re.findall(r'(?:import|from|require\()\s*[\'"]([^\'"]+)[\'"]', source_code))
        cbo = len(imports)

        # Decision constructs for CC
        decisions = len(re.findall(r'\b(if|else\s+if|for|while|do|case|catch)\b|\?\?|&&|\|\||\?[^:]+:', source_code))
        
        # Classes in JS/TS
        class_matches = re.findall(r'class\s+([A-Za-z0-9_$]+)(?:\s+extends\s+([A-Za-z0-9_$]+))?', source_code)
        
        if not class_matches:
            # Module / Functional Component representation
            functions = re.findall(r'(?:function\s+([A-Za-z0-9_$]+)|(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)', source_code)
            num_funcs = max(1, len(functions))
            cc = 1 + decisions
            
            results.append(NormalizedMetric(
                class_name=base_name,
                package_name=package_name,
                file_path=file_path,
                language=lang,
                unit_type="component" if ext in (".jsx", ".tsx") else "module",
                loc=loc,
                cyclomatic_complexity=max(1, cc // num_funcs),
                wmc=max(1, cc),
                cbo=cbo,
                rfc=num_funcs + cbo,
                lcom=0.0,
                num_methods=num_funcs,
                coupled_types=imports,
                metric_availability={
                    "loc": True,
                    "cyclomatic_complexity": True,
                    "wmc": True,
                    "cbo": True,
                    "lcom": True,
                    "dit": False,
                    "noc": False,
                    "rfc": True
                }
            ))
            return results

        for c_match in class_matches:
            c_name = c_match[0]
            super_name = c_match[1] if c_match[1] else None
            
            # Approximate methods in class
            methods = re.findall(r'(?:async\s+)?([A-Za-z0-9_$]+)\s*\([^)]*\)\s*\{', source_code)
            num_methods = max(1, len(methods))
            
            # Fields: this.<field>
            fields = set(re.findall(r'this\.([A-Za-z0-9_$]+)', source_code))
            
            cc = 1 + decisions
            wmc = max(1, cc)
            
            # Simplified LCOM
            lcom_val = 0.0 if num_methods <= 1 or not fields else 0.5
            
            results.append(NormalizedMetric(
                class_name=c_name,
                package_name=package_name,
                file_path=file_path,
                language=lang,
                unit_type="class",
                loc=loc,
                cyclomatic_complexity=max(1, cc // num_methods),
                wmc=wmc,
                cbo=cbo,
                rfc=num_methods + cbo,
                lcom=round(lcom_val, 4),
                dit=2 if super_name else 1,
                super_class=super_name,
                num_methods=num_methods,
                num_fields=len(fields),
                coupled_types=imports
            ))

        return results


class AnalyzerRegistry:
    """Registry coordinating language-specific analyzers."""
    
    def __init__(self):
        self._analyzers: List[LanguageAnalyzer] = [
            JavaAnalyzer(),
            PythonAnalyzer(),
            JavaScriptTypeScriptAnalyzer()
        ]
        self._extension_map: Dict[str, LanguageAnalyzer] = {}
        for analyzer in self._analyzers:
            for ext in analyzer.supported_extensions:
                self._extension_map[ext.lower()] = analyzer

    def register(self, analyzer: LanguageAnalyzer):
        self._analyzers.append(analyzer)
        for ext in analyzer.supported_extensions:
            self._extension_map[ext.lower()] = analyzer

    def get_analyzer(self, file_path: str) -> Optional[LanguageAnalyzer]:
        ext = os.path.splitext(file_path)[1].lower()
        return self._extension_map.get(ext)

    def is_supported(self, file_path: str) -> bool:
        return self.get_analyzer(file_path) is not None

    def get_supported_extensions(self) -> Set[str]:
        return set(self._extension_map.keys())

    def get_supported_languages(self) -> List[str]:
        return [a.language_name for a in self._analyzers]

    def analyze_repository(self, repo_dir: str, file_list: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Scans and extracts normalized metrics across all supported languages in the repository.
        Normalizes all file paths relative to repo_dir.
        """
        all_metrics: List[NormalizedMetric] = []
        scanned_files_by_lang: Dict[str, int] = {}
        analyzers_used: Set[str] = set()

        if file_list is not None:
            files_to_scan = file_list
        else:
            files_to_scan = []
            for root, _, files in os.walk(repo_dir):
                if any(ignored in root for ignored in ('.git', 'node_modules', '.venv', 'venv', '__pycache__', 'target', 'build', 'dist')):
                    continue
                for f in files:
                    full_p = os.path.join(root, f)
                    if self.is_supported(full_p):
                        files_to_scan.append(full_p)

        for f_path in files_to_scan:
            analyzer = self.get_analyzer(f_path)
            if not analyzer:
                continue
            
            analyzers_used.add(analyzer.language_name)
            scanned_files_by_lang[analyzer.language_name] = scanned_files_by_lang.get(analyzer.language_name, 0) + 1
            
            metrics = analyzer.analyze_file(f_path)
            for m in metrics:
                # Normalize file path to relative repository path
                try:
                    rel_p = os.path.relpath(m.file_path, repo_dir).replace('\\', '/')
                    m.file_path = rel_p
                except Exception:
                    m.file_path = os.path.basename(m.file_path)
            all_metrics.extend(metrics)

        # Cross-class inheritance computation (NOC and DIT tree resolution)
        class_map = {m.class_name: m for m in all_metrics}
        for m in all_metrics:
            if m.super_class and m.super_class in class_map:
                class_map[m.super_class].noc += 1
                depth = 1
                curr = m
                visited = set()
                while curr.super_class and curr.super_class in class_map and curr.super_class not in visited:
                    visited.add(curr.class_name)
                    depth += 1
                    curr = class_map[curr.super_class]
                m.dit = depth

        total_units = len(all_metrics)
        packages = {m.package_name for m in all_metrics}
        total_loc = sum(m.loc for m in all_metrics)
        total_methods = sum(m.num_methods for m in all_metrics)
        total_fields = sum(m.num_fields for m in all_metrics)

        # Unit type breakdown
        units_by_type = {
            "classes": sum(1 for m in all_metrics if getattr(m, 'unit_type', 'class') == 'class'),
            "modules": sum(1 for m in all_metrics if getattr(m, 'unit_type', 'class') == 'module'),
            "components": sum(1 for m in all_metrics if getattr(m, 'unit_type', 'class') == 'component')
        }

        project_summary = {
            "total_files": len(files_to_scan),
            "total_classes": total_units,
            "units_by_type": units_by_type,
            "total_packages": len(packages),
            "total_loc": total_loc,
            "avg_loc": round(total_loc / max(1, total_units), 2),
            "avg_wmc": round(sum(m.wmc for m in all_metrics) / max(1, total_units), 2),
            "avg_cbo": round(sum(m.cbo for m in all_metrics) / max(1, total_units), 2),
            "avg_rfc": round(sum(m.rfc for m in all_metrics) / max(1, total_units), 2),
            "avg_lcom": round(sum(m.lcom for m in all_metrics) / max(1, total_units), 4),
            "avg_dit": round(sum(m.dit for m in all_metrics) / max(1, total_units), 2),
            "avg_noc": round(sum(m.noc for m in all_metrics) / max(1, total_units), 2),
            "avg_complexity": round(sum(m.cyclomatic_complexity for m in all_metrics) / max(1, total_units), 2),
            "total_methods": total_methods,
            "total_fields": total_fields,
            "scanned_files_by_lang": scanned_files_by_lang,
            "analyzers_used": list(analyzers_used)
        }

        return {
            "classes": [m.to_dict() for m in all_metrics],
            "project": project_summary,
            "detected_languages": scanned_files_by_lang,
            "analyzers_used": list(analyzers_used)
        }


# Global default registry instance
default_registry = AnalyzerRegistry()
