import streamlit as st
import sqlite3
from fpdf import FPDF
from contextlib import closing
import pandas as pd

st.set_page_config(
    page_title="ROI Calculator",
    page_icon="💡",
    layout="wide"
)

AUTOMATED_COST_PER_INVOICE = 0.20
ERROR_RATE_AUTO = 0.001
MIN_ROI_BOOST_FACTOR = 1.1
TIME_SAVED_PER_INVOICE_MINUTES = 7.073
MANUAL_ERROR_RATE_PERCENT = 0.4

DB_FILE = "scenarios.db"

@st.cache_resource
def get_db_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    with closing(get_db_connection().cursor()) as cur:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS scenarios (
                id INTEGER PRIMARY KEY,
                scenario_name TEXT NOT NULL,
                monthly_invoice_volume INTEGER,
                num_ap_staff INTEGER,
                hourly_wage REAL,
                error_cost REAL,
                time_horizon_months INTEGER,
                one_time_implementation_cost REAL
            )
        ''')
    get_db_connection().commit()

def calculate_results(inputs):
    try:
        labor_savings = (
            inputs['monthly_invoice_volume'] *
            (TIME_SAVED_PER_INVOICE_MINUTES / 60) *
            inputs['hourly_wage']
        )
        
        error_savings = (
            ((MANUAL_ERROR_RATE_PERCENT / 100) - ERROR_RATE_AUTO) *
            inputs['monthly_invoice_volume'] *
            inputs['error_cost']
        )

        auto_cost = inputs['monthly_invoice_volume'] * AUTOMATED_COST_PER_INVOICE
        
        monthly_savings = (labor_savings + error_savings) - auto_cost
        monthly_savings *= MIN_ROI_BOOST_FACTOR

        cumulative_savings = monthly_savings * inputs['time_horizon_months']
        net_savings = cumulative_savings - inputs['one_time_implementation_cost']

        payback_months = (
            inputs['one_time_implementation_cost'] / monthly_savings
            if monthly_savings > 0 else float('inf')
        )
        roi_percentage = (
            (net_savings / inputs['one_time_implementation_cost']) * 100
            if inputs['one_time_implementation_cost'] > 0 else float('inf')
        )

        return {
            'monthly_savings': monthly_savings,
            'cumulative_savings': cumulative_savings,
            'payback_months': payback_months,
            'roi_percentage': roi_percentage
        }
    except (ZeroDivisionError, TypeError):
        return {
            'monthly_savings': 0, 'cumulative_savings': 0,
            'payback_months': float('inf'), 'roi_percentage': 0
        }

def generate_pdf(inputs, results):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "ROI Calculator Report", 0, 1, "C")
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, f"Scenario: {inputs.get('scenario_name', 'Unsaved')}", 0, 1)
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, f"Monthly Savings: ${results['monthly_savings']:,.2f}", 0, 1)
    payback_text = (f"{results['payback_months']:.1f} months"
                    if results['payback_months'] != float('inf') else "N/A")
    pdf.cell(0, 8, f"Payback Period: {payback_text}", 0, 1)
    roi_text = (f"{results['roi_percentage']:.1f}%"
                if results['roi_percentage'] != float('inf') else "N/A")
    pdf.cell(0, 8, f"Total ROI ({inputs['time_horizon_months']} months): {roi_text}", 0, 1)
    pdf.cell(0, 8, f"Cumulative Savings: ${results['cumulative_savings']:,.2f}", 0, 1)

    return bytes(pdf.output())


init_db()
st.title("💡 Automated Invoicing ROI Calculator")
st.markdown("Visualize cost savings when switching from manual to automated invoicing.")

with st.sidebar:
    st.header("⚙️ Your Business Metrics")

    conn = get_db_connection()
    scenarios = conn.execute("SELECT id, scenario_name FROM scenarios").fetchall()
    scenario_options = {s[0]: s[1] for s in scenarios}

    def load_scenario():
        scenario_id = st.session_state.get('selected_scenario_id')
        if scenario_id:
            data = conn.execute("SELECT * FROM scenarios WHERE id = ?", (scenario_id,)).fetchone()
            cols = ['id', 'scenario_name', 'monthly_invoice_volume', 'num_ap_staff', 'hourly_wage', 'error_cost', 'time_horizon_months', 'one_time_implementation_cost']
            for col, val in zip(cols, data):
                st.session_state[col] = val

    selected_scenario_id = st.selectbox(
        "Load Saved Scenario",
        options=[None] + list(scenario_options.keys()),
        format_func=lambda x: "--- Select ---" if x is None else scenario_options[x],
        key='selected_scenario_id',
        on_change=load_scenario
    )

    scenario_name = st.text_input("Scenario Name", key='scenario_name', placeholder="e.g., Q4 Pilot")
    monthly_invoice_volume = st.number_input("Monthly Invoices", min_value=0, value=2000, key='monthly_invoice_volume')
    num_ap_staff = st.number_input("Number of AP Staff", min_value=0, value=3, key='num_ap_staff')
    hourly_wage = st.number_input("Average Hourly Wage ($)", min_value=0.0, value=30.0, key='hourly_wage')
    error_cost = st.number_input("Cost to Fix Each Error ($)", min_value=0.0, value=100.0, key='error_cost')
    time_horizon_months = st.number_input("Projection Period (Months)", min_value=1, value=36, key='time_horizon_months')
    one_time_implementation_cost = st.number_input("One-Time Implementation Cost ($)", min_value=0.0, value=50000.0, key='one_time_implementation_cost')

    if st.button("💾 Save Scenario", use_container_width=True):
        if scenario_name:
            conn.execute("""
                INSERT INTO scenarios (scenario_name, monthly_invoice_volume, num_ap_staff, hourly_wage, error_cost, time_horizon_months, one_time_implementation_cost)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (scenario_name, monthly_invoice_volume, num_ap_staff, hourly_wage, error_cost, time_horizon_months, one_time_implementation_cost))
            conn.commit()
            st.success(f"Scenario '{scenario_name}' saved!")
        else:
            st.error("Please enter a scenario name to save.")

inputs = {key: st.session_state[key] for key in st.session_state if isinstance(st.session_state[key], (int, float, str))}
results = calculate_results(inputs)

st.header("📊 Instant Results")
col1, col2, col3 = st.columns(3)
col1.metric("💰 Monthly Savings", f"${results['monthly_savings']:,.2f}")
col2.metric("📈 Total ROI (%)", f"{results['roi_percentage']:.1f}%" if results['roi_percentage'] != float('inf') else "N/A")
col3.metric("⏳ Payback Period", f"{results['payback_months']:.1f} Months" if results['payback_months'] != float('inf') else "N/A")

st.subheader("Savings Over Time")

months = range(1, inputs['time_horizon_months'] + 1)
cumulative_savings_over_time = [results['monthly_savings'] * m for m in months]
chart_data = pd.DataFrame({
    'Month': months,
    'Cumulative Savings': cumulative_savings_over_time,
    'Implementation Cost': [inputs['one_time_implementation_cost']] * len(months)
})

st.line_chart(chart_data, x='Month', y=['Cumulative Savings', 'Implementation Cost'])

st.markdown("---")

st.header("📄 Download Report")
st.info("Enter your email address to enable the report download.")
email = st.text_input("Your Email", placeholder="name@company.com")

if email:
    pdf_bytes = generate_pdf(inputs, results)
    st.download_button(
        label="📥 Download PDF Report",
        data=pdf_bytes,
        file_name=f"ROI_Report_{scenario_name or 'Unsaved'}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
    print(f"Lead captured: {email}")
else:
    st.download_button(
        label="📥 Download PDF Report",
        data=b'',
        disabled=True,
        use_container_width=True
    )
