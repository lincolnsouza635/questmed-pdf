"""
QuestMed PDF Generator — Webhook Server
========================================
Recebe dados do aluno via POST (chamado pelo Make),
roda os dois prompts no Claude, gera o PDF com design
e devolve o arquivo ou salva no Google Drive.

Deploy: Railway, Render ou Google Cloud Run (gratuito)
"""

from flask import Flask, request, jsonify, send_file
import anthropic
import json
import os
import io
import tempfile
from pdf_generator import build_pdf  # módulo separado com o design

app = Flask(__name__)

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

# ── Prompts ───────────────────────────────────────────────────────────────

PROMPT_1_SYSTEM = """Você é o Agente de Cronograma Personalizado da QuestMed.

Sua função é analisar as respostas do formulário do aluno e gerar um cronograma de estudos para residência médica com foco em ENAMED, ENARE, PSU-MG, FELUMA e provas semelhantes.

ATENÇÃO:
Seu objetivo não é apenas montar uma estratégia macro.
Seu objetivo principal é gerar um cronograma EXECUTÁVEL na vida real do aluno, com detalhamento por semana e por dia, respeitando:
- rotina real
- dias disponíveis
- horas disponíveis em cada dia
- melhor e pior período de rendimento
- plantões, trabalho, internato
- finais de semana
- cansaço
- urgência da prova
- áreas fracas
- incidência estatística por especialidade, tema e assunto

[... prompt 1 completo conforme seu arquivo ...]

Agora gere o cronograma final completo."""

PROMPT_2_SYSTEM = """Você é o Agente de Formatação de Cronograma da QuestMed.
Sua função é transformar um cronograma narrativo de estudos para residência médica em um CALENDÁRIO OPERACIONAL EM TABELA.

Formato obrigatório das tabelas:
- Semana
- Dia
- Especialidade
- Tema
- Assuntos prioritários
- Número de questões
- Tipo do bloco
- Observação do dia

Retorne APENAS um JSON válido com esta estrutura exata:

{
  "nome": "Nome do aluno",
  "prova": "ENAMED",
  "diagnostico": "texto do diagnóstico estratégico",
  "rotina_interpretada": "como a rotina foi interpretada",
  "resumo_executivo": {
    "semanas": 16,
    "carga_semanal": "13-16h",
    "questoes_semana": "150-220",
    "simulados": "quinzenais"
  },
  "regras_execucao": ["regra 1", "regra 2", "regra 3", "regra 4"],
  "semanas": [
    {
      "numero": 1,
      "objetivo": "Objetivo da semana",
      "total_questoes": "175",
      "foco": "Foco principal",
      "ajuste": "Se atrasar faça X",
      "fase": "1",
      "dias": [
        {
          "dia": "Segunda-feira",
          "especialidade": "Clínica Médica",
          "tema": "HAS e Diabetes",
          "assuntos": "diagnóstico, metas, tratamento, complicações",
          "questoes": "25",
          "tipo": "Bloco novo",
          "observacao": "dia moderado"
        }
      ]
    }
  ],
  "mensagem_final": "Mensagem personalizada para o aluno"
}

Retorne APENAS o JSON, sem texto antes ou depois, sem markdown, sem explicações."""


