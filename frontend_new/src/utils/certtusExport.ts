/**
 * certtusExport.ts
 * Gera planilha Excel no layout exato de importação do Certtus (colunas A-S).
 * 
 * Layout Certtus:
 * A - Código Fabricante    | B - Marca           | C - Modelo
 * D - Versão               | E - Potência/Motor  | F - Mês Inicial Modelo
 * G - Ano Inicial Modelo   | H - Mês Final Modelo| I - Ano Final Modelo
 * J - Combustível          | K - Código/Nome Motor| L - ABS
 * M - Direção Hidráulica   | N - Ar Condicionado | O - Transmissão
 * P - Localização          | Q - Lado            | R - Aplicação
 * S - Informações para E-commerce
 */
import * as XLSX from "xlsx";

// ============================================================
// DICIONÁRIO DE COMBUSTÍVEL → Código Certtus
// ============================================================
const COMBUSTIVEL_MAP: Record<string, string> = {
  // Valores diretos
  "GASOLINA": "CG",
  "ETANOL": "CE",
  "ALCOOL": "CE",
  "ÁLCOOL": "CE",
  "DIESEL": "CD",
  "GNV": "CGV",
  "GAS NATURAL": "CGV",
  "GÁS NATURAL": "CGV",
  "GASOGENIO": "CGO",
  "GASOGÊNIO": "CGO",
  "GAS METANO": "CGM",
  "GÁS METANO": "CGM",
  "ELETRICO": "CEFI",
  "ELÉTRICO": "CEFI",
  "ELETRICO FI": "CEFI",
  "ELÉTRICO FI": "CEFI",
  "ELETRICO FE": "CEFE",
  "ELÉTRICO FE": "CEFE",

  // Bicombustível / Flex
  "FLEX": "BI",
  "BICOMBUSTIVEL": "BI",
  "BICOMBUSTÍVEL": "BI",
  "GASOLINA/ETANOL": "BI",
  "ETANOL/GASOLINA": "BI",
  "GASOLINA/ALCOOL": "BI",
  "ÁLCOOL/GASOLINA": "BI",
  "ALCOOL/GASOLINA": "BI",

  // Combinações com GNV/GNC
  "GASOLINA/GNV": "CGG",
  "GASOLINA/GNC": "CGGN",
  "ETANOL/GNV": "CAG",
  "ETANOL/GNC": "CAGC",
  "ALCOOL/GNV": "CAG",
  "ÁLCOOL/GNV": "CAG",
  "DIESEL/GNV": "CDG",
  "DIESEL/GNC": "CDGC",

  // Híbridos
  "GASOLINA/ELETRICO": "CGE",
  "GASOLINA/ELÉTRICO": "CGE",
  "GASOLINA/ETANOL/GNV": "CGEG",
  "GASOLINA/ETANOL/GN": "CGEG",
};

// ============================================================
// MAPEAMENTO DE POSIÇÃO → Código Certtus
// ============================================================
const POSICAO_MAP: Record<string, string> = {
  "DIANTEIRO": "DIAN",
  "DIANTEIRA": "DIAN",
  "DIANT": "DIAN",
  "DIANT.": "DIAN",
  "FRONT": "DIAN",
  "FRONTAL": "DIAN",
  "TRASEIRO": "TRAS",
  "TRASEIRA": "TRAS",
  "TRAS": "TRAS",
  "TRAS.": "TRAS",
  "REAR": "TRAS",
};

// ============================================================
// MAPEAMENTO DE LADO → Código Certtus
// ============================================================
const LADO_MAP: Record<string, string> = {
  "DIREITO": "LD",
  "DIREITA": "LD",
  "DIR": "LD",
  "DIR.": "LD",
  "D": "LD",
  "RIGHT": "LD",
  "ESQUERDO": "LE",
  "ESQUERDA": "LE",
  "ESQ": "LE",
  "ESQ.": "LE",
  "E": "LE",
  "LEFT": "LE",
  // Já no formato Certtus
  "LD": "LD",
  "LE": "LE",
};

// ============================================================
// FUNÇÕES DE DETECÇÃO POR PALAVRAS-CHAVE
// ============================================================

/**
 * Mapeia o combustível dos dados do catálogo para o código Certtus.
 * Suporta combustíveis múltiplos separados por / (ex: "GASOLINA/ETANOL")
 */
