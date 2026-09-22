# SPDX-License-Identifier: AGPL-3.0-or-later
"""Hand-translated zfr rule README body templates (no machine translation)."""

LOCALES = ("zh_CN", "zh_TW", "ja", "de", "fr", "ko", "it", "ar")

# Ize one-liner: English is: Ize rule `{code}` (`{id}`).
IZE_LINE = {
    "zh_CN": "Ize 规则 `{code}`（`{id}`）。",
    "zh_TW": "Ize 規則 `{code}`（`{id}`）。",
    "ja": "Ize ルール `{code}`（`{id}`）。",
    "de": "Ize-Regel `{code}` (`{id}`).",
    "fr": "Règle Ize `{code}` (`{id}`).",
    "ko": "Ize 규칙 `{code}`(`{id}`).",
    "it": "Regola Ize `{code}` (`{id}`).",
    "ar": "قاعدة Ize `{code}` (`{id}`).",
}

# Placeholder-only body (keep {title} {detail} literally):
PLACEHOLDER_BODY = {
    "zh_CN": "### {title}\n\n{detail}\n",
    "zh_TW": "### {title}\n\n{detail}\n",
    "ja": "### {title}\n\n{detail}\n",
    "de": "### {title}\n\n{detail}\n",
    "fr": "### {title}\n\n{detail}\n",
    "ko": "### {title}\n\n{detail}\n",
    "it": "### {title}\n\n{detail}\n",
    "ar": "### {title}\n\n{detail}\n",
}

# Shared fragments for the generic packaging-layout rule card.
_RULE_CARD_OPEN = {
    "zh_CN": (
        "### {title}\n"
        "\n"
        "规则 {id}（`{code}`）属于 zephyr packaging/\n"
        "布局约定。默认严重级别提示：{sev}。\n"
    ),
    "zh_TW": (
        "### {title}\n"
        "\n"
        "規則 {id}（`{code}`）屬於 zephyr packaging/\n"
        "版面配置約定。預設嚴重程度提示：{sev}。\n"
    ),
    "ja": (
        "### {title}\n"
        "\n"
        "ルール {id}（`{code}`）は zephyr packaging/\n"
        "レイアウト契約の一部です。既定の重大度ヒント: {sev}。\n"
    ),
    "de": (
        "### {title}\n"
        "\n"
        "Regel {id} (`{code}`) gehört zum zephyr packaging/\n"
        "Layout-Vertrag. Standard-Schweregrad-Hinweis: {sev}.\n"
    ),
    "fr": (
        "### {title}\n"
        "\n"
        "La règle {id} (`{code}`) fait partie du contrat de\n"
        "disposition packaging/ de zephyr. Indice de sévérité par défaut : {sev}.\n"
    ),
    "ko": (
        "### {title}\n"
        "\n"
        "규칙 {id}(`{code}`)는 zephyr packaging/\n"
        "레이아웃 계약의 일부입니다. 기본 심각도 힌트: {sev}.\n"
    ),
    "it": (
        "### {title}\n"
        "\n"
        "La regola {id} (`{code}`) fa parte del contratto di\n"
        "layout packaging/ di zephyr. Suggerimento di gravità predefinito: {sev}.\n"
    ),
    "ar": (
        "### {title}\n"
        "\n"
        "القاعدة {id} (`{code}`) جزء من عقد تخطيط\n"
        "packaging/ في zephyr. تلميح الشدة الافتراضي: {sev}.\n"
    ),
}

_RULE_CARD_LINT = {
    "zh_CN": (
        "### lint 做什么\n"
        "\n"
        "{detail}\n"
        "在 `zfr lint` 中由 `{code}` 实现。尽可能附带\n"
        "具体修复说明。可用 `-w` / `-e` / `--strict` 重映射严重级别。\n"
    ),
    "zh_TW": (
        "### lint 做什麼\n"
        "\n"
        "{detail}\n"
        "在 `zfr lint` 中由 `{code}` 實作。盡可能附帶\n"
        "具體修復說明。可用 `-w` / `-e` / `--strict` 重對應嚴重程度。\n"
    ),
    "ja": (
        "### lint の動作\n"
        "\n"
        "{detail}\n"
        "`zfr lint` 内の `{code}` で実装されています。可能なら\n"
        "具体的な修正文を付けます。重大度は `-w` / `-e` / `--strict` で再割当てできます。\n"
    ),
    "de": (
        "### Was lint tut\n"
        "\n"
        "{detail}\n"
        "Implementiert unter `{code}` in `zfr lint`. Befunde tragen\n"
        "wenn möglich einen konkreten Fix-Text. Schweregrad umbiegen mit\n"
        "`-w` / `-e` / `--strict`.\n"
    ),
    "fr": (
        "### Ce que fait lint\n"
        "\n"
        "{detail}\n"
        "Implémenté sous `{code}` dans `zfr lint`. Les constats portent\n"
        "quand possible une chaîne de correction concrète. Remappez la sévérité avec\n"
        "`-w` / `-e` / `--strict`.\n"
    ),
    "ko": (
        "### lint가 하는 일\n"
        "\n"
        "{detail}\n"
        "`zfr lint`의 `{code}` 아래에서 구현됩니다. 가능하면\n"
        "구체적인 수정 문자열을 붙입니다. 심각도는 `-w` / `-e` / `--strict`로 다시 매핑합니다.\n"
    ),
    "it": (
        "### Cosa fa lint\n"
        "\n"
        "{detail}\n"
        "Implementato sotto `{code}` in `zfr lint`. I rilievi portano\n"
        "quando possibile una stringa di correzione concreta. Riassegna la gravità con\n"
        "`-w` / `-e` / `--strict`.\n"
    ),
    "ar": (
        "### ماذا يفعل lint\n"
        "\n"
        "{detail}\n"
        "مُنفَّذ تحت `{code}` في `zfr lint`. تحمل النتائج\n"
        "عند الإمكان نص إصلاح ملموس. أعد تعيين الشدة بـ\n"
        "`-w` / `-e` / `--strict`.\n"
    ),
}

_RULE_CARD_CHANGE = {
    "zh_CN": (
        "### 改动树时\n"
        "\n"
        "修复可能触及 packaging、meson.build、源码或脚手架\n"
        "副本。上传前请 diff Maintainer、Depends、%files 与 *.in 脚本。\n"
    ),
    "zh_TW": (
        "### 變更樹時\n"
        "\n"
        "修復可能觸及 packaging、meson.build、原始碼或鷹架\n"
        "副本。上傳前請 diff Maintainer、Depends、%files 與 *.in 腳本。\n"
    ),
    "ja": (
        "### ツリーを変えるとき\n"
        "\n"
        "修正は packaging、meson.build、ソース、スキャフォールド\n"
        "コピーに触れることがあります。アップロード前に Maintainer、Depends、%files、*.in スクリプトを diff してください。\n"
    ),
    "de": (
        "### Beim Ändern des Baums\n"
        "\n"
        "Fixes können packaging, meson.build, Quellen oder Scaffold-\n"
        "Kopien berühren. Diffen Sie Maintainer, Depends, %files und *.in-Skripte vor dem Upload.\n"
    ),
    "fr": (
        "### En modifiant l'arborescence\n"
        "\n"
        "Les correctifs peuvent toucher packaging, meson.build, les sources ou des copies\n"
        "d'échafaudage. Comparez Maintainer, Depends, %files et les scripts *.in avant l'envoi.\n"
    ),
    "ko": (
        "### 트리를 바꿀 때\n"
        "\n"
        "수정은 packaging, meson.build, 소스 또는 스캐폴드\n"
        "사본에 영향을 줄 수 있습니다. 업로드 전에 Maintainer, Depends, %files, *.in 스크립트를 diff하세요.\n"
    ),
    "it": (
        "### Quando si cambia l'albero\n"
        "\n"
        "Le correzioni possono toccare packaging, meson.build, sorgenti o copie\n"
        "di scaffold. Confrontate Maintainer, Depends, %files e gli script *.in prima dell'upload.\n"
    ),
    "ar": (
        "### عند تغيير الشجرة\n"
        "\n"
        "قد تمس الإصلاحات packaging أو meson.build أو المصادر أو نسخ\n"
        "السقالات. قارن Maintainer و Depends و %files وسكربتات *.in قبل الرفع.\n"
    ),
}


def _rule_card(locale: str, intro: str = "") -> str:
    parts = []
    if intro:
        parts.append(intro.rstrip() + "\n")
    parts.append(_RULE_CARD_OPEN[locale].rstrip())
    parts.append("")
    parts.append(_RULE_CARD_LINT[locale].rstrip())
    parts.append("")
    parts.append(_RULE_CARD_CHANGE[locale].rstrip())
    parts.append("")
    return "\n".join(parts) + "\n"


