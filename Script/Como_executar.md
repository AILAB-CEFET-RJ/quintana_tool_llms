# Execucao batch via SSH

Use este comando para rodar a avaliacao do corpus com uma arquitetura de agentes:

```bash
python executar_avaliacao.py conjunto_1 agente-unico
```

Para rodar a arquitetura de multiplos agentes:

```bash
python executar_avaliacao.py conjunto_1 agentes-multiplos
```

Argumentos obrigatorios:

- `conjunto_1`: diretorio ou arquivo JSON do corpus a corrigir.
- `agente-unico` ou `agentes-multiplos`: arquitetura de agentes a usar.

## Preparar ambiente Python

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Preparar Ollama

O executor usa automaticamente o modelo que estiver carregado no Ollama. Em uma sessao SSH, deixe um modelo ativo:

```bash
ollama run gemma3:latest
```

Em outra sessao SSH, rode o batch:

```bash
source .venv/bin/activate
python executar_avaliacao.py conjunto_1 agente-unico
```

Se nenhum modelo estiver carregado, o executor para e mostra uma mensagem pedindo para iniciar um modelo no Ollama.

## Usar OpenAI em vez de Ollama

Voce pode usar uma chave da OpenAI no lugar do modelo carregado pelo Ollama.

Opcao recomendada, usando variavel de ambiente:

```bash
export OPENAI_API_KEY="sua-chave"
python executar_avaliacao.py conjunto_1 agente-unico --provedor openai
```

Tambem funciona com a arquitetura de multiplos agentes:

```bash
export OPENAI_API_KEY="sua-chave"
python executar_avaliacao.py conjunto_1 agentes-multiplos --provedor openai
```

Por padrao, o modelo OpenAI usado e `gpt-4.1-mini`. Para escolher outro:

```bash
python executar_avaliacao.py conjunto_1 agente-unico --provedor openai --openai-model gpt-4.1
```

Se preferir passar a chave diretamente no comando:

```bash
python executar_avaliacao.py conjunto_1 agente-unico --provedor openai --openai-api-key "sua-chave"
```

## Teste rapido

Para validar corpus e arquitetura sem chamar nenhum provedor LLM:

```bash
python executar_avaliacao.py conjunto_1 agentes-multiplos --check-only
```

Para rodar poucas redacoes com Ollama:

```bash
python executar_avaliacao.py conjunto_1 agente-unico -n 3 --output-dir resultados_teste
```

```bash
python executar_avaliacao.py conjunto_1 agentes-multiplos --num-redacoes 3 --output-dir resultados_teste_multi
```

Com OpenAI:

```bash
python executar_avaliacao.py conjunto_1 agentes-multiplos --provedor openai -n 3 --output-dir resultados_teste_multi_openai
```

## Saidas

Por padrao, as saidas ficam em `resultados_batch`:

- `resultados_batch/resultado_completo.csv`: resultado consolidado.
- `resultados_batch/json/<id>.json`: resposta detalhada por redacao.
- `resultados_batch/falhas.csv`: itens que falharam apos as tentativas.

Se a execucao cair, rode o mesmo comando novamente. O executor pula automaticamente as redacoes que ja possuem JSON de resultado.

Para recomecar do zero:

```bash
python executar_avaliacao.py conjunto_1 agente-unico --overwrite
```

## Adicionar novas arquiteturas depois

Para criar uma arquitetura futura, por exemplo `multi-agentes`:

1. Crie um novo arquivo Python que exponha `avaliar_redacao(...)` e `extrair_json(...)`.
2. Adicione a arquitetura no dicionario `ARQUITETURAS` de `executar_avaliacao.py`.
3. Rode passando o novo nome no segundo argumento:

```bash
python executar_avaliacao.py conjunto_1 multi-agentes
```
