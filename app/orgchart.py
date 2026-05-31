from __future__ import annotations

import html
import re
from collections import defaultdict, deque

from .schemas import Edge, Node, OrgChart


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "nodo"


def infer_org_chart_from_text(text: str) -> OrgChart:
    raw = text.replace("\n", " ")
    parts = re.split(r"[\.;]", raw)

    nodes_by_name: dict[str, Node] = {}
    edges: list[Edge] = []

    patterns = [
        re.compile(r"(?P<child>[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ ]{1,60})\\s+reporta\\s+a\\s+(?P<manager>[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ ]{1,60})", re.IGNORECASE),
        re.compile(r"(?P<child>[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ ]{1,60})\\s+depende\\s+de\\s+(?P<manager>[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ ]{1,60})", re.IGNORECASE),
        re.compile(r"(?P<manager>[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ ]{1,60})\\s+lidera\\s+a\\s+(?P<child>[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ ]{1,60})", re.IGNORECASE),
    ]

    def get_or_create(name: str) -> Node:
        clean_name = re.sub(r"\\s+", " ", name).strip()
        key = clean_name.lower()
        if key not in nodes_by_name:
            node_id = slugify(clean_name)
            if any(node.id == node_id for node in nodes_by_name.values()):
                node_id = f"{node_id}_{len(nodes_by_name) + 1}"
            nodes_by_name[key] = Node(id=node_id, name=clean_name, title="")
        return nodes_by_name[key]

    for part in parts:
        sentence = part.strip()
        if not sentence:
            continue
        for pattern in patterns:
            match = pattern.search(sentence)
            if not match:
                continue

            child = get_or_create(match.group("child"))
            manager = get_or_create(match.group("manager"))

            relation = Edge.model_validate({"from": manager.id, "to": child.id, "label": "reporta"})
            exists = any(e.from_id == relation.from_id and e.to_id == relation.to_id for e in edges)
            if not exists:
                edges.append(relation)

    if not nodes_by_name:
        # Fallback: build a simple three-level template so the user can editarlo.
        nodes = [
            Node(id="direccion_general", name="Dirección General", title=""),
            Node(id="gerencia_1", name="Gerencia 1", title=""),
            Node(id="gerencia_2", name="Gerencia 2", title=""),
        ]
        edges = [
            Edge.model_validate({"from": "direccion_general", "to": "gerencia_1", "label": "reporta"}),
            Edge.model_validate({"from": "direccion_general", "to": "gerencia_2", "label": "reporta"}),
        ]
        return OrgChart(nodes=nodes, edges=edges)

    return OrgChart(nodes=list(nodes_by_name.values()), edges=edges)


def _level_by_node(nodes: list[Node], edges: list[Edge]) -> dict[str, int]:
    incoming = defaultdict(int)
    outgoing = defaultdict(list)

    for node in nodes:
        incoming[node.id] = 0

    for edge in edges:
        incoming[edge.to_id] += 1
        outgoing[edge.from_id].append(edge.to_id)

    roots = [node.id for node in nodes if incoming[node.id] == 0]
    if not roots:
        roots = [nodes[0].id]

    levels: dict[str, int] = {root: 0 for root in roots}
    queue = deque(roots)

    while queue:
        current = queue.popleft()
        for child in outgoing[current]:
            candidate = levels[current] + 1
            if child not in levels or candidate > levels[child]:
                levels[child] = candidate
            queue.append(child)

    for node in nodes:
        levels.setdefault(node.id, 0)

    return levels


def to_drawio_xml(org_chart: OrgChart, diagram_name: str = "Organigrama") -> str:
    nodes = org_chart.nodes
    edges = org_chart.edges

    levels = _level_by_node(nodes, edges)
    grouped: dict[int, list[Node]] = defaultdict(list)
    for node in nodes:
        grouped[levels[node.id]].append(node)

    node_positions: dict[str, tuple[int, int]] = {}
    x_spacing = 240
    y_spacing = 140

    for level, level_nodes in sorted(grouped.items(), key=lambda item: item[0]):
        for idx, node in enumerate(level_nodes):
            node_positions[node.id] = (40 + idx * x_spacing, 40 + level * y_spacing)

    xml_cells = [
        '<mxCell id="0"/>',
        '<mxCell id="1" parent="0"/>',
    ]

    for node in nodes:
        x, y = node_positions[node.id]
        label = html.escape(node.name)
        if node.title:
            label = f"{label}&#xa;<font color=\"#666666\">{html.escape(node.title)}</font>"

        xml_cells.append(
            (
                f'<mxCell id="{html.escape(node.id)}" value="{label}" '
                'style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF4E6;strokeColor=#C2410C;fontSize=14;" '
                'vertex="1" parent="1">'
                f'<mxGeometry x="{x}" y="{y}" width="180" height="74" as="geometry"/>'
                '</mxCell>'
            )
        )

    for idx, edge in enumerate(edges, start=1):
        edge_id = f"edge_{idx}"
        label = html.escape(edge.label)
        xml_cells.append(
            (
                f'<mxCell id="{edge_id}" value="{label}" '
                'style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;" '
                f'edge="1" parent="1" source="{html.escape(edge.from_id)}" target="{html.escape(edge.to_id)}">'
                '<mxGeometry relative="1" as="geometry"/>'
                '</mxCell>'
            )
        )

    inner = "".join(xml_cells)
    escaped_name = html.escape(diagram_name)

    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<mxfile host="app.diagrams.net" modified="2026-01-01T00:00:00.000Z" agent="Organigrama-System" version="24.7.17">'
        f'<diagram name="{escaped_name}" id="diagram_1">'
        '<mxGraphModel dx="1460" dy="880" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">'
        f'<root>{inner}</root>'
        '</mxGraphModel>'
        '</diagram>'
        '</mxfile>'
    )
