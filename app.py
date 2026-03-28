# ============================================================
#  FinansKobi — KOBİ Finansal Planlama Uygulaması
#  Python / Dash versiyonu — Spyder'da çalıştırılabilir
#
#  KURULUM (Anaconda Prompt'ta bir kez çalıştır):
#  pip install dash dash-bootstrap-components pandas openpyxl
#
#  ÇALIŞTIRMA:
#  Spyder'da bu dosyayı aç → F5'e bas (veya Run butonu)
#  Tarayıcıda: http://127.0.0.1:8050
# ============================================================

import dash
from dash import dcc, html, Input, Output, State, ctx, dash_table, ALL
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
import uuid
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import os


# ── Uygulama başlat ──────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="FinansKobi"
)

# ── Renk paleti ───────────────────────────────────────────────
YESIL      = "#1D9E75"
YESIL_ACK  = "#E1F5EE"
YESIL_KOY  = "#0F6E56"
KIRMIZI    = "#D85A30"
KIRMIZI_ACK= "#FAECE7"
KIRMIZI_KOY= "#993C1D"
SARI       = "#EF9F27"
SARI_ACK   = "#FAEEDA"
SARI_KOY   = "#854F0B"
MAVI       = "#378ADD"
MAVI_ACK   = "#E6F1FB"
MAVI_KOY   = "#185FA5"
ARKA_PLAN  = "#F4F3EF"
BEYAZ      = "#FFFFFF"
KOYU       = "#111110"

# ── Örnek başlangıç verisi ────────────────────────────────────
ORNEK_ISLEMLER = [
    {"id": "t1", "ad": "Satış Gelirleri",    "tutar": 85000, "tur": "gelir",  "kategori": "Satış",       "tarih": "2026-03-01", "siklik": "aylik"},
    {"id": "t2", "ad": "Hizmet Gelirleri",   "tutar": 32000, "tur": "gelir",  "kategori": "Hizmet",      "tarih": "2026-03-01", "siklik": "aylik"},
    {"id": "t3", "ad": "Personel Maaşları",  "tutar": 45000, "tur": "gider",  "kategori": "Personel",    "tarih": "2026-03-01", "siklik": "aylik"},
    {"id": "t4", "ad": "Kira",               "tutar": 12000, "tur": "gider",  "kategori": "Kira & Ofis", "tarih": "2026-03-01", "siklik": "aylik"},
    {"id": "t5", "ad": "Hammadde/Malzeme",   "tutar": 28000, "tur": "gider",  "kategori": "Üretim",      "tarih": "2026-03-01", "siklik": "aylik"},
    {"id": "t6", "ad": "Pazarlama",          "tutar": 8000,  "tur": "gider",  "kategori": "Pazarlama",   "tarih": "2026-03-01", "siklik": "aylik"},
    {"id": "t7", "ad": "Elektrik & Doğalgaz","tutar": 4500,  "tur": "gider",  "kategori": "Faturalar",   "tarih": "2026-03-01", "siklik": "aylik"},
]

ORNEK_KREDILER = [
    {"id": "k1", "ad": "Yatırım Kredisi (Garanti)", "tur": "Banka Kredisi",       "anapara": 500000, "kalan": 320000, "aylik_taksit": 9800,  "faiz": 28.5, "baslangic": "2024-01-01", "bitis": "2027-12-31", "not": "Makine alımı"},
    {"id": "k2", "ad": "Araç Leasing (BMW)",         "tur": "Leasing",             "anapara": 80000,  "kalan": 45000,  "aylik_taksit": 2200,  "faiz": 22.0, "baslangic": "2025-03-01", "bitis": "2027-02-28", "not": ""},
    {"id": "k3", "ad": "Kredi Kartı Borcu",          "tur": "Kredi Kartı",         "anapara": 25000,  "kalan": 18500,  "aylik_taksit": 3500,  "faiz": 36.0, "baslangic": "2026-01-01", "bitis": "2026-07-01", "not": "Tedarikçi ödemeleri"},
]

ORNEK_UZUN_VADELI = [
    {"id": "u1", "ad": "Yıllık Bakım Sözleşmesi (Müşteri A)", "tur": "gelir", "toplam": 120000, "aylik": 10000, "baslangic": "2026-01-01", "bitis": "2026-12-31", "kategori": "Hizmet Geliri", "not": ""},
    {"id": "u2", "ad": "Tedarikçi Taksit Ödemeleri",          "tur": "gider", "toplam": 60000,  "aylik": 5000,  "baslangic": "2026-01-01", "bitis": "2026-12-31", "kategori": "Tedarik",       "not": ""},
]

# ── Yardımcı fonksiyonlar ─────────────────────────────────────

def yeni_id():
    return str(uuid.uuid4())[:8]

def para_format(n):
    try:
        n = float(n)
        return f"₺{n:,.0f}".replace(",", ".")
    except:
        return "₺0"

def ay_label(yil, ay):
    aylar = ["Oca","Şub","Mar","Nis","May","Haz","Tem","Ağu","Eyl","Eki","Kas","Ara"]
    return f"{aylar[ay-1]} {yil}"

def ay_aktif_mi(yil, ay, baslangic_str, bitis_str):
    try:
        b = datetime.strptime(baslangic_str[:7], "%Y-%m")
        e = datetime.strptime(bitis_str[:7], "%Y-%m")
        c = datetime(yil, ay, 1)
        return b <= c <= e
    except:
        return False

def siklik_carpan(siklik, yil, ay, tx_tarih):
    try:
        tx_dt = datetime.strptime(tx_tarih[:7], "%Y-%m")
        cur_dt = datetime(yil, ay, 1)
        if cur_dt < tx_dt:
            return 0
        if siklik == "aylik":
            return 1
        if siklik == "tek_sefer":
            return 1 if cur_dt == tx_dt else 0
        if siklik == "ucaylik":
            diff = (cur_dt.year - tx_dt.year) * 12 + (cur_dt.month - tx_dt.month)
            return 1 if diff % 3 == 0 else 0
        if siklik == "yillik":
            return 1 if cur_dt.month == tx_dt.month else 0
    except:
        return 0
    return 0

def cashflow_hesapla(islemler, krediler, uzun_vadeli, acilis_bakiye, baslangic_ay, ay_sayisi):
    sonuc = []
    kumulatif = acilis_bakiye

    bugun = datetime.now()
    try:
        bas_dt = datetime.strptime(baslangic_ay, "%Y-%m")
    except:
        bas_dt = datetime(bugun.year, 1, 1)

    for i in range(ay_sayisi):
        dt = bas_dt + relativedelta(months=i)
        yil, ay = dt.year, dt.month
        label = ay_label(yil, ay)

        # İşlemsel gelir/gider
        islemsel_gelir = 0
        islemsel_gider = 0
        for tx in islemler:
            carpan = siklik_carpan(tx.get("siklik","aylik"), yil, ay, tx.get("tarih","2026-01-01"))
            if carpan == 0:
                continue
            if tx["tur"] == "gelir":
                islemsel_gelir += tx["tutar"] * carpan
            else:
                islemsel_gider += tx["tutar"] * carpan

        # Kredi taksitleri
        kredi_taksit = 0
        for k in krediler:
            if ay_aktif_mi(yil, ay, k.get("baslangic",""), k.get("bitis","")):
                kredi_taksit += k.get("aylik_taksit", 0)

        # Uzun vadeli
        uzun_gelir = 0
        uzun_gider = 0
        for u in uzun_vadeli:
            if ay_aktif_mi(yil, ay, u.get("baslangic",""), u.get("bitis","")):
                if u["tur"] == "gelir":
                    uzun_gelir += u.get("aylik", 0)
                else:
                    uzun_gider += u.get("aylik", 0)

        toplam_gelir = islemsel_gelir + uzun_gelir
        toplam_gider = islemsel_gider + kredi_taksit + uzun_gider
        net = toplam_gelir - toplam_gider
        kumulatif += net

        sonuc.append({
            "ay": f"{yil}-{ay:02d}",
            "label": label,
            "islemsel_gelir": round(islemsel_gelir),
            "uzun_gelir": round(uzun_gelir),
            "islemsel_gider": round(islemsel_gider),
            "kredi_taksit": round(kredi_taksit),
            "uzun_gider": round(uzun_gider),
            "toplam_gelir": round(toplam_gelir),
            "toplam_gider": round(toplam_gider),
            "net": round(net),
            "kumulatif": round(kumulatif),
        })

    return sonuc

