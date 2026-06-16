/**
 * mercadoLivreGenerator.ts
 * Gera conteúdo otimizado para anúncios (Mercado Livre, Shopee, Site Próprio).
 */

export interface MercadoLivreContent {
  titulo: string;
  descricaoResumida: string;
  aplicacoes: string;
  referencias: string;
  palavrasChave: string;
}

/**
 * Capitaliza as primeiras letras de cada palavra (Title Case).
 */
function toTitleCase(str: string): string {
  return str.toLowerCase().replace(/(?:^|\s|-)\S/g, function(a) { return a.toUpperCase(); });
}

/**
 * Agrupa resultados por modelo, retornando uma estrutura organizada para facilitar a renderização.
 */
function groupForApplications(results: any[]): Record<string, any[]> {
  const byModel: Record<string, any[]> = {};
  results.forEach((res) => {
    const modelo = (res.modelo || "OUTROS").toUpperCase().trim();
    if (!byModel[modelo]) byModel[modelo] = [];
    byModel[modelo].push(res);
  });
  return byModel;
}

/**
 * Gera o título otimizado para busca.
 * Formato: "[Nome da Peça] {Marca} {Código} {Modelos} {Motores} {Anos}"
 */
function generateTitulo(results: any[], partId: string): string {
  if (results.length === 0) return "";
  const marcaPeca = toTitleCase(results[0]?.marca || "").trim();
  const modelos = [...new Set(results.map(r => toTitleCase(r.modelo || "").trim()).filter(Boolean))].slice(0, 3).join(" ");
  
  // Motores simplificados (ex: 1.0, 1.6)
  const motoresRaw = results.map(r => (r.motor || "").trim().toUpperCase()).filter(Boolean);
  const motoresPrincipais = [...new Set(motoresRaw.map(m => m.split(" ")[0]))].slice(0, 2).join(" ");

  // Menor e maior ano
  const anos = results.map(r => Number(r.ano_inicio)).filter(y => !isNaN(y) && y > 1900);
  const anosFim = results.map(r => Number(r.ano_fim)).filter(y => !isNaN(y) && y > 1900);
  const minAno = anos.length > 0 ? Math.min(...anos) : "";
  const maxAno = anosFim.length > 0 ? Math.max(...anosFim) : minAno;
  const anoStr = (minAno && maxAno && minAno !== maxAno) ? `${minAno}-${maxAno}` : (minAno ? `${minAno}` : "");

  // Título base
  const base = `[NOME DA PEÇA] ${marcaPeca} ${partId}`;
  
  // Monta título priorizando caber em 60-70 caracteres
  let titulo = `${base} ${modelos} ${motoresPrincipais} ${anoStr}`.replace(/\s+/g, " ").trim();
  
  // Limita o título
  return titulo.length > 70 ? titulo.substring(0, 70) : titulo;
}

/**
 * Gera a descrição resumida com visual premium.
 */
function generateDescricaoResumida(results: any[], partId: string): string {
  const marcaPeca = (results[0]?.marca || "").toUpperCase().trim();
  const byModel = groupForApplications(results);

  const lines: string[] = [];
  lines.push(`📦 [NOME DA PEÇA] ${marcaPeca} ${partId}`);
  lines.push(`─────────────────────────────────`);
  lines.push("✅ Produto novo e original.");
  lines.push("");
  lines.push(`  • Código: ${partId}`);
  lines.push(`  • Marca: ${marcaPeca}`);
  lines.push("");
  lines.push("🚗 Aplicação Resumida:");

  Object.entries(byModel).sort(([a], [b]) => a.localeCompare(b)).forEach(([modelo, items]) => {
    const montadora = (items[0]?.veiculo || "").toUpperCase().trim();
    const motores = [...new Set(items.map(i => (i.motor || "").trim().toUpperCase()).filter(Boolean))].join(" / ");
    
    const anos = items.map(r => Number(r.ano_inicio)).filter(y => !isNaN(y) && y > 1900);
    const anosFim = items.map(r => Number(r.ano_fim)).filter(y => !isNaN(y) && y > 1900);
    const anoStr = formatMinMaxYear(anos, anosFim);

    let line = `  ▸ ${montadora} ${modelo}`;
    if (motores) line += ` ${motores}`;
    if (anoStr) line += ` - ${anoStr}`;
    lines.push(line);
  });

  lines.push("");
  lines.push("⚠️ Antes da compra confirme a aplicação pelo modelo, ano e motorização do veículo.");

  return lines.join("\n");
}

/**
 * Limpa strings que vêm sujas do catálogo:
 * - Múltiplos espaços
 * - Barras duplas ( / / ) ou soltas
 * - Hífens duplos ( -- )
 */
