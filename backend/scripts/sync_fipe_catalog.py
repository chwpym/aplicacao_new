import os
import json
import httpx
import asyncio
from datetime import datetime
from typing import Dict, List

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "app", "data", "automakers_catalog.json")

async def sync_catalog():
    print(f"[{datetime.now().isoformat()}] Iniciando Sincronização FIPE (BrasilAPI)...")
    
    # 1. Carregar Catálogo Atual
    catalog_data = {"last_update": "", "catalog": {}}
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            catalog_data = json.load(f)
    
    current_catalog = catalog_data.get("catalog", {})
    
    # 2. Buscar Marcas
    print("Buscando marcas de carros...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get("https://brasilapi.com.br/api/fipe/marcas/v1/carros")
            if resp.status_code != 200:
                print(f"Erro ao buscar marcas: {resp.status_code}")
                return
            
            marcas_fipe = resp.json()
            print(f"Encontradas {len(marcas_fipe)} marcas.")
            
            # 3. Para cada marca, buscar modelos
            for i, marca in enumerate(marcas_fipe):
                marca_nome = marca["nome"].upper()
                marca_id = marca["valor"]
                
                # Normalizações comuns
                if "VOLKSWAGEN" in marca_nome: marca_nome = "VW"
                if "CHEVROLET" in marca_nome: marca_nome = "GM"
                
                print(f"[{i+1}/{len(marcas_fipe)}] Processando {marca_nome}...")
                
                try:
                    url_modelos = f"https://brasilapi.com.br/api/fipe/veiculos/v1/carros/{marca_id}"
                    m_resp = await client.get(url_modelos)
                    
                    if m_resp.status_code == 200:
                        modelos_list = m_resp.json()
                        
                        if marca_nome not in current_catalog:
                            current_catalog[marca_nome] = []
                        
                        # Adiciona modelos novos (sem duplicar)
                        novos_count = 0
                        for m in modelos_list:
                            modelo_nome = m.get("modelo", "").upper()
                            if modelo_nome and modelo_nome not in current_catalog[marca_nome]:
                                current_catalog[marca_nome].append(modelo_nome)
                                novos_count += 1
                        
                        if novos_count > 0:
                            print(f"  + {novos_count} novos modelos adicionados para {marca_nome}")
                    else:
                        print(f"  ! Erro ao buscar modelos da marca {marca_nome}: {m_resp.status_code}")
                
                except Exception as e:
                    print(f"  ! Falha na marca {marca_nome}: {str(e)}")
                
                # Pequeno delay para não sobrecarregar a API e evitar rate limit
                await asyncio.sleep(0.5)
                
        except Exception as e:
            print(f"Erro geral na sincronização: {str(e)}")

    # 4. Salvar Catálogo Atualizado
    catalog_data["last_update"] = datetime.now().isoformat()
    catalog_data["catalog"] = current_catalog
    
    # Ordenar modelos alfabeticamente para ficar bonito
    for m in current_catalog:
        current_catalog[m].sort()
    
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n[{datetime.now().isoformat()}] Sincronização concluída com sucesso!")
    print(f"Arquivo salvo em: {DATA_PATH}")

if __name__ == "__main__":
    asyncio.run(sync_catalog())
