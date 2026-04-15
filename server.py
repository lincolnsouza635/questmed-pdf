from flask import Flask, request, jsonify, send_file
import json, io, os, re
from pdf_generator import build_pdf

app = Flask(__name__)

def limpar_json(texto):
    """Tenta extrair e limpar o JSON do texto recebido."""
    texto = texto.strip()
    
    # Remove blocos markdown ```json ... ```
    if '```' in texto:
        matches = re.findall(r'```(?:json)?\s*([\s\S]*?)```', texto)
        if matches:
            texto = matches[0].strip()
    
    # Tenta parse direto
    try:
        return json.loads(texto)
    except:
        pass
    
    # Tenta encontrar o JSON entre { }
    try:
        start = texto.index('{')
        # Encontra o fechamento correto contando chaves
        depth = 0
        end = start
        for i, c in enumerate(texto[start:], start):
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    end = i
                    break
        candidato = texto[start:end+1]
        return json.loads(candidato)
    except:
        pass
    
    return None

@app.route("/gerar-pdf", methods=["POST"])
def gerar_pdf():
    try:
        # Pega o raw data para evitar problemas de parse
        raw = request.get_data(as_text=True)
        
        try:
            dados = json.loads(raw)
        except:
            dados = {}
        
        nome = dados.get("nome", "Aluno")
        cronograma_texto = dados.get("cronograma", "")

        if not cronograma_texto:
            return jsonify({"erro": "Cronograma vazio"}), 400

        print(f"[QuestMed] Gerando PDF para: {nome} ({len(cronograma_texto)} chars)")

        # Tenta parsear o JSON do cronograma
        cronograma = limpar_json(cronograma_texto)
        
        if not cronograma:
            return jsonify({"erro": f"JSON inválido — não foi possível parsear"}), 400

        # Garante campos obrigatórios
        cronograma.setdefault("nome", nome)
        cronograma.setdefault("prova", dados.get("prova", "ENAMED"))
        cronograma.setdefault("diagnostico", "")
        cronograma.setdefault("rotina_interpretada", "")
        cronograma.setdefault("resumo_executivo", {
            "semanas": len(cronograma.get("semanas", [])) or 16,
            "carga_semanal": "13-16h",
            "questoes_semana": "150-220",
            "simulados": "Quinzenais"
        })
        cronograma.setdefault("regras_execucao", [
            "Questões inéditas + correção ativa são o eixo principal",
            "Revisões automáticas da QuestMed são obrigatórias todos os dias",
            "Em dia ruim: apenas revisão automática + bloco leve",
            "Simulado sem correção não conta — análise de erros é obrigatória",
        ])
        cronograma.setdefault("mensagem_final", f"{nome}, constância inteligente bate esforço episódico.")

        # Gera PDF
        pdf_buffer = io.BytesIO()
        build_pdf(cronograma, pdf_buffer)
        pdf_buffer.seek(0)

        nome_arquivo = f"Cronograma_QuestMed_{nome.replace(' ', '_')}.pdf"
        print(f"[QuestMed] PDF gerado com sucesso: {nome_arquivo}")

        return send_file(
            pdf_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=nome_arquivo
        )

    except Exception as e:
        print(f"[QuestMed] Erro: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"erro": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