# ── Grafik fonksiyonları ──────────────────────────────────────

GRAFIK_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=10, b=10),
    font=dict(family="DM Sans, sans-serif", size=12, color="#555"),
    legend=dict(orientation="h", y=-0.15, x=0),
)

def bar_grafik(cashflow):
    labels = [m["label"].split(" ")[0] for m in cashflow]
    fig = go.Figure()
    fig.add_bar(name="İşlemsel Gelir", x=labels, y=[m["islemsel_gelir"] for m in cashflow], marker_color=YESIL, marker_line_width=0)
    fig.add_bar(name="Uzun Vadeli Gelir", x=labels, y=[m["uzun_gelir"] for m in cashflow], marker_color="#9FE1CB", marker_line_width=0)
    fig.add_bar(name="İşlemsel Gider", x=labels, y=[-m["islemsel_gider"] for m in cashflow], marker_color=KIRMIZI, marker_line_width=0)
    fig.add_bar(name="Kredi Taksiti", x=labels, y=[-m["kredi_taksit"] for m in cashflow], marker_color=MAVI, marker_line_width=0)
    fig.add_bar(name="Uzun Vadeli Gider", x=labels, y=[-m["uzun_gider"] for m in cashflow], marker_color=SARI, marker_line_width=0)
    fig.add_hline(y=0, line_color="#ccc", line_width=1)
    fig.update_layout(**GRAFIK_LAYOUT, barmode="relative", height=280)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#f0f0f0")
    return fig

def kumulatif_grafik(cashflow):
    labels = [m["label"].split(" ")[0] for m in cashflow]
    fig = go.Figure()
    fig.add_scatter(name="Aylık Net", x=labels, y=[m["net"] for m in cashflow],
                    mode="lines", line=dict(color=MAVI, width=2, dash="dot"))
    fig.add_scatter(name="Kümülatif Bakiye", x=labels, y=[m["kumulatif"] for m in cashflow],
                    mode="lines+markers", line=dict(color=YESIL, width=2.5),
                    fill="tozeroy", fillcolor="rgba(29,158,117,0.07)")
    fig.add_hline(y=0, line_color=KIRMIZI, line_width=1, line_dash="dash")
    fig.update_layout(**GRAFIK_LAYOUT, height=220)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#f0f0f0")
    return fig

def senaryo_grafik(cashflow_baz, cashflow_iyi, cashflow_kotu):
    labels = [m["label"].split(" ")[0] for m in cashflow_baz]
    fig = go.Figure()
    fig.add_scatter(name="Kötümser", x=labels, y=[m["net"] for m in cashflow_kotu],
                    mode="lines", line=dict(color=KIRMIZI, width=1.5, dash="dot"))
    fig.add_scatter(name="Baz Senaryo", x=labels, y=[m["net"] for m in cashflow_baz],
                    mode="lines+markers", line=dict(color=YESIL, width=2.5))
    fig.add_scatter(name="İyimser", x=labels, y=[m["net"] for m in cashflow_iyi],
                    mode="lines", line=dict(color=MAVI, width=1.5, dash="dot"))
    fig.add_hline(y=0, line_color="#ccc", line_width=1)
    fig.update_layout(**GRAFIK_LAYOUT, height=240)
    return fig

# ── UI bileşenleri ────────────────────────────────────────────

def metrik_kart(baslik, deger, alt="", alt_renk="#888", sol_renk=YESIL):
    return dbc.Card([
        html.Div(style={"height":"3px","background":sol_renk,"borderRadius":"8px 8px 0 0"}),
        dbc.CardBody([
            html.P(baslik, style={"fontSize":"11px","color":"#888","marginBottom":"6px","lineHeight":"1.3"}),
            html.H4(deger, style={"fontSize":"20px","fontWeight":"600","color":"#111","marginBottom":"4px","letterSpacing":"-0.5px"}),
            html.P(alt, style={"fontSize":"11px","color":alt_renk,"margin":"0"}) if alt else html.Div(),
        ], style={"padding":"12px 16px"})
    ], style={"border":"0.5px solid rgba(0,0,0,0.08)","borderRadius":"10px","background":BEYAZ})

def rozet(metin, renk="gri"):
    renkler = {
        "yesil": {"bg":"#E1F5EE","color":"#0F6E56"},
        "kirmizi": {"bg":"#FAECE7","color":"#993C1D"},
        "sari": {"bg":"#FAEEDA","color":"#854F0B"},
        "mavi": {"bg":"#E6F1FB","color":"#185FA5"},
        "gri": {"bg":"#f0efe8","color":"#555"},
    }
    r = renkler.get(renk, renkler["gri"])
    return html.Span(metin, style={
        "display":"inline-block","fontSize":"11px","padding":"2px 8px",
        "borderRadius":"20px","background":r["bg"],"color":r["color"],"fontWeight":"500"
    })

def uyari_kutusu(mesaj, tip="warn"):
    renkler = {"warn":{"bg":SARI_ACK,"color":SARI_KOY,"border":SARI},
               "danger":{"bg":KIRMIZI_ACK,"color":KIRMIZI_KOY,"border":"#F0997B"},
               "ok":{"bg":YESIL_ACK,"color":YESIL_KOY,"border":"#9FE1CB"}}
    r = renkler.get(tip, renkler["warn"])
    return html.Div(mesaj, style={
        "background":r["bg"],"color":r["color"],
        "border":f"0.5px solid {r['border']}",
        "borderRadius":"6px","padding":"10px 14px",
        "fontSize":"13px","marginBottom":"10px"
    })

# ── Sayfa: Genel Bakış ────────────────────────────────────────

def sayfa_genel_bakis(veri):
    islemler = veri.get("islemler", ORNEK_ISLEMLER)
    krediler = veri.get("krediler", ORNEK_KREDILER)
    uzun_vadeli = veri.get("uzun_vadeli", ORNEK_UZUN_VADELI)
    acilis = veri.get("acilis_bakiye", 150000)

    bugun = datetime.now()
    bas_ay = f"{bugun.year}-01"
    cf = cashflow_hesapla(islemler, krediler, uzun_vadeli, acilis, bas_ay, 12)

    cur_idx = next((i for i, m in enumerate(cf) if m["ay"] == f"{bugun.year}-{bugun.month:02d}"), 0)
    current = cf[cur_idx] if cf else {}
    prev = cf[cur_idx - 1] if cur_idx > 0 else {}

    toplam_gelir = current.get("toplam_gelir", 0)
    toplam_gider = current.get("toplam_gider", 0)
    net = toplam_gelir - toplam_gider
    marj = round((net / toplam_gelir * 100), 1) if toplam_gelir > 0 else 0
    toplam_kredi = sum(k.get("kalan", 0) for k in krediler)
    aylik_kredi = sum(k.get("aylik_taksit", 0) for k in krediler)
    bakiye = current.get("kumulatif", acilis)

    prev_net = prev.get("toplam_gelir",0) - prev.get("toplam_gider",0) if prev else net
    degisim = round(((net - prev_net) / abs(prev_net)) * 100, 1) if prev_net != 0 else 0

    uyarilar = []
    if marj < 5: uyarilar.append(uyari_kutusu(f"⚠ Kâr marjı kritik: %{marj}. Gider optimizasyonu gerekli.", "danger"))
    elif marj < 15: uyarilar.append(uyari_kutusu(f"⚠ Kâr marjı %{marj} — hedef %15 üzeri.", "warn"))
    neg_aylar = [m for m in cf if m["kumulatif"] < 0]
    if neg_aylar: uyarilar.append(uyari_kutusu(f"⚠ {neg_aylar[0]['label']} ayında nakit negatife düşüyor!", "danger"))
    if not uyarilar: uyarilar.append(uyari_kutusu("✓ Finansal göstergeler sağlıklı.", "ok"))

    return html.Div([
        html.H4("Genel Bakış", style={"fontWeight":"600","marginBottom":"20px","letterSpacing":"-0.4px"}),
        dbc.Row([
            dbc.Col(metrik_kart("Bu Ay Toplam Gelir", para_format(toplam_gelir), alt_renk=YESIL_KOY, sol_renk=YESIL), width=2),
            dbc.Col(metrik_kart("Bu Ay Toplam Gider", para_format(toplam_gider), f"Kredi: {para_format(current.get('kredi_taksit',0))}", SARI_KOY, KIRMIZI), width=2),
            dbc.Col(metrik_kart("Net Kâr", para_format(net), f"{'↑' if degisim >= 0 else '↓'} %{abs(degisim)} geçen ay", YESIL_KOY if degisim >= 0 else KIRMIZI_KOY, YESIL if net >= 0 else KIRMIZI), width=2),
            dbc.Col(metrik_kart("Kâr Marjı", f"%{marj}", "Sağlıklı" if marj >= 15 else "Dikkat" if marj >= 5 else "Kritik", YESIL_KOY if marj >= 15 else SARI_KOY if marj >= 5 else KIRMIZI_KOY, YESIL if marj >= 15 else SARI if marj >= 5 else KIRMIZI), width=2),
            dbc.Col(metrik_kart("Toplam Kredi Bakiyesi", para_format(toplam_kredi), f"Aylık taksit: {para_format(aylik_kredi)}", SARI_KOY, MAVI), width=2),
            dbc.Col(metrik_kart("Mevcut Nakit", para_format(bakiye), "Kümülatif", YESIL_KOY if bakiye > 0 else KIRMIZI_KOY, YESIL if bakiye > 0 else KIRMIZI), width=2),
        ], className="g-2 mb-3"),
        html.Div(uyarilar),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.P("Aylık Gelir / Gider Karşılaştırması", style={"fontSize":"13px","color":"#555","fontWeight":"500","marginBottom":"8px"}),
                        dcc.Graph(figure=bar_grafik(cf), config={"displayModeBar": False}),
                    ], style={"padding":"16px 20px"})
                ], style={"border":"0.5px solid rgba(0,0,0,0.08)","borderRadius":"10px"})
            ], width=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.P("Kümülatif Nakit Akışı", style={"fontSize":"13px","color":"#555","fontWeight":"500","marginBottom":"8px"}),
                        dcc.Graph(figure=kumulatif_grafik(cf), config={"displayModeBar": False}),
                    ], style={"padding":"16px 20px"})
                ], style={"border":"0.5px solid rgba(0,0,0,0.08)","borderRadius":"10px"})
            ], width=4),
        ], className="g-3"),
    ])

