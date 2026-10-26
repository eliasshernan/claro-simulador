import base64
import io
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from calculos import BONO_LIDER, VALOR_EXC_COMP, VALOR_EXC_ICB, calcular_comision, excedentes, porcentaje

st.set_page_config(page_title="Comisiones Distri-Lisu", page_icon="🔴")

NOMBRE_IMAGEN = "comisiones.png.png"
NOMBRE_LOGO = "logo_empresa.png"
TZ = ZoneInfo("America/Argentina/Buenos_Aires")

st.markdown("""
    <style>
    .stButton>button { background-color: #ee122c; color: white; font-weight: bold;
        width: 100%; height: 3em; border-radius: 8px; }
    [data-testid="stMetricValue"] { color: #1e1e1e !important; }
    [data-testid="stMetricLabel"] { color: #555555 !important; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px;
        border: 2px solid #ee122c; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
    [data-testid="stExpander"] { border: 1px solid #ddd; border-radius: 10px;
        background-color: rgba(238, 18, 44, 0.03); }
    .header-container { display: flex; align-items: center; gap: 15px; margin-bottom: 20px; }
    .header-container img { height: 52px; width: auto; object-fit: contain;
        background-color: #ffffff; padding: 4px; border-radius: 6px;
        filter: grayscale(0) contrast(1.4) saturate(2); mix-blend-mode: color-dodge; }
    .header-container h1 { margin: 0 !important; padding: 0 !important; }
    </style>
    """, unsafe_allow_html=True)


def pesos(x):
    return f"${x:,.2f}"


@st.cache_data
def logo_base64(ruta):
    with open(ruta, "rb") as f:
        return base64.b64encode(f.read()).decode()


def generar_excel(res):
    d, e = res["d"], res["entradas"]
    resumen = [
        ["CONCEPTO", "VALOR"],
        ["Vendedor", res["vendedor"]],
        ["Fecha Auditoría", res["fecha"].strftime("%d/%m/%Y %H:%M")],
        ["BASE CORE (Escalas + Exc)", d["base_core"]],
        ["IMPACTO CLARO PAY", d["impacto_cp"]],
        ["TOTAL REFERIDOS", d["fijas_total"]],
        ["DESCUENTO PRODUCTIVIDAD (<3 vtas)", d["impacto_prod"]],
        ["BONOS RANKING LÍDER", d["bonos"]],
        ["TOTAL NETO FINAL", d["total_final"]],
    ]
    detalle = [
        ["Concepto", "Dato de Entrada", "Detalle de Cálculo", "Monto"],
        ["Incentivo ICB", f"{e['u_icb']} de {e['obj_icb']} ({d['icb_pct']:.1f}%)", f"Escala alcanzada: ${d['p_icb']:,}", d["p_icb"]],
        ["Excedentes ICB", f"Obj: {e['obj_icb']}", f"{d['exc_icb']} unidades x ${VALOR_EXC_ICB}", d["m_exc_icb"]],
        ["Incentivo Comp.", f"{e['u_comp']} de {e['obj_comp']} ({d['comp_pct']:.1f}%)", f"Escala alcanzada: ${d['p_comp']:,}", d["p_comp"]],
        ["Excedentes Comp.", f"Obj: {e['obj_comp']}", f"{d['exc_comp']} unidades x ${VALOR_EXC_COMP}", d["m_exc_comp"]],
        ["Bono PSR", f"{e['psr']} Unidades", "Monto según escala PSR", d["p_psr"]],
        ["Modificador CP", f"SI: {e['si_pct']}% / Act: {e['ca_q']}", f"{(d['mod_si'] + d['mod_ca']) * 100:.0f}% sobre Base Core", d["impacto_cp"]],
        ["Referidos Totales", f"{d['v_fijas_q']} ventas", f"Estado: {d['mod_p_label']}", d["fijas_total"]],
        ["Ajuste Castigo", "< 3 ventas", "Aplica -15% sobre subtotal si corresponde", d["impacto_prod"]],
    ]
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame(resumen).to_excel(writer, sheet_name="Liquidacion_Resumen", index=False, header=False)
        pd.DataFrame(detalle).to_excel(writer, sheet_name="Detalle_Calculos", index=False)
        for ws in writer.book.worksheets:
            for col in ws.columns:
                largo = max(len(str(c.value)) for c in col if c.value is not None)
                ws.column_dimensions[col[0].column_letter].width = max(largo + 4, 12)
            for fila in ws.iter_rows():
                for c in fila:
                    if isinstance(c.value, (int, float)):
                        c.number_format = "$#,##0.00"
    return output.getvalue()


