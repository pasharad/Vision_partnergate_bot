# Partnership Bot — Schema

## Overview

A Persian-language Telegram bot that serves advertising board rental data from an Excel file to whitelisted clients. The data covers billboard pricing, availability status, and rental details across gas stations in Tehran and Mazandaran. All user-facing text is in Persian (فارسی).

---

## 1. Data Model

### Excel File Structure (actual)

**Single sheet:** `shayan_s test` — 195 rows, 17 columns (A–Q)

| Col | Persian Header                    | English              | Example Value                         | Notes                     |
|-----|-----------------------------------|----------------------|---------------------------------------|---------------------------|
| A   | (Do Not Modify) Product           | product_id           | `5da0122f-a247-...`                   | GUID — internal, skip      |
| B   | (Do Not Modify) Row Checksum      | checksum             | `gYwyxE4CsG/...`                     | Internal — skip            |
| C   | (Do Not Modify) Modified On       | modified_on          | `1405/03/22 09:28`                    | Jalali datetime            |
| D   | کد تابلو                          | board_code           | `ab-0`, `am-11`                       | Unique board identifier    |
| E   | جایگاه                            | station              | `عباس آباد`, `امیرآباد`               | Gas station name           |
| F   | وضعیت رزرو قراردادی               | status               | `خالی` or `پر`                        | Available or Occupied      |
| G   | تاریخ پایان رزرو قراردادی         | reservation_end      | `1405/07/21 22:00`                    | Jalali datetime            |
| H   | شهر                               | city                 | `تهران`, `مازندران`                   | City                       |
| I   | شرح تابلو                         | description          | `هدبورد جایگاه عباس آباد`             | Full board name            |
| J   | حالت تابلو                        | mode                 | `افقی` or `عمودی`                     | Horizontal or Vertical     |
| K   | قیمت (ماهیانه)                    | price_monthly        | `2970000000`                          | Monthly price (Rial)       |
| L   | دو ماه                            | price_2month         | `2762100000`                          | 2-month price (Rial)       |
| M   | سه تا پنج ماهه                    | price_3_5month       | `2554200000`                          | 3-5 month price (Rial)     |
| N   | شش تا هشت ماهه                    | price_6_8month       | `2227500000`                          | 6-8 month price (Rial)     |
| O   | مساحت (متر مربع)                  | area_sqm             | `79.2`                                | Board area in m²           |
| P   | قیمت واحد چاپ و نصب              | print_unit_price     | `3700000`                             | Print+install unit (Rial)  |
| Q   | هزینه چاپ و نصب                   | print_total_cost     | `293040000`                           | Print+install total (Rial) |

> **Note:** First data row is "خدمات اضافی" (extra services) with zeroed prices — skip it during parsing.

### Data Statistics

- **Total boards:** 194
- **Statuses:** خالی (available: ~45%), پر (occupied: ~55%)
- **Cities:** تهران (majority), مازندران
- **Board modes:** افقی (horizontal), عمودی (vertical)
- **Unique stations:** 52 gas stations
- **Price range:** 150,000,000 – 4,920,000,000 Rial/month
- **Area range:** 3.76 – 264.40 m²

### In-Memory Data Cache

```python
@dataclass
class DataCache:
    boards:       list[Board]      # All 194 board records
    last_loaded:  datetime
    is_stale:     bool             # True if older than 4 hours
```

---

## 2. User Model

### Whitelist (stored in `whitelist.json`)

```json
{
  "users": [
    {"telegram_id": 123456789, "name": "Ali", "role": "client"},
    {"telegram_id": 987654321, "name": "Admin", "role": "admin"}
  ]
}
```

- **client** — can query data (prices, availability, search)
- **admin** — can also trigger manual reload, manage whitelist

### Access Control Flow

```
User sends /start or any command
        │
        ▼
  Is user in whitelist?
   ├─ NO  → Reply: "دسترسی غیرمجاز. با مدیر تماس بگیرید."
   └─ YES → Proceed to command handler
```

