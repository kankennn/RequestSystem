from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageTemplate,
    Paragraph,
    PageBreak,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "pdf"
FONT_DIR = Path("C:/Windows/Fonts")
FONT = FONT_DIR / "arial.ttf"
FONT_BOLD = FONT_DIR / "arialbd.ttf"

pdfmetrics.registerFont(TTFont("Arial", str(FONT)))
pdfmetrics.registerFont(TTFont("Arial-Bold", str(FONT_BOLD)))

NAVY = colors.HexColor("#17324D")
BLUE = colors.HexColor("#2374AB")
PALE = colors.HexColor("#EAF1F7")
INK = colors.HexColor("#25313B")
MUTED = colors.HexColor("#657482")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="CoverTitle", fontName="Arial-Bold", fontSize=23, leading=29,
    textColor=NAVY, alignment=TA_CENTER, spaceAfter=8 * mm,
))
styles.add(ParagraphStyle(
    name="CoverSub", fontName="Arial", fontSize=12, leading=18,
    textColor=MUTED, alignment=TA_CENTER, spaceAfter=5 * mm,
))
styles.add(ParagraphStyle(
    name="Section", fontName="Arial-Bold", fontSize=15, leading=20,
    textColor=NAVY, spaceBefore=5 * mm, spaceAfter=3 * mm, keepWithNext=True,
))
styles.add(ParagraphStyle(
    name="Subsection", fontName="Arial-Bold", fontSize=11, leading=15,
    textColor=BLUE, spaceBefore=3 * mm, spaceAfter=2 * mm, keepWithNext=True,
))
styles.add(ParagraphStyle(
    name="BodyRu", fontName="Arial", fontSize=9.2, leading=13.2,
    textColor=INK, spaceAfter=2.4 * mm,
))
styles.add(ParagraphStyle(
    name="Small", fontName="Arial", fontSize=8, leading=10.5,
    textColor=INK,
))
styles.add(ParagraphStyle(
    name="TableHead", fontName="Arial-Bold", fontSize=8, leading=10,
    textColor=colors.white,
))
styles.add(ParagraphStyle(
    name="Label", fontName="Arial-Bold", fontSize=8.4, leading=11.3,
    textColor=NAVY,
))
styles.add(ParagraphStyle(
    name="Footer", fontName="Arial", fontSize=7.5, leading=9,
    textColor=MUTED,
))


def para(text, style="BodyRu"):
    return Paragraph(text, styles[style])


def header_footer(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(colors.HexColor("#D9E2EA"))
    canvas.setLineWidth(0.5)
    canvas.line(18 * mm, height - 16 * mm, width - 18 * mm, height - 16 * mm)
    canvas.setFont("Arial", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, height - 12.5 * mm, "СИСТЕМА УЧЁТА ЗАЯВОК  |  ТЕХНОЛОГИИ РАЗРАБОТКИ ПО")
    canvas.line(18 * mm, 14 * mm, width - 18 * mm, 14 * mm)
    canvas.drawString(18 * mm, 9.5 * mm, doc.subject_label)
    canvas.drawRightString(width - 18 * mm, 9.5 * mm, f"Стр. {doc.page}")
    canvas.restoreState()


def make_doc(path, title):
    doc = BaseDocTemplate(
        str(path), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=22 * mm, bottomMargin=20 * mm, title=title,
        author="Дельянов Радислав",
    )
    doc.subject_label = title
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="standard", frames=[frame], onPage=header_footer)])
    return doc


def make_cover(labs, description):
    return [
        Spacer(1, 38 * mm),
        para("ОТЧЁТ", "CoverTitle"),
        para(f"Лабораторные работы {labs}", "CoverTitle"),
        Spacer(1, 5 * mm),
        para("Система учёта заявок", "CoverSub"),
        para(description, "CoverSub"),
        Spacer(1, 26 * mm),
        para("<b>Дисциплина:</b> Технологии разработки программного обеспечения", "BodyRu"),
        para("<b>Студент:</b> Дельянов Радислав", "BodyRu"),
        para("<b>Группа:</b> ______________________________", "BodyRu"),
        para("<b>Дата:</b> 11 октября 2026 г.", "BodyRu"),
        Spacer(1, 18 * mm),
        para("Материалы подготовлены на основе проекта и проверок, перечисленных в отчёте. "
             "Публичное развёртывание пропущено по решению студента.", "Small"),
        PageBreak(),
    ]


