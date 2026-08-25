export const generateEtiquetaString = (results: any[]): string => {
  if (results.length === 0) return "";

  const montadorasModelos: Record<string, Set<string>> = {};

  results.forEach((res) => {
    let marca = res.veiculo || res.marca || "";
    let modelo = res.modelo || "";

    marca = marca.trim().toUpperCase();
    modelo = modelo.trim().toUpperCase();

    if (!marca) return;

    if (!montadorasModelos[marca]) {
      montadorasModelos[marca] = new Set();
    }
    if (modelo) {
      montadorasModelos[marca].add(modelo);
    }
  });

  const priorityBrands = [
    "VW", "VOLKSWAGEN", "GM", "CHEVROLET", "FIAT", "FORD", "TOYOTA",
    "HONDA", "HYUNDAI", "RENAULT", "NISSAN", "JEEP", "PEUGEOT", "CITROEN",
    "MITSUBISHI", "CAOA CHERY", "CHERY", "KIA", "AUDI", "BMW", "MERCEDES"
  ];

  const getBrandWeight = (b: string) => {
    let abrev = b;
    if (abrev === "CHEVROLET") abrev = "GM";
    if (abrev === "VOLKSWAGEN") abrev = "VW";
    const idx = priorityBrands.indexOf(abrev);
    return idx !== -1 ? idx : 999;
  };

  const sortedBrands = Object.keys(montadorasModelos).sort((a, b) => {
    const wA = getBrandWeight(a);
    const wB = getBrandWeight(b);
    if (wA !== wB) return wA - wB;
    return a.localeCompare(b);
  });

  const partes: string[] = [];
  const MAX_TOTAL_CHARS = 112; 
  const MUITAS_MARCAS = sortedBrands.length > 4;

  for (const marca of sortedBrands) {
    let marcaAbrev = marca;
    if (marcaAbrev === "CHEVROLET") marcaAbrev = "GM";
    if (marcaAbrev === "VOLKSWAGEN") marcaAbrev = "VW";

    const modelos = Array.from(montadorasModelos[marca]).sort();
    
    let textoAdicionar = "";
    if (MUITAS_MARCAS) {
      textoAdicionar = marcaAbrev;
    } else {
      if (modelos.length > 0) {
        textoAdicionar = `${marcaAbrev} ${modelos.join("/")}`;
      } else {
        textoAdicionar = marcaAbrev;
      }
    }
    
    const simulacao = partes.length > 0 ? partes.join(" - ") + " - " + textoAdicionar : textoAdicionar;
    if (simulacao.length > MAX_TOTAL_CHARS + 15) { 
      partes.push("+OUTROS");
      break;
    }

    partes.push(textoAdicionar);
  }

  let stringCompleta = partes.join(MUITAS_MARCAS ? " / " : " - ");

  const maxLineLength = 28;
  const maxLines = 4;
  const lines: string[] = [];

  let currentLine = "";
  const words = stringCompleta.split(/([ /-])/); 

  for (let i = 0; i < words.length; i++) {
    const word = words[i];
    
    if (currentLine.length + word.length <= maxLineLength) {
      currentLine += word;
    } else {
      if (currentLine.length > 0) {
        lines.push(currentLine.trim());
      }
      currentLine = word.trim() === "/" || word.trim() === "-" ? "" : word; 
      
      while (currentLine.length > maxLineLength) {
        lines.push(currentLine.substring(0, maxLineLength));
        currentLine = currentLine.substring(maxLineLength);
      }
    }

    if (lines.length >= maxLines) break; 
  }

  if (currentLine.length > 0 && lines.length < maxLines) {
    lines.push(currentLine.trim());
  }

  return lines.join("\n");
};

export const copyToClipboardEtiqueta = (results: any[]) => {
  const textToCopy = generateEtiquetaString(results);
  if (!textToCopy) return;

  try {
    navigator.clipboard.writeText(textToCopy);
  } catch (err) {
    console.error("Falha ao copiar etiqueta", err);
  }
};