function mapCombustivel(raw: string | null | undefined): string {
  if (!raw) return "";
  const normalized = raw.toUpperCase().trim()
    .replace(/\s+/g, " ")
    .replace(/Á/g, "A").replace(/É/g, "E").replace(/Í/g, "I")
    .replace(/Ó/g, "O").replace(/Ú/g, "U");

  // Tenta match direto
  if (COMBUSTIVEL_MAP[normalized]) return COMBUSTIVEL_MAP[normalized];

  // Tenta match sem acentos no mapa
  for (const [key, code] of Object.entries(COMBUSTIVEL_MAP)) {
    const keyNorm = key.replace(/Á/g, "A").replace(/É/g, "E").replace(/Í/g, "I")
      .replace(/Ó/g, "O").replace(/Ú/g, "U");
    if (keyNorm === normalized) return code;
  }

  // Tenta detectar por palavras-chave parciais
  if (/\bFLEX\b/i.test(raw) || /\bBI\s*COMB/i.test(raw)) return "BI";
  if (/\bGASOLINA\b/i.test(raw) && /\bETANOL\b/i.test(raw)) return "BI";
  if (/\bGASOLINA\b/i.test(raw) && /\bALCOOL\b/i.test(raw)) return "BI";
  if (/\bGASOLINA\b/i.test(raw) && /\bEL[EÉ]TRICO\b/i.test(raw)) return "CGE";
  if (/\bDIESEL\b/i.test(raw)) return "CD";
  if (/\bGASOLINA\b/i.test(raw)) return "CG";
  if (/\bETANOL\b/i.test(raw) || /\b[AÁ]LCOOL\b/i.test(raw)) return "CE";
  if (/\bEL[EÉ]TRICO\b/i.test(raw)) return "CEFI";
  if (/\bGNV\b/i.test(raw)) return "CGV";

  return ""; // Não reconhecido — fica vazio para revisão manual
}

/**
 * Mapeia posição para código Certtus (DIAN/TRAS)
 */
function mapPosicao(raw: string | null | undefined): string {
  if (!raw) return "";
  const normalized = raw.toUpperCase().trim();
  if (POSICAO_MAP[normalized]) return POSICAO_MAP[normalized];

  // Detecção parcial
  if (/\bDIAN/i.test(raw) || /\bFRONT/i.test(raw)) return "DIAN";
  if (/\bTRAS/i.test(raw) || /\bREAR/i.test(raw)) return "TRAS";

  return "";
}

/**
 * Mapeia lado para código Certtus (LD/LE)
 */
function mapLado(raw: string | null | undefined): string {
  if (!raw) return "";
  const normalized = raw.toUpperCase().trim();
  if (LADO_MAP[normalized]) return LADO_MAP[normalized];

  if (/\bDIR/i.test(raw) || /\bRIGHT/i.test(raw)) return "LD";
  if (/\bESQ/i.test(raw) || /\bLEFT/i.test(raw)) return "LE";

  return "";
}

/**
 * Detecta se tem ABS a partir dos campos disponíveis
 */
function detectAbs(res: any): string {
  const sources = [
    res.sistema_freio,
    res.observacao,
    res.apenas,
    res.restricao,
    JSON.stringify(res.ficha_tecnica || {}),
  ].join(" ").toUpperCase();

  if (/\bCOM\s*ABS\b/i.test(sources) || /\bC\/\s*ABS\b/i.test(sources)) return "CABS";
  if (/\bSEM\s*ABS\b/i.test(sources) || /\bS\/\s*ABS\b/i.test(sources)) return "SABS";

  return "";
}

/**
 * Detecta tipo de direção a partir dos campos disponíveis
 */
function detectDirecao(res: any): string {
  const sources = [
    res.direcao,
    res.observacao,
    res.apenas,
    res.restricao,
    JSON.stringify(res.ficha_tecnica || {}),
  ].join(" ").toUpperCase();

  if (/\bCOM\s*DIR.*HIDR/i.test(sources) || /\bC\/\s*D\.?\s*H/i.test(sources) || /\bDIR.*HIDR/i.test(sources) || /\bCDH\b/i.test(sources)) return "CDH";
  if (/\bSEM\s*DIR.*HIDR/i.test(sources) || /\bS\/\s*D\.?\s*H/i.test(sources) || /\bSDH\b/i.test(sources)) return "SDH";

  return "";
}

/**
 * Detecta ar condicionado a partir dos campos disponíveis
 */
function detectArCondicionado(res: any): string {
  const sources = [
    res.observacao,
    res.apenas,
    res.restricao,
    JSON.stringify(res.ficha_tecnica || {}),
  ].join(" ").toUpperCase();

  if (/\bCOM\s*AR\b/i.test(sources) || /\bC\/\s*AR\b/i.test(sources) || /\bCAR\b/.test(sources) || /\bCOM\s*A\.?\s*C\.?\b/i.test(sources)) return "CAR";
  if (/\bSEM\s*AR\b/i.test(sources) || /\bS\/\s*AR\b/i.test(sources) || /\bSAR\b/.test(sources) || /\bSEM\s*A\.?\s*C\.?\b/i.test(sources)) return "SAR";

  return "";
}

/**
 * Detecta tipo de transmissão a partir dos campos disponíveis
 */
function detectTransmissao(res: any): string {
  const sources = [
    res.observacao,
    res.apenas,
    res.restricao,
    JSON.stringify(res.ficha_tecnica || {}),
  ].join(" ").toUpperCase();

  if (/\bAUTOM[AÁ]TIC/i.test(sources) || /\bTMA\b/.test(sources) || /\bAT\b/.test(sources) || /\bAUTO\b/i.test(sources)) return "TMA";
  if (/\bMANUAL\b/i.test(sources) || /\bTMM\b/.test(sources) || /\bMT\b/.test(sources)) return "TMM";

  return "";
}