# ── Sayfa: Gelir & Gider ──────────────────────────────────────

def sayfa_islemler(veri):
    islemler = veri.get("islemler", ORNEK_ISLEMLER)

    satirlar = []
    for tx in islemler:
        renk = YESIL_KOY if tx["tur"] == "gelir" else KIRMIZI_KOY
        tur_rozet = rozet("Gelir", "yesil") if tx["tur"] == "gelir" else rozet("Gider", "kirmizi")
        siklik_map = {"aylik":"Her Ay","tek_sefer":"Tek Sefer","ucaylik":"Her 3 Ay","yillik":"Yıllık"}
        satirlar.append(html.Tr([
            html.Td(tx["ad"], style={"fontWeight":"500","fontSize":"13px"}),
            html.Td(rozet(tx.get("kategori",""), "gri")),
            html.Td(siklik_map.get(tx.get("siklik","aylik"),"Her Ay"), style={"fontSize":"13px"}),
            html.Td(para_format(tx["tutar"]), style={"fontWeight":"500","color":renk,"fontSize":"13px"}),
            html.Td(tur_rozet),
            html.Td(html.Button("✕", id={"type":"islem-sil","index":tx["id"]},
                style={"background":"none","border":"0.5px solid rgba(0,0,0,0.1)","borderRadius":"6px",
                       "width":"28px","height":"28px","cursor":"pointer","fontSize":"12px","color":"#888"})),
        ]))

    toplam_gelir = sum(t["tutar"] for t in islemler if t["tur"] == "gelir")
    toplam_gider = sum(t["tutar"] for t in islemler if t["tur"] == "gider")

    return html.Div([
        html.Div([
            html.H4("Gelir & Gider Kalemleri", style={"fontWeight":"600","marginBottom":"0","letterSpacing":"-0.4px"}),
            html.Button("+ Yeni Ekle", id="islem-ekle-btn",
                style={"background":KOYU,"color":BEYAZ,"border":"none","borderRadius":"6px",
                       "padding":"7px 16px","fontSize":"12px","fontWeight":"500","cursor":"pointer"}),
        ], style={"display":"flex","justifyContent":"space-between","alignItems":"center","marginBottom":"20px"}),

        dbc.Row([
            dbc.Col(metrik_kart("Aylık Gelir", para_format(toplam_gelir), sol_renk=YESIL), width=4),
            dbc.Col(metrik_kart("Aylık Gider", para_format(toplam_gider), sol_renk=KIRMIZI), width=4),
            dbc.Col(metrik_kart("Net", para_format(toplam_gelir - toplam_gider),
                                sol_renk=YESIL if toplam_gelir >= toplam_gider else KIRMIZI), width=4),
        ], className="g-2 mb-3"),

        dbc.Card([
            dbc.CardBody([
                html.Table([
                    html.Thead(html.Tr([
                        html.Th(s, style={"fontSize":"11px","color":"#888","textTransform":"uppercase",
                                          "letterSpacing":"0.5px","fontWeight":"500","padding":"8px 12px",
                                          "borderBottom":"0.5px solid rgba(0,0,0,0.08)"})
                        for s in ["Açıklama","Kategori","Sıklık","Tutar","Tür",""]
                    ])),
                    html.Tbody(satirlar, id="islemler-tablo-body"),
                ], style={"width":"100%","borderCollapse":"collapse"}),
            ], style={"padding":"0"}),
        ], style={"border":"0.5px solid rgba(0,0,0,0.08)","borderRadius":"10px"}),

        # Modal: yeni işlem ekle
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Yeni Kalem Ekle")),
            dbc.ModalBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Tür", style={"fontSize":"12px","fontWeight":"500","color":"#666","marginBottom":"4px"}),
                        dcc.Dropdown(["Gelir","Gider"], "Gelir", id="yeni-islem-tur", clearable=False),
                    ], width=6),
                    dbc.Col([
                        html.Label("Sıklık", style={"fontSize":"12px","fontWeight":"500","color":"#666","marginBottom":"4px"}),
                        dcc.Dropdown(["Her Ay","Tek Sefer","Her 3 Ay","Yıllık"], "Her Ay", id="yeni-islem-siklik", clearable=False),
                    ], width=6),
                ], className="mb-3"),
                html.Label("Açıklama", style={"fontSize":"12px","fontWeight":"500","color":"#666","marginBottom":"4px"}),
                dbc.Input(id="yeni-islem-ad", placeholder="Örn: Satış Gelirleri", className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Tutar (₺)", style={"fontSize":"12px","fontWeight":"500","color":"#666","marginBottom":"4px"}),
                        dbc.Input(id="yeni-islem-tutar", type="number", placeholder="0", className="mb-3"),
                    ], width=6),
                    dbc.Col([
                        html.Label("Kategori", style={"fontSize":"12px","fontWeight":"500","color":"#666","marginBottom":"4px"}),
                        dcc.Dropdown(
                            ["Satış","Hizmet","Kira Geliri","Personel","Kira & Ofis","Üretim","Pazarlama","Faturalar","Vergi","Diğer"],
                            "Satış", id="yeni-islem-kategori", clearable=False),
                    ], width=6),
                ]),
            ]),
            dbc.ModalFooter([
                dbc.Button("İptal", id="islem-modal-iptal", color="secondary", outline=True, className="me-2"),
                dbc.Button("Kaydet", id="islem-kaydet-btn", style={"background":KOYU,"border":"none"}),
            ]),
        ], id="islem-modal", is_open=False),
    ])

# ── Sayfa: Krediler ───────────────────────────────────────────

