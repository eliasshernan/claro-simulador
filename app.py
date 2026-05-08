import streamlit as st
import pandas as pd
from datetime import datetime
import io

# --- CONFIGURACIÓN VISUAL Y ESTILOS ---
st.set_page_config(page_title="Comisiones Distri-Lisu", page_icon="🔴")

st.markdown("""
    <style>
    /* Botón principal */
    .stButton>button { 
        background-color: #ee122c; 
        color: white; 
        font-weight: bold; 
        width: 100%; 
        height: 3em; 
        border-radius: 8px;
    }
    /* Arreglo para que la métrica se vea en fondo blanco (Modo Claro/Oscuro) */
    [data-testid="stMetricValue"] {
        color: #1e1e1e !important;
    }
    [data-testid="stMetricLabel"] {
        color: #555555 !important;
    }
    .stMetric { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 12px; 
        border: 2px solid #ee122c;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    /* Estilo de los expanders */
    [data-testid="stExpander"] {
        border: 1px solid #ddd;
        border-radius: 10px;
        background-color: rgba(238, 18, 44, 0.03);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🔴 Comisiones Distri-Lisu")
st.write(f"Versión 2026.7 - {datetime.now().strftime('%d/%m/%Y')}")

vendedor = st.text_input("Nombre del Vendedor", placeholder="Ej: Elias")

# --- ENTRADA DE DATOS ---
with st.expander("📊 INDICADORES BÁSICOS", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("ICB")
        icb_pct = st.number_input("% Alcance ICB", min_value=0.0, value=0.0, step=0.1)
        obj_icb_u = st.number_input("Objetivo ICB (Unidades)", min_value=1, value=100)
        # Cálculo: Excedentes si supera el 110%
        exc_icb = max(0, int(((icb_pct - 110) / 100) * obj_icb_u)) if icb_pct > 110 else 0
        st.caption(f"Excedentes detectados: {exc_icb}")

    with c2:
        st.subheader("Completos")
        comp_pct = st.number_input("% Alcance Completos", min_value=0.0, value=0.0, step=0.1)
        obj_comp_u = st.number_input("Objetivo Comp. (Unidades)", min_value=1, value=100)
        # Cálculo: Excedentes si supera el 110%
        exc_comp = max(0, int(((comp_pct - 110) / 100) * obj_comp_u)) if comp_pct > 110 else 0
        st.caption(f"Excedentes detectados: {exc_comp}")
    
    st.divider()
    psr = st.number_input("Cantidad PSR/ICB Total", min_value=0, value=0)

with st.expander("📱 CLARO PAY"):
    c3, c4 = st.columns(2)
    si_pct = c3.number_input("% Sell In CP", min_value=0.0, value=75.0)
    ca_q = c4.number_input("Activaciones CP (Cant. Real)", min_value=0, value=0)

with st.expander("🏠 REFERIDOS"):
    c5, c6 = st.columns(2)
    portas = c5.number_input("Portabilidades ($5k)", min_value=0, value=0)
    lineas = c6.number_input("Líneas Nuevas ($2.5k)", min_value=0, value=0)
    baf = c5.number_input("BAF Internet ($8k)", min_value=0, value=0)
    cp5k = c6.number_input("CP >$5k ($2.5k)", min_value=0, value=0)

with st.expander("🏆 BONOS RANKING"):
    l_icb = st.checkbox("Líder ICB ($9545)")
    l_comp = st.checkbox("Líder Completos ($9545)")

# --- LÓGICA DE AUDITORÍA ---
def calcular_todo():
    # 1. Escalas Core según %
    def escala(pct):
        if pct >= 110: return 97749
        elif pct >= 105: return 83376
        elif pct >= 100: return 69000
        elif pct >= 90: return 44850
        elif pct >= 80: return 27600
        return 0

    p_icb = escala(icb_pct)
    p_comp = escala(comp_pct)
    
    # Pago PSR según tabla
    p_psr = 140760 if psr >= 144 else 115920 if psr >= 132 else 92000 if psr >= 125 else 59800 if psr >= 108 else 0
    
    # Montos de excedentes
    m_exc_icb = exc_icb * 191
    m_exc_comp = exc_comp * 423
    
    base_core = p_icb + p_comp + p_psr + m_exc_icb + m_exc_comp

    # 2. Modificadores Claro Pay
    mod_si = 0.2 if si_pct>=80 else 0.1 if si_pct>=75 else 0.0 if si_pct>=70 else -0.25 if si_pct>=60 else -0.5
    mod_ca = 0.2 if ca_q>=44 else 0.1 if ca_q>=38 else 0.0 if ca_q>=31 else -0.25 if ca_q>=24 else -0.5
    impacto_cp = base_core * (mod_si + mod_ca)

    # 3. Ventas Fijas
    fijas_total = (portas*5000) + (lineas*2500) + (baf*8000) + (cp5k*2500)
    
    # 4. Ajuste de Productividad
    subtotal_pre_prod = base_core + impacto_cp + fijas_total
    v_fijas_q = portas + lineas + baf
    mod_p = 0.15 if v_fijas_q >= 10 else 0.0 if v_fijas_q >= 5 else -0.15
    impacto_prod = subtotal_pre_prod * mod_p

    # 5. Bonos Finales
    bonos = (9545 if l_icb else 0) + (9545 if l_comp else 0)
    total_final = max(0, subtotal_pre_prod + impacto_prod + bonos)

    return locals() # Captura todas las variables calculadas

# --- BOTÓN DE ACCIÓN ---
if st.button("🚀 GENERAR CÁLCULO"):
    if not vendedor:
        st.warning("⚠️ Por favor, ingresa el nombre del vendedor.")
    else:
        d = calcular_todo()
        
        st.divider()
        st.metric("TOTAL A LIQUIDAR", f"${d['total_final']:,.2f}")

        # --- GENERACIÓN DE EXCEL CON PANDAS ---
        output = io.BytesIO()
        
        # Hoja 1: Resumen Ejecutivo
        resumen = [
            ["CONCEPTO", "VALOR"],
            ["Vendedor", vendedor],
            ["Fecha Auditoría", datetime.now().strftime("%d/%m/%Y %H:%M")],
            ["---", "---"],
            ["BASE CORE (Escalas + Exc)", d['base_core']],
            ["IMPACTO CLARO PAY", d['impacto_cp']],
            ["TOTAL VENTAS FIJAS", d['fijas_total']],
            ["AJUSTE PRODUCTIVIDAD", d['impacto_prod']],
            ["BONOS RANKING", d['bonos']],
            ["TOTAL NETO FINAL", d['total_final']]
        ]
        
        # Hoja 2: Detalle de la Auditoría
        detalle = [
            ["Concepto", "Dato de Entrada", "Detalle de Cálculo", "Monto"],
            ["Incentivo ICB", f"{icb_pct}%", f"Escala alcanzada: ${d['p_icb']}", d['p_icb']],
            ["Excedentes ICB", f"Obj: {obj_icb_u}", f"{exc_icb} unidades x $191", d['m_exc_icb']],
            ["Incentivo Comp.", f"{comp_pct}%", f"Escala alcanzada: ${d['p_comp']}", d['p_comp']],
            ["Excedentes Comp.", f"Obj: {obj_comp_u}", f"{exc_comp} unidades x $423", d['m_exc_comp']],
            ["Bono PSR", f"{psr} Unidades", "Monto según escala PSR", d['p_psr']],
            ["Modificador CP", f"SI: {si_pct}% / Act: {ca_q}", f"{(d['mod_si']+d['mod_ca'])*100}% sobre Base Core", d['impacto_cp']],
            ["Ventas Fijas", f"{d['v_fijas_q']} ventas", "Comisiones Portas/Líneas/BAF", d['fijas_total']],
            ["Productividad", f"Rango: {d['v_fijas_q']}", f"{d['mod_p']*100}% sobre Subtotal", d['impacto_prod']]
        ]

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pd.DataFrame(resumen).to_excel(writer, sheet_name='Liquidacion_Resumen', index=False, header=False)
            pd.DataFrame(detalle).to_excel(writer, sheet_name='Detalle_Calculos', index=False)

        st.download_button(
            label="📥 Descargar Reporte Full",
            data=output.getvalue(),
            file_name=f"Auditoria_{vendedor}_{datetime.now().strftime('%d_%m')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        st.success("Auditoría generada con éxito. Los excedentes se calcularon automáticamente sobre el 110%.")
