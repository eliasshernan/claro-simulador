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
st.write(f"Versión 2026.8 (Auto-% Unidades) - {datetime.now().strftime('%d/%m/%Y')}")

vendedor = st.text_input("Nombre del Vendedor", placeholder="Ej: Elias")

# --- ENTRADA DE DATOS ---
with st.expander("📊 INDICADORES BÁSICOS", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("ICB")
        obj_icb_u = st.number_input("Objetivo ICB (Unidades)", min_value=1, value=100)
        u_real_icb = st.number_input("Unidades Reales ICB", min_value=0, value=0)
        
        # El programa calcula automáticamente el % de alcance
        icb_pct = (u_real_icb / obj_icb_u) * 100 if obj_icb_u > 0 else 0.0
        st.caption(f"Alcance calculado: {icb_pct:.1f}%")
        
        # Cálculo: Excedentes si supera el 110%
        exc_icb = max(0, int(((icb_pct - 110) / 100) * obj_icb_u)) if icb_pct > 110 else 0
        st.caption(f"Excedentes detectados: {exc_icb}")

    with c2:
        st.subheader("Completos")
        obj_comp_u = st.number_input("Objetivo Comp. (Unidades)", min_value=1, value=100)
        u_real_comp = st.number_input("Unidades Reales Completos", min_value=0, value=0)
        
        # El programa calcula automáticamente el % de alcance
        comp_pct = (u_real_comp / obj_comp_u) * 100 if obj_comp_u > 0 else 0.0
        st.caption(f"Alcance calculado: {comp_pct:.1f}%")
        
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
    portas = c5.number_input("Portabilidades", min_value=0, value=0)
    lineas = c6.number_input("Líneas Nuevas", min_value=0, value=0)
    baf = c5.number_input("BAF Internet", min_value=0, value=0)
    cp5k = c6.number_input("CP 1° Compra >$5500", min_value=0, value=0)

with st.expander("🏆 BONOS RANKING"):
    l_icb = st.checkbox("Líder ICB ($12409)")
    l_comp = st.checkbox("Líder Completos ($12409)")

# --- LÓGICA DE AUDITORÍA ---
def calcular_todo():
    # 1. Escalas Core
    def escala(pct):
        if pct >= 110: return 127499
        elif pct >= 105: return 108752
        elif pct >= 100: return 90000
        elif pct >= 90: return 58500
        elif pct >= 80: return 36000
        return 0

    p_icb = escala(icb_pct)
    p_comp = escala(comp_pct)
    
    # Pago PSR
    p_psr = 183600 if psr >= 144 else 151200 if psr >= 132 else 120000 if psr >= 125 else 78000 if psr >= 108 else 0
    
    # Excedentes
    m_exc_icb = exc_icb * 248
    m_exc_comp = exc_comp * 550
    
    base_core = p_icb + p_comp + p_psr + m_exc_icb + m_exc_comp

    # 2. Modificadores Claro Pay
    mod_si = 0.2 if si_pct>=80 else 0.1 if si_pct>=75 else 0.0 if si_pct>=70 else -0.25 if si_pct>=60 else -0.5
    mod_ca = 0.2 if ca_q>=44 else 0.1 if ca_q>=38 else 0.0 if ca_q>=31 else -0.25 if ca_q>=24 else -0.5
    impacto_cp = base_core * (mod_si + mod_ca)

    # 3. Ventas Fijas (Lógica de precios según volumen de referidos)
    v_fijas_q = portas + lineas + baf
    
    if v_fijas_q >= 10:
        val_porta = 6500
        val_linea = 4000
        val_baf = 10000
        mod_p_label = "Premio Premium (>=10 ventas)"
    elif v_fijas_q >= 3:
        val_porta = 5000
        val_linea = 2500
        val_baf = 8000
        mod_p_label = "Rango Neutro (3-9 ventas)"
    else:
        val_porta = 5000
        val_linea = 2500
        val_baf = 8000
        mod_p_label = "Penalización -15% (<3 ventas)"
        
    tot_portas = portas * val_porta
    tot_lineas = lineas * val_linea
    tot_baf = baf * val_baf
    tot_cp5k = cp5k * 3500
    
    fijas_total = tot_portas + tot_lineas + tot_baf + tot_cp5k
    
    # 4. Ajuste por baja productividad
    subtotal_pre_prod = base_core + impacto_cp + fijas_total
    
    if v_fijas_q < 3:
        impacto_prod = subtotal_pre_prod * -0.15
    else:
        impacto_prod = 0.0

    # 5. Bonos Finales
    bonos = (12409 if l_icb else 0) + (12409 if l_comp else 0)
    total_final = max(0, subtotal_pre_prod + impacto_prod + bonos)

    return locals()

# --- BOTÓN DE ACCIÓN ---
if st.button("🚀 GENERAR CÁLCULO"):
    if not vendedor:
        st.warning("⚠️ Por favor, ingresa el nombre del vendedor.")
    else:
        d = calcular_todo()
        
        st.divider()
        st.metric("TOTAL A LIQUIDAR", f"${d['total_final']:,.2f}")

        # --- SECCIÓN: DESGLOSE VISUAL EN LA PANTALLA ---
        st.subheader("🔍 DESGLOSE DETALLADO DEL CÁLCULO")
        
        with st.expander("📋 Ver detalle línea por línea", expanded=True):
            st.markdown(f"**👤 Vendedor:** {vendedor}")
            st.markdown("---")
            
            # Detalle de Core
            st.markdown("**📊 Indicadores Core & PSR:**")
            st.write(f"* **Escala ICB ({u_real_icb} u. de {obj_icb_u} u. = {icb_pct:.1f}%):** ${d['p_icb']:,}")
            if exc_icb > 0:
                st.write(f"    * *Excedentes ICB:* {exc_icb} u. × $248 = ${d['m_exc_icb']:,}")
            st.write(f"* **Escala Completos ({u_real_comp} u. de {obj_comp_u} u. = {comp_pct:.1f}%):** ${d['p_comp']:,}")
            if exc_comp > 0:
                st.write(f"    * *Excedentes Completos:* {exc_comp} u. × $550 = ${d['m_exc_comp']:,}")
            st.write(f"* **Escala PSR ({psr} u.):** ${d['p_psr']:,}")
            st.write(f"👉 **Subtotal Base Core:** ${d['base_core']:,}")
            
            st.markdown("---")
            
            # Detalle Claro Pay
            st.markdown("**📱 Claro Pay Modificadores:**")
            total_mod_cp = (d['mod_si'] + d['mod_ca']) * 100
            st.write(f"* *Sell In ({si_pct}%):* {d['mod_si']*100}% | *Activaciones ({ca_q} u.):* {d['mod_ca']*100}%")
            st.write(f"👉 **Impacto Claro Pay ({total_mod_cp}% sobre Core):** ${d['impacto_cp']:,}")
            
            st.markdown("---")
            
            # Detalle Referidos
            st.markdown(f"**🏠 Referidos y Ventas Fijas ({d['mod_p_label']}):**")
            st.write(f"* **Portabilidades:** {portas} u. × ${d['val_porta']:,} = **${d['tot_portas']:,}**")
            st.write(f"* **Líneas Nuevas:** {lineas} u. × ${d['val_linea']:,} = **${d['tot_lineas']:,}**")
            st.write(f"* **BAF Internet:** {baf} u. × ${d['val_baf']:,} = **${d['tot_baf']:,}**")
            st.write(f"* **Claro Pay >$5500:** {cp5k} u. × $3,500 = **${d['tot_cp5k']:,}**")
            st.write(f"👉 **Total Referidos:** ${d['fijas_total']:,}")
            
            if d['impacto_prod'] < 0:
                st.markdown(f"⚠️ **Descuento por baja productividad (<3 ventas):** ${d['impacto_prod']:,}")
                
            st.markdown("---")
            
            # Detalle Bonos
            if d['bonos'] > 0:
                st.markdown("**🏆 Bonos de Ranking:**")
                if l_icb: st.write("* Líder ICB: $12,409")
                if l_comp: st.write("* Líder Completos: $12,409")
                st.write(f"👉 **Total Bonos:** ${d['bonos']:,}")
                st.markdown("---")
                
            st.markdown(f"### **💰 NETO TOTAL ACUMULADO: ${d['total_final']:,.2f}**")

        st.divider()

        # --- GENERACIÓN DE EXCEL CON PANDAS ---
        output = io.BytesIO()
        
        resumen = [
            ["CONCEPTO", "VALOR"],
            ["Vendedor", vendedor],
            ["Fecha Auditoría", datetime.now().strftime("%d/%m/%Y %H:%M")],
            ["---", "---"],
            ["BASE CORE (Escalas + Exc)", d['base_core']],
            ["IMPACTO CLARO PAY", d['impacto_cp']],
            ["TOTAL REFERIDOS (CON PRODUCTIVIDAD)", d['fijas_total']],
            ["DESCUENTO PRODUCTIVIDAD (<3 vtas)", d['impacto_prod']],
            ["BONOS RANKING LÍDER", d['bonos']],
            ["TOTAL NETO FINAL", d['total_final']]
        ]
        
        detalle = [
            ["Concepto", "Dato de Entrada", "Detalle de Cálculo", "Monto"],
            ["Incentivo ICB", f"{u_real_icb} de {obj_icb_u} ({icb_pct:.1f}%)", f"Escala alcanzada: ${d['p_icb']}", d['p_icb']],
            ["Excedentes ICB", f"Obj: {obj_icb_u}", f"{exc_icb} unidades x $248", d['m_exc_icb']],
            ["Incentivo Comp.", f"{u_real_comp} de {obj_comp_u} ({comp_pct:.1f}%)", f"Escala alcanzada: ${d['p_comp']}", d['p_comp']],
            ["Excedentes Comp.", f"Obj: {obj_comp_u}", f"{exc_comp} unidades x $550", d['m_exc_comp']],
            ["Bono PSR", f"{psr} Unidades", "Monto según escala PSR", d['p_psr']],
            ["Modificador CP", f"SI: {si_pct}% / Act: {ca_q}", f"{(d['mod_si']+d['mod_ca'])*100}% sobre Base Core", d['impacto_cp']],
            ["Referidos Totales", f"{d['v_fijas_q']} ventas", f"Estado: {d['mod_p_label']}", d['fijas_total']],
            ["Ajuste Castigo", f"< 3 ventas", "Aplica -15% sobre subtotal si corresponde", d['impacto_prod']]
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
