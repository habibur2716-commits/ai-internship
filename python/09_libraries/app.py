import streamlit as st

st.title("My First App")
st.write("Hello, this is my Streamlit app!")

name = st.text_input("Enter your name")
if name:
    st.write(f"Hello, {name}!")