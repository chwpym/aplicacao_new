

// Helper para traduzir chaves internas para rótulos em maiúsculas de cabeçalho
const getHeaderLabel = (key: string): string => {
  const labels: Record<string, string> = {
    marca: "MARCA",
    codigo: "CÓDIGO",
    veiculo: "VEÍCULO",
    modelo: "MODELO",
    versao: "VERSÃO",
    motor: "MOTOR",
    configuracao_motor: "CONF. MOTOR",
    combustivel: "COMBUSTÍVEL",
    posicao: "POSIÇÃO",
    lado: "LADO",
    direcao: "DIREÇÃO",
    sistema_freio: "SIST. FREIO",
    restricao: "RESTRIÇÃO",
    apenas: "APENAS",
    ano: "ANO",
    referencias: "REFERÊNCIAS",
    observacao: "OBSERVAÇÃO"
  };
  return labels[key] || key.toUpperCase();
};

const columnFixedWidths: Record<string, number> = {
  marca: 12,
  codigo: 15,
  veiculo: 12,
  modelo: 24,
  versao: 20,
  motor: 8,
  configuracao_motor: 12,
  combustivel: 11,
  posicao: 10,
  lado: 8,
  direcao: 8,
  sistema_freio: 12,
  restricao: 15,
  apenas: 12,
  ano: 11,
  referencias: 25,
  observacao: 25
};

const formatValueToWidth = (val: string, width: number): string => {
  const cleanVal = val.trim();
  if (cleanVal.length > width) {
    return cleanVal.substring(0, width);
  }
  return cleanVal.padEnd(width);
};

const getProportionalWidth = (text: string, fontName: string, fontSize: number): number => {
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  if (!ctx) return text.length * 8; // Aproximação de fallback
  ctx.font = `${fontSize}pt "${fontName}"`;
  return ctx.measureText(text).width;
};

const padProportional = (
  text: string,
  targetPhysicalWidth: number,
  fontName: string,
  fontSize: number
): string => {
  const cleanVal = text.trim();
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  if (!ctx) return cleanVal.padEnd(Math.ceil(targetPhysicalWidth / 8)); // Fallback
  
  ctx.font = `${fontSize}pt "${fontName}"`;
  const valWidth = ctx.measureText(cleanVal).width;
  
  if (valWidth >= targetPhysicalWidth) {
    // Se o valor for maior que a largura física alvo, cortamos caractere por caractere
    let truncated = cleanVal;
    while (truncated.length > 0 && ctx.measureText(truncated).width > targetPhysicalWidth) {
      truncated = truncated.slice(0, -1);
    }
    return truncated;
  }
  
  // Calcula o número de espaços necessários para preencher a largura física alvo
  const spaceWidth = ctx.measureText(" ").width;
  const missingWidth = targetPhysicalWidth - valWidth;
  const numSpaces = Math.round(missingWidth / spaceWidth);
  
  return cleanVal + " ".repeat(numSpaces);
};