/**
 * Monta o texto de aplicação combinando observação, restrição e apenas
 */
function buildAplicacao(res: any): string {
  const parts: string[] = [];
  if (res.observacao) parts.push(res.observacao);
  if (res.restricao) parts.push(`Restrição: ${res.restricao}`);
  if (res.apenas) parts.push(`Apenas: ${res.apenas}`);
  return parts.join(" | ");
}

/**
 * Extrai ano como número de 4 dígitos, tratando strings como "2015", "2015.0", etc.
 */
function extractYear(raw: any): string | number | undefined {
  if (!raw && raw !== 0) return undefined;
  const str = String(raw).trim();
  const match = str.match(/\b(\d{4})\b/);
  if (match) return Number(match[1]);
  return undefined;
}

// ============================================================
// FUNÇÃO PRINCIPAL DE EXPORTAÇÃO
// ============================================================

/**
 * Gera e baixa um arquivo Excel no layout de importação do Certtus.
 * 
 * @param displayResults - Resultados de busca processados (array de SearchResult)
 * @param partId - Código da peça buscada (será usado como Código Fabricante)
 */
export const exportToCerttus = (displayResults: any[], partId: string) => {
  if (displayResults.length === 0) return;

  // O Certtus possui duas linhas de cabeçalho
  const headerRow1 = [
    "",                             // A
    "Modelo do Veículo",            // B
    "", "", "", "", "", "", "", "", "", // C a K
    "Especificações para Aplicação", // L
    "", "", "", "", "", "", ""      // M a S
  ];

  const headerRow2 = [
    "Código Fabricante",      // A
    "Marca",                  // B
    "Modelo",                 // C
    "Versão",                 // D
    "Potência/Motor",         // E
    "Mês Inicial Modelo",     // F
    "Ano Inicial Modelo",     // G
    "Mês Final Modelo",       // H
    "Ano Final Modelo ",      // I (espaço no final conforme modelo)
    "Combustível",            // J
    "Código/Nome Motor",      // K
    "ABS",                    // L
    "Direção Hidráulica",     // M
    "Ar Condicionado",        // N
    "Transmissão",            // O
    "Localização",            // P
    "Lado ",                  // Q (espaço no final conforme modelo)
    "Aplicação",              // R
    "Informações para E-commerce" // S
  ];

  // Monta cada linha no formato Certtus
  const rows = displayResults.map((res: any) => {
    const anoInicio = extractYear(res.ano_inicio);
    const anoFim = extractYear(res.ano_fim);

    return [
      partId || "",                              // A - Código Fabricante
      (res.veiculo || "").toUpperCase().trim(),   // B - Marca (montadora)
      (res.modelo || "").toUpperCase().trim(),    // C - Modelo
      (res.versao || "").toUpperCase().trim(),    // D - Versão
      res.motor ? res.motor.toUpperCase().trim() : "TODOS", // E - Potência/Motor (obrigatório no Certtus)
      "",                                         // F - Mês Inicial (catálogos não trazem)
      anoInicio ?? "",                             // G - Ano Inicial
      "",                                         // H - Mês Final
      anoFim ?? "",                                // I - Ano Final
      mapCombustivel(res.combustivel),            // J - Combustível
      (res.configuracao_motor || "").toUpperCase().trim(), // K - Código/Nome Motor
      detectAbs(res),                             // L - ABS
      detectDirecao(res),                         // M - Direção Hidráulica
      detectArCondicionado(res),                  // N - Ar Condicionado
      detectTransmissao(res),                     // O - Transmissão
      mapPosicao(res.posicao),                    // P - Localização
      mapLado(res.lado),                          // Q - Lado
      buildAplicacao(res),                        // R - Aplicação
      "",                                         // S - E-commerce (futuro)
    ];
  });

  // Cria a planilha com as duas linhas de cabeçalho
  const wsData = [headerRow1, headerRow2, ...rows];
  const worksheet = XLSX.utils.aoa_to_sheet(wsData);

  // Define larguras das colunas para melhor visualização
  worksheet["!cols"] = [
    { wch: 18 }, // A - Código Fabricante
    { wch: 15 }, // B - Marca
    { wch: 18 }, // C - Modelo
    { wch: 15 }, // D - Versão
    { wch: 15 }, // E - Motor
    { wch: 8 },  // F - Mês Ini
    { wch: 8 },  // G - Ano Ini
    { wch: 8 },  // H - Mês Fim
    { wch: 8 },  // I - Ano Fim
    { wch: 12 }, // J - Combustível
    { wch: 20 }, // K - Cód Motor
    { wch: 8 },  // L - ABS
    { wch: 8 },  // M - Dir Hidráulica
    { wch: 8 },  // N - Ar Cond
    { wch: 8 },  // O - Transmissão
    { wch: 8 },  // P - Localização
    { wch: 8 },  // Q - Lado
    { wch: 40 }, // R - Aplicação
    { wch: 40 }, // S - E-commerce
  ];

  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "Importação Certtus");

  const filename = `certtus_${partId || "peca"}_${new Date().toISOString().split("T")[0]}.xlsx`;
  XLSX.writeFile(workbook, filename);
};
