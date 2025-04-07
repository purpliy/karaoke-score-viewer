import streamlit as st
import pandas as pd

# タイトル
st.title("🎤 DAM 採点履歴ビューア")

st.subheader("📁 採点結果（AI・DX-G）のCSVをアップロード")
uploaded_ai = st.file_uploader("精密採点AiのCSVファイル", type="csv")
uploaded_dxg = st.file_uploader("精密採点DX-GのCSVファイル", type="csv")

if uploaded_ai or uploaded_dxg:
    try:
        if uploaded_ai and uploaded_dxg:
            df_ai = pd.read_csv(uploaded_ai)
            df_dxg = pd.read_csv(uploaded_dxg)

            # 必要なら、点数を数値化＆日付をdatetimeに変換
            for df in [df_ai, df_dxg]:
                df["点数"] = pd.to_numeric(df["点数"], errors="coerce")
                df["日付"] = pd.to_datetime(df["日付"], errors="coerce")

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

        # 🔍 点数フィルタ別リスト表示
        st.subheader("🏅 90点以上の曲")
        high_scores = filtered_df[filtered_df["点数"] >= 90]
        st.dataframe(high_scores, use_container_width=True)

        st.subheader("🎯 89点台の曲（89.000以上 90.000未満）")
        score_89s = filtered_df[
            (filtered_df["点数"] >= 89) & (filtered_df["点数"] < 90)
        ]
        st.dataframe(score_89s, use_container_width=True)

        # 曲名一覧を取得（重複なし）
        曲リスト = sorted(filtered_df["曲名"].dropna().unique())

        # 曲名セレクトボックス
        選んだ曲 = st.selectbox("点数の推移を見たい曲を選んでください", 曲リスト)

        # 選択された曲のデータを抽出して日付順に並び替え
        曲データ = filtered_df[filtered_df["曲名"] == 選んだ曲].copy()
        曲データ["日付"] = pd.to_datetime(曲データ["日付"], errors="coerce")
        曲データ = 曲データ.dropna(subset=["日付", "点数"]).sort_values("日付")

        # グラフ表示（点数の折れ線）
        st.line_chart(data=曲データ, x="日付", y="点数", use_container_width=True)

    except Exception as e:
        st.error(f"CSVの読み込みに失敗しました: {e}")
else:
    st.info("上の欄からCSVファイルをアップロードしてください。")
