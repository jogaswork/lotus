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
        [KeyboardButton(text="🛍 Каталог"), KeyboardButton(text="👤 Профиль"), KeyboardButton(text="ℹ️ Информация")],
        [KeyboardButton(text="📦 Мои покупки"), KeyboardButton(text="🚚 Доставка")],
        [KeyboardButton(text="🔥 Работа"), KeyboardButton(text="👨‍💻 Оператор")],
        [KeyboardButton(text="👥 Реферальная система")],
        [KeyboardButton(text="💲 Пополнить баланс")],
    ]
    
    if is_worker or is_admin:
        extra_row = []
        if is_worker: extra_row.append(KeyboardButton(text="🔑 Панель воркера"))
        if is_admin: extra_row.append(KeyboardButton(text="👑 Панель главного администратора"))
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
            [KeyboardButton(text="👑 Админы"), KeyboardButton(text="👤 Режим покупателя")]
        ],
        resize_keyboard=True,
    )

def worker_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить клад")],
            [KeyboardButton(text="🗑 Мои клады"), KeyboardButton(text="📊 Статистика кладов")],
            [KeyboardButton(text="🔗 Моя реф-ссылка"), KeyboardButton(text="📋 Логи рефералов")],
            [KeyboardButton(text="🦣 Мои мамонты")],
            [KeyboardButton(text="🏙 Города")],
            [KeyboardButton(text="📊 Накрутить статистику")],
            [KeyboardButton(text="👤 Режим покупателя")]
        ],
        resize_keyboard=True,
    )

def jobs_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏃 Курьер"), KeyboardButton(text="🖼 Трафаретчик"), KeyboardButton(text="🚚 Водитель")],
            [KeyboardButton(text="📄 Верификация"), KeyboardButton(text="👩‍💻 Вакансия оператора")],
            [KeyboardButton(text="🔙 Главное меню")]
        ],
        resize_keyboard=True,
    )

def job_detail_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="◀️ Назад к вакансиям")],
            [KeyboardButton(text="🏠 В главное меню")],
        ],
        resize_keyboard=True,
    )

# --- НОВЫЕ КЛАВИАТУРЫ ДЛЯ ВЫБОРА ОПЛАТЫ ---
def topup_method_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Банковская карта", callback_data="topup_method_card")],
            [InlineKeyboardButton(text="🪙 Криптовалюта", callback_data="topup_method_crypto")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="topup_cancel")]
        ]
    )

def topup_crypto_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data="topup_cancel")]
        ]
    )
# ------------------------------------------

def insufficient_funds_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💲 Пополнить баланс", callback_data="topup_start")],
            [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="topup_back_to_menu")],
        ]
    )

def topup_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отменить", callback_data="topup_cancel")]])

def topup_pay_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📤 Я отправил скриншот", callback_data="topup_sent")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="topup_cancel")],
        ]
    )

def admin_topup_keyboard(topup_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"topup_approve_{topup_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"topup_reject_{topup_id}"),
            ]
        ]
    )

def admin_user_manage_keyboard(user_id: int, is_banned: bool, is_worker: bool) -> InlineKeyboardMarkup:
    ban_text = "🟢 Разбанить" if is_banned else "🔴 Забанить"
    worker_text = "❌ Забрать воркера" if is_worker else "👷 Выдать воркера"
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=ban_text, callback_data=f"adm_usr_ban_{user_id}")],
            [InlineKeyboardButton(text=worker_text, callback_data=f"adm_usr_wrk_{user_id}")]
        ]
    )

def admin_admin_manage_keyboard(user_id: int, is_adm: bool) -> InlineKeyboardMarkup:
    adm_text = "❌ Забрать админку" if is_adm else "👑 Выдать админку"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=adm_text, callback_data=f"adm_usr_adm_{user_id}")]
        ]
    )

def admin_ban_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚫 Забанить", callback_data="m_ban_user")],
            [InlineKeyboardButton(text="🟢 Разбанить", callback_data="m_unban_user")],
            [InlineKeyboardButton(text="📋 Список забаненных", callback_data="m_ban_list")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="m_ban_close")]
        ]
    )

def admin_worker_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👷 Выдать / Забрать", callback_data="m_manage_worker")],
            [InlineKeyboardButton(text="📋 Список воркеров", callback_data="m_worker_list")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="m_ban_close")]
        ]
    )

def admin_admins_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👑 Выдать / Забрать", callback_data="m_manage_admin")],
            [InlineKeyboardButton(text="📋 Список админов", callback_data="m_admin_list")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="m_ban_close")]
        ]
    )

