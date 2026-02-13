
import json
import sqlite3
import os

db_path = os.path.join("backend", "catalogo.db")

nome = "Wega Teste"
slug = "wega-teste"
url = "https://wega.wedigi.com.br/api/v1/produto?cod={id}"
tipo = "rest"
headers = json.dumps({
    "Origin": "https://wegamotors.com", 
    "Referer": "https://wegamotors.com/"
})
mapeamento = json.dumps({
    "container": "Obj.DetailApl",
    "marca": "Montadora",
    "veiculo": "Modelo",
    "modelo": "Modelo",
    "motor": "Motor",
    "configuracao_motor": "DescModelo",
    "ano_inicio": "Ano",
    "image_pattern": "https://admin.wegamotors.com/wp-content/imagens/{id}.jpg",
    "referencias": "root:Obj.DetailConv",
    "ref_marca": "Marca",
    "ref_codigo": "CodigoConcorrente"
}, indent=2)

def register():
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM provedores WHERE slug = ?", (slug,))
        cursor.execute("""
            INSERT INTO provedores (nome, slug, url, tipo, headers, mapeamento, ativo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (nome, slug, url, tipo, headers, mapeamento, 1))
        conn.commit()
        print(f"Sucesso: Provedor '{nome}' atualizado com imagens dinâmicas!")
        conn.close()
    except Exception as e:
        print(f"Erro ao cadastrar: {e}")

if __name__ == "__main__":
    register()
