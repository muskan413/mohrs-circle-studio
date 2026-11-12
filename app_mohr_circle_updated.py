import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Mohr's Circle Studio Pro",
    page_icon="⭕",
    layout="wide",
)

# ----------------------------- Styling -----------------------------
st.markdown("""
<style>
.stApp { background-color: #FFFFFF; color: #172033; }
h1, h2, h3, h4 { color: #123B66 !important; }
p, li, label, .stMarkdown { color: #374151 !important; }
[data-testid="stSidebar"] { background-color: #F1F5F9; }
[data-testid="stMetric"] { background-color: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 12px; padding: 16px; }
[data-testid="stMetricValue"] { color: #123B66 !important; }
</style>
""", unsafe_allow_html=True)

STRAIN_FACTORS = {
    "Microstrain (με)": 1e-6,
    "Millistrain (mε)": 1e-3,
    "Percentage (%)": 1e-2,
    "Strain (mm/mm)": 1.0,
}

STRESS_FACTORS = {
    "Pa": 1.0,
    "kPa": 1e3,
    "MPa": 1e6,
    "GPa": 1e9,
}

def clean_num(val, decimals=4):
    if abs(val) < 1e-11:
        return 0.0
    return round(val, decimals)

# ----------------------------- Sidebar Inputs -----------------------------
with st.sidebar:
    st.markdown("## ⚙️ Input Panel")
    mode = st.radio(
        "Analysis Mode",
        ["Direct Strain Input", "Stress to Strain & Mohr Circle", "Direct Stress Mohr Circle"],
        index=0,
    )

    if mode == "Stress to Strain & Mohr Circle":
        st.markdown("### Material Properties")
        stress_unit = st.selectbox("Stress unit", list(STRESS_FACTORS), index=2)

        # Approximate textbook values; exact values depend on grade/alloy and syllabus.
        MATERIAL_E_MPA = {
            "Steel": 200000.0,
            "Aluminium": 70000.0,
            "Copper": 120000.0,
            "Brass": 100000.0,
            "Cast iron": 100000.0,
            "Concrete": 30000.0,
            "Timber (wood)": 10000.0,
            "Rubber (approx.)": 10.0,
        }
        material = st.selectbox(
            "Choose material",
            ["Steel", "Aluminium", "Copper", "Brass", "Cast iron",
             "Concrete", "Timber (wood)", "Rubber (approx.)", "Custom / Enter E manually"],
            index=0,
        )
        if material == "Custom / Enter E manually":
            E_value = st.number_input("Young's modulus E", value=200000.0, min_value=0.000001, format="%.6g")
            E_unit = st.selectbox("E unit", ["MPa", "GPa", "Pa"], index=0)
        else:
            E_value = MATERIAL_E_MPA[material]
            E_unit = "MPa"
            st.info(f"Young's modulus for {material}: **{E_value:g} MPa** ({E_value / 1000:g} GPa). This is an approximate reference value.")
        nu = st.number_input("Poisson's ratio ν", min_value=-0.99, max_value=0.499, value=0.30, format="%.3f")

        st.markdown("### Stress Inputs")
        sx = st.number_input("σx", value=100.0, format="%.6g")
        sy = st.number_input("σy", value=0.0, format="%.6g")
        txy = st.number_input("τxy", value=30.0, format="%.6g")

    elif mode == "Direct Strain Input":
        input_unit = st.selectbox("Input strain unit", list(STRAIN_FACTORS), index=0)
        eps_x_raw = st.number_input("εx", value=500.0, format="%.8g")
        eps_y_raw = st.number_input("εy", value=-200.0, format="%.8g")
        gamma_raw = st.number_input("γxy (Engineering shear)", value=300.0, format="%.8g")

    else:
        stress_unit_direct = st.selectbox("Stress Unit", ["MPa", "kPa", "Pa", "GPa"], index=0, key="dir_s_unit")
        sig_x_in = st.number_input("σx", value=80.0, key="dir_sx")
        sig_y_in = st.number_input("σy", value=20.0, key="dir_sy")
        tau_xy_in = st.number_input("τxy", value=30.0, key="dir_txy")

    selected_angle = st.slider("Explore Plane Angle θ (°)", -90.0, 90.0, 0.0, 0.5)
    submit_btn = st.button("🚀 Submit & Calculate", type="primary")

