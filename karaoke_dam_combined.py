# ===== 精密採点Ai + DX-G 両方対応スクリプト（更新チェック付き） =====
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from webdriver_manager.chrome import ChromeDriverManager

import time
import csv
import os
import pandas as pd

DAMTOMO_ID = "yourID"
DAMTOMO_PASS = "yourPASS"
CSV_AI = "scores_ai.csv"
CSV_DXG = "scores_dxg.csv"

# Selenium起動
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome()

# ログイン処理
driver.get("https://www.clubdam.com/app/damtomo/auth/member/Login.do")
time.sleep(2)
driver.find_element(By.ID, "LoginID").send_keys(DAMTOMO_ID)
driver.find_element(By.ID, "LoginPassword").send_keys(DAMTOMO_PASS)
driver.find_element(By.ID, "LoginButton").click()
time.sleep(3)

# Cookie通知を閉じる
try:
    consent_button = driver.find_element(By.ID, "onetrust-accept-btn-handler")
    consent_button.click()
    print("✅ Cookie通知を閉じました")
    time.sleep(1)
except:
    pass

# タブクリック
def click_tab(tab_text):
    try:
        tab = driver.find_element(By.LINK_TEXT, tab_text)
        tab.click()
        time.sleep(2)
    except Exception as e:
        print(f"タブクリック失敗: {e}")

# データ保存（差分があるときのみ）
def save_if_updated(new_data, path):
    column_count = max(len(row) for row in new_data)
    if column_count == 5:
        columns = ["date", "name", "artist", "score", "key"]
    else:
        columns = ["date", "name", "artist", "score"]

    new_df = pd.DataFrame(new_data, columns=columns)
    new_df = new_df.apply(
        lambda col: col.str.strip() if col.dtype == object else col
    )
    new_df["score"] = pd.to_numeric(new_df["score"], errors="coerce")

    # ここで常に上書き保存
    new_df.to_csv(path, index=False, encoding="utf-8", float_format="%.3f")
    print(f"✅ データを {path} に上書き保存しました！")



# Ai履歴取得
def scrape_ai_history(container_id):
    data = []
    container = driver.find_element(By.ID, container_id)
    pager = container.find_element(By.CSS_SELECTOR, "div.ppage.clearfix > ul.ppp")
    page_buttons = [
        li for li in pager.find_elements(By.TAG_NAME, "li")
        if li.get_attribute("class").startswith("pagen") 
           and li.text.strip().isdigit()
    ]
    num_pages = len(page_buttons)

    for idx in range(num_pages):
        container = driver.find_element(By.ID, container_id)
        
        if container.value_of_css_property("display") != "block":
            break

        for table in container.find_elements(By.CSS_SELECTOR, "table.ai"):
            try:
                tds = table.find_elements(By.TAG_NAME, "td")
                if len(tds) < 3:
                    continue
                date_time = tds[0].text.strip()
                song_title = tds[1].find_element(By.TAG_NAME, "a").text.strip()
                raw_text = tds[1].text.strip().split("\n")
                artist = raw_text[1] if len(raw_text) > 1 else ""
                score = tds[2].text.strip().replace("点", "")
                data.append([date_time, song_title, artist, score])
            except:
                continue

        if idx + 1 < num_pages:
            # 再度ページャ要素を取得
            page_items = container.find_elements(By.CSS_SELECTOR, "ul.ppp > li[class^='pagen']")

            # 同意ボタンが出ていれば閉じる
            try:
                driver.find_element(By.ID, "onetrust-accept-btn-handler").click()
                time.sleep(1)
            except:
                pass

            # 次ページの <li> をクリック
            next_li = page_items[idx + 1]
            next_li.find_element(By.TAG_NAME, "a").click()
            time.sleep(2)
        else:
            break

    return data