BODIES: dict[str, dict[str, str]] = {
    # -------------------------------------------------------------------------
    "0769b291976e": PLACEHOLDER_BODY,
    # -------------------------------------------------------------------------
    "075a551f9133": {
        "zh_CN": """\
### 语言环境是产品界面

Gettext 目录与完整文档 man/<locale>/ 页面决定用户在已配置的 l10n 级别（`-l` / lint.options）下看到的内容。


### 本检查：{title}

{detail}


### 仍需人工完成

Ize 可生成 .po 桩文件并修正折行风格；真正的翻译与 man 本地化仍需人工（或 `zfr translate`）。长文说明写在按规则的 README-<locale>.md 中——请手译，不要等待缓慢的机器翻译。
""",
        "zh_TW": """\
### 語系是產品介面

Gettext 目錄與整份文件 man/<locale>/ 頁面決定使用者在已設定的 l10n 層級（`-l` / lint.options）下看到的內容。


### 本檢查：{title}

{detail}


### 仍需人工完成

Ize 可產生 .po 樁檔並修正折行風格；真正的翻譯與 man 在地化仍需人工（或 `zfr translate`）。長文說明寫在各規則的 README-<locale>.md——請手譯，不要等待緩慢的機器翻譯。
""",
        "ja": """\
### ロケールはプロダクトの表層です

Gettext カタログと文書全体の man/<locale>/ ページが、設定された l10n レベル（`-l` / lint.options）でユーザーに見える内容を左右します。


### この検査: {title}

{detail}


### 人手の作業は残ります

Ize は .po のスタブ作成と折り返し整形はできますが、本翻訳と man のローカライズは人手（または `zfr translate`）が必要です。長い解説はルールごとの README-<locale>.md にあります——手訳し、遅い機械翻訳を待たないでください。
""",
        "de": """\
### Locales sind Produktfläche

Gettext-Kataloge und vollständige man/<locale>/-Seiten bestimmen, was Nutzer auf dem konfigurierten l10n-Level (`-l` / lint.options) sehen.


### Diese Prüfung: {title}

{detail}


### Menschliche Arbeit bleibt

Ize kann .po-Dateien stubben und den Zeilenumbruch korrigieren; echte Übersetzung und man-Lokalisierung brauchen weiterhin Menschen (oder `zfr translate`). Lange Erläuterungen stehen in README-<locale>.md je Regel — von Hand übersetzen; nicht auf langsame Maschinenübersetzung warten.
""",
        "fr": """\
### Les locales sont une surface produit

Les catalogues gettext et les pages man/<locale>/ documentaires entières déterminent ce que voient les utilisateurs au niveau l10n configuré (`-l` / lint.options).


### Ce contrôle : {title}

{detail}


### Le travail humain reste nécessaire

Ize peut créer des .po ébauches et corriger le style de retour à la ligne ; la vraie traduction et la localisation man demandent encore des personnes (ou `zfr translate`). Les longs essais de lecture sont dans README-<locale>.md par règle — traduisez-les à la main ; n'attendez pas la traduction automatique lente.
""",
        "ko": """\
### 로케일은 제품 표면입니다

Gettext 카탈로그와 전체 문서 man/<locale>/ 페이지가 설정된 l10n 수준(`-l` / lint.options)에서 사용자가 보는 내용을 결정합니다.


### 이 검사: {title}

{detail}


### 사람의 작업은 남습니다

Ize는 .po 스텁 생성과 줄바꿈 스타일 수정은 가능하지만, 실제 번역과 man 현지화는 여전히 사람(또는 `zfr translate`)이 필요합니다. 긴 설명은 규칙별 README-<locale>.md에 있습니다 — 직접 번역하고, 느린 기계 번역을 기다리지 마세요.
""",
        "it": """\
### Le locale sono una superficie di prodotto

I cataloghi gettext e le pagine man/<locale>/ di documento intero determinano ciò che gli utenti vedono al livello l10n configurato (`-l` / lint.options).


### Questo controllo: {title}

{detail}


### Resta lavoro umano

Ize può creare stub .po e correggere lo stile di a capo; la traduzione reale e la localizzazione man richiedono ancora persone (o `zfr translate`). I lunghi testi di consultazione sono in README-<locale>.md per regola — traducete a mano; non attendete la traduzione automatica lenta.
""",
        "ar": """\
### المحليات واجهة منتج

كتالوجات Gettext وصفحات man/<locale>/ للمستندات الكاملة تتحكم فيما يراه المستخدمون عند مستوى l10n المضبوط (`-l` / lint.options).


### هذا الفحص: {title}

{detail}


### يبقى العمل البشري

يمكن لـ Ize إنشاء ملفات .po أولية وإصلاح أسلوب الالتفاف؛ الترجمة الحقيقية وتوطين man ما زالا يحتاجان أشخاصًا (أو `zfr translate`). المقالات الطويلة في README-<locale>.md لكل قاعدة — ترجمها يدويًا؛ لا تنتظر الترجمة الآلية البطيئة.
""",
    },
    # -------------------------------------------------------------------------
    "1074899cca0a": {
        "zh_CN": """\
### Debian 是 APT 契约

control / rules / copyright / source format 决定软件包如何构建以及用户安装到什么。Zephyr 统一采用 Meson + dh `--buildsystem=meson --builddirectory=debian/build`。


### 本检查：{title}

{detail}
默认严重级别提示：{sev}。


### 为何重要

错误的 Architecture、缺失 Build-Depends，或非 Meson 的 rules 文件会导致 debuild 失败，或生成无法加载的包——即便本地编译成功。


### 编辑打包时

Ize 可能按模板重写——上传前务必 diff Maintainer、Depends 与 Architecture。
""",
        "zh_TW": """\
### Debian 是 APT 契約

control / rules / copyright / source format 決定套件如何建置以及使用者安裝到什麼。Zephyr 統一採用 Meson + dh `--buildsystem=meson --builddirectory=debian/build`。


### 本檢查：{title}

{detail}
預設嚴重程度提示：{sev}。


### 為何重要

錯誤的 Architecture、缺少 Build-Depends，或非 Meson 的 rules 檔會導致 debuild 失敗，或產出無法載入的套件——即便本機編譯成功。


### 編輯打包時

Ize 可能依範本重寫——上傳前務必 diff Maintainer、Depends 與 Architecture。
""",
        "ja": """\
### Debian は APT の契約です

control / rules / copyright / source format がパッケージのビルド方法とインストール内容を決めます。Zephyr は Meson + dh `--buildsystem=meson --builddirectory=debian/build` に標準化しています。


### この検査: {title}

{detail}
既定の重大度ヒント: {sev}。


### なぜ重要か

誤った Architecture、欠けた Build-Depends、非 Meson の rules は debuild を失敗させたり、ローカルではビルドできても読み込めないパッケージを生み出します。


### パッケージングを編集するとき

Ize はテンプレートから書き換えることがあります——アップロード前に必ず Maintainer、Depends、Architecture を diff してください。
""",
        "de": """\
### Debian ist der APT-Vertrag

control / rules / copyright / source format entscheiden, wie das Paket baut und was Nutzer installieren. Zephyr standardisiert auf Meson + dh `--buildsystem=meson --builddirectory=debian/build`.


### Diese Prüfung: {title}

{detail}
Standard-Schweregrad-Hinweis: {sev}.


### Warum es zählt

Falsche Architecture, fehlende Build-Depends oder eine Nicht-Meson-rules-Datei lassen debuild scheitern oder erzeugen nicht ladbare Pakete — auch wenn lokale Builds gelingen.


### Beim Bearbeiten des Packaging

Ize kann aus Vorlagen umschreiben — immer Maintainer, Depends und Architecture vor dem Upload diffen.
""",
        "fr": """\
### Debian est le contrat APT

control / rules / copyright / source format décident comment le paquet se construit et ce que les utilisateurs installent. Zephyr standardise sur Meson + dh `--buildsystem=meson --builddirectory=debian/build`.


### Ce contrôle : {title}

{detail}
Indice de sévérité par défaut : {sev}.


### Pourquoi c'est important

Une Architecture incorrecte, des Build-Depends manquantes ou un fichier rules non-Meson font échouer debuild ou produisent des paquets inutilisables même si la compilation locale réussit.


### En éditant le packaging

Ize peut réécrire depuis les modèles — comparez toujours Maintainer, Depends et Architecture avant l'envoi.
""",
        "ko": """\
### Debian은 APT 계약입니다

control / rules / copyright / source format이 패키지 빌드 방식과 사용자가 설치하는 내용을 결정합니다. Zephyr는 Meson + dh `--buildsystem=meson --builddirectory=debian/build`로 표준화합니다.


### 이 검사: {title}

{detail}
기본 심각도 힌트: {sev}.


### 왜 중요한가

잘못된 Architecture, 누락된 Build-Depends, 또는 비-Meson rules 파일은 debuild를 실패시키거나, 로컬 컴파일이 되어도 로드할 수 없는 패키지를 만듭니다.


### 패키징을 편집할 때

Ize가 템플릿으로 다시 쓸 수 있습니다 — 업로드 전에 항상 Maintainer, Depends, Architecture를 diff하세요.
""",
        "it": """\
### Debian è il contratto APT

control / rules / copyright / source format decidono come il pacchetto si costruisce e cosa installano gli utenti. Zephyr standardizza su Meson + dh `--buildsystem=meson --builddirectory=debian/build`.


### Questo controllo: {title}

{detail}
Suggerimento di gravità predefinito: {sev}.


### Perché conta

Architecture sbagliata, Build-Depends mancanti o un file rules non-Meson fanno fallire debuild o producono pacchetti non caricabili anche se la compilazione locale riesce.


### Quando si modifica il packaging

Ize può riscrivere dai modelli — confrontate sempre Maintainer, Depends e Architecture prima dell'upload.
""",
        "ar": """\
### Debian هو عقد APT

تحدد control / rules / copyright / source format كيف يُبنى الحزمة وما الذي يثبّته المستخدمون. يوحّد Zephyr على Meson + dh `--buildsystem=meson --builddirectory=debian/build`.


### هذا الفحص: {title}

{detail}
تلميح الشدة الافتراضي: {sev}.


### لماذا يهم

Architecture خاطئة أو Build-Depends ناقصة أو ملف rules غير Meson تفشل debuild أو تنتج حزمًا غير قابلة للتحميل حتى إن نجح التجميع المحلي.


### عند تحرير التعبئة

قد يعيد Ize الكتابة من القوالب — قارن دائمًا Maintainer و Depends و Architecture قبل الرفع.
""",
    },
    # -------------------------------------------------------------------------
    "1330a6ebf46c": {
        "zh_CN": """\
### 过长文件难于归属

很长的源文件难以审阅、测试与归属维护。Zephyr 偏好内聚模块——通常放在包级子目录下，配以薄入口文件（与 create/ize 期望的形状相同）。子目录可选：若以其他方式外置辅助代码且结果可维护，亦可。


### 改进带来什么

更小的审阅 diff、更清晰的模块边界、更容易的单元测试，以及繁忙文件上更少的合并冲突。


### 阈值

lint 统计非空行（跳过 build/debian/po/…）。约 ~600 行出现提示；约 ~1000 行出现警告。模板示例模块跳过。匹配附近 `.lintignore`（gitignore 风格；可位于任意子目录）的路径跳过——语言模板默认忽略 `*.css`。


### 修复需人工

自行拆分或抽取内聚段落，并更新 meson/安装/导入列表。`zfr ize` 不会自动拆分源文件。
""",
        "zh_TW": """\
### 過長檔案難於歸屬

很長的原始碼檔難以審閱、測試與歸屬維護。Zephyr 偏好內聚模組——通常放在套件子目錄下，配以薄入口檔（與 create/ize 期望的形狀相同）。子目錄可選：若以其他方式外置輔助程式碼且結果可維護，亦可。


### 改進帶來什麼

更小的審閱 diff、更清晰的模組邊界、更容易的單元測試，以及繁忙檔案上更少的合併衝突。


### 閾值

lint 統計非空行（跳過 build/debian/po/…）。約 ~600 行出現提示；約 ~1000 行出現警告。範本示例模組跳過。符合附近 `.lintignore`（gitignore 風格；可位於任意子目錄）的路徑跳過——語言範本預設忽略 `*.css`。


### 修復需人工

自行拆分或抽取內聚段落，並更新 meson/安裝/匯入清單。`zfr ize` 不會自動拆分原始碼。
""",
        "ja": """\
### 長いファイルは所有を阻む

非常に長いソースはレビュー・テスト・担当が難しくなります。Zephyr は凝集したモジュールを好みます——多くの場合パッケージ配下のサブディレクトリに薄いエントリ点ファイルを置く形（create/ize が期待する形と同じ）です。サブディレクトリは必須ではありません。別の方法でヘルパーを外出し、維持できるなら問題ありません。


### 改善の見返り

より小さいレビュー diff、明確なモジュール境界、単体テストの容易さ、混雑ファイルでのマージ衝突の減少。


### 閾値

lint は空でない行を数えます（build/debian/po/… は除外）。約 ~600 行で note、約 ~1000 行で warning。テンプレートの例モジュールはスキップ。近くの `.lintignore`（gitignore 風；任意のサブディレクトリ可）に合うパスはスキップ——言語テンプレートは既定で `*.css` を無視します。


### 修正は手作業

凝集した節を分割・抽出し、meson/インストール/インポート一覧を自分で更新してください。`zfr ize` はソースを自動分割しません。
""",
        "de": """\
### Lange Dateien erschweren Ownership

Sehr lange Quelldateien sind schwer zu reviewen, zu testen und zu verantworten. Zephyr bevorzugt kohäsive Module — oft unter einem Paket-Unterverzeichnis mit einer dünnen Einstiegsdatei (dieselbe Form, die create/ize erwarten). Ein Unterverzeichnis ist optional: wenn Helfer anders ausgelagert werden und das Ergebnis wartbar bleibt, ist das in Ordnung.


### Was Verbesserung bringt

Kleinere Review-Diffs, klarere Modulgrenzen, einfachere Unit-Tests und weniger Merge-Konflikte auf stark bearbeiteten Dateien.


### Schwellen

Lint zählt nicht-leere Zeilen (build/debian/po/… ausgelassen). Ein Hinweis erscheint bei ~600 Zeilen; eine Warnung bei ~1000. Template-Beispielmodule werden übersprungen. Pfade, die zu einer nahen `.lintignore` passen (gitignore-Stil; darf in jedem Unterverzeichnis liegen), werden übersprungen — Sprachvorlagen ignorieren `*.css` standardmäßig.


### Beheben ist manuell

Teilen oder extrahieren Sie kohäsive Abschnitte und aktualisieren Sie meson-/Install-/Import-Listen selbst. `zfr ize` splittet Quellen nicht automatisch.
""",
        "fr": """\
### Les longs fichiers freinent l'ownership

Les très longs fichiers sources sont durs à relire, tester et posséder. Zephyr préfère des modules cohésifs — souvent sous un sous-répertoire de paquet avec un fichier d'entrée mince (la même forme que create/ize attendent). Un sous-répertoire est optionnel : si les aides sont externalisées autrement et que le résultat reste maintenable, c'est bien.


### Ce que l'amélioration apporte

Des diffs de relecture plus petits, des frontières de modules plus claires, des tests unitaires plus faciles, et moins de conflits de fusion sur les fichiers très actifs.


### Seuils

Lint compte les lignes non vides (en sautant build/debian/po/…). Une note apparaît vers ~600 lignes ; un avertissement vers ~1000. Les modules d'exemple des modèles sont ignorés. Les chemins correspondant à un `.lintignore` voisin (style gitignore ; peut vivre dans n'importe quel sous-répertoire) sont ignorés — les modèles de langage ignorent `*.css` par défaut.


### La correction est manuelle

Découpez ou extrayez des sections cohésives et mettez à jour vous-même les listes meson/install/import. `zfr ize` ne découpe pas automatiquement les sources.
""",
        "ko": """\
### 긴 파일은 소유를 어렵게 합니다

매우 긴 소스 파일은 리뷰·테스트·소유가 어렵습니다. Zephyr는 응집된 모듈을 선호합니다 — 대개 패키지 하위 디렉터리에 얇은 진입점 파일( create/ize가 기대하는 형태와 동일)을 둡니다. 하위 디렉터리는 선택입니다. 다른 방식으로 헬퍼를 분리해 유지 가능하면 괜찮습니다.


### 개선이 주는 이득

더 작은 리뷰 diff, 더 명확한 모듈 경계, 더 쉬운 단위 테스트, 바쁜 파일에서의 병합 충돌 감소.


### 임계값

lint는 비어 있지 않은 줄을 셉니다(build/debian/po/… 건너뜀). 약 ~600줄에서 note, 약 ~1000줄에서 warning. 템플릿 예제 모듈은 건너뜁니다. 근처 `.lintignore`(gitignore 스타일; 아무 하위 디렉터리에나 있을 수 있음)와 맞는 경로는 건너뜁니다 — 언어 템플릿은 기본적으로 `*.css`를 무시합니다.


### 수정은 수동

응집된 절을 나누거나 추출하고 meson/설치/import 목록을 직접 갱신하세요. `zfr ize`는 소스를 자동 분할하지 않습니다.
""",
        "it": """\
### I file lunghi ostacolano l'ownership

File sorgente molto lunghi sono difficili da rivedere, testare e possedere. Zephyr preferisce moduli coesi — spesso sotto una sottodirectory di pacchetto con un file di ingresso sottile (la stessa forma che create/ize si aspettano). Una sottodirectory è opzionale: se gli helper sono esternalizzati altrimenti e il risultato resta manutenibile, va bene.


### Cosa guadagnate migliorando

Diff di revisione più piccoli, confini di modulo più chiari, test unitari più facili e meno conflitti di merge sui file molto toccati.


### Soglie

Lint conta le righe non vuote (saltando build/debian/po/…). Una nota compare intorno a ~600 righe; un avviso intorno a ~1000. I moduli di esempio dei template sono saltati. I percorsi che corrispondono a un `.lintignore` vicino (stile gitignore; può stare in qualsiasi sottodirectory) sono saltati — i template di linguaggio ignorano `*.css` per impostazione predefinita.


### La correzione è manuale

Spezzate o estraete sezioni coese e aggiornate voi stessi le liste meson/install/import. `zfr ize` non spezza automaticamente i sorgenti.
""",
        "ar": """\
### الملفات الطويلة تعيق الملكية

ملفات المصدر الطويلة جدًا يصعب مراجعتها واختبارها وتملكها. يفضّل Zephyr وحدات متماسكة — غالبًا تحت دليل فرعي للحزمة مع ملف دخول رفيع (نفس الشكل الذي يتوقعه create/ize). الدليل الفرعي اختياري: إن أُخرجت المساعدات بطريقة أخرى والنتيجة قابلة للصيانة، فلا بأس.


### ماذا يمنحكم التحسين

فروقات مراجعة أصغر، حدود وحدات أوضح، اختبارات وحدة أسهل، وتعارضات دمج أقل على الملفات النشطة.


### العتبات

يحسب lint الأسطر غير الفارغة (متخطيًا build/debian/po/…). تظهر ملاحظة حول ~600 سطر؛ وتحذير حول ~1000. تُتخطى وحدات أمثلة القوالب. المسارات المطابقة لـ `.lintignore` قريب (أسلوب gitignore؛ قد يعيش في أي دليل فرعي) تُتخطى — قوالب اللغات تتجاهل `*.css` افتراضيًا.


### الإصلاح يدوي

قسّم أو استخرج أقسامًا متماسكة وحدّث قوائم meson/التثبيت/الاستيراد بنفسك. `zfr ize` لا يقسّم المصادر تلقائيًا.
""",
    },
    # -------------------------------------------------------------------------
    "16e1cc2a1270": {
        "zh_CN": """\
### 版本字面量会漂移

硬编码的发行字符串会在你一 bump 就与 debian/changelog 和 Meson project_version() 分叉。


### 单一事实来源

优先在构建时用 @VERSION@ / PROJECT_VERSION 替换，使 `--version`、包装脚本与软件包保持一致。


### 转换时的风险

C/C++ 通常需要 config.h；脚本需要 *.in。大树写入前先对 ize 做干跑（`-n`）。
""",
        "zh_TW": """\
### 版本字面量會漂移

硬編碼的發行字串會在你一 bump 就與 debian/changelog 和 Meson project_version() 分叉。


### 單一事實來源

優先在建置時用 @VERSION@ / PROJECT_VERSION 替換，使 `--version`、包裝腳本與套件保持一致。


### 轉換時的風險

C/C++ 通常需要 config.h；腳本需要 *.in。大樹寫入前先對 ize 做乾跑（`-n`）。
""",
        "ja": """\
### バージョン文字列はずれる

ハードコードしたリリース文字列は、バンプした瞬間に debian/changelog と Meson project_version() から乖離します。


### 単一の信頼源

ビルド時に置換される @VERSION@ / PROJECT_VERSION を使い、`--version`・ラッパー・パッケージを揃えましょう。


### 変換時のリスク

C/C++ は通常 config.h が必要；スクリプトは *.in が必要。大きなツリーでは書き込み前に ize のドライラン（`-n`）を。
""",
        "de": """\
### Versionsliterale driften

Ein hart codierter Release-String weicht von debian/changelog und Meson project_version() ab, sobald Sie bump'en.


### Eine Wahrheitsquelle

Bevorzugen Sie zur Build-Zeit ersetzte @VERSION@ / PROJECT_VERSION, damit `--version`, Wrapper und Pakete übereinstimmen.


### Risiken beim Umstellen

C/C++ braucht meist config.h; Skripte brauchen *.in. Vor dem Schreiben auf großen Bäumen ize trocken laufen lassen (`-n`).
""",
        "fr": """\
### Les littéraux de version dérivent

Une chaîne de version en dur diverge de debian/changelog et de Meson project_version() dès que vous bump'ez.


### Une seule source de vérité

Préférez @VERSION@ / PROJECT_VERSION substitués à la construction pour que `--version`, les wrappers et les paquets restent alignés.


### Risques lors de la conversion

C/C++ a souvent besoin de config.h ; les scripts de *.in. Faites un dry-run ize (`-n`) sur les grands arbres avant d'écrire.
""",
        "ko": """\
### 버전 리터럴은 어긋납니다

하드코딩된 릴리스 문자열은 bump하는 순간 debian/changelog와 Meson project_version()에서 갈라집니다.


### 단일 진실 공급원

빌드 시 치환되는 @VERSION@ / PROJECT_VERSION을 써서 `--version`, 래퍼, 패키지를 맞추세요.


### 변환 시 위험

C/C++는 보통 config.h가 필요하고, 스크립트는 *.in이 필요합니다. 큰 트리에서는 쓰기 전에 ize 드라이런(`-n`)을 하세요.
""",
        "it": """\
### I letterali di versione divergono

Una stringa di release cablata diverge da debian/changelog e da Meson project_version() non appena fate bump.


### Un'unica fonte di verità

Preferite @VERSION@ / PROJECT_VERSION sostituiti in build così `--version`, wrapper e pacchetti restano allineati.


### Rischi in conversione

C/C++ di solito serve config.h; gli script servono *.in. Fate un dry-run ize (`-n`) sugli alberi grandi prima di scrivere.
""",
        "ar": """\
### حرفيات الإصدار تنحرف

سلسلة إصدار مكتوبة حرفيًا تنفصل عن debian/changelog و Meson project_version() فور الرفع.


### مصدر حقيقة واحد

فضّل @VERSION@ / PROJECT_VERSION المستبدلين وقت البناء حتى تبقى `--version` والأغلفة والحزم متوافقة.


### مخاطر عند التحويل

C/C++ يحتاج عادة config.h؛ والسكربتات تحتاج *.in. نفّذ تشغيلًا جافًا لـ ize (`-n`) على الأشجار الكبيرة قبل الكتابة.
""",
    },
    # -------------------------------------------------------------------------
    "18fa922354b8": {
        "zh_CN": """\
### 各生态同一名称

目录名、meson project()、debian Source 与 RPM Name 必须一致。不一致会扰乱重命名、发布与仓库。


### 检查：{title}

{detail}
""",
        "zh_TW": """\
### 各生態同一名稱

目錄名、meson project()、debian Source 與 RPM Name 必須一致。不一致會擾亂重新命名、發佈與倉庫。


### 檢查：{title}

{detail}
""",
        "ja": """\
### エコシステム横断で一つの名前

ディレクトリ名、meson project()、debian Source、RPM Name は一致させます。不一致は rename・リリース・リポジトリを混乱させます。


### 検査: {title}

{detail}
""",
        "de": """\
### Ein Name über Ökosysteme

Verzeichnisname, meson project(), debian Source und RPM Name müssen übereinstimmen. Abweichungen verwirren Rename, Release und Repos.


### Prüfung: {title}

{detail}
""",
        "fr": """\
### Un seul nom entre écosystèmes

Le nom de répertoire, meson project(), debian Source et RPM Name doivent s'accorder. Les écarts perturbent rename, release et dépôts.


### Contrôle : {title}

{detail}
""",
        "ko": """\
### 생태계 전반에 하나의 이름

디렉터리 이름, meson project(), debian Source, RPM Name은 일치해야 합니다. 불일치는 rename, release, 저장소를 혼란스럽게 합니다.


### 검사: {title}

{detail}
""",
        "it": """\
### Un nome tra gli ecosistemi

Nome della directory, meson project(), debian Source e RPM Name devono concordare. I disallineamenti confondono rename, release e repository.


### Controllo: {title}

{detail}
""",
        "ar": """\
### اسم واحد عبر المنظومات

يجب أن تتفق اسم الدليل و meson project() و debian Source و RPM Name. الاختلاف يربك إعادة التسمية والإصدار والمستودعات.


### الفحص: {title}

{detail}
""",
    },
    # -------------------------------------------------------------------------
    "1b9259264b07": {
        "zh_CN": """\
仅用于 RPM 的补丁 packaging/rpm/*.patch 必须在 spec 中列为 PatchN:，并在 %prep 中应用（%autosetup -p1 或 %patch -PN -p1）。Makefile 与 build-rpm.sh 会把它们复制到 SOURCES。

### RPM 须镜像 Meson/Debian

spec 的 %files、BuildArch 与 Version 必须描述 Meson 安装的同一载荷。项目本地 rpmbuild TOPDIR 与过期文件列表是常见失败模式。


### 本检查：{title}

{detail}
严重级别提示：{sev}。


### 典型后果

未打包文件、错误的 noarch/ELF、残留 rpmbuild/，或把 Debian substvars 复制进 Requires。
""",
        "zh_TW": """\
僅用於 RPM 的修補 packaging/rpm/*.patch 必須在 spec 中列為 PatchN:，並在 %prep 中套用（%autosetup -p1 或 %patch -PN -p1）。Makefile 與 build-rpm.sh 會把它們複製到 SOURCES。

### RPM 須鏡像 Meson/Debian

spec 的 %files、BuildArch 與 Version 必須描述 Meson 安裝的同一載荷。專案本地 rpmbuild TOPDIR 與過期檔案清單是常見失敗模式。


### 本檢查：{title}

{detail}
嚴重程度提示：{sev}。


### 典型後果

未打包檔案、錯誤的 noarch/ELF、殘留 rpmbuild/，或把 Debian substvars 複製進 Requires。
""",
        "ja": """\
RPM 専用パッチ packaging/rpm/*.patch は spec で PatchN: として列挙し、%prep で適用します（%autosetup -p1 または %patch -PN -p1）。Makefile と build-rpm.sh が SOURCES へコピーします。

### RPM は Meson/Debian を鏡写しにする

spec の %files、BuildArch、Version は Meson がインストールする同一ペイロードを記述する必要があります。プロジェクトローカルの rpmbuild TOPDIR と古いファイル一覧はよくある失敗パターンです。


### この検査: {title}

{detail}
重大度ヒント: {sev}。


### 典型的な余波

未パッケージファイル、誤った noarch/ELF、残った rpmbuild/、または Debian substvars が Requires にコピーされること。
""",
        "de": """\
RPM-only-Patches unter packaging/rpm/*.patch müssen als PatchN: in der Spec stehen und in %prep angewendet werden (%autosetup -p1 oder %patch -PN -p1). Makefile und build-rpm.sh kopieren sie nach SOURCES.

### RPM muss Meson/Debian spiegeln

spec %files, BuildArch und Version müssen dieselbe Nutzlast beschreiben, die Meson installiert. Projektlokales rpmbuild-TOPDIR und veraltete Dateilisten sind häufige Fehlermodi.


### Diese Prüfung: {title}

{detail}
Schweregrad-Hinweis: {sev}.


### Typische Folgen

Ungepackte Dateien, falsches noarch/ELF, übrig gebliebenes rpmbuild/ oder Debian-Substvars, die in Requires kopiert wurden.
""",
        "fr": """\
Les correctifs RPM-only sous packaging/rpm/*.patch doivent figurer comme PatchN: dans le spec et être appliqués dans %prep (%autosetup -p1 ou %patch -PN -p1). Makefile et build-rpm.sh les copient dans SOURCES.

### RPM doit refléter Meson/Debian

%files, BuildArch et Version du spec doivent décrire la même charge utile que Meson installe. Un TOPDIR rpmbuild local au projet et des listes de fichiers périmées sont des modes d'échec courants.


### Ce contrôle : {title}

{detail}
Indice de sévérité : {sev}.


### Retombées typiques

Fichiers non empaquetés, mauvais noarch/ELF, rpmbuild/ restant, ou substvars Debian copiés dans Requires.
""",
        "ko": """\
RPM 전용 패치 packaging/rpm/*.patch는 spec에 PatchN:으로 나열하고 %prep에서 적용해야 합니다(%autosetup -p1 또는 %patch -PN -p1). Makefile과 build-rpm.sh가 SOURCES로 복사합니다.

### RPM은 Meson/Debian을 미러링해야 합니다

spec의 %files, BuildArch, Version은 Meson이 설치하는 동일 페이로드를 기술해야 합니다. 프로젝트 로컬 rpmbuild TOPDIR과 오래된 파일 목록이 흔한 실패 모드입니다.


### 이 검사: {title}

{detail}
심각도 힌트: {sev}.


### 전형적인 여파

미패키지 파일, 잘못된 noarch/ELF, 남은 rpmbuild/, 또는 Requires에 복사된 Debian substvars.
""",
        "it": """\
Le patch solo-RPM sotto packaging/rpm/*.patch devono essere elencate come PatchN: nello spec e applicate in %prep (%autosetup -p1 o %patch -PN -p1). Makefile e build-rpm.sh le copiano in SOURCES.

### RPM deve rispecchiare Meson/Debian

%files, BuildArch e Version dello spec devono descrivere lo stesso payload che Meson installa. TOPDIR rpmbuild locale al progetto e elenchi file obsoleti sono modalità di fallimento comuni.


### Questo controllo: {title}

{detail}
Suggerimento di gravità: {sev}.


### Conseguenze tipiche

File non pacchettizzati, noarch/ELF sbagliato, rpmbuild/ residuo, o substvars Debian copiati in Requires.
""",
        "ar": """\
يجب إدراج رقع RPM فقط تحت packaging/rpm/*.patch كـ PatchN: في المواصفة وتطبيقها في %prep (%autosetup -p1 أو %patch -PN -p1). Makefile و build-rpm.sh ينسخانها إلى SOURCES.

### يجب أن يعكس RPM Meson/Debian

يجب أن تصف %files و BuildArch و Version في المواصفة نفس الحمولة التي يثبّتها Meson. TOPDIR لـ rpmbuild محلي للمشروع وقوائم ملفات قديمة أنماط فشل شائعة.


### هذا الفحص: {title}

{detail}
تلميح الشدة: {sev}.


### العواقب النموذجية

ملفات غير معبأة، noarch/ELF خاطئ، rpmbuild/ متبقٍ، أو substvars لديبيان منسوخة إلى Requires.
""",
    },
}


