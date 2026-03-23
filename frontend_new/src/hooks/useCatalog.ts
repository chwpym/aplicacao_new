import { useState, useEffect, useMemo } from "react";
import { searchApi, configApi } from "../services/api";
import JSZip from "jszip";

export const useCatalog = () => {
  const [partId, setPartId] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [provedores, setProvedores] = useState<any[]>([]);
  const [selectedProvedor, setSelectedProvedor] = useState<number | "">("");
  const [agrupar, setAgrupar] = useState(true);
  const [visibleFields, setVisibleFields] = useState<any>({
    marca: true,
    veiculo: true,
    modelo: true,
    versao: true,
    motor: true,
    configuracao_motor: true,
    combustivel: true,
    ano: true,
    imagem: false,
    referencias: false,
    observacao: false,
    posicao: false,
    lado: false,
    direcao: false,
    sistema_freio: false,
    restricao: false,
    apenas: false,
    ficha_tecnica: true,
  });

  useEffect(() => {
    fetchProvedores();
  }, []);

  const fetchProvedores = async () => {
    try {
      const response = await configApi.getProvedores();
      const ativos = response.data
        .filter((p: any) => p.ativo)
        .sort((a: any, b: any) => a.nome.localeCompare(b.nome));

      setProvedores(ativos);
    } catch (error) {
      console.error("Erro ao buscar provedores:", error);
    }
  };

  // Atualiza visibilidade de campos conforme o provedor selecionado
  useEffect(() => {
    if (selectedProvedor) {
      const prov = provedores.find(
        (p) => String(p.id) === String(selectedProvedor),
      );
      if (prov && prov.mapeamento) {
        try {
          const map = JSON.parse(prov.mapeamento);
          if (map.visibility) {
            setVisibleFields((prev: any) => ({
              ...prev,
              ...map.visibility,
            }));
          }
        } catch {}
      }
    }
  }, [selectedProvedor, provedores]);

  const getFieldLabel = (field: string) => {
    if (selectedProvedor) {
      const prov = provedores.find(
        (p) => String(p.id) === String(selectedProvedor),
      );
      if (prov) {
        // Tenta extrair do mapeamento JSON
        if (prov.mapeamento) {
          try {
            const map = JSON.parse(prov.mapeamento);
            if (map.labels && map.labels[field]) {
              return map.labels[field];
            }
          } catch {}
        }


      }
    }

    const defaults: Record<string, string> = {
      marca: "Marca Peça",
      veiculo: "Montadora",
      modelo: "Veículo",
      versao: "Modelo",
      motor: "Motor",
      configuracao_motor: "Config. Motor",
      combustivel: "Combustível",
      ano: "Ano",
      imagem: "Imagens",
      referencias: "Referências OE",
      observacao: "Observações",
      posicao: "Posição",
      lado: "Lado",
      direcao: "Direção",
      sistema_freio: "Sistema Freio",
      restricao: "Restrição",
      apenas: "Apenas",
      ficha_tecnica: "Ficha Técnica",
    };

    return defaults[field] || field.replace("_", " ");
  };

  const compareResults = (a: any, b: any) => {
    const priority = [
      "marca",
      "veiculo",
      "modelo",
      "versao",
      "motor",
      "configuracao_motor",
      "combustivel",
      "posicao",
      "lado",
      "ano_inicio",
    ];

    for (const field of priority) {
      // Se o campo for 'ano_inicio', verificamos se 'ano' está visível
      const visibilityKey = field === "ano_inicio" ? "ano" : field;
      if (visibleFields[visibilityKey]) {
        const valA = String(a[field] || "").trim();
        const valB = String(b[field] || "").trim();
        if (valA !== valB) {
          // Ordenação numérica para ano, alfabética para o resto
          if (field === "ano_inicio") {
            return (Number(a[field]) || 0) - (Number(b[field]) || 0);
          }
          return valA.localeCompare(valB);
        }
      }
    }
    return 0;
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!partId) return;

    setLoading(true);
    try {
      // Passa apenas o provedor selecionado
      const response = await searchApi.buscarPeca(
        partId,
        selectedProvedor ? [selectedProvedor as number] : undefined,
        agrupar,
      );
      // Ordenação inicial
      const sorted = response.data.sort(compareResults);
      setResults(sorted);
    } catch (error) {
      console.error("Erro na busca:", error);
      alert("Erro ao realizar busca. Verifique se o backend está rodando.");
    } finally {
      setLoading(false);
    }
  };

  const formatYearShort = (year: number | string | null | undefined) => {
    if (!year) return "";
    const s = year.toString();
    return s.length >= 4 ? s.substring(2) : s;
  };

  const uniqueReferences = useMemo(() => {
    const brands: Record<string, Set<string>> = {};
    results.forEach((res) => {
      if (res.referencias) {
        // Tenta split por ' | ' primeiro, depois por outros possíveis separadores
        res.referencias.split(/\s*\|\s*/).forEach((ref: string) => {
          // Tenta split por ': ' (com espaço) ou ':' (sem espaço)
          const parts = ref.split(/:\s*/);
          if (parts.length >= 2) {
            const brand = parts[0].trim();
            const code = parts.slice(1).join(":").trim();
            if (brand && code) {
              const cleanBrand = brand
                .toUpperCase()
                .replace(" ORIGINAL", "")
                .replace("ORIGINAL ", "");
              if (!brands[cleanBrand]) brands[cleanBrand] = new Set();
              brands[cleanBrand].add(code);
            }
          }
        });
      }
    });
    return brands;
  }, [results]);

  const copyToClipboard = (mode: "completa" | "intermediaria" | "agrupada") => {
    if (results.length === 0) return;

    let text = "";

    // Sempre ordena antes de copiar, seguindo a lógica da tela
    const sortedResults = [...results].sort(compareResults);

    if (mode === "completa") {
      const lines = sortedResults
        .map((res) => {
          const parts = [];
          if (visibleFields.marca) parts.push(res.marca);
          if (visibleFields.veiculo) parts.push(res.veiculo);
          if (visibleFields.modelo) parts.push(res.modelo);
          if (visibleFields.versao) parts.push(res.versao);
          if (visibleFields.motor) parts.push(res.motor);
          if (visibleFields.configuracao_motor)
            parts.push(res.configuracao_motor);
          if (visibleFields.combustivel) parts.push(res.combustivel);
          if (visibleFields.posicao) parts.push(res.posicao);
          if (visibleFields.lado) parts.push(res.lado);
          if (visibleFields.direcao) parts.push(res.direcao);
          if (visibleFields.sistema_freio) parts.push(res.sistema_freio);
          if (visibleFields.restricao) parts.push(res.restricao);
          if (visibleFields.apenas) parts.push(res.apenas);
          if (visibleFields.ano) {
            const anoStr =
              res.ano_inicio || res.ano_fim
                ? `${res.ano_inicio || ""}...${res.ano_fim || ""}`
                : "";
            if (anoStr) parts.push(anoStr);
          }
          if (visibleFields.referencias) parts.push(res.referencias);
          return parts.join(" ").replace(/\s+/g, " ").trim();
        })
        .filter((line) => line.length > 0);

      text = Array.from(new Set(lines)).join("\n");
    } else {
      const groups: any = {};
      sortedResults.forEach((res) => {
        const dynamicKeyParts = [];
        if (visibleFields.marca) dynamicKeyParts.push(res.marca);
        if (visibleFields.veiculo) dynamicKeyParts.push(res.veiculo);
        if (visibleFields.modelo) dynamicKeyParts.push(res.modelo);
        if (visibleFields.versao) dynamicKeyParts.push(res.versao);
        if (visibleFields.motor) dynamicKeyParts.push(res.motor);
        if (visibleFields.configuracao_motor)
          dynamicKeyParts.push(res.configuracao_motor);
        if (visibleFields.combustivel) dynamicKeyParts.push(res.combustivel);
        if (visibleFields.posicao) dynamicKeyParts.push(res.posicao);
        if (visibleFields.lado) dynamicKeyParts.push(res.lado);
        if (visibleFields.direcao) dynamicKeyParts.push(res.direcao);
        if (visibleFields.sistema_freio)
          dynamicKeyParts.push(res.sistema_freio);
        if (visibleFields.restricao) dynamicKeyParts.push(res.restricao);
        if (visibleFields.apenas) dynamicKeyParts.push(res.apenas);

        const key = dynamicKeyParts.join("|") || "default";

        if (!groups[key]) {
          groups[key] = {
            parts: dynamicKeyParts,
            anos: [],
            items: [],
          };
        }
        groups[key].anos.push({ start: res.ano_inicio, end: res.ano_fim });
        groups[key].items.push(res);
      });

      // Grupos já estão ordenados porque percorremos sortedResults
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
            lines.push(
              `${g.parts.join(" ")} ${range}`.replace(/\s+/g, " ").trim(),
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
          return `${g.parts.join(" ")} ${yearRange}`
            .replace(/\s+/g, " ")
            .trim();
        });
        text = lines.join("\n");
      }
    }

    if (Object.keys(uniqueReferences).length > 0) {
      text += "\n\nORIGINAL:";
      Object.entries(uniqueReferences).forEach(([brand, codes]) => {
        // Remove espaços duplos e garante formatação limpa
        const codesList = Array.from(codes as Set<string>)
          .sort()
          .join(" - ");
        text += `\n${brand}  ${codesList}`;
      });
    }

    navigator.clipboard.writeText(text);
  };

  // Lógica para processar os resultados que serão EXIBIDOS na tela
  const displayResults = useMemo(() => {
    if (results.length === 0) return [];

    // Se "Agrupar Resultados" estiver desligado no topo, mostramos tudo individual
    if (!agrupar) return results;

    const groups: any = {};
    results.forEach((res) => {
      // Chave baseada apenas no que está visível
      const keyParts = [];
      if (visibleFields.marca) keyParts.push(res.marca);
      if (visibleFields.veiculo) keyParts.push(res.veiculo);
      if (visibleFields.modelo) keyParts.push(res.modelo);
      if (visibleFields.motor) keyParts.push(res.motor);
      if (visibleFields.configuracao_motor)
        keyParts.push(res.configuracao_motor);
      if (visibleFields.combustivel) keyParts.push(res.combustivel);
      if (visibleFields.posicao) keyParts.push(res.posicao);
      if (visibleFields.lado) keyParts.push(res.lado);
      if (visibleFields.direcao) keyParts.push(res.direcao);
      if (visibleFields.sistema_freio) keyParts.push(res.sistema_freio);
      if (visibleFields.restricao) keyParts.push(res.restricao);
      if (visibleFields.apenas) keyParts.push(res.apenas);

      const key = keyParts.join("|") || "default";

      if (!groups[key]) {
        groups[key] = {
          ...res, // Pega os dados base do primeiro item
          anos: [],
        };
      }
      if (res.ano_inicio || res.ano_fim) {
        groups[key].anos.push({ start: res.ano_inicio, end: res.ano_fim });
      }
    });

    // Transforma os grupos em linhas de exibição
    const processed: any[] = [];
    Object.values(groups).forEach((g: any) => {
      // No modo de exibição, vamos manter os ranges de anos organizados (similar ao INTERM)
      const uniqueRanges = new Set<string>();
      g.anos.forEach((a: any) => {
        uniqueRanges.add(`${a.start}...${a.end}`);
      });

      Array.from(uniqueRanges)
        .sort()
        .forEach((range) => {
          const [start, end] = range.split("...");
          processed.push({
            ...g,
            // Garante que start/end sejam tratados corretamente para ordenação posterior
            ano_inicio:
              start !== "undefined" && start !== "null" && start !== ""
                ? isNaN(Number(start))
                  ? start
                  : Number(start)
                : null,
            ano_fim:
              end !== "undefined" && end !== "null" && end !== ""
                ? isNaN(Number(end))
                  ? end
                  : Number(end)
                : null,
          });
        });

      // Se não tiver anos, adiciona a linha base
      if (g.anos.length === 0) {
        processed.push(g);
      }
    });

    // Ordenação dinâmica final baseada no que está visível
    return processed.sort(compareResults);
  }, [results, visibleFields, agrupar]);

  const clearResults = () => {
    setResults([]);
    setPartId("");
  };

  const downloadAllImages = async () => {
    const imagesToDownload: { url: string; name: string }[] = [];
    const seenUrls = new Set<string>();

    results.forEach((res) => {
      const allImgs =
        res.imagens && res.imagens.length > 0
          ? res.imagens
          : res.image || res.imagem
            ? [res.image || res.imagem]
            : [];
      allImgs.forEach((url: string, imgIdx: number) => {
        if (url && url.startsWith("http") && !seenUrls.has(url)) {
          seenUrls.add(url);
          // Como as fotos são da PEÇA, usamos o código ou marca para o nome
          // Extraímos o nome do arquivo da URL original para manter extensões e sufixos (ex: WO-545B.jpg)
          const urlPath =
            url.split("/").pop()?.split("?")[0] || `imagem_${imgIdx}.jpg`;
          const fileName = `${res.marca || "PECA"}_${urlPath}`.replace(
            /[^a-z0-9._-]/gi,
            "_",
          );
          imagesToDownload.push({ url, name: fileName });
        }
      });
    });

    if (imagesToDownload.length === 0) {
      alert("Nenhuma imagem encontrada para baixar.");
      return;
    }

    setLoading(true);
    const zip = new JSZip();

    try {
      const downloadPromises = imagesToDownload.map(async (img) => {
        try {
          // Usa o proxy do backend para evitar CORS
          const proxyUrl = `http://localhost:8000/search/proxy/image?url=${encodeURIComponent(img.url)}`;
          const response = await fetch(proxyUrl);
          if (!response.ok)
            throw new Error(`HTTP error! status: ${response.status}`);
          const blob = await response.blob();
          zip.file(img.name, blob);
        } catch (err) {
          console.error(`Falha ao baixar imagem via proxy: ${img.url}`, err);
        }
      });

      await Promise.all(downloadPromises);

      const content = await zip.generateAsync({ type: "blob" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(content);
      link.download = `imagens_${partId || "busca"}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error("Erro ao gerar ZIP:", error);
      alert("Erro ao compactar imagens.");
    } finally {
      setLoading(false);
    }
  };

  return {
    partId,
    setPartId,
    loading,
    results,
    provedores,
    selectedProvedor,
    setSelectedProvedor,
    agrupar,
    setAgrupar,
    visibleFields,
    setVisibleFields,
    uniqueReferences,
    displayResults,
    handleSearch,
    getFieldLabel,
    copyToClipboard,
    clearResults,
    downloadAllImages,
  };
};
