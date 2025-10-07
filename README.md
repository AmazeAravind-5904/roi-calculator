# 💡 Automated Invoicing ROI Calculator

This is a lightweight ROI calculator built with Streamlit that helps visualize the cost savings and payback period when switching from manual to automated invoicing.

## ✅ Features

-   **Live ROI Simulation:** Instantly see results as you adjust business metrics.
-   **Scenario Management:** Save and load different calculation scenarios.
-   **Email-Gated PDF Reports:** Download a summary report after providing an email address.
-   **Favorable-Bias Logic:** The calculation logic includes a bias factor to ensure results favor automation.

## ⚙️ Tech Stack

-   **Language:** Python
-   **Framework:** Streamlit
-   **Database:** SQLite (built-in)
-   **PDF Generation:** FPDF2

## 🚀 Setup and Running Locally

### Prerequisites

-   Python 3.8 or higher
-   pip

### Instructions

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd roi-calculator
    ```

2.  **Create the `requirements.txt` file** with the following content:
    ```
    streamlit
    fpdf2
    ```

3.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Streamlit app:**
    ```bash
    python -m streamlit run app.py
    ```
    Your browser will open with the running application.

## ☁️ Deployment

This application is ready for deployment on **Streamlit Community Cloud**. Simply push the repository (containing `app.py` and `requirements.txt`) to GitHub and connect it in your Streamlit dashboard.