---

## 3. Bot Commands & Persian Messages

### All Users (whitelisted)

| Command         | Button Label          | Description                                      |
|-----------------|-----------------------|--------------------------------------------------|
| `/start`        | —                     | خوشآمدگویی + نمایش منوی اصلی                     |
| `/help`         | راهنما                | لیست دستورات                                     |
| `/available`    | تابلوهای خالی         | نمایش تابلوهای موجود (خالی) با قیمت و جزئیات     |
| `/occupied`     | تابلوهای پر           | نمایش تابلوهای رزرو شده (پر)                     |
| `/prices`       | لیست قیمت‌ها          | جدول کامل قیمت تمام تابلوها                       |
| `/search`       | جستجو                 | جستجو بر اساس جایگاه، شهر، کد تابلو              |
| `/details`      | جزئیات تابلو          | دریافت اطلاعات کامل یک تابلو با کد               |

### Admin Only

| Command              | Description                                     |
|----------------------|-------------------------------------------------|
| `/reload`            | بارگذاری مجدد فایل اکسل                         |
| `/status`            | وضعیت ربات (آخرین بارگذاری، تعداد تابلوها)       |
| `/add_user <id>`     | افزودن کاربر به لیست سفید                        |
| `/remove_user <id>`  | حذف کاربر از لیست سفید                           |

---

## 4. Persian Message Templates

Centralized in `messages.py`:

```python
MESSAGES = {
    "welcome": (
        "سلام! 👋\n"
        "من ربات اطلاعات تابلوهای تبلیغاتی جایگاه‌های سوخت هستم.\n"
        "از منوی زیر اطلاعات مورد نظر خود را انتخاب کنید:"
    ),
    "access_denied": "⛔ دسترسی غیرمجاز.\nشما در لیست کاربران مجاز نیستید.\nبا مدیر تماس بگیرید.",
    "no_data": "اطلاعاتی برای این بخش موجود نیست.",
    "reload_success": "✅ فایل با موفقیت بارگذاری شد.\nتعداد تابلوها: {count}",
    "reload_failed": "❌ خطا در بارگذاری فایل. لطفاً بعداً تلاش کنید.",
    "last_reload": "آخرین بارگذاری: {time}\nتعداد تابلوها: {count}",
    "search_prompt": "🔍 عبارت مورد جستجو را وارد کنید:\n(مثلاً: نام جایگاه، شهر، یا کد تابلو)",
    "no_results": "نتیجه‌ای یافت نشد.",
    "admin_added": "✅ کاربر {id} اضافه شد.",
    "admin_removed": "✅ کاربر {id} حذف شد.",
    "board_detail": (
        "📋 جزئیات تابلو: {code}\n"
        "━━━━━━━━━━━━━━━━━\n"
        "جایگاه: {station}\n"
        "شهر: {city}\n"
        "وضعیت: {status}\n"
        "حالت: {mode}\n"
        "مساحت: {area} متر مربع\n"
        "━━━━━━━━━━━━━━━━━\n"
        "💰 قیمت ماهیانه: {price_monthly}\n"
        "💰 ۲ ماهه: {price_2month}\n"
        "💰 ۳ تا ۵ ماهه: {price_3_5month}\n"
        "💰 ۶ تا ۸ ماهه: {price_6_8month}\n"
        "━━━━━━━━━━━━━━━━━\n"
        "🖨 هزینه چاپ و نصب: {print_cost}\n"
        "📅 تاریخ پایان رزرو: {reservation_end}"
    ),
}
```

### Inline Keyboard Labels

```
Main Menu:
  [ تابلوهای خالی ]   [ تابلوهای پر ]
  [ لیست قیمت‌ها ]     [ جستجو ]

Filters (after tapping a button):
  [ فیلتر: تهران ]   [ فیلتر: مازندران ]
  [ فیلتر: افقی ]    [ فیلتر: عمودی ]
  [ بازگشت به منوی اصلی ]
```

