# QuestMed PDF Generator — Setup Completo

## O que esse servidor faz

Recebe os dados do aluno via POST (enviado pelo Make),
chama o Claude API duas vezes com seus prompts,
gera o PDF com o design da QuestMed e devolve o arquivo.

---

## Estrutura dos arquivos

```
questmed_server/
├── server.py          ← servidor Flask (endpoint principal)
├── pdf_generator.py   ← design do PDF (cores, logo, tabelas)
├── LOGO_NAVY.png      ← logo da QuestMed (copiar aqui)
├── requirements.txt
├── Procfile           ← para Railway/Render
└── README.md
```

---

## Passo 1 — Subir o servidor (Railway — recomendado, grátis)

1. Crie conta em https://railway.app
2. Clique em "New Project" → "Deploy from GitHub repo"
3. Suba esses arquivos num repositório GitHub
4. Em "Variables", adicione:
   ```
   ANTHROPIC_API_KEY = sua_chave_aqui
   ```
5. Railway detecta o Procfile automaticamente e sobe o servidor
6. Copie a URL gerada (ex: `https://questmed-pdf.up.railway.app`)

---

## Passo 2 — Adicionar os prompts completos

Em `server.py`, substitua o placeholder em `PROMPT_1_SYSTEM` pelo
seu prompt completo (o arquivo que você tem).

O `PROMPT_2_SYSTEM` já está configurado para devolver JSON estruturado.

---

## Passo 3 — Configurar o Make

Após o módulo "Google Sheets → Add a Row", adicione:

### Módulo: HTTP → Make a request

```
URL:    https://sua-url.railway.app/gerar-pdf
Método: POST
Headers:
  Content-Type: application/json
Body (JSON):
{
  "nome":             "{{nome}}",
  "email":            "{{email}}",
  "prova":            "{{prova_principal}}",
  "data_prova":       "{{data_da_prova}}",
  "especialidade":    "{{especialidade_desejada}}",
  "instituicoes":     "{{instituicoes}}",
  "dias_semana":      "{{dias_disponiveis}}",
  "horas_dia":        "{{horas_por_dia}}",
  "horas_semana":     "{{horas_por_semana}}",
  "melhor_periodo":   "{{melhor_periodo}}",
  "pior_periodo":     "{{pior_periodo}}",
  "dia_dificil":      "{{dia_mais_dificil}}",
  "estabilidade_rotina": "{{estabilidade}}",
  "plantoes":         "{{plantoes_semana}}",
  "carga_trabalho":   "{{carga_trabalho}}",
  "internato":        "{{internato}}",
  "responsabilidade_familiar": "{{responsabilidade_familiar}}",
  "fds_livre":        "{{fds_livres}}",
  "atividade_fisica": "{{atividade_fisica}}",
  "rotina_real":      "{{rotina_em_texto}}",
  "nivel_atual":      "{{nivel_atual}}",
  "base_teorica":     "{{base_teorica}}",
  "tempo_preparacao": "{{tempo_preparacao}}",
  "metodo_atual":     "{{metodo_atual}}",
  "questoes_feitas":  "{{questoes_resolvidas}}",
  "simulados_feitos": "{{simulados_feitos}}",
  "media_acertos":    "{{media_acertos}}",
  "areas_fortes":     "{{areas_fortes}}",
  "areas_fracas":     "{{areas_fracas}}",
  "obstaculo":        "{{principal_obstaculo}}",
  "reacao_atraso":    "{{reacao_ao_atraso}}",
  "motivo":           "{{motivo_para_passar}}",
  "peso_emocional":   "{{peso_emocional}}",
  "prioridade":       "{{prioridade_cronograma}}"
}
```

Timeout: 300 segundos (o Claude leva ~60-90s para gerar tudo)

### Resposta
O módulo devolve o PDF em binário.
Use o próximo módulo "Google Drive → Upload a File" para salvar.

---

## Passo 4 — Salvar no Google Drive

Módulo: **Google Drive → Upload a File**
```
Folder:    /QuestMed/Cronogramas/
File name: Cronograma_{{nome}}.pdf
File data: [output do módulo HTTP anterior — campo "data"]
```

---

## Tempo estimado por geração

| Etapa                  | Tempo     |
|------------------------|-----------|
| Prompt 1 (narrativo)   | ~30–50s   |
| Prompt 2 (JSON)        | ~20–30s   |
| Geração do PDF         | ~2–5s     |
| **Total**              | ~60–90s   |

O Make tem timeout de 300s por padrão — suficiente.

---

## Teste local

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sua_chave
python server.py
```

Depois teste com:
```bash
curl -X POST http://localhost:8080/gerar-pdf \
  -H "Content-Type: application/json" \
  -d '{"nome":"Teste","prova":"ENAMED","rotina_real":"estudo de manhã"}' \
  --output teste.pdf
```

---

## Custo estimado por aluno

Claude Sonnet 4 — ~$0.01 a $0.03 por geração completa (2 prompts).
