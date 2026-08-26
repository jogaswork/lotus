import asyncio
import logging
import math
import json

from aiogram import Bot, Dispatcher, F, BaseMiddleware
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery

import config
import database as db
import keyboards as kb

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

admins_in_buyer_mode: set[int] = set()
BOT_USERNAME: str = ""

def is_admin(user_id: int) -> bool:
    if user_id in admins_in_buyer_mode: return False
    if user_id in config.ADMIN_IDS: return True
    return db.is_admin_user(user_id)

def get_buyer_menu(user_id: int):
    is_w = db.is_worker(user_id)
    is_a = user_id in config.ADMIN_IDS or db.is_admin_user(user_id)
    return kb.buyer_menu(is_worker=is_w, is_admin=is_a)

class MenuMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = event.from_user
        
        if user:
            action_text = ""
            if hasattr(event, "text") and event.text:
                action_text = f"💬 Сообщение: ✏️ {event.text}"
            elif hasattr(event, "data") and event.data:
                action_text = f"🔘 Кнопка: {event.data}"
            elif hasattr(event, "photo") and event.photo:
                action_text = "📸 Отправил фото"
                
            if action_text:
                db.log_action(user.id, user.username or str(user.id), action_text)
                
        if hasattr(event, "text") and event.text:
            key_phrases = [
                "🛍 Каталог", "👤 Профиль", "ℹ️ Информация", "📦 Мои покупки", 
                "🚚 Доставка", "🔥 Работа", "👨‍💻 Оператор", "👥 Реферальная система", 
                "💲 Пополнить баланс", "🔑 Панель воркера", "👑 Панель главного администратора",
                "🔙 Главное меню", "◀️ В главное меню", "📋 Все логи", "🔍 Поиск юзера", 
                "💳 Настройка карты", "💰 Пополнения", "👨‍💻 Настройка оператора", "⚙️ Настройки",
                "👥 Пользователи", "🏙 Каталог (SA)", "➕ Добавить клад", "📊 Накрутить статистику",
                "🏭 Управление складом", "🚫 Бан/Разбан", "👷 Воркеры", "👑 Админы", "👤 Режим покупателя",
                "🗑 Мои клады", "📊 Статистика кладов", "🔗 Моя реф-ссылка", "📋 Логи рефералов", 
                "🦣 Мои мамонты", "🏙 Города", "➕ Добавить город", "🗑 Удалить город", "❌ Отмена",
                "◀️ Назад к вакансиям", "🏠 В главное меню"
            ]
            
            if event.text in key_phrases:
                state: FSMContext = data.get('state')
                if state:
                    await state.clear()
                    
        if user and db.is_banned(user.id):
            return
            
        return await handler(event, data)

dp.message.middleware(MenuMiddleware())
dp.callback_query.middleware(MenuMiddleware())

# === FSM СТЕЙТЫ ===
class Broadcast(StatesGroup): 
    text = State()
class TopUp(StatesGroup): 
    amount = State()
    screenshot = State()
class AdminUserManage(StatesGroup): 
    user_id = State()
class AdminManage(StatesGroup): 
    admin_user_id = State()
class AdminWarehouse(StatesGroup): 
    name = State()
    desc = State()
    price = State()
    price_unit = State()
    unit = State()
    emoji = State()
class WorkerOrder(StatesGroup): 
    step1_city = State()
    step2_district = State()
    step3_product = State()
    step4_type = State()
    step4_size = State()
    step6_quantity = State()
class AddCustomCity(StatesGroup): 
    city_name = State()
    district_name = State()
class DelCustomCity(StatesGroup): 
    city_name = State()
class SettingsMenu(StatesGroup): 
    chat_link = State()
class BoostStats(StatesGroup): 
    amount = State()
class AdminCard(StatesGroup): 
    card_num = State()
    card_holder = State()
class AdminOp(StatesGroup): 
    op_user = State()
    op_status = State()
    op_eta = State()

# ==========================================
# ОБРАБОТЧИК ОТМЕНЫ
# ==========================================
@dp.message(F.text == "❌ Отмена")
async def cancel_fsm_action(message: Message, state: FSMContext):
    await state.clear()
    if is_admin(message.from_user.id):
        await message.answer("❌ Действие отменено.", reply_markup=kb.admin_menu())
    elif db.is_worker(message.from_user.id):
        await message.answer("❌ Действие отменено.", reply_markup=kb.worker_menu())
    else:
        await message.answer("❌ Действие отменено.", reply_markup=get_buyer_menu(message.from_user.id))

@dp.callback_query(F.data == "cancel_settings")
async def cancel_inline_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer("Отменено")

# ==========================================
# СТАРТ И РЕЖИМЫ
# ==========================================
@dp.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    user_id = message.from_user.id
    is_new_user = not db.user_exists(user_id)
    db.get_or_create_user(user_id, message.from_user.username)

    if is_new_user and command.args:
        try: 
            referrer_id = int(command.args.replace("ref_", ""))
        except ValueError: 
            referrer_id = None
            
        if referrer_id and referrer_id != user_id and db.user_exists(referrer_id):
            db.set_referrer(user_id, referrer_id)

    if is_admin(user_id):
        await message.answer("👑 Панель главного администратора", reply_markup=kb.admin_menu())
    else:
        await message.answer(config.WELCOME_TEXT, reply_markup=get_buyer_menu(user_id))

@dp.message(F.text == "👤 Режим покупателя")
async def switch_to_buyer(message: Message):
    if message.from_user.id in config.ADMIN_IDS or db.is_worker(message.from_user.id) or db.is_admin_user(message.from_user.id):
        if message.from_user.id in config.ADMIN_IDS or db.is_admin_user(message.from_user.id):
            admins_in_buyer_mode.add(message.from_user.id)
        await message.answer("Вы переключились в режим покупателя.", reply_markup=get_buyer_menu(message.from_user.id))

@dp.message(F.text.in_({"👑 Панель главного администратора", "/admin"}))
async def switch_to_admin(message: Message):
    if message.from_user.id in config.ADMIN_IDS or db.is_admin_user(message.from_user.id):
        admins_in_buyer_mode.discard(message.from_user.id)
        await message.answer("👑 Панель главного администратора", reply_markup=kb.admin_menu())

@dp.message(F.text.in_({"🔑 Панель воркера", "/work"}))
async def switch_to_worker(message: Message):
    if is_admin(message.from_user.id) or db.is_worker(message.from_user.id):
        await message.answer("🔑 Панель воркера", reply_markup=kb.worker_menu())

# ==========================================
# ПАНЕЛЬ АДМИНА (ЛОГИ И ПАГИНАЦИЯ)
# ==========================================
@dp.message(F.text == "📋 Все логи")
async def admin_all_logs(message: Message):
    if not is_admin(message.from_user.id): return
    
    total_logs = db.count_action_logs()
    if total_logs == 0:
        await message.answer("Логов пока нет.")
        return
        
    logs_per_page = 10
    total_pages = math.ceil(total_logs / logs_per_page)
    
    logs = db.get_action_logs(limit=logs_per_page, offset=0)
    
    lines = [f"[{l[3]}] @{l[1]} (id{l[0]})\n{l[2]}" for l in logs]
    text = "📋 Последние действия юзеров:\n\n" + "\n\n".join(lines)
    
    await message.answer(text, reply_markup=kb.admin_logs_pagination_keyboard(1, total_pages))

