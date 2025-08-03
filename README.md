# Anaysis of Calcium imaging data

This Streamlit app allows you to upload calcium imaging excel data, identify neuronal responders to chemical stimuli (Cap, m-CPBG, KCl), calculate ΔF/F₀, and visualize overlap between response groups.

## Features
- Upload Excel files with size and intensity data (odd columns being size and even columns being intensity per neuron)
- Set frame windows for Capsaicin, KCl, and m-CPBG
- Automatically calculate:
  - Baseline vs. stimulus response
  - ΔF/F₀ ratios
  - Responder overlap (Venn diagram)
- Download results as CSV

## To Run Locally

```bash
git clone https://github.com/yourusername/calcium-imaging-app.git
cd calcium-imaging-app
pip install -r requirements.txt
streamlit run app.py
