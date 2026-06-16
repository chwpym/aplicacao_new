import json
import os

def main():
    f_path = "d:/Dev/aplicacao_new/NEW_PROVIDER.txt"
    if not os.path.exists(f_path):
        print("Arquivo NEW_PROVIDER.txt não encontrado.")
        return
        
    with open(f_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Isola a parte do JSON (que fica antes da linha do curl)
    json_part = content.split("curl")[0].strip()
    
    try:
        data = json.loads(json_part)
        catalog_items = data.get("catalog", [])
        if not catalog_items:
            print("Nenhum item encontrado na lista de catálogo.")
            return
            
        first_item = catalog_items[0]
        print("=== CHAVES E VALORES DISPONÍVEIS NO PROVEDOR VIEMAR ===")
        for key, val in first_item.items():
            if val is None:
                print(f"\n- {key}: None")
                continue
                
            # Exibe os dados de forma estruturada baseando-se no tipo
            if isinstance(val, dict):
                # Se for dicionário com chaves comuns da Viemar (title, value, typeValue, subValue, valueList)
                value_field = val.get("value")
                sub_values = val.get("subValue", [])
                value_list = val.get("valueList", [])
                
                print(f"\n- {key} (Dicionário):")
                if val.get("title"):
                    print(f"  * Title: {val['title']}")
                if value_field:
                    print(f"  * Value: {value_field}")
                if value_list:
                    print(f"  * ValueList ({len(value_list)} itens): {[item.get('value') for item in value_list]}")
                if sub_values:
                    print(f"  * SubValue ({len(sub_values)} itens): {sub_values}")
            else:
                print(f"\n- {key}: {val}")
                
        # Inspeciona também a estrutura das aplicações aninhadas
        apps = first_item.get("application", [])
        if apps:
            print("\n=== ESTRUTURA DE UMA APLICAÇÃO ANINHADA (APPLICATION) ===")
            first_app = apps[0]
            for key, val in first_app.items():
                print(f"  - {key}: {val}")
                
    except Exception as e:
        print("Erro ao parsear o JSON:", e)

if __name__ == "__main__":
    main()