def admin_operator_settings() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Изменить Username", callback_data="op_edit_username")],
            [InlineKeyboardButton(text="🌐 Изменить Статус", callback_data="op_edit_status")],
            [InlineKeyboardButton(text="⏳ Изменить ETA", callback_data="op_edit_eta")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_settings")]
        ]
    )

def admin_card_settings() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Изм. номер карты", callback_data="card_edit_num")],
            [InlineKeyboardButton(text="👤 Изм. получателя", callback_data="card_edit_holder")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_settings")]
        ]
    )

def settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_settings")]
        ]
    )

def sa_catalog_keyboard(cities: list[str]) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for c in cities:
        row.append(InlineKeyboardButton(text=f"✅ {c}", callback_data="noop"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row: buttons.append(row)
    buttons.append([InlineKeyboardButton(text="➕ Добавить город", callback_data="sa_add_city")])
    buttons.append([InlineKeyboardButton(text="🗑 Удалить город", callback_data="sa_del_city")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def worker_boost_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Заказы юзера", callback_data="bst_1"), InlineKeyboardButton(text="⚖️ Диспуты юзе...", callback_data="bst_2")],
            [InlineKeyboardButton(text="🌍 Глобал. заказы", callback_data="bst_3"), InlineKeyboardButton(text="👥 Глобал. юзеры", callback_data="bst_4")]
        ]
    )

def warehouse_list_keyboard(items: list[tuple]) -> InlineKeyboardMarkup:
    buttons = []
    for item in items:
        item_id, name, desc, price, unit, is_active, emoji = item[0], item[1], item[2], item[3], item[4], item[5], item[6]
        status_icon = "✅" if is_active else "❌"
        buttons.append([InlineKeyboardButton(text=f"{status_icon} {emoji} {name} — от {price}₽", callback_data=f"wh_view_{item_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def warehouse_item_keyboard(item_id: int, is_active: bool) -> InlineKeyboardMarkup:
    status_text = "✅ Показать" if not is_active else "❌ Скрыть"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=status_text, callback_data=f"wh_toggle_{item_id}"),
                InlineKeyboardButton(text="✏️ Изм. название", callback_data=f"wh_editname_{item_id}")
            ],
            [
                InlineKeyboardButton(text="💰 Изменить це...", callback_data=f"wh_editprice_{item_id}"),
                InlineKeyboardButton(text="📝 Изм. описание", callback_data=f"wh_editdesc_{item_id}")
            ],
            [
                InlineKeyboardButton(text="📐 Изм. единицу", callback_data=f"wh_editunit_{item_id}"),
                InlineKeyboardButton(text="😎 Изм. эмодзи", callback_data=f"wh_editemoji_{item_id}")
            ],
            [
                InlineKeyboardButton(text="🗑 Очистить слот", callback_data=f"wh_clear_{item_id}")
            ],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="wh_back_list")]
        ]
    )

