import sqlite3, json, os, asyncio, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
DB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "catalogo.db"))

c = sqlite3.connect(DB)
cols = [r[1] for r in c.execute("pragma table_info(provedores)")]
print("cols:", cols)
mapeamento = json.dumps({"brand_slug": "wasco"})
ex = c.execute("select id from provedores where slug='wasco'").fetchone()
if ex:
    c.execute("update provedores set nome=?, url=?, tipo=?, mapeamento=?, ativo=1 where id=?",
              ("DHF WASCO", "https://buscanarede.com.br/wasco", "wasco", mapeamento, ex[0]))
else:
    c.execute("insert into provedores (nome, slug, url, tipo, mapeamento, ativo) values (?,?,?,?,?,1)",
              ("DHF WASCO", "wasco", "https://buscanarede.com.br/wasco", "wasco", mapeamento))
c.commit()
row = c.execute("select * from provedores where slug='wasco'").fetchone()
print(dict(zip(cols, row)))

if len(sys.argv) > 1:
    from app.providers.provider_factory import get_provider  # noqa
    from types import SimpleNamespace
    cfg = SimpleNamespace(**dict(zip(cols, row)))
    p = get_provider(cfg)
    res = asyncio.run(p.buscar(sys.argv[1]))
    print(f"{len(res)} resultados")
    for r in res[:3]:
        print(json.dumps(r, ensure_ascii=False, default=str)[:1200])
