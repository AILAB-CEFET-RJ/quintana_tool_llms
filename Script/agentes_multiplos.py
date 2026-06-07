import asyncio
import json
import os
import re

import httpx

import agente_unico
from llm_client import gerar_texto


NOME_ARQUITETURA = "agentes-multiplos"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "")
PONTUACOES_VALIDAS = {0, 40, 80, 120, 160, 200}
MAX_TENTATIVAS_AGENTE = int(os.getenv("AGENTES_MAX_TENTATIVAS", "2"))

COMPETENCIAS = {
    "competencia_1": {
        "rotulo": "Competencia 1",
        "descricao": "Dominio da modalidade escrita formal da lingua portuguesa.",
        "criterios": (
            "Avalie desvios gramaticais, convencoes da escrita, registro, sintaxe, "
            "acentuacao, ortografia e adequacao formal. Nao avalie as outras competencias."
        ),
    },
    "competencia_2": {
        "rotulo": "Competencia 2",
        "descricao": "Compreensao da proposta e dominio do texto dissertativo-argumentativo.",
        "criterios": (
            "Avalie atendimento ao tema, repertorio sociocultural, projeto dissertativo-"
            "argumentativo e desenvolvimento tematico. Nao avalie as outras competencias."
        ),
    },
    "competencia_3": {
        "rotulo": "Competencia 3",
        "descricao": "Selecao, relacao, organizacao e interpretacao de argumentos.",
        "criterios": (
            "Avalie projeto de texto, organizacao das ideias, coerencia argumentativa, "
            "autoria e defesa do ponto de vista. Nao avalie as outras competencias."
        ),
    },
    "competencia_4": {
        "rotulo": "Competencia 4",
        "descricao": "Conhecimento dos mecanismos linguisticos de coesao.",
        "criterios": (
            "Avalie articulacao entre frases e paragrafos, progressao textual, recursos "
            "coesivos, conectivos, retomadas e encadeamento. Nao avalie as outras competencias."
        ),
    },
    "competencia_5": {
        "rotulo": "Competencia 5",
        "descricao": "Proposta de intervencao com respeito aos direitos humanos.",
        "criterios": (
            "Avalie presenca, pertinencia e detalhamento da proposta de intervencao, "
            "incluindo agente, acao, meio/modo, finalidade e detalhamento. Nao avalie as outras competencias."
        ),
    },
}