def sayfa_krediler(veri):
    krediler = veri.get("krediler", ORNEK_KREDILER)

    toplam_kalan = sum(k.get("kalan", 0) for k in krediler)
    aylik_taksit = sum(k.get("aylik_taksit", 0) for k in krediler)
    aylik_faiz = sum(k.get("kalan", 0) * k.get("faiz", 0) / 100 / 12 for k in krediler)

    kartlar = []
    for k in krediler:
        anapara = k.get("anapara", 0)
        kalan = k.get("kalan", 0)
        odenen = anapara - kalan
        yuzde = round((odenen / anapara * 100)) if anapara > 0 else 0

        bitis = k.get("bitis", "")
        if bitis:
            try:
                bitis_dt = datetime.strptime(bitis[:7], "%Y-%m")
                kalan_ay = (bitis_dt.year - datetime.now().year) * 12 + (bitis_dt.month - datetime.now().month)
                kalan_sure = f"{kalan_ay} ay" if kalan_ay > 0 else "Tamamlandı"
            except:
                kalan_sure = "–"
        else:
            kalan_sure = "–"

        tur_renk = {"Banka Kredisi":"mavi","Leasing":"sari","Kredi Kartı":"kirmizi","Tedarikçi Kredisi":"yesil"}.get(k.get("tur",""), "gri")

        kartlar.append(dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        rozet(k.get("tur", "Kredi"), tur_renk),
                        html.Button("✕", id={"type":"kredi-sil","index":k["id"]},
                            style={"background":"none","border":"0.5px solid rgba(0,0,0,0.1)","borderRadius":"6px",
                                   "width":"28px","height":"28px","cursor":"pointer","fontSize":"12px","color":"#888"}),
                    ], style={"display":"flex","justifyContent":"space-between","marginBottom":"8px"}),

                    html.H6(k["ad"], style={"fontWeight":"600","fontSize":"14px","marginBottom":"12px"}),

                    html.Div([
                        html.Span(f"Ödenen: {para_format(odenen)}", style={"fontSize":"11px","color":YESIL_KOY,"fontWeight":"500"}),
                        html.Span(f"Kalan: {para_format(kalan)}", style={"fontSize":"11px","color":KIRMIZI_KOY,"fontWeight":"500"}),
                    ], style={"display":"flex","justifyContent":"space-between","marginBottom":"5px"}),
                    dbc.Progress(value=yuzde, color="success", style={"height":"6px","marginBottom":"4px"}),
                    html.P(f"%{yuzde} ödendi", style={"fontSize":"10px","color":"#aaa","marginBottom":"12px"}),

                    dbc.Row([
                        dbc.Col([html.P("Aylık Taksit", style={"fontSize":"10px","color":"#999","marginBottom":"2px"}),
                                 html.P(para_format(k.get("aylik_taksit",0)), style={"fontSize":"13px","fontWeight":"600","color":KIRMIZI_KOY,"margin":"0"})], width=4),
                        dbc.Col([html.P("Faiz Oranı", style={"fontSize":"10px","color":"#999","marginBottom":"2px"}),
                                 html.P(f"%{k.get('faiz',0)}", style={"fontSize":"13px","fontWeight":"600","color":SARI_KOY,"margin":"0"})], width=4),
                        dbc.Col([html.P("Kalan Süre", style={"fontSize":"10px","color":"#999","marginBottom":"2px"}),
                                 html.P(kalan_sure, style={"fontSize":"13px","fontWeight":"600","color":"#111","margin":"0"})], width=4),
                    ], style={"background":"#fafaf8","borderRadius":"6px","padding":"8px","margin":"0"}),

                    html.P(k.get("not",""), style={"fontSize":"11px","color":"#aaa","marginTop":"8px","marginBottom":"0"}) if k.get("not") else html.Div(),
                ], style={"padding":"16px"}),
            ], style={"border":"0.5px solid rgba(0,0,0,0.08)","borderRadius":"10px"}),
        ], width=4, className="mb-3"))

    # Ekle butonu kartı
    kartlar.append(dbc.Col([
        dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.Div("+", style={"fontSize":"28px","color":"#bbb","marginBottom":"8px"}),
                    html.P("Kredi veya Yükümlülük Ekle", style={"fontSize":"13px","fontWeight":"500","color":"#888","marginBottom":"4px"}),
                    html.P("Banka kredisi, leasing, kredi kartı", style={"fontSize":"11px","color":"#bbb"}),
                ], style={"textAlign":"center"}),
            ], style={"padding":"30px","cursor":"pointer"}),
        ], id="kredi-ekle-btn", style={"border":"0.5px dashed rgba(0,0,0,0.15)","borderRadius":"10px",
                                        "background":"#fafaf8","cursor":"pointer","minHeight":"200px",
                                        "display":"flex","alignItems":"center","justifyContent":"center"}),
    ], width=4, className="mb-3"))

    return html.Div([
        html.Div([
            html.H4("Krediler & Uzun Vadeli Yükümlülükler", style={"fontWeight":"600","marginBottom":"0","letterSpacing":"-0.4px"}),
        ], style={"display":"flex","justifyContent":"space-between","alignItems":"center","marginBottom":"20px"}),

        dbc.Row([
            dbc.Col(metrik_kart("Toplam Kredi Bakiyesi", para_format(toplam_kalan), sol_renk=MAVI), width=4),
            dbc.Col(metrik_kart("Aylık Toplam Taksit", para_format(aylik_taksit), sol_renk=KIRMIZI), width=4),
            dbc.Col(metrik_kart("Aylık Faiz Yükü (tahmini)", para_format(aylik_faiz), sol_renk=SARI), width=4),
        ], className="g-2 mb-3"),

        dbc.Row(kartlar),

        # Modal: kredi ekle
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Yeni Kredi / Yükümlülük")),
            dbc.ModalBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Kredi Türü", style={"fontSize":"12px","fontWeight":"500","color":"#666","marginBottom":"4px"}),
                        dcc.Dropdown(["Banka Kredisi","Leasing","Kredi Kartı","Tedarikçi Kredisi","Diğer"],
                                     "Banka Kredisi", id="yeni-kredi-tur", clearable=False),
                    ], width=6),
                    dbc.Col([
                        html.Label("Kredi Adı", style={"fontSize":"12px","fontWeight":"500","color":"#666","marginBottom":"4px"}),
                        dbc.Input(id="yeni-kredi-ad", placeholder="Örn: Yatırım Kredisi"),
                    ], width=6),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Orijinal Tutar (₺)", style={"fontSize":"12px","fontWeight":"500","color":"#666","marginBottom":"4px"}),
                        dbc.Input(id="yeni-kredi-anapara", type="number", placeholder="0"),
                    ], width=4),
                    dbc.Col([
                        html.Label("Kalan Bakiye (₺)", style={"fontSize":"12px","fontWeight":"500","color":"#666","marginBottom":"4px"}),
                        dbc.Input(id="yeni-kredi-kalan", type="number", placeholder="0"),
                    ], width=4),
                    dbc.Col([
                        html.Label("Faiz Oranı (% Yıllık)", style={"fontSize":"12px","fontWeight":"500","color":"#666","marginBottom":"4px"}),
                        dbc.Input(id="yeni-kredi-faiz", type="number", placeholder="0", step=0.1),
                    ], width=4),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Başlangıç Tarihi", style={"fontSize":"12px","fontWeight":"500","color":"#666","marginBottom":"4px"}),
                        dbc.Input(id="yeni-kredi-baslangic", type="date"),
                    ], width=4),
                    dbc.Col([
                        html.Label("Bitiş Tarihi", style={"fontSize":"12px","fontWeight":"500","color":"#666","marginBottom":"4px"}),
                        dbc.Input(id="yeni-kredi-bitis", type="date"),
                    ], width=4),
                    dbc.Col([
                        html.Label("Aylık Taksit (₺)", style={"fontSize":"12px","fontWeight":"500","color":"#666","marginBottom":"4px"}),
                        dbc.Input(id="yeni-kredi-taksit", type="number", placeholder="0"),
                    ], width=4),
                ], className="mb-3"),
                html.Label("Notlar", style={"fontSize":"12px","fontWeight":"500","color":"#666","marginBottom":"4px"}),
                dbc.Textarea(id="yeni-kredi-not", placeholder="Banka adı, şube, açıklama...", style={"height":"70px"}),
            ]),
            dbc.ModalFooter([
                dbc.Button("İptal", id="kredi-modal-iptal", color="secondary", outline=True, className="me-2"),
                dbc.Button("Kaydet", id="kredi-kaydet-btn", style={"background":KOYU,"border":"none"}),
            ]),
        ], id="kredi-modal", is_open=False, size="lg"),
    ])

# ── Sayfa: Uzun Vadeli ────────────────────────────────────────