def mostrar_resultado(res):
    d, e, vendedor = res["d"], res["entradas"], res["vendedor"]
    st.divider()
    st.metric("TOTAL A LIQUIDAR", pesos(d["total_final"]))
    st.subheader("🔍 DESGLOSE DETALLADO DEL CÁLCULO")

    with st.expander("📋 Ver detalle línea por línea", expanded=True):
        st.markdown(f"**👤 Vendedor:** {vendedor}")
        st.markdown("---")
        st.markdown("**📊 Indicadores Core & PSR:**")
        st.write(f"* **Escala ICB ({e['u_icb']} u. de {e['obj_icb']} u. = {d['icb_pct']:.1f}%):** {pesos(d['p_icb'])}")
        if d["exc_icb"] > 0:
            st.write(f"    * *Excedentes ICB:* {d['exc_icb']} u. × ${VALOR_EXC_ICB} = {pesos(d['m_exc_icb'])}")
        st.write(f"* **Escala Completos ({e['u_comp']} u. de {e['obj_comp']} u. = {d['comp_pct']:.1f}%):** {pesos(d['p_comp'])}")
        if d["exc_comp"] > 0:
            st.write(f"    * *Excedentes Completos:* {d['exc_comp']} u. × ${VALOR_EXC_COMP} = {pesos(d['m_exc_comp'])}")
        st.write(f"* **Escala PSR ({e['psr']} u.):** {pesos(d['p_psr'])}")
        st.write(f"👉 **Subtotal Base Core:** {pesos(d['base_core'])}")
        st.markdown("---")

        st.markdown("**📱 Claro Pay Modificadores:**")
        total_mod = (d["mod_si"] + d["mod_ca"]) * 100
        st.write(f"* *Sell In ({e['si_pct']}%):* {d['mod_si'] * 100:.0f}% | *Activaciones ({e['ca_q']} u.):* {d['mod_ca'] * 100:.0f}%")
        st.write(f"👉 **Impacto Claro Pay ({total_mod:.0f}% sobre Core):** {pesos(d['impacto_cp'])}")
        st.markdown("---")

        st.markdown(f"**🏠 Referidos y Ventas Fijas ({d['mod_p_label']}):**")
        st.write(f"* **Portabilidades:** {e['portas']} u. × ${d['val_porta']:,} = **{pesos(d['tot_portas'])}**")
        st.write(f"* **Líneas Nuevas:** {e['lineas']} u. × ${d['val_linea']:,} = **{pesos(d['tot_lineas'])}**")
        st.write(f"* **BAF Internet:** {e['baf']} u. × ${d['val_baf']:,} = **{pesos(d['tot_baf'])}**")
        st.write(f"👉 **Total Referidos:** {pesos(d['fijas_total'])}")
        if d["impacto_prod"] < 0:
            st.markdown(f"⚠️ **Descuento por baja productividad (<3 ventas):** {pesos(d['impacto_prod'])}")
        st.markdown("---")

        if d["bonos"] > 0:
            st.markdown("**🏆 Bonos de Ranking:**")
            if e["lider_icb"]:
                st.write(f"* Líder PSR / ICB: ${BONO_LIDER:,}")
            if e["lider_comp"]:
                st.write(f"* Líder Completos: ${BONO_LIDER:,}")
            st.write(f"👉 **Total Bonos:** {pesos(d['bonos'])}")
            st.markdown("---")
        st.markdown(f"### **💰 NETO TOTAL ACUMULADO: {pesos(d['total_final'])}**")

    st.divider()
    seguro = re.sub(r"[^\w-]", "_", vendedor)
    st.download_button(
        label="📥 Descargar Reporte Full",
        data=generar_excel(res),
        file_name=f"Auditoria_{seguro}_{res['fecha'].strftime('%d_%m')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )


# --- TÍTULO ---
if os.path.exists(NOMBRE_LOGO):
    st.markdown(f"""
        <div class="header-container">
            <img src="data:image/png;base64,{logo_base64(NOMBRE_LOGO)}">
            <h1>Comisiones Distri-Lisu</h1>
        </div>
        """, unsafe_allow_html=True)
else:
    st.title("🔴 Comisiones Distri-Lisu")

vendedor = st.text_input("Nombre del Vendedor", placeholder="Ej: Elias")

with st.expander("📋 ESQUEMA COMISIONAL"):
    st.write("Consulte las escalas vigentes y valores oficiales:")
    if os.path.exists(NOMBRE_IMAGEN):
        st.image(NOMBRE_IMAGEN, use_container_width=True)
        with open(NOMBRE_IMAGEN, "rb") as f:
            st.download_button("📥 Descargar Imagen", data=f, file_name="Esquema_Comisiones.png",
                               mime="image/png", use_container_width=True)
    else:
        st.error("⚠️ No se encontró la imagen del esquema comisional.")

# --- ENTRADA DE DATOS ---
with st.expander("📊 INDICADORES BÁSICOS", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("ICB")
        obj_icb = st.number_input("Objetivo ICB (Unidades)", min_value=1, value=100)
        u_icb = st.number_input("Alcance logrado ICB", min_value=0, value=0)
        pct = porcentaje(u_icb, obj_icb)
        st.caption(f"Alcance calculado: {pct:.1f}%")
        st.caption(f"Excedentes detectados: {excedentes(pct, obj_icb)}")
    with c2:
        st.subheader("Completos")
        obj_comp = st.number_input("Objetivo Comp. (Unidades)", min_value=1, value=100)
        u_comp = st.number_input("Alcance logrado Completos", min_value=0, value=0)
        pct = porcentaje(u_comp, obj_comp)
        st.caption(f"Alcance calculado: {pct:.1f}%")
        st.caption(f"Excedentes detectados: {excedentes(pct, obj_comp)}")
    st.divider()
    psr = st.number_input("Cantidad PSR/ICB Total", min_value=0, value=0)

with st.expander("📱 CLARO PAY"):
    c3, c4 = st.columns(2)
    si_pct = c3.number_input("% Sell In CP", min_value=0.0, max_value=100.0, value=75.0)
    ca_q = c4.number_input("Activaciones CP (Cant. Real)", min_value=0, value=0)

with st.expander("🏠 REFERIDOS"):
    r1, r2 = st.columns(2)
    with r1:
        portas = st.number_input("Portabilidades", min_value=0, value=0)
        st.caption("*( <10: $5,000 | >=10: $6,500 )*")
        st.write("")
        baf = st.number_input("BAF Internet", min_value=0, value=0)
        st.caption("*( <10: $8,000 | >=10: $10,000 )*")
    with r2:
        lineas = st.number_input("Líneas Nuevas", min_value=0, value=0)
        st.caption("*( <10: $2,500 | >=10: $4,000 )*")
        st.write("")
        st.markdown("<br>", unsafe_allow_html=True)
        st.info(f"🔢 **Total Referidos: {portas + lineas + baf}**")

with st.expander("🏆 BONOS RANKING"):
    lider_icb = st.checkbox(f"Líder PSR / ICB (${BONO_LIDER:,})")
    lider_comp = st.checkbox(f"Líder Completos (${BONO_LIDER:,})")

# --- ACCIÓN ---
if st.button("🚀 GENERAR CÁLCULO"):
    if not vendedor.strip():
        st.warning("⚠️ Por favor, ingresa el nombre del vendedor.")
    else:
        entradas = dict(u_icb=u_icb, obj_icb=obj_icb, u_comp=u_comp, obj_comp=obj_comp, psr=psr,
                        si_pct=si_pct, ca_q=ca_q, portas=portas, lineas=lineas, baf=baf,
                        lider_icb=lider_icb, lider_comp=lider_comp)
        st.session_state["resultado"] = {
            "vendedor": vendedor.strip(), "fecha": datetime.now(TZ),
            "entradas": entradas, "d": calcular_comision(**entradas),
        }

# El resultado queda en session_state: sobrevive al hacer clic en "Descargar"
if "resultado" in st.session_state:
    mostrar_resultado(st.session_state["resultado"])
