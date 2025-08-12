import streamlit as st
import pandas as pd
import requests
import io

st.title("Slotoloty")

# link do bezpośredniego pobierania z Dropbox
dropbox_url = "https://www.dropbox.com/scl/fi/p9bkjet6zo4o10x6ysar6/sloty.xlsx?rlkey=n0z3ox0ous5u1u744bguan7ad&st=h5jbvqzc&dl=1"

try:
    response = requests.get(dropbox_url)
    response.raise_for_status()
    df1 = pd.read_excel(io.BytesIO(response.content), engine="openpyxl")
    df1 = df1.drop(df1.columns[3:9], axis=1)
    df1 = df1[["Numer rejsu", "Dzień Tyg", "Airport", "Dopuszczalne anulacje"]]
except Exception as e:
    st.error(f"Błąd podczas pobierania pliku sloty.xlsx z Dropbox: {e}")
    st.stop()


# 📤 Wgranie pliku testowego przez użytkownika
uploaded_file = st.file_uploader("Wgraj plik testowe.xlsx", type=["xlsx"])

if uploaded_file:
    try:
        df5 = pd.read_excel(uploaded_file, engine="openpyxl")
        df5 = df5.drop(columns=["NO", "Al", "OS", "STD (UTC)", "STA (UTC)", "Own", "A/C", "Cfg", "Seats",
                                "Srv", "Class", "Blkt", "Cntxt", "Reason", "Act", "Change", "Time", "By"])
        df5['Date'] = pd.to_datetime(df5['Date']).dt.date

        df5.columns = ["Numer rejsu", "Date", "Dzień Tyg", "Org", "+", "Dest"]
        df5 = df5[["Numer rejsu", "Date", "Dzień Tyg", "+", "Org", "Dest"]]

        dni_map = {'MON': 1, 'TUE': 2, 'WED': 3, 'THU': 4, 'FRI': 5, 'SAT': 6, 'SUN': 7}
        df5['Dzień Tyg'] = df5['Dzień Tyg'].str.strip().map(dni_map)
        df5 = df5.dropna()

        def przesun_dzien(dzien):
            try:
                dzien = int(dzien)
                return 1 if dzien == 7 else dzien + 1
            except:
                return dzien

        nowe_wiersze = []
        for _, row in df5.iterrows():
            numer = row['Numer rejsu']
            dzien = row['Dzień Tyg']
            plus = row['+']
            org = row['Org']
            dest = row['Dest']
            date = row['Date']

            nowe_wiersze.append({'Numer rejsu': numer, 'Dzień Tyg': dzien, '+': plus, 'Port': org, 'Date': date})
            nowe_wiersze.append({'Numer rejsu': numer, 'Dzień Tyg': przesun_dzien(dzien) if plus == 1 else dzien,
                                 '+': plus, 'Port': dest, 'Date': date})

        df6 = pd.DataFrame(nowe_wiersze)
        df6 = df6.rename(columns={'Port': 'Airport'}).drop(columns="+")

        df6_uzupelniony = df6.merge(df1, on=['Airport', 'Numer rejsu', 'Dzień Tyg'], how='left')

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df6_uzupelniony.to_excel(writer, index=False)
        output.seek(0)

        st.success("Dane zostały przetworzone pomyślnie.")
        st.download_button(label="Pobierz wynikowy plik Excel",
                           data=output,
                           file_name="propozycje_anulacji.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        st.error(f"Wystąpił błąd podczas przetwarzania pliku: {e}")
