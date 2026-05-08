#!/usr/bin/env python3
# Regenerate apps/Puff1/Resources/Strings*.resx from the tables below. Run if UI strings change.
import os
import xml.sax.saxutils as x

OUT = os.path.join(os.path.dirname(__file__), "..", "apps", "puff1", "Resources")
HEADER = """<?xml version="1.0" encoding="utf-8"?>
<root>
  <resheader name="resmimetype">
    <value>text/microsoft-resx</value>
  </resheader>
  <resheader name="version">
    <value>2.0</value>
  </resheader>
  <resheader name="reader">
    <value>System.Resources.ResXResourceReader, System.Resources.Extensions, Version=4.0.0.0, Culture=neutral, PublicKeyToken=cc7b13ffcd2ddd51</value>
  </resheader>
  <resheader name="writer">
    <value>System.Resources.ResXResourceWriter, System.Resources.Extensions, Version=4.0.0.0, Culture=neutral, PublicKeyToken=cc7b13ffcd2ddd51</value>
  </resheader>
"""
KEYS = [
    "Help_Usage",
    "Help_Concat",
    "Help_ReadStdin",
    "Option_Verbose",
    "Option_Quiet",
    "Option_Help",
    "Option_Version",
    "ReportBugs",
    "Version_Title",
    "Copyright",
    "Version_License",
    "Version_FreeSoftware",
    "Version_OpposesAI",
    "Version_RejectsLicensing",
    "Version_NoWarranty",
]

# Default (English) — template for invariant culture
S_EN: dict[str, str] = {
    "Help_Usage": "Usage: puff1 [OPTION]... [FILE]...\n",
    "Help_Concat": "Concatenate FILE(s) to standard output. With no FILE, or when FILE is -,\n",
    "Help_ReadStdin": "read standard input.\n\n",
    "Option_Verbose": "repeat for more verbose loggings\n",
    "Option_Quiet": "show less logging messages\n",
    "Option_Help": "display this help and exit\n",
    "Option_Version": "output version information and exit\n\n",
    "ReportBugs": "Report bugs to: <{0}>",
    "Version_Title": "puff1 dev",
    "Copyright": "Copyright (C) {0} {1}",
    "Version_License": "License AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>",
    "Version_FreeSoftware": "This is free software: you are free to change and redistribute it.",
    "Version_OpposesAI": "This project opposes AI exploitation and AI hegemony.",
    "Version_RejectsLicensing": "This project rejects mindless MIT-style licensing and politically naive BSD-style licensing.",
    "Version_NoWarranty": "There is NO WARRANTY, to the extent permitted by law.",
}

