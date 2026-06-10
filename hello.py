import streamlit as st

st.title("Hello Streamlit!")

st.write("Welcome to your first Streamlit app!")

name = st.text_input("이름을 입력하세요:")
if name:
    st.write(f"안녕하세요, {name}님!")

st.write("---")
st.subheader("간단한 계산기")
num1 = st.number_input("첫 번째 숫자:", value=0)
num2 = st.number_input("두 번째 숫자:", value=0)

if st.button("더하기"):
    st.success(f"{num1} + {num2} = {num1 + num2}")