# Continue building BODIES in a second write via exec — append remaining hashes.
_MORE = {
    "2811fd00154a": {
        "zh_CN": """\
### 源码卫生

{title}。涵盖会破坏可重定位安装的过长文件与硬编码路径/版本。


### lint 如何看待

{detail}
""",
        "zh_TW": """\
### 原始碼衛生

{title}。涵蓋會破壞可重定位安裝的過長檔案與硬編碼路徑/版本。


### lint 如何看待

{detail}
""",
        "ja": """\
### ソース衛生

{title}。再配置可能なインストールを壊す長さとハードコードされたパス/バージョンを扱います。


### lint の見方

{detail}
""",
        "de": """\
### Quellhygiene

{title}. Deckt Länge und hart codierte Pfade/Versionen, die relokierbare Installationen brechen.


### Wie lint schaut

{detail}
""",
        "fr": """\
### Hygiène des sources

{title}. Couvre la longueur et les chemins/versions en dur qui cassent les installations relocalisables.


### Comment lint regarde

{detail}
""",
        "ko": """\
### 소스 위생

{title}. 재배치 가능 설치를 깨는 길이와 하드코딩된 경로/버전을 다룹니다.


### lint가 보는 방식

{detail}
""",
        "it": """\
### Igiene dei sorgenti

{title}. Copre lunghezza e percorsi/versioni cablati che rompono installazioni rilocabili.


### Come guarda lint

{detail}
""",
        "ar": """\
### نظافة المصدر

{title}. يغطي الطول والمسارات/الإصدارات المكتوبة حرفيًا التي تكسر التثبيتات القابلة لإعادة التموضع.


### كيف ينظر lint

{detail}
""",
    },
    "2bc2a0fbd723": {
        "zh_CN": """\
### 共享布局让工具有方向

LICENSE、man/、VERSION、hooks、completion 与 scripts/ 是 create/ize/lint/release 期望的地标。


### 缺失或错误：{title}

{detail}


### 脚手架刷新

Solve 可能从模板安装或刷新文件（.githooks、LICENSE、cursor 规则等）。提交前请审阅。
""",
        "zh_TW": """\
### 共享版面讓工具有方向

LICENSE、man/、VERSION、hooks、completion 與 scripts/ 是 create/ize/lint/release 期望的地標。


### 缺失或錯誤：{title}

{detail}


### 鷹架刷新

Solve 可能從範本安裝或刷新檔案（.githooks、LICENSE、cursor 規則等）。提交前請審閱。
""",
        "ja": """\
### 共有レイアウトがツールの指針になる

LICENSE、man/、VERSION、hooks、completion、scripts/ は create/ize/lint/release が期待する目印です。


### 欠落または誤り: {title}

{detail}


### スキャフォールド更新

Solve はテンプレートからファイルをインストールまたは更新することがあります（.githooks、LICENSE、cursor ルールなど）。コミット前に確認してください。
""",
        "de": """\
### Gemeinsames Layout hält Werkzeuge orientiert

LICENSE, man/, VERSION, Hooks, Completion und scripts/ sind die Landmarken, die create/ize/lint/release erwarten.


### Fehlend oder falsch: {title}

{detail}


### Scaffold-Auffrischung

Solve kann Dateien aus der Vorlage installieren oder auffrischen (.githooks, LICENSE, Cursor-Regeln, …). Vor dem Commit prüfen.
""",
        "fr": """\
### Une disposition partagée oriente les outils

LICENSE, man/, VERSION, hooks, completion et scripts/ sont les repères que create/ize/lint/release attendent.


### Manquant ou incorrect : {title}

{detail}


### Rafraîchissement d'échafaudage

Solve peut installer ou rafraîchir des fichiers depuis le modèle (.githooks, LICENSE, règles cursor, …). Relisez avant de committer.
""",
        "ko": """\
### 공유 레이아웃이 도구를 방향 잡습니다

LICENSE, man/, VERSION, hooks, completion, scripts/는 create/ize/lint/release가 기대하는 이정표입니다.


### 누락 또는 오류: {title}

{detail}


### 스캐폴드 갱신

Solve가 템플릿에서 파일을 설치하거나 갱신할 수 있습니다(.githooks, LICENSE, cursor 규칙 등). 커밋 전에 검토하세요.
""",
        "it": """\
### Un layout condiviso orienta gli strumenti

LICENSE, man/, VERSION, hooks, completion e scripts/ sono i punti di riferimento che create/ize/lint/release si aspettano.


### Mancante o errato: {title}

{detail}


### Aggiornamento dello scaffold

Solve può installare o aggiornare file dal modello (.githooks, LICENSE, regole cursor, …). Rivedete prima del commit.
""",
        "ar": """\
### التخطيط المشترك يوجّه الأدوات

LICENSE و man/ و VERSION والخطافات والإكمال و scripts/ هي المعالم التي يتوقعها create/ize/lint/release.


### مفقود أو خاطئ: {title}

{detail}


### تحديث السقالة

قد يثبت Solve ملفات من القالب أو يحدّثها (.githooks و LICENSE وقواعد cursor، …). راجع قبل الالتزام.
""",
    },
}

