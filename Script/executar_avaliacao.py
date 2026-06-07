#!/usr/bin/env python3
import argparse
import asyncio
import csv
import importlib.util
import json
import os
import re
import sys
import time
from pathlib import Path

import httpx


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OPENAI_MODEL_PADRAO = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
PONTUACOES_VALIDAS = {0, 40, 80, 120, 160, 200}

ARQUITETURAS = {
    "agente-unico": "agente_unico.py",
    "agentes-multiplos": "agentes_multiplos.py",
}

COLUNAS_CSV = [
    "id",
    "arquitetura",
    "provedor_llm",
    "modelo_llm",
    "nota_antiga",
    "nota_nova",
    "c1",
    "c2",
    "c3",
    "c4",
    "c5",
    "justificativa_c1",
    "justificativa_c2",
    "justificativa_c3",
    "justificativa_c4",
    "justificativa_c5",
    "diagnostico_geral",
    "tema",
    "c1_antiga",
    "c2_antiga",
    "c3_antiga",
    "c4_antiga",
    "c5_antiga",
    "arquivo_origem",
]

COLUNAS_FALHAS = [
    "id",
    "arquitetura",
    "arquivo_origem",
    "indice_global",
    "tentativas",
    "erro",
    "resposta_bruta",
]


def chave_natural(caminho):
    partes = re.split(r"(\d+)", str(caminho))
    return [int(parte) if parte.isdigit() else parte.lower() for parte in partes]


def achatar_registros(valor):
    if isinstance(valor, dict):
        yield valor
    elif isinstance(valor, list):
        for item in valor:
            yield from achatar_registros(item)
    else:
        raise ValueError("O corpus deve conter objetos JSON ou listas de objetos JSON.")


def carregar_corpus(caminho_corpus):
    caminho = Path(caminho_corpus)
    if caminho.is_dir():
        arquivos = sorted(caminho.glob("*.json"), key=chave_natural)
    elif caminho.is_file():
        arquivos = [caminho]
    else:
        raise FileNotFoundError(f"Corpus nao encontrado: {caminho}")

    if not arquivos:
        raise ValueError(f"Nenhum arquivo .json encontrado em: {caminho}")

    redacoes = []
    for arquivo in arquivos:
        with arquivo.open("r", encoding="utf-8") as f:
            dados = json.load(f)

        for indice_arquivo, entrada in enumerate(achatar_registros(dados)):
            validar_entrada(entrada, arquivo, indice_arquivo)
            redacoes.append({
                "entrada": entrada,
                "arquivo": str(arquivo),
                "indice_arquivo": indice_arquivo,
                "indice_global": len(redacoes) + 1,
            })

    return redacoes


def validar_entrada(entrada, arquivo, indice):
    campos = ["id", "tema", "texto", "nota", "competencias"]
    ausentes = [campo for campo in campos if campo not in entrada or entrada[campo] is None]
    if ausentes:
        raise ValueError(f"{arquivo} item {indice}: campos ausentes: {', '.join(ausentes)}")

    if not str(entrada.get("texto", "")).strip():
        raise ValueError(f"{arquivo} item {indice}: texto vazio")

    competencias = entrada.get("competencias")
    if not isinstance(competencias, list) or len(competencias) < 5:
        raise ValueError(f"{arquivo} item {indice}: competencias invalidas")


def carregar_arquitetura(nome_arquitetura):
    arquivo = Path(ARQUITETURAS[nome_arquitetura])
    if not arquivo.exists():
        raise FileNotFoundError(f"Arquivo da arquitetura nao encontrado: {arquivo}")

    spec = importlib.util.spec_from_file_location(nome_arquitetura.replace("-", "_"), arquivo)
    if spec is None or spec.loader is None:
        raise ImportError(f"Nao foi possivel carregar a arquitetura: {arquivo}")

    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)

    if not hasattr(modulo, "avaliar_redacao"):
        raise AttributeError(f"{arquivo} precisa expor a funcao async avaliar_redacao(...).")
    if not hasattr(modulo, "extrair_json"):
        raise AttributeError(f"{arquivo} precisa expor a funcao extrair_json(...).")

    return modulo


def base_ollama(url_generate):
    if url_generate.endswith("/api/generate"):
        return url_generate[:-len("/api/generate")]
    if url_generate.endswith("/api/chat"):
        return url_generate[:-len("/api/chat")]
    return url_generate.rstrip("/")


