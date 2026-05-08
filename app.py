import streamlit as st
import pandas as pd
from datetime import datetime
import io

# Configuración visual
st.set_page_config(page_title="Comisiones Distri-Lisu", page_icon="🔴")

st.markdown("""
    <style>
    .stButton>button { background-color: #ee122c; color: white; font-weight: bold; width: 100%; height: 3em; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #ddd; }
    [data-testid="stExpander"] { border: 1px solid #ee122c; border-radius: 10px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔴 Auditoría Distri-Lisu")
st.write("Versión 2026.4 - Reporte Detallado")

vendedor = st.text_input("Nombre del Vendedor", placeholder="Ej: Elias")

# --- ENTRADA DE DATOS ---
with st.expander("📊 INDICADORES CORE", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        obj_icb = st.number_input("Objetivo ICB", min_value=1, value=100)
        real_icb = st.number_input("Real ICB", min_value=0, value=0)
        pct_icb = (real_icb / obj_icb) * 100
        exc_icb = max(0, int(real_icb - (obj_icb * 1.10)))
    with c2:
        obj_comp = st.number_input("Objetivo Comp.", min_value=1, value=100)
        real_comp = st.number_input("Real Comp.", min_value=0, value=0)
        pct_comp = (real_comp / obj_comp) * 100
        exc_comp = max(0, int(real_comp - (obj_comp * 1.10)))
    
    st.divider()
    psr = st.number_input("Cantidad PSR/ICB", min_value=0, value=0)

with st.expander("📱 CLARO PAY"):
    c3, c4 = st.columns(2)
    si_pct = c3.number_input("% Sell In CP", min_value=0.0, value=75.0)
    ca_q = c4.number_input("Activaciones CP (Cant.)", min_value=0, value=0)

with st.expander("🏠 PRODUCTOS FIJOS"):
    c5, c6 = st.columns(2)
    portas = c5.number_input("Portabilidades", min_value=0, value=0)
    lineas = c6.number_input("Líneas Nuevas", min_value=0, value=0)
    baf = c5.number_input("BAF Internet", min_value=0, value=0)
    cp5k = c6.number_input("CP >$5k", min_value=0, value=0)

with st.expander("🏆 BONOS"):
    l_icb = st.checkbox("Líder ICB ($9545)")
    l_comp = st.checkbox("Líder Completos ($9545)")

# --- LÓGICA DE AUDITORÍA ---
def calcular_todo():
    # 1. Escalas Core
    def escala(pct):
        if pct >= 110: return 97749
        elif pct >= 105: return 83376
        elif pct >= 100: return 69000
        elif pct >= 90: return 44850
        elif pct >= 80: return 27600
        return 0

    p_icb = escala(pct_icb)
    p_comp = escala(pct_comp)
    p_psr = 140760 if psr >= 144 else 115920 if psr >= 132 else 92000 if psr >= 125 else 59800 if psr >= 108 else 0
    
    monto_exc_icb = exc_icb * 191
    monto_exc_comp = exc_comp * 423
    base_core = p_icb + p_comp + p_psr + monto_exc_icb + monto_exc_comp

    # 2. Modificadores CP
    mod_si = 0.2 if si_pct>=80 else 0.1 if si_pct>=75 else 0.0 if si_pct>=70 else -0.25 if si_pct>=60 else -0.5
    mod_ca = 0.2 if ca_q>=44 else 0.1 if ca_q>=38 else 0.0 if ca_q>=31 else -0.25 if ca_q>=24 else -0.5
    mod_cp_total = mod_si + mod_ca
    impacto_cp = base_core * mod_cp_total

    # 3. Fijas
    fijas_total = (portas*5000) + (lineas*2500) + (baf*8000) + (cp5k*2500)

    # 4. Productividad
    subtotal = base_core + impacto_cp + fijas_total
    v_fijas_q = portas + lineas + baf
    mod_p = 0.15 if v_fijas_q >= 10 else 0.0 if v_fijas_q >= 5 else -0.15
    impacto_prod = subtotal * mod_p

    # 5. Final
    bonos = (9545 if l_icb else 0) + (9545 if l_comp else 0)
    total_final = max(0, subtotal + impacto_prod + bonos)

    return locals() # Retorna todas las variables locales para el reporte

if st.button("🚀 GENERAR AUDITORÍA COMPLETA"):
    d = calcular_todo()
    
    st.divider()
    st.metric("TOTAL A LIQUIDAR", f"${d['total_final']:,.2f}")

    # Crear Excel Detallado con Pandas
    output = io.BytesIO()
    
    # Tabla 1: Resumen General
    resumen = [
        ["Vendedor", vendedor],
        ["Fecha", datetime.now().strftime("%d/%m/%Y %H:%M")],
        ["---", "---"],
        ["BASE CORE (Incentivos + Excedentes)", d['base_core']],
        ["IMPACTO CLARO PAY", d['impacto_cp']],
        ["VENTAS FIJAS", d['fijas_total']],
        ["AJUSTE PRODUCTIVIDAD", d['impacto_prod']],
        ["BONOS RANKING", d['bonos']],
        ["TOTAL NETO", d['total_final']]
    ]
    
    # Tabla 2: Detalle Matemático (Caja Negra)
    detalle = [
        ["Categoría", "Variable", "Valor", "Monto/Impacto"],
        ["CORE", "Alcance ICB", f"{d['pct_icb']:.1f}%", f"${d['p_icb']}"],
        ["CORE", "Excedentes ICB", d['exc_icb'], f"${d['monto_exc_icb']}"],
        ["CORE", "Alcance Comp.", f"{d['pct_comp']:.1f}%", f"${d['p_comp']}"],
        ["CORE", "Excedentes Comp.", d['exc_comp'], f"${d['monto_exc_comp']}"],
        ["CORE", "Bono PSR", d['psr'], f"${d['p_psr']}"],
        ["CLARO PAY", "Modificador Sell In", f"{d['mod_si']*100}%", "-"],
        ["CLARO PAY", "Modificador Act.", f"{d['mod_ca']*100}%", "-"],
        ["PRODUCTIVIDAD", "Ventas Q (Portas+Lin+BAF)", d['v_fijas_q'], f"{d['mod_p']*100}%"]
    ]

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pd.DataFrame(resumen).to_excel(writer, sheet_name='Liquidación', index=False, header=False)
        pd.DataFrame(detalle).to_excel(writer, sheet_name='Detalle de Cálculos', index=False, header=False)

    st.download_button(
        label="📥 Descargar Reporte de Auditoría Full",
        data=output.getvalue(),
        file_name=f"Reporte_{vendedor}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    st.success("Cálculos verificados. El Excel incluye el desglose de excedentes y multiplicadores.")