BODIES.update(_MORE)
del _MORE

_PLAIN = {
    "57e6faa86f6f": {
        "zh_CN": """\
meson.build 应通过 configuration_data（ize_cfg / config_h / paths_cfg）提供 VERSION/PROJECT_VERSION，且 src/ 下至少一个源文件（或 configure_file 输入）必须消费 @VERSION@ 或 PROJECT_VERSION。

### 有替换无无消费者是不完整的

Meson 必须既定义 VERSION/PROJECT_VERSION，又有真正读取它的源——否则打包后的二进制仍会说谎。


### 如何检查

查找 configuration_data 键，以及已安装源中的 @VERSION@ / PROJECT_VERSION 用法。


### 闭环

补上缺失的一半（替换或消费者）。Solve 在可用时映射到 subst 的 ize 步骤。
""",
        "zh_TW": """\
meson.build 應透過 configuration_data（ize_cfg / config_h / paths_cfg）提供 VERSION/PROJECT_VERSION，且 src/ 下至少一個原始碼（或 configure_file 輸入）必須消費 @VERSION@ 或 PROJECT_VERSION。

### 有替換無消費者是不完整的

Meson 必須既定義 VERSION/PROJECT_VERSION，又有真正讀取它的原始碼——否則打包後的二進位仍會說謊。


### 如何檢查

查找 configuration_data 鍵，以及已安裝原始碼中的 @VERSION@ / PROJECT_VERSION 用法。


### 閉環

補上缺失的一半（替換或消費者）。Solve 在可用時對應到 subst 的 ize 步驟。
""",
        "ja": """\
meson.build は configuration_data（ize_cfg / config_h / paths_cfg）経由で VERSION/PROJECT_VERSION を供給し、src/ 配下の少なくとも一つのソース（または configure_file 入力）が @VERSION@ または PROJECT_VERSION を消費する必要があります。

### 置換だけで消費者が無いのは不完全

Meson は VERSION/PROJECT_VERSION を定義し、実際に読むソースも持たねばなりません——さもなくばパッケージ済みバイナリは嘘をつきます。


### 検査方法

configuration_data のキーと、インストールされるソース内の @VERSION@ / PROJECT_VERSION 使用を探します。


### ループを閉じる

欠けている半分（置換または消費者）を追加。Solve は可能なとき subst の ize 手順に対応付けます。
""",
        "de": """\
meson.build soll VERSION/PROJECT_VERSION über configuration_data (ize_cfg / config_h / paths_cfg) speisen, und mindestens eine Quelle unter src/ (oder eine configure_file-Eingabe) muss @VERSION@ oder PROJECT_VERSION verbrauchen.

### Substitution ohne Verbraucher ist unvollständig

Meson muss VERSION/PROJECT_VERSION sowohl definieren als auch Quellen haben, die es wirklich lesen — sonst lügen gepackte Binaries weiterhin.


### Wie geprüft wird

Sucht configuration_data-Schlüssel und @VERSION@ / PROJECT_VERSION-Nutzung in installierten Quellen.


### Den Kreis schließen

Die fehlende Hälfte ergänzen (Subst oder Verbraucher). Solve mappt auf die Subst-ize-Schritte, wenn verfügbar.
""",
        "fr": """\
meson.build doit alimenter VERSION/PROJECT_VERSION via configuration_data (ize_cfg / config_h / paths_cfg), et au moins une source sous src/ (ou une entrée configure_file) doit consommer @VERSION@ ou PROJECT_VERSION.

### Une substitution sans consommateur est incomplète

Meson doit à la fois définir VERSION/PROJECT_VERSION et avoir des sources qui le lisent vraiment — sinon les binaires empaquetés mentent encore.


### Comment c'est vérifié

Cherche les clés configuration_data et l'usage de @VERSION@ / PROJECT_VERSION dans les sources installées.


### Fermer la boucle

Ajoutez la moitié manquante (subst ou consommateur). Solve mappe vers les étapes ize subst quand disponibles.
""",
        "ko": """\
meson.build는 configuration_data(ize_cfg / config_h / paths_cfg)로 VERSION/PROJECT_VERSION을 공급해야 하며, src/ 아래 최소 하나의 소스(또는 configure_file 입력)가 @VERSION@ 또는 PROJECT_VERSION을 소비해야 합니다.

### 소비자 없는 치환은 불완전합니다

Meson은 VERSION/PROJECT_VERSION을 정의하고 실제로 읽는 소스도 있어야 합니다 — 그렇지 않으면 패키지된 바이너리가 여전히 거짓말합니다.


### 검사 방식

configuration_data 키와 설치된 소스의 @VERSION@ / PROJECT_VERSION 사용을 찾습니다.


### 고리 닫기

빠진 절반(치환 또는 소비자)을 추가하세요. Solve는 가능하면 subst ize 단계로 매핑합니다.
""",
        "it": """\
meson.build deve alimentare VERSION/PROJECT_VERSION via configuration_data (ize_cfg / config_h / paths_cfg), e almeno una sorgente sotto src/ (o un input configure_file) deve consumare @VERSION@ o PROJECT_VERSION.

### Sostituzione senza consumatore è incompleta

Meson deve sia definire VERSION/PROJECT_VERSION sia avere sorgenti che lo leggono davvero — altrimenti i binari pacchettizzati mentono ancora.


### Come viene controllato

Cerca chiavi configuration_data e uso di @VERSION@ / PROJECT_VERSION nelle sorgenti installate.


### Chiudere il cerchio

Aggiungete la metà mancante (subst o consumatore). Solve mappa ai passi ize subst quando disponibili.
""",
        "ar": """\
يجب أن يغذّي meson.build VERSION/PROJECT_VERSION عبر configuration_data (ize_cfg / config_h / paths_cfg)، ويجب أن يستهلك مصدر واحد على الأقل تحت src/ (أو مدخل configure_file) @VERSION@ أو PROJECT_VERSION.

### الاستبدال بلا مستهلك غير مكتمل

يجب أن يعرّف Meson VERSION/PROJECT_VERSION وأن تكون هناك مصادر تقرأه فعليًا — وإلا تظل الثنائيات المعبأة تكذب.


### كيف يُفحص

يبحث عن مفاتيح configuration_data واستخدام @VERSION@ / PROJECT_VERSION في المصادر المثبتة.


### إغلاق الحلقة

أضف النصف الناقص (استبدال أو مستهلك). يربط Solve بخطوات ize للاستبدال عند التوفر.
""",
    },
    "5fc0a4bfb642": {
        "zh_CN": """\
### Meson 是权威构建系统

身份、许可证、版本来源、手册页、补全以及 look/posync 目标都在 meson.build。此处漂移会同时破坏 Debian 与 RPM。


### 本检查：{title}

{detail}


### 编辑提示

Ize 会修补 meson.build；将自定义目标与模板块对齐，大改后重新 configure。
""",
        "zh_TW": """\
### Meson 是權威建置系統

身分、授權、版本來源、手冊頁、補全以及 look/posync 目標都在 meson.build。此處漂移會同時破壞 Debian 與 RPM。


### 本檢查：{title}

{detail}


### 編輯提示

Ize 會修補 meson.build；將自訂目標與範本區塊對齊，大改後重新 configure。
""",
        "ja": """\
### Meson が正式なビルドシステムです

識別子、ライセンス、バージョン源、man、補完、look/posync ターゲットは meson.build に置きます。ここでのずれは Debian も RPM も壊します。


### この検査: {title}

{detail}


### 編集のヒント

Ize は meson.build をパッチします；カスタムターゲットをテンプレートブロックと調停し、大きな編集後は再 configure。
""",
        "de": """\
### Meson ist das maßgebliche Build-System

Identität, Lizenz, Versionsquelle, Manpages, Completion und look/posync-Targets leben in meson.build. Drift hier bricht Debian und RPM gleichermaßen.


### Diese Prüfung: {title}

{detail}


### Bearbeitungstipps

Ize patcht meson.build; gleichen Sie eigene Targets mit Vorlagenblöcken ab und re-konfigurieren Sie nach großen Edits.
""",
        "fr": """\
### Meson est le système de build de référence

Identité, licence, source de version, pages man, completion et cibles look/posync vivent dans meson.build. Une dérive ici casse Debian et RPM.


### Ce contrôle : {title}

{detail}


### Conseils d'édition

Ize patch meson.build ; réconciliez les cibles personnalisées avec les blocs du modèle et reconfigurez après de grandes modifications.
""",
        "ko": """\
### Meson이 공식 빌드 시스템입니다

정체성, 라이선스, 버전 원천, man 페이지, 보완, look/posync 타깃은 meson.build에 있습니다. 여기서의 어긋남은 Debian과 RPM을 함께 깨뜨립니다.


### 이 검사: {title}

{detail}


### 편집 팁

Ize가 meson.build를 패치합니다; 사용자 정의 타깃을 템플릿 블록과 맞추고 큰 편집 후 다시 configure하세요.
""",
        "it": """\
### Meson è il sistema di build di riferimento

Identità, licenza, fonte versione, man, completion e target look/posync vivono in meson.build. La deriva qui rompe Debian e RPM allo stesso modo.


### Questo controllo: {title}

{detail}


### Suggerimenti di editing

Ize patcha meson.build; riconciliate i target personalizzati con i blocchi del template e riconfigurate dopo grandi modifiche.
""",
        "ar": """\
### Meson هو نظام البناء المرجعي

الهوية والرخصة ومصدر الإصدار وصفحات man والإكمال وأهداف look/posync تعيش في meson.build. الانحراف هنا يكسر Debian و RPM معًا.


### هذا الفحص: {title}

{detail}


### نصائح التحرير

Ize يرقّع meson.build؛ وفّق الأهداف المخصصة مع كتل القالب وأعد configure بعد التعديلات الكبيرة.
""",
    },
    "6449382bafea": {
        "zh_CN": """\
### 语言模板期望

{title}。每种语言保留惯用标记（tests/、Cargo.toml、bas i18n 辅助、bash *.in 等），使树保持可打包。


### 细节

{detail}
""",
        "zh_TW": """\
### 語言範本期望

{title}。每種語言保留慣用標記（tests/、Cargo.toml、bas i18n 輔助、bash *.in 等），使樹保持可打包。


### 細節

{detail}
""",
        "ja": """\
### 言語テンプレートの期待

{title}。各言語は慣用マーカー（tests/、Cargo.toml、bas i18n ヘルパー、bash *.in など）を保ち、ツリーをパッケージ可能に保ちます。


### 詳細

{detail}
""",
        "de": """\
### Erwartungen der Sprachvorlagen

{title}. Jede Sprache behält idiomatische Marker (tests/, Cargo.toml, bas-i18n-Helfer, bash *.in, …), damit der Baum packbar bleibt.


### Details

{detail}
""",
        "fr": """\
### Attentes des modèles de langage

{title}. Chaque langage garde des marqueurs idiomatiques (tests/, Cargo.toml, aides i18n bas, bash *.in, …) pour que l'arbre reste empaquetable.


### Détails

{detail}
""",
        "ko": """\
### 언어 템플릿 기대사항

{title}. 각 언어는 관용 표식(tests/, Cargo.toml, bas i18n 헬퍼, bash *.in 등)을 유지해 트리를 패키징 가능하게 둡니다.


### 세부사항

{detail}
""",
        "it": """\
### Aspettative dei template di linguaggio

{title}. Ogni linguaggio mantiene marcatori idiomatici (tests/, Cargo.toml, helper i18n bas, bash *.in, …) così l'albero resta pacchettizzabile.


### Dettagli

{detail}
""",
        "ar": """\
### توقعات قوالب اللغات

{title}. تحتفظ كل لغة بعلامات اصطلاحية (tests/ و Cargo.toml ومساعدات bas i18n و bash *.in، …) حتى تبقى الشجرة قابلة للتعبئة.


### التفاصيل

{detail}
""",
    },
    "9c3e7564f4a6": {
        "zh_CN": """\
### RPM 须镜像 Meson/Debian

spec 的 %files、BuildArch 与 Version 必须描述 Meson 安装的同一载荷。项目本地 rpmbuild TOPDIR 与过期文件列表是常见失败模式。


### 本检查：{title}

{detail}
严重级别提示：{sev}。


### 典型后果

未打包文件、错误的 noarch/ELF、残留 rpmbuild/，或把 Debian substvars 复制进 Requires。
""",
        "zh_TW": """\
### RPM 須鏡像 Meson/Debian

spec 的 %files、BuildArch 與 Version 必須描述 Meson 安裝的同一載荷。專案本地 rpmbuild TOPDIR 與過期檔案清單是常見失敗模式。


### 本檢查：{title}

{detail}
嚴重程度提示：{sev}。


### 典型後果

未打包檔案、錯誤的 noarch/ELF、殘留 rpmbuild/，或把 Debian substvars 複製進 Requires。
""",
        "ja": """\
### RPM は Meson/Debian を鏡写しにする

spec の %files、BuildArch、Version は Meson がインストールする同一ペイロードを記述する必要があります。プロジェクトローカルの rpmbuild TOPDIR と古いファイル一覧はよくある失敗パターンです。


### この検査: {title}

{detail}
重大度ヒント: {sev}。


### 典型的な余波

未パッケージファイル、誤った noarch/ELF、残った rpmbuild/、または Debian substvars が Requires にコピーされること。
""",
        "de": """\
### RPM muss Meson/Debian spiegeln

spec %files, BuildArch und Version müssen dieselbe Nutzlast beschreiben, die Meson installiert. Projektlokales rpmbuild-TOPDIR und veraltete Dateilisten sind häufige Fehlermodi.


### Diese Prüfung: {title}

{detail}
Schweregrad-Hinweis: {sev}.


### Typische Folgen

Ungepackte Dateien, falsches noarch/ELF, übrig gebliebenes rpmbuild/ oder Debian-Substvars, die in Requires kopiert wurden.
""",
        "fr": """\
### RPM doit refléter Meson/Debian

%files, BuildArch et Version du spec doivent décrire la même charge utile que Meson installe. Un TOPDIR rpmbuild local au projet et des listes de fichiers périmées sont des modes d'échec courants.


### Ce contrôle : {title}

{detail}
Indice de sévérité : {sev}.


### Retombées typiques

Fichiers non empaquetés, mauvais noarch/ELF, rpmbuild/ restant, ou substvars Debian copiés dans Requires.
""",
        "ko": """\
### RPM은 Meson/Debian을 미러링해야 합니다

spec의 %files, BuildArch, Version은 Meson이 설치하는 동일 페이로드를 기술해야 합니다. 프로젝트 로컬 rpmbuild TOPDIR과 오래된 파일 목록이 흔한 실패 모드입니다.


### 이 검사: {title}

{detail}
심각도 힌트: {sev}.


### 전형적인 여파

미패키지 파일, 잘못된 noarch/ELF, 남은 rpmbuild/, 또는 Requires에 복사된 Debian substvars.
""",
        "it": """\
### RPM deve rispecchiare Meson/Debian

%files, BuildArch e Version dello spec devono descrivere lo stesso payload che Meson installa. TOPDIR rpmbuild locale al progetto e elenchi file obsoleti sono modalità di fallimento comuni.


### Questo controllo: {title}

{detail}
Suggerimento di gravità: {sev}.


### Conseguenze tipiche

File non pacchettizzati, noarch/ELF sbagliato, rpmbuild/ residuo, o substvars Debian copiati in Requires.
""",
        "ar": """\
### يجب أن يعكس RPM Meson/Debian

يجب أن تصف %files و BuildArch و Version في المواصفة نفس الحمولة التي يثبّتها Meson. TOPDIR لـ rpmbuild محلي للمشروع وقوائم ملفات قديمة أنماط فشل شائعة.


### هذا الفحص: {title}

{detail}
تلميح الشدة: {sev}.


### العواقب النموذجية

ملفات غير معبأة، noarch/ELF خاطئ، rpmbuild/ متبقٍ، أو substvars لديبيان منسوخة إلى Requires.
""",
    },
    "e78736b81287": {
        "zh_CN": """\
### 硬编码 /usr 破坏前缀

绝对 FHS 路径（/usr/share、/usr/bin 等）在 DESTDIR、非标准前缀以及 Meson configure_file 暂存下会失败。


### 首选形态

脚本使用 @PREFIX@ / @DATADIR@ / @LOCALEDIR@（或等价物），并由 Meson 通过 *.in 安装。


### Solve 做什么

Ize 将受影响脚本重命名为 *.in 并接线 configure_file。请重新检查 shebang 以及假定了实际路径的测试。
""",
        "zh_TW": """\
### 硬編碼 /usr 破壞前綴

絕對 FHS 路徑（/usr/share、/usr/bin 等）在 DESTDIR、非標準前綴以及 Meson configure_file 暫存下會失敗。


### 首選形態

腳本使用 @PREFIX@ / @DATADIR@ / @LOCALEDIR@（或等價物），並由 Meson 透過 *.in 安裝。


### Solve 做什麼

Ize 將受影響腳本重新命名為 *.in 並接線 configure_file。請重新檢查 shebang 以及假定了實際路徑的測試。
""",
        "ja": """\
### ハードコードした /usr は接頭辞を壊す

絶対 FHS パス（/usr/share、/usr/bin など）は DESTDIR、非標準接頭辞、Meson configure_file のステージングで失敗します。


### 望ましい形

スクリプトは @PREFIX@ / @DATADIR@ / @LOCALEDIR@（または同等）を使い、Meson 経由で *.in からインストールします。


### Solve の動作

Ize は該当スクリプトを *.in に改名し configure_file を配線します。shebang と実パス前提のテストを再確認してください。
""",
        "de": """\
### Hartes /usr bricht Präfixe

Absolute FHS-Pfade (/usr/share, /usr/bin, …) scheitern unter DESTDIR, nicht-standard Präfixen und Meson-configure_file-Staging.


### Bevorzugte Form

Skripte nutzen @PREFIX@ / @DATADIR@ / @LOCALEDIR@ (oder Entsprechungen) und werden aus *.in via Meson installiert.


### Was Solve tut

Ize benennt betroffene Skripte in *.in um und verdrahtet configure_file. Shebangs und Tests, die Live-Pfade annahmen, erneut prüfen.
""",
        "fr": """\
### Un /usr en dur casse les préfixes

Les chemins FHS absolus (/usr/share, /usr/bin, …) échouent sous DESTDIR, préfixes non standard et le staging Meson configure_file.


### Forme préférée

Les scripts utilisent @PREFIX@ / @DATADIR@ / @LOCALEDIR@ (ou équivalent) et sont installés depuis *.in via Meson.


### Ce que fait Solve

Ize renomme les scripts concernés en *.in et câble configure_file. Revérifiez les shebangs et les tests qui supposaient des chemins vivants.
""",
        "ko": """\
### 하드코딩된 /usr는 접두사를 깨뜨립니다

절대 FHS 경로(/usr/share, /usr/bin, …)는 DESTDIR, 비표준 접두사, Meson configure_file 스테이징에서 실패합니다.


### 권장 형태

스크립트는 @PREFIX@ / @DATADIR@ / @LOCALEDIR@(또는 동등물)을 쓰고 Meson을 통해 *.in에서 설치됩니다.


### Solve가 하는 일

Ize는 영향받는 스크립트를 *.in으로 이름 바꾸고 configure_file을 연결합니다. shebang과 실제 경로를 가정한 테스트를 다시 확인하세요.
""",
        "it": """\
### Un /usr cablato rompe i prefissi

I percorsi FHS assoluti (/usr/share, /usr/bin, …) falliscono sotto DESTDIR, prefissi non standard e lo staging Meson configure_file.


### Forma preferita

Gli script usano @PREFIX@ / @DATADIR@ / @LOCALEDIR@ (o equivalenti) e si installano da *.in via Meson.


### Cosa fa Solve

Ize rinomina gli script interessati in *.in e collega configure_file. Ricontrollate shebang e test che assumevano percorsi live.
""",
        "ar": """\
### /usr المكتوب حرفيًا يكسر البادئات

مسارات FHS المطلقة (/usr/share و /usr/bin، …) تفشل تحت DESTDIR والبادئات غير القياسية وتجهيز Meson configure_file.


### الشكل المفضّل

تستخدم السكربتات @PREFIX@ / @DATADIR@ / @LOCALEDIR@ (أو ما يعادلها) وتُثبَّت من *.in عبر Meson.


### ماذا يفعل Solve

Ize يعيد تسمية السكربتات المتأثرة إلى *.in ويوصّل configure_file. أعد فحص shebang وأي اختبارات افترضت مسارات حية.
""",
    },
    "f26ddba2a747": {
        "zh_CN": """\
### 单一事实来源

`VERSION` 应与最新的 `debian/changelog` 条目一致。标准 `.githooks/pre-commit`（配合 `core.hooksPath=.githooks`）会在提交时重写 `VERSION`。


### 已配置同步钩子时

若该 pre-commit 钩子存在且从 changelog 同步 VERSION，则下次提交前的暂时不一致是预期的——lint 报告 **ok** 而非警告。


### 未配置钩子时

不一致为 **warn**：手动对齐 VERSION，或通过 `zfr ize` 安装标准钩子，然后 `git config core.hooksPath .githooks`。
""",
        "zh_TW": """\
### 單一事實來源

`VERSION` 應與最新的 `debian/changelog` 條目一致。標準 `.githooks/pre-commit`（配合 `core.hooksPath=.githooks`）會在提交時重寫 `VERSION`。


### 已設定同步鉤子時

若該 pre-commit 鉤子存在且從 changelog 同步 VERSION，則下次提交前的暫時不一致是預期的——lint 報告 **ok** 而非警告。


### 未設定鉤子時

不一致為 **warn**：手動對齊 VERSION，或透過 `zfr ize` 安裝標準鉤子，然後 `git config core.hooksPath .githooks`。
""",
        "ja": """\
### 単一の信頼源

`VERSION` は最新の `debian/changelog` 項目と一致すべきです。標準の `.githooks/pre-commit`（`core.hooksPath=.githooks` と併用）がコミット時に `VERSION` を書き直します。


### 同期フックが設定されているとき

その pre-commit フックがあり changelog から VERSION を同期するなら、次のコミットまでの一時的な不一致は想定内——lint は警告ではなく **ok** を報告します。


### フックが無いとき

不一致は **warn**：手で VERSION を揃えるか、`zfr ize` で標準フックを入れ、`git config core.hooksPath .githooks`。
""",
        "de": """\
### Eine Wahrheitsquelle

`VERSION` sollte dem neuesten `debian/changelog`-Eintrag entsprechen. Der Standard-`.githooks/pre-commit` (mit `core.hooksPath=.githooks`) schreibt `VERSION` beim Commit um.


### Wenn ein Sync-Hook konfiguriert ist

Ist dieser pre-commit-Hook vorhanden und synchronisiert VERSION aus dem Changelog, ist eine vorübergehende Abweichung bis zum nächsten Commit erwartet — lint meldet **ok** statt Warnung.


### Wenn kein Hook konfiguriert ist

Eine Abweichung ist **warn**: VERSION von Hand angleichen oder den Standard-Hook via `zfr ize` installieren, dann `git config core.hooksPath .githooks`.
""",
        "fr": """\
### Une seule source de vérité

`VERSION` doit correspondre à la dernière entrée de `debian/changelog`. Le `.githooks/pre-commit` standard (avec `core.hooksPath=.githooks`) réécrit `VERSION` au commit.


### Quand un hook de sync est configuré

Si ce hook pre-commit est présent et synchronise VERSION depuis le changelog, un décalage temporaire jusqu'au prochain commit est attendu — lint rapporte **ok** au lieu d'un avertissement.


### Quand aucun hook n'est configuré

Un décalage est un **warn** : alignez VERSION à la main ou installez le hook standard via `zfr ize`, puis `git config core.hooksPath .githooks`.
""",
        "ko": """\
### 단일 진실 공급원

`VERSION`은 최신 `debian/changelog` 항목과 일치해야 합니다. 표준 `.githooks/pre-commit`(`core.hooksPath=.githooks`와 함께)이 커밋 시 `VERSION`을 다시 씁니다.


### 동기화 훅이 설정된 경우

해당 pre-commit 훅이 있고 changelog에서 VERSION을 동기화하면, 다음 커밋까지의 일시적 불일치는 예상됩니다 — lint는 경고 대신 **ok**를 보고합니다.


### 훅이 없는 경우

불일치는 **warn**: VERSION을 손으로 맞추거나 `zfr ize`로 표준 훅을 설치한 뒤 `git config core.hooksPath .githooks`.
""",
        "it": """\
### Un'unica fonte di verità

`VERSION` dovrebbe corrispondere all'ultima voce di `debian/changelog`. Il `.githooks/pre-commit` standard (con `core.hooksPath=.githooks`) riscrive `VERSION` al commit.


### Quando un hook di sync è configurato

Se quel hook pre-commit è presente e sincronizza VERSION dal changelog, una discrepanza temporanea fino al prossimo commit è attesa — lint riporta **ok** invece di un avviso.


### Quando nessun hook è configurato

Una discrepanza è un **warn**: allineate VERSION a mano o installate l'hook standard via `zfr ize`, poi `git config core.hooksPath .githooks`.
""",
        "ar": """\
### مصدر حقيقة واحد

يجب أن يطابق `VERSION` أحدث إدخال في `debian/changelog`. يعيد `.githooks/pre-commit` القياسي (مع `core.hooksPath=.githooks`) كتابة `VERSION` عند الالتزام.


### عند ضبط خطاف مزامنة

إن وُجد خطاف pre-commit ذلك ويُزامن VERSION من سجل التغييرات، فعدم التطابق المؤقت حتى الالتزام التالي متوقع — يُبلّغ lint بـ **ok** بدل التحذير.


### عند عدم ضبط خطاف

عدم التطابق **warn**: وافق VERSION يدويًا أو ثبّت الخطاف القياسي عبر `zfr ize`، ثم `git config core.hooksPath .githooks`.
""",
    },
    "f509ce998009": {
        "zh_CN": """\
存在 po/ 时，meson.run_target('posync') 必须调用 scripts/posync.sh，而非内联的 bash -euc heredoc。运行 `zfr ize` 以抽取。

### 内联 posync 难以维护

meson.build 内的 bash -euc heredoc 会在模板间重复且难调试。约定是由 run_target('posync') 接线的 `zfr translate --sync`（Python），而非内联 heredoc。


### 回报

一条命令即可本地同步 xgettext/msgmerge；ninja posync 保持简短；CI 可调用 `zfr translate --sync` 或导入 `translate.sync`。


### Solve

Ize 将 run_target('posync') 重写为通过项目 Python 入口调用 translate --sync（在 zfr 内优先 import）。之后请核对 POTFILES 与语言标志。
""",
        "zh_TW": """\
存在 po/ 時，meson.run_target('posync') 必須呼叫 scripts/posync.sh，而非內聯的 bash -euc heredoc。執行 `zfr ize` 以抽取。

### 內聯 posync 難以維護

meson.build 內的 bash -euc heredoc 會在範本間重複且難除錯。約定是由 run_target('posync') 接線的 `zfr translate --sync`（Python），而非內聯 heredoc。


### 回報

一條指令即可本機同步 xgettext/msgmerge；ninja posync 保持簡短；CI 可呼叫 `zfr translate --sync` 或匯入 `translate.sync`。


### Solve

Ize 將 run_target('posync') 重寫為透過專案 Python 入口呼叫 translate --sync（在 zfr 內優先 import）。之後請核對 POTFILES 與語言旗標。
""",
        "ja": """\
po/ があるとき、meson.run_target('posync') はインラインの bash -euc heredoc ではなく scripts/posync.sh を呼ぶ必要があります。抽出には `zfr ize` を実行。

### インライン posync は保守不能

meson.build 内の bash -euc heredoc はテンプレート間で重複し、デバッグが苦痛です。契約は run_target('posync') から配線した `zfr translate --sync`（Python）であり、インライン heredoc ではありません。


### 見返り

一つのコマンドで xgettext/msgmerge をローカル同期；ninja posync は短く保たれ；CI は `zfr translate --sync` を呼ぶか `translate.sync` を import できます。


### Solve

Ize は run_target('posync') をプロジェクトの Python エントリ経由で translate --sync を呼ぶよう書き換えます（zfr 内では import 優先）。その後 POTFILES と言語フラグを確認。
""",
        "de": """\
Wenn po/ existiert, muss meson.run_target('posync') scripts/posync.sh aufrufen statt eines Inline-bash -euc-Heredocs. Mit `zfr ize` extrahieren.

### Inline-posync ist unwartbar

Ein bash -euc-Heredoc in meson.build dupliziert sich über Vorlagen und ist schwer zu debuggen. Der Vertrag ist `zfr translate --sync` (Python) von run_target('posync') verdrahtet, kein Inline-Heredoc.


### Nutzen

Ein Befehl synchronisiert xgettext/msgmerge lokal; ninja posync bleibt kurz; CI kann `zfr translate --sync` aufrufen oder `translate.sync` importieren.


### Solve

Ize schreibt run_target('posync') um, damit translate --sync über den Projekt-Python-Einstieg aufgerufen wird (import-first in zfr). Danach POTFILES und Sprachflags prüfen.
""",
        "fr": """\
Quand po/ existe, meson.run_target('posync') doit appeler scripts/posync.sh plutôt qu'un heredoc bash -euc en ligne. Lancez `zfr ize` pour extraire.

### Un posync en ligne est immaintenable

Un heredoc bash -euc dans meson.build se duplique entre modèles et est pénible à déboguer. Le contrat est `zfr translate --sync` (Python) câblé depuis run_target('posync'), pas un heredoc en ligne.


### Gain

Une commande synchronise xgettext/msgmerge localement ; ninja posync reste court ; la CI peut appeler `zfr translate --sync` ou importer `translate.sync`.


### Solve

Ize réécrit run_target('posync') pour invoquer translate --sync via l'entrée Python du projet (import d'abord dans zfr). Vérifiez ensuite POTFILES et les drapeaux de langue.
""",
        "ko": """\
po/가 있으면 meson.run_target('posync')는 인라인 bash -euc heredoc이 아니라 scripts/posync.sh를 호출해야 합니다. 추출하려면 `zfr ize`를 실행하세요.

### 인라인 posync는 유지 불가합니다

meson.build 안의 bash -euc heredoc은 템플릿마다 중복되고 디버그가 고통스럽습니다. 계약은 run_target('posync')에서 연결된 `zfr translate --sync`(Python)이며, 인라인 heredoc이 아닙니다.


### 이득

한 명령으로 xgettext/msgmerge를 로컬 동기화; ninja posync는 짧게 유지; CI는 `zfr translate --sync`를 호출하거나 `translate.sync`를 import할 수 있습니다.


### Solve

Ize는 run_target('posync')를 프로젝트 Python 진입점을 통해 translate --sync를 호출하도록 다시 씁니다(zfr 안에서는 import 우선). 이후 POTFILES와 언어 플래그를 확인하세요.
""",
        "it": """\
Quando esiste po/, meson.run_target('posync') deve chiamare scripts/posync.sh invece di un heredoc bash -euc in linea. Eseguite `zfr ize` per estrarre.

### Un posync in linea è immantenibile

Un heredoc bash -euc in meson.build si duplica tra i template ed è doloroso da debuggare. Il contratto è `zfr translate --sync` (Python) collegato da run_target('posync'), non un heredoc in linea.


### Guadagno

Un comando sincronizza xgettext/msgmerge in locale; ninja posync resta breve; la CI può chiamare `zfr translate --sync` o importare `translate.sync`.


### Solve

Ize riscrive run_target('posync') per invocare translate --sync tramite l'ingresso Python del progetto (import-first in zfr). Verificate poi POTFILES e i flag di lingua.
""",
        "ar": """\
عند وجود po/ يجب أن يستدعي meson.run_target('posync') ملف scripts/posync.sh بدل heredoc لـ bash -euc مضمّن. شغّل `zfr ize` للاستخراج.

### posync المضمّن غير قابل للصيانة

heredoc لـ bash -euc داخل meson.build يتكرر عبر القوالب ويصعب تصحيحه. العقد هو `zfr translate --sync` (Python) موصول من run_target('posync')، لا heredoc مضمّن.


### العائد

أمر واحد يزامن xgettext/msgmerge محليًا؛ يبقى ninja posync قصيرًا؛ يمكن لـ CI استدعاء `zfr translate --sync` أو استيراد `translate.sync`.


### Solve

Ize يعيد كتابة run_target('posync') لاستدعاء translate --sync عبر مدخل Python للمشروع (استيراد أولًا داخل zfr). تحقق بعد ذلك من POTFILES وأعلام اللغة.
""",
    },
    "06f24437da6f": {
        "zh_CN": """\
根级 *.sh 辅助与 look / install-symlinks / uninstall-symlinks / posync / deploy 的 meson run_target 体应放在 scripts/。运行 `zfr ize` 以移动并重新接线。

### 维护脚本属于 scripts/

仓库根的 install-symlinks / deploy 辅助会搅乱打包表面。Zephyr 把它们放在 scripts/。目录同步与 DESTDIR 预览尽量用 `zfr translate --sync` 与 `zfr build --look`，而非定制 posync.sh/look.sh。


### 检测

标记根级维护用 *.sh 名称，以及应外置或改用 zfr 子命令的内联 run_target 体。


### 移动之后

更新文档以及调用旧路径的 CI。Solve 将 Meson run_target 重写到 scripts/… 或 zfr translate/build。
""",
        "zh_TW": """\
根級 *.sh 輔助與 look / install-symlinks / uninstall-symlinks / posync / deploy 的 meson run_target 體應放在 scripts/。執行 `zfr ize` 以移動並重新接線。

### 維護腳本屬於 scripts/

倉庫根的 install-symlinks / deploy 輔助會攪亂打包表面。Zephyr 把它們放在 scripts/。目錄同步與 DESTDIR 預覽盡量用 `zfr translate --sync` 與 `zfr build --look`，而非自訂 posync.sh/look.sh。


### 偵測

標記根級維護用 *.sh 名稱，以及應外置或改用 zfr 子命令的內聯 run_target 體。


### 移動之後

更新文件以及呼叫舊路徑的 CI。Solve 將 Meson run_target 重寫到 scripts/… 或 zfr translate/build。
""",
        "ja": """\
ルートの *.sh ヘルパーと look / install-symlinks / uninstall-symlinks / posync / deploy の meson run_target 本体は scripts/ に置きます。移動と再配線には `zfr ize`。

### メンテ用スクリプトは scripts/ 配下

リポジトリ根の install-symlinks / deploy ヘルパーはパッケージング表面を散らかします。Zephyr はそれらを scripts/ に置きます。カタログ同期と DESTDIR プレビューは可能なら専用 posync.sh/look.sh ではなく `zfr translate --sync` と `zfr build --look`。


### 検出

ルートのメンテ用 *.sh 名と、外出しまたは zfr サブコマンドへの置換が必要なインライン run_target 本体にフラグを立てます。


### 移動後

ドキュメントと旧パスを呼ぶ CI を更新。Solve は Meson run_target を scripts/… または zfr translate/build へ書き換えます。
""",
        "de": """\
Root-*.sh-Helfer und meson-run_target-Körper für look / install-symlinks / uninstall-symlinks / posync / deploy gehören nach scripts/. Mit `zfr ize` verschieben und neu verdrahten.

### Wartungsskripte gehören unter scripts/

install-symlinks-/deploy-Helfer an der Repo-Wurzel vermüllen die Packaging-Oberfläche. Zephyr hält sie unter scripts/. Katalog-Sync und DESTDIR-Vorschau sind `zfr translate --sync` und `zfr build --look` statt eigener posync.sh/look.sh, wenn möglich.


### Erkennung

Markiert Root-*.sh-Wartungsnamen und Inline-run_target-Körper, die ausgelagert oder durch zfr-Unterbefehle ersetzt werden sollen.


### Nach dem Verschieben

Docs und CI aktualisieren, die alte Pfade riefen. Solve schreibt Meson-run_targets nach scripts/… oder zfr translate/build um.
""",
        "fr": """\
Les aides *.sh à la racine et les corps meson run_target pour look / install-symlinks / uninstall-symlinks / posync / deploy appartiennent à scripts/. Lancez `zfr ize` pour déplacer et recâbler.

### Les scripts de maintenance appartiennent sous scripts/

Les aides install-symlinks / deploy à la racine du dépôt encombrent la surface de packaging. Zephyr les garde sous scripts/. La sync de catalogues et l'aperçu DESTDIR sont `zfr translate --sync` et `zfr build --look` plutôt que des posync.sh/look.sh sur mesure quand c'est possible.


### Détection

Signale les noms *.sh de maintenance à la racine et les corps run_target en ligne à externaliser ou remplacer par des sous-commandes zfr.


### Après le déplacement

Mettez à jour la doc et toute CI qui appelait les anciens chemins. Solve réécrit les run_targets Meson vers scripts/… ou zfr translate/build.
""",
        "ko": """\
루트 수준 *.sh 헬퍼와 look / install-symlinks / uninstall-symlinks / posync / deploy용 meson run_target 본문은 scripts/에 있어야 합니다. 옮기고 다시 연결하려면 `zfr ize`를 실행하세요.

### 유지보수 스크립트는 scripts/ 아래

저장소 루트의 install-symlinks / deploy 헬퍼는 패키징 표면을 어지럽힙니다. Zephyr는 그것들을 scripts/에 둡니다. 카탈로그 동기화와 DESTDIR 미리보기는 가능하면 맞춤 posync.sh/look.sh 대신 `zfr translate --sync`와 `zfr build --look`입니다.


### 탐지

루트 *.sh 유지보수 이름과 외부화하거나 zfr 하위 명령으로 바꿔야 할 인라인 run_target 본문에 표시합니다.


### 이동 후

문서와 옛 경로를 호출하던 CI를 갱신하세요. Solve는 Meson run_target을 scripts/… 또는 zfr translate/build로 다시 씁니다.
""",
        "it": """\
Gli helper *.sh a radice e i corpi meson run_target per look / install-symlinks / uninstall-symlinks / posync / deploy appartengono in scripts/. Eseguite `zfr ize` per spostare e ricollegare.

### Gli script di manutenzione stanno sotto scripts/

Gli helper install-symlinks / deploy alla radice del repo ingombrano la superficie di packaging. Zephyr li tiene sotto scripts/. Sync del catalogo e anteprima DESTDIR sono `zfr translate --sync` e `zfr build --look` invece di posync.sh/look.sh su misura quando possibile.


### Rilevamento

Segnala nomi *.sh di manutenzione a radice e corpi run_target in linea da esternalizzare o sostituire con sottocomandi zfr.


### Dopo lo spostamento

Aggiornate docs e ogni CI che chiamava i vecchi percorsi. Solve riscrive i run_target Meson verso scripts/… o zfr translate/build.
""",
        "ar": """\
مساعدات *.sh على الجذر وأجسام meson run_target لـ look / install-symlinks / uninstall-symlinks / posync / deploy تنتمي إلى scripts/. شغّل `zfr ize` للنقل وإعادة التوصيل.

### سكربتات الصيانة تحت scripts/

مساعدات install-symlinks / deploy على جذر المستودع تشوّش سطح التعبئة. يبقيها Zephyr تحت scripts/. مزامنة الكتالوج ومعاينة DESTDIR هما `zfr translate --sync` و `zfr build --look` بدل posync.sh/look.sh المخصّصة عند الإمكان.


### الاكتشاف

يعلّم أسماء *.sh للصيانة على الجذر وأجسام run_target المضمّنة التي يجب إخراجها أو استبدالها بأوامر zfr الفرعية.


### بعد النقل

حدّث الوثائق وأي CI استدعى المسارات القديمة. Solve يعيد كتابة أهداف Meson run_target إلى scripts/… أو zfr translate/build.
""",
    },
}
BODIES.update(_PLAIN)
del _PLAIN


