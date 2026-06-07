import asyncio
import json
import httpx
import os
import csv
import re

from llm_client import gerar_texto

# --- CONFIGURAÇÕES ---
NOME_ARQUITETURA = "agente-unico"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "")

EXEMPLO_1_TEXTO = """
[REDAÇÃO EXCELENTE - TEMA: Desafios para a valorizacao da heranca africana no Brasil]
Milhoes de africanos foram trazidos para o Brasil durante a epoca colonial e seus habitos os acompanharam. Contudo, suas praticas encontraram nesse local distante a discriminacao, prova disso e a Revolta dos Males, evento que se originou da repressao aos cultos islamicos.Diante disso, a carencia de valorizacao dos costumes vindos da Africa pode ser vista, inclusive, no cenario hodierno, pois silencia-los e parte de um processo de deslegitimacao provocado pelos meios de comunicacao. Sendo assim, duas questoes relevantes devem ser apontadas: o preconceito que e dirigido a essa cultura e a falsa ideia de democracia racial da sociedade brasileira.Nesse vies, e importante abordar a discriminacao dirigida ao coletivo africano, seus descendentes e suas praticas no Brasil, ja que a difusao de ideias de hegemonia branca permeiam os meios de difusao de informacoes. Sobre isso, Maya Angelou, escritora preta, afirma que os preconceitos sao dirigidos aos habitos de grupos segregados. Sob esse contexto, uma vez que o audiovisual, por exemplo, ao associar cultos negros a bruxaria, converte-se em um cruel deslegitimador do conjunto de praticas que tratam sobre a heranca africana. Diante dessa abordagem, isso ocorre porque a midia hegemonica difunde ideais eurocentricos como desejados, o que visa o embranquecimento, que consiste em fazer com que outras culturas adotem crencas e habitos da branca. Desse modo, como desencadeamento, devido a discriminacao abordada por Maya, a valorizacao da heranca africana torna-se um desafio no Brasil.Alem disso, a falsa concepcao de que existe uma democracia racial - que e a ideal valorizacao de todas as culturas - tambem deve ser abordada, pois a a repressao da cultura africana e uma triste realidade do pais. A respeito disso, Gilberto Freyre, sociologo brasileiro, na obra Casa Grande e Senzala, trata da mesticagem do Brasil como elemento que extinguiu preconceitos. Entretanto, a heranca da Africa e posta em detrimento de outras culturas, seja, por exemplo, na difusao da literatura africana, que somente se tornou obrigatoria nessas terras apos decretos do inicio dos anos 2000, devido a muitas lutas, enquanto a portuguesa faz parte dos curriculos ha muitas decadas.Sob essa abordagem, isso ocorre porque o apagamento da heranca da Africa no Brasil ainda e parte da realidade embranquecedora. Dessa maneira, como consequencia, a ideia de Gilberto e contestada e a valorizacao dessa cultura se torna objeto de lutas populares.Urge, portanto, sanar os desafios para a valorizacao da cultura da Africa no Brasil. Para isso, cabe ao Ministerio da Cultura - orgao que atua na difusao da diversidade cultural - por meio de uma alianca com o Poder Legislativo, criar uma lei a fim de instituir a adesao ao audiovisual da heranca da Africa, de modo nao discriminatorio, para que o preconceito apontado por Angelou seja extinguido. Ademais, compete ao Ministerio da Igualdade racial - agente sanador de diferencas culturais, mediante campanhas nas redes sociais, difundir as praticas vindas da Africa, com o fito de aponta-las como parte da identidade brasileira. Assim, a heranca africana sera valorizada e casos como o da Revolta dos Males serao evitados no Brasil.
"""

EXEMPLO_1_JSON = """
{
  "competencia_1": { "nota": 200, "justificativa": "Nivel 5 - Demonstra excelente dominio da modalidade escrita formal da lingua portuguesa e de escolha de registro. Desvios gramaticais ou de convencoes da escrita serao aceitos somente como excepcionalidade e quando nao caracterizem reincidencia." },
  "competencia_2": { "nota": 200, "justificativa": "Nivel 5 - Desenvolve o tema por meio de argumentacao consistente, a partir de um repertorio sociocultural produtivo e apresenta excelente dominio do texto dissertativo-argumentativo." },
  "competencia_3": { "nota": 160, "justificativa": "Nivel 4 - Apresenta informacoes, fatos e opinioes relacionados ao tema, de forma organizada, com indicios de autoria, em defesa de um ponto de vista." },
  "competencia_4": { "nota": 200, "justificativa": "Nivel 5 - Articula bem as partes do texto e apresenta repertorio diversificado de recursos coesivos." },
  "competencia_5": { "nota": 200, "justificativa": "Nivel 5 - Elabora muito bem proposta de intervencao, detalhada, relacionada ao tema e articulada a discussao desenvolvida no texto." },
  "nota_final": 960
}
"""