def sayfa_uzun_vadeli(veri):
    uzun_vadeli = veri.get("uzun_vadeli", ORNEK_UZUN_VADELI)

    bugun = datetime.now().strftime("%Y-%m")
    toplam_aylik_gelir = sum(u["aylik"] for u in uzun_vadeli if u["tur"] == "gelir" and u.get("baslangic","")[:7] <= bugun <= u.get("bitis","9999-12")[:7])
    toplam_aylik_gider = sum(u["aylik"] for u in uzun_vadeli if u["tur"] == "gider" and u.get("baslangic","")[:7] <= bugun <= u.get("bitis","9999-12")[:7])
    toplam_taahhut = sum(u["toplam"] for u in uzun_vadeli)

    satirlar = []
    for u in uzun_vadeli:
        aktif = u.get("baslangic","")[:7] <= bugun <= u.get("bitis","9999-12")[:7]
        renk = YESIL_KOY if u["tur"] == "gelir" else KIRMIZI_KOY
        satirlar.append(html.Tr([
            html.Td([
                html.Div(u["ad"], style={"fontWeight":"500","fontSize":"13px"}),
                html.Div(u.get("not",""), style={"fontSize":"11px","color":"#aaa"}) if u.get("not") else html.Span(),
            ]),
            html.Td(rozet(u.get("kategori",""), "gri")),
            html.Td([
                html.Div(u.get("baslangic","")[:7].replace("-","/"), style={"fontSize":"12px"}),
                html.Div("↓", style={"fontSize":"10px","color":"#bbb"}),
                html.Div(u.get("bitis","")[:7].replace("-","/"), style={"fontSize":"12px"}),
            ]),
            html.Td(para_format(u.get("aylik",0)), style={"fontWeight":"500","color":renk,"fontSize":"13px"}),
            html.Td(para_format(u.get("toplam",0)), style={"fontSize":"13px"}),
            html.Td(rozet("Aktif","yesil") if aktif else rozet("Pasif","gri")),
            html.Td(html.Button("✕", id={"type":"uzun-sil","index":u["id"]},
                style={"background":"none","border":"0.5px solid rgba(0,0,0,0.1)","borderRadius":"6px",
                       "width":"28px","height":"28px","cursor":"pointer","fontSize":"12px","color":"#888"})),
        ]))

    return html.Div([
        html.Div([
            html.H4("Uzun Vadeli Gelir & Giderler", style={"fontWeight":"600","marginBottom":"0","letterSpacing":"-0.4px"}),
            html.Button("+ Ekle", id="uzun-ekle-btn",
                style={"background":KOYU,"color":BEYAZ,"border":"none","borderRadius":"6px",
                       "padding":"7px 16px","fontSize":"12px","fontWeight":"500","cursor":"pointer"}),
        ], style={"display":"flex","justifyContent":"space-between","alignItems":"center","marginBottom":"16px"}),

        html.Div([
            html.Strong("Bu bölüm ne işe yarar? "),
            "Sözleşmeli gelirler, taksitli ödemeler, devlet teşvikleri gibi birden fazla aya yayılan kalemleri buraya girin. Cash Flow hesaplamasına otomatik dahil edilir."
        ], style={"background":MAVI_ACK,"border":f"0.5px solid #B5D4F4","borderRadius":"6px",
                  "padding":"11px 14px","fontSize":"13px","color":MAVI_KOY,"marginBottom":"18px"}),

        dbc.Row([
            dbc.Col(metrik_kart("Aylık Uzun Vadeli Gelir", para_format(toplam_aylik_gelir), sol_renk=YESIL), width=4),
            dbc.Col(metrik_kart("Aylık Uzun Vadeli Gider", para_format(toplam_aylik_gider), sol_renk=KIRMIZI), width=4),
            dbc.Col(metrik_kart("Toplam Taahhüt", para_format(toplam_taahhut), sol_renk="#7F77DD"), width=4),
        ], className="g-2 mb-3"),

        dbc.Card([
            dbc.CardBody([
                html.Table([
                    html.Thead(html.Tr([
                        html.Th(s, style={"fontSize":"11px","color":"#888","textTransform":"uppercase",
                                          "letterSpacing":"0.5px","fontWeight":"500","padding":"8px 12px",
                                          "borderBottom":"0.5px solid rgba(0,0,0,0.08)"})
                        for s in ["Açıklama","Kategori","Süre","Aylık Tutar","Toplam","Durum",""]
                    ])),
                    html.Tbody(satirlar),
                ], style={"width":"100%","borderCollapse":"collapse"}),
            ], style={"padding":"0"}),
        ], style={"border":"0.5px solid rgba(0,0,0,0.08)","borderRadius":"10px"}),

        # Modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Uzun Vadeli Kalem Ekle")),
            dbc.ModalBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Tür", style={"fontSize":"12px","fontWeight":"500","color":"#666","marginBottom":"4px"}),
                        dcc.Dropdown(["Uzun Vadeli Gelir","Uzun Vadeli Gider"], "Uzun Vadeli Gelir", id="yeni-uzun-tur", clearable=False),
                    ], width=6),
                    dbc.Col([
                        html.Label("Açıklama", style={"fontSize":"12px","fontWeight":"500","color":"#666","marginBottom":"4px"}),
                        dbc.Input(id="yeni-uzun-ad", placeholder="Örn: Yıllık Bakım Sözleşmesi"),
                    ], width=6),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Başlangıç", style={"fontSize":"12px","fontWeight":"500","color":"#666","marginBottom":"4px"}),
                        dbc.Input(id="yeni-uzun-baslangic", type="date"),
                    ], width=6),
                    dbc.Col([
                        html.Label("Bitiş", style={"fontSize":"12px","fontWeight":"500","color":"#666","marginBottom":"4px"}),
                        dbc.Input(id="yeni-uzun-bitis", type="date"),
                    ], width=6),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Toplam Tutar (₺)", style={"fontSize":"12px","fontWeight":"500","color":"#666","marginBottom":"4px"}),
                        dbc.Input(id="yeni-uzun-toplam", type="number", placeholder="0"),
                    ], width=6),
                    dbc.Col([
                        html.Label("Aylık Tutar (₺)", style={"fontSize":"12px","fontWeight":"500","color":"#666","marginBottom":"4px"}),
                        dbc.Input(id="yeni-uzun-aylik", type="number", placeholder="0"),
                    ], width=6),
                ], className="mb-3"),
                html.Label("Kategori", style={"fontSize":"12px","fontWeight":"500","color":"#666","marginBottom":"4px"}),
                dcc.Dropdown(["Hizmet Geliri","Satış Geliri","Tedarik","Abonelik","Devlet Teşviği","Diğer"],
                             "Hizmet Geliri", id="yeni-uzun-kategori", clearable=False, className="mb-3"),
                html.Label("Notlar", style={"fontSize":"12px","fontWeight":"500","color":"#666","marginBottom":"4px"}),
                dbc.Input(id="yeni-uzun-not", placeholder="Müşteri adı, sözleşme no..."),
            ]),
            dbc.ModalFooter([
                dbc.Button("İptal", id="uzun-modal-iptal", color="secondary", outline=True, className="me-2"),
                dbc.Button("Kaydet", id="uzun-kaydet-btn", style={"background":KOYU,"border":"none"}),
            ]),
        ], id="uzun-modal", is_open=False),
    ])

# ── Sayfa: Cash Flow ──────────────────────────────────────────

