import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import * as XLSX from "xlsx";

export const exportToExcel = (displayResults: any[], visibleFields: any, getFieldLabel: (f: string) => string, partId: string) => {
  if (displayResults.length === 0) return;

  const dataToExport = displayResults.map((res: any) => {
    const row: any = {};
    // Lista de campos que SEMPRE devem ser exportados para o Excel, mesmo se ocultos na UI
    const mandatoryFields = ["referencias", "ficha_tecnica"];
    
    // Unifica os campos visíveis com os obrigatórios para a exportação
    const fieldsToExport = new Set([...Object.keys(visibleFields).filter(k => visibleFields[k]), ...mandatoryFields]);

    fieldsToExport.forEach((field) => {
      const label = getFieldLabel(field);
      
      if (field === "ano") {
        row[`${label} Início`] = res.ano_inicio || "---";
        row[`${label} Fim`] = res.ano_fim || "---";
      } else if (field === "referencias") {
        // Tratamento especial para referências no Excel
        const refs = res.referencias;
        if (typeof refs === "string") {
          row[label] = refs.replace(/\|/g, " | ");
        } else if (Array.isArray(refs)) {
          row[label] = refs.join(" | ");
        } else {
          row[label] = refs || "---";
        }
      } else if (field === "imagens" || field === "imagem") {
        row[label] = res.imagens ? res.imagens.join(", ") : res.imagem || "";
      } else {
        row[label] = res[field] || "---";
      }
    });
    return row;
  });

  const worksheet = XLSX.utils.json_to_sheet(dataToExport);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "Resultados");

  const filename = `busca_${displayResults[0]?.codigo || partId || "peca"}_${new Date().toISOString().split("T")[0]}.xlsx`;
  XLSX.writeFile(workbook, filename);
};

export const exportToPdf = (displayResults: any[], results: any[], visibleFields: any, uniqueReferences: any, partId: string, columnConfig: any[]) => {
  if (displayResults.length === 0) return;

  const doc = new jsPDF("l", "pt", "a4");
  const pageWidth = doc.internal.pageSize.getWidth();
  let currentY = 40;

  // 1. TÍTULO PRINCIPAL
  doc.setFontSize(16);
  doc.setFont("helvetica", "bold");
  const title = `Relatório de Aplicações - ${results[0]?.codigo || partId || "Busca"}`;
  doc.text(title, 40, currentY);
  currentY += 20;

  // 2. RESUMO DE REFERÊNCIAS OE
  if (Object.keys(uniqueReferences).length > 0) {
    doc.setFontSize(9);
    doc.setFont("helvetica", "bold");
    doc.text("REFERENCIAS DE SIMILARES:", 40, currentY);
    currentY += 12;

    doc.setFont("helvetica", "normal");
    doc.setFontSize(8);
    
    const manufacturersInResults = new Set(
      results.map(r => r.veiculo?.toUpperCase().trim()).filter(v => !!v)
    );

    const sortedBrands = Object.entries(uniqueReferences).sort(([brandA], [brandB]) => {
      const isPriorityA = brandA === "ORIGINAL" || brandA === "OEM" || manufacturersInResults.has(brandA);
      const isPriorityB = brandB === "ORIGINAL" || brandB === "OEM" || manufacturersInResults.has(brandB);
      
      if (isPriorityA && !isPriorityB) return -1;
      if (!isPriorityA && isPriorityB) return 1;
      return brandA.localeCompare(brandB);
    });

    let refLines: string[] = [];
    sortedBrands.forEach(([brand, codes]) => {
      const codesList = Array.from(codes as Set<string>).sort().join(" - ");
      refLines.push(`${brand}: ${codesList}`);
    });

    const refText = refLines.join("  |  ");
    const splitRefs = doc.splitTextToSize(refText, pageWidth - 80);
    doc.text(splitRefs, 40, currentY);
    currentY += (splitRefs.length * 10) + 10;
  }

  // 3. TABELA DE RESULTADOS
  const headers = columnConfig
    .filter((col) => visibleFields[col.id])
    .map((col) => col.getHeader());

  const rows = displayResults.map((res: any) => 
    columnConfig
      .filter((col) => visibleFields[col.id])
      .map((col) => {
        if (col.id === "imagens" || col.id === "imagem" || col.id === "ficha_tecnica") {
           return "---";
        }
        if (col.id === "ano") {
           return res.ano_inicio || res.ano_fim ? `${res.ano_inicio || ""}...${res.ano_fim || ""}` : "---";
        }
        return res[col.id] || "---";
      })
  );

  autoTable(doc, {
    startY: currentY,
    head: [headers],
    body: rows,
    theme: "grid",
    styles: { fontSize: 7, cellPadding: 3 },
    headStyles: { fillColor: [37, 99, 235] },
    margin: { left: 40, right: 40 },
  });

  const filename = `busca_${results[0]?.codigo || partId || "peca"}_${new Date().toISOString().split("T")[0]}.pdf`;
  doc.save(filename);
};