export const copyToClipboardTable = (
  results: any[],
  visibleFields: any,
  automakers: string[],
  uniqueReferences: Record<string, Set<string>>,
  formatType: "grade" | "limpa" | "tabulado" = "grade",
  agrupar: boolean = true,
  erpFont: string = "monospace",
  erpFontSize: number = 9,
  hideDashesRow: boolean = false
) => {
  if (results.length === 0) return;

  const compareResults = (a: any, b: any) => {
    const priority = [
      "marca", "veiculo", "modelo", "versao", "motor",
      "configuracao_motor", "combustivel", "posicao", "lado", "ano_inicio",
    ];

    for (const field of priority) {
      const visibilityKey = field === "ano_inicio" ? "ano" : field;
      if (visibleFields[visibilityKey]) {
        const valA = String(a[field] || "").trim();
        const valB = String(b[field] || "").trim();
        if (valA !== valB) {
          if (field === "ano_inicio") {
            return (Number(a[field]) || 0) - (Number(b[field]) || 0);
          }
          return valA.localeCompare(valB);
        }
      }
    }
    return 0;
  };

  // Sempre ordena antes de copiar, seguindo a lógica da tela
  const sortedResults = [...results].sort(compareResults);

  // Ordem de campos baseada nas colunas
  const orderedKeys = [
    "marca", "codigo", "veiculo", "modelo", "versao", "motor", "configuracao_motor",
    "combustivel", "posicao", "lado", "direcao", "sistema_freio",
    "restricao", "apenas"
  ];

  const activeKeys: string[] = [];
  orderedKeys.forEach(key => {
    if (visibleFields[key]) {
      activeKeys.push(key);
    }
  });
  if (visibleFields.ano) {
    activeKeys.push("ano");
  }
  if (visibleFields.referencias) {
    activeKeys.push("referencias");
  }
  if (visibleFields.observacao) {
    activeKeys.push("observacao");
  }

  if (activeKeys.length === 0) return;

  // Consolidar por agrupamento, se ativado
  let finalResults = [...sortedResults];

  if (agrupar) {
    const keysForGrouping = activeKeys.filter(k => k !== "ano");
    const groups: Record<string, { baseRow: any; starts: any[]; ends: any[] }> = {};

    finalResults.forEach(res => {
      const keyParts = keysForGrouping.map(key => String(res[key] || "").trim());
      const groupKey = keyParts.join("||") || "default";

      if (!groups[groupKey]) {
        groups[groupKey] = {
          baseRow: { ...res },
          starts: [],
          ends: []
        };
      }
      if (res.ano_inicio !== null && res.ano_inicio !== undefined && res.ano_inicio !== "") {
        groups[groupKey].starts.push(res.ano_inicio);
      }
      if (res.ano_fim !== null && res.ano_fim !== undefined && res.ano_fim !== "") {
        groups[groupKey].ends.push(res.ano_fim);
      }
    });

    finalResults = Object.values(groups).map(g => {
      const starts = g.starts.map(Number).filter(n => !isNaN(n));
      const ends = g.ends.map(Number).filter(n => !isNaN(n));
      
      const minStart = starts.length > 0 ? Math.min(...starts) : null;
      const maxEnd = ends.length > 0 ? Math.max(...ends) : null;

      return {
        ...g.baseRow,
        ano_inicio: minStart,
        ano_fim: maxEnd
      };
    });

    finalResults.sort(compareResults);
  }

  let plainTextText = "";

  if (formatType === "grade" || formatType === "limpa") {
    if (erpFont !== "monospace") {
      // ==========================================
      // LARGURAS FÍSICAS PROPORCIONAIS USANDO CANVAS
      // ==========================================
      const columnWidths: Record<string, number> = {};
      
      // Inicializa com o tamanho físico do cabeçalho
      activeKeys.forEach(key => {
        const label = getHeaderLabel(key);
        columnWidths[key] = getProportionalWidth(label, erpFont, erpFontSize);
      });

      // Encontra a largura física máxima por coluna, respeitando o cap de caracteres
      finalResults.forEach(res => {
        activeKeys.forEach(key => {
          let val = "";
          if (key === "ano") {
            val = res.ano_inicio || res.ano_fim
              ? `${res.ano_inicio || ""}...${res.ano_fim || ""}`
              : "";
          } else {
            val = String(res[key] || "").trim();
          }
          
          const cap = columnFixedWidths[key] || 25;
          const truncatedVal = val.length > cap ? val.substring(0, cap) : val;
          const valWidth = getProportionalWidth(truncatedVal, erpFont, erpFontSize);
          
          if (valWidth > columnWidths[key]) {
            columnWidths[key] = valWidth;
          }
        });
      });

      // Constrói cabeçalho e linhas
      const headerRow = "| " + activeKeys.map(key => {
        const label = getHeaderLabel(key);
        return padProportional(label, columnWidths[key], erpFont, erpFontSize);
      }).join(" | ") + " |";

      const separatorRow = "|-" + activeKeys.map(key => {
        const colWidth = columnWidths[key];
        const dashWidth = getProportionalWidth("-", erpFont, erpFontSize);
        const numDashes = Math.round(colWidth / dashWidth);
        return "-".repeat(numDashes);
      }).join("-|-") + "-|";

      const dataRows = finalResults.map(res => {
        return "| " + activeKeys.map(key => {
          let val = "";
          if (key === "ano") {
            val = res.ano_inicio || res.ano_fim
              ? `${res.ano_inicio || ""}...${res.ano_fim || ""}`
              : "";
          } else {
            val = String(res[key] || "").trim();
          }
          return padProportional(val, columnWidths[key], erpFont, erpFontSize);
        }).join(" | ") + " |";
      });

      plainTextText = hideDashesRow
        ? [headerRow, ...dataRows].join("\n")
        : [headerRow, separatorRow, ...dataRows].join("\n");
    } else {
      // ==========================================
      // LARGURAS PADRÃO MONOESPAÇADAS (POR CARACTERES)
      // ==========================================
      const columnWidths: Record<string, number> = {};
      
      // Inicializa com o tamanho do cabeçalho
      activeKeys.forEach(key => {
        columnWidths[key] = getHeaderLabel(key).length;
      });

      // Encontra a largura máxima dinâmica por coluna, respeitando o limite máximo (cap)
      finalResults.forEach(res => {
        activeKeys.forEach(key => {
          let val = "";
          if (key === "ano") {
            val = res.ano_inicio || res.ano_fim
              ? `${res.ano_inicio || ""}...${res.ano_fim || ""}`
              : "";
          } else {
            val = String(res[key] || "").trim();
          }
          
          const cap = columnFixedWidths[key] || 25;
          const valLen = Math.min(val.length, cap);
          if (valLen > columnWidths[key]) {
            columnWidths[key] = valLen;
          }
        });
      });

      const headerRow = "| " + activeKeys.map(key => {
        const label = getHeaderLabel(key);
        return formatValueToWidth(label, columnWidths[key]);
      }).join(" | ") + " |";

      const separatorRow = "|-" + activeKeys.map(key => {
        return "-".repeat(columnWidths[key]);
      }).join("-|-") + "-|";

      const dataRows = finalResults.map(res => {
        return "| " + activeKeys.map(key => {
          let val = "";
          if (key === "ano") {
            val = res.ano_inicio || res.ano_fim
              ? `${res.ano_inicio || ""}...${res.ano_fim || ""}`
              : "";
          } else {
            val = String(res[key] || "").trim();
          }
          return formatValueToWidth(val, columnWidths[key]);
        }).join(" | ") + " |";
      });

      plainTextText = hideDashesRow
        ? [headerRow, ...dataRows].join("\n")
        : [headerRow, separatorRow, ...dataRows].join("\n");
    }
  } else if (formatType === "tabulado") {
    // ==========================================
    // 2. CONSTRUÇÃO DA TABELA TABULADA POR TABS (\t)
    // ==========================================
    const headerRow = activeKeys.map(key => getHeaderLabel(key)).join("\t");
    const dataRows = finalResults.map(res => {
      return activeKeys.map(key => {
        let val = "";
        if (key === "ano") {
          val = res.ano_inicio || res.ano_fim
            ? `${res.ano_inicio || ""}...${res.ano_fim || ""}`
            : "";
        } else {
          val = String(res[key] || "").trim();
        }
        return val;
      }).join("\t");
    });

    plainTextText = [headerRow, ...dataRows].join("\n");
  }

  // ==========================================
  // 3. CONSTRUÇÃO DA TABELA HTML (PARA EXCEL/PLANILHAS)
  // ==========================================
  let htmlText = `<table style="border-collapse: collapse; font-family: Calibri, sans-serif; width: 100%; border: 1px solid #cbd5e1;">`;
  
  // Cabeçalho da Tabela
  htmlText += `<thead><tr style="background-color: #f1f5f9; border-bottom: 2px solid #cbd5e1;">`;
  activeKeys.forEach(key => {
    htmlText += `<th style="border: 1px solid #cbd5e1; padding: 6px 10px; text-align: left; font-weight: bold; font-size: 11pt; color: #0f172a;">${getHeaderLabel(key)}</th>`;
  });
  htmlText += `</tr></thead>`;

  // Corpo da Tabela
  htmlText += `<tbody>`;
  finalResults.forEach((res, idx) => {
    const bgColor = idx % 2 === 0 ? "#ffffff" : "#f8fafc";
    htmlText += `<tr style="background-color: ${bgColor}; border-bottom: 1px solid #e2e8f0;">`;
    activeKeys.forEach(key => {
      let val = "";
      if (key === "ano") {
        val = res.ano_inicio || res.ano_fim
          ? `${res.ano_inicio || ""}...${res.ano_fim || ""}`
          : "";
      } else {
        val = String(res[key] || "").trim();
      }
      htmlText += `<td style="border: 1px solid #e2e8f0; padding: 6px 10px; font-size: 10.5pt; color: #334155;">${val}</td>`;
    });
    htmlText += `</tr>`;
  });
  htmlText += `</tbody></table>`;


  // ==========================================
  // 4. CONSOLIDAÇÃO DE SIMILARES, FICHA TÉCNICA E IDX
  // ==========================================
  let extraText = "";

  if (Object.keys(uniqueReferences).length > 0) {
    extraText += "\n\n...\nREFERÊNCIA DE SIMILARES :\n";

    const visibleManufacturers = new Set(
      results.map(r => r.veiculo?.toUpperCase().trim()).filter(v => !!v)
    );

    const knownAutomakers = new Set([
      "VOLKSWAGEN", "VW", "CHEVROLET", "GM", "FIAT", "FORD", "TOYOTA",
      "HONDA", "HYUNDAI", "RENAULT", "NISSAN", "JEEP", "PEUGEOT",
      "CITROEN", "MITSUBISHI", "AUDI", "BMW", "MERCEDES-BENZ", "MERCEDES",
      "KIA", "VOLVO", "PORSCHE", "LAND ROVER", "CHERY", "CAOA CHERY",
      "SUZUKI", "SUBARU", "JAC", "DODGE", "CHRYSLER", "RAM", "ALFA ROMEO"
    ]);

    const sortedBrands = Object.entries(uniqueReferences).sort(([brandA], [brandB]) => {
      const isMkrA = automakers.includes(brandA) || visibleManufacturers.has(brandA) || knownAutomakers.has(brandA);
      const isMkrB = automakers.includes(brandB) || visibleManufacturers.has(brandB) || knownAutomakers.has(brandB);

      const isPriorityA = brandA === "ORIGINAL" || brandA === "OEM" || isMkrA;
      const isPriorityB = brandB === "ORIGINAL" || brandB === "OEM" || isMkrB;

      if (isPriorityA && !isPriorityB) return -1;
      if (!isPriorityA && isPriorityB) return 1;
      return brandA.localeCompare(brandB);
    });

    const seenCodes = new Set<string>();
    const normalizeCode = (c: string) => c.toUpperCase().replace(/[\s\-\.]/g, "");

    sortedBrands.forEach(([brand, codes]) => {
      const filteredCodes = Array.from(codes as Set<string>)
        .filter(code => {
          const norm = normalizeCode(code);
          if (seenCodes.has(norm)) return false;
          seenCodes.add(norm);
          return true;
        })
        .sort();

      if (filteredCodes.length > 0) {
        const codesList = filteredCodes.join(" - ");
        extraText += `${brand}: ${codesList}\n`;
      }
    });
  }

  // Fichas Técnicas Dinâmicas
  const appendFichaTecnica = (filterFn: (r: any) => boolean, titleLabel: string) => {
    const matching = results.filter(r => filterFn(r) && r.ficha_tecnica);
    if (matching.length > 0) {
      const ficha = matching[0].ficha_tecnica;
      if (Object.keys(ficha).length > 0) {
        extraText += `\n\n...\nFICHA TÉCNICA (${titleLabel}):\n`;
        Object.entries(ficha).forEach(([nome, valor]) => {
          if (valor === "-") {
            extraText += `${nome}\n`;
          } else {
            extraText += `${nome}: ${valor}\n`;
          }
        });
      }
    }
  };

  // Hipper Freios
  appendFichaTecnica(r => r.provedor === "HIPPER FREIOS", "HIPPER FREIOS");
  // Notus
  appendFichaTecnica(r => r.provedor === "NOTUS", "NOTUS");
  // Multiqualità
  appendFichaTecnica(r => r.provedor?.toUpperCase() === "MULTIQUALITA" || r.marca_peca === "MULTIQUALITÀ" || r.marca === "MULTIQUALITÀ", "MULTIQUALITÀ");
  // Autafastar
  appendFichaTecnica(r => r.provedor?.toUpperCase() === "AUTAFASTAR" || r.marca?.toUpperCase() === "AUTAFASTAR", "AUTAFASTAR");
  // Japanparts
  appendFichaTecnica(r => r.provedor?.toUpperCase() === "JAPANPARTS" || r.marca?.toUpperCase() === "JAPANPARTS", "JAPANPARTS");

  // Schaeffler (LUK, INA, FAG)
  const schaefflerBrands = ["LUK", "FAG", "INA"];
  const schaefflerResults = results.filter(r =>
    schaefflerBrands.includes(r.provedor?.toUpperCase()) || schaefflerBrands.includes(r.marca?.toUpperCase())
  );
  if (schaefflerResults.length > 0) {
    const withFicha = schaefflerResults.find(r => r.ficha_tecnica && Object.keys(r.ficha_tecnica).length > 0);
    if (withFicha) {
      const ficha = withFicha.ficha_tecnica;
      const brandLabel = withFicha.provedor?.toUpperCase() || withFicha.marca?.toUpperCase() || "SCHAEFFLER";
      extraText += `\n\n...\nFICHA TÉCNICA (${brandLabel}):\n`;
      Object.entries(ficha).forEach(([nome, valor]) => {
        if (valor === "-") {
          extraText += `${nome}\n`;
        } else {
          extraText += `${nome}: ${valor}\n`;
        }
      });
    }
  }

  // Bosch
  appendFichaTecnica(r => r.provedor?.toUpperCase() === "BOSCH" || r.marca?.toUpperCase() === "BOSCH", "BOSCH");
  // Ima
  appendFichaTecnica(r => r.provedor?.toUpperCase() === "IMA" || r.marca?.toUpperCase() === "IMA", "IMA");
  // Intermec
  appendFichaTecnica(r => r.provedor?.toUpperCase() === "INTERMEC" || r.marca?.toUpperCase() === "INTERMEC" || r.marca_peca?.toUpperCase() === "INTERMEC", "INTERMEC");


  // ==========================================
  // BLOCO DE INDEXAÇÃO PARA BUSCA (IDX)
  // ==========================================
  const generateIdxString = (resultsData: any[], referencesData: Record<string, Set<string>>, finalSourceText: string) => {
    const idxLines: string[] = ["\n\n...\nIDX:"];
    const expandedYears = new Set<string>();

    const parseYearTo4Digits = (yStr: string): number => {
      const y = parseInt(yStr, 10);
      if (yStr.length === 4) return y;
      return y <= 50 ? 2000 + y : 1900 + y;
    };

    const yearRanges = finalSourceText.match(/\b(\d{2,4})\.\.\.(\d{2,4})\b/g) || [];
    yearRanges.forEach(range => {
      const parts = range.split('...');
      if (parts.length === 2) {
        const startY = parseYearTo4Digits(parts[0]);
        const endY = parseYearTo4Digits(parts[1]);
        if (startY <= endY && endY - startY < 50) {
          for (let y = startY; y <= endY; y++) {
            expandedYears.add(y.toString());
            expandedYears.add(y.toString().substring(2));
          }
        }
      }
    });

    const getCleanWords = (str: string) => {
      if (!str) return [];
      const regex = /[a-zA-Z\u00C0-\u024F\u1E00-\u1EFF0-9]+(?:[\.,-][a-zA-Z\u00C0-\u024F\u1E00-\u1EFF0-9]+)*/g;
      const m = str.match(regex) || [];
      const arr: string[] = [];
      m.forEach(w => {
        let u = w.toUpperCase();
        if (u === 'AT' || u === 'OEM' || u === 'ORIGINAL') return;
        arr.push(u);
        if (u.includes('-')) arr.push(u.replace(/-/g, ''));
        if (u === 'S10') arr.push('S-10');
        if (u === 'F250') arr.push('F-250');
        if (u === 'F1000') arr.push('F-1000');
        if (u === 'F100') arr.push('F-100');
        if (u === 'D10') arr.push('D-10');
        if (u === 'D20') arr.push('D-20');
        if (u === 'A10') arr.push('A-10');
        if (u === 'C10') arr.push('C-10');
      });
      return arr;
    };

    const montadorasModelos = new Set<string>();
    resultsData.forEach(r => {
      getCleanWords(r.veiculo || r.marca).forEach(w => montadorasModelos.add(w));
      getCleanWords(r.modelo).forEach(w => montadorasModelos.add(w));
      getCleanWords(r.versao).forEach(w => montadorasModelos.add(w));
    });
    if (montadorasModelos.size > 0) idxLines.push(Array.from(montadorasModelos).join(" "));

    const motoresCombustiveis = new Set<string>();
    resultsData.forEach(r => {
      getCleanWords(r.motor).forEach(w => motoresCombustiveis.add(w));
      getCleanWords(r.configuracao_motor).forEach(w => motoresCombustiveis.add(w));
      getCleanWords(r.combustivel).forEach(w => motoresCombustiveis.add(w));
    });
    if (motoresCombustiveis.size > 0) idxLines.push(Array.from(motoresCombustiveis).join(" "));

    Object.entries(referencesData).forEach(([brand, codesSet]) => {
      const brandWords = getCleanWords(brand);
      const codesWords = new Set<string>();
      codesSet.forEach(code => {
        getCleanWords(code).forEach(w => codesWords.add(w));
      });
      const finalArr = [...brandWords, ...Array.from(codesWords)];
      if (finalArr.length > 0) idxLines.push(finalArr.join(" "));
    });

    if (expandedYears.size > 0) {
      const sortedYears = Array.from(expandedYears).sort();
      idxLines.push(`ANOS: ${sortedYears.join(" ")}`);
    }

    return idxLines.join("\n");
  };

  extraText += generateIdxString(results, uniqueReferences, plainTextText);

  // Adiciona a parte extra no texto simples
  plainTextText += extraText;

  // Adiciona a parte extra no HTML como bloco de texto simples formatado abaixo da tabela para que fique legível e não quebre o alinhamento
  htmlText += `<br><pre style="font-family: Calibri, sans-serif; font-size: 11pt; color: #334155; margin-top: 15px; white-space: pre-wrap; line-height: 1.4;">${extraText.trim()}</pre>`;

  // ==========================================
  // 5. SALVAR NA ÁREA DE TRANSFERÊNCIA (MULTIPLOS FORMATOS)
  // ==========================================
  const blobPlain = new Blob([plainTextText.trim()], { type: "text/plain" });
  const blobHtml = new Blob([htmlText.trim()], { type: "text/html" });

  try {
    navigator.clipboard.write([
      new ClipboardItem({
        "text/plain": blobPlain,
        "text/html": blobHtml
      })
    ]);
  } catch (err) {
    console.error("Falha ao salvar múltiplos formatos usando ClipboardItem, tentando fallback para text/plain", err);
    navigator.clipboard.writeText(plainTextText.trim());
  }
};