_MORE2 = {
    "4ff43a5e0225": {loc: _rule_card(loc) for loc in LOCALES},
    "8f3e26b0fb48": {
        "zh_CN": _rule_card("zh_CN", """当把 debian/control 的 Build-Depends 转成 rpmbuild 时，按经验映射：bash-builtins → bash（提供 bash.pc）。仅 RPM 的源码调整放在 packaging/rpm/*.patch，用 PatchN + %autosetup/%patch 应用（build-rpm 复制到 SOURCES）；不要在容器里改动系统 .pc 文件。
"""),
        "zh_TW": _rule_card("zh_TW", """當把 debian/control 的 Build-Depends 轉成 rpmbuild 時，按經驗對應：bash-builtins → bash（提供 bash.pc）。僅 RPM 的原始碼調整放在 packaging/rpm/*.patch，用 PatchN + %autosetup/%patch 套用（build-rpm 複製到 SOURCES）；不要在容器裡改動系統 .pc 檔。
"""),
        "ja": _rule_card("ja", """debian/control の Build-Depends を rpmbuild に写すときは経験的マッピングを適用：bash-builtins → bash（bash.pc を同梱）。RPM 専用のソース調整は packaging/rpm/*.patch に置き、PatchN + %autosetup/%patch で適用（build-rpm が SOURCES へコピー）；コンテナ内でシステムの .pc を書き換えない。
"""),
        "de": _rule_card("de", """Beim Übersetzen von debian/control Build-Depends nach rpmbuild Erfahrungs-Mappings anwenden: bash-builtins → bash (liefert bash.pc). RPM-only-Quellanpassungen liegen in packaging/rpm/*.patch und werden mit PatchN + %autosetup/%patch angewendet (build-rpm kopiert nach SOURCES); System-.pc-Dateien im Container nicht mutieren.
"""),
        "fr": _rule_card("fr", """En traduisant les Build-Depends de debian/control vers rpmbuild, appliquez des correspondances empiriques : bash-builtins → bash (fournit bash.pc). Les ajustements de sources RPM-only vivent dans packaging/rpm/*.patch et s'appliquent avec PatchN + %autosetup/%patch (build-rpm les copie vers SOURCES) ; ne mutilez pas les .pc système dans le conteneur.
"""),
        "ko": _rule_card("ko", """debian/control의 Build-Depends를 rpmbuild로 옮길 때 경험적 매핑을 적용하세요: bash-builtins → bash(bash.pc 제공). RPM 전용 소스 조정은 packaging/rpm/*.patch에 두고 PatchN + %autosetup/%patch로 적용합니다(build-rpm이 SOURCES로 복사); 컨테이너에서 시스템 .pc 파일을 바꾸지 마세요.
"""),
        "it": _rule_card("it", """Nel tradurre i Build-Depends di debian/control in rpmbuild, applicate mappature empiriche: bash-builtins → bash (fornisce bash.pc). Le modifiche sorgente solo-RPM vivono in packaging/rpm/*.patch e si applicano con PatchN + %autosetup/%patch (build-rpm le copia in SOURCES); non mutate i .pc di sistema nel contenitore.
"""),
        "ar": _rule_card("ar", """عند تحويل Build-Depends من debian/control إلى rpmbuild، طبّق تعيينات تجريبية: bash-builtins → bash (يوفّر bash.pc). تعديلات المصدر الخاصة بـ RPM فقط تعيش في packaging/rpm/*.patch وتُطبَّق بـ PatchN + %autosetup/%patch (build-rpm ينسخها إلى SOURCES)؛ لا تُغيّر ملفات .pc النظام في الحاوية.
"""),
    },
    "eb3debe31053": {
        "zh_CN": _rule_card("zh_CN", """期望 .github/workflows/release-packages.yml 在 release published 时触发，并有 scripts/ci 辅助脚本。对等依赖使用 scripts/ci/deps.conf 与仅安装式拉取（绝不要嵌套构建）。Apt 组件为 main。
"""),
        "zh_TW": _rule_card("zh_TW", """期望 .github/workflows/release-packages.yml 在 release published 時觸發，並有 scripts/ci 輔助腳本。對等相依使用 scripts/ci/deps.conf 與僅安裝式拉取（絕不要巢狀建置）。Apt 元件為 main。
"""),
        "ja": _rule_card("ja", """release published で起動する .github/workflows/release-packages.yml と scripts/ci ヘルパーを期待します。ピア依存は scripts/ci/deps.conf とインストール専用フェッチ（ネストビルド禁止）。Apt コンポーネントは main。
"""),
        "de": _rule_card("de", """Erwartet .github/workflows/release-packages.yml ausgelöst bei release published, plus scripts/ci-Helfer. Peer-Deps nutzen scripts/ci/deps.conf und Install-only-Fetch (nie Nested-Build). Apt-Komponente ist main.
"""),
        "fr": _rule_card("fr", """Attendez .github/workflows/release-packages.yml déclenché sur release published, plus des aides scripts/ci. Les dépendances paires utilisent scripts/ci/deps.conf et un fetch install-only (jamais de nested-build). Le composant Apt est main.
"""),
        "ko": _rule_card("ko", """.github/workflows/release-packages.yml이 release published에서 트리거되고 scripts/ci 헬퍼가 있기를 기대합니다. 피어 의존성은 scripts/ci/deps.conf와 설치 전용 fetch를 씁니다(중첩 빌드 금지). Apt 컴포넌트는 main입니다.
"""),
        "it": _rule_card("it", """Aspettatevi .github/workflows/release-packages.yml attivato su release published, più helper in scripts/ci. Le peer dep usano scripts/ci/deps.conf e fetch solo-installazione (mai nested-build). Il componente Apt è main.
"""),
        "ar": _rule_card("ar", """توقّع .github/workflows/release-packages.yml يُطلق عند release published، مع مساعدات scripts/ci. تبعيات النظراء تستخدم scripts/ci/deps.conf وجلب تثبيت فقط (لا بناء متداخل أبدًا). مكوّن Apt هو main.
"""),
    },
    "f26cab8526d2": {
        "zh_CN": _rule_card("zh_CN", """Debian armhf 使用 linux/arm/v7；raspi_* 使用 linux/arm/v6。loong64 仅用于 uos_*/kylin_*。Ubuntu 可能增加 i386/amd64v3；另有 mingw/cygwin 矩阵段用于 Windows 原生构建。
"""),
        "zh_TW": _rule_card("zh_TW", """Debian armhf 使用 linux/arm/v7；raspi_* 使用 linux/arm/v6。loong64 僅用於 uos_*/kylin_*。Ubuntu 可能增加 i386/amd64v3；另有 mingw/cygwin 矩陣段用於 Windows 原生建置。
"""),
        "ja": _rule_card("ja", """Debian armhf は linux/arm/v7；raspi_* は linux/arm/v6。loong64 は uos_*/kylin_* のみ。Ubuntu は i386/amd64v3 を足すことがあり、Windows ネイティブ向けに mingw/cygwin 行列セクションもあります。
"""),
        "de": _rule_card("de", """Debian armhf nutzt linux/arm/v7; raspi_* nutzt linux/arm/v6. loong64 nur für uos_*/kylin_*. Ubuntu kann i386/amd64v3 ergänzen; außerdem mingw/cygwin-Matrixabschnitte für native Windows-Builds.
"""),
        "fr": _rule_card("fr", """Debian armhf utilise linux/arm/v7 ; raspi_* utilise linux/arm/v6. loong64 seulement pour uos_*/kylin_*. Ubuntu peut ajouter i386/amd64v3 ; aussi des sections de matrice mingw/cygwin pour les builds natifs Windows.
"""),
        "ko": _rule_card("ko", """Debian armhf는 linux/arm/v7을 쓰고; raspi_*는 linux/arm/v6을 씁니다. loong64는 uos_*/kylin_*만. Ubuntu는 i386/amd64v3를 추가할 수 있고; Windows 네이티브 빌드용 mingw/cygwin 매트릭스 섹션도 있습니다.
"""),
        "it": _rule_card("it", """Debian armhf usa linux/arm/v7; raspi_* usa linux/arm/v6. loong64 solo per uos_*/kylin_*. Ubuntu può aggiungere i386/amd64v3; anche sezioni di matrice mingw/cygwin per build nativi Windows.
"""),
        "ar": _rule_card("ar", """Debian armhf يستخدم linux/arm/v7؛ raspi_* يستخدم linux/arm/v6. loong64 فقط لـ uos_*/kylin_*. قد يضيف Ubuntu i386/amd64v3؛ وأيضًا أقسام مصفوفة mingw/cygwin لبناءات Windows الأصلية.
"""),
    },
}
BODIES.update(_MORE2)
del _MORE2