# Migrated from previous po/ catalogs (splits and wording merged where old gettext was fuzzy)
LANGS: dict[str, dict[str, str]] = {
    "de": {
        "Help_Usage": "Verwendung: puff1 [OPTION]... [FILE]...\n",
        "Help_Concat": "Verkettet FILE(s) zur Standardausgabe. Ohne FILE oder wenn FILE - ist,\n",
        "Help_ReadStdin": "wird von der Standardeingabe gelesen.\n\n",
        "Option_Verbose": "wiederholen fuer ausfuehrlichere Protokollmeldungen\n",
        "Option_Quiet": "weniger Protokollmeldungen anzeigen\n",
        "Option_Help": "diese Hilfe anzeigen und beenden\n",
        "Option_Version": "Versionsinformationen anzeigen und beenden\n",
        "ReportBugs": "Fehler bitte melden: <{0}>",
        "Version_Title": "puff1 dev",
        "Copyright": "Copyright (C) {0} {1}",
        "Version_License": "Lizenz AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>\n",
        "Version_FreeSoftware": "Dies ist freie Software: Sie duerfen sie aendern und weitergeben.\n",
        "Version_OpposesAI": "Dieses Projekt lehnt KI-Ausbeutung und KI-Hegemonie ab.\n",
        "Version_RejectsLicensing": "Dieses Projekt lehnt gedankenlose MIT-artige Lizenzen und politisch naive BSD-artige Lizenzen ab.\n",
        "Version_NoWarranty": "Es gibt KEINE GARANTIE, soweit gesetzlich zulaessig.\n",
    },
    "fr": {
        "Help_Usage": "Utilisation : puff1 [OPTION]... [FILE]...\n",
        "Help_Concat": "Concatene les FILE(s) vers la sortie standard. Sans FILE, ou si FILE vaut -,\n",
        "Help_ReadStdin": "lit l'entree standard.\n\n",
        "Option_Verbose": "repeter pour obtenir des journaux plus verbeux\n",
        "Option_Quiet": "afficher moins de messages de journal\n",
        "Option_Help": "afficher cette aide et quitter\n",
        "Option_Version": "afficher les informations de version et quitter\n",
        "ReportBugs": "Rapporter les bogues a : <{0}>",
        "Version_Title": "puff1 dev",
        "Copyright": "Copyright (C) {0} {1}",
        "Version_License": "Licence AGPL-3.0-or-later : <https://www.gnu.org/licenses/agpl-3.0.html>\n",
        "Version_FreeSoftware": "Ce logiciel est libre : vous pouvez le modifier et le redistribuer.\n",
        "Version_OpposesAI": "Ce projet s'oppose a l'exploitation par l'IA et a l'hegemonie de l'IA.\n",
        "Version_RejectsLicensing": "Ce projet rejette les licences de type MIT sans reflexion et les licences de type BSD politiquement naives.\n",
        "Version_NoWarranty": "AUCUNE GARANTIE n'est fournie, dans les limites permises par la loi.\n",
    },
    "it": {
        "Help_Usage": "Uso: puff1 [OPTION]... [FILE]...\n",
        "Help_Concat": "Concatena i FILE sull'output standard. Senza FILE, o quando FILE e -,\n",
        "Help_ReadStdin": "legge dallo standard input.\n\n",
        "Option_Verbose": "ripeti per ottenere log piu verbosi\n",
        "Option_Quiet": "mostra meno messaggi di log\n",
        "Option_Help": "mostra questo aiuto ed esce\n",
        "Option_Version": "mostra le informazioni di versione ed esce\n",
        "ReportBugs": "Segnala bug a: <{0}>",
        "Version_Title": "puff1 dev",
        "Copyright": "Copyright (C) {0} {1}",
        "Version_License": "Licenza AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>\n",
        "Version_FreeSoftware": "Questo e software libero: puoi modificarlo e ridistribuirlo.\n",
        "Version_OpposesAI": "Questo progetto si oppone allo sfruttamento dell'IA e all'egemonia dell'IA.\n",
        "Version_RejectsLicensing": "Questo progetto rifiuta licenze in stile MIT acritiche e licenze in stile BSD politicamente ingenue.\n",
        "Version_NoWarranty": "NON c'e ALCUNA GARANZIA, nei limiti consentiti dalla legge.\n",
    },
    "ja": {
        "Help_Usage": "使い方: puff1 [OPTION]... [FILE]...\n",
        "Help_Concat": "FILE を連結して標準出力へ出力します。FILE がない場合、または FILE が - の場合は、\n",
        "Help_ReadStdin": "標準入力を読み取ります。\n\n",
        "Option_Verbose": "さらに詳細なログを出すには繰り返して指定\n",
        "Option_Quiet": "ログメッセージを少なく表示\n",
        "Option_Help": "このヘルプを表示して終了\n",
        "Option_Version": "バージョン情報を表示して終了\n",
        "ReportBugs": "不具合の報告: <{0}>",
        "Version_Title": "puff1 dev",
        "Copyright": "Copyright (C) {0} {1}",
        "Version_License": "ライセンス AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>\n",
        "Version_FreeSoftware": "これはフリーソフトウェアです。自由に改変および再配布できます。\n",
        "Version_OpposesAI": "このプロジェクトは AI 搾取と AI 覇権に反対します。\n",
        "Version_RejectsLicensing": "このプロジェクトは無批判な MIT 型ライセンスと政治的に愚かな BSD 型ライセンスに反対します。\n",
        "Version_NoWarranty": "法の許す範囲で一切の保証はありません。\n",
    },
    "ko": {
        "Help_Usage": "사용법: puff1 [OPTION]... [FILE]...\n",
        "Help_Concat": "FILE 내용을 이어서 표준 출력으로 보냅니다. FILE이 없거나 FILE이 - 이면,\n",
        "Help_ReadStdin": "표준 입력을 읽습니다.\n\n",
        "Option_Verbose": "더 자세한 로그를 보려면 반복 지정\n",
        "Option_Quiet": "로그 메시지를 더 적게 표시\n",
        "Option_Help": "도움말을 표시하고 종료\n",
        "Option_Version": "버전 정보를 표시하고 종료\n",
        "ReportBugs": "오류 제보: <{0}>",
        "Version_Title": "puff1 dev",
        "Copyright": "Copyright (C) {0} {1}",
        "Version_License": "라이선스 AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>\n",
        "Version_FreeSoftware": "이것은 자유 소프트웨어이며 자유롭게 수정 및 재배포할 수 있습니다.\n",
        "Version_OpposesAI": "이 프로젝트는 AI 착취와 AI 패권에 반대합니다.\n",
        "Version_RejectsLicensing": "이 프로젝트는 무비판적 MIT식 라이선스와 정치적으로 어리석은 BSD식 라이선스를 거부합니다.\n",
        "Version_NoWarranty": "법이 허용하는 한 어떠한 보증도 없습니다.\n",
    },
    "zh-Hans": {
        "Help_Usage": "用法：puff1 [选项]... [文件]...\n",
        "Help_Concat": "将文件内容连接并输出到标准输出。若未提供文件，或文件为 -，\n",
        "Help_ReadStdin": "则从标准输入读取。\n\n",
        "Option_Verbose": "重复使用以输出更多详细日志\n",
        "Option_Quiet": "显示更少的日志消息\n",
        "Option_Help": "显示此帮助并退出\n",
        "Option_Version": "输出版本信息并退出\n",
        "ReportBugs": "问题报告: <{0}>",
        "Version_Title": "puff1 dev",
        "Copyright": "Copyright (C) {0} {1}",
        "Version_License": "许可证 AGPL-3.0-or-later：<https://www.gnu.org/licenses/agpl-3.0.html>\n",
        "Version_FreeSoftware": "这是自由软件：你可以自由修改并重新分发。\n",
        "Version_OpposesAI": "本项目反对 AI 剥削与 AI 霸权。\n",
        "Version_RejectsLicensing": "本项目反对无脑 MIT 式许可证和政治愚蠢 BSD 式许可证。\n",
        "Version_NoWarranty": "在法律允许范围内，不提供任何担保。\n",
    },
    "zh-Hant": {
        "Help_Usage": "用法：puff1 [選項]... [檔案]...\n",
        "Help_Concat": "將檔案內容串接後輸出到標準輸出。若未提供檔案，或檔案為 -，\n",
        "Help_ReadStdin": "則從標準輸入讀取。\n\n",
        "Option_Verbose": "重複使用以顯示更多詳細日誌\n",
        "Option_Quiet": "顯示較少的日誌訊息\n",
        "Option_Help": "顯示此說明並結束\n",
        "Option_Version": "輸出版本資訊並結束\n",
        "ReportBugs": "問題回報: <{0}>",
        "Version_Title": "puff1 dev",
        "Copyright": "Copyright (C) {0} {1}",
        "Version_License": "授權 AGPL-3.0-or-later：<https://www.gnu.org/licenses/agpl-3.0.html>\n",
        "Version_FreeSoftware": "這是自由軟體：你可以自由修改並再散布。\n",
        "Version_OpposesAI": "本專案反對 AI 剝削與 AI 霸權。\n",
        "Version_RejectsLicensing": "本專案反對無腦 MIT 式授權與政治愚蠢 BSD 式授權。\n",
        "Version_NoWarranty": "在法律允許範圍內，不提供任何保證。\n",
    },
    "th": {
        "Help_Usage": "การใช้งาน: puff1 [OPTION]... [FILE]...\n",
        "Help_Concat": "ต่อเนื้อหาของ FILE ไปยังเอาต์พุตมาตรฐาน หากไม่มี FILE หรือ FILE เป็น -,\n",
        "Help_ReadStdin": "จะอ่านจากอินพุตมาตรฐาน\n\n",
        "Option_Verbose": "ใส่ซ้ำเพื่อแสดงบันทึกแบบละเอียดมากขึ้น\n",
        "Option_Quiet": "แสดงข้อความบันทึกให้น้อยลง\n",
        "Option_Help": "แสดงความช่วยเหลือนี้และออก\n",
        "Option_Version": "แสดงข้อมูลเวอร์ชันและออก\n",
        "ReportBugs": "รายงานข้อบกพร่อง: <{0}>",
        "Version_Title": "puff1 dev",
        "Copyright": "Copyright (C) {0} {1}",
        "Version_License": "สัญญาอนุญาต AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>\n",
        "Version_FreeSoftware": "นี่คือซอฟต์แวร์เสรี คุณมีสิทธิ์แก้ไขและแจกจ่ายต่อได้\n",
        "Version_OpposesAI": "โครงการนี้คัดค้านการเอาเปรียบด้วย AI และอำนาจนำของ AI\n",
        "Version_RejectsLicensing": "โครงการนี้ปฏิเสธใบอนุญาตแบบ MIT ที่ไร้วิจารณญาณ และใบอนุญาตแบบ BSD ที่โง่เขลาทางการเมือง\n",
        "Version_NoWarranty": "ไม่มีการรับประกันใด ๆ ตามขอบเขตที่กฎหมายอนุญาต\n",
    },
    "vi": {
        "Help_Usage": "Cách dùng: puff1 [OPTION]... [FILE]...\n",
        "Help_Concat": "Nối các FILE và ghi ra đầu ra chuẩn. Khi không có FILE hoặc FILE là -,\n",
        "Help_ReadStdin": "đọc từ đầu vào chuẩn.\n\n",
        "Option_Verbose": "lap lai de hien thi nhieu nhat ky chi tiet hon\n",
        "Option_Quiet": "hien thi it thong diep nhat ky hon\n",
        "Option_Help": "hiển thị trợ giúp này và thoát\n",
        "Option_Version": "in thông tin phiên bản và thoát\n",
        "ReportBugs": "Báo lỗi: <{0}>",
        "Version_Title": "puff1 dev",
        "Copyright": "Copyright (C) {0} {1}",
        "Version_License": "Giấy phép AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>\n",
        "Version_FreeSoftware": "Đây là phần mềm tự do: bạn có thể sửa đổi và phân phối lại.\n",
        "Version_OpposesAI": "Dự án này phản đối bóc lột AI và bá quyền AI.\n",
        "Version_RejectsLicensing": "Dự án này bác bỏ kiểu cấp phép MIT máy móc và kiểu cấp phép BSD ngây ngô về chính trị.\n",
        "Version_NoWarranty": "KHÔNG CÓ BẤT KỲ BẢO HÀNH nào trong phạm vi luật cho phép.\n",
    },
    "eo": {
        "Help_Usage": "Uzo: puff1 [OPTION]... [FILE]...\n",
        "Help_Concat": "Kunigas FILE(j)n al norma eligo. Sen FILE, au kiam FILE estas -,\n",
        "Help_ReadStdin": "legi de norma enigo.\n\n",
        "Option_Verbose": "ripetu por pli detalaj protokoloj\n",
        "Option_Quiet": "montri malpli da protokolaj mesagxoj\n",
        "Option_Help": "montri cxi tiun helpon kaj eliri\n",
        "Option_Version": "montri versiajn informojn kaj eliri\n",
        "ReportBugs": "Raporti erarojn: <{0}>",
        "Version_Title": "puff1 dev",
        "Copyright": "Copyright (C) {0} {1}",
        "Version_License": "Permesilo AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>\n",
        "Version_FreeSoftware": "Tio estas libera programaro: vi rajtas sxangxi kaj redistribui gxin.\n",
        "Version_OpposesAI": "Tiu projekto kontrauxas AI-ekspluaton kaj AI-hegemonion.\n",
        "Version_RejectsLicensing": "Tiu projekto malakceptas senpripensan MIT-stilan permesilon kaj politike naivan BSD-stilan permesilon.\n",
        "Version_NoWarranty": "NE ESTAS GARANTIO, lau la amplekso permesita de la lexo.\n",
    },
}


def esc(s: str) -> str:
    return x.escape(s, entities={'"':"&quot;","'":"&apos;"})


def write(path: str, d: dict[str, str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    parts = [HEADER]
    for k in KEYS:
        v = d[k]
        parts.append(
            f'  <data name="{k}" xml:space="preserve">\n    <value>{esc(v)}</value>\n  </data>\n'
        )
    parts.append("</root>\n")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(parts))


def main() -> None:
    write(os.path.join(OUT, "Strings.resx"), S_EN)
    for tag, d in LANGS.items():
        write(os.path.join(OUT, f"Strings.{tag}.resx"), d)
    print("Wrote", 1 + len(LANGS), "resx under", OUT)


if __name__ == "__main__":
    main()