def sayfa_cashflow(veri, horizon=12):
    islemler = veri.get("islemler", ORNEK_ISLEMLER)
    krediler = veri.get("krediler", ORNEK_KREDILER)
    uzun_vadeli = veri.get("uzun_vadeli", ORNEK_UZUN_VADELI)
    acilis = veri.get("acilis_bakiye", 150000)

    bugun = datetime.now()
    bas_ay = f"{bugun.year}-{bugun.month:02d}"
    cf = cashflow_hesapla(islemler, krediler, uzun_vadeli, acilis, bas_ay, horizon)

    if not cf:
        return html.Div("Veri yok")

    ort_net = round(sum(m["net"] for m in cf) / len(cf))
    en_iyi = max(cf, key=lambda m: m["net"])
    en_dusuk = min(cf, key=lambda m: m["kumulatif"])
    neg_aylar = [m for m in cf if m["kumulatif"] < 0]

    tablo_satirlari = []
    bugun_str = f"{bugun.year}-{bugun.month:02d}"
    for m in cf:
        net_renk = YESIL_KOY if m["net"] >= 0 else KIRMIZI_KOY
        bak_renk = YESIL_KOY if m["kumulatif"] >= 0 else KIRMIZI_KOY
        is_current = m["ay"] == bugun_str
        style = {"background":"rgba(29,158,117,0.04)"} if is_current else {}
        tablo_satirlari.append(html.Tr([
            html.Td(html.Strong(m["label"]) if is_current else m["label"], style={"fontSize":"13px","padding":"8px 10px",**style}),
            html.Td(para_format(m["islemsel_gelir"]), style={"color":YESIL_KOY,"fontSize":"12px","padding":"8px 10px",**style}),
            html.Td(para_format(m["uzun_gelir"]), style={"color":"#5DCAA5","fontSize":"12px","padding":"8px 10px",**style}),
            html.Td(para_format(m["islemsel_gider"]), style={"color":KIRMIZI_KOY,"fontSize":"12px","padding":"8px 10px",**style}),
            html.Td(para_format(m["kredi_taksit"]), style={"color":MAVI_KOY,"fontSize":"12px","padding":"8px 10px",**style}),
            html.Td(para_format(m["uzun_gider"]), style={"color":SARI_KOY,"fontSize":"12px","padding":"8px 10px",**style}),
            html.Td(para_format(m["net"]), style={"fontWeight":"600","color":net_renk,"fontSize":"12px","padding":"8px 10px",**style}),
            html.Td(para_format(m["kumulatif"]), style={"fontWeight":"500","color":bak_renk,"fontSize":"12px","padding":"8px 10px",**style}),
        ]))

    return html.Div([
        html.Div([
            html.H4("Cash Flow Analizi", style={"fontWeight":"600","marginBottom":"0","letterSpacing":"-0.4px"}),
            html.Div([
                html.Span("Dönem: ", style={"fontSize":"13px","color":"#888","marginRight":"8px"}),
                *[html.Button(f"{h} ay", id={"type":"cf-horizon","index":h},
                    style={"padding":"4px 12px","borderRadius":"20px","border":"0.5px solid rgba(0,0,0,0.12)",
                           "background": KOYU if h == horizon else "transparent",
                           "color": BEYAZ if h == horizon else "#666",
                           "fontSize":"12px","fontWeight":"500","cursor":"pointer","marginRight":"4px"})
                  for h in [6, 12, 18, 24]]
            ], style={"display":"flex","alignItems":"center"}),
        ], style={"display":"flex","justifyContent":"space-between","alignItems":"center","marginBottom":"16px"}),

        dbc.Row([
            dbc.Col(metrik_kart("Ort. Aylık Net", para_format(ort_net), sol_renk=YESIL if ort_net >= 0 else KIRMIZI), width=3),
            dbc.Col(metrik_kart("En İyi Ay", en_iyi["label"], para_format(en_iyi["net"]), YESIL_KOY, YESIL), width=3),
            dbc.Col(metrik_kart("En Düşük Bakiye", para_format(en_dusuk["kumulatif"]), en_dusuk["label"],
                                KIRMIZI_KOY if en_dusuk["kumulatif"] < 0 else YESIL_KOY,
                                KIRMIZI if en_dusuk["kumulatif"] < 0 else YESIL), width=3),
            dbc.Col(metrik_kart("Negatif Nakit Ayı", str(len(neg_aylar)),
                                neg_aylar[0]["label"] + "'den itibaren" if neg_aylar else "Yok",
                                KIRMIZI_KOY if neg_aylar else YESIL_KOY,
                                KIRMIZI if neg_aylar else YESIL), width=3),
        ], className="g-2 mb-3"),

        (uyari_kutusu(f"⚠ {neg_aylar[0]['label']} ayında nakit bakiye negatife düşüyor ({para_format(neg_aylar[0]['kumulatif'])}). Finansman planı yapın!", "danger") if neg_aylar else html.Div()),

        dbc.Card([dbc.CardBody([
            html.P("Aylık Nakit Giriş / Çıkış Dağılımı", style={"fontSize":"13px","color":"#555","fontWeight":"500","marginBottom":"8px"}),
            dcc.Graph(figure=bar_grafik(cf), config={"displayModeBar":False}),
        ], style={"padding":"16px 20px"})], style={"border":"0.5px solid rgba(0,0,0,0.08)","borderRadius":"10px","marginBottom":"14px"}),

        dbc.Card([dbc.CardBody([
            html.P("Kümülatif Nakit Pozisyonu", style={"fontSize":"13px","color":"#555","fontWeight":"500","marginBottom":"8px"}),
            dcc.Graph(figure=kumulatif_grafik(cf), config={"displayModeBar":False}),
        ], style={"padding":"16px 20px"})], style={"border":"0.5px solid rgba(0,0,0,0.08)","borderRadius":"10px","marginBottom":"14px"}),

        dbc.Card([dbc.CardBody([
            html.P("Aylık Detay Tablosu", style={"fontSize":"13px","color":"#555","fontWeight":"500","marginBottom":"12px"}),
            html.Div([
                html.Table([
                    html.Thead(html.Tr([
                        html.Th(s, style={"fontSize":"11px","color":"#888","textTransform":"uppercase",
                                          "letterSpacing":"0.5px","fontWeight":"500","padding":"8px 10px",
                                          "borderBottom":"0.5px solid rgba(0,0,0,0.08)","whiteSpace":"nowrap"})
                        for s in ["Ay","İşl. Gelir","UV Gelir","İşl. Gider","Kredi","UV Gider","Net Akış","Bakiye"]
                    ])),
                    html.Tbody(tablo_satirlari),
                ], style={"width":"100%","borderCollapse":"collapse"}),
            ], style={"overflowX":"auto"}),
        ], style={"padding":"16px 20px"})], style={"border":"0.5px solid rgba(0,0,0,0.08)","borderRadius":"10px"}),
    ])

# ── Sayfa: Tahmin ─────────────────────────────────────────────