def wh_select_unit_keyboard(item_id: int) -> InlineKeyboardMarkup:
    buttons, row = [], []
    for i in range(1, 11):
        row.append(InlineKeyboardButton(text=f"{i}", callback_data=f"wh_setprice_{item_id}_{i}"))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row: buttons.append(row)
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"wh_view_{item_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def dynamic_list_keyboard(items: list[str], prefix: str, back_callback: str | None = None) -> InlineKeyboardMarkup:
    buttons, row = [], []
    for i, item in enumerate(items):
        row.append(InlineKeyboardButton(text=item, callback_data=f"{prefix}_{i}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row: buttons.append(row)
    if back_callback:
        buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def dynamic_products_keyboard(products: list[tuple[str, str]], prefix: str, back_callback: str) -> InlineKeyboardMarkup:
    buttons = []
    for i, (prod_name, emoji) in enumerate(products):
        buttons.append([InlineKeyboardButton(text=f"{emoji} {prod_name}", callback_data=f"{prefix}_{i}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад к районам", callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def dynamic_sizes_keyboard(sizes_prices: list[tuple], prefix: str, back_callback: str) -> InlineKeyboardMarkup:
    buttons = []
    for i, (size, price, count) in enumerate(sizes_prices):
        buttons.append([InlineKeyboardButton(text=f"{size} шт - {price} ₽", callback_data=f"{prefix}_{i}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
def buyer_confirm_keyboard(price: float) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить оплату", callback_data="b_buy_confirm")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="b_buy_cancel")]
    ])

def cancel_state_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить город"), KeyboardButton(text="🗑 Удалить город")],
            [KeyboardButton(text="🔙 Главное меню")]
        ],
        resize_keyboard=True
    )

def w_step1_city_keyboard(custom_cities_dict: dict) -> InlineKeyboardMarkup:
    # 🌍 Кнопка "Все города" идет первой
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
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)
def w_step2_district_keyboard(city: str, custom_cities_dict: dict) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text="🌍 Все районы", callback_data="wdist:all")]]
    districts = custom_cities_dict.get(city, [])
    row = []
    for dist in sorted(list(set(districts))):
        row.append(InlineKeyboardButton(text=dist, callback_data=f"wdist:{dist}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row: buttons.append(row)
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="wback:1")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def w_step3_warehouse_keyboard(active_items: list[tuple]) -> InlineKeyboardMarkup:
    buttons = []
    for item in active_items:
        item_id, name, desc, base_price, unit, is_active, emoji = item[0], item[1], item[2], item[3], item[4], item[5], item[6]
        buttons.append([InlineKeyboardButton(text=f"{emoji} {name} — от {base_price}₽", callback_data=f"wwh_{item_id}")])
    
    if not active_items:
        buttons.append([InlineKeyboardButton(text="Склад пуст", callback_data="empty")])
        
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def w_step4_type_keyboard() -> InlineKeyboardMarkup:
    buttons, row = [], []
    for t in config.STASH_TYPES:
        row.append(InlineKeyboardButton(text=t, callback_data=f"wtype:{t}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="wback:3")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def w_step4_package_size_keyboard(prices_dict: dict) -> InlineKeyboardMarkup:
    sizes = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    buttons, row = [], []
    for size in sizes:
        if str(size) in prices_dict:
            calc_price = float(prices_dict[str(size)])
            row.append(InlineKeyboardButton(text=f"{size} шт - {calc_price} ₽", callback_data=f"wsize:{size}"))
            if len(row) == 3:
                buttons.append(row)
                row = []
    if row:
        buttons.append(row)
        
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="wback:4")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def w_step5_quantity_keyboard() -> InlineKeyboardMarkup:
    buttons, row = [], []
    for i in range(1, 11):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"wqty:{i}"))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="wback:5")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def w_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="w_confirm_add"), InlineKeyboardButton(text="❌ Отмена", callback_data="w_cancel_add")]
        ]
    )

def worker_stashes_list(stashes: list[tuple]) -> InlineKeyboardMarkup:
    buttons = []
    
    if stashes:
        buttons.append([InlineKeyboardButton(text="🚨 Удалить ВСЕ клады 🚨", callback_data="wdelall_ask")])
        
    for stash_id, prod, size, type_val in stashes[:40]:
        label = f"🎈 🔮 {prod} — {size}.0 шт"
        buttons.append([
            InlineKeyboardButton(text=label, callback_data="noop"),
            InlineKeyboardButton(text="🗑", callback_data=f"wdel_{stash_id}")
        ])
        
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def confirm_delete_all_stashes_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, удалить все", callback_data="wdelall_confirm"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="wdelall_cancel")
            ]
        ]
    )

def referral_buyer_keyboard(ref_link: str) -> InlineKeyboardMarkup:
    promo_text = "🪷 Присоединяйся к лучшему магазину Lotus! Качественный товар, автоматическая выдача и быстрые клады 24/7."
    share_url = f"https://t.me/share/url?url={ref_link}&text={urllib.parse.quote(promo_text)}"
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Поделиться ссылкой", url=share_url)],
            [InlineKeyboardButton(text="👥 Мои рефералы", callback_data="my_referrals")]
        ]
    )

def referral_worker_keyboard(ref_link: str) -> InlineKeyboardMarkup:
    promo_text = "🪷 Присоединяйся к лучшему магазину Lotus! Качественный товар, автоматическая выдача и быстрые клады 24/7."
    share_url = f"https://t.me/share/url?url={ref_link}&text={urllib.parse.quote(promo_text)}"
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Поделиться ссылкой", url=share_url)]
        ]
    )

def admin_logs_pagination_keyboard(current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    
    if current_page > 1:
        row.append(InlineKeyboardButton(text="◀️", callback_data=f"logs_page_{current_page - 1}"))
    
    row.append(InlineKeyboardButton(text=f"{current_page}/{total_pages}", callback_data="noop"))
    
    if current_page < total_pages:
        row.append(InlineKeyboardButton(text="▶️", callback_data=f"logs_page_{current_page + 1}"))
        
    buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)
