"""Baixa do Banco Central (SGS) as séries usadas nas Calculadoras do portal e grava data/indices.json."""
import datetime as dt, json, os, time, urllib.request

MENSAIS = {  # código SGS: variação mensal em %
    "ipca": 433, "igpm": 189, "inpc": 188, "igpdi": 190, "incc": 192,
    "selic": 4390, "cdi": 4391,
}
POUPANCA = 195  # rentabilidade da poupança por data de aniversário (regra nova, desde 04/05/2012)
INICIO = 2000
SAIDA = "data/indices.json"


def baixa(codigo, ini, fim):
    url = (f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json"
           f"&dataInicial={ini:%d/%m/%Y}&dataFinal={fim:%d/%m/%Y}")
    for tentativa in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"Accept": "application/json"}), timeout=60) as r:
                return json.load(r)
        except Exception as e:
            erro = e
            time.sleep(2 ** tentativa * 3)
    raise erro


def janelas(ini, fim, anos=9):
    a = ini
    while a <= fim:
        b = min(dt.date(a.year + anos, 12, 31), fim)
        yield a, b
        a = b + dt.timedelta(days=1)


def main():
    hoje = dt.date.today()
    antigo = {}
    if os.path.exists(SAIDA):
        antigo = json.load(open(SAIDA, encoding="utf-8"))
    out = {"atualizado": hoje.isoformat(), "fonte": "Banco Central do Brasil, SGS", "m": {}, "poup": {}}
    for nome, cod in MENSAIS.items():
        try:
            serie = {}
            for a, b in janelas(dt.date(INICIO, 1, 1), hoje):
                for x in baixa(cod, a, b):
                    d, m, y = x["data"].split("/")
                    serie[f"{y}-{m}"] = round(float(x["valor"]), 4)
            out["m"][nome] = dict(sorted(serie.items()))
        except Exception as e:
            print("falhou", nome, e)
            if nome in antigo.get("m", {}):
                out["m"][nome] = antigo["m"][nome]
    try:
        poup = {}
        for a, b in janelas(dt.date(2012, 5, 4), hoje):
            for x in baixa(POUPANCA, a, b):
                d, m, y = x["data"].split("/")
                poup[f"{y}-{m}-{d}"] = round(float(x["valor"]), 4)
        out["poup"] = dict(sorted(poup.items()))
    except Exception as e:
        print("falhou poupança", e)
        out["poup"] = antigo.get("poup", {})
    os.makedirs("data", exist_ok=True)
    json.dump(out, open(SAIDA, "w", encoding="utf-8"), separators=(",", ":"))
    print({k: len(v) for k, v in out["m"].items()}, "poupança", len(out["poup"]))


main()
