mermaid.initialize({ startOnLoad: false, theme: "default" });

const statusEl = document.querySelector("#status");
const transcriptEl = document.querySelector("#transcript");
const chartJsonEl = document.querySelector("#chartJson");
const diagramEl = document.querySelector("#diagram");
const uploadForm = document.querySelector("#uploadForm");

const addNodeBtn = document.querySelector("#addNodeBtn");
const addEdgeBtn = document.querySelector("#addEdgeBtn");
const renderBtn = document.querySelector("#renderBtn");
const exportBtn = document.querySelector("#exportBtn");

const state = {
  chart: {
    nodes: [
      { id: "direccion_general", name: "Dirección General", title: "" },
      { id: "gerencia_1", name: "Gerencia 1", title: "" },
      { id: "gerencia_2", name: "Gerencia 2", title: "" },
    ],
    edges: [
      { from: "direccion_general", to: "gerencia_1", label: "reporta" },
      { from: "direccion_general", to: "gerencia_2", label: "reporta" },
    ],
  },
};

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.style.color = isError ? "#b91c1c" : "#5f4a39";
}

function normalizeId(value) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "") || "nodo";
}

function refreshJson() {
  chartJsonEl.value = JSON.stringify(state.chart, null, 2);
}

function syncFromJson() {
  try {
    const parsed = JSON.parse(chartJsonEl.value);
    if (!Array.isArray(parsed.nodes) || !Array.isArray(parsed.edges)) {
      throw new Error("El JSON debe tener arrays nodes y edges");
    }

    state.chart = {
      nodes: parsed.nodes.map((n) => ({
        id: String(n.id || "").trim(),
        name: String(n.name || "").trim(),
        title: String(n.title || "").trim(),
      })),
      edges: parsed.edges.map((e) => ({
        from: String(e.from || "").trim(),
        to: String(e.to || "").trim(),
        label: String(e.label || "").trim(),
      })),
    };
    return true;
  } catch (error) {
    setStatus(`JSON inválido: ${error.message}`, true);
    return false;
  }
}

function chartToMermaid(chart) {
  const nodeAlias = new Map();

  const lines = ["flowchart TD"];
  chart.nodes.forEach((node, idx) => {
    const alias = `N${idx + 1}`;
    nodeAlias.set(node.id, alias);
    const title = node.title ? `<br/><span style='font-size:12px;color:#555'>${node.title}</span>` : "";
    const safeLabel = (node.name || node.id).replace(/\"/g, "'");
    lines.push(`  ${alias}[\"${safeLabel}${title}\"]`);
  });

  chart.edges.forEach((edge) => {
    const from = nodeAlias.get(edge.from);
    const to = nodeAlias.get(edge.to);
    if (!from || !to) {
      return;
    }
    const label = edge.label ? `|${edge.label.replace(/\|/g, "/")}|` : "";
    lines.push(`  ${from} -->${label} ${to}`);
  });

  return lines.join("\n");
}

async function renderChart() {
  if (!syncFromJson()) {
    return;
  }

  const mermaidDef = chartToMermaid(state.chart);
  const renderId = `chart_${Date.now()}`;
  try {
    const { svg } = await mermaid.render(renderId, mermaidDef);
    diagramEl.innerHTML = svg;
    setStatus("Organigrama renderizado");
  } catch (error) {
    setStatus(`Error al renderizar: ${error.message}`, true);
  }
}

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const fileInput = document.querySelector("#fileInput");
  const modelSize = document.querySelector("#modelSize").value;
  const file = fileInput.files[0];

  if (!file) {
    setStatus("Selecciona un archivo primero", true);
    return;
  }

  const formData = new FormData();
  formData.append("file", file);
  formData.append("model_size", modelSize);

  setStatus("Procesando archivo... esto puede tardar unos minutos");

  try {
    const response = await fetch("/api/transcribe", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorBody = await response.json();
      throw new Error(errorBody.detail || "No se pudo procesar el archivo");
    }

    const data = await response.json();
    transcriptEl.value = data.transcript;
    state.chart = data.org_chart;
    refreshJson();
    await renderChart();
    setStatus("Transcripción y organigrama generados");
  } catch (error) {
    setStatus(`Error: ${error.message}`, true);
  }
});

addNodeBtn.addEventListener("click", () => {
  if (!syncFromJson()) {
    return;
  }

  const id = normalizeId(document.querySelector("#nodeId").value);
  const name = document.querySelector("#nodeName").value.trim();
  const title = document.querySelector("#nodeTitle").value.trim();

  if (!name) {
    setStatus("El nombre del nodo es obligatorio", true);
    return;
  }

  const exists = state.chart.nodes.some((node) => node.id === id);
  if (exists) {
    setStatus("Ya existe un nodo con ese id", true);
    return;
  }

  state.chart.nodes.push({ id, name, title });
  refreshJson();
  setStatus("Nodo agregado");
});

addEdgeBtn.addEventListener("click", () => {
  if (!syncFromJson()) {
    return;
  }

  const from = document.querySelector("#edgeFrom").value.trim();
  const to = document.querySelector("#edgeTo").value.trim();
  const label = document.querySelector("#edgeLabel").value.trim() || "reporta";

  if (!from || !to) {
    setStatus("Completa from y to", true);
    return;
  }

  const fromExists = state.chart.nodes.some((node) => node.id === from);
  const toExists = state.chart.nodes.some((node) => node.id === to);

  if (!fromExists || !toExists) {
    setStatus("Los nodos from/to deben existir", true);
    return;
  }

  state.chart.edges.push({ from, to, label });
  refreshJson();
  setStatus("Relación agregada");
});

renderBtn.addEventListener("click", () => {
  renderChart();
});

exportBtn.addEventListener("click", async () => {
  if (!syncFromJson()) {
    return;
  }

  try {
    const response = await fetch("/api/export/drawio?name=organigrama", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(state.chart),
    });

    if (!response.ok) {
      throw new Error("No se pudo exportar el archivo");
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "organigrama.drawio";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);

    setStatus("Archivo draw.io exportado");
  } catch (error) {
    setStatus(`Error de exportación: ${error.message}`, true);
  }
});

refreshJson();
renderChart();