def montar_dados_aluno(dados: dict) -> str:
    """Formata os dados do formulário para o prompt."""
    return f"""
Nome: {dados.get('nome', '')}
Prova principal: {dados.get('prova', '')}
Data da prova: {dados.get('data_prova', '')}
Especialidade desejada: {dados.get('especialidade', '')}
Instituições prioritárias: {dados.get('instituicoes', '')}

Dias disponíveis por semana: {dados.get('dias_semana', '')}
Horas líquidas por dia: {dados.get('horas_dia', '')}
Horas líquidas por semana: {dados.get('horas_semana', '')}
Melhor período do dia: {dados.get('melhor_periodo', '')}
Pior período do dia: {dados.get('pior_periodo', '')}
Dia mais difícil da semana: {dados.get('dia_dificil', '')}

Estabilidade da rotina: {dados.get('estabilidade_rotina', '')}
Plantões por semana: {dados.get('plantoes', '')}
Carga de trabalho: {dados.get('carga_trabalho', '')}
Internato: {dados.get('internato', '')}
Responsabilidade familiar: {dados.get('responsabilidade_familiar', '')}
Finais de semana livres: {dados.get('fds_livre', '')}
Atividade física: {dados.get('atividade_fisica', '')}

Rotina real (descrição do aluno): {dados.get('rotina_real', '')}

Nível atual: {dados.get('nivel_atual', '')}
Base teórica: {dados.get('base_teorica', '')}
Tempo de preparação: {dados.get('tempo_preparacao', '')}
Método atual: {dados.get('metodo_atual', '')}
Questões já resolvidas: {dados.get('questoes_feitas', '')}
Simulados já feitos: {dados.get('simulados_feitos', '')}
Média de acertos: {dados.get('media_acertos', '')}

Áreas fortes: {dados.get('areas_fortes', '')}
Áreas fracas: {dados.get('areas_fracas', '')}

Principal obstáculo: {dados.get('obstaculo', '')}
Reação ao atraso: {dados.get('reacao_atraso', '')}
Motivo para passar: {dados.get('motivo', '')}
Peso emocional: {dados.get('peso_emocional', '')}
Prioridade desejada: {dados.get('prioridade', '')}
"""


def chamar_claude(system: str, user: str, max_tokens: int = 8000) -> str:
    """Chama a API do Claude e retorna o texto."""
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}]
    )
    return response.content[0].text


@app.route("/gerar-pdf", methods=["POST"])
def gerar_pdf():
    """
    Endpoint principal chamado pelo Make.

    Body JSON esperado:
    {
        "nome": "Júlia Oliveira",
        "prova": "ENAMED",
        "email": "julia@email.com",
        ... (todos os campos do formulário)
    }

    Retorna: arquivo PDF para download
    """
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Nenhum dado recebido"}), 400

        nome = dados.get("nome", "Aluno")
        print(f"[QuestMed] Gerando cronograma para: {nome}")

        # ── Passo 1: Claude gera o cronograma narrativo ──────────────────
        print("[QuestMed] Chamando Prompt 1 (cronograma narrativo)...")
        dados_formatados = montar_dados_aluno(dados)
        cronograma_narrativo = chamar_claude(
            system=PROMPT_1_SYSTEM,
            user=f"Dados do aluno:\n{dados_formatados}\n\nAgora gere o cronograma final completo.",
            max_tokens=8000
        )
        print("[QuestMed] Prompt 1 concluído.")

        # ── Passo 2: Claude converte em JSON estruturado ─────────────────
        print("[QuestMed] Chamando Prompt 2 (tabela JSON)...")
        cronograma_json_str = chamar_claude(
            system=PROMPT_2_SYSTEM,
            user=f"Converta o cronograma abaixo em JSON:\n\n{cronograma_narrativo}",
            max_tokens=8000
        )
        print("[QuestMed] Prompt 2 concluído.")

        # ── Passo 3: Parse do JSON ────────────────────────────────────────
        # Remove possíveis blocos markdown caso o Claude retorne ```json
        json_limpo = cronograma_json_str.strip()
        if json_limpo.startswith("```"):
            json_limpo = json_limpo.split("```")[1]
            if json_limpo.startswith("json"):
                json_limpo = json_limpo[4:]
        cronograma = json.loads(json_limpo.strip())

        # ── Passo 4: Gera PDF com design QuestMed ────────────────────────
        print("[QuestMed] Gerando PDF...")
        pdf_buffer = io.BytesIO()
        build_pdf(cronograma, pdf_buffer)
        pdf_buffer.seek(0)

        nome_arquivo = f"Cronograma_QuestMed_{nome.replace(' ', '_')}.pdf"
        print(f"[QuestMed] PDF gerado: {nome_arquivo}")

        return send_file(
            pdf_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=nome_arquivo
        )

    except json.JSONDecodeError as e:
        print(f"[QuestMed] Erro ao parsear JSON do Claude: {e}")
        return jsonify({"erro": "Falha ao estruturar cronograma", "detalhe": str(e)}), 500
    except Exception as e:
        print(f"[QuestMed] Erro geral: {e}")
        return jsonify({"erro": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "servico": "QuestMed PDF Generator"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
