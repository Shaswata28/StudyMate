const diagramHeader = /^(?:(?:flowchart|graph)\s+(?:TD|TB|BT|LR|RL)|sequenceDiagram)\b/;

export class DiagramSyntaxError extends Error {}

export function isMermaidDiagram(code: string) {
  return diagramHeader.test(code.trimStart());
}

export async function renderDiagram(id: string, code: string) {
  const source = code.trim();
  if (!isMermaidDiagram(source) || source.length > 12000 ||
      /%%\{|@\{|^\s*(?:click|links?|properties|details)\s|<|!\[|\burl\s*\(/im.test(source)) {
    throw new Error("Enter a supported diagram without interactive or external content.");
  }
  const { default: mermaid } = await import("mermaid");
  mermaid.initialize({ startOnLoad: false, securityLevel: "strict", htmlLabels: false, suppressErrorRendering: true });
  try {
    await mermaid.parse(source);
  } catch (error) {
    throw new DiagramSyntaxError(error instanceof Error ? error.message : String(error));
  }
  const result = await mermaid.render(id, source);
  const svg = new DOMParser().parseFromString(result.svg, "image/svg+xml").documentElement;
  const [, , width, height] = (svg.getAttribute("viewBox") ?? "").split(/\s+/).map(Number);
  if (width > 0 && height > 0) {
    svg.setAttribute("width", String(Math.ceil(width)));
    svg.setAttribute("height", String(Math.ceil(height)));
  }
  return new XMLSerializer().serializeToString(svg);
}