st.markdown("# ⭕ Mohr's Circle Studio Pro")
st.markdown("Comprehensive 2D Strain and Stress Transformation & Principal Plane Analysis")

if submit_btn:
    st.session_state["submitted"] = True

if st.session_state.get("submitted", False):
    if mode != "Direct Stress Mohr Circle":
        if mode == "Stress to Strain & Mohr Circle":
            E_pa = E_value * STRESS_FACTORS[E_unit]
            sx_pa = sx * STRESS_FACTORS[stress_unit]
            sy_pa = sy * STRESS_FACTORS[stress_unit]
            txy_pa = txy * STRESS_FACTORS[stress_unit]
            G_pa = E_pa / (2 * (1 + nu))
            eps_x = (sx_pa - nu * sy_pa) / E_pa
            eps_y = (sy_pa - nu * sx_pa) / E_pa
            gamma_xy = txy_pa / G_pa
            input_unit = "Strain (mm/mm)"
        else:
            eps_x = eps_x_raw * STRAIN_FACTORS[input_unit]
            eps_y = eps_y_raw * STRAIN_FACTORS[input_unit]
            gamma_xy = gamma_raw * STRAIN_FACTORS[input_unit]

        center = (eps_x + eps_y) / 2
        radius = math.sqrt(((eps_x - eps_y) / 2) ** 2 + (gamma_xy / 2) ** 2)
        eps_1 = center + radius
        eps_2 = center - radius
        gamma_max = 2 * radius
        theta_p1 = 0.5 * math.degrees(math.atan2(gamma_xy, eps_x - eps_y))
        theta_p2 = theta_p1 + 90.0

        t = math.radians(selected_angle)
        diff = (eps_x - eps_y) / 2
        sel_eps = center + diff * math.cos(2 * t) + (gamma_xy / 2) * math.sin(2 * t)
        sel_gamma_half = -diff * math.sin(2 * t) + (gamma_xy / 2) * math.cos(2 * t)

        def display_strain(v):
            val = clean_num(v, 6)
            if input_unit == "Strain (mm/mm)":
                return f"{val:.4f} mm/mm"
            converted = val / STRAIN_FACTORS[input_unit]
            return f"{clean_num(converted, 2)} {input_unit.split(' ')[1].strip('()')}"

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Principal Strain ε₁", display_strain(eps_1), f"θp₁ = {clean_num(theta_p1, 2)}°")
        with c2:
            st.metric("Principal Strain ε₂", display_strain(eps_2), f"θp₂ = {clean_num(theta_p2, 2)}°")
        with c3:
            st.metric("Max Shear γmax", display_strain(gamma_max), "Engineering Shear")
        with c4:
            st.metric("Circle Radius R", display_strain(radius))

        tab1, tab2, tab3 = st.tabs(["⭕ Strain Mohr Circle", "📊 Principal Planes", "📘 Formulas"])
        with tab1:
            a = np.linspace(0, 2 * np.pi, 600)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=center + radius * np.cos(a), y=radius * np.sin(a), mode="lines", name="Mohr Circle", line=dict(width=3, color="#123B66")))
            fig.add_trace(go.Scatter(x=[eps_x, eps_y], y=[gamma_xy / 2, -gamma_xy / 2], mode="markers+text", text=["A (εx, γxy/2)", "B (εy, −γxy/2)"], textposition=["top center", "bottom center"], marker=dict(size=12, color="#E67E22")))
            fig.add_trace(go.Scatter(x=[eps_1, eps_2], y=[0, 0], mode="markers+text", text=["ε₁", "ε₂"], textposition="top center", marker=dict(size=13, symbol="star", color="#2563EB")))
            fig.add_trace(go.Scatter(x=[sel_eps], y=[sel_gamma_half], mode="markers+text", text=[f"θ={selected_angle:.1f}°"], textposition="top center", marker=dict(size=14, symbol="diamond", color="#DC2626")))

            extent = max(1e-8, radius * 1.35, abs(center) * 0.25)
            # Reverse vertical axis so negative shear-strain coordinates appear upward.
            fig.update_layout(title="Interactive Mohr's Strain Circle", xaxis_title="Normal Strain, ε", yaxis_title="Engineering Shear Coordinate, γ/2", template="plotly_white", height=550, xaxis=dict(range=[center - extent, center + extent], scaleanchor="y", scaleratio=1), yaxis=dict(range=[extent, -extent]))
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.metric("θp₁", f"{clean_num(theta_p1, 3)}°")
                st.write(f"εn = **{display_strain(eps_1)}**, γn = **0**")
            with col_p2:
                st.metric("θp₂", f"{clean_num(theta_p2, 3)}°")
                st.write(f"εn = **{display_strain(eps_2)}**, γn = **0**")

        with tab3:
            st.latex(r"\varepsilon_n = \frac{\varepsilon_x + \varepsilon_y}{2} + \frac{\varepsilon_x - \varepsilon_y}{2}\cos 2\theta + \frac{\gamma_{xy}}{2}\sin 2\theta")
            st.latex(r"\varepsilon_{1,2} = \frac{\varepsilon_x + \varepsilon_y}{2} \pm \sqrt{\left(\frac{\varepsilon_x - \varepsilon_y}{2}\right)^2 + \left(\frac{\gamma_{xy}}{2}\right)^2}")

    else:
        s_factor = STRESS_FACTORS[stress_unit_direct]
        sx_val = sig_x_in * s_factor
        sy_val = sig_y_in * s_factor
        txy_val = tau_xy_in * s_factor

        scenter = (sx_val + sy_val) / 2.0
        sradius = math.sqrt(((sx_val - sy_val) / 2.0) ** 2 + txy_val ** 2)
        sig1 = scenter + sradius
        sig2 = scenter - sradius
        tau_max = sradius
        tp_stress = 0.5 * math.degrees(math.atan2(2.0 * txy_val, sx_val - sy_val))
        tp_stress2 = tp_stress + 90.0

        disp_fac = 1.0 / s_factor

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Major Principal Stress σ₁", f"{clean_num(sig1 * disp_fac, 3)} {stress_unit_direct}", f"θp₁ = {clean_num(tp_stress, 2)}°")
        with m2:
            st.metric("Minor Principal Stress σ₂", f"{clean_num(sig2 * disp_fac, 3)} {stress_unit_direct}", f"θp₂ = {clean_num(tp_stress2, 2)}°")
        with m3:
            st.metric("Max In-Plane Shear τmax", f"{clean_num(tau_max * disp_fac, 3)} {stress_unit_direct}")

        # Mohr's Stress Circle Graph
        angles = np.linspace(0, 2 * np.pi, 361)
        stress_circle_x = (scenter + sradius * np.cos(angles)) * disp_fac
        stress_circle_y = (sradius * np.sin(angles)) * disp_fac

        s_fig = go.Figure()
        s_fig.add_trace(go.Scatter(x=stress_circle_x, y=stress_circle_y, mode="lines", name="Mohr's Stress Circle", line=dict(color="#007F86", width=3)))
        s_fig.add_trace(go.Scatter(x=[sx_val * disp_fac, sy_val * disp_fac], y=[txy_val * disp_fac, -txy_val * disp_fac], mode="markers+text", text=["X (σx, τxy)", "Y (σy, −τxy)"], textposition="top center", name="Stress Points", marker=dict(color="#E67E22", size=10)))
        s_fig.add_trace(go.Scatter(x=[sig1 * disp_fac, sig2 * disp_fac], y=[0, 0], mode="markers+text", text=["σ₁", "σ₂"], textposition="bottom center", name="Principal Stresses", marker=dict(color="#2563EB", size=10)))
        s_fig.add_trace(go.Scatter(x=[scenter * disp_fac], y=[0], mode="markers+text", text=["C"], textposition="top center", name="Centre", marker=dict(color="#172033", size=9)))

        s_extent = max(1e-8, sradius * disp_fac * 1.35, abs(scenter * disp_fac) * 0.25)
        s_fig.update_layout(
            title="Interactive Mohr's Stress Circle",
            template="plotly_white",
            xaxis_title=f"Normal Stress σ ({stress_unit_direct})",
            yaxis_title=f"Shear Stress τ ({stress_unit_direct})",
            height=550,
            xaxis=dict(range=[scenter * disp_fac - s_extent, scenter * disp_fac + s_extent], scaleanchor="y", scaleratio=1),
            yaxis=dict(range=[-s_extent, s_extent])
        )
        st.plotly_chart(s_fig, use_container_width=True)
else:
    st.info("👈 Please enter your parameters in the sidebar and click **'🚀 Submit & Calculate'** to view results and Mohr's circle.")