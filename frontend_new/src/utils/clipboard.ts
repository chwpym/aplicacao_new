export const formatYearShort = (year: number | string | null | undefined) => {
  if (!year) return "";
  const s = year.toString();
  return s.length >= 4 ? s.substring(2) : s;
};

export const generateUniqueReferences = (results: any[]) => {
  const brands: Record<string, Set<string>> = {};
  results.forEach((res) => {
    if (res.referencias) {
      // Quebra por múltiplos separadores: |, ,, ;, e quebra de linha
      const refParts = res.referencias.split(/\s*(?:\||,|;|\n)\s*/);

      refParts.forEach((part: string) => {
        if (!part.trim()) return;

        // Faz o split seguro. Queremos dividir no `:` ou em ` - ` (com espaços).
        // Não podemos dividir apenas em `-` sem espaços, pois quebra marcas como "FRAS-LE".
        const pair = part.split(/\s*:\s*|\s+-\s+/);

        if (pair.length >= 2) {
          const brand = pair[0].trim();
          const code = pair.slice(1).join(":").trim();

          if (brand && code) {
            let cleanBrand = brand
              .toUpperCase()
              .replace(/\s+ORIGINAL$/g, "")
              .replace(/^ORIGINAL\s+/g, "");

            // Converte OEM isolado para ORIGINAL para agrupar junto
            if (cleanBrand === "OEM") {
              cleanBrand = "ORIGINAL";
            }

            if (!brands[cleanBrand]) brands[cleanBrand] = new Set();
            // Split codes that might have been joined with ":" or " - " and add individually to the set
            // Isso garante que códigos como "123:456" virem ["123", "456"] e sejam unidos por " - " depois
            code.split(/\s*:\s*|\s+-\s+/).forEach(c => {
              if (c.trim()) brands[cleanBrand].add(c.trim());
            });
          }
        }
      });
    }
  });
  return brands;
};