async def detectar_modelo_ollama():
    url_ps = f"{base_ollama(OLLAMA_URL)}/api/ps"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resposta = await client.get(url_ps)
        resposta.raise_for_status()
        dados = resposta.json()

    modelos = dados.get("models", [])
    if not modelos:
        raise RuntimeError(
            "Nenhum modelo esta carregado no Ollama. Abra outra sessao SSH e execute, por exemplo, "
            "`ollama run gemma3:latest`; depois rode este batch novamente."
        )

    primeiro = modelos[0]
    modelo = primeiro.get("name") or primeiro.get("model")
    if not modelo:
        raise RuntimeError("Ollama respondeu /api/ps, mas nao informou o nome do modelo.")

    return modelo


def inteiro(valor, padrao=0):
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        return padrao


def id_redacao(item):
    valor = item["entrada"].get("id")
    if valor is None or str(valor).strip() == "":
        return f"item-{item['indice_global']}"
    return str(valor).strip()


def notas_antigas(entrada):
    notas = [0, 0, 0, 0, 0]
    competencias = entrada.get("competencias", [])
    for i in range(min(5, len(competencias))):
        if isinstance(competencias[i], dict):
            notas[i] = inteiro(competencias[i].get("nota"), 0)
    return notas


def normalizar_nota_competencia(nota):
    nota = max(0, min(200, nota))
    return int(((nota + 20) // 40) * 40)


def validar_resultado(resultado):
    if not isinstance(resultado, dict):
        return "resultado nao e um objeto JSON"

    total = 0
    for i in range(1, 6):
        chave = f"competencia_{i}"
        competencia = resultado.get(chave)
        if not isinstance(competencia, dict):
            return f"campo ausente ou invalido: {chave}"

        nota = inteiro(competencia.get("nota"), -1)
        if nota not in PONTUACOES_VALIDAS:
            nota_original = nota
            nota = normalizar_nota_competencia(nota)
            justificativa = str(competencia.get("justificativa", "")).strip()
            competencia["justificativa"] = (
                f"{justificativa} [Nota original do modelo: {nota_original}; "
                f"normalizada para {nota} para respeitar a escala 0, 40, 80, 120, 160 ou 200.]"
            ).strip()

        competencia["nota"] = nota
        total += nota

    nota_final_original = inteiro(resultado.get("nota_final"), total)
    if nota_final_original != total:
        diagnostico = str(resultado.get("diagnostico_geral", "")).strip()
        resultado["diagnostico_geral"] = (
            f"{diagnostico} [Nota final original do modelo: {nota_final_original}; "
            f"recalculada para {total} como soma das cinco competências.]"
        ).strip()

    resultado["nota_final"] = total
    return None


def caminho_json_resultado(pasta_json, item):
    nome = re.sub(r"[^A-Za-z0-9_.-]+", "_", id_redacao(item)).strip("._")
    if not nome:
        nome = f"item-{item['indice_global']}"
    return pasta_json / f"{nome}.json"


def montar_linha_csv(item, resultado, arquitetura, provedor, modelo):
    entrada = item["entrada"]
    antigas = notas_antigas(entrada)
    return {
        "id": id_redacao(item),
        "arquitetura": arquitetura,
        "provedor_llm": provedor,
        "modelo_llm": modelo,
        "nota_antiga": inteiro(entrada.get("nota"), 0),
        "nota_nova": resultado.get("nota_final", 0),
        "c1": resultado.get("competencia_1", {}).get("nota", 0),
        "c2": resultado.get("competencia_2", {}).get("nota", 0),
        "c3": resultado.get("competencia_3", {}).get("nota", 0),
        "c4": resultado.get("competencia_4", {}).get("nota", 0),
        "c5": resultado.get("competencia_5", {}).get("nota", 0),
        "justificativa_c1": resultado.get("competencia_1", {}).get("justificativa", ""),
        "justificativa_c2": resultado.get("competencia_2", {}).get("justificativa", ""),
        "justificativa_c3": resultado.get("competencia_3", {}).get("justificativa", ""),
        "justificativa_c4": resultado.get("competencia_4", {}).get("justificativa", ""),
        "justificativa_c5": resultado.get("competencia_5", {}).get("justificativa", ""),
        "diagnostico_geral": resultado.get("diagnostico_geral", ""),
        "tema": entrada.get("tema", ""),
        "c1_antiga": antigas[0],
        "c2_antiga": antigas[1],
        "c3_antiga": antigas[2],
        "c4_antiga": antigas[3],
        "c5_antiga": antigas[4],
        "arquivo_origem": item["arquivo"],
    }


async def avaliar_com_tentativas(
    modulo,
    item,
    provedor,
    modelo,
    max_tentativas,
    retry_delay,
    openai_api_key=None,
    openai_base_url=None,
):
    entrada = item["entrada"]
    resposta_bruta = ""
    ultimo_erro = ""

    for tentativa in range(1, max_tentativas + 1):
        try:
            resposta_bruta = await modulo.avaliar_redacao(
                entrada.get("texto", ""),
                entrada.get("tema", ""),
                modelo=modelo if provedor == "ollama" else None,
                ollama_url=OLLAMA_URL,
                provedor=provedor,
                openai_api_key=openai_api_key,
                openai_model=modelo if provedor == "openai" else None,
                openai_base_url=openai_base_url,
            ) or ""
        except Exception as exc:
            resposta_bruta = ""
            ultimo_erro = f"erro na arquitetura: {exc}"

        if resposta_bruta:
            resultado = modulo.extrair_json(resposta_bruta)
            if resultado:
                erro = validar_resultado(resultado)
                if erro is None:
                    return resultado, resposta_bruta, "", tentativa
                ultimo_erro = erro
            else:
                ultimo_erro = "resposta sem JSON valido"
        elif not ultimo_erro:
            ultimo_erro = "arquitetura retornou resposta vazia"

        if tentativa < max_tentativas and retry_delay > 0:
            await asyncio.sleep(retry_delay)

    return None, resposta_bruta, ultimo_erro, max_tentativas


async def resolver_modelo_llm(args):
    if args.provedor == "ollama":
        return await detectar_modelo_ollama()

    openai_api_key = args.openai_api_key or os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise RuntimeError("Chave OpenAI nao informada. Use OPENAI_API_KEY ou --openai-api-key.")

    return args.openai_model or OPENAI_MODEL_PADRAO


async def executar(args):
    modulo = carregar_arquitetura(args.arquitetura)
    redacoes = carregar_corpus(args.corpus)
    if args.limit:
        redacoes = redacoes[:args.limit]

    if args.check_only:
        print(f"Corpus: {args.corpus}")
        print(f"Arquitetura: {args.arquitetura}")
        print(f"Provedor LLM: {args.provedor}")
        print(f"Redacoes carregadas: {len(redacoes)}")
        print("Check-only concluido. Nenhum provedor LLM foi chamado.")
        return 0

    modelo = await resolver_modelo_llm(args)
    openai_api_key = args.openai_api_key or os.getenv("OPENAI_API_KEY")
    openai_base_url = args.openai_base_url or OPENAI_BASE_URL

    pasta_saida = Path(args.output_dir)
    pasta_json = pasta_saida / "json"
    csv_saida = pasta_saida / "resultado_completo.csv"
    csv_falhas = pasta_saida / "falhas.csv"

    pasta_saida.mkdir(parents=True, exist_ok=True)
    pasta_json.mkdir(parents=True, exist_ok=True)

    if args.overwrite:
        for caminho in [csv_saida, csv_falhas]:
            if caminho.exists():
                caminho.unlink()
        for caminho in pasta_json.glob("*.json"):
            caminho.unlink()

    modo_csv = "a" if csv_saida.exists() else "w"
    modo_falhas = "a" if csv_falhas.exists() else "w"

    print(f"Corpus: {args.corpus}")
    print(f"Arquitetura: {args.arquitetura}")
    print(f"Provedor LLM: {args.provedor}")
    print(f"Modelo LLM: {modelo}")
    print(f"Redacoes no lote: {len(redacoes)}")
    print(f"Saida: {pasta_saida}")

    processadas = 0
    falhas = 0
    puladas = 0
    inicio = time.perf_counter()

    with csv_saida.open(modo_csv, newline="", encoding="utf-8") as csvfile, \
         csv_falhas.open(modo_falhas, newline="", encoding="utf-8") as falhasfile:
        writer = csv.DictWriter(csvfile, fieldnames=COLUNAS_CSV)
        falhas_writer = csv.DictWriter(falhasfile, fieldnames=COLUNAS_FALHAS)

        if modo_csv == "w":
            writer.writeheader()
        if modo_falhas == "w":
            falhas_writer.writeheader()

        total = len(redacoes)
        for posicao, item in enumerate(redacoes, start=1):
            redacao_id = id_redacao(item)
            json_saida = caminho_json_resultado(pasta_json, item)

            if json_saida.exists() and not args.overwrite:
                puladas += 1
                if posicao % args.log_every == 0 or posicao == total:
                    print(f"[{posicao}/{total}] pulando ID {redacao_id} (resultado ja existe)")
                continue

            print(f"[{posicao}/{total}] avaliando ID {redacao_id}", flush=True)
            resultado, resposta_bruta, erro, tentativas = await avaliar_com_tentativas(
                modulo,
                item,
                args.provedor,
                modelo,
                args.max_attempts,
                args.retry_delay,
                openai_api_key=openai_api_key,
                openai_base_url=openai_base_url,
            )

            if resultado is None:
                falhas += 1
                falhas_writer.writerow({
                    "id": redacao_id,
                    "arquitetura": args.arquitetura,
                    "arquivo_origem": item["arquivo"],
                    "indice_global": item["indice_global"],
                    "tentativas": tentativas,
                    "erro": erro,
                    "resposta_bruta": resposta_bruta,
                })
                falhasfile.flush()
                print(f" -> Falha: {erro}", flush=True)
                continue

            writer.writerow(montar_linha_csv(item, resultado, args.arquitetura, args.provedor, modelo))
            csvfile.flush()

            with json_saida.open("w", encoding="utf-8") as f:
                json.dump({
                    "id": redacao_id,
                    "arquitetura": args.arquitetura,
                    "provedor_llm": args.provedor,
                    "modelo_llm": modelo,
                    "arquivo_origem": item["arquivo"],
                    "indice_no_arquivo": item["indice_arquivo"],
                    "indice_global": item["indice_global"],
                    "tema": item["entrada"].get("tema", ""),
                    "nota_antiga": inteiro(item["entrada"].get("nota"), 0),
                    "nota_nova": resultado.get("nota_final", 0),
                    "competencias_antigas": notas_antigas(item["entrada"]),
                    "avaliacao_llm": resultado,
                    "resposta_bruta": resposta_bruta,
                    "tentativas": tentativas,
                }, f, ensure_ascii=False, indent=2)

            processadas += 1

    duracao = time.perf_counter() - inicio
    print(
        f"Concluido: {processadas} processadas, {falhas} falhas, "
        f"{puladas} puladas em {duracao:.1f}s"
    )
    print(f"CSV: {csv_saida}")
    print(f"JSONs: {pasta_json}")
    if falhas:
        print(f"Falhas: {csv_falhas}")

    return 1 if falhas else 0


def criar_parser():
    parser = argparse.ArgumentParser(
        description="Executa avaliacao batch de redacoes com uma arquitetura de agentes."
    )
    parser.add_argument("corpus", help="Diretorio ou arquivo JSON do corpus. Exemplo: conjunto_1")
    parser.add_argument(
        "arquitetura",
        choices=sorted(ARQUITETURAS),
        help="Arquitetura de agentes. Opcoes atuais: agente-unico, agentes-multiplos",
    )
    parser.add_argument("--output-dir", default="resultados_batch", help="Pasta de saida.")
    parser.add_argument("--max-attempts", type=int, default=2, help="Tentativas por redacao.")
    parser.add_argument("--retry-delay", type=float, default=1.0, help="Pausa entre tentativas.")
    parser.add_argument("--limit", type=int, help="Processa apenas as primeiras N redacoes.")
    parser.add_argument("--log-every", type=int, default=50, help="Frequencia de log para itens pulados.")
    parser.add_argument("--overwrite", action="store_true", help="Apaga resultados anteriores antes de rodar.")
    parser.add_argument("--check-only", action="store_true", help="Valida corpus e arquitetura sem chamar o provedor LLM.")
    parser.add_argument(
        "--provedor",
        choices=["ollama", "openai"],
        default="ollama",
        help="Provedor LLM a usar. Padrao: ollama.",
    )
    parser.add_argument(
        "--openai-api-key",
        help="Chave da OpenAI. Se omitida, usa a variavel OPENAI_API_KEY.",
    )
    parser.add_argument(
        "--openai-model",
        default=OPENAI_MODEL_PADRAO,
        help=f"Modelo OpenAI. Padrao: {OPENAI_MODEL_PADRAO}.",
    )
    parser.add_argument(
        "--openai-base-url",
        default=OPENAI_BASE_URL,
        help=f"Base URL compativel com OpenAI Responses API. Padrao: {OPENAI_BASE_URL}.",
    )
    return parser


def main():
    parser = criar_parser()
    args = parser.parse_args()

    if args.max_attempts < 1:
        parser.error("--max-attempts deve ser >= 1")
    if args.retry_delay < 0:
        parser.error("--retry-delay deve ser >= 0")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit deve ser >= 1")
    if args.log_every < 1:
        parser.error("--log-every deve ser >= 1")

    try:
        return asyncio.run(executar(args))
    except KeyboardInterrupt:
        print("Execucao interrompida pelo usuario.")
        return 130
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