---

## 5. Interaction Flow

```
Client opens bot
        │
        ▼
    /start  ──→  خوشآمدگویی + منوی اصلی
                  [ تابلوهای خالی ]   [ تابلوهای پر ]
                  [ لیست قیمت‌ها ]     [ جستجو ]
        │
        ▼
   Client taps a button
        │
        ▼
   Bot checks cache freshness
   ├─ Fresh (< 4h)  → Serve from memory
   └─ Stale (> 4h)  → Reload Excel, then serve
        │
        ▼
   Bot formats response in Persian
   (Jalali dates, Rial prices with commas, status icons)
        │
        ▼
   Example output for "تابلوهای خالی":
   ┌──────────┬────────────────────┬──────────┬──────────────────┐
   │   کد     │     جایگاه         │   شهر    │   قیمت ماهیانه   │
   ├──────────┼────────────────────┼──────────┼──────────────────┤
   │ ab-0     │ عباس آباد          │ تهران    │ ۲,۹۷۰,۰۰۰,۰۰۰ │
   │ ak-0     │ خلازیر            │ تهران    │   ۶۰۰,۰۰۰,۰۰۰ │
   │ am-12    │ امیرآباد           │ تهران    │   ۹۹۰,۰۰۰,۰۰۰ │
   └──────────┴────────────────────┴──────────┴──────────────────┘
   (paginated — 10 per page with [بعدی] [قبلی] buttons)
        │
        ▼
   Client can:
   ├─ Tap [بعدی] / [قبلی] to navigate pages
   ├─ Tap a board code to see full details
   ├─ Tap another main menu button
   ├─ Tap [جستجو] then type a query
   └─ Tap [بازگشت به منوی اصلی]
```

---

## 6. Formatting Rules

### Prices
- Raw data is in **Rials** — convert to **Tomans** for display (÷10)
- Example: `2,970,000,000 Rial` → `۲۹۷,۰۰۰,۰۰۰ تومان`
- Format with comma separators: `۱۵۰,۰۰۰,۰۰۰ تومان`
- For large numbers, use millions/billions abbreviation:
  - `۲,۹۷۰ میلیون تومان` or `۲.۹۷ میلیارد تومان`

### Dates
- Already stored as Jalali in the Excel — display as-is
- Format: `۱۴۰۵/۰۷/۲۱` (no time needed for display)

### Status Display
- `خالی` → `🟢 خالی` (available)
- `پر` → `🔴 پر` (occupied)

### Tables
- Monospace code blocks for alignment
- 10 rows per page with pagination
- Persian column headers

---

## 7. Architecture

```
partnership-bot/
├── bot.py                 # Entry point, bot initialization
├── config.py              # Settings (token, file path, intervals)
├── excel_loader.py        # Read & parse Excel → DataCache
├── messages.py            # All Persian text (centralized)
├── handlers/
│   ├── __init__.py
│   ├── start.py           # /start, main menu
│   ├── boards.py          # /available, /occupied, /prices, /details
│   ├── search.py          # /search
│   └── admin.py           # /reload, /status, /add_user, /remove_user
├── models.py              # Board dataclass, DataCache
├── utils.py               # Price formatting, table builder, pagination
├── whitelist.json         # Allowed Telegram user IDs
├── data/                  # Excel file lives here
│   └── boards.xlsx
├── requirements.txt
└── .env                   # TELEGRAM_BOT_TOKEN, EXCEL_FILE_PATH
```

---

## 8. Key Components

### `excel_loader.py`
- Reads the main sheet (`shayan_s test`) with `openpyxl`
- Skips column A/B/C (internal GUID/checksum/modified date)
- Parses columns D–Q into `Board` dataclass objects
- Skips the first data row ("خدمات اضافی" with zero prices)
- Stores all 194 boards in `DataCache`
- Runs on startup + every 4 hours via `APScheduler`