@dp.callback_query(F.data.startswith("logs_page_"))
async def admin_logs_page(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    
    page = int(callback.data.split("_")[2])
    logs_per_page = 10
    
    total_logs = db.count_action_logs()
    total_pages = math.ceil(total_logs / logs_per_page)
    
    if page > total_pages:
        page = total_pages
        
    offset = (page - 1) * logs_per_page
    
    logs = db.get_action_logs(limit=logs_per_page, offset=offset)
    
    lines = [f"[{l[3]}] @{l[1]} (id{l[0]})\n{l[2]}" for l in logs]
    text = "📋 Последние действия юзеров:\n\n" + "\n\n".join(lines)
    
    try:
        await callback.message.edit_text(text, reply_markup=kb.admin_logs_pagination_keyboard(page, total_pages))
    except Exception:
        pass
    await callback.answer()

@dp.message(F.text == "⚙️ Настройки")
async def admin_settings(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await state.set_state(SettingsMenu.chat_link)
    current = db.get_setting('chat_link')
    await message.answer(f"⚙️ Настройки\n\nСсылка на чат: {current}\n\nОтправьте новую ссылку на чат:", reply_markup=kb.settings_keyboard())

@dp.message(SettingsMenu.chat_link)
async def admin_save_chat_link(message: Message, state: FSMContext):
    db.set_setting('chat_link', message.text)
    await state.clear()
    await message.answer("✅ Ссылка сохранена.", reply_markup=kb.admin_menu())

@dp.message(F.text == "👥 Пользователи")
async def admin_users_count(message: Message):
    if not is_admin(message.from_user.id): return
    count = db.count_all_users()
    await message.answer(f"👥 Пользователи\nВсего в боте: {count}")

@dp.message(F.text == "💰 Пополнения")
async def admin_topups(message: Message):
    if not is_admin(message.from_user.id): return
    topups = db.get_all_topups(10)
    if not topups:
        await message.answer("Пополнений пока нет.")
        return
    lines = []
    for tid, uname, amt, st, dt in topups:
        status_ico = "✅" if st == "подтверждено" else ("❌" if st == "отклонено" else "⏳")
        lines.append(f"ID: {tid} | @{uname} | {amt}₽ | {status_ico}")
    await message.answer("💰 Последние пополнения:\n\n" + "\n".join(lines))

@dp.message(F.text == "💳 Настройка карты")
async def admin_card_set(message: Message):
    if not is_admin(message.from_user.id): return
    c_num = db.get_setting("card_number")
    c_hold = db.get_setting("card_holder")
    await message.answer(f"💳 Текущие реквизиты:\nНомер: `{c_num}`\nПолучатель: `{c_hold}`\n\nЧто хотите изменить?", reply_markup=kb.admin_card_settings(), parse_mode="Markdown")

@dp.callback_query(F.data == "card_edit_num")
async def card_edit_n(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminCard.card_num)
    await callback.message.edit_text("Введите новый номер карты (16 цифр):", reply_markup=kb.settings_keyboard())

@dp.message(AdminCard.card_num)
async def card_save_n(message: Message, state: FSMContext):
    db.set_setting("card_number", message.text)
    await state.clear()
    await message.answer("✅ Номер карты обновлен.", reply_markup=kb.admin_menu())

@dp.callback_query(F.data == "card_edit_holder")
async def card_edit_h(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminCard.card_holder)
    await callback.message.edit_text("Введите ФИО и Банк получателя:", reply_markup=kb.settings_keyboard())

@dp.message(AdminCard.card_holder)
async def card_save_h(message: Message, state: FSMContext):
    db.set_setting("card_holder", message.text)
    await state.clear()
    await message.answer("✅ Получатель обновлен.", reply_markup=kb.admin_menu())

@dp.message(F.text == "👨‍💻 Настройка оператора")
async def admin_op_set(message: Message):
    if not is_admin(message.from_user.id): return
    u = db.get_setting("operator_username")
    s = db.get_setting("operator_status")
    e = db.get_setting("operator_eta")
    text = f"👨‍💻 Настройка оператора\nUsername: {u}\nСтатус: {s}\nETA: {e}\n\nЧто изменить?"
    await message.answer(text, reply_markup=kb.admin_operator_settings())

@dp.callback_query(F.data == "op_edit_username")
async def op_edit_u(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminOp.op_user)
    await callback.message.edit_text("Введите новый Username (с @):", reply_markup=kb.settings_keyboard())

@dp.message(AdminOp.op_user)
async def op_save_u(message: Message, state: FSMContext):
    db.set_setting("operator_username", message.text)
    await state.clear()
    await message.answer("✅ Username оператора обновлен.", reply_markup=kb.admin_menu())

@dp.callback_query(F.data == "op_edit_status")
async def op_edit_s(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminOp.op_status)
    await callback.message.edit_text("Введите новый статус (например: online):", reply_markup=kb.settings_keyboard())

@dp.message(AdminOp.op_status)
async def op_save_s(message: Message, state: FSMContext):
    db.set_setting("operator_status", message.text)
    await state.clear()
    await message.answer("✅ Статус оператора обновлен.", reply_markup=kb.admin_menu())

@dp.callback_query(F.data == "op_edit_eta")
async def op_edit_e(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminOp.op_eta)
    await callback.message.edit_text("Введите новое ETA (например: 5 мин):", reply_markup=kb.settings_keyboard())

@dp.message(AdminOp.op_eta)
async def op_save_e(message: Message, state: FSMContext):
    db.set_setting("operator_eta", message.text)
    await state.clear()
    await message.answer("✅ ETA оператора обновлено.", reply_markup=kb.admin_menu())

@dp.message(F.text == "🏙 Каталог (SA)")
async def admin_sa_catalog(message: Message):
    if not is_admin(message.from_user.id): return
    cities = list(db.get_all_custom_cities().keys())
    await message.answer("🌍 Глобальный каталог\nУправление городами:", reply_markup=kb.sa_catalog_keyboard(cities))

@dp.callback_query(F.data == "sa_add_city")
async def sa_add_c(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddCustomCity.city_name)
    await callback.message.answer("Введите название нового города:", reply_markup=kb.cancel_state_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "sa_del_city")
async def sa_del_c(callback: CallbackQuery, state: FSMContext):
    await state.set_state(DelCustomCity.city_name)
    await callback.message.answer("Введите точное название города для удаления:", reply_markup=kb.cancel_state_keyboard())
    await callback.answer()

@dp.message(DelCustomCity.city_name)
async def sa_del_c_finish(message: Message, state: FSMContext):
    db.delete_custom_city(message.text)
    await state.clear()
    await message.answer(f"✅ Город {message.text} и его районы удалены.", reply_markup=kb.admin_menu())

# === КНОПКИ АДМИНЫ, ВОРКЕРЫ И ПОИСК ЮЗЕРА ===
@dp.message(F.text == "👑 Админы")
async def admin_admins_menu_btn(message: Message):
    if not is_admin(message.from_user.id): return
    await message.answer("👑 Управление администраторами:", reply_markup=kb.admin_admins_menu())

@dp.callback_query(F.data == "m_manage_admin")
async def admin_manage_admin_search(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminManage.admin_user_id)
    await callback.message.edit_text("🔍 Введите @username или ID пользователя для управления правами админа:", reply_markup=kb.settings_keyboard())

@dp.callback_query(F.data == "m_admin_list")
async def admin_admin_list_show(callback: CallbackQuery):
    admins = db.get_admins()
    if not admins:
        await callback.message.edit_text("Список админов пуст (кроме создателя).", reply_markup=kb.admin_admins_menu())
        return
    text = "👑 Список назначенных админов:\n\n" + "\n".join([f"• @{u[1]} (ID: {u[0]})" for u in admins])
    await callback.message.edit_text(text, reply_markup=kb.admin_admins_menu())

@dp.message(AdminManage.admin_user_id)
async def admin_manage_admin_info(message: Message, state: FSMContext):
    text_input = message.text.strip()
    target_id = None
    if text_input.startswith('@') or not text_input.isdigit():
        user = db.get_user_by_username(text_input)
        if user: target_id = user[0]
    else:
        target_id = int(text_input)
        if not db.user_exists(target_id): target_id = None
        
    if not target_id:
        await message.answer("❌ Пользователь не найден.", reply_markup=kb.settings_keyboard())
        return
        
    if target_id in config.ADMIN_IDS:
        await message.answer("❌ Этот пользователь — системный администратор, его права нельзя изменить.", reply_markup=kb.admin_menu())
        await state.clear()
        return

    await state.clear()
    is_adm = db.is_admin_user(target_id)
    text = f"👤 Пользователь найден!\nID: {target_id}\nАдмин: {'Да 👑' if is_adm else 'Нет ❌'}"
    await message.answer(text, reply_markup=kb.admin_admin_manage_keyboard(target_id, is_adm))

@dp.callback_query(F.data.startswith("adm_usr_adm_"))
async def adm_toggle_admin_status(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    target_id = int(callback.data.split("_")[3])
    current = db.is_admin_user(target_id)
    db.set_user_admin(target_id, not current)
    await callback.message.edit_text(f"Пользователь {target_id} {'ТЕПЕРЬ АДМИН 👑' if not current else 'БОЛЬШЕ НЕ АДМИН ❌'}")


@dp.message(F.text == "👷 Воркеры")
async def admin_workers_menu(message: Message):
    if not is_admin(message.from_user.id): return
    await message.answer("👷 Управление воркерами:", reply_markup=kb.admin_worker_menu())

@dp.callback_query(F.data == "m_manage_worker")
async def admin_manage_worker_search(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminUserManage.user_id)
    await callback.message.edit_text("🔍 Введите @username или ID пользователя для управления правами:", reply_markup=kb.settings_keyboard())

@dp.callback_query(F.data == "m_worker_list")
async def admin_worker_list_show(callback: CallbackQuery):
    workers = db.get_workers()
    if not workers:
        await callback.message.edit_text("Список воркеров пуст.", reply_markup=kb.admin_worker_menu())
        return
    text = "👷 Список воркеров:\n\n" + "\n".join([f"• @{u[1]} (ID: {u[0]})" for u in workers])
    await callback.message.edit_text(text, reply_markup=kb.admin_worker_menu())

@dp.message(F.text == "🔍 Поиск юзера")
async def admin_manage_users(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await state.set_state(AdminUserManage.user_id)
    await message.answer("🔍 Введите @username или ID пользователя:", reply_markup=kb.settings_keyboard())

@dp.message(AdminUserManage.user_id)
async def admin_user_info(message: Message, state: FSMContext):
    text_input = message.text.strip()
    target_id = None
    
    if text_input.startswith('@') or not text_input.isdigit():
        user = db.get_user_by_username(text_input)
        if user: target_id = user[0]
    else:
        target_id = int(text_input)
        if not db.user_exists(target_id): target_id = None
        
    if not target_id:
        await message.answer("❌ Пользователь не найден.", reply_markup=kb.settings_keyboard())
        return
        
    await state.clear()
    is_ban = db.is_banned(target_id)
    is_wrk = db.is_worker(target_id)
    text = f"👤 Пользователь найден!\nID: {target_id}\nСтатус бана: {'Да 🔴' if is_ban else 'Нет 🟢'}\nВоркер: {'Да 👷' if is_wrk else 'Нет ❌'}"
    await message.answer(text, reply_markup=kb.admin_user_manage_keyboard(target_id, is_ban, is_wrk))
    await message.answer("Панель управления:", reply_markup=kb.admin_menu())

@dp.callback_query(F.data.startswith("adm_usr_ban_"))
async def adm_toggle_ban(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    target_id = int(callback.data.split("_")[3])
    current = db.is_banned(target_id)
    db.set_user_banned(target_id, not current)
    await callback.message.edit_text(f"Пользователь {target_id} {'ЗАБАНЕН 🔴' if not current else 'РАЗБАНЕН 🟢'}")

@dp.callback_query(F.data.startswith("adm_usr_wrk_"))
async def adm_toggle_worker(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    target_id = int(callback.data.split("_")[3])
    current = db.is_worker(target_id)
    db.set_user_worker(target_id, not current)
    await callback.message.edit_text(f"Пользователь {target_id} {'ТЕПЕРЬ ВОРКЕР 👷' if not current else 'БОЛЬШЕ НЕ ВОРКЕР ❌'}")

@dp.message(F.text == "🚫 Бан/Разбан")
async def admin_ban_system(message: Message):
    if not is_admin(message.from_user.id): return
    await message.answer("Управление банами:", reply_markup=kb.admin_ban_menu())

@dp.callback_query(F.data == "m_ban_user")
async def m_ban_user_cb(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminUserManage.user_id)
    await callback.message.edit_text("Введите @username или ID пользователя для бана:", reply_markup=kb.settings_keyboard())
    
@dp.callback_query(F.data == "m_unban_user")
async def m_unban_user_cb(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminUserManage.user_id)
    await callback.message.edit_text("Введите @username или ID пользователя для разбана:", reply_markup=kb.settings_keyboard())

@dp.callback_query(F.data == "m_ban_list")
async def m_ban_list_cb(callback: CallbackQuery):
    banned = db.get_banned_users()
    if not banned:
        await callback.message.edit_text("Список забаненных пуст.", reply_markup=kb.admin_ban_menu())
        return
    text = "Забаненные пользователи:\n\n" + "\n".join([f"• @{u[1]} (ID: {u[0]})" for u in banned])
    await callback.message.edit_text(text, reply_markup=kb.admin_ban_menu())

@dp.callback_query(F.data == "m_ban_close")
async def m_ban_close_cb(callback: CallbackQuery):
    await callback.message.delete()

# ==========================================
# ПАНЕЛЬ АДМИНА: СКЛАД
# ==========================================
async def show_warehouse_list(message_or_callback):
    items = db.get_all_warehouse_items()
    text = f"🏭 Управление складом\nПозиций: {len(items)}\n\nВыберите позицию или добавьте новую:"
    markup = kb.warehouse_list_keyboard(items)
    
    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(text, reply_markup=markup)
    else:
        await message_or_callback.message.edit_text(text, reply_markup=markup)

@dp.message(F.text == "🏭 Управление складом")
async def admin_warehouse_btn(message: Message):
    if not is_admin(message.from_user.id): return
    await show_warehouse_list(message)

@dp.callback_query(F.data == "wh_back_list")
async def admin_warehouse_back(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    await show_warehouse_list(callback)
    await callback.answer()

@dp.callback_query(F.data.startswith("wh_view_"))
async def admin_wh_view(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    item_id = int(callback.data.split("_")[2])
    item = db.get_warehouse_item(item_id)
    if not item: return
    
    i_id, name, desc, base_price, unit, is_active, emoji, prices_json = item
    free_stashes, sold_stashes = db.count_stashes_for_product(name)
    
    prices = json.loads(prices_json) if prices_json else {}
    prices_str_list = []
    for i in range(1, 11):
        p = prices.get(str(i))
        if p is not None:
            prices_str_list.append(f"{i}: {p}₽")
        else:
            prices_str_list.append(f"{i}: ---")
            
    prices_str = "\n" + "\n".join(prices_str_list)
    
    text = (
        f"<b>{emoji} {name}</b>\n\n"
        f"📜 {desc}\n\n"
        f"💰 <b>Установленные цены:</b>{prices_str}\n\n"
        f"📐 Единица: {unit}\n"
        f"{'✅ Активен' if is_active else '❌ Скрыт'}\n\n"
        f"🔢 Свободных кладов: {free_stashes}\n"
        f"✅ Продано кладов: {sold_stashes}"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.warehouse_item_keyboard(item_id, bool(is_active)))
    await callback.answer()

@dp.callback_query(F.data.startswith("wh_toggle_"))
async def admin_wh_toggle(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    item_id = int(callback.data.split("_")[2])
    item = db.get_warehouse_item(item_id)
    new_status = 0 if item[5] else 1
    db.update_warehouse_field(item_id, "is_active", new_status)
    await admin_wh_view(callback)

@dp.callback_query(F.data.startswith("wh_clear_"))
async def admin_wh_clear(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    item_id = int(callback.data.split("_")[2])
    db.update_warehouse_field(item_id, "name", f"Слот {item_id}")
    db.update_warehouse_field(item_id, "description", "Описание отсутствует")
    db.update_warehouse_field(item_id, "base_price", 0.0)
    db.update_warehouse_field(item_id, "prices", "{}") 
    db.update_warehouse_field(item_id, "emoji", "📦")
    db.update_warehouse_field(item_id, "is_active", 1)
    await callback.answer("Слот удалён!", show_alert=True)
    await show_warehouse_list(callback)

@dp.callback_query(F.data.startswith("wh_editname_"))
async def wh_editname(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    item_id = int(callback.data.split("_")[2])
    await state.update_data(wh_item_id=item_id)
    await state.set_state(AdminWarehouse.name)
    await callback.message.answer("Введите новое название товара:", reply_markup=kb.settings_keyboard())
    await callback.answer()

@dp.message(AdminWarehouse.name)
async def wh_save_name(message: Message, state: FSMContext):
    data = await state.get_data()
    db.update_warehouse_field(data['wh_item_id'], "name", message.text)
    await state.clear()
    await message.answer("✅ Название обновлено.", reply_markup=kb.admin_menu())
    await show_warehouse_list(message)

@dp.callback_query(F.data.startswith("wh_editprice_"))
async def wh_editprice(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    item_id = int(callback.data.split("_")[2])
    await callback.message.edit_text("Выберите фасовку (штуки/граммы), для которой хотите изменить или установить цену:", reply_markup=kb.wh_select_unit_keyboard(item_id))
    await callback.answer()

@dp.callback_query(F.data.startswith("wh_setprice_"))
async def wh_setprice(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    parts = callback.data.split("_")
    item_id = int(parts[2])
    unit_qty = int(parts[3])
    
    await state.update_data(wh_item_id=item_id, wh_unit_qty=unit_qty)
    await state.set_state(AdminWarehouse.price)
    await callback.message.edit_text(f"Введите цену для фасовки {unit_qty} шт/г:", reply_markup=kb.settings_keyboard())
    await callback.answer()

@dp.message(AdminWarehouse.price)
async def wh_save_price(message: Message, state: FSMContext):
    try: price = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Цена должна быть числом:")
        return
    data = await state.get_data()
    db.update_warehouse_price(data['wh_item_id'], data['wh_unit_qty'], price)
    await state.clear()
    await message.answer("✅ Цена успешно обновлена.", reply_markup=kb.admin_menu())
    await show_warehouse_list(message)

@dp.callback_query(F.data.startswith("wh_editdesc_"))
async def wh_editdesc(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    item_id = int(callback.data.split("_")[2])
    await state.update_data(wh_item_id=item_id)
    await state.set_state(AdminWarehouse.desc)
    await callback.message.answer("Введите новое описание:", reply_markup=kb.settings_keyboard())
    await callback.answer()

@dp.message(AdminWarehouse.desc)
async def wh_save_desc(message: Message, state: FSMContext):
    data = await state.get_data()
    db.update_warehouse_field(data['wh_item_id'], "description", message.text)
    await state.clear()
    await message.answer("✅ Описание обновлено.", reply_markup=kb.admin_menu())
    await show_warehouse_list(message)

@dp.callback_query(F.data.startswith("wh_editunit_"))
async def wh_editunit(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    item_id = int(callback.data.split("_")[2])
    await state.update_data(wh_item_id=item_id)
    await state.set_state(AdminWarehouse.unit)
    await callback.message.answer("Введите единицу измерения (г / шт):", reply_markup=kb.settings_keyboard())
    await callback.answer()

@dp.message(AdminWarehouse.unit)
async def wh_save_unit(message: Message, state: FSMContext):
    data = await state.get_data()
    db.update_warehouse_field(data['wh_item_id'], "unit", message.text)
    await state.clear()
    await message.answer("✅ Единица измерения обновлена.", reply_markup=kb.admin_menu())
    await show_warehouse_list(message)

@dp.callback_query(F.data.startswith("wh_editemoji_"))
async def wh_editemoji(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    item_id = int(callback.data.split("_")[2])
    await state.update_data(wh_item_id=item_id)
    await state.set_state(AdminWarehouse.emoji)
    await callback.message.answer("Отправьте новый эмодзи для этого товара (например: 🌿 🔮):", reply_markup=kb.settings_keyboard())
    await callback.answer()

@dp.message(AdminWarehouse.emoji)
async def wh_save_emoji(message: Message, state: FSMContext):
    data = await state.get_data()
    db.update_warehouse_field(data['wh_item_id'], "emoji", message.text)
    await state.clear()
    await message.answer("✅ Эмодзи обновлены.", reply_markup=kb.admin_menu())
    await show_warehouse_list(message)

# ==========================================
# ПАНЕЛЬ ВОРКЕРА И КНОПКИ
# ==========================================
@dp.message(F.text.in_({"🔙 Главное меню", "◀️ В главное меню", "🏠 В главное меню"}))
async def back_to_main_menu(message: Message):
    if is_admin(message.from_user.id):
        await message.answer("Главное меню", reply_markup=kb.admin_menu())
    else:
        await message.answer("Главное меню", reply_markup=get_buyer_menu(message.from_user.id))

@dp.message(F.text == "🗑 Мои клады")
async def w_my_orders(message: Message):
    if not db.is_worker(message.from_user.id) and not is_admin(message.from_user.id): return
    stashes = db.get_active_worker_stashes(message.from_user.id)
    if not stashes:
        await message.answer("У вас нет активных кладов.")
        return
        
    limit_msg = ""
    if len(stashes) > 40:
        limit_msg = f"\n(Показаны последние 40 из {len(stashes)})"
        
    await message.answer(f"📥 Ваши активные клады ({len(stashes)} шт.){limit_msg}\nНажмите 🗑 рядом с кладом чтобы удалить:", reply_markup=kb.worker_stashes_list(stashes))

@dp.callback_query(F.data == "wdelall_ask")
async def w_delall_ask(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚠️ Вы уверены, что хотите удалить **ВСЕ** ваши активные клады?\nЭто действие нельзя отменить!",
        parse_mode="Markdown",
        reply_markup=kb.confirm_delete_all_stashes_keyboard()
    )

@dp.callback_query(F.data == "wdelall_confirm")
async def w_delall_confirm(callback: CallbackQuery):
    deleted = db.delete_all_worker_stashes(callback.from_user.id)
    await callback.message.edit_text(f"✅ Успешно удалено кладов: {deleted}")
    await callback.answer(f"Удалено {deleted} кладов")

@dp.callback_query(F.data == "wdelall_cancel")
async def w_delall_cancel(callback: CallbackQuery):
    stashes = db.get_active_worker_stashes(callback.from_user.id)
    if not stashes:
        await callback.message.edit_text("У вас нет активных кладов.")
        return
        
    limit_msg = ""
    if len(stashes) > 40:
        limit_msg = f"\n(Показаны последние 40 из {len(stashes)})"
        
    await callback.message.edit_text(
        f"📥 Ваши активные клады ({len(stashes)} шт.){limit_msg}\nНажмите 🗑 рядом с кладом чтобы удалить:", 
        reply_markup=kb.worker_stashes_list(stashes)
    )
    await callback.answer("Отменено")

@dp.callback_query(F.data.startswith("wdel_"))
async def w_del_stash(callback: CallbackQuery):
    stash_id = int(callback.data.split("_")[1])
    if db.delete_worker_stash(stash_id, callback.from_user.id):
        await callback.answer("Удалено!")
        stashes = db.get_active_worker_stashes(callback.from_user.id)
        if stashes:
            limit_msg = ""
            if len(stashes) > 40:
                limit_msg = f"\n(Показаны последние 40 из {len(stashes)})"
            await callback.message.edit_text(
                f"📥 Ваши активные клады ({len(stashes)} шт.){limit_msg}\nНажмите 🗑 рядом с кладом чтобы удалить:", 
                reply_markup=kb.worker_stashes_list(stashes)
            )
        else:
            await callback.message.edit_text("У вас нет активных кладов.")
    else:
        await callback.answer("Ошибка или клад уже продан", show_alert=True)

@dp.message(F.text == "📊 Статистика кладов")
async def w_stats(message: Message):
    if not db.is_worker(message.from_user.id) and not is_admin(message.from_user.id): return
    total, sold, free = db.get_worker_stats(message.from_user.id)
    await message.answer(f"📊 Ваша статистика кладов\n\n📦 Всего добавлено: {total}\n✅ Продано: {sold}\n🗑 Остаток: {free}")

@dp.message(F.text == "🔗 Моя реф-ссылка")
async def w_ref(message: Message):
    if not db.is_worker(message.from_user.id) and not is_admin(message.from_user.id): return
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{message.from_user.id}"
    await message.answer(f"Ваша реферальная ссылка:\n{link}\n\nКопируйте и распространяйте её.", reply_markup=kb.referral_worker_keyboard(link))

@dp.message(F.text == "📋 Логи рефералов")
async def w_ref_logs(message: Message):
    if not db.is_worker(message.from_user.id) and not is_admin(message.from_user.id): return
    refs = db.get_referrals(message.from_user.id)
    if not refs:
        await message.answer("У вас пока нет рефералов.")
        return
    lines = [f"👤 @{r[1] or r[0]} (Регистрация: {r[2].split(' ')[0]})" for r in refs]
    await message.answer("📋 Ваши приглашенные рефералы:\n\n" + "\n".join(lines))

@dp.message(F.text == "🦣 Мои мамонты")
async def w_customers(message: Message):
    if not db.is_worker(message.from_user.id) and not is_admin(message.from_user.id): return
    earned = db.get_referral_earned(message.from_user.id)
    refs = db.get_referrals(message.from_user.id)
    count = len(refs)
    
    text = (
        f"🦣 Ваши мамонты (рефералы):\n\n"
        f"👥 Всего приглашено: {count}\n"
        f"💰 Заработано с их пополнений: {earned} {config.CURRENCY}\n\n"
        f"Распространяйте реферальную ссылку для увеличения заработка!"
    )
    await message.answer(text)

@dp.message(F.text == "📊 Накрутить статистику")
async def w_boost(message: Message, state: FSMContext):
    if not db.is_worker(message.from_user.id) and not is_admin(message.from_user.id): return
    await message.answer("📊 Накрутка статистики\nВыберите что накрутить:", reply_markup=kb.worker_boost_keyboard())

@dp.callback_query(F.data.startswith("bst_"))
async def w_boost_cb(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BoostStats.amount)
    await callback.message.edit_text("📊 Счётчик пользователей\n\nВведите значение (например: 3000 или +500 или -200):", reply_markup=kb.settings_keyboard())
    await callback.answer()

@dp.message(BoostStats.amount)
async def w_boost_save(message: Message, state: FSMContext):
    try: val = int(message.text.replace("+", ""))
    except: 
        await message.answer("Введите число!")
        return
    db.boost_worker_stats(message.from_user.id, abs(val))
    await state.clear()
    await message.answer("✅ Статистика обновлена.", reply_markup=kb.worker_menu())

@dp.message(F.text == "🏙 Города")
async def w_cities_menu(message: Message):
    if not db.is_worker(message.from_user.id) and not is_admin(message.from_user.id): return
    await message.answer("Управление городами:", reply_markup=kb.worker_cities_menu())

@dp.message(F.text == "➕ Добавить город")
async def w_add_city_step1(message: Message, state: FSMContext):
    if not db.is_worker(message.from_user.id) and not is_admin(message.from_user.id): return
    await state.set_state(AddCustomCity.city_name)
    await message.answer("Введите название нового города:", reply_markup=kb.cancel_state_keyboard())

@dp.message(AddCustomCity.city_name)
async def w_add_city_step2(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await state.set_state(AddCustomCity.district_name)
    await message.answer("Введите название района для этого города:", reply_markup=kb.cancel_state_keyboard())

@dp.message(AddCustomCity.district_name)
async def w_add_city_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    db.add_custom_city(data['city'], message.text)
    await state.clear()
    await message.answer(f"✅ Город {data['city']} (Район: {message.text}) успешно добавлен!", reply_markup=kb.worker_cities_menu())

@dp.message(F.text == "🗑 Удалить город")
async def w_del_city_step1(message: Message, state: FSMContext):
    if not db.is_worker(message.from_user.id) and not is_admin(message.from_user.id): return
    await state.set_state(DelCustomCity.city_name)
    await message.answer("Введите точное название города для удаления:", reply_markup=kb.cancel_state_keyboard())

@dp.message(DelCustomCity.city_name)
async def w_del_city_finish(message: Message, state: FSMContext):
    db.delete_custom_city(message.text)
    await state.clear()
    await message.answer(f"✅ Город {message.text} и его районы удалены.", reply_markup=kb.worker_cities_menu())


# ==========================================
# ВОРКЕР И АДМИН: ДОБАВЛЕНИЕ КЛАДОВ В БАЗУ
# ==========================================
@dp.message(F.text == "➕ Добавить клад")
async def w_order_step1(message: Message, state: FSMContext):
    if not db.is_worker(message.from_user.id) and not is_admin(message.from_user.id): return
    await state.set_state(WorkerOrder.step1_city)
    cities_dict = db.get_all_custom_cities()
    await message.answer("🏙 Шаг 1/5 — Выберите город:", reply_markup=kb.w_step1_city_keyboard(cities_dict))

# === ШАГ 1: ВЫБОР ГОРОДА ===
@dp.callback_query(F.data.startswith("wcity:") | F.data.startswith("w_order_step1:"))
async def w_step1_city(callback: CallbackQuery, state: FSMContext):
    city_name = callback.data.split(":")[1]
    cities_dict = db.get_all_custom_cities()

    # 🌍 ОБРАБОТКА "ВСЕ ГОРОДА"
    if city_name == "all":
        await state.update_data(w_city="all", w_dist="all")
        await state.set_state(WorkerOrder.step3_product)
        products = db.get_all_warehouse_items()
        await callback.message.edit_text(
            "🌍 Выбраны **Все города и все районы**.\n\nШаг 3/5 — Выберите товар:",
            reply_markup=kb.w_step3_product_keyboard(products),
            parse_mode="Markdown"
        )
        await callback.answer()
        return

    if city_name not in cities_dict:
        await callback.answer("Город не найден.", show_alert=True)
        return

    await state.update_data(w_city=city_name)
    districts = cities_dict.get(city_name, [])

    await state.set_state(WorkerOrder.step2_district)
    await callback.message.edit_text(
        f"Город: {city_name}\nШаг 2/5 — Выберите район:",
        reply_markup=kb.w_step2_district_keyboard(districts)
    )
    await callback.answer()


# === ШАГ 2: ВЫБОР РАЙОНА ===
@dp.callback_query(F.data.startswith("wdist:") | F.data.startswith("w_order_step2:"))
async def w_step2_district(callback: CallbackQuery, state: FSMContext):
    dist_name = callback.data.split(":")[1]
    data = await state.get_data()
    city_name = data.get("w_city")

    cities_dict = db.get_all_custom_cities()
    available_districts = cities_dict.get(city_name, [])

    # 🌍 ОБРАБОТКА "ВСЕ РАЙОНЫ"
    if dist_name == "all":
        await state.update_data(w_dist="all")
    elif dist_name not in available_districts:
        await callback.answer("Район не найден.", show_alert=True)
        return
    else:
        await state.update_data(w_dist=dist_name)

    await state.set_state(WorkerOrder.step3_product)
    products = db.get_all_warehouse_items()
    await callback.message.edit_text(
        f"Город: {city_name}\nРайон: {'Все районы' if dist_name == 'all' else dist_name}\n\nШаг 3/5 — Выберите товар:",
        reply_markup=kb.w_step3_product_keyboard(products)
    )
    await callback.answer()
    loc_str = "Все районы" if district == "all" else district
    await callback.message.edit_text(f"🏘 {data['w_city']} -> {loc_str}\n📦 Шаг 3/5 — Выберите товар из склада:", reply_markup=kb.w_step3_warehouse_keyboard(active_items))
    await callback.answer()

@dp.callback_query(WorkerOrder.step3_product, F.data.startswith("wwh_"))
async def w_order_step4(callback: CallbackQuery, state: FSMContext):
    item_id = int(callback.data.split("_")[1])
    item = db.get_warehouse_item(item_id)
    if not item: return
    
    prices_json = item[7]
    prices = json.loads(prices_json) if prices_json else {}
    
    await state.update_data(w_prod_id=item_id, w_prod_name=item[1], w_prices=prices, w_emoji=item[6])
    await state.set_state(WorkerOrder.step4_type)
    await callback.message.edit_text(f"📍 Шаг 4/5 — Выберите тип клада:", reply_markup=kb.w_step4_type_keyboard())
    await callback.answer()

@dp.callback_query(WorkerOrder.step4_type, F.data.startswith("wtype:"))
async def w_order_step4_size(callback: CallbackQuery, state: FSMContext):
    type_val = callback.data.split(":")[1]
    await state.update_data(w_type=type_val)
    await state.set_state(WorkerOrder.step4_size)
    data = await state.get_data()
    
    prices_dict = data.get('w_prices', {})
    
    if not prices_dict:
        await callback.message.edit_text("❌ Администратор еще не задал цены для этого товара ни на одну фасовку. Выберите другой товар.", reply_markup=kb.cancel_state_keyboard())
        await callback.answer()
        return

    text = f"📍 Тип клада: {type_val}\n\n📦 Шаг 4/5 — Выберите фасовку (показаны только те, для которых установлена цена):"
    await callback.message.edit_text(text, reply_markup=kb.w_step4_package_size_keyboard(prices_dict))
    await callback.answer()

@dp.callback_query(WorkerOrder.step4_size, F.data.startswith("wsize:"))
async def w_order_step5_qty(callback: CallbackQuery, state: FSMContext):
    size = int(callback.data.split(":")[1])
    data = await state.get_data()
    
    prices_dict = data.get('w_prices', {})
    calc_price = float(prices_dict.get(str(size), 0))
    
    await state.update_data(w_size=size, w_price=calc_price)
    await state.set_state(WorkerOrder.step6_quantity)
    
    text = (
        f"{data.get('w_emoji', '📦')} {data['w_prod_name']} — {size}.0 шт\n"
        f"💰 Цена за клад: {calc_price} ₽\n"
        f"📍 Тип: {data['w_type']}\n\n"
        f"🔢 Шаг 5/5 — Сколько таких кладов добавить?"
    )
    await callback.message.edit_text(text, reply_markup=kb.w_step5_quantity_keyboard())
    await callback.answer()

@dp.callback_query(WorkerOrder.step6_quantity, F.data.startswith("wqty:"))
async def w_order_confirm(callback: CallbackQuery, state: FSMContext):
    qty = int(callback.data.split(":")[1])
    await state.update_data(w_qty=qty)
    data = await state.get_data()
    
    cities_dict = db.get_all_custom_cities()
    targets = []
    
    if data['w_city'] == 'all':
        for c, dists in cities_dict.items():
            for d in dists:
                targets.append((c, d))
    elif data.get('w_dist') == 'all':
        for d in cities_dict.get(data['w_city'], []):
            targets.append((data['w_city'], d))
    else:
        targets.append((data['w_city'], data['w_dist']))
        
    await state.update_data(w_targets=targets)
        
    total_stashes = len(targets) * qty
    total_price = float(data['w_price']) * total_stashes
    
    loc_str = "🌍 Все города и районы" if data['w_city'] == 'all' else (f"🏙 {data['w_city']} (Все районы)" if data.get('w_dist') == 'all' else f"🏙 {data['w_city']}, {data['w_dist']}")
    
    text = (
        f"✅ Подтверждение добавления кладов\n\n"
        f"📍 Локация: {loc_str}\n"
        f"📦 Товар: {data.get('w_emoji', '📦')} {data['w_prod_name']}\n"
        f"💰 Цена за клад: {data['w_price']} ₽\n"
        f"📍 Тип клада: {data['w_type']}\n"
        f"⚖️ Содержимое клада: {data['w_size']}.0 шт\n"
        f"🗺 Кладов на район: {qty}\n"
        f"🔢 Всего кладов: {total_stashes}\n"
        f"💵 Общая стоимость: {total_price} ₽"
    )
    await callback.message.edit_text(text, reply_markup=kb.w_confirm_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "w_confirm_add")
async def w_order_finish(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    targets = data.get('w_targets', [])
    qty_per_district = data['w_qty']
    
    for c, d in targets:
        db.add_worker_order(callback.from_user.id, c, d, data['w_prod_name'], data['w_type'], data['w_size'], qty_per_district, data['w_price'])
        
    await state.clear()
    
    total_added = len(targets) * qty_per_district
    
    text = (
        f"✅ Клады успешно добавлены!\n"
        f"{data.get('w_emoji', '📦')} {data['w_prod_name']} — {data['w_size']}.0 шт\n"
        f"📍 Тип: {data['w_type']}\n"
        f"💰 Цена за клад: {data['w_price']} ₽\n"
        f"📦 Добавлено кладов: {total_added}"
    )
    
    await callback.message.edit_text(text)
    if is_admin(callback.from_user.id):
        await callback.message.answer("👑 Панель главного администратора", reply_markup=kb.admin_menu())
    else:
        await callback.message.answer("🔑 Панель воркера", reply_markup=kb.worker_menu())
    await callback.answer()

@dp.callback_query(F.data == "w_cancel_add")
async def w_order_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Добавление отменено.")
    if is_admin(callback.from_user.id):
        await callback.message.answer("👑 Панель главного администратора", reply_markup=kb.admin_menu())
    else:
        await callback.message.answer("🔑 Панель воркера", reply_markup=kb.worker_menu())
    await callback.answer()

@dp.callback_query(F.data.startswith("wback:"))
async def w_order_back(callback: CallbackQuery, state: FSMContext):
    step = int(callback.data.split(":")[1])
    cities_dict = db.get_all_custom_cities()
    data = await state.get_data()
    
    if step == 1:
        await state.set_state(WorkerOrder.step1_city)
        await callback.message.edit_text("🏙 Шаг 1/5 — Выберите город:", reply_markup=kb.w_step1_city_keyboard(cities_dict))
    elif step == 2:
        city = data.get('w_city', 'Неизвестно')
        if city == 'all':
            await state.set_state(WorkerOrder.step1_city)
            await callback.message.edit_text("🏙 Шаг 1/5 — Выберите город:", reply_markup=kb.w_step1_city_keyboard(cities_dict))
        else:
            await state.set_state(WorkerOrder.step2_district)
            await callback.message.edit_text(f"🏙 {city}\n🏘 Шаг 2/5 — Выберите район:", reply_markup=kb.w_step2_district_keyboard(city, cities_dict))
    elif step == 3:
        await state.set_state(WorkerOrder.step3_product)
        active_items = db.get_active_warehouse_items()
        await callback.message.edit_text(f"📦 Шаг 3/5 — Выберите товар из склада:", reply_markup=kb.w_step3_warehouse_keyboard(active_items))
    elif step == 4:
        await state.set_state(WorkerOrder.step4_type)
        await callback.message.edit_text(f"📍 Шаг 4/5 — Выберите тип клада:", reply_markup=kb.w_step4_type_keyboard())
    elif step == 5:
        await state.set_state(WorkerOrder.step4_size)
        prices_dict = data.get('w_prices', {})
        await callback.message.edit_text(f"📍 Тип клада: {data.get('w_type')}\n\n📦 Шаг 4/5 — Выберите фасовку (показаны только те, для которых установлена цена):", reply_markup=kb.w_step4_package_size_keyboard(prices_dict))
    await callback.answer()


# ==========================================
# ДИНАМИЧЕСКИЙ КАТАЛОГ ПОКУПАТЕЛЯ
# ==========================================
@dp.message(F.text == "🛍 Каталог")
async def b_catalog_start(message: Message, state: FSMContext):
    cities = db.get_available_cities()
    if not cities:
        await message.answer("😔 К сожалению, сейчас нет доступных кладов.")
        return
    await state.update_data(b_cities=cities)
    await message.answer("🏙 Выберите город:", reply_markup=kb.dynamic_list_keyboard(cities, "bcity"))

@dp.callback_query(F.data.startswith("bcity_"))
async def b_catalog_city(callback: CallbackQuery, state: FSMContext):
    idx = int(callback.data.split("_")[1])
    data = await state.get_data()
    
    if "b_cities" not in data:
        await callback.answer("Сессия устарела. Начните заново.", show_alert=True)
        return
        
    city = data["b_cities"][idx]
    districts = db.get_available_districts(city)
    await state.update_data(b_city=city, b_districts=districts)
    
    await callback.message.edit_text(f"🏙 {city}\nВыберите район:", reply_markup=kb.dynamic_list_keyboard(districts, "bdist", "b_back_city"))
    await callback.answer()

@dp.callback_query(F.data == "b_back_city")
async def b_catalog_back_city(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.message.edit_text("🏙 Выберите город:", reply_markup=kb.dynamic_list_keyboard(data["b_cities"], "bcity"))
    await callback.answer()

@dp.callback_query(F.data.startswith("bdist_"))
async def b_catalog_dist(callback: CallbackQuery, state: FSMContext):
    idx = int(callback.data.split("_")[1])
    data = await state.get_data()
    dist = data["b_districts"][idx]
    city = data["b_city"]
    
    products_data = db.get_available_products_with_emojis(city, dist)
    if not products_data:
        await callback.answer("Товары закончились", show_alert=True)
        return
        
    await state.update_data(b_dist=dist, b_products=products_data)
    await callback.message.edit_text(f"📍 {city} -> {dist}\n⌨️ Выберите товар:", reply_markup=kb.dynamic_products_keyboard(products_data, "bprod", "b_back_dist"))
    await callback.answer()

@dp.callback_query(F.data == "b_back_dist")
async def b_catalog_back_dist(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.message.edit_text(f"🏙 {data['b_city']}\nВыберите район:", reply_markup=kb.dynamic_list_keyboard(data["b_districts"], "bdist", "b_back_city"))
    await callback.answer()

@dp.callback_query(F.data.startswith("bprod_"))
async def b_catalog_prod(callback: CallbackQuery, state: FSMContext):
    idx = int(callback.data.split("_")[1])
    data = await state.get_data()
    prod_name, emoji = data["b_products"][idx]
    
    types = db.get_available_types(data["b_city"], data["b_dist"], prod_name)
    await state.update_data(b_prod=prod_name, b_emoji=emoji, b_types=types)
    
    await callback.message.edit_text(f"📍 Товар: {emoji} {prod_name}\n📦 Выберите тип клада:", reply_markup=kb.dynamic_list_keyboard(types, "btype", "b_back_prod"))
    await callback.answer()

@dp.callback_query(F.data == "b_back_prod")
async def b_catalog_back_prod(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.message.edit_text(f"📍 {data['b_city']} -> {data['b_dist']}\n⌨️ Выберите товар:", reply_markup=kb.dynamic_products_keyboard(data["b_products"], "bprod", "b_back_dist"))
    await callback.answer()

@dp.callback_query(F.data.startswith("btype_"))
async def b_catalog_type(callback: CallbackQuery, state: FSMContext):
    idx = int(callback.data.split("_")[1])
    data = await state.get_data()
    type_val = data["b_types"][idx]
    
    sizes_prices = db.get_available_sizes_prices(data["b_city"], data["b_dist"], data["b_prod"], type_val)
    await state.update_data(b_type=type_val, b_sizes=sizes_prices)
    
    await callback.message.edit_text(f"📍 Тип: {type_val}\n⚖️ Выберите фасовку:", reply_markup=kb.dynamic_sizes_keyboard(sizes_prices, "bsize", "b_back_type"))
    await callback.answer()

@dp.callback_query(F.data == "b_back_type")
async def b_catalog_back_type(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.message.edit_text(f"📍 Товар: {data['b_emoji']} {data['b_prod']}\n📦 Выберите тип клада:", reply_markup=kb.dynamic_list_keyboard(data["b_types"], "btype", "b_back_prod"))
    await callback.answer()

@dp.callback_query(F.data.startswith("bsize_"))
async def b_catalog_size(callback: CallbackQuery, state: FSMContext):
    idx = int(callback.data.split("_")[1])
    data = await state.get_data()
    size_tuple = data["b_sizes"][idx]
    size_val, price, count = size_tuple
    
    await state.update_data(b_size=size_val)
    
    text = (
        f"⚠️ Вы уверены что хотите приобрести данную позицию?\n\n"
        f"После подтверждения с вашего баланса будет списано: <b>{price} ₽</b>\n\n"
        f"Возврат денежных средств после покупки не предусмотрен, даже при ошибочном нажатии!"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.buyer_confirm_keyboard(price))
    await callback.answer()

@dp.callback_query(F.data == "b_buy_cancel")
async def b_catalog_cancel(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    sizes_prices = data.get("b_sizes")
    if sizes_prices:
        await callback.message.edit_text(f"📍 Тип: {data['b_type']}\n⚖️ Выберите фасовку:", reply_markup=kb.dynamic_sizes_keyboard(sizes_prices, "bsize", "b_back_type"))
    else:
        await callback.message.delete()
    await callback.answer("Отменено")

@dp.callback_query(F.data == "b_buy_confirm")
async def b_catalog_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = callback.from_user.id
    username = callback.from_user.username or callback.from_user.full_name
    
    try:
        success, result, price = db.reserve_and_buy_stash(user_id, username, data['b_city'], data['b_dist'], data['b_prod'], data['b_type'], data['b_size'])
        
        if not success:
            if "Недостаточно" in str(result):
                c_num = db.get_setting("card_number", "0000 0000 0000 0000")
                c_hold = db.get_setting("card_holder", "Имя Фамилия Банк")
                text_fail = f"❌ {result}\n\n💳 Оплата по карте\nПереведите нужную сумму на карту:\n`{c_num}` {c_hold}\n\nПосле перевода перейдите в меню '💲 Пополнить баланс' и отправьте скриншот."
                await callback.message.answer(text_fail, parse_mode="Markdown", reply_markup=kb.insufficient_funds_keyboard())
            else:
                await callback.message.answer(f"❌ Ошибка: {result}")
            await callback.answer(str(result), show_alert=True)
            return
            
        order_id = result
        new_balance = db.get_balance(user_id)
        op_usr = db.get_setting("operator_username") 
        
        await callback.message.edit_text(
            f"✅ <b>Заказ №{order_id} успешно оформлен!</b>\n\n"
            f"📦 Товар: {data['b_emoji']} {data['b_prod']} ({data['b_size']} шт)\n"
            f"📍 Локация: {data['b_city']}, {data['b_dist']}\n"
            f"Сумма: {price} {config.CURRENCY}\n"
            f"Остаток на балансе: {new_balance} {config.CURRENCY}\n\n"
            f"⚠️ <b>Для получения адреса напишите нашему оператору:</b> {op_usr}\n"
            f"<i>(Обязательно укажите номер вашего заказа)</i>",
            parse_mode="HTML"
        )
        await callback.answer("Успешная покупка!")

        dynamic_admins = db.get_admins()
        dynamic_admin_ids = [adm[0] for adm in dynamic_admins]
        all_admin_ids = set(config.ADMIN_IDS + dynamic_admin_ids)
        
        admin_text = (
            f"🚨 <b>Новый заказ №{order_id}!</b>\n\n"
            f"👤 Покупатель: @{username} (ID: <code>{user_id}</code>)\n"
            f"📦 Товар: {data['b_emoji']} {data['b_prod']} ({data['b_size']} шт)\n"
            f"📍 Локация: {data['b_city']}, {data['b_dist']}\n"
            f"📍 Тип клада: {data['b_type']}\n"
            f"💰 Сумма: {price} {config.CURRENCY}\n\n"
            f"👨‍💻 Ожидайте сообщения от покупателя для выдачи клада."
        )
        
        for admin_id in all_admin_ids:
            try:
                await bot.send_message(chat_id=admin_id, text=admin_text, parse_mode="HTML")
            except Exception as e:
                logging.error(f"Не удалось отправить уведомление о заказе админу {admin_id}: {e}")

    except Exception as e:
        logging.error(f"Buy error: {e}")
        await callback.message.answer("❌ Произошла ошибка. Обратитесь в поддержку.")
        await callback.answer()


# ==========================================
# ОСТАЛЬНОЙ ФУНКЦИОНАЛ ПОКУПАТЕЛЯ
# ==========================================
@dp.message(F.text == "💲 Пополнить баланс")
async def topup_from_menu(message: Message, state: FSMContext):
    await state.set_state(TopUp.amount)
    await message.answer(f"Введите сумму пополнения в рублях (минимум {config.MIN_TOPUP} ₽):", reply_markup=kb.topup_cancel_keyboard())

@dp.callback_query(F.data == "topup_back_to_menu")
async def topup_back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Главное меню:", reply_markup=get_buyer_menu(callback.from_user.id))
    await callback.answer()

@dp.callback_query(F.data == "topup_cancel")
async def topup_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Пополнение отменено.", reply_markup=get_buyer_menu(callback.from_user.id))
    await callback.answer()

@dp.callback_query(F.data == "topup_start")
async def topup_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TopUp.amount)
    await callback.message.answer(f"Введите сумму пополнения в рублях (минимум {config.MIN_TOPUP} ₽):", reply_markup=kb.topup_cancel_keyboard())
    await callback.answer()

@dp.message(TopUp.amount)
async def topup_amount(message: Message, state: FSMContext):
    try: amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Сумма должна быть числом. Попробуйте ещё раз:", reply_markup=kb.topup_cancel_keyboard())
        return

    await state.update_data(topup_amount=amount)
    await message.answer("Выберите способ оплаты:", reply_markup=kb.topup_method_keyboard())

@dp.callback_query(F.data == "topup_method_card")
async def topup_method_card(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    amount = data.get("topup_amount")
    if not amount: return
    c_num = db.get_setting("card_number")
    c_hold = db.get_setting("card_holder")
    await callback.message.edit_text(f"💳 Оплата по карте\n\nПереведите {amount} ₽ на карту:\n`{c_num}`  {c_hold}\n\nПосле перевода нажмите кнопку ниже и отправьте скриншот чека.", reply_markup=kb.topup_pay_keyboard(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "topup_method_crypto")
async def topup_method_crypto(callback: CallbackQuery, state: FSMContext):
    op_usr = db.get_setting("operator_username")
    text = (
        "🪙 <b>Оплата криптовалютой</b>\n\n"
        f"⚠️ Для получения реквизитов и фиксации курса свяжитесь с нашим оператором: {op_usr}\n\n"
        "После перевода оператор зачислит средства на ваш баланс вручную."
    )
    await callback.message.edit_text(text, reply_markup=kb.topup_crypto_keyboard(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "topup_sent")
async def topup_sent(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(TopUp.screenshot)
    await callback.message.answer("Пришлите скриншот чека/перевода отдельным сообщением (фото):", reply_markup=kb.topup_cancel_keyboard())
    await callback.answer()

@dp.message(TopUp.screenshot, F.photo)
async def topup_screenshot(message: Message, state: FSMContext):
    data = await state.get_data()
    amount = data.get("topup_amount")
    if amount is None:
        await state.clear()
        await message.answer("Что-то пошло не так, начните пополнение заново.", reply_markup=get_buyer_menu(message.from_user.id))
        return

    photo_id = message.photo[-1].file_id
    topup_id = db.create_topup(user_id=message.from_user.id, username=message.from_user.username or message.from_user.full_name, amount=amount, screenshot_file_id=photo_id)
    await state.clear()
    await message.answer("✅ Скриншот отправлен на проверку администратору. Баланс пополнится после подтверждения.", reply_markup=get_buyer_menu(message.from_user.id))

    dynamic_admins = db.get_admins()
    dynamic_admin_ids = [adm[0] for adm in dynamic_admins]
    all_admin_ids = set(config.ADMIN_IDS + dynamic_admin_ids)

    for admin_id in all_admin_ids:
        try: 
            await bot.send_photo(
                chat_id=admin_id, 
                photo=photo_id, 
                caption=f"💳 Заявка на пополнение №{topup_id}\nОт: @{message.from_user.username or message.from_user.id}\nСумма: {amount} {config.CURRENCY}", 
                reply_markup=kb.admin_topup_keyboard(topup_id)
            )
        except Exception as e: 
            logging.error(f"Не удалось отправить уведомление админу {admin_id}: {e}")

@dp.message(TopUp.screenshot)
async def topup_screenshot_invalid(message: Message):
    await message.answer("Пришлите, пожалуйста, именно фото (скриншот чека).")

@dp.callback_query(F.data.startswith("topup_approve_"))
async def topup_approve(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    topup_id = int(callback.data.split("_")[2])
    topup = db.get_topup(topup_id)
    if not topup: return
    tid, user_id, username, amount, screenshot_file_id, status = topup
    if status != "ожидает": return

    db.change_balance(user_id, amount)
    db.set_topup_status(topup_id, "подтверждено")

    referrer_id = db.get_referrer(user_id)
    if referrer_id:
        bonus = round(amount * 0.10, 2)
        db.add_referral_earning(referrer_id, bonus)

    await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ Подтверждено", reply_markup=None)
    await callback.answer("Баланс пополнен")
    
    try:
        await bot.send_message(
            chat_id=user_id, 
            text=f"✅ <b>Отличные новости!</b>\nВаш платеж подтвержден, баланс успешно пополнен на <b>{amount} {config.CURRENCY}</b>.", 
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Не удалось отправить уведомление о пополнении юзеру {user_id}: {e}")

@dp.callback_query(F.data.startswith("topup_reject_"))
async def topup_reject(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    topup_id = int(callback.data.split("_")[2])
    topup = db.get_topup(topup_id)
    if not topup: return
    
    tid, user_id, username, amount, screenshot_file_id, status = topup
    if status != "ожидает": return
    
    db.set_topup_status(topup_id, "отклонено")
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ Отклонено", reply_markup=None)
    await callback.answer("Заявка отклонена")
    
    try:
        await bot.send_message(
            chat_id=user_id, 
            text=f"❌ <b>Платеж отклонен</b>\nВаша заявка на пополнение {amount} {config.CURRENCY} была отклонена.\nЕсли это ошибка, обратитесь к оператору.", 
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Не удалось отправить уведомление об отклонении юзеру {user_id}: {e}")

@dp.message(F.text == "👤 Профиль")
async def profile(message: Message):
    db.get_or_create_user(message.from_user.id, message.from_user.username)
    username, balance, created_at = db.get_user_profile(message.from_user.id)
    orders_count = db.count_user_orders(message.from_user.id)
    reg_date = created_at.split(" ")[0] if created_at else "—"

    text = f"🪷 Ваш профиль 🪷\n\n👤 Логин: @{username or 'не указан'}\n🆔 ID: {message.from_user.id}\n📦 Количество заказов: {orders_count}\n⚖️ Диспуты: 0\n💰 Баланс: {balance} {config.CURRENCY}\n📅 Дата регистрации: {reg_date}\n\nСсылка на чат: {db.get_setting('chat_link')}\nДля доступа к чату необходимо сделать 5 заказов"
    await message.answer(text, reply_markup=kb.insufficient_funds_keyboard())

@dp.message(F.text == "👥 Реферальная система")
async def referral_program(message: Message):
    user_id = message.from_user.id
    db.get_or_create_user(user_id, message.from_user.username)
    earned = db.get_referral_earned(user_id)
    bot_info = await bot.get_me()
    referral_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"

    text = (
        "👥 Реферальная программа 👥\n"
        "➖ ➖ ➖ ➖ ➖\n"
        f"Ваша реферальная ссылка: {referral_link}\n"
        f"▫️ Заработано за всё время: {earned} ₽\n\n"
        "Если человек, приглашенный по реферальной ссылке, пополнит "
        "баланс, то вы получите 10% от суммы его депозита."
    )
    await message.answer(text, reply_markup=kb.referral_buyer_keyboard(referral_link))

@dp.callback_query(F.data == "my_referrals")
async def show_my_referrals_cb(callback: CallbackQuery):
    refs = db.get_referrals(callback.from_user.id)
    if not refs:
        await callback.answer("У вас пока нет рефералов 😔", show_alert=True)
        return
        
    lines = [f"👤 @{r[1] or r[0]} (Регистрация: {r[2].split(' ')[0]})" for r in refs]
    text = "📋 Ваши приглашенные рефералы:\n\n" + "\n".join(lines)
    
    if len(text) > 4000:
        text = text[:4000] + "..."
        
    await callback.message.answer(text)
    await callback.answer()

@dp.message(F.text == "🚚 Доставка")
async def delivery_info(message: Message):
    await message.answer(config.DELIVERY_INFO)

@dp.message(F.text == "ℹ️ Информация")
async def shop_info(message: Message):
    await message.answer(config.SHOP_INFO.strip())

@dp.message(F.text == "🔥 Работа")
async def show_jobs(message: Message):
    await message.answer("🔥 Работа 🔥\nВыберите интересующую вакансию:", reply_markup=kb.jobs_menu())

@dp.message(F.text == "📦 Мои покупки")
async def my_orders_buyer(message: Message):
    orders = db.get_user_orders(message.from_user.id)
    if not orders:
        await message.answer("У вас пока нет покупок.")
        return
    lines = [f"№{oid} • {name} • {price} {config.CURRENCY}" for oid, name, price, status, created_at, method in orders]
    await message.answer("\n".join(lines))

@dp.message(F.text == "👨‍💻 Оператор")
async def support(message: Message):
    chat_link = db.get_setting("chat_link")
    op_usr = db.get_setting("operator_username")
    op_status = db.get_setting("operator_status")
    op_eta = db.get_setting("operator_eta")
    
    status_emoji = "🟢 Онлайн" if op_status.lower() == "online" else "🔴 Оффлайн"
    
    text = (
        "👨‍💻 Оператор 👨‍💻\n"
        "➖ ➖ ➖ ➖ ➖\n"
        "В данном разделе можно сверить контакты оператора, либо же начать диалог с ним.\n\n"
        "Важные правила при общении с оператором:\n"
        "▫️ Сообщения по типу: «привет», «можете подсказать?», «что есть?» будут игнорироваться.\n"
        "▫️ Сообщения по типу: «Сколько стоит...» без указания города и района будут игнорироваться.\n"
        "▫️ Различный спам, флуд или оскорбление будет караться блокировкой.\n\n"
        f"{status_emoji} (ETA ~ {op_eta})\n"
        f"🔗 Актуальные контакты: {op_usr}"
    )
    await message.answer(text)

@dp.message()
async def handle_jobs_or_unknown(message: Message):
    if not message.text: return
    for key, text in config.VACANCIES.items():
        if key == message.text:
            await message.answer(f"{message.text}\n➖ ➖ ➖ ➖ ➖\n{text}", disable_web_page_preview=True)
            return

async def main():
    global BOT_USERNAME
    db.init_db()
    bot_info = await bot.get_me()
    BOT_USERNAME = bot_info.username
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