# DX-G履歴取得
def scrape_dxg_history(container_id):
    data = []
    # 初回のコンテナ取得
    container = driver.find_element(By.ID, container_id)
    # ページャー（ul.ppp）を絞り込んで取得
    pager = container.find_element(By.CSS_SELECTOR, "div.ppage.clearfix > ul.ppp")
    # class="pagenXX" & 数字テキスト の <li> だけフィルタ
    page_buttons = [
        li for li in pager.find_elements(By.TAG_NAME, "li")
        if li.get_attribute("class").startswith("pagen") 
           and li.text.strip().isdigit()
    ]
    num_pages = len(page_buttons)

    for idx in range(num_pages):
        # 毎ループ、最新のコンテナを再取得
        container = driver.find_element(By.ID, container_id)

        # display チェック（必要なら）
        if container.value_of_css_property("display") != "block":
            break

        # ── DX-G テーブルスクレイピング ──
        for table in container.find_elements(By.CSS_SELECTOR, "table"):
            try:
                rows = table.find_elements(By.TAG_NAME, "tr")
                date      = table.find_element(By.CSS_SELECTOR, "td.field_01").text.strip()
                song      = rows[1].find_element(By.TAG_NAME, "a").text.strip()
                artist    = rows[2].find_elements(By.TAG_NAME, "td")[0].text.strip()
                score     = rows[3].find_elements(By.TAG_NAME, "td")[0].text.strip().replace("点", "")
                key       = rows[4].find_elements(By.TAG_NAME, "td")[0].text.strip()
                data.append([date, song, artist, score, key])
            except:
                continue

        # ── 次ページがあれば移動 ──
        if idx + 1 < num_pages:
            # 同意ダイアログがあれば閉じる
            try:
                driver.find_element(By.ID, "onetrust-accept-btn-handler").click()
                time.sleep(1)
            except:
                pass

            # ページャーを再取得＆フィルタし直し
            container = driver.find_element(By.ID, container_id)
            pager = container.find_element(By.CSS_SELECTOR, "div.ppage.clearfix > ul.ppp")
            page_buttons = [
                li for li in pager.find_elements(By.TAG_NAME, "li")
                if li.get_attribute("class").startswith("pagen") 
                   and li.text.strip().isdigit()
            ]

            # 次のページ番号をクリック
            page_buttons[idx + 1].find_element(By.TAG_NAME, "a").click()
            time.sleep(2)
        else:
            break

    return data

def upload_multiple_to_drive(file_paths, folder_name=None):
    # 認証処理（最初だけブラウザが開く）
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)

    # フォルダ作成または取得
    folder_id = None
    if folder_name:
        folder_list = drive.ListFile({'q': f"title='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()
        if folder_list:
            folder_id = folder_list[0]['id']
        else:
            folder_metadata = {'title': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
            folder = drive.CreateFile(folder_metadata)
            folder.Upload()
            folder_id = folder['id']

    for file_path in file_paths:
        # 同名ファイルがあれば削除
        query = f"title='{file_path}' and trashed=false"
        if folder_id:
            query += f" and '{folder_id}' in parents"
        file_list = drive.ListFile({'q': query}).GetList()
        for f in file_list:
            f.Delete()

        # アップロード
        file_metadata = {'title': file_path}
        if folder_id:
            file_metadata['parents'] = [{'id': folder_id}]

        upload_file = drive.CreateFile(file_metadata)
        upload_file.SetContentFile(file_path)
        upload_file.Upload()
        print(f"✅ Google Drive に {file_path} をアップロードしました！")

# 実行：Ai
click_tab("精密採点Ai")
ai_data = scrape_ai_history("DamHistoryMarkingAiListResult")
save_if_updated(ai_data, CSV_AI)

# 実行：DX-G
click_tab("精密採点DX-G")
dxg_data = scrape_dxg_history("DamHistoryMarkingDxGListResult")
save_if_updated(dxg_data, CSV_DXG)

#Upload to googledrive
upload_multiple_to_drive(["scores_ai.csv", "scores_dxg.csv"], folder_name="KaraokeScores")


driver.quit()