export const copyToClipboard = (
  mode: "completa" | "intermediaria" | "agrupada",
  results: any[],
  visibleFields: any,
  automakers: string[],
  uniqueReferences: Record<string, Set<string>>
) => {
  if (results.length === 0) return;

  let text = "";

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

  // Ordem de campos estritamente baseada nas colunas visíveis da tabela principal
  const orderedKeys = [
    "marca", "codigo", "veiculo", "modelo", "versao", "motor", "configuracao_motor",
    "combustivel", "posicao", "lado", "direcao", "sistema_freio",
    "restricao", "apenas"
  ];

  if (mode === "completa") {
    const lines = sortedResults
      .map((res) => {
        const parts = [];
        orderedKeys.forEach(key => {
          if (visibleFields[key] && res[key]) parts.push(res[key]);
        });

        if (visibleFields.ano) {
          const anoStr =
            res.ano_inicio || res.ano_fim
              ? `${res.ano_inicio || ""}...${res.ano_fim || ""}`
              : "";
          if (anoStr) parts.push(anoStr);
        }
        if (visibleFields.referencias && res.referencias) parts.push(res.referencias);
        if (visibleFields.observacao && res.observacao) parts.push(res.observacao);

        return parts.join(" ").replace(/\s+/g, " ").trim();
      })
      .filter((line) => line.length > 0);

    text = Array.from(new Set(lines)).join("\n");
  } else {
    const groups: any = {};
    const baseKeysToObs = new Map<string, boolean>();

    sortedResults.forEach((res) => {
      const baseKeyParts: any[] = [];
      const keysToUse = mode === "intermediaria"
        ? ["marca", "veiculo", "modelo", "versao", "motor", "configuracao_motor"]
        : orderedKeys;

      keysToUse.forEach(key => {
        if (visibleFields[key] && res[key]) baseKeyParts.push(res[key]);
      });

      const baseKeyStr = baseKeyParts.join("|") || "default";

      const obsText = (mode === "agrupada" && visibleFields.observacao && res.observacao) ? res.observacao : "";
      if (obsText) {
        baseKeysToObs.set(baseKeyStr, true);
      }

      // A chave única do grupo deve incluir a observação (para não mesclar obs diferentes)
      const key = `${baseKeyStr}|${obsText}`;

      if (!groups[key]) {
        groups[key] = {
          parts: baseKeyParts, // Só a base, sem a obs
          baseKey: baseKeyStr,
          hasObs: !!obsText,
          obsText: obsText,
          anos: [],
          items: [],
        };
      }
      groups[key].anos.push({ start: res.ano_inicio, end: res.ano_fim });
      groups[key].items.push(res);
    });

    // Remove redundant empty obs groups if a populated one exists for the same baseKey
    if (mode === "agrupada") {
      Object.keys(groups).forEach(key => {
        const g = groups[key];
        if (!g.hasObs && baseKeysToObs.get(g.baseKey)) {
          delete groups[key];
        }
      });
    }

    const sortedGroups = Object.values(groups);

    if (mode === "intermediaria") {
      const lines: string[] = [];
      sortedGroups.forEach((g: any) => {
        const uniqueRanges = new Set<string>();
        g.anos.forEach((a: any) => {
          const yearRange = `${formatYearShort(a.start)}...${a.end ? formatYearShort(a.end) : ""}`;
          uniqueRanges.add(yearRange);
        });
        const sortedRanges = Array.from(uniqueRanges).sort();
        sortedRanges.forEach((range) => {
          const rangeText = range === "..." ? "" : range;
          lines.push(
            `${g.parts.join(" ")} ${rangeText}`.replace(/\s+/g, " ").trim(),
          );
        });
      });
      text = lines.join("\n");
    } else {
      // mode === 'agrupada'
      const lines = sortedGroups.map((g: any) => {
        const starts = g.anos
          .map((a: any) => a.start)
          .filter((a: any) => a !== null && a !== undefined && a !== "");
        const ends = g.anos
          .map((a: any) => a.end)
          .filter((a: any) => a !== null && a !== undefined && a !== "");
        const minStart =
          starts.length > 0
            ? starts.every((s: any) => !isNaN(Number(s)))
              ? Math.min(...starts.map(Number))
              : starts[0]
            : "";
        const maxEnd =
          ends.length > 0
            ? ends.every((e: any) => !isNaN(Number(e)))
              ? Math.max(...ends.map(Number))
              : ends[ends.length - 1]
            : "";

        const yearRange = `${formatYearShort(minStart)}${maxEnd ? "..." + formatYearShort(maxEnd) : "..."}`;
        const rangeText = yearRange === "..." ? "" : yearRange;

        // Monta a linha: Base + Ano + Observacao
        const finalLineParts = [...g.parts];
        if (rangeText) finalLineParts.push(rangeText);
        if (g.obsText) finalLineParts.push(g.obsText);

        return finalLineParts.join(" ").replace(/\s+/g, " ").trim();
      });
      text = lines.join("\n");
    }
  }

  if (Object.keys(uniqueReferences).length > 0) {
    // Adiciona o separador rígido '...' para o sistema receptor
    text += "\n\n...\nREFERÊNCIA DE SIMILARES :\n";

    // Identifica montadoras conhecidas presentes nos resultados
    const visibleManufacturers = new Set(
      results.map(r => r.veiculo?.toUpperCase().trim()).filter(v => !!v)
    );

    // Lista de fallback de montadoras principais no Brasil para garantir que fiquem no topo
    const knownAutomakers = new Set([
      "VOLKSWAGEN", "VW", "CHEVROLET", "GM", "FIAT", "FORD", "TOYOTA",
      "HONDA", "HYUNDAI", "RENAULT", "NISSAN", "JEEP", "PEUGEOT",
      "CITROEN", "MITSUBISHI", "AUDI", "BMW", "MERCEDES-BENZ", "MERCEDES",
      "KIA", "VOLVO", "PORSCHE", "LAND ROVER", "CHERY", "CAOA CHERY",
      "SUZUKI", "SUBARU", "JAC", "DODGE", "CHRYSLER", "RAM", "ALFA ROMEO"
    ]);

    // Ordenação Padronizada de Marcas: ORIGINAL/Montadoras no topo, depois ordem alfabética
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

    // Função interna para normalizar código (remover espaços, pontos e traços para comparação de duplicatas)
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
        // Garante formato vertical: um marca por linha e espaçamento limpo
        text += `${brand}: ${codesList}\n`;
      }
    });
  }

  // Bloco de Medidas Técnicas (Específico Hipper Freios)
  const hipperResults = results.filter(r => r.provedor === "HIPPER FREIOS" && r.ficha_tecnica);
  if (hipperResults.length > 0) {
    const ficha = hipperResults[0].ficha_tecnica;
    if (Object.keys(ficha).length > 0) {
      text += "\n\n...\nMEDIDAS TÉCNICAS (HIPPER FREIOS):\n";
      Object.entries(ficha).forEach(([nome, valor]) => {
        text += `${nome}: ${valor}\n`;
      });
    }
  }

  // Bloco de Ficha Técnica (Específico NOTUS)
  const notusResults = results.filter(r => r.provedor === "NOTUS" && r.ficha_tecnica);
  if (notusResults.length > 0) {
    const ficha = notusResults[0].ficha_tecnica;
    if (Object.keys(ficha).length > 0) {
      text += "\n\n...\nFICHA TÉCNICA (NOTUS):\n";
      Object.entries(ficha).forEach(([nome, valor]) => {
        const valFinal = (valor && String(valor).trim() !== "") ? valor : "-";
        text += `${nome}: ${valFinal}\n`;
      });
    }
  }

  // Bloco de Ficha Técnica (Específico MULTIQUALITÀ)
  const multiResults = results.filter(r =>
    (r.provedor?.toUpperCase() === "MULTIQUALITA" || r.marca_peca === "MULTIQUALITÀ" || r.marca === "MULTIQUALITÀ")
    && r.ficha_tecnica
  );
  if (multiResults.length > 0) {
    const ficha = multiResults[0].ficha_tecnica;
    if (Object.keys(ficha).length > 0) {
      text += "\n\n...\nFICHA TÉCNICA (MULTIQUALITÀ):\n";
      Object.entries(ficha).forEach(([nome, valor]) => {
        if (valor === "-") {
          text += `${nome}\n`;
        } else {
          text += `${nome}: ${valor}\n`;
        }
      });
    }
  }

  // Bloco de Ficha Técnica (Específico AUTAFASTAR)
  const autafastarResults = results.filter(r =>
    (r.provedor?.toUpperCase() === "AUTAFASTAR" || r.marca?.toUpperCase() === "AUTAFASTAR")
    && r.ficha_tecnica
  );
  if (autafastarResults.length > 0) {
    const ficha = autafastarResults[0].ficha_tecnica;
    if (Object.keys(ficha).length > 0) {
      text += "\n\n...\nFICHA TÉCNICA (AUTAFASTAR):\n";
      Object.entries(ficha).forEach(([nome, valor]) => {
        if (valor === "-") {
          text += `${nome}\n`;
        } else {
          text += `${nome}: ${valor}\n`;
        }
      });
    }
  }

  // Bloco de Ficha Técnica (Específico JAPANPARTS)
  const japanpartsResults = results.filter(r =>
    (r.provedor?.toUpperCase() === "JAPANPARTS" || r.marca?.toUpperCase() === "JAPANPARTS")
    && r.ficha_tecnica
  );
  if (japanpartsResults.length > 0) {
    const ficha = japanpartsResults[0].ficha_tecnica;
    if (Object.keys(ficha).length > 0) {
      text += "\n\n...\nFICHA TÉCNICA (JAPANPARTS):\n";
      Object.entries(ficha).forEach(([nome, valor]) => {
        if (valor === "-") {
          text += `${nome}\n`;
        } else {
          text += `${nome}: ${valor}\n`;
        }
      });
    }
  }

  // Bloco de Ficha Técnica (Específico SCHAEFFLER — LUK, FAG, INA)
  const schaefflerBrands = ["LUK", "FAG", "INA"];
  const schaefflerResults = results.filter(r =>
    schaefflerBrands.includes(r.provedor?.toUpperCase()) || schaefflerBrands.includes(r.marca?.toUpperCase())
  );
  if (schaefflerResults.length > 0) {
    const withFicha = schaefflerResults.find(r => r.ficha_tecnica && Object.keys(r.ficha_tecnica).length > 0);
    if (withFicha) {
      const ficha = withFicha.ficha_tecnica;
      const brandLabel = withFicha.provedor?.toUpperCase() || withFicha.marca?.toUpperCase() || "SCHAEFFLER";
      text += `\n\n...\nFICHA TÉCNICA (${brandLabel}):\n`;
      Object.entries(ficha).forEach(([nome, valor]) => {
        if (valor === "-") {
          text += `${nome}\n`;
        } else {
          text += `${nome}: ${valor}\n`;
        }
      });
    }
  }

  // Bloco de Ficha Técnica (Específico BOSCH)
  const boschResults = results.filter(r =>
    (r.provedor?.toUpperCase() === "BOSCH" || r.marca?.toUpperCase() === "BOSCH")
    && r.ficha_tecnica
  );
  if (boschResults.length > 0) {
    const ficha = boschResults[0].ficha_tecnica;
    if (Object.keys(ficha).length > 0) {
      text += "\n\n...\nFICHA TÉCNICA (BOSCH):\n";
      Object.entries(ficha).forEach(([nome, valor]) => {
        if (valor === "-") {
          text += `${nome}\n`;
        } else {
          text += `${nome}: ${valor}\n`;
        }
      });
    }
  }

  // Bloco de Ficha Técnica (Específico IMA)
  const imaResults = results.filter(r =>
    (r.provedor?.toUpperCase() === "IMA" || r.marca?.toUpperCase() === "IMA")
    && r.ficha_tecnica
  );
  if (imaResults.length > 0) {
    const ficha = imaResults[0].ficha_tecnica;
    if (Object.keys(ficha).length > 0) {
      text += "\n\n...\nFICHA TÉCNICA (IMA):\n";
      Object.entries(ficha).forEach(([nome, valor]) => {
        if (valor === "-") {
          text += `${nome}\n`;
        } else {
          text += `${nome}: ${valor}\n`;
        }
      });
    }
  }


  // ==========================================
  // BLOCO DE INDEXAÇÃO PARA BUSCA (IDX)
  // ==========================================
  const generateIdxString = (resultsData: any[], referencesData: Record<string, Set<string>>, finalSourceText: string) => {
    const idxLines: string[] = ["\n\n...\nIDX:"];

    // Conjunto global para guardar todos os anos expandidos
    const expandedYears = new Set<string>();

    const parseYearTo4Digits = (yStr: string): number => {
      const y = parseInt(yStr, 10);
      if (yStr.length === 4) return y;
      return y <= 50 ? 2000 + y : 1900 + y;
    };

    // Extrai ranges de anos globais do texto formatado
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

    // 1. Linha de Montadoras + Modelos (Carros)
    const montadorasModelos = new Set<string>();
    resultsData.forEach(r => {
      getCleanWords(r.veiculo || r.marca).forEach(w => montadorasModelos.add(w));
      getCleanWords(r.modelo).forEach(w => montadorasModelos.add(w));
      getCleanWords(r.versao).forEach(w => montadorasModelos.add(w));
    });
    if (montadorasModelos.size > 0) idxLines.push(Array.from(montadorasModelos).join(" "));

    // 2. Linha de Motores + Combustíveis
    const motoresCombustiveis = new Set<string>();
    resultsData.forEach(r => {
      getCleanWords(r.motor).forEach(w => motoresCombustiveis.add(w));
      getCleanWords(r.configuracao_motor).forEach(w => motoresCombustiveis.add(w));
      getCleanWords(r.combustivel).forEach(w => motoresCombustiveis.add(w));
    });
    if (motoresCombustiveis.size > 0) idxLines.push(Array.from(motoresCombustiveis).join(" "));

    // 3. Referências de Similares (Uma linha por marca)
    Object.entries(referencesData).forEach(([brand, codesSet]) => {
      const brandWords = getCleanWords(brand);
      const codesWords = new Set<string>();
      codesSet.forEach(code => {
        getCleanWords(code).forEach(w => codesWords.add(w));
      });
      const finalArr = [...brandWords, ...Array.from(codesWords)];
      if (finalArr.length > 0) idxLines.push(finalArr.join(" "));
    });

    // 4. Anos Expandidos
    if (expandedYears.size > 0) {
      const sortedYears = Array.from(expandedYears).sort();
      idxLines.push(`ANOS: ${sortedYears.join(" ")}`);
    }

    return idxLines.join("\n");
  };

  text += generateIdxString(results, uniqueReferences, text);

  navigator.clipboard.writeText(text.trim());
};
