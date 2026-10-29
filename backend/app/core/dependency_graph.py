import logging
from typing import Dict, List, Set, Optional, Any
import networkx as nx
from javalang.tree import (
    ClassDeclaration,
    InterfaceDeclaration,
    FieldDeclaration,
    MethodDeclaration,
    ConstructorDeclaration,
    Creator,
    ReferenceType,
)
from app.models.schemas import (
    DependencyGraphNode,
    DependencyGraphEdge,
    DependencyGraphResponse,
    MetricVector,
)

logger = logging.getLogger("software_dna.graph")


import ast
from pathlib import Path


class DependencyGraphEngine:
    """
    Maintains an incremental NetworkX class dependency graph across commits.
    Preserves unchanged nodes and selectively rebuilds edges for modified classes.
    """

    def __init__(self):
        self.graph = nx.DiGraph()

    def update_graph(
        self,
        ast_map: Dict[str, Any],
        metrics_map: Dict[str, MetricVector],
        changed_files: List[str],
        commit_sha: str,
        version_label: str = "V1",
    ) -> DependencyGraphResponse:
        """
        Incrementally updates the class dependency graph.
        """
        # Step 1: Identify all classes across ASTs
        class_to_file: Dict[str, str] = {}
        class_to_package: Dict[str, str] = {}
        class_ast_nodes: Dict[str, Any] = {}

        for file_path, tree in ast_map.items():
            if not tree:
                continue

            if isinstance(tree, ast.Module):
                pkg_name = ".".join(Path(file_path).parts[:-1]) or "root"
                for node in tree.body:
                    if isinstance(node, ast.ClassDef):
                        class_to_file[node.name] = file_path
                        class_to_package[node.name] = pkg_name
                        class_ast_nodes[node.name] = node
                continue

            if hasattr(tree, "types"):
                package_name = tree.package.name if tree.package else "default"
                for type_decl in tree.types:
                    if isinstance(type_decl, (ClassDeclaration, InterfaceDeclaration)):
                        class_name = type_decl.name
                        class_to_file[class_name] = file_path
                        class_to_package[class_name] = package_name
                        class_ast_nodes[class_name] = type_decl

        # Step 2: Determine which classes were modified
        changed_classes: Set[str] = set()
        for class_name, f_path in class_to_file.items():
            if f_path in changed_files:
                changed_classes.add(class_name)

        # Step 3: Ensure all current classes exist as nodes
        for class_name, type_decl in class_ast_nodes.items():
            f_path = class_to_file[class_name]
            pkg = class_to_package[class_name]
            m = metrics_map.get(class_name)
            is_changed = class_name in changed_classes or (not self.graph.has_node(class_name))

            self.graph.add_node(
                class_name,
                label=class_name,
                package=pkg,
                file_path=f_path,
                commit_sha=commit_sha,
                metrics=m,
                is_changed=is_changed,
            )

        # Step 4: For modified classes, clear outgoing edges and re-extract dependencies
        for class_name in changed_classes:
            type_decl = class_ast_nodes.get(class_name)
            if not type_decl:
                continue

            # Remove existing outgoing edges for this modified class
            existing_out_edges = list(self.graph.out_edges(class_name))
            self.graph.remove_edges_from(existing_out_edges)

            # Re-extract dependencies
            dependencies = self._extract_dependencies(type_decl, set(class_ast_nodes.keys()))

            for target_class, dep_type in dependencies.items():
                if target_class != class_name and target_class in class_ast_nodes:
                    # Check if this edge was just introduced
                    self.graph.add_edge(
                        class_name,
                        target_class,
                        dependency_type=dep_type,
                        introduced_commit=commit_sha,
                        active=True,
                        is_new=(commit_sha != "initial"),
                    )

        logger.info(
            f"[GRAPH] Nodes: {self.graph.number_of_nodes()} | Edges: {self.graph.number_of_edges()} | "
            f"Updated Nodes: {len(changed_classes)}"
        )

        return self.to_schema_response(changed_classes)

    def _extract_dependencies(
        self,
        class_node: Any,
        known_classes: Set[str],
    ) -> Dict[str, str]:
        """
        Detects: inheritance, interface implementation, field types, parameter types, object creators.
        """
        deps: Dict[str, str] = {}

        if isinstance(class_node, ast.ClassDef):
            for base in class_node.bases:
                if isinstance(base, ast.Name) and base.id in known_classes:
                    deps[base.id] = "inheritance"
            for node in ast.walk(class_node):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in known_classes:
                    deps[node.func.id] = "instantiation"
            return deps

        # Java AST
        if isinstance(class_node, ClassDeclaration) and class_node.extends:
            ext_name = class_node.extends.name
            if ext_name in known_classes:
                deps[ext_name] = "inheritance"

        if isinstance(class_node, ClassDeclaration) and class_node.implements:
            for impl in class_node.implements:
                if impl.name in known_classes:
                    deps[impl.name] = "implementation"

        if hasattr(class_node, "fields"):
            for field in class_node.fields:
                if field.type and field.type.name in known_classes:
                    deps[field.type.name] = "field_dependency"

        if hasattr(class_node, "methods"):
            for method in class_node.methods:
                if method.return_type and method.return_type.name in known_classes:
                    deps[method.return_type.name] = "method_return"
                for param in method.parameters:
                    if param.type and param.type.name in known_classes:
                        deps[param.type.name] = "parameter_dependency"

        for _, creator in class_node.filter(Creator):
            if creator.type and creator.type.name in known_classes:
                deps[creator.type.name] = "instantiation"

        return deps

    def to_schema_response(self, changed_classes: Optional[Set[str]] = None) -> DependencyGraphResponse:
        """Converts internal NetworkX graph to frontend-ready Pydantic schema."""
        changed_classes = changed_classes or set()
        nodes: List[DependencyGraphNode] = []
        edges: List[DependencyGraphEdge] = []

        for node_id, data in self.graph.nodes(data=True):
            nodes.append(
                DependencyGraphNode(
                    id=node_id,
                    label=data.get("label", node_id),
                    package=data.get("package", "default"),
                    file_path=data.get("file_path", ""),
                    commit_sha=data.get("commit_sha", ""),
                    metrics=data.get("metrics"),
                    is_changed=node_id in changed_classes or data.get("is_changed", False),
                )
            )

        for u, v, data in self.graph.edges(data=True):
            edges.append(
                DependencyGraphEdge(
                    source=u,
                    target=v,
                    dependency_type=data.get("dependency_type", "reference"),
                    introduced_commit=data.get("introduced_commit", ""),
                    active=data.get("active", True),
                    is_new=data.get("is_new", False),
                )
            )

        return DependencyGraphResponse(
            nodes=nodes,
            edges=edges,
            total_nodes=len(nodes),
            total_edges=len(edges),
        )
