import streamlit as st
import requests

st.set_page_config(page_title="Currency Converter", page_icon="🤑")
st.title("Currency Converter 💰")

amt = st.number_input("Enter the amount to convert:", min_value=0.0, value=1.0, step=0.01)

from_curr = st.text_input("From currency (USD, INR, EUR, GBP, JPY):", value="INR").upper().strip()
to_curr = st.text_input("To currency (USD, INR, EUR, GBP, JPY):", value="USD").upper().strip()

if st.button("Convert ⚡"):
    url = f"https://open.er-api.com/v6/latest/{from_curr}"
    data = requests.get(url).json()

    if data.get("result") == "success":
        rate = data["rates"].get(to_curr)
        if rate:
            converted = amt * rate
            st.success(f"{amt} {from_curr} = {converted:.2f} {to_curr}")
        else:
            st.error("Invalid TO currency code.")
    else:
        st.error("Invalid FROM currency code.")