def extrair_json(texto):
    if not texto:
        return None

    candidatos = [texto.strip()]
    candidatos.extend(re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", texto, re.DOTALL | re.IGNORECASE))

    inicio = texto.find("{")
    while inicio != -1:
        profundidade = 0
        for posicao in range(inicio, len(texto)):
            if texto[posicao] == "{":
                profundidade += 1
            elif texto[posicao] == "}":
                profundidade -= 1
                if profundidade == 0:
                    candidatos.append(texto[inicio:posicao + 1])
                    break
        inicio = texto.find("{", inicio + 1)

    for candidato in candidatos:
        candidato = re.sub(r",\s*([}\]])", r"\1", candidato)
        try:
            resultado = json.loads(candidato)
        except json.JSONDecodeError:
            continue
        if isinstance(resultado, dict):
            return resultado

    return None


def carregar_exemplos():
    pares = [
        (agente_unico.EXEMPLO_1_TEXTO, agente_unico.EXEMPLO_1_JSON),
        (agente_unico.EXEMPLO_2_TEXTO, agente_unico.EXEMPLO_2_JSON),
        (agente_unico.EXEMPLO_3_TEXTO, agente_unico.EXEMPLO_3_JSON),
    ]
    exemplos = []
    for texto, avaliacao_json in pares:
        avaliacao = agente_unico.extrair_json(avaliacao_json)
        if avaliacao:
            exemplos.append((texto.strip(), avaliacao))
    return exemplos


EXEMPLOS = carregar_exemplos()


def json_competencia(avaliacao, chave):
    return json.dumps({chave: avaliacao[chave]}, ensure_ascii=False, indent=2)


def prompt_competencia(chave):
    info = COMPETENCIAS[chave]
    blocos = []
    for indice, (texto, avaliacao) in enumerate(EXEMPLOS, start=1):
        blocos.append(
            "REDAÇÃO DE EXEMPLO {0}:\n{1}\n\nAVALIAÇÃO ESPERADA {0}:\n{2}".format(
                indice,
                texto,
                json_competencia(avaliacao, chave),
            )
        )

    return """
Você é um agente avaliador especialista na {rotulo} do ENEM.

Foco exclusivo:
{descricao}

Critérios:
{criterios}

Regras:
1. Avalie somente {rotulo}.
2. Use apenas as notas 0, 40, 80, 120, 160 ou 200.
3. Nunca use notas como 100, 140, 150 ou 180. Se sua avaliação ficar entre dois níveis, escolha um dos níveis permitidos.
4. Justifique a nota com evidências do texto.
5. Responda única e exclusivamente com um JSON válido neste formato:
{{
  "{chave}": {{
    "nota": 0,
    "justificativa": "..."
  }}
}}
6. Não use Markdown, comentários ou texto fora do JSON.

Abaixo estão exemplos de redações avaliadas. Use-os como referência de critério, escala de notas e formato de saída:

{exemplos}

Agora avalie a redação enviada pelo usuário.
""".strip().format(
        rotulo=info["rotulo"],
        descricao=info["descricao"],
        criterios=info["criterios"],
        chave=chave,
        exemplos="\n\n---\n\n".join(blocos),
    )


def prompt_agregador():
    blocos = []
    for indice, (_, avaliacao) in enumerate(EXEMPLOS, start=1):
        entrada = {chave: avaliacao[chave] for chave in COMPETENCIAS}
        saida = dict(entrada)
        saida["nota_final"] = avaliacao["nota_final"]
        saida["diagnostico_geral"] = "Diagnostico sintetico coerente com as cinco competencias."
        blocos.append(
            "AVALIAÇÕES DOS AGENTES {0}:\n{1}\n\nSAÍDA ESPERADA {0}:\n{2}".format(
                indice,
                json.dumps(entrada, ensure_ascii=False, indent=2),
                json.dumps(saida, ensure_ascii=False, indent=2),
            )
        )

    return """
Você é o agente agregador final da correção ENEM.

Sua tarefa:
1. Receber a redação original e as avaliações dos cinco agentes especialistas.
2. Revisar as notas individuais quando houver inconsistência clara entre nota, justificativa, rubrica ENEM e evidências da redação.
3. Manter a nota do agente especialista quando ela estiver coerente.
4. Não seja excessivamente severo: redações medianas ou boas não devem ser rebaixadas por problemas pontuais.
5. Use apenas as notas 0, 40, 80, 120, 160 ou 200 em cada competência.
6. Calcular "nota_final" como a soma das cinco notas finais revisadas.
7. Produzir um "diagnostico_geral" curto e coerente com as justificativas finais.
8. Responder única e exclusivamente com um JSON válido.
9. Não usar Markdown, comentários ou texto fora do JSON.

Abaixo estão exemplos de consolidação das avaliações dos agentes:

{exemplos}

Agora consolide as avaliações enviadas pelo usuário.
""".strip().format(exemplos="\n\n---\n\n".join(blocos))


PROMPTS_COMPETENCIAS = {
    chave: prompt_competencia(chave)
    for chave in COMPETENCIAS
}
PROMPT_AGREGADOR = prompt_agregador()


async def chamar_modelo(
    prompt_usuario,
    system_prompt,
    modelo,
    ollama_url,
    provedor="ollama",
    openai_api_key=None,
    openai_model=None,
    openai_base_url=None,
):
    return await gerar_texto(
        prompt_usuario=prompt_usuario,
        system_prompt=system_prompt,
        provedor=provedor,
        modelo=modelo,
        ollama_url=ollama_url,
        openai_api_key=openai_api_key,
        openai_model=openai_model,
        openai_base_url=openai_base_url,
    )


def nota_competencia(resultado, chave):
    try:
        return int(float(resultado[chave]["nota"]))
    except (KeyError, TypeError, ValueError):
        return -1


def normalizar_nota(nota):
    nota = max(0, min(200, nota))
    return int(((nota + 20) // 40) * 40)


def normalizar_competencia(resultado, chave):
    if not isinstance(resultado, dict):
        return None

    if isinstance(resultado.get(chave), dict):
        competencia = resultado[chave]
    elif "nota" in resultado and "justificativa" in resultado:
        competencia = resultado
    else:
        competencia = None
        for valor in resultado.values():
            if isinstance(valor, dict) and "nota" in valor and "justificativa" in valor:
                competencia = valor
                break

    if not isinstance(competencia, dict):
        return None

    try:
        nota = int(float(competencia.get("nota")))
    except (TypeError, ValueError):
        return None

    nota_original = nota
    if nota not in PONTUACOES_VALIDAS:
        nota = normalizar_nota(nota)

    justificativa = str(competencia.get("justificativa", "")).strip()
    if nota_original != nota:
        justificativa = (
            f"{justificativa} [Nota original do modelo: {nota_original}; "
            f"normalizada para {nota} para respeitar a escala 0, 40, 80, 120, 160 ou 200.]"
        ).strip()

    return {
        "nota": nota,
        "justificativa": justificativa,
    }


async def avaliar_competencia(
    chave,
    texto_redacao,
    tema_redacao,
    modelo,
    ollama_url,
    provedor="ollama",
    openai_api_key=None,
    openai_model=None,
    openai_base_url=None,
):
    prompt_usuario = f"TEMA: {tema_redacao}\n\nREDAÇÃO DO ALUNO:\n{texto_redacao}"
    ultimo_erro = ""

    for tentativa in range(1, MAX_TENTATIVAS_AGENTE + 1):
        try:
            resposta = await chamar_modelo(
                prompt_usuario,
                PROMPTS_COMPETENCIAS[chave],
                modelo,
                ollama_url,
                provedor=provedor,
                openai_api_key=openai_api_key,
                openai_model=openai_model,
                openai_base_url=openai_base_url,
            )
        except Exception as exc:
            ultimo_erro = f"erro na chamada Ollama: {exc}"
        else:
            resultado = extrair_json(resposta)
            competencia = normalizar_competencia(resultado, chave)
            if competencia:
                return competencia
            trecho = resposta.replace("\n", " ")[:500]
            ultimo_erro = f"resposta sem JSON valido para a competencia. Resposta recebida: {trecho}"

        if tentativa < MAX_TENTATIVAS_AGENTE:
            await asyncio.sleep(1)

    raise RuntimeError(f"{chave}: {ultimo_erro}")


def montar_resultado_deterministico(avaliacoes, diagnostico=None):
    resultado = {}
    nota_final = 0
    for chave in COMPETENCIAS:
        resultado[chave] = avaliacoes[chave]
        nota_final += int(avaliacoes[chave]["nota"])
    resultado["nota_final"] = nota_final
    resultado["diagnostico_geral"] = diagnostico or (
        "A avaliação foi consolidada a partir das cinco competências especializadas."
    )
    return resultado


def normalizar_resultado_agregado(agregado, avaliacoes):
    if not isinstance(agregado, dict):
        return None

    resultado = {}
    nota_final = 0
    for chave in COMPETENCIAS:
        competencia = normalizar_competencia({chave: agregado.get(chave)}, chave)
        if not competencia:
            competencia = avaliacoes[chave]

        resultado[chave] = competencia
        nota_final += int(competencia["nota"])

    resultado["nota_final"] = nota_final
    resultado["diagnostico_geral"] = str(
        agregado.get("diagnostico_geral")
        or "A avaliação foi revisada pelo agente agregador a partir das cinco competências."
    ).strip()
    return resultado


async def agregar_resultados(
    avaliacoes,
    texto_redacao,
    tema_redacao,
    modelo,
    ollama_url,
    provedor="ollama",
    openai_api_key=None,
    openai_model=None,
    openai_base_url=None,
):
    prompt_usuario = (
        "TEMA:\n{tema}\n\n"
        "REDAÇÃO DO ALUNO:\n{texto}\n\n"
        "AVALIAÇÕES DOS AGENTES ESPECIALISTAS:\n{avaliacoes}"
    ).format(
        tema=tema_redacao,
        texto=texto_redacao,
        avaliacoes=json.dumps(avaliacoes, ensure_ascii=False, indent=2),
    )

    try:
        resposta = await chamar_modelo(
            prompt_usuario,
            PROMPT_AGREGADOR,
            modelo,
            ollama_url,
            provedor=provedor,
            openai_api_key=openai_api_key,
            openai_model=openai_model,
            openai_base_url=openai_base_url,
        )
        agregado = extrair_json(resposta) or {}
    except Exception:
        agregado = {}

    return normalizar_resultado_agregado(agregado, avaliacoes) or montar_resultado_deterministico(avaliacoes)


async def avaliar_redacao(
    texto_redacao,
    tema_redacao,
    modelo=None,
    ollama_url=None,
    provedor="ollama",
    openai_api_key=None,
    openai_model=None,
    openai_base_url=None,
):
    modelo = modelo or OLLAMA_MODEL
    ollama_url = ollama_url or OLLAMA_URL
    if provedor == "ollama" and not modelo:
        raise ValueError("Modelo Ollama nao informado para a arquitetura agentes-multiplos.")

    avaliacoes = {}
    for chave in COMPETENCIAS:
        avaliacoes[chave] = await avaliar_competencia(
            chave,
            texto_redacao,
            tema_redacao,
            modelo,
            ollama_url,
            provedor=provedor,
            openai_api_key=openai_api_key,
            openai_model=openai_model,
            openai_base_url=openai_base_url,
        )

    resultado_final = await agregar_resultados(
        avaliacoes,
        texto_redacao,
        tema_redacao,
        modelo,
        ollama_url,
        provedor=provedor,
        openai_api_key=openai_api_key,
        openai_model=openai_model,
        openai_base_url=openai_base_url,
    )
    return json.dumps(resultado_final, ensure_ascii=False, indent=2)
