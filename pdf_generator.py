
"""
QuestMed PDF Generator — Módulo de design
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import Flowable
from reportlab.pdfgen import canvas as pdfcanvas
import os

NAVY       = colors.HexColor('#191645')
AMBER_BG   = colors.HexColor('#fff8ed')
AMBER_FG   = colors.HexColor('#92400e')
AMBER_ACC  = colors.HexColor('#F5A623')
WHITE      = colors.white
GRAY_DARK  = colors.HexColor('#1f2937')
GRAY       = colors.HexColor('#6b7280')
GRAY_LIGHT = colors.HexColor('#f3f4f6')
GRAY_MID   = colors.HexColor('#e5e7eb')
W, H = A4
LOGO_PATH  = os.path.join(os.path.dirname(__file__), 'LOGO_NAVY.png')


def hex_str(c):
    return '%02x%02x%02x' % (int(c.red*255), int(c.green*255), int(c.blue*255))


def get_tipo_colors(tipo):
    t = tipo.lower()
    if 'simulado' in t or 'corre' in t or 'mini' in t:
        return AMBER_BG, AMBER_FG
    return GRAY_LIGHT, GRAY_DARK


def make_styles():
    s = {}
    base = dict(fontName='Helvetica', fontSize=8.5, textColor=GRAY_DARK,
                spaceAfter=3, leading=13)
    s['body']    = ParagraphStyle('body', **base, alignment=TA_JUSTIFY)
    s['body_c']  = ParagraphStyle('body_c', **base, alignment=TA_CENTER)
    s['small']   = ParagraphStyle('small', fontName='Helvetica', fontSize=7.5, textColor=GRAY, leading=11)
    s['tbl_hdr'] = ParagraphStyle('tbl_hdr', fontName='Helvetica-Bold', fontSize=7.5, textColor=WHITE, alignment=TA_CENTER)
    s['tbl_cell']= ParagraphStyle('tbl_cell', fontName='Helvetica', fontSize=7.5, textColor=GRAY_DARK, leading=11)
    s['tbl_cell_c']=ParagraphStyle('tbl_cell_c', fontName='Helvetica', fontSize=7.5, textColor=GRAY_DARK, leading=11, alignment=TA_CENTER)
    s['tbl_bold']= ParagraphStyle('tbl_bold', fontName='Helvetica-Bold', fontSize=7.5, textColor=GRAY_DARK, leading=11)
    s['week_num']= ParagraphStyle('week_num', fontName='Helvetica-Bold', fontSize=12, textColor=NAVY)
    s['week_obj']= ParagraphStyle('week_obj', fontName='Helvetica', fontSize=8, textColor=GRAY, leading=12)
    s['final']   = ParagraphStyle('final', fontName='Helvetica', fontSize=9, textColor=WHITE, spaceAfter=4, leading=14, alignment=TA_JUSTIFY)
    s['final_b'] = ParagraphStyle('final_b', fontName='Helvetica-Bold', fontSize=9, textColor=WHITE, spaceAfter=4, leading=14)
    return s


class NavyBar(Flowable):
    def __init__(self, text, sub='', height=1.0*cm):
        super().__init__()
        self.text = text; self.sub = sub
        self.bar_h = height; self.height = height; self.width = 0

    def wrap(self, aw, ah):
        self.width = aw; return aw, self.bar_h

    def draw(self):
        c = self.canv
        c.setFillColor(NAVY); c.roundRect(0, 0, self.width, self.bar_h, 6, fill=1, stroke=0)
        c.setFillColor(AMBER_ACC); c.rect(0, 0, 3, self.bar_h, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont('Helvetica-Bold', 10)
        c.drawString(12, self.bar_h/2 + (3 if self.sub else -4), self.text)
        if self.sub:
            c.setFillColor(colors.HexColor('#b8b4e0'))
            c.setFont('Helvetica', 7.5)
            c.drawString(12, self.bar_h/2 - 8, self.sub)


class CoverPage(Flowable):
    def __init__(self, dados, width, height):
        super().__init__()
        self.dados = dados; self.width = width; self.height = height

    def wrap(self, aw, ah): return self.width, self.height

    def draw(self):
        c = self.canv; w, h = self.width, self.height
        c.setFillColor(NAVY); c.rect(0, 0, w, h, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#1f1c5a')); c.circle(w-1*cm, h-1*cm, 4*cm, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#141238')); c.circle(0.5*cm, 0.5*cm, 2.5*cm, fill=1, stroke=0)
        if os.path.exists(LOGO_PATH):
            c.drawImage(LOGO_PATH, w/2-3.5*cm, h-3.8*cm, 7*cm, 7*cm*(104/284),
                        preserveAspectRatio=True, mask='auto')
        c.setFillColor(WHITE); c.setFont('Helvetica-Bold', 22)
        c.drawCentredString(w/2, h-5*cm, 'Cronograma Personalizado')
        c.setFillColor(colors.HexColor('#b8b4e0')); c.setFont('Helvetica-Bold', 16)
        c.drawCentredString(w/2, h-6.2*cm, self.dados.get('nome','Aluno'))
        c.setStrokeColor(AMBER_ACC); c.setLineWidth(1.5)
        c.line(w/2-5*cm, h-6.8*cm, w/2+5*cm, h-6.8*cm)
        resumo = self.dados.get('resumo_executivo', {})
        c.setFillColor(colors.HexColor('#b8b4e0')); c.setFont('Helvetica', 10)
        c.drawCentredString(w/2, h-7.8*cm,
            f'Prova-alvo: {self.dados.get("prova","ENAMED")}   ·   {resumo.get("semanas","16")} Semanas   ·   Plano completo')
        fases = [('Fase 1','Semanas 1–4','Destravar',GRAY_LIGHT,GRAY_DARK),
                 ('Fase 2','Semanas 5–12','Volume',GRAY_LIGHT,GRAY_DARK),
                 ('Fase 3','Semanas 13–16','Reta final',AMBER_BG,AMBER_FG)]
        box_w=(w-2*cm)/3; bx=1*cm; by=h-11.5*cm
        for fl,fs,desc,bg,fg in fases:
            c.setFillColor(bg); c.roundRect(bx,by,box_w-0.3*cm,2.2*cm,8,fill=1,stroke=0)
            c.setFillColor(fg); c.setFont('Helvetica-Bold',10)
            c.drawCentredString(bx+(box_w-0.3*cm)/2,by+1.4*cm,fl)
            c.setFont('Helvetica-Bold',8); c.drawCentredString(bx+(box_w-0.3*cm)/2,by+0.9*cm,fs)
            c.setFont('Helvetica',8); c.drawCentredString(bx+(box_w-0.3*cm)/2,by+0.3*cm,desc)
            bx+=box_w
        regras=self.dados.get('regras_execucao',[])
        c.setFillColor(colors.HexColor('#1e1958')); c.roundRect(0.5*cm,h-17.5*cm,w-1*cm,3.5*cm,8,fill=1,stroke=0)
        c.setFillColor(WHITE); c.setFont('Helvetica-Bold',8.5); c.drawString(1.2*cm,h-14.8*cm,'Regras de ouro:')
        c.setFillColor(colors.HexColor('#b8b4e0')); c.setFont('Helvetica',7.5)
        nums='①②③④'
        for i,r in enumerate(regras[:4]):
            c.drawString(1.2*cm,h-15.5*cm+i*(-0.5*cm),f'{nums[i]} {str(r)[:90]}')
        c.setFillColor(colors.HexColor('#374151')); c.rect(0,0,w,0.8*cm,fill=1,stroke=0)
        c.setFillColor(GRAY_MID); c.setFont('Helvetica',7)
        c.drawCentredString(w/2,0.25*cm,'QuestMed — Cronograma exclusivo e personalizado · Não compartilhar')


class NumberedCanvas(pdfcanvas.Canvas):
    def __init__(self,*a,**k): super().__init__(*a,**k); self._saved_page_states=[]
    def showPage(self): self._saved_page_states.append(dict(self.__dict__)); self._startPage()
    def save(self):
        n=len(self._saved_page_states)
        for i,st in enumerate(self._saved_page_states):
            self.__dict__.update(st)
            if i>0: self._chrome(i+1,n)
            super().showPage()
        super().save()
    def _chrome(self,pn,total):
        self.setFillColor(NAVY); self.rect(0,H-0.7*cm,W,0.7*cm,fill=1,stroke=0)
        if os.path.exists(LOGO_PATH):
            self.drawImage(LOGO_PATH,0.3*cm,H-0.65*cm,3*cm,0.55*cm,preserveAspectRatio=True,mask='auto')
        self.setFillColor(WHITE); self.setFont('Helvetica',7)
        self.drawRightString(W-0.5*cm,H-0.45*cm,'Cronograma Personalizado · QuestMed')
        self.setFillColor(GRAY_LIGHT); self.rect(0,0,W,0.55*cm,fill=1,stroke=0)
        self.setFillColor(GRAY); self.setFont('Helvetica',6.5)
        self.drawString(0.5*cm,0.18*cm,'QuestMed · Material personalizado e confidencial')
        self.drawRightString(W-0.5*cm,0.18*cm,f'Página {pn} de {total}')


def build_pdf(dados: dict, output):
    doc = SimpleDocTemplate(output, pagesize=A4,
        leftMargin=1.2*cm, rightMargin=1.2*cm,
        topMargin=1.4*cm, bottomMargin=1.0*cm)
    ST = make_styles(); story = []

    # Capa
    story.append(CoverPage(dados, W-2.4*cm, H-2.9*cm))
    story.append(PageBreak())

    # Diagnóstico
    story.append(NavyBar('1. Diagnóstico Estratégico'))
    story.append(Spacer(1, 0.3*cm))
    for label, txt in [('Diagnóstico', dados.get('diagnostico','')),
                        ('Rotina', dados.get('rotina_interpretada',''))]:
        if not txt: continue
        r = Table([[
            Paragraph(f'<b>{label}</b>', ParagraphStyle('dl', fontName='Helvetica-Bold',
                fontSize=8, textColor=GRAY_DARK)),
            Paragraph(txt, ST['body']),
        ]], colWidths=[2.8*cm, None])
        r.setStyle(TableStyle([('BACKGROUND',(0,0),(0,0),GRAY_LIGHT),
            ('BACKGROUND',(1,0),(1,0),WHITE),('ROWPADDING',(0,0),(-1,-1),8),
            ('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),0.3,GRAY_MID)]))
        story.append(r)

    story.append(Spacer(1, 0.35*cm))

    # Stats
    resumo = dados.get('resumo_executivo', {})
    stats = [[str(resumo.get('semanas','16')),'Semanas'],
             [resumo.get('carga_semanal','—'),'Carga/semana'],
             [resumo.get('questoes_semana','—'),'Questões/sem'],
             [resumo.get('simulados','—'),'Simulados']]
    st_d = [[Paragraph(f'<b>{v}</b><br/><font size="7">{l}</font>',ST['body_c']) for v,l in stats]]
    st_t = Table(st_d, colWidths=['25%']*4)
    st_ts = [('ROWPADDING',(0,0),(-1,-1),12),('ALIGN',(0,0),(-1,-1),'CENTER'),
             ('GRID',(0,0),(-1,-1),0,colors.transparent)]
    for i in range(3): st_ts.append(('BACKGROUND',(i,0),(i,0),GRAY_LIGHT))
    st_ts += [('BACKGROUND',(3,0),(3,0),AMBER_BG),('TEXTCOLOR',(3,0),(3,0),AMBER_FG)]
    st_t.setStyle(TableStyle(st_ts)); story.append(st_t)
    story.append(Spacer(1, 0.4*cm))

    # Regras
    story.append(NavyBar('2. Regras de Execução'))
    story.append(Spacer(1, 0.3*cm))
    for i, r in enumerate(dados.get('regras_execucao', [])):
        row = Table([[
            Paragraph(str(i+1), ParagraphStyle('rn', fontName='Helvetica-Bold',
                fontSize=11, textColor=NAVY, alignment=TA_CENTER)),
            Paragraph(str(r), ST['body']),
        ]], colWidths=[0.9*cm, None])
        row.setStyle(TableStyle([('BACKGROUND',(0,0),(0,0),GRAY_LIGHT),
            ('BACKGROUND',(1,0),(1,0),WHITE),('ROWPADDING',(0,0),(-1,-1),8),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LINEBELOW',(0,0),(-1,0),0.3,GRAY_MID)]))
        story.append(row)

    story.append(PageBreak())

    # Cronograma
    story.append(NavyBar('3. Cronograma Semanal Detalhado', 'Calendário operacional completo'))
    story.append(Spacer(1, 0.3*cm))

    FASE_INFO = {
        '1': ('Fase 1 — Destravar','Semanas 1–4',GRAY_LIGHT,GRAY_DARK),
        '2': ('Fase 2 — Volume','Semanas 5–12',GRAY_LIGHT,GRAY_DARK),
        '3': ('Fase 3 — Reta Final','Semanas 13–16',AMBER_BG,AMBER_FG),
    }
    fase_atual = None

    for w in dados.get('semanas', []):
        fase = str(w.get('fase','1'))
        if fase != fase_atual:
            fase_atual = fase
            if fase in FASE_INFO:
                fl,fs,fbg,ffg = FASE_INFO[fase]
                ph = Table([[
                    Paragraph(f'<font color="#{hex_str(ffg)}"><b>{fl}</b></font>',ST['body_c']),
                    Paragraph(f'<font color="#{hex_str(ffg)}">{fs}</font>',ST['body_c']),
                ]],colWidths=['60%','40%'])
                ph.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),fbg),
                    ('ROWPADDING',(0,0),(-1,-1),6),('ALIGN',(0,0),(-1,-1),'CENTER')]))
                story.append(ph); story.append(Spacer(1,0.2*cm))

        # Header semana
        wh = Table([[
            Paragraph(f'<b>Semana {w.get("numero","")}</b>', ST['week_num']),
            Paragraph(w.get('objetivo',''), ST['week_obj']),
            Paragraph(f'<b>~{w.get("total_questoes","—")} questões</b>',
                ParagraphStyle('wt',fontName='Helvetica-Bold',fontSize=8,
                    textColor=AMBER_FG,alignment=TA_RIGHT)),
        ]], colWidths=[2.5*cm,None,3*cm])
        wh.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),GRAY_LIGHT),
            ('ROWPADDING',(0,0),(-1,-1),6),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('LINEABOVE',(0,0),(-1,0),1.5,NAVY),('LINEBELOW',(0,0),(-1,0),0.3,GRAY_MID)]))
        story.append(wh)

        # Tabela dias
        dias = w.get('dias',[])
        if dias:
            hdr = [Paragraph(f'<b>{h}</b>',ST['tbl_hdr'])
                   for h in ['Dia','Especialidade','Tema','Assuntos','Qst.','Tipo','Obs.']]
            rows = [hdr]
            sim_rows = []
            for i,d in enumerate(dias):
                tipo = d.get('tipo','')
                _,tipo_fg = get_tipo_colors(tipo)
                dia_s = (d.get('dia','').replace('-feira','')
                    .replace('Segunda','Seg').replace('Terça','Ter')
                    .replace('Quarta','Qua').replace('Quinta','Qui').replace('Sexta','Sex'))
                rows.append([
                    Paragraph(f'<b>{dia_s}</b>',ST['tbl_bold']),
                    Paragraph(d.get('especialidade',''),ST['tbl_cell']),
                    Paragraph(d.get('tema',''),ST['tbl_cell']),
                    Paragraph(d.get('assuntos',''),ST['tbl_cell']),
                    Paragraph(d.get('questoes','—'),ST['tbl_cell_c']),
                    Paragraph(tipo,ParagraphStyle('tp',fontName='Helvetica',
                        fontSize=7.5,textColor=tipo_fg,leading=11)),
                    Paragraph(d.get('observacao',''),ST['tbl_cell']),
                ])
                if any(k in tipo.lower() for k in ['simulado','corre','mini']):
                    sim_rows.append(i+1)

            tbl = Table(rows, colWidths=[1.5*cm,2.5*cm,2.3*cm,None,0.8*cm,2.2*cm,1.8*cm])
            ts = [('BACKGROUND',(0,0),(-1,0),NAVY),('TEXTCOLOR',(0,0),(-1,0),WHITE),
                  ('FONTSIZE',(0,0),(-1,-1),7.5),('ROWPADDING',(0,0),(-1,-1),5),
                  ('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),0.3,GRAY_MID),
                  ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#f8fafc'),WHITE])]
            for ri in sim_rows:
                ts += [('BACKGROUND',(5,ri),(5,ri),AMBER_BG),
                       ('TEXTCOLOR',(5,ri),(5,ri),AMBER_FG)]
            tbl.setStyle(TableStyle(ts)); story.append(tbl)

        # Foco/ajuste
        fa = Table([[
            Paragraph(f'<font color="#{hex_str(NAVY)}"><b>Foco:</b></font> {w.get("foco","")}',ST['small']),
            Paragraph(f'<font color="#{hex_str(AMBER_FG)}"><b>Se atrasar:</b></font> {w.get("ajuste","")}',ST['small']),
        ]],colWidths=['50%','50%'])
        fa.setStyle(TableStyle([('BACKGROUND',(0,0),(0,0),GRAY_LIGHT),
            ('BACKGROUND',(1,0),(1,0),AMBER_BG),('ROWPADDING',(0,0),(-1,-1),5),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
        story.append(fa); story.append(Spacer(1,0.35*cm))

    # Mensagem final
    story.append(PageBreak())
    msg = dados.get('mensagem_final','')
    final_t = Table([[[
        Paragraph('Mensagem Final',ParagraphStyle('ft',fontName='Helvetica-Bold',
            fontSize=12,textColor=WHITE,spaceAfter=10)),
        Paragraph(msg, ST['final']),
    ]]],colWidths=[None])
    final_t.setStyle(TableStyle([('BACKGROUND',(0,0),(0,0),NAVY),
        ('ROWPADDING',(0,0),(-1,-1),18)]))
    story.append(final_t)

    doc.build(story, canvasmaker=NumberedCanvas)