### `models.py`
```python
from dataclasses import dataclass

@dataclass
class Board:
    board_code: str          # D: کد تابلو — "ab-0"
    station: str             # E: جایگاه — "عباس آباد"
    status: str              # F: وضعیت — "خالی" or "پر"
    reservation_end: str     # G: تاریخ پایان — "1405/07/21 22:00"
    city: str                # H: شهر — "تهران"
    description: str         # I: شرح تابلو
    mode: str                # J: حالت — "افقی" or "عمودی"
    price_monthly: int       # K: قیمت ماهیانه (Rial)
    price_2month: int        # L: دو ماه
    price_3_5month: int      # M: سه تا پنج ماهه
    price_6_8month: int      # N: شش تا هشت ماهه
    area_sqm: float          # O: مساحت
    print_unit_price: int    # P: قیمت واحد چاپ و نصب
    print_total_cost: int    # Q: هزینه چاپ و نصب

class DataCache:
    boards: list[Board]
    last_loaded: datetime
    is_stale: bool

    def get_available(self) -> list[Board]:
        return [b for b in self.boards if b.status == "خالی"]

    def get_occupied(self) -> list[Board]:
        return [b for b in self.boards if b.status == "پر"]

    def search(self, query: str) -> list[Board]:
        q = query.lower()
        return [b for b in self.boards if q in b.board_code.lower()
                or q in b.station.lower() or q in b.city.lower()
                or q in b.description.lower()]

    def get_by_code(self, code: str) -> Board | None:
        for b in self.boards:
            if b.board_code == code:
                return b
        return None
```

### `utils.py` — helpers:
```python
def rial_to_toman(rial: int) -> str:
    """Convert Rial to formatted Toman: 2970000000 → '۲۹۷,۰۰۰,۰۰۰ تومان'"""

def format_area(area: float) -> str:
    """Format area: 79.2 → '۷۹.۲ متر مربع'"""

def paginate(items: list, page: int, per_page: int = 10) -> tuple[list, int, bool]:
    """Return (items_page, total_pages, has_next)"""

def build_board_table(boards: list[Board]) -> str:
    """Build a monospace table for Telegram display"""
```

### `handlers/boards.py`
- `/available` — filters `status == "خالی"`, paginates, shows table
- `/occupied` — filters `status == "پر"`, paginates, shows table
- `/prices` — shows all boards with prices, sorted by station
- `/details <code>` — shows full board info with all pricing tiers

### `handlers/search.py`
- Waits for user text input after tapping [جستجو]
- Searches across board_code, station, city, description
- Returns matching boards as paginated table

### `handlers/admin.py`
- `/reload` — forces `excel_loader.reload()`, replies with count
- `/status` — shows last reload time + board count
- `/add_user <id>` — adds to `whitelist.json`
- `/remove_user <id>` — removes from `whitelist.json`

---

## 9. Error Handling

| Scenario                        | Behavior                                      |
|---------------------------------|-----------------------------------------------|
| Excel file not found            | Log error, notify admin, serve stale cache     |
| Excel format changed            | Log warning, keep last good cache              |
| User not in whitelist           | "⛔ دسترسی غیرمجاز. با مدیر تماس بگیرید."     |
| Reload fails                    | Serve stale data, notify admin                 |
| No data for filter              | "اطلاعاتی یافت نشد."                          |
| Invalid board code in /details  | "کد تابلو نامعتبر است."                        |

---

## 10. Dependencies

```
python-telegram-bot>=20.0    # Telegram Bot API wrapper
openpyxl>=3.1               # Excel file reader
apscheduler>=3.10           # Scheduled Excel reload
python-dotenv               # Environment variables
```

> `jdatetime` removed — dates are already Jalali in the Excel, no conversion needed.

---

## 11. Future Considerations (not in MVP)

- Inline search with filters (by location, board type, price range)
- Export data as PDF / image from bot
- Arabic language support (alongside Persian)
- Admin dashboard (web UI to manage whitelist + upload new Excel)
- Usage analytics (who queries what)
- Offer/promotion management when that data becomes available