def sayfa_tahmin(veri, gelir_buyume=4, maliyet_artis=2):
    islemler = veri.get("islemler", ORNEK_ISLEMLER)
    krediler = veri.get("krediler", ORNEK_KREDILER)
    uzun_vadeli = veri.get("uzun_vadeli", ORNEK_UZUN_VADELI)
    acilis = veri.get("acilis_bakiye", 150000)

    bugun = datetime.now()
    bas_ay = f"{bugun.year}-{bugun.month:02d}"

    def tahmin_hesapla(inc_b, exp_b):
        base = cashflow_hesapla(islemler, krediler, uzun_vadeli, acilis, bas_ay, 12)
        result = []
        for i, m in enumerate(base):
            ig = (1 + inc_b/100) ** i
            eg = (1 + exp_b/100) ** i
            proj_gelir = (m["islemsel_gelir"] + m["uzun_gelir"]) * ig
            proj_gider = (m["islemsel_gider"] + m["uzun_gider"]) * eg + m["kredi_taksit"]
            net = proj_gelir - proj_gider
            result.append({**m, "proj_gelir": round(proj_gelir), "proj_gider": round(proj_gider), "proj_net": round(net)})
        return result

    baz = tahmin_hesapla(gelir_buyume, maliyet_artis)
    iyi = tahmin_hesapla(gelir_buyume * 1.5, maliyet_artis * 0.7)
    kotu = tahmin_hesapla(gelir_buyume * 0.3, maliyet_artis * 1.5)

    yillik_gelir = sum(m["proj_gelir"] for m in baz)
    yillik_gider = sum(m["proj_gider"] for m in baz)
    yillik_net = yillik_gelir - yillik_gider
    neg_sayisi = len([m for m in baz if m["proj_net"] < 0])

    tablo_satirlari = []
    for m in baz:
        marj = round((m["proj_net"] / m["proj_gelir"]) * 100, 1) if m["proj_gelir"] > 0 else 0
        marj_rozet = rozet(f"Sağlıklı %{marj}", "yesil") if marj >= 15 else rozet(f"Dikkat %{marj}", "sari") if marj >= 5 else rozet(f"Kritik %{marj}", "kirmizi")
        tablo_satirlari.append(html.Tr([
            html.Td(html.Strong(m["label"]), style={"fontSize":"13px","padding":"8px 12px"}),
            html.Td(para_format(m["proj_gelir"]), style={"color":YESIL_KOY,"fontSize":"13px","padding":"8px 12px"}),
            html.Td(para_format(m["proj_gider"]), style={"color":KIRMIZI_KOY,"fontSize":"13px","padding":"8px 12px"}),
            html.Td(para_format(m["proj_net"]), style={"fontWeight":"600","color":YESIL_KOY if m["proj_net"] >= 0 else KIRMIZI_KOY,"fontSize":"13px","padding":"8px 12px"}),
            html.Td(marj_rozet, style={"padding":"8px 12px"}),
        ]))

    return html.Div([
        html.H4("Finansal Tahmin & Senaryo Analizi", style={"fontWeight":"600","marginBottom":"20px","letterSpacing":"-0.4px"}),

        dbc.Card([dbc.CardBody([
            html.P("Büyüme Varsayımları", style={"fontSize":"13px","fontWeight":"500","marginBottom":"14px"}),
            dbc.Row([
                dbc.Col([
                    html.Label(f"Aylık Gelir Büyümesi: %{gelir_buyume}", style={"fontSize":"12px","fontWeight":"500","color":"#666","marginBottom":"6px"}),
                    dcc.Slider(id="gelir-buyume-slider", min=-5, max=20, step=0.5, value=gelir_buyume,
                               marks={-5:"-5%",0:"0%",5:"5%",10:"10%",15:"15%",20:"20%"},
                               tooltip={"placement":"bottom","always_visible":False}),
                ], width=6),
                dbc.Col([
                    html.Label(f"Aylık Maliyet Artışı: %{maliyet_artis}", style={"fontSize":"12px","fontWeight":"500","color":"#666","marginBottom":"6px"}),
                    dcc.Slider(id="maliyet-artis-slider", min=-5, max=15, step=0.5, value=maliyet_artis,
                               marks={-5:"-5%",0:"0%",5:"5%",10:"10%",15:"15%"},
                               tooltip={"placement":"bottom","always_visible":False}),
                ], width=6),
            ]),
        ], style={"padding":"16px 20px"})], style={"border":"0.5px solid rgba(0,0,0,0.08)","borderRadius":"10px","marginBottom":"16px"}),

        dbc.Row([
            dbc.Col(metrik_kart("Yıllık Tahmini Gelir", para_format(yillik_gelir), sol_renk=YESIL), width=3),
            dbc.Col(metrik_kart("Yıllık Tahmini Gider", para_format(yillik_gider), sol_renk=KIRMIZI), width=3),
            dbc.Col(metrik_kart("Yıllık Net Kâr", para_format(yillik_net), sol_renk=YESIL if yillik_net >= 0 else KIRMIZI), width=3),
            dbc.Col(metrik_kart("Kötü Ay Sayısı", str(neg_sayisi), "Net negatif ay" if neg_sayisi > 0 else "Tüm aylar pozitif",
                                KIRMIZI_KOY if neg_sayisi > 0 else YESIL_KOY,
                                KIRMIZI if neg_sayisi > 0 else YESIL), width=3),
        ], className="g-2 mb-3"),

        dbc.Card([dbc.CardBody([
            html.P("Senaryo Karşılaştırması — Aylık Net Kâr", style={"fontSize":"13px","color":"#555","fontWeight":"500","marginBottom":"8px"}),
            dcc.Graph(figure=senaryo_grafik(baz, iyi, kotu), config={"displayModeBar":False}),
        ], style={"padding":"16px 20px"})], style={"border":"0.5px solid rgba(0,0,0,0.08)","borderRadius":"10px","marginBottom":"14px"}),

        dbc.Card([dbc.CardBody([
            html.P("12 Aylık Tahmin Tablosu (Baz Senaryo)", style={"fontSize":"13px","color":"#555","fontWeight":"500","marginBottom":"12px"}),
            html.Table([
                html.Thead(html.Tr([
                    html.Th(s, style={"fontSize":"11px","color":"#888","textTransform":"uppercase",
                                      "letterSpacing":"0.5px","fontWeight":"500","padding":"8px 12px",
                                      "borderBottom":"0.5px solid rgba(0,0,0,0.08)"})
                    for s in ["Ay","Tahmini Gelir","Tahmini Gider","Net Kâr","Kâr Marjı"]
                ])),
                html.Tbody(tablo_satirlari),
            ], style={"width":"100%","borderCollapse":"collapse"}),
        ], style={"padding":"16px 20px"})], style={"border":"0.5px solid rgba(0,0,0,0.08)","borderRadius":"10px"}),
    ])

# ── Ana Layout ────────────────────────────────────────────────

app.layout = html.Div([
    # Global veri deposu (tarayıcı session'ında tutulur)
    dcc.Store(id="uygulama-verisi", data={
        "islemler": ORNEK_ISLEMLER,
        "krediler": ORNEK_KREDILER,
        "uzun_vadeli": ORNEK_UZUN_VADELI,
        "acilis_bakiye": 150000,
    }),
    dcc.Store(id="cf-horizon-store", data=12),
    dcc.Store(id="tahmin-store", data={"gelir_buyume": 4, "maliyet_artis": 2}),

    # Sidebar
    html.Div([
        html.Div([
            html.Div(style={"width":"26px","height":"26px","background":YESIL,"borderRadius":"7px","flexShrink":"0"}),
            html.Span("FinansKobi", style={"fontSize":"16px","fontWeight":"600","color":"white","letterSpacing":"-0.3px"}),
        ], style={"display":"flex","alignItems":"center","gap":"10px","padding":"20px 18px 8px"}),
        html.P("Demo İşletme A.Ş.", style={"fontSize":"11px","color":"#666","padding":"0 18px 16px","borderBottom":"0.5px solid #222"}),

        html.Nav([
            *[html.Button([
                html.Span(icon, style={"width":"18px","textAlign":"center","fontSize":"14px"}),
                html.Span(label),
            ], id=f"nav-{page_id}", n_clicks=0,
                style={"display":"flex","alignItems":"center","gap":"10px","padding":"9px 10px","borderRadius":"6px",
                       "border":"none","background":"transparent","cursor":"pointer","width":"100%",
                       "textAlign":"left","color":"#888","fontFamily":"DM Sans, sans-serif","fontSize":"13.5px"})
              for page_id, icon, label in [
                  ("genel","◈","Genel Bakış"),("islemler","⇅","Gelir & Gider"),
                  ("krediler","⬡","Krediler"),("uzun","◷","Uzun Vadeli"),
                  ("cashflow","◱","Cash Flow"),("tahmin","◈","Tahmin"),
              ]]
        ], style={"padding":"10px 8px","flex":"1","display":"flex","flexDirection":"column","gap":"2px"}),

        html.Div([
            html.P("v1.0.0 — Beta", style={"fontSize":"10px","color":"#555","fontFamily":"monospace","margin":"0"}),
            html.P("KOBİ Finansal Platform", style={"fontSize":"10px","color":"#444","margin":"0"}),
        ], style={"padding":"12px 18px","borderTop":"0.5px solid #222"}),
    ], style={"width":"220px","background":"#111110","display":"flex","flexDirection":"column",
              "position":"fixed","top":"0","left":"0","height":"100vh","overflowY":"auto"}),

    # Ana içerik
    html.Div(id="sayfa-icerigi",
             style={"marginLeft":"220px","padding":"28px 32px","maxWidth":"1200px","minHeight":"100vh"}),

    # Aktif sayfa takibi
    dcc.Store(id="aktif-sayfa", data="genel"),
], style={"background":ARKA_PLAN,"minHeight":"100vh","fontFamily":"DM Sans, sans-serif"})

# ── Callback: Sayfa navigasyonu ───────────────────────────────

@app.callback(
    Output("aktif-sayfa", "data"),
    [Input(f"nav-{p}", "n_clicks") for p in ["genel","islemler","krediler","uzun","cashflow","tahmin"]],
    prevent_initial_call=True,
)
def sayfa_degistir(*args):
    tetikleyen = ctx.triggered_id
    if tetikleyen:
        return tetikleyen.replace("nav-", "")
    return "genel"

@app.callback(
    Output("sayfa-icerigi", "children"),
    Input("aktif-sayfa", "data"),
    Input("uygulama-verisi", "data"),
    Input("cf-horizon-store", "data"),
    Input("tahmin-store", "data"),
)
def icerik_goster(sayfa, veri, horizon, tahmin_veri):
    if sayfa == "genel":    return sayfa_genel_bakis(veri)
    if sayfa == "islemler": return sayfa_islemler(veri)
    if sayfa == "krediler": return sayfa_krediler(veri)
    if sayfa == "uzun":     return sayfa_uzun_vadeli(veri)
    if sayfa == "cashflow": return sayfa_cashflow(veri, horizon)
    if sayfa == "tahmin":   return sayfa_tahmin(veri, tahmin_veri.get("gelir_buyume",4), tahmin_veri.get("maliyet_artis",2))
    return sayfa_genel_bakis(veri)