EXEMPLO_2_TEXTO = """
[REDAÇÃO MÉDIA - TEMA: Jogos de apostas online: por que isso pode ser um problema?]
Com a mudanca nas formas de realizacao de jogos e apostas online, os jogadores terao um ambiente digital 24 horas por dia para fazerem as apostas, os jogos podem ser feitos de casa ou em qualquer lugar onde tenha acesso a internet, usando computador, notebook, tablets, smartphone e celular, todo o servico e feito de forma online, ainda nao sabemos como sera a reacao de abstinencia e compulsividade dos jogadores.No Brasil existe um grande numero de usuarios de jogos de varios segmentos, e temos o conhecimento de jogadores que sao compulsivos e nao conseguem ficar sem jogar, inclusive existem casos de internacoes de jogadores que se tornaram compulsivos por nao conseguirem controlar as crises de abstinencias, por motivo de nao controlar o seu desejo de jogar, jogar, jogar e jogar. As familias depois que percebem que a situacao se tornou um problema de saude no membro da familia, procura por tratamentos diversos com intuito de solucionar o problema do vicio do familiar. Algumas familias tomam medidas drasticas internando o familiar em clinicas de tratamento psiquiatricos, levando o tratamento ate o fim quando o muitas vezes o paciente por nao suportar os regimes e restricoes do tratamento, foge e vai morar na rua, se isola da sociedade fica indiferente com os amigos, depois de morar na casa de todos os parentes e amigos, foi internado na clinica e nao suportando o tratamento e por falta de opcoes de lugar para morar, foi morar na rua. Agora com a criacao de uma plataforma moderna de jogos digitalizados, com disponibilidade 24 horas por dia dentro de casa ou em qualquer lugar com sinal de internet, qual o impulsionamento na abstinencia dos jogadores compulsivos podera ocorrer, quais as mudancas de comportamentos teremos que nos adaptar e conviver com a nova modalidade dos jogos.Como sabemos que no Brasil existem um grande numero de jogadores compulsivos de jogos, com a modernizacao da plataforma e necessaria, uma fiscalizacao rigorosa por parte da ANATEL e outras instituicoes de suporte online, uma opcao e a integracao da telemedicina realizando consultas obrigatorias, do inicio ao fim de cada jogo online, em todos os jogadores, e no final do jogo sendo entregue um relatorio medico com diagnostico de abstinencia de cada jogador, e esta consulta deve ser armazenada no banco de dados do SUS, quando o jogador for fazer uma consulta medica ou for internado em alguma clinica de tratamento estas consultas da telemedicina dos jogos online sejam disponibilizadas na ficha do paciente, ao profissional da saude que fizer o atendimento a este paciente. Esta medida seria uma solucao favoravel aos futuros problemas de saude causados pelos jogos online dos jogadores brasileiros.
"""

EXEMPLO_2_JSON = """
{
  "competencia_1": { "nota": 160, "justificativa": "Nivel 4 - Demonstra bom dominio da modalidade escrita formal da lingua portuguesa e de escolha de registro, com poucos desvios gramaticais e de convencoes da escrita." },
  "competencia_2": { "nota": 120, "justificativa": "Nivel 3 - Desenvolve o tema por meio de argumentacao previsivel e apresenta dominio mediano do texto dissertativo-argumentativo, com proposicao, argumentacao e conclusao." },
  "competencia_3": { "nota": 120, "justificativa": "Nivel 3 - Apresenta informacoes, fatos e opinioes relacionados ao tema, limitados aos argumentos dos textos motivadores e pouco organizados, em defesa de um ponto de vista." },
  "competencia_4": { "nota": 120, "justificativa": "Nivel 3 - Articula as partes do texto, de forma mediana, com inadequacoes, e apresenta repertorio pouco diversificado de recursos coesivos." },
  "competencia_5": { "nota": 80, "justificativa": "Nivel 2 - Elabora, de forma insuficiente, proposta de intervencao relacionada ao tema, ou nao articulada com a discussao desenvolvida no texto." },
  "nota_final": 600
}
"""

