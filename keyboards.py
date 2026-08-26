from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
import config
import urllib.parse


def buyer_menu(is_worker: bool = False, is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="🛍 Каталог"),
            KeyboardButton(text="👤 Профиль"),
            KeyboardButton(text="ℹ️ Информация"),
        ],
        [KeyboardButton(text="📦 Мои покупки"), KeyboardButton(text="🚚 Доставка")],
        [KeyboardButton(text="🔥 Работа"), KeyboardButton(text="👨‍💻 Оператор")],
        [KeyboardButton(text="👥 Реферальная система")],
        [KeyboardButton(text="💲 Пополнить баланс")],
    ]
    if is_worker or is_admin:
        extra_row = []
        if is_worker:
            extra_row.append(KeyboardButton(text="🔑 Панель воркера"))
        if is_admin:
            extra_row.append(KeyboardButton(text="👑 Панель главного администратора"))
        keyboard.insert(0, extra_row)
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def admin_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Все логи"), KeyboardButton(text="🔍 Поиск юзера")],
            [KeyboardButton(text="💳 Настройка карты"), KeyboardButton(text="💰 Пополнения")],
            [KeyboardButton(text="👨‍💻 Настройка оператора"), KeyboardButton(text="⚙️ Настройки")],
            [KeyboardButton(text="👥 Пользователи"), KeyboardButton(text="🏙 Каталог (SA)")],
            [KeyboardButton(text="➕ Добавить клад"), KeyboardButton(text="📊 Накрутить статистику")],
            [KeyboardButton(text="🏭 Управление складом")],
            [KeyboardButton(text="🚫 Бан/Разбан"), KeyboardButton(text="👷 Воркеры")],
            [KeyboardButton(text="🔙 Главное меню")],
        ],
        resize_keyboard=True,
    )


def worker_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить клад"), KeyboardButton(text="📦 Мои клады")],
            [KeyboardButton(text="🏭 Склад")],
            [KeyboardButton(text="🔙 Главное меню")],
        ],
        resize_keyboard=True,
    )


def settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏙 Города и районы", callback_data="set_cities")],
            [InlineKeyboardButton(text="💳 Способы оплаты", callback_data="set_payments")],
        ]
    )


def custom_cities_keyboard(cities_dict: dict) -> InlineKeyboardMarkup:
    buttons = []
    for city in cities_dict.keys():
        buttons.append([InlineKeyboardButton(text=f"🏙 {city}", callback_data=f"city_manage:{city}")])
    buttons.append([InlineKeyboardButton(text="➕ Добавить город", callback_data="add_city")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def city_manage_keyboard(city: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить район", callback_data=f"add_dist:{city}")],
            [InlineKeyboardButton(text="🗑 Удалить город", callback_data=f"del_city:{city}")],
            [InlineKeyboardButton(text="◀️ Назад к городам", callback_data="set_cities")],
        ]
    )


def districts_keyboard(city: str, districts: list) -> InlineKeyboardMarkup:
    buttons = []
    for d in districts:
        buttons.append([InlineKeyboardButton(text=f"🗑 {d}", callback_data=f"del_dist:{city}:{d}")])
    buttons.append([InlineKeyboardButton(text="➕ Добавить район", callback_data=f"add_dist:{city}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"city_manage:{city}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def warehouse_keyboard(products: list) -> InlineKeyboardMarkup:
    buttons = []
    for p in products:
        buttons.append([InlineKeyboardButton(text=f"{p['emoji']} {p['name']} ({p['price']} {p['currency']})", callback_data=f"wh_prod:{p['id']}")])
    buttons.append([InlineKeyboardButton(text="➕ Добавить товар на склад", callback_data="wh_add")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def warehouse_item_keyboard(product_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Изменить название", callback_data=f"wh_edit_name:{product_id}")],
            [InlineKeyboardButton(text="✏️ Изменить цену", callback_data=f"wh_edit_price:{product_id}")],
            [InlineKeyboardButton(text="✏️ Изменить эмодзи", callback_data=f"wh_edit_emoji:{product_id}")],
            [InlineKeyboardButton(text="🗑 Удалить товар", callback_data=f"wh_del:{product_id}")],
            [InlineKeyboardButton(text="◀️ Назад на склад", callback_data="admin_wh")],
        ]
    )


def catalog_cities_keyboard(cities: list) -> InlineKeyboardMarkup:
    buttons, row = [], []
    for city in cities:
        row.append(InlineKeyboardButton(text=city, callback_data=f"b_city:{city}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def catalog_districts_keyboard(districts: list) -> InlineKeyboardMarkup:
    buttons, row = [], []
    for dist in districts:
        row.append(InlineKeyboardButton(text=dist, callback_data=f"b_dist:{dist}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="◀️ Назад к городам", callback_data="b_back_cities")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def catalog_products_keyboard(products: list) -> InlineKeyboardMarkup:
    buttons = []
    for p in products:
        buttons.append([InlineKeyboardButton(text=f"{p['emoji']} {p['name']} — от {p['min_price']} RUB", callback_data=f"b_prod:{p['id']}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад к районам", callback_data="b_back_districts")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def catalog_subproducts_keyboard(items: list) -> InlineKeyboardMarkup:
    buttons = []
    for item in items:
        buttons.append([InlineKeyboardButton(text=f"📦 {item['type']} {item['size']} ({item['price']} RUB)", callback_data=f"b_item:{item['id']}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад к товарам", callback_data="b_back_products")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def buyer_confirm_keyboard(price: float) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить оплату", callback_data="b_buy_confirm")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="b_buy_cancel")],
        ]
    )


def cancel_state_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить город"), KeyboardButton(text="🗑 Удалить город")],
            [KeyboardButton(text="🔙 Главное меню")],
        ],
        resize_keyboard=True,
    )


def w_step1_city_keyboard(custom_cities_dict: dict) -> InlineKeyboardMarkup:
    # 🌍 Первой кнопкой выводится "Все города"
    buttons = [[InlineKeyboardButton(text="🌍 Все города", callback_data="wcity:all")]]
    row = []
    unique_cities = sorted(list(set(list(custom_cities_dict.keys()))))
    for city in unique_cities:
        row.append(InlineKeyboardButton(text=city, callback_data=f"wcity:{city}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def w_step2_district_keyboard(districts: list) -> InlineKeyboardMarkup:
    # 🌍 Первой кнопкой выводится "Все районы"
    buttons = [[InlineKeyboardButton(text="🌍 Все районы", callback_data="wdist:all")]]
    row = []
    for dist in districts:
        row.append(InlineKeyboardButton(text=dist, callback_data=f"wdist:{dist}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def w_step3_product_keyboard(products: list) -> InlineKeyboardMarkup:
    buttons = []
    for p in products:
        buttons.append([InlineKeyboardButton(text=f"{p['emoji']} {p['name']}", callback_data=f"wprod:{p['id']}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