function cleanString(str: string): string {
  if (!str) return "";
  return str
    .replace(/--+/g, "-") // Remove hífens duplos
    .replace(/\s*\/\s*\//g, " / ") // Remove / / duplicados
    .replace(/\(\s+/g, "(")
    .replace(/\s+\)/g, ")")
    .replace(/\(\s*\)/g, "") // Remove parênteses vazios
    .replace(/\(\s*\//g, "(") // Remove barra logo após abrir parênteses: (/ CITY) -> (CITY)
    .replace(/\/\s*\)/g, ")") // Remove barra logo antes de fechar: (CITY /) -> (CITY)
    .replace(/\(\s*-\s*/g, "(") // Remove hífen logo após parênteses: (- G5) -> (G5)
    .replace(/-\s*\//g, "- ") // Corrige (G5 - / CITY) -> (G5 - CITY)
    .replace(/\/\s*-/g, " -") // Corrige (CITY / - G5) -> (CITY - G5)
    .replace(/^[\/\-\s]+/, "") // Remove barras e hífens do começo da string
    .replace(/[\/\-\s]+$/, "") // Remove barras e hífens do final da string
    .replace(/\s+/g, " ")
    .trim();
}

/**
 * Normaliza e limpa a versão, mantendo termos técnicos como MI e TOTAL
 */
function normalizeVersion(str: string) {
  if (!str) return "";
  return cleanString(str);
}

/**
 * Agrupa anos contínuos.
 * Ex: [2008, 2010, 2011, 2012, 2014] -> "2008, 2010 a 2012, 2014"
 */
function formatContinuousYears(years: number[]): string {
  if (!years || years.length === 0) return "";
  
  const uniqueYears = [...new Set(years)].filter(y => y > 1900).sort((a, b) => a - b);
  if (uniqueYears.length === 0) return "";

  const ranges: string[] = [];
  let start = uniqueYears[0];
  let end = uniqueYears[0];

  for (let i = 1; i < uniqueYears.length; i++) {
    if (uniqueYears[i] === end + 1) {
      end = uniqueYears[i];
    } else {
      ranges.push(start === end ? `${start}` : `${start} a ${end}`);
      start = uniqueYears[i];
      end = uniqueYears[i];
    }
  }
  ranges.push(start === end ? `${start}` : `${start} a ${end}`);

  return ranges.join(", ");
}

/**
 * Formata o intervalo geral sumarizado para a Descrição Resumida
 */
function formatMinMaxYear(anosIni: number[], anosFim: number[]): string {
  const anos = [...anosIni, ...anosFim].filter(y => !isNaN(y) && y > 1900);
  if (anos.length === 0) return "";
  
  const minAno = Math.min(...anos);
  const maxAno = Math.max(...anos);
  
  if (minAno === maxAno) return `${minAno}`;
  return `${minAno} a ${maxAno}`;
}

/**
 * Gera as aplicações detalhadas com visual estruturado,
 * removendo duplicidades e unindo anos para especificações idênticas.
 */
function generateAplicacoesDetalhes(results: any[]): string {
  const byModel = groupForApplications(results);
  const lines: string[] = [];

  lines.push("⚙️ APLICAÇÕES DETALHADAS:");
  lines.push(`─────────────────────────────────`);

  Object.entries(byModel).sort(([a], [b]) => a.localeCompare(b)).forEach(([modelo, items]) => {
    // Agrupa por especificação exata para não repetir linhas idênticas
    const specsMap: Record<string, number[]> = {};

    items.forEach(i => {
      // Ignora aplicações excessivamente genéricas (ex: tem apenas motor 1.0 e ano)
      if (!i.versao && !i.configuracao_motor && !i.combustivel) return;

      let parts = [];
      if (i.versao) parts.push(normalizeVersion(i.versao.toUpperCase()));
      if (i.motor) parts.push(i.motor.toUpperCase());
      if (i.configuracao_motor) parts.push(i.configuracao_motor.toUpperCase());
      if (i.combustivel) parts.push(i.combustivel.toUpperCase());

      let specStr = parts.join(" ");
      specStr = cleanString(specStr);
      
      // Filtro de segurança: se sobrou quase nada
      if (specStr.length < 3) return;

      if (!specsMap[specStr]) specsMap[specStr] = [];
      
      const anoIni = Number(i.ano_inicio);
      const anoFim = Number(i.ano_fim);

      if (anoIni && anoFim && anoFim >= anoIni) {
        // Preenche o range de anos para garantir continuidade
        for (let y = anoIni; y <= anoFim; y++) {
          specsMap[specStr].push(y);
        }
      } else if (anoIni) {
        specsMap[specStr].push(anoIni);
      }
    });

    // Se o modelo ficar vazio após os filtros, não imprime
    if (Object.keys(specsMap).length === 0) return;

    lines.push(`▸ ${modelo}`);

    // Monta as linhas brutas com seus anos formatados
    const modelLines = Object.entries(specsMap)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([spec, years]) => {
        return {
          spec,
          anoStr: formatContinuousYears(years),
        };
      });

    // Remove aplicações que são subconjuntos de outras do mesmo ano
    const filteredLines = modelLines.filter((lineA, index, arr) => {
      // Verifica se existe alguma outra linhaB que contém todas as palavras da linhaA
      return !arr.some(lineB => {
        if (lineA.spec === lineB.spec) return false;
        
        // Se o ano for diferente, não é redundante, mantemos as duas.
        if (lineA.anoStr !== lineB.anoStr) return false;
        
        const wordsA = lineA.spec.replace(/[^\w]/g, " ").split(/\s+/).filter(Boolean);
        const wordsB = lineB.spec.replace(/[^\w]/g, " ").split(/\s+/).filter(Boolean);
        
        // Se a especificação B tiver todas as palavras da especificação A, A é subconjunto (redundante)
        return wordsA.length < wordsB.length && wordsA.every(wa => wordsB.includes(wa));
      });
    });

    filteredLines.forEach(({ spec, anoStr }) => {
      let line = `  • ${spec}`;
      if (anoStr) line += ` - ${anoStr}`;
      lines.push(cleanString(line));
    });

    lines.push("");
  });

  return lines.join("\n").trim();
}

/**
 * Gera referências equivalentes no formato compacto da V1.
 */
function generateReferencias(uniqueReferences: any): string {
  if (!uniqueReferences || Object.keys(uniqueReferences).length === 0) {
    return "Nenhuma referência equivalente informada.";
  }

  const lines: string[] = [];
  lines.push("🔗 REFERÊNCIAS / CÓDIGOS ORIGINAIS:");
  lines.push(`─────────────────────────────────`);

  Object.entries(uniqueReferences).sort(([a], [b]) => a.localeCompare(b)).forEach(([brand, codes]) => {
    const brandName = brand.toUpperCase();
    const codeArray = Array.from(codes as Set<string>)
      .map(c => cleanString(c.toUpperCase()))
      .sort();
    lines.push(`  • ${brandName}: ${codeArray.join(" / ")}`);
  });

  return lines.join("\n").trim();
}

/**
 * Gera palavras-chave ocultas (IDX).
 */
function generatePalavrasChave(results: any[], partId: string, uniqueReferences: any): string {
  const keywords = new Set<string>();

  const marcaPeca = (results[0]?.marca || "").toUpperCase().trim();
  if (marcaPeca) keywords.add(marcaPeca);
  if (partId) keywords.add(cleanString(partId.toUpperCase()));

  results.forEach(r => {
    if (r.veiculo) keywords.add(r.veiculo.toUpperCase().trim());
    if (r.modelo) {
      r.modelo.split(" ").forEach((w: string) => keywords.add(w.toUpperCase().trim()));
    }
    if (r.versao) {
      const cleanVersao = cleanString(r.versao).replace(/[^\w\s]/gi, ' ').split(" ");
      cleanVersao.forEach((w: string) => {
        if (w.trim().length > 1) keywords.add(w.toUpperCase().trim());
      });
    }
    if (r.motor) {
      r.motor.split(" ").forEach((w: string) => keywords.add(w.toUpperCase().trim()));
    }
    if (r.configuracao_motor) {
      r.configuracao_motor.split(" ").forEach((w: string) => keywords.add(w.toUpperCase().trim()));
    }
    if (r.combustivel) keywords.add(r.combustivel.toUpperCase().trim());
  });

  if (uniqueReferences) {
    Object.values(uniqueReferences).forEach((codes: any) => {
      Array.from(codes as Set<string>).forEach(c => keywords.add(cleanString(c.toUpperCase())));
    });
  }

  return Array.from(keywords).sort().join("\n");
}

/**
 * Função principal que gera a nova estrutura do Mercado Livre.
 */
export const generateMercadoLivreContent = (
  displayResults: any[],
  partId: string,
  uniqueReferences?: any
): MercadoLivreContent => {
  if (displayResults.length === 0) {
    return {
      titulo: "",
      descricaoResumida: "",
      aplicacoes: "",
      referencias: "",
      palavrasChave: "",
    };
  }

  return {
    titulo: cleanString(generateTitulo(displayResults, partId)),
    descricaoResumida: generateDescricaoResumida(displayResults, partId),
    aplicacoes: generateAplicacoesDetalhes(displayResults),
    referencias: generateReferencias(uniqueReferences),
    palavrasChave: generatePalavrasChave(displayResults, partId, uniqueReferences),
  };
};