EXEMPLO_3_TEXTO = """
[REDAÇÃO RUIM - TEMA: Desafios para a valorizacao da heranca africana no Brasil]
Durante muitos anos famos enganados com a ideia de que so o homem branco e inteligente, deixando assim, uma impressao que os negros sejam incapaz de fazer algo bom, pois eram conciderados como se fosse burros. isso nos tras um grande desafio para que pasaomos valorizar a importancia dos povos africanos que tanto contribuiram com a nossa cultura aqui no brasil. E importante lembrar que o Brasil foi quem mais importou escravo africano no continente americano, entre os seculo xvi e xix. Deste modo,nao tem como negar a influencia da cultura africana no pais. Isso inclui, lingua, a danca, a musica, a religiao e tambem o folclore. Na lingua as palavras como fuba, macaco e moleque, sao de origem africana. O mesmo ocorem na danca a influencia africana esta presente em quase todos os estados brasileiros. Durante muitos tempo, a contribuicao do povo africano foi apagada pela a influencia da ilite que aqui existe. Alem disso, ate nos dias atuais temos grandes desafios de provar que os povos africanos contribuiram e muito para a formacao da cultura brasileira de diversas formas. Sendo assim, nao tem como negar que o Brasil foi construido com a cultura africana.
"""

EXEMPLO_3_JSON = """
{
  "competencia_1": { "nota": 120, "justificativa": "Nivel 3 - Demonstra dominio mediano da modalidade escrita formal da lingua portuguesa e de escolha de registro, com alguns desvios gramaticais e de convencoes da escrita." },
  "competencia_2": { "nota": 120, "justificativa": "Nivel 3 - Desenvolve o tema por meio de argumentacao previsivel e apresenta dominio mediano do texto dissertativo-argumentativo, com proposicao, argumentacao e conclusao." },
  "competencia_3": { "nota": 80, "justificativa": "Nivel 2 - Apresenta informacoes, fatos e opinioes relacionados ao tema, mas desorganizados ou contraditorios e limitados aos argumentos dos textos motivadores, em defesa de um ponto de vista." },
  "competencia_4": { "nota": 80, "justificativa": "Nivel 2 - Articula as partes do texto, de forma insuficiente, com muitas inadequacoes e apresenta repertorio limitado de recursos coesivos." },
  "competencia_5": { "nota": 0, "justificativa": "Nivel 0 - Nao apresenta proposta de intervencao ou apresenta proposta nao relacionada ao tema ou ao assunto." },
  "nota_final": 400
}
"""


system_prompt = f"""
Você é um avaliador especialista da redação do ENEM.
Seu papel é ler a redação enviada e produzir notas individuais exclusivas (0, 40, 80, 120, 160 ou 200) para cada uma das cinco competências, uma nota final (0 a 1000), e um diagnóstico.

Competências que você deve avaliar

Competência 1 – Domínio da norma culta.
Competência 2 – Compreensão da proposta e desenvolvimento do tema.
Competência 3 – Seleção e organização de argumentos.
Competência 4 – Coesão e coerência.
Competência 5 – Proposta de intervenção.

Regras de Avaliação:
1. Siga estritamente os critérios da TRI do ENEM.
2. NUNCA atribua notas intermediárias como 100, 140, 150, 180 ou 190. Use APENAS os múltiplos de 40: 0, 40, 80, 120, 160, 200.
3. Explique as notas com base em evidências do texto.
4. Você DEVE responder ÚNICA e EXCLUSIVAMENTE com um objeto JSON válido. Não inclua textos antes ou depois do JSON.

Abaixo, forneço exemplos de como eu espero que você avalie e formate a saída:

--- INÍCIO DOS EXEMPLOS (AGENTE UNICO) ---

REDAÇÃO DE EXEMPLO 1:
{EXEMPLO_1_TEXTO.strip()}

AVALIAÇÃO ESPERADA 1:
{EXEMPLO_1_JSON.strip()}

REDAÇÃO DE EXEMPLO 2:
{EXEMPLO_2_TEXTO.strip()}

AVALIAÇÃO ESPERADA 2:
{EXEMPLO_2_JSON.strip()}

--- FIM DOS EXEMPLOS ---

Agora, comporte-se exatamente como mostrado nos exemplos acima para a redação que será enviada pelo usuário.
"""

def extrair_json(texto):
    match = re.search(r"\{.*\}", texto, re.DOTALL)
    if not match:
        return None
    candidato = re.sub(r",\s*([}\]])", r"\1", match.group())
    try:
        return json.loads(candidato)
    except:
        return None

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
    # Passamos o tema junto para dar mais contexto ao modelo
    prompt_usuario = f"TEMA: {tema_redacao}\n\nREDAÇÃO DO ALUNO:\n{texto_redacao}"
    modelo = modelo or OLLAMA_MODEL
    ollama_url = ollama_url or OLLAMA_URL

    if provedor == "ollama" and not modelo:
        raise ValueError("Modelo Ollama nao informado para a arquitetura agente-unico.")

    try:
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
    except Exception as e:
        print(f"Erro na requisição: {e}")
        return None
