import streamlit as st
import pandas as pd

# タイトル
st.title("🎤 DAM 採点履歴ビューア")

# ファイルアップロード
uploaded_file = st.file_uploader("CSVファイルをアップロード (scores_ai.csv / scores_dxg.csv)", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # 表示オプション
        st.subheader("🔎 フィルター")
        artist_filter = st.text_input("アーティスト名で検索")
        song_filter = st.text_input("曲名で検索")

        filtered_df = df.copy()
        if artist_filter:
            filtered_df = filtered_df[filtered_df["アーティスト"].str.contains(artist_filter, case=False, na=False)]
        if song_filter:
            filtered_df = filtered_df[filtered_df["曲名"].str.contains(song_filter, case=False, na=False)]

        st.subheader("📄 採点履歴")
        st.dataframe(filtered_df, use_container_width=True)

        # 点数グラフ
        st.subheader("📊 点数の推移グラフ")
        if "点数" in filtered_df.columns:
            try:
                filtered_df["点数"] = pd.to_numeric(filtered_df["点数"], errors="coerce")
                score_plot = filtered_df.sort_values("点数", ascending=False).head(20)
                st.bar_chart(score_plot.set_index("曲名")["点数"])
            except:
                st.warning("点数列の数値変換に失敗しました")
    except Exception as e:
        st.error(f"CSVの読み込みに失敗しました: {e}")
else:
    st.info("上の欄からCSVファイルをアップロードしてください。")
