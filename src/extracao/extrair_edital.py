import json
from pathlib import Path
from datetime import datetime
import fitz

def processar_edital_pdf(caminho_pdf: str, pasta_saida: str) -> dict:
    """
    Lê um edital em PDF, extrai o texto por página, salva em .txt
    e gera metadados rastreáveis em .json (Nível Júnior -> Pleno).
    """
    arquivo = Path(caminho_pdf)
    if not arquivo.exists():
        raise FileNotFoundError(f"Edital não encontrado: {arquivo}")

    saida_dir = Path(pasta_saida)
    saida_dir.mkdir(parents=True, exist_ok=True)

    paginas_extraidas = []
    texto_completo = []

    # Abre o PDF com gerenciamento seguro de contexto
    with fitz.open(arquivo) as doc:
        total_paginas = len(doc)
        for indice, pagina in enumerate(doc, start=1):
            texto_pag = pagina.get_text("text").strip()
            texto_completo.append(f"--- PÁGINA {indice} ---\n{texto_pag}")
            paginas_extraidas.append({
                "arquivo_origem": arquivo.name,
                "pagina": indice,
                "caracteres": len(texto_pag),
                "conteudo": texto_pag
            })

    # 1. Salva o texto bruto consolidado em .txt
    nome_base = arquivo.stem
    caminho_txt = saida_dir / f"{nome_base}_extraido.txt"
    caminho_txt.write_text("\n\n".join(texto_completo), encoding="utf-8")

    # 2. Salva metadados + páginas em .json para o Apache Hop / Postgres
    resultado = {
        "arquivo_origem": arquivo.name,
        "data_extracao": datetime.now().isoformat(),
        "total_paginas": total_paginas,
        "paginas": paginas_extraidas
    }
    caminho_json = saida_dir / f"{nome_base}_metadados.json"
    caminho_json.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] {arquivo.name}: {total_paginas} páginas processadas.")
    return resultado

if __name__ == "__main__":
    # Raiz do projeto (projeto-concursos), calculada a partir deste arquivo,
    # para o script funcionar independente da pasta de onde for executado
    raiz = Path(__file__).resolve().parents[2]
    pasta_brutos = raiz / "dados" / "brutos"
    pasta_saida = raiz / "dados" / "temporarios"

    pdfs = sorted(pasta_brutos.glob("*.pdf"))
    if not pdfs:
        print(f"Nenhum PDF encontrado em {pasta_brutos}")

    for pdf in pdfs:
        try:
            processar_edital_pdf(caminho_pdf=str(pdf), pasta_saida=str(pasta_saida))
        except Exception as erro:
            # Um PDF com problema não interrompe os demais
            print(f"[ERRO] {pdf.name}: {erro}")