def cover(labs, description):
    return make_cover(labs, description)


def heading(text):
    return para(text, "Section")


def subheading(text):
    return para(text, "Subsection")


def bullets(items):
    return [para("•&nbsp;&nbsp;" + item) for item in items]


def lab5_report():
    story = cover("№ 5", "Проектирование реляционной модели и реализация схемы SQLite")
    story += [
        heading("1. Цель и постановка задачи"),
        para("Цель работы — спроектировать реляционную модель данных для системы учёта заявок, "
             "определить сущности, ключи, связи и ограничения целостности, а затем проверить "
             "схему на SQLite."),
        PageBreak(),
        heading("2. Сущности и назначение"),
    ]
    rows = [
        [para("Сущность", "TableHead"), para("Назначение и связи", "TableHead")],
        [para("<b>users</b>", "Small"), para("Пользователи; заявители, исполнители, авторы комментариев и инициаторы изменений.", "Small")],
        [para("<b>categories</b>", "Small"), para("Справочник категорий; одна категория может относиться к нескольким заявкам.", "Small")],
        [para("<b>statuses</b>", "Small"), para("Справочник статусов; один статус может быть у многих заявок.", "Small")],
        [para("<b>requests</b>", "Small"), para("Заявка со ссылками на категорию, статус, заявителя и необязательного исполнителя.", "Small")],
        [para("<b>comments</b>", "Small"), para("Сообщения по заявке с автором и временем создания.", "Small")],
        [para("<b>request_history</b>", "Small"), para("Аудит изменений: заявка, автор, поле, старое/новое значение и время.", "Small")],
    ]
    table = Table(rows, colWidths=[42 * mm, 132 * mm], repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D4DEE7")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story += [table, heading("3. Ключи, связи и ограничения")]
    story += bullets([
        "Первичные ключи — целочисленные автоинкрементные идентификаторы.",
        "Внешние ключи связывают заявки со справочниками и пользователями, комментарии и аудит — с заявками и авторами.",
        "Email и названия категорий уникальны без учёта регистра.",
        "CHECK-ограничения контролируют роли, длины текстовых полей, приоритеты и булевы флаги.",
        "Индексы созданы для фильтрации заявок по статусу, категории и дате.",
        "В приложении заявка удаляется мягко: архивирование сохраняет историю и комментарии.",
    ])
    story += [
        heading("4. Реализация"),
        para("SQL DDL вынесен в <b>docs/database/schema.sql</b>, ER-модель — в "
             "<b>docs/database/er-diagram.mmd</b>. Приложение использует согласованную схему "
             "в <b>app/db.py</b>, включает внешние ключи и идемпотентную инициализацию "
             "демонстрационных данных."),
        heading("5. Проверка"),
        para("DDL выполнен на чистом SQLite-соединении. Созданы шесть таблиц; "
             "<font name='Arial-Bold'>PRAGMA foreign_key_check</font> не выявил нарушений. "
             "Попытка вставить заявку со ссылкой на отсутствующую категорию завершилась "
             "ожидаемой ошибкой целостности."),
        heading("6. Вывод и ограничения"),
        para("Подготовлена воспроизводимая реляционная модель, соответствующая предметной "
             "области и прикладной схеме. Ролевая авторизация и аутентификация остаются вне "
             "учебной демонстрационной реализации; прямые SQL-изменения не записываются в аудит."),
        subheading("Материалы"),
        para("ER-модель: docs/database/er-diagram.mmd. SQL: docs/database/schema.sql. "
             "Инициализация: app/db.py."),
    ]
    return story


def lab68_report():
    story = cover("№ 6–8", "Реализация функциональности, REST API и локальная контейнеризация")
    story += [
        heading("Лабораторная № 6. Разработка функционала"),
        para("Реализовано приложение FastAPI поверх SQLite. Слои схем, репозитория и "
             "бизнес-правил разделены; стартовая база содержит 4 пользователя, 4 категории, "
             "4 статуса и 10 демонстрационных заявок."),
    ]
    rows = [
        [para("Возможность", "TableHead"), para("Реализация и проверка", "TableHead")],
        [para("CRUD и архив", "Small"), para("Создание, получение, изменение и мягкое архивирование заявок.", "Small")],
        [para("Поиск и фильтры", "Small"), para("Поиск текста/ID; фильтрация по статусу, категории и приоритету.", "Small")],
        [para("Правила статусов", "Small"), para("Сервисный слой проверяет допустимость перехода.", "Small")],
        [para("Ошибки/валидация", "Small"), para("Pydantic и единый JSON-формат ответов 404/422/500.", "Small")],
        [para("Автотесты", "Small"), para("4 API-теста: справочники, создание/поиск, валидация, статусы и архив.", "Small")],
    ]
    table = Table(rows, colWidths=[45 * mm, 129 * mm], repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D4DEE7")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story += [table, PageBreak(), heading("Лабораторная № 7. REST API")]
    story += bullets([
        "OpenAPI/Swagger доступен через /docs, JSON-контракт — через /openapi.json.",
        "API предоставляет операции заявок, справочники пользователей/статусов/категорий, комментарии и health-check.",
        "Примеры запросов и Postman-коллекция находятся в docs/requests.http и docs/postman_collection.json.",
    ])
    story += [
        heading("Лабораторная № 8. Docker и локальный запуск"),
        para("11 октября 2026 г. пользователь собрал образ и запустил Compose-композицию "
             "в Docker Desktop. По предоставленным скриншотам контейнер достиг состояния "
             "<b>healthy</b>, порт 8000 опубликован на localhost, запрос к "
             "<b>http://localhost:8000/health</b> вернул <b>status=ok</b> и <b>database=ok</b>."),
        para("Публичный/удалённый деплой намеренно пропущен по решению студента; сервер, "
             "внешний URL и проверка доступности из интернета отсутствуют."),
        heading("Запуск и проверка"),
        para("<b>docker compose up --build -d</b><br/>"
             "<b>docker compose ps</b><br/>"
             "<b>Invoke-RestMethod http://localhost:8000/health</b><br/>"
             "Автотесты: <b>python -m pytest -q</b>."),
        heading("Вывод и известные ограничения"),
        para("Функциональность, REST API и локальный контейнер подготовлены. "
             "Перед публичным использованием необходимы аутентификация/авторизация, HTTPS, "
             "резервное копирование и миграции. Удалённое развёртывание не входит в выполненный объём."),
    ]
    return story


def log_record(title, date, task, model, prompts, context, result, verification, changes, choice):
    story = [
        heading(title),
        para(f"<b>Дата / этап:</b> {date}"),
        para(f"<b>Задача:</b> {task}"),
        para(f"<b>Модель:</b> {model}"),
    ]
    for label, text in prompts:
        story += [subheading(label), para(text)]
    for label, text in [
        ("Контекст", context), ("Результат", result), ("Проверка", verification),
        ("Доработка / решение студента", changes), ("Почему выбран такой подход", choice),
    ]:
        story += [subheading(label), para(text)]
    return story


def ai_journal():
    story = make_cover("№ 5–8", "Журнал применения ИИ: проектирование, ревью и проверка")
    story += [
        para("Журнал фиксирует рабочие запросы и результаты в проекте. Внешние диалоги "
             "не экспортировались; записи ниже описывают взаимодействия в Codex и "
             "проверки, фактически выполненные в репозитории.", "BodyRu"),
        heading("Лабораторная № 5"),
    ]
    story += log_record(
        "Проектирование модели данных",
        "11 октября 2026 г., анализ предметной области",
        "Сопоставить сущности системы заявок с реляционными таблицами и определить связи/ограничения.",
        "Codex — модель/версия не указаны интерфейсом",
        [
            ("Запрос 1 - проектирование", "«По ТЗ системы учёта заявок предложи нормализованную реляционную модель для пользователей, заявок, категорий, статусов, комментариев и аудита. Укажи PK/FK, обязательность связей, уникальность и CHECK-ограничения. Сохрани учебную простоту и перечисли допущения»."),
            ("Запрос 2 - проверка согласованности", "«Сверь ER-модель и SQLite DDL с существующим app/db.py. Найди расхождения таблиц, типов связей, ограничений и индексов. Не утверждай, что схема корректна, пока не предложишь проверяемые SQLite-инварианты»."),
        ],
        "ТЗ docs/TZ.md, существующие app/db.py и структура проекта; передавались только учебные сущности.",
        "За основу приняты шесть сущностей: users, categories, statuses, requests, comments и request_history; схема вынесена в DDL и ER-диаграмму.",
        "DDL исполнен в SQLite in-memory; проверены таблицы, PRAGMA foreign_key_check и отклонение некорректного внешнего ключа.",
        "Схема сопоставлена с приложением; мягкое архивирование оставлено как поведение API, а не физическое удаление.",
        "Контекстное проектирование полезнее общего SQL-ответа; окончательное решение проверено исполняемой СУБД.",
    )
    story += [PageBreak(), heading("Лабораторная № 6")]
    story += log_record(
        "Планирование функциональности и ревью сервисного слоя",
        "10 октября 2026 г., реализация",
        "Разложить CRUD, статусы, поиск, валидацию и архивирование по слоям.",
        "Codex — модель/версия не указаны интерфейсом",
        [
            ("Первый запрос", "«Сделай CRUD заявок на Python»."),
            ("Недостатки первого запроса", "Не заданы проект, роли, SQLite, сервисный слой, правила статусов, формат ошибок и критерии проверки; ответ мог бы быть слишком общим."),
            ("Уточнённый запрос", "«Выступи разработчиком существующего Python-проекта “Система учёта заявок”. Составь план CRUD заявки с SQLite и repository/service слоями, обязательными полями, поиском, фильтрами, назначением исполнителя, мягким удалением и допустимыми переходами статуса. Не добавляй реальные секреты; выдай задачи и критерии проверки»."),
            ("Запрос ревью", "«Проверь сервисные правила переходов статусов и валидацию заявок по ТЗ. Найди обход бизнес-правил, некорректные ссылки и ошибки API; каждое замечание подкрепи конкретным тестом»."),
        ],
        "ТЗ, архитектурное описание, app/db.py, repository.py, services.py, schemas.py.",
        "Сформированы разделение DB/repository/service, ограничения данных, статусные переходы и тестовые данные.",
        "Реализация сопоставлена с требованиями; сценарии API вошли в tests/test_api.py. Четыре теста ранее прошли локально.",
        "Приняты мягкое архивирование, история и явные переходы; рекомендации проверялись в коде, а не копировались безусловно.",
        "Контекст проекта и тестируемые критерии сокращают риск получить посторонний каркас вместо продолжения существующей системы.",
    )
    story += [PageBreak(), heading("Лабораторная № 7")]
    story += log_record(
        "Проектирование и критический разбор REST API",
        "10 октября 2026 г., проектирование API",
        "Определить маршруты заявок и справочников, JSON-схемы, HTTP-коды, фильтры и формат ошибок.",
        "Codex — модель/версия не указаны интерфейсом",
        [
            ("Запрос проектирования", "«Предложи REST-контракт для Request в FastAPI: список/карточка, POST, PATCH, DELETE/archive, справочники users/statuses/categories, фильтры q/status/category/priority, Pydantic-валидация и коды 200/201/204/404/422. Отдели endpoint от service и не включай реальные секреты»."),
            ("Запрос ревью", "«Критически проверь API-контракт: обязательные поля, диапазоны, HTTP-коды, единообразие ошибок, безопасность и отсутствие дублирования бизнес-логики. Для каждого замечания предложи способ воспроизводимой проверки»."),
        ],
        "app/main.py, app/schemas.py, требования ЛР № 7; демонстрационные идентификаторы.",
        "Подготовлены CRUD endpoint-ы, справочники, фильтры, OpenAPI и единый формат ошибок.",
        "docs/requests.http и Postman collection содержат сценарии успешных и ошибочных запросов; автотесты проверяют ключевые API-пути.",
        "Оставлены ошибки 404/422 по смыслу операции; DELETE выполняет мягкое архивирование; аутентификация честно указана как ограничение.",
        "Раздельный запрос проектирования и критического ревью позволяет проверить контракт с разных сторон.",
    )
    story += [PageBreak(), heading("Лабораторная № 8")]
    story += log_record(
        "Docker-конфигурация и локальный контейнер",
        "10–11 октября 2026 г., подготовка и ручная проверка",
        "Подготовить повторяемый Docker-запуск и проверить пользователя контейнера, контекст сборки, порт, секреты и health-check.",
        "Codex — модель/версия не указаны интерфейсом",
        [
            ("Запрос генерации", "«Предложи Dockerfile для Python 3.12 FastAPI + SQLite: app/main.py, requirements.txt и prototype, запуск на 8000, настройки через окружение и /health. Исключи секреты, локальную БД и виртуальное окружение из build context»."),
            ("Запрос ревью", "«Проведи ревью Dockerfile и Compose: права процесса, базовый образ, слой зависимостей, контекст, volume SQLite, согласованность портов, отсутствие обязательного несуществующего .env и работоспособность health-check. Предложи минимальные исправления»."),
        ],
        "Dockerfile, .dockerignore, docker-compose.yml, .env.example; секреты и реальные пользовательские данные не передавались.",
        "Образ Python 3.12 slim, непривилегированный пользователь, Compose volume и health-check. Compose изменён так, чтобы локальный запуск не требовал отсутствующий .env.",
        "По скриншотам пользователя 11.10.2026 образ собран, контейнер healthy, localhost:8000 опубликован; /health вернул status=ok и database=ok. Удалённый сервер не проверялся.",
        "Учтены пути COPY и изоляция данных; выбран локальный Docker-деплой. Публичный деплой пропускается по решению студента.",
        "Ограниченный контекст и проверка запуском отделяют полезные инфраструктурные предложения от общих шаблонов; модель выбрана как помощник для технического ревью.",
    )
    return story


def ai_lab5_journal():
    story = make_cover("№ 5", "Журнал применения ИИ")
    story += [
        para("Запись составлена по фактической работе над моделью данных в этой сессии. "
             "Экспорт диалога из внешнего сервиса не приложен.", "BodyRu"),
        heading("Проектирование и проверка модели данных"),
    ]
    story += log_record(
        "Лабораторная № 5 - SQLite и ER-модель",
        "11 октября 2026 г., анализ и реализация",
        "Восстановить лабораторную № 5 по методическим материалам и согласовать ER-модель с существующей базой приложения.",
        "Codex — точная модель/версия не отображается в интерфейсе",
        [
            ("Запрос пользователя", "«Да, займусь. ЛР 5 можно сделать на основе ТЗ и существующей модели SQLite; ЛР 8 доведу до локально проверяемого Docker-развёртывания. Публичный деплой на VPS смогу выполнить только при наличии сервера и доступа, поэтому сначала проверю, что доступно в проекте и среде»."),
            ("Рабочий запрос к ИИ", "«Сопоставь ТЗ системы учёта заявок и существующую SQLite-модель. Подготовь набор сущностей, PK/FK, ограничения целостности, ER-диаграмму и воспроизводимый SQL DDL. Укажи допущения и проверки, не выдумывай отсутствующие сведения»."),
            ("Запрос проверки", "«Проверь DDL на чистой SQLite-базе: создание всех таблиц, PRAGMA foreign_key_check и отказ на ссылку к отсутствующей записи. Сверь модель с app/db.py и отметь ограничения реализации»."),
        ],
        "docs/TZ.md, app/db.py и предоставленная методичка лабораторных 6–8. Рассмотрены учебные данные, секретов нет.",
        "Созданы docs/database/schema.sql, docs/database/er-diagram.mmd и docs/REPORT_5.md.",
        "DDL исполнен на временной SQLite-базе; созданы шесть таблиц; внешний ключ проверен нарушающей вставкой и был отклонён.",
        "Модель сверена с действующей схемой приложения; явно указано, что RBAC и аудит прямых SQL-изменений не реализованы.",
        "Для предметной модели применён контекст проекта; модель/версия ИИ в интерфейсе не была видна, поэтому не указана фиктивно.",
    )
    return story


def write_pdf(filename, title, story):
    OUT.mkdir(parents=True, exist_ok=True)
    doc = make_doc(OUT / filename, title)
    doc.build(story)


if __name__ == "__main__":
    write_pdf("REPORT_LAB5.pdf", "Отчёт по лабораторной работе № 5", lab5_report())
    write_pdf("REPORT_LAB6-8.pdf", "Отчёт по лабораторным работам № 6–8", lab68_report())
    write_pdf("AI_LOG_LAB5.pdf", "AI-журнал лабораторной работы № 5", ai_lab5_journal())
    write_pdf("AI_LOG_LAB6-8.pdf", "AI-журнал лабораторных работ № 6–8", ai_journal())
