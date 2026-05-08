import streamlit as st
import pandas as pd
from datetime import datetime
import io

# Configuración visual
st.set_page_config(page_title="Auditoría Claro Full", page_icon="🔴")

st.markdown("""
    <style>
    .stButton>button { background-color: #ee122c; color: white; font-weight: bold; width: 100%; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔴 Comisiones Distri-Lisu")
st.write("Versión 2026 - Mobile & Web")

vendedor = st.text_input("Nombre del Vendedor", placeholder="Ej: Elias")

# --- ENTRADA DE DATOS ---
with st.expander("📊 INDICADORES CORE", expanded=True):
    col1, col2 = st.columns(2)
    icb = col1.number_input("% Alcance ICB", min_value=0.0, value=0.0, step=0.1)
    comp = col2.number_input("% Alcance Completos", min_value=0.0, value=0.0, step=0.1)
    psr = st.number_input("Cantidad PSR", min_value=0, value=0)
    exc_icb = col1.number_input("Excedentes ICB", min_value=0, value=0)
    exc_comp = col2.number_input("Excedentes Comp.", min_value=0, value=0)

with st.expander("📱 CLARO PAY"):
    col3, col4 = st.columns(2)
    si_pct = col3.number_input("% Sell In CP", min_value=0.0, value=70.0)
    ca_q = col4.number_input("Cant. Activaciones CP", min_value=0, value=0)

with st.expander("🏠 PRODUCTOS FIJOS"):
    col5, col6 = st.columns(2)
    portas = col5.number_input("Portabilidades ($5000)", min_value=0, value=0)
    lineas = col6.number_input("Líneas Nuevas ($2500)", min_value=0, value=0)
    baf = col5.number_input("BAF Internet ($8000)", min_value=0, value=0)
    cp5k = col6.number_input("CP >$5k ($2500)", min_value=0, value=0)

with st.expander("🏆 BONOS Y EXTRAS"):
    l_icb = st.checkbox("Líder ICB ($9545)")
    l_comp = st.checkbox("Líder Completos ($9545)")

# --- LÓGICA DE CÁLCULO (LA QUE QUEDÓ DE 10) ---
def realizar_auditoria():
    # 1. Escala Core
    def escala(pct):
        if pct >= 110: return 97749
        elif pct >= 105: return 83376
        elif pct >= 100: return 69000
        elif pct >= 90: return 44850
        elif pct >= 80: return 27600
        return 0

    p_icb = escala(icb)
    p_comp = escala(comp)
    p_psr = 140760 if psr >= 144 else 115920 if psr >= 132 else 92000 if psr >= 125 else 59800 if psr >= 108 else 0
    monto_exc = (exc_icb * 191) + (exc_comp * 423)
    base_core = p_icb + p_comp + p_psr + monto_exc

    # 2. Modificadores CP
    mod_si = 0.2 if si_pct>=80 else 0.1 if si_pct>=75 else 0.0 if si_pct>=70 else -0.25 if si_pct>=60 else -0.5
    mod_ca = 0.2 if ca_q>=44 else 0.1 if ca_q>=38 else 0.0 if ca_q>=31 else -0.25 if ca_q>=24 else -0.5
    impacto_cp = base_core * (mod_si + mod_ca)
    monto_con_cp = base_core + impacto_cp

    # 3. Fijas
    v_portas, v_lineas = portas * 5000, lineas * 2500
    v_baf, v_cp5k = baf * 8000, cp5k * 2500
    total_fijas = v_portas + v_lineas + v_baf + v_cp5k

    # 4. Productividad
    m_cerrado = monto_con_cp + total_fijas
    tot_v = portas + lineas + baf
    mod_p = 0.15 if tot_v >= 10 else 0.0 if tot_v >= 5 else -0.15
    impacto_prod = m_cerrado * mod_p
    
    # 5. Total
    bonos = (9545 if l_icb else 0) + (9545 if l_comp else 0)
    total_final = max(0, m_cerrado + impacto_prod + bonos)
    
    return total_final, base_core, impacto_cp, total_fijas, impacto_prod, bonos

# --- MOSTRAR RESULTADOS ---
if st.button("CALCULAR Y GENERAR REPORTE"):
    res, core, i_cp, fijas, i_prod, bonos = realizar_auditoria()
    
    st.divider()
    st.metric(label="TOTAL NETO A COBRAR", value=f"${res:,.2f}")
    
    # Detalle para el vendedor
    st.write("### 📝 Desglose de Auditoría")
    col_a, col_b = st.columns(2)
    col_a.write(f"**Base Core:** ${core:,.0f}")
    col_a.write(f"**Impacto CP:** ${i_cp:,.0f}")
    col_b.write(f"**Ventas Fijas:** ${fijas:,.0f}")
    col_b.write(f"**Ajuste Prod:** ${i_prod:,.0f}")
    
    # Excel Detallado
    datos_excel = [
        ["Vendedor", vendedor],
        ["Fecha", datetime.now().strftime("%d/%m/%Y")],
        ["---", "---"],
        ["Base Core", core],
        ["Impacto CP", i_cp],
        ["Ventas Fijas", fijas],
        ["Ajuste Productividad", i_prod],
        ["Bonos Ranking", bonos],
        ["TOTAL FINAL", res]
    ]
    
    df = pd.DataFrame(datos_excel, columns=["Concepto", "Valor"])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    
    st.download_button(
        label="📥 Descargar Excel para Auditoría",
        data=output.getvalue(),
        file_name=f"Liquidacion_{vendedor}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )