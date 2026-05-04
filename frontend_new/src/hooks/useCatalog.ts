import { useState, useEffect, useMemo, useRef } from "react";
import { searchApi, configApi } from "../services/api";
import { useAutomakerCache } from "./useAutomakerCache";
import { generateUniqueReferences, copyToClipboard as performCopy } from "../utils/clipboard";
import JSZip from "jszip";
export const useCatalog = () => {
  const { automakers } = useAutomakerCache();
  const [partId, setPartId] = useState("");
  const [filterText, setFilterText] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 30; // 30 itens por página
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [provedores, setProvedores] = useState<any[]>([]);
  const [selectedProvedor, setSelectedProvedor] = useState<number | "">("");
  const [agrupar, setAgrupar] = useState(true);
  const abortControllerRef = useRef<AbortController | null>(null);
  const defaultFields: Record<string, boolean> = {
    marca: true,
    codigo: false,
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
  };

  const [visibleFields, setVisibleFieldsState] = useState<any>(() => {
    try {
      const saved = localStorage.getItem('visibleFieldsDefault');
      if (saved) return { ...defaultFields, ...JSON.parse(saved) };
    } catch {}
    return defaultFields;
  });

  // Wrapper que salva no localStorage toda vez que o usuário altera
  const setVisibleFields = (updater: any) => {
    setVisibleFieldsState((prev: any) => {
      const next = typeof updater === 'function' ? updater(prev) : updater;
      try { localStorage.setItem('visibleFieldsDefault', JSON.stringify(next)); } catch {}
      return next;
    });
  };

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

  // Removida a sobreposição automática de visibilidade para manter os filtros globais sob controle do usuário

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
      codigo: "Cód. Peça",
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

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!partId) return;

    // Se já houver uma busca em andamento, cancelamos ela antes de começar a nova
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const controller = new AbortController();
    abortControllerRef.current = controller;

    setResults([]);
    setFilterText("");
    setCurrentPage(1);
    setLoading(true);

    try {
      if (selectedProvedor) {
        const p = provedores.find(prov => prov.id === selectedProvedor);
        const response = await searchApi.buscarPeca(
          partId,
          [selectedProvedor as number],
          agrupar,
          { signal: controller.signal }
        );
        const cleanedData = response.data.map((r: any) => ({
          ...r,
          marca: r.marca && r.marca.trim() ? r.marca : (r.provedor || p?.nome || "---").toUpperCase()
        }));
        const sorted = cleanedData.sort(compareResults);
        setResults(sorted);
      } else {
        const promises = provedores.map(async (p) => {
          try {
            const response = await searchApi.buscarPeca(
              partId, 
              [p.id], 
              agrupar,
              { signal: controller.signal }
            );
            if (response.data && response.data.length > 0) {
              const cleanedData = response.data.map((r: any) => ({
                ...r,
                marca: r.marca && r.marca.trim() ? r.marca : (r.provedor || p.nome || "---").toUpperCase()
              }));
              setResults((prev) => {
                const combined = [...prev, ...cleanedData];
                return combined.sort(compareResults);
              });
            }
          } catch (err: any) {
            if (err.name !== 'AbortError' && err.name !== 'CanceledError') {
              console.error(`Erro ao buscar no provedor ${p.nome}:`, err);
            }
          }
        });

        await Promise.allSettled(promises);
      }
    } catch (error: any) {
      if (error.name === 'AbortError' || error.name === 'CanceledError') {
        console.log("Busca global cancelada pelo usuário ou por nova digitação.");
      } else {
        console.error("Erro na busca:", error);
        alert("Erro ao realizar busca. Verifique se o backend está rodando.");
      }
    } finally {
      // Só desativa o loading se for o controller atual (para não bugar com cancelamentos rápidos)
      if (abortControllerRef.current === controller) {
        setLoading(false);
        abortControllerRef.current = null;
      }
    }
  };

  const cancelSearch = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setLoading(false);
  };


  const uniqueReferences = useMemo(() => {
    return generateUniqueReferences(results);
  }, [results]);

  const copyToClipboard = (mode: "completa" | "intermediaria" | "agrupada") => {
    performCopy(mode, results, visibleFields, automakers, uniqueReferences);
  };

  // Lógica para processar os resultados que serão EXIBIDOS na tela
  const displayResults = useMemo(() => {
    if (results.length === 0) return [];

    // 1. FILTRAGEM DINÂMICA LOCAL (Varre colunas VISÍVEIS)
    let filtered = results;
    if (filterText) {
      const lowerFilter = filterText.toLowerCase();
      filtered = results.filter((res) => {
        return Object.entries(res).some(([key, val]) => {
          // Ignora campos de controle ou ocultos para evitar falsos positivos
          if (visibleFields[key] === false) return false;
          return String(val).toLowerCase().includes(lowerFilter);
        });
      });
    }

    // Se "Agrupar Resultados" estiver desligado no topo, mostramos tudo individual
    if (!agrupar) return filtered.sort(compareResults);

    const groups: any = {};
    filtered.forEach((res) => {
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
      if (visibleFields.observacao) keyParts.push(res.observacao);
      if (visibleFields.ficha_tecnica && res.ficha_tecnica) {
        // Serializa a ficha técnica para a chave
        keyParts.push(JSON.stringify(res.ficha_tecnica));
      }

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
  }, [results, visibleFields, agrupar, filterText]);

  const totalPages = Math.max(1, Math.ceil(displayResults.length / itemsPerPage));

  // 2. Fatiamento para Paginação
  const paginatedResults = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return displayResults.slice(start, start + itemsPerPage);
  }, [displayResults, currentPage, itemsPerPage]);

  const clearResults = () => {
    setResults([]);
    setPartId("");
    setFilterText("");
    setCurrentPage(1);
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
    paginatedResults,
    filterText,
    setFilterText,
    currentPage,
    setCurrentPage,
    totalPages,
    handleSearch,
    getFieldLabel,
    copyToClipboard,
    clearResults,
    downloadAllImages,
    cancelSearch,
  };

};
