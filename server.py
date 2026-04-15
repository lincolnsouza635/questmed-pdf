"""
QuestMed PDF Generator
Recebe JSON do Claude (via Make) e gera PDF com design QuestMed.
"""
from flask import Flask, request, jsonify, send_file
import json, io, os
from pdf_generator import build_pdf

app = Flask(__name__)

@app.route("/gerar-pdf", methods=["POST"])
def gerar_pdf():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Nenhum dado recebido"}), 400

        nome = dados.get("nome", "Aluno")
        cronograma_raw = dados.get("cronograma", "")

        if not cronograma_raw:
            return jsonify({"erro": "Cronograma vazio"}), 400

        print(f"[QuestMed] Gerando PDF para: {nome}")

        # Limpa possível markdown do Claude
        texto = cronograma_raw.strip()
        if "```" in texto:
            partes = texto.split("```")
            for p in partes:
                p2 = p.strip()
                if p2.startswith("json"):
                    p2 = p2[4:].strip()
                if p2.startswith("{"):
                    texto = p2
                    break

        # Parse do JSON
        cronograma = json.loads(texto)

        # Garante campos obrigatórios
        if "nome" not in cronograma:
            cronograma["nome"] = nome
        if "prova" not in cronograma:
            cronograma["prova"] = dados.get("prova", "ENAMED")
        if "regras_execucao" not in cronograma:
            cronograma["regras_execucao"] = [
                "Questões inéditas + correção ativa são o eixo principal",
                "Revisões automáticas da QuestMed são obrigatórias todos os dias",
                "Em dia ruim: apenas revisão automática + bloco leve",
                "Simulado sem correção não conta — análise de erros é obrigatória",
            ]
        if "resumo_executivo" not in cronograma:
            cronograma["resumo_executivo"] = {
                "semanas": len(cronograma.get("semanas", [])) or 16,
                "carga_semanal": "13-16h",
                "questoes_semana": "150-220",
                "simulados": "Quinzenais"
            }

        # Gera PDF
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
        print(f"[QuestMed] Erro JSON: {e}")
        return jsonify({"erro": f"JSON inválido: {str(e)}"}), 400
    except Exception as e:
        print(f"[QuestMed] Erro: {e}")
        return jsonify({"erro": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "servico": "QuestMed PDF Generator"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