# ── Callback: CF horizon ──────────────────────────────────────

@app.callback(
    Output("cf-horizon-store", "data"),
    Input({"type":"cf-horizon","index":ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def cf_horizon_degistir(clicks):
    if not ctx.triggered_id:
        return 12
    return ctx.triggered_id["index"]

# ── Callback: Tahmin sliders ──────────────────────────────────

@app.callback(
    Output("tahmin-store", "data"),
    Input("gelir-buyume-slider", "value"),
    Input("maliyet-artis-slider", "value"),
    prevent_initial_call=True,
)
def tahmin_guncelle(gelir, maliyet):
    return {"gelir_buyume": gelir or 4, "maliyet_artis": maliyet or 2}

# ── Callback: İşlem ekle / sil ────────────────────────────────

@app.callback(
    Output("islem-modal", "is_open"),
    Input("islem-ekle-btn", "n_clicks"),
    Input("islem-modal-iptal", "n_clicks"),
    Input("islem-kaydet-btn", "n_clicks"),
    State("islem-modal", "is_open"),
    prevent_initial_call=True,
)
def islem_modal_toggle(ekle, iptal, kaydet, acik):
    tetikleyen = ctx.triggered_id
    if tetikleyen in ["islem-modal-iptal", "islem-kaydet-btn"]:
        return False
    return True

@app.callback(
    Output("uygulama-verisi", "data", allow_duplicate=True),
    Input("islem-kaydet-btn", "n_clicks"),
    State("yeni-islem-ad", "value"),
    State("yeni-islem-tutar", "value"),
    State("yeni-islem-tur", "value"),
    State("yeni-islem-siklik", "value"),
    State("yeni-islem-kategori", "value"),
    State("uygulama-verisi", "data"),
    prevent_initial_call=True,
)
def islem_kaydet(n, ad, tutar, tur, siklik, kategori, veri):
    if not n or not ad or not tutar:
        return veri
    siklik_map = {"Her Ay":"aylik","Tek Sefer":"tek_sefer","Her 3 Ay":"ucaylik","Yıllık":"yillik"}
    yeni = {
        "id": yeni_id(), "ad": ad,
        "tutar": float(tutar),
        "tur": "gelir" if tur == "Gelir" else "gider",
        "kategori": kategori or "Diğer",
        "tarih": datetime.now().strftime("%Y-%m-%d"),
        "siklik": siklik_map.get(siklik, "aylik"),
    }
    veri["islemler"] = veri.get("islemler", []) + [yeni]
    return veri

@app.callback(
    Output("uygulama-verisi", "data", allow_duplicate=True),
    Input({"type":"islem-sil","index":ALL}, "n_clicks"),
    State("uygulama-verisi", "data"),
    prevent_initial_call=True,
)
def islem_sil(clicks, veri):
    if not any(c for c in clicks if c):
        return veri
    sil_id = ctx.triggered_id["index"]
    veri["islemler"] = [t for t in veri.get("islemler",[]) if t["id"] != sil_id]
    return veri

# ── Callback: Kredi ekle / sil ────────────────────────────────

@app.callback(
    Output("kredi-modal", "is_open"),
    Input("kredi-ekle-btn", "n_clicks"),
    Input("kredi-modal-iptal", "n_clicks"),
    Input("kredi-kaydet-btn", "n_clicks"),
    State("kredi-modal", "is_open"),
    prevent_initial_call=True,
)
def kredi_modal_toggle(ekle, iptal, kaydet, acik):
    tetikleyen = ctx.triggered_id
    if tetikleyen in ["kredi-modal-iptal", "kredi-kaydet-btn"]:
        return False
    return True

@app.callback(
    Output("uygulama-verisi", "data", allow_duplicate=True),
    Input("kredi-kaydet-btn", "n_clicks"),
    State("yeni-kredi-ad", "value"),
    State("yeni-kredi-tur", "value"),
    State("yeni-kredi-anapara", "value"),
    State("yeni-kredi-kalan", "value"),
    State("yeni-kredi-faiz", "value"),
    State("yeni-kredi-taksit", "value"),
    State("yeni-kredi-baslangic", "value"),
    State("yeni-kredi-bitis", "value"),
    State("yeni-kredi-not", "value"),
    State("uygulama-verisi", "data"),
    prevent_initial_call=True,
)
def kredi_kaydet(n, ad, tur, anapara, kalan, faiz, taksit, bas, bit, not_, veri):
    if not n or not ad:
        return veri
    yeni = {
        "id": yeni_id(), "ad": ad, "tur": tur or "Banka Kredisi",
        "anapara": float(anapara or 0), "kalan": float(kalan or 0),
        "faiz": float(faiz or 0), "aylik_taksit": float(taksit or 0),
        "baslangic": bas or datetime.now().strftime("%Y-%m-%d"),
        "bitis": bit or "", "not": not_ or "",
    }
    veri["krediler"] = veri.get("krediler", []) + [yeni]
    return veri

@app.callback(
    Output("uygulama-verisi", "data", allow_duplicate=True),
    Input({"type":"kredi-sil","index":ALL}, "n_clicks"),
    State("uygulama-verisi", "data"),
    prevent_initial_call=True,
)
def kredi_sil(clicks, veri):
    if not any(c for c in clicks if c):
        return veri
    sil_id = ctx.triggered_id["index"]
    veri["krediler"] = [k for k in veri.get("krediler",[]) if k["id"] != sil_id]
    return veri

# ── Callback: Uzun vadeli ekle / sil ─────────────────────────

@app.callback(
    Output("uzun-modal", "is_open"),
    Input("uzun-ekle-btn", "n_clicks"),
    Input("uzun-modal-iptal", "n_clicks"),
    Input("uzun-kaydet-btn", "n_clicks"),
    State("uzun-modal", "is_open"),
    prevent_initial_call=True,
)
def uzun_modal_toggle(ekle, iptal, kaydet, acik):
    tetikleyen = ctx.triggered_id
    if tetikleyen in ["uzun-modal-iptal", "uzun-kaydet-btn"]:
        return False
    return True

@app.callback(
    Output("uygulama-verisi", "data", allow_duplicate=True),
    Input("uzun-kaydet-btn", "n_clicks"),
    State("yeni-uzun-ad", "value"),
    State("yeni-uzun-tur", "value"),
    State("yeni-uzun-toplam", "value"),
    State("yeni-uzun-aylik", "value"),
    State("yeni-uzun-baslangic", "value"),
    State("yeni-uzun-bitis", "value"),
    State("yeni-uzun-kategori", "value"),
    State("yeni-uzun-not", "value"),
    State("uygulama-verisi", "data"),
    prevent_initial_call=True,
)
def uzun_kaydet(n, ad, tur, toplam, aylik, bas, bit, kat, not_, veri):
    if not n or not ad:
        return veri
    yeni = {
        "id": yeni_id(), "ad": ad,
        "tur": "gelir" if "Gelir" in (tur or "") else "gider",
        "toplam": float(toplam or 0), "aylik": float(aylik or 0),
        "baslangic": bas or datetime.now().strftime("%Y-%m-%d"),
        "bitis": bit or "", "kategori": kat or "Diğer", "not": not_ or "",
    }
    veri["uzun_vadeli"] = veri.get("uzun_vadeli", []) + [yeni]
    return veri

@app.callback(
    Output("uygulama-verisi", "data", allow_duplicate=True),
    Input({"type":"uzun-sil","index":ALL}, "n_clicks"),
    State("uygulama-verisi", "data"),
    prevent_initial_call=True,
)
def uzun_sil(clicks, veri):
    if not any(c for c in clicks if c):
        return veri
    sil_id = ctx.triggered_id["index"]
    veri["uzun_vadeli"] = [u for u in veri.get("uzun_vadeli",[]) if u["id"] != sil_id]
    return veri

# ── Çalıştır ──────────────────────────────────────────────────

server = app.server


for endpoint, view in app.server.view_functions.items():
    app.server.view_functions[endpoint] = sifreli(view)

if __name__ == "__main__":
    print("=" * 55)
    print("  FinansKobi başlatılıyor...")
    print("  Tarayıcıda aç: http://127.0.0.1:8050")
    print("  Durdurmak için: Spyder konsolunda kırmızı kareye bas")
    print("=" * 55)
    app.run(debug=False, port=8050)
