import React, { useState, useEffect } from "react";
import {
  X,
  Save,
  Shield,
  Database,
  Globe,
  RefreshCcw,
  HelpCircle,
  Search,
  FlaskConical,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import FieldManager from "./FieldManager";

interface ProvedorFormProps {
  provedor?: any;
  onSave: (data: any) => void;
  onCancel: () => void;
}

const GRAPHQL_TEMPLATE = `query getProduct($id: String!, $market: MarketType!) {
  product(id: $id, market: $market) {
    id
    partNumber
    crossReferences {
      brand { name }
      partNumber
    }
    vehicles {
      brand
      name
      model
      engineName
      engineConfiguration
      startYear
      endYear
      note
    }
    images {
      imageUrl
    }
  }
}`;

const ProvedorForm: React.FC<ProvedorFormProps> = ({
  provedor,
  onSave,
  onCancel,
}) => {
  const [formData, setFormData] = useState({
    nome: provedor?.nome || "",
    url: provedor?.url || "",
    tipo: provedor?.tipo || "graphql",
    ativo: provedor?.ativo ?? true,
    headers: provedor?.headers || "{}",
    query: provedor?.query || "",
    login_required: provedor?.login_required ?? false,
    username: provedor?.username || "",
    password: provedor?.password || "",
    mapeamento: provedor?.mapeamento || "{}",
  });

  const [showHelp, setShowHelp] = useState(false);
  const navigate = useNavigate();

  const handleTestPlayground = () => {
    // Salva o rascunho atual para o playground carregar
    const draft = {
      ...formData,
      id: Date.now(),
      date: new Date().toISOString(),
    };
    localStorage.setItem("playground_auto_load", JSON.stringify(draft));
    navigate("/playground");
  };

  // Aplicar template automático ao trocar para GraphQL
  useEffect(() => {
    if (formData.tipo === "graphql" && !formData.query && !provedor) {
      setFormData((prev: any) => ({ ...prev, query: GRAPHQL_TEMPLATE }));
    }
  }, [formData.tipo, provedor]);

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
    >,
  ) => {
    const { name, value, type } = e.target as HTMLInputElement;
    const val =
      type === "checkbox" ? (e.target as HTMLInputElement).checked : value;

    setFormData((prev: any) => {
      const next = { ...prev, [name]: val };

      // Sugestão automática de mapeamento para REST ou DS
      if (name === "nome" || name === "tipo") {
        const currentNome =
          name === "nome"
            ? String(value).toUpperCase()
            : (next.nome || "").toUpperCase();
        const currentTipo = name === "tipo" ? value : next.tipo;

        if (name === "tipo") {
          const isUrlDefaultOrEmpty =
            !next.url ||
            next.url.includes("catalogofraga") ||
            next.url.includes("ds.ind.br") ||
            next.url.includes("viemar") ||
            next.url.includes("exemplo.com");

          if (value === "graphql") {
            next.query = GRAPHQL_TEMPLATE;
            if (!next.headers || next.headers === "{}") {
              next.headers = JSON.stringify(
                {
                  Origin: "https://[BRAND].catalogofraga.com.br",
                  Referer: "https://[BRAND].catalogofraga.com.br/",
                },
                null,
                2,
              );
            }
            if (isUrlDefaultOrEmpty) {
              next.url = "https://bff.catalogofraga.com.br/gateway/graphql";
            }
            next.mapeamento = JSON.stringify(
              {
                marca: "brand",
                veiculo: "name",
                motor: "engineName",
                ano_inicio: "startYear",
                imagem: "images",
              },
              null,
              2,
            );
          } else if (value === "ds") {
            next.mapeamento = JSON.stringify(
              {
                container: ".jq-apps tr",
                marca: "td.montadora",
                veiculo: "td.modelo",
                motor: "td.motor",
                configuracao_motor: "td.complemento",
                observacao: "td.observacoes",
                ano_inicio: "td.ano",
                imagem: ".pgwSlider img",
                referencias: ".jq-codes tr",
                labels: {
                  configuracao_motor: "Combustível",
                  observacao: "Observações",
                },
              },
              null,
              2,
            );
            if (isUrlDefaultOrEmpty) {
              next.url = "https://www.ds.ind.br/pt/busca-full?q={id}";
            }
          } else if (value === "cofap") {
            if (isUrlDefaultOrEmpty) {
              next.url = "https://bff.catalogofraga.com.br/gateway/graphql";
            }
            next.headers = JSON.stringify(
              {
                Origin: "https://cofap.catalogofraga.com.br",
                Referer: "https://cofap.catalogofraga.com.br/",
              },
              null,
              2,
            );
            next.query = GRAPHQL_TEMPLATE;
            next.mapeamento = JSON.stringify(
              {
                marca: "brand",
                veiculo: "name",
                motor: "engineName",
                ano_inicio: "startYear",
                imagem: "images",
              },
              null,
              2,
            );
          } else if (value === "viemar") {
            if (isUrlDefaultOrEmpty) {
              next.url = "https://catalogo.viemar.com.br/catalog/search/catalog/code";
            }
            next.query = JSON.stringify(
              {
                searchCode: "{id}",
                cardMode: true,
              },
              null,
              2,
            );
            next.headers = JSON.stringify(
              {
                accept: "application/json, text/plain, */*",
                "content-type": "application/json;charset=UTF-8",
              },
              null,
              2,
            );
            next.mapeamento = JSON.stringify(
              {
                marca: "brand.value",
                veiculo: "model.value",
                ano_inicio: "year.value",
                referencias: "crossReference.valueList",
              },
              null,
              2,
            );
          } else if (value === "scraper") {
            if (isUrlDefaultOrEmpty) {
              next.url = "https://www.site-exemplo.com/busca?q={id}";
            }
            next.mapeamento = JSON.stringify({ container: "body", marca: "h1" }, null, 2);
          } else if (value === "rest") {
            if (isUrlDefaultOrEmpty) {
              next.url = "https://api.exemplo.com/v1/produto/{id}";
            }
            if (!next.headers || next.headers === "{}") {
              next.headers = JSON.stringify(
                { Accept: "application/json", "Content-Type": "application/json" },
                null,
                2,
              );
            }
            next.mapeamento = JSON.stringify(
              {
                container: "Obj",
                marca: "Marca",
                veiculo: "Modelo",
                ano_inicio: "Ano",
              },
              null,
              2,
            );
          }
        }

        // Original DS specific logic, now integrated into the 'tipo' check
        if (currentNome === "DS" && name === "nome") {
          // Only apply if 'nome' is changed to 'DS'
          if (currentTipo === "rest") {
            next.mapeamento = JSON.stringify({
              marca: "brand",
              veiculo: "vehicle",
              motor: "engine",
              ano_inicio: "start_year",
              imagem: "image_url",
            });
          } else if (currentTipo === "ds") {
            // This block is now largely redundant due to the 'tipo' === 'ds' block above,
            // but keeping it for 'nome' change trigger if needed.
            // The 'tipo' change takes precedence for initial setup.
            if (!next.url || next.url.includes("busca-full")) {
              next.url = "https://www.ds.ind.br/pt/busca-full?q={id}";
            }
          }
        }
      }
      return next;
    });
  };

  const handleRestoreTemplate = () => {
    if (window.confirm("Deseja restaurar a query padrão para GraphQL?")) {
      setFormData((prev: any) => ({ ...prev, query: GRAPHQL_TEMPLATE }));
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
      <div className="bg-surface-light dark:bg-surface-dark w-full max-w-2xl rounded-2xl shadow-2xl flex flex-col max-h-[90vh] animate-in fade-in zoom-in duration-200">
        {/* Header */}
        <div className="p-6 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="bg-primary/10 p-2 rounded-lg text-primary">
              {provedor ? <RefreshCcw size={20} /> : <Database size={20} />}
            </div>
            <h2 className="text-xl font-bold">
              {provedor ? "Editar Provedor" : "Novo Provedor"}
            </h2>
          </div>
          <button
            onClick={onCancel}
            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-500 uppercase tracking-wider">
                Nome
              </label>
              <input
                name="nome"
                value={formData.nome}
                onChange={handleChange}
                placeholder="Ex: SABÓ, INDISA..."
                className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-2.5 outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-500 uppercase tracking-wider">
                Tipo
              </label>
              <select
                name="tipo"
                value={formData.tipo}
                onChange={handleChange}
                className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-2.5 outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all appearance-none"
              >
                <option value="graphql">GraphQL Fraga</option>
                <option value="autoexperts">
                  AutoExperts (Nativo/Multi-marcas)
                </option>
                <option value="ate">Catálogo ATE (Nativo)</option>
                <option value="rest">REST API / ERP (JSON Dinâmico)</option>
                <option value="ds">Robô Scraper (Site DS / Manual)</option>
                <option value="scraper">Scraper Genérico (Universal)</option>
                <option value="viemar">Viemar</option>
                <option value="cofap">Cofap (Fraga)</option>
                <option value="native">Provedor de Sistema (Nativo)</option>
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-500 uppercase tracking-wider">
              URL do Endpoint
            </label>
            <input
              name="url"
              value={formData.url}
              onChange={handleChange}
              placeholder="https://bff.catalogofraga.com.br/gateway/graphql"
              className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-2.5 outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all font-mono text-sm"
            />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="text-sm font-semibold text-slate-500 uppercase tracking-wider">
                Cabeçalhos JSON (Headers)
              </label>
              <span className="text-[10px] text-primary italic font-medium">
                Obrigatório para Fraga (Origin/Referer)
              </span>
            </div>
            <textarea
              name="headers"
              value={formData.headers}
              onChange={handleChange}
              rows={3}
              placeholder='{"Origin": "https://...", "Referer": "https://..."}'
              className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all font-mono text-xs custom-scrollbar"
            />
          </div>

          {(formData.tipo === "graphql" || formData.tipo === "cofap") && (
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <label className="text-sm font-semibold text-slate-500 uppercase tracking-wider">
                  Query GraphQL
                </label>
                <button
                  onClick={handleRestoreTemplate}
                  className="text-[10px] text-primary hover:underline flex items-center gap-1"
                >
                  <RefreshCcw size={10} /> Restaurar Padrão
                </button>
              </div>
              <textarea
                name="query"
                value={formData.query}
                onChange={handleChange}
                rows={8}
                className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all font-mono text-xs custom-scrollbar"
              />
            </div>
          )}

          {(formData.tipo === "autoexperts" ||
            formData.tipo === "ate" ||
            formData.tipo === "native") && (
            <div className="p-4 bg-primary/5 border border-primary/20 rounded-xl flex items-start gap-4">
              <RefreshCcw className="text-primary mt-1 shrink-0" size={20} />
              <div>
                <h4 className="text-sm font-bold text-primary mb-1">
                  PROVEDOR INTEGRADO PELO SISTEMA
                </h4>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Este provedor utiliza uma lógica nativa personalizada no
                  backend. Você pode ajustar o <strong>Nome</strong>, a{" "}
                  <strong>URL Base</strong> e os <strong>Cabeçalhos</strong>,
                  mas a estrutura de busca e extração de dados é otimizada via
                  código interno.
                </p>
              </div>
            </div>
          )}

          {(formData.tipo === "rest" ||
            formData.tipo === "ds" ||
            formData.tipo === "scraper") && (
            <div className="space-y-4 border-t border-slate-200 dark:border-slate-800 pt-4">
              <div className="flex justify-between items-center">
                <label className="text-sm font-semibold text-slate-500 uppercase tracking-wider">
                  {formData.tipo === "rest"
                    ? "Mapeamento JSON"
                    : "Seletores CSS (Scraper)"}
                </label>
                <span className="text-[10px] text-slate-400">
                  Define como extrair os dados
                </span>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {[
                  "container",
                  "product_link",
                  "marca",
                  "veiculo",
                  "modelo",
                  "motor",
                  "configuracao_motor",
                  "ano_inicio",
                  "ano_fim",
                  "imagem",
                  "image_pattern",
                  "referencias",
                  "ref_marca",
                  "ref_codigo",
                  "observacao",
                ].map((field) => (
                  <div key={field} className="space-y-1">
                    <label className="text-[10px] text-slate-400 uppercase font-bold">
                      {(() => {
                        const labels: Record<string, string> = {
                          veiculo: "Nome do Carro",
                          modelo: "Modelo / Versão",
                          configuracao_motor: "Combustível / Detalhes",
                          ano_inicio: "Ano Inicial",
                          ano_fim: "Ano Final",
                          image_pattern: "Padrão URL Imagem ({id})",
                          product_link: "Link da Página",
                          ref_marca: "Referência: Atributo Marca",
                          ref_codigo: "Referência: Atributo Código",
                        };
                        return (
                          labels[field] || field.toUpperCase().replace("_", " ")
                        );
                      })()}
                    </label>
                    <input
                      placeholder={
                        formData.tipo === "rest" || formData.tipo === "scraper"
                          ? `Ex: ${field}`
                          : `CSS: .${field}`
                      }
                      className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-1.5 text-xs outline-none focus:border-primary"
                      value={(() => {
                        try {
                          const m = JSON.parse(formData.mapeamento);
                          return m[field] || "";
                        } catch {
                          return "";
                        }
                      })()}
                      onChange={(e) => {
                        const val = e.target.value;
                        setFormData((prev: any) => {
                          let currentMap = {};
                          try {
                            currentMap = JSON.parse(prev.mapeamento);
                          } catch {}
                          const nextMap = { ...currentMap, [field]: val };
                          return {
                            ...prev,
                            mapeamento: JSON.stringify(nextMap),
                          };
                        });
                      }}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="space-y-4 pt-4 border-t border-slate-200 dark:border-slate-800">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Shield size={18} className="text-primary" />
                <span className="font-semibold">Requer Autenticação?</span>
              </div>
              <input
                type="checkbox"
                name="login_required"
                checked={formData.login_required}
                onChange={handleChange}
                className="w-5 h-5 rounded border-slate-300 text-primary focus:ring-primary"
              />
            </div>

            {formData.login_required && (
              <div className="grid grid-cols-2 gap-4 animate-in slide-in-from-top-2 duration-300">
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-slate-500 uppercase tracking-wider">
                    E-mail / Usuário
                  </label>
                  <input
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                    className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-2.5 outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-slate-500 uppercase tracking-wider">
                    Senha
                  </label>
                  <input
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-2.5 outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                  />
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center justify-between pt-4">
            <div className="flex items-center gap-2">
              <div
                className={`w-3 h-3 rounded-full ${formData.ativo ? "bg-emerald-500" : "bg-slate-300"}`}
              />
              <span className="font-semibold">Provedor Ativo</span>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                name="ativo"
                checked={formData.ativo}
                onChange={handleChange}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary"></div>
            </label>
          </div>

          {/* Novo Gerenciador de Campos / Labels */}
          <div className="pt-6 border-t border-slate-200 dark:border-slate-800">
            <FieldManager
              mapping={formData.mapeamento}
              onChange={(newMap) =>
                setFormData((prev) => ({ ...prev, mapeamento: newMap }))
              }
            />
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-slate-200 dark:border-slate-800 flex justify-between items-center bg-slate-50/50 dark:bg-slate-900/50 rounded-b-2xl">
          <button
            onClick={() => setShowHelp(!showHelp)}
            className="text-slate-500 hover:text-primary transition-colors flex items-center gap-2 text-sm font-medium"
          >
            <HelpCircle size={18} /> Ajuda
          </button>
          <div className="flex gap-3">
            <button
              onClick={onCancel}
              className="px-6 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 font-semibold hover:bg-slate-100 dark:hover:bg-slate-800 transition-all text-sm"
            >
              Cancelar
            </button>
            <button
              onClick={handleTestPlayground}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl border border-primary/20 bg-primary/5 text-primary font-bold hover:bg-primary/10 transition-all text-sm"
            >
              <FlaskConical size={18} />
              Testar no Playground
            </button>
            <button
              onClick={() => onSave(formData)}
              className="bg-primary hover:bg-primary-hover text-white px-8 py-2.5 rounded-xl font-bold flex items-center gap-2 transition-all shadow-lg shadow-primary/25 text-sm"
            >
              <Save size={18} /> Salvar Alterações
            </button>
          </div>
        </div>
      </div>

      {/* Help Lateral Panel - Simple Version */}
      {showHelp && (
        <div className="fixed inset-y-0 right-0 w-80 bg-surface-light dark:bg-surface-dark border-l border-slate-200 dark:border-slate-800 shadow-2xl z-[110] p-8 animate-in slide-in-from-right duration-300 custom-scrollbar overflow-y-auto">
          <div className="flex justify-between items-center mb-8">
            <h3 className="font-bold text-xl">Guia de Ajuda</h3>
            <button
              onClick={() => setShowHelp(false)}
              className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full"
            >
              <X size={20} />
            </button>
          </div>
          <div className="space-y-6 text-sm text-slate-500 leading-relaxed text-justify">
            <section>
              <h4 className="text-slate-900 dark:text-slate-100 font-bold mb-2 flex items-center gap-2">
                <Globe size={16} className="text-primary" /> Catálogos GraphQL
              </h4>
              <p>
                Para catálogos que usam a tecnologia **GraphQL Fraga**,
                selecione este tipo. A query será preenchida automaticamente.
              </p>
            </section>
            <section>
              <h4 className="text-slate-900 dark:text-slate-100 font-bold mb-2 flex items-center gap-2">
                <Search size={16} className="text-primary" /> REST API / ERP
              </h4>
              <p>
                Para buscar dados de um ERP ou servidor REST, use o **Mapeamento
                JSON**. Basta dizer ao sistema qual campo da API deles
                corresponde aos nossos campos (ex: `brand` &rarr; `Marca`).
              </p>
            </section>
            <section>
              <h4 className="text-slate-900 dark:text-slate-100 font-bold mb-2 flex items-center gap-2">
                <Database size={16} className="text-primary" /> Robô Scraper
              </h4>
              <p>
                Se o site não tem API, o robô Scraper pode ler os dados
                visualmente usando **seletores CSS**. É como dizer: "Olhe para a
                tabela e pegue o texto da primeira coluna".
              </p>
            </section>
            <section>
              <h4 className="text-slate-900 dark:text-slate-100 font-bold mb-2 flex items-center gap-2">
                <RefreshCcw size={16} className="text-primary" /> Sugestões
              </h4>
              <p>
                Ao digitar nomes como **DS**, o sistema tentará preencher o
                mapeamento ideal para você automaticamente.
              </p>
            </section>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProvedorForm;
