import logging, re, asyncio
from aiogram import Bot, Dispatcher, Router, F, types
from aiogram.filters import Command, CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from io import BytesIO
from models import get_db, Participant, Chat, Match
from tournament import (
    create_tournament, register_participant, close_registration,
    get_active_tournament, get_user_matches, get_all_standings,
    find_match_by_players, submit_match_result, get_remaining_matches_for_user
)
from config import BOT_TOKEN, ADMIN_IDS, WEBAPP_URL
from ocr import recognize_image, parse_score

logging.basicConfig(level=logging.INFO)
router = Router()
REG = re.compile(r'^\+(\S+)$')
RES = re.compile(r'@(\S+)\s+(?:выиграл|победил|won)\s+(\d+)[\s:\-](\d+)\s+@(\S+)', re.I)
DRW = re.compile(r'@(\S+)\s+(?:ничья|draw)\s+(\d+)[\s:\-](\d+)\s+@(\S+)', re.I)
reg_msg_id = None
reg_chat_id = None
reg_text = ""

def kb(user_id):
    b=[[KeyboardButton(text="🏆 Турнир")],[KeyboardButton(text="📊 Мои матчи", web_app=WebAppInfo(url=f"{WEBAPP_URL}/app.html"))]]
    if user_id in ADMIN_IDS: b.append([KeyboardButton(text="⚙️ Админ")])
    return ReplyKeyboardMarkup(keyboard=b, resize_keyboard=True)

def save_chat(chat_id, title, active=1):
    db=next(get_db())
    ex=db.query(Chat).filter(Chat.chat_id==chat_id).first()
    if ex:
        ex.title=title; ex.is_active=active
    else:
        db.add(Chat(chat_id=chat_id, title=title, is_active=active))
    db.commit()

@router.my_chat_member()
async def on_my_chat_member(ev: types.ChatMemberUpdated):
    if ev.chat.type in ("group","supergroup"):
        active = 1 if ev.new_chat_member.status in ("member","administrator","creator") else 0
        save_chat(ev.chat.id, ev.chat.title or f"Chat {ev.chat.id}", active)

@router.message(CommandStart())
async def start(m: types.Message):
    db=next(get_db()); t=get_active_tournament(db)
    txt=f"Привет, {m.from_user.full_name}! 👋\n\nFC Mobile H2H Tournament Bot.\n"
    if t: txt+=f"\n🏆 {t.name}\nСтатус: {t.status.value}\nУчастников: {len(t.participants)} / {t.max_participants}"
    else: txt+="\nНет активных турниров."
    await m.answer(txt, reply_markup=kb(m.from_user.id), parse_mode="HTML")

@router.message(F.text=="🏆 Турнир")
async def cur(m: types.Message):
    db=next(get_db()); t=get_active_tournament(db)
    if not t: return await m.answer("Нет активных турниров.")
    txt=f"<b>🏆 {t.name}</b>\n\nСтатус: {t.status.value}\nУчастников: {len(t.participants)} / {t.max_participants}\n"
    if t.status.value=="active":
        for g in get_all_standings(db, t.id):
            txt+=f"\n<b>{g['group_name']}</b>\n"
            for i,p in enumerate(g['standings'],1): txt+=f"{i}. {p['nickname']} — {p['points']} очк. ({p['wins']}В-{p['draws']}Н-{p['losses']}П)\n"
    await m.answer(txt, parse_mode="HTML")

@router.message(F.text=="⚙️ Админ")
async def adm(m: types.Message):
    if m.from_user.id not in ADMIN_IDS: return await m.answer("Нет доступа.")
    kb=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать турнир", callback_data="ad:create")],
        [InlineKeyboardButton(text="📝 Открыть регистрацию", callback_data="ad:open")],
        [InlineKeyboardButton(text="🔒 Закрыть и жеребьевка", callback_data="ad:close")],
        [InlineKeyboardButton(text="📋 Участники", callback_data="ad:list")],
    ])
    await m.answer("⚙️ Админ-панель", reply_markup=kb)

@router.callback_query(F.data=="ad:create")
async def ad_create(c: types.CallbackQuery):
    await c.message.answer("Введи: <code>Название, кол-во групп</code>\nПример: <code>FC Cup, 2</code>", parse_mode="HTML")
    await c.answer()

@router.message(F.text.regexp(r"^(.+),\s*(\d+)$"))
async def proc_create(m: types.Message):
    if m.from_user.id not in ADMIN_IDS: return
    a=m.text.split(","); n=a[0].strip(); g=int(a[1].strip())
    db=next(get_db()); t=create_tournament(db,n,g)
    await m.answer(f"✅ Турнир <b>{t.name}</b>\nГрупп: {t.groups_count}\nМакс участников: {t.max_participants}", parse_mode="HTML")

@router.callback_query(F.data=="ad:open")
async def ad_open(c: types.CallbackQuery):
    db=next(get_db()); t=get_active_tournament(db)
    if not t or t.status.value!="registration": return await c.answer("Нет турнира в регистрации!")
    chats=db.query(Chat).filter(Chat.is_active==1).all()
    if not chats:
        return await c.message.answer("❌ Бот не добавлен ни в одну группу!\n\nДобавь бота в группу и сделай его администратором, потом повтори.")
    rows=[[InlineKeyboardButton(text=f"📢 {ch.title}", callback_data=f"ad:open:{ch.chat_id}")] for ch in chats]
    kbm=InlineKeyboardMarkup(inline_keyboard=rows)
    await c.message.answer("Выбери группу для сбора участников:", reply_markup=kbm)
    await c.answer()

@router.callback_query(F.data.startswith("ad:open:"))
async def ad_open_chat(c: types.CallbackQuery):
    global reg_msg_id, reg_chat_id, reg_text
    if c.from_user.id not in ADMIN_IDS: return await c.answer("Нет доступа.")
    chat_id=int(c.data.split(":")[2])
    db=next(get_db()); t=get_active_tournament(db)
    if not t or t.status.value!="registration": return await c.answer("Нет турнира в регистрации!")
    try:
        msg=await c.bot.send_message(chat_id, f"📝 <b>Сбор на {t.name}!</b>\n\nОтветь +ник\nПример: <code>+ProPlayer</code>\n\nУчастники:\n", parse_mode="HTML")
        reg_msg_id, reg_chat_id, reg_text = msg.message_id, msg.chat.id, msg.html_text
        t.chat_id = msg.chat.id
        db.commit()
        await c.message.answer(f"✅ Сбор открыт в группе: <b>{msg.chat.title}</b>", parse_mode="HTML")
    except Exception as e:
        await c.message.answer(f"❌ Не удалось отправить в группу: {e}")
    await c.answer()

@router.message(F.reply_to_message, F.text.regexp(r'^\+(\S+)$'))
async def reg_reply(m: types.Message):
    global reg_msg_id, reg_chat_id, reg_text
    if not reg_msg_id or m.reply_to_message.message_id!=reg_msg_id: return
    nick=REG.match(m.text).group(1)
    db=next(get_db()); t=get_active_tournament(db)
    if not t or t.status.value!="registration": return
    ex=db.query(Participant).filter(Participant.tournament_id==t.id, Participant.user_id==m.from_user.id).first()
    if ex: return await m.answer("Уже зарегистрирован!")
    p=register_participant(db,t.id,m.from_user.id,m.from_user.username or "",nick)
    if p:
        ln=f"@{m.from_user.username} ({nick})\n" if m.from_user.username else f"{m.from_user.full_name} ({nick})\n"
        reg_text+=ln
        await m.bot.edit_message_text(chat_id=reg_chat_id, message_id=reg_msg_id, text=reg_text, parse_mode="HTML")
        await m.answer("✅ Зарегистрирован!")
    else: await m.answer("❌ Ошибка (возможно нет мест).")

@router.callback_query(F.data=="ad:list")
async def ad_list(c: types.CallbackQuery):
    db=next(get_db()); t=get_active_tournament(db)
    if not t: return await c.answer("Нет турнира!")
    txt=f"<b>📋 Участники {t.name}:</b>\n\n"
    for p in t.participants: txt+=f"• {p.game_nickname} (@{p.username})\n"
    await c.message.answer(txt, parse_mode="HTML")
    await c.answer()

@router.callback_query(F.data=="ad:close")
async def ad_close(c: types.CallbackQuery):
    db=next(get_db()); t=get_active_tournament(db)
    if not t or t.status.value!="registration": return await c.answer("Нет турнира для закрытия!")
    target_chat=t.chat_id
    if not target_chat:
        return await c.message.answer("❌ Не найден чат регистрации. Открой регистрацию заново.")
    t2=close_registration(db,t.id)
    if not t2: return await c.answer("Недостаточно участников!")
    await c.message.answer(f"🔒 Регистрация закрыта. Участников: {len(t2.participants)}. Жеребьевка в группе...")
    await c.bot.send_message(target_chat, f"🔒 Регистрация закрыта. Участников: {len(t2.participants)}.\n🎲 Жеребьевка...")
    for g in t2.groups:
        await c.bot.send_message(target_chat, f"<b>{g.name}:</b>\nНачинаю жеребьевку...", parse_mode="HTML")
        await asyncio.sleep(1)
        names=[f"{p.game_nickname} (@{p.username})" for p in g.participants]
        txt=f"<b>{g.name}:</b>\n"
        msg=await c.bot.send_message(target_chat, txt, parse_mode="HTML")
        for i,nm in enumerate(names,1):
            txt+=f"{i}. {nm}\n"
            await msg.edit_text(txt, parse_mode="HTML")
            await asyncio.sleep(0.8)
    await c.bot.send_message(target_chat, "✅ Жеребьевка завершена!\n\nКаждый с каждым — 2 матча.\nНапишите боту в личку <code>с кем я играю</code>\nРезультат матча прямо в группе: <code>@user выиграл 3-0 @opp</code>", parse_mode="HTML")
    await c.message.answer("✅ Жеребьевка проведена в группе.")
    await c.answer()

@router.message(F.text.lower().contains("с кем я играю"))
async def my_matches(m: types.Message):
    db=next(get_db()); t=get_active_tournament(db)
    if not t or t.status.value!="active": return await m.answer("Нет активного турнира.")
    mt=get_user_matches(db,t.id,m.from_user.id)
    if not mt: return await m.answer("Ты не в турнире.")
    txt="<b>Твои матчи:</b>\n\n"
    for i,x in enumerate(mt,1):
        if x['finished']: txt+=f"{i}. {x['opponent']} — {x['my_score']}:{x['opponent_score']} ✅\n"
        else: txt+=f"{i}. {x['opponent']} (TG: @{x['opponent_tg']}) ⏳\n"
    rem=[x for x in mt if not x['finished']]
    if rem:
        txt+="\n<b>Осталось сыграть:</b>\n"
        for x in rem: txt+=f"• {x['opponent']} (@{x['opponent_tg']})\n"
    await m.answer(txt, parse_mode="HTML")

async def _proc_result(m: types.Message, is_draw=False):
    db=next(get_db()); t=get_active_tournament(db)
    if not t or t.status.value!="active": return
    r=(DRW if is_draw else RES).match(m.text)
    if not r: return
    tg1,s1,s2,tg2=r.groups()
    p1=db.query(Participant).filter(Participant.tournament_id==t.id, Participant.username==tg1.lstrip("@")).first()
    p2=db.query(Participant).filter(Participant.tournament_id==t.id, Participant.username==tg2.lstrip("@")).first()
    if not p1 or not p2: return await m.reply("Не нашёл участника по @username.")
    mt=find_match_by_players(db,t.id,p1.id,p2.id)
    if not mt: return await m.reply("Матч не найден или уже сыгран.")
    s1=int(s1); s2=int(s2)
    if is_draw and s1!=s2: return await m.reply("При ничье счёт должен быть равным.")
    submit_match_result(db,mt.id,s1,s2)
    await m.reply(f"✅ Результат сохранён: {p1.game_nickname} {s1}:{s2} {p2.game_nickname}")

@router.message(F.text.regexp(r'@(\S+)\s+(?:выиграл|победил|won)\s+(\d+)[\s:\-](\d+)\s+@(\S+)', flags=re.I))
async def res_win(m: types.Message): await _proc_result(m, is_draw=False)

@router.message(F.text.regexp(r'@(\S+)\s+(?:ничья|draw)\s+(\d+)[\s:\-](\d+)\s+@(\S+)', flags=re.I))
async def res_draw(m: types.Message): await _proc_result(m, is_draw=True)

@router.message(F.photo)
async def handle_photo(m: types.Message):
    db=next(get_db()); t=get_active_tournament(db)
    if not t or t.status.value!="active": return
    participant=db.query(Participant).filter(Participant.tournament_id==t.id, Participant.user_id==m.from_user.id).first()
    if not participant:
        return await m.reply("Ты не участник турнира.")
    # незавершённые матчи игрока
    pending=db.query(Match).filter(
        Match.tournament_id==t.id,
        Match.status=="pending",
        ((Match.player1_id==participant.id) | (Match.player2_id==participant.id))
    ).all()
    if not pending:
        return await m.reply("У тебя нет незавершённых матчей.")
    status_msg=await m.reply("📸 Распознаю скриншот...")
    try:
        photo=m.photo[-1]  # самое большое фото
        file=await m.bot.get_file(photo.file_id)
        buf=BytesIO()
        await m.bot.download_file(file.file_path, destination=buf)
        buf.seek(0)
        text=await recognize_image(buf)
    except Exception as e:
        return await status_msg.edit_text(f"❌ Ошибка OCR: {e}")
    score=parse_score(text)
    if not score:
        return await status_msg.edit_text(
            "❌ Не удалось распознать счёт на скриншоте.\n\nВведи результат текстом:\n"
            "<code>@твой_ник выиграл 3-0 @ник_соперника</code>",
            parse_mode="HTML"
        )
    s1,s2=score
    # кнопки с соперниками
    rows=[]
    for mt in pending:
        opp = mt.player2 if mt.player1_id==participant.id else mt.player1
        if not opp: continue
        # порядок очков: для игрока s1 — его, s2 — сопернику
        # в match player1 может быть как мы, так и соперник
        rows.append([InlineKeyboardButton(
            text=f"vs {opp.game_nickname} ({s1}:{s2})",
            callback_data=f"ocr:{mt.id}:{s1}:{s2}:{participant.id}"
        )])
    rows.append([InlineKeyboardButton(text="🔁 Перевернуть счёт", callback_data=f"ocrflip:{s1}:{s2}")])
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="ocrcancel")])
    kb=InlineKeyboardMarkup(inline_keyboard=rows)
    await status_msg.edit_text(
        f"📸 Распознан счёт: <b>{s1}:{s2}</b>\n\nВыбери соперника:",
        parse_mode="HTML",
        reply_markup=kb
    )


@router.callback_query(F.data.startswith("ocrflip:"))
async def ocr_flip(c: types.CallbackQuery):
    _, s1, s2 = c.data.split(":")
    s1, s2 = int(s1), int(s2)
    # просто показываем тот же список, но счёт поменян
    db=next(get_db()); t=get_active_tournament(db)
    if not t: return await c.answer("Нет турнира.")
    participant=db.query(Participant).filter(Participant.tournament_id==t.id, Participant.user_id==c.from_user.id).first()
    if not participant: return await c.answer("Ты не участник.")
    pending=db.query(Match).filter(
        Match.tournament_id==t.id,
        Match.status=="pending",
        ((Match.player1_id==participant.id) | (Match.player2_id==participant.id))
    ).all()
    ns1, ns2 = s2, s1
    rows=[]
    for mt in pending:
        opp = mt.player2 if mt.player1_id==participant.id else mt.player1
        if not opp: continue
        rows.append([InlineKeyboardButton(
            text=f"vs {opp.game_nickname} ({ns1}:{ns2})",
            callback_data=f"ocr:{mt.id}:{ns1}:{ns2}:{participant.id}"
        )])
    rows.append([InlineKeyboardButton(text="🔁 Перевернуть счёт", callback_data=f"ocrflip:{ns1}:{ns2}")])
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="ocrcancel")])
    kb=InlineKeyboardMarkup(inline_keyboard=rows)
    await c.message.edit_text(
        f"📸 Распознан счёт: <b>{ns1}:{ns2}</b>\n\nВыбери соперника:",
        parse_mode="HTML",
        reply_markup=kb
    )
    await c.answer("Счёт перевёрнут")


@router.callback_query(F.data=="ocrcancel")
async def ocr_cancel(c: types.CallbackQuery):
    await c.message.edit_text("❌ Отменено. Введи результат текстом: <code>@твой_ник выиграл 3-0 @соперник</code>", parse_mode="HTML")
    await c.answer()


@router.callback_query(F.data.startswith("ocr:"))
async def ocr_submit(c: types.CallbackQuery):
    _, match_id, s1, s2, player_id = c.data.split(":")
    match_id, s1, s2, player_id = int(match_id), int(s1), int(s2), int(player_id)
    db=next(get_db())
    mt=db.query(Match).filter(Match.id==match_id, Match.status=="pending").first()
    if not mt:
        return await c.answer("Матч уже сыгран или не найден.", show_alert=True)
    # убедимся что нажал один из участников матча
    if c.from_user.id not in [mt.player1.user_id if mt.player1 else None, mt.player2.user_id if mt.player2 else None]:
        return await c.answer("Только участники этого матча могут подтвердить.", show_alert=True)
    # s1:s2 были с точки зрения отправителя (player_id). Сопоставим с player1/player2.
    if mt.player1_id == player_id:
        p1_score, p2_score = s1, s2
    else:
        p1_score, p2_score = s2, s1
    submit_match_result(db, mt.id, p1_score, p2_score)
    p1n = mt.player1.game_nickname if mt.player1 else "?"
    p2n = mt.player2.game_nickname if mt.player2 else "?"
    await c.message.edit_text(
        f"✅ Результат сохранён:\n<b>{p1n} {p1_score}:{p2_score} {p2n}</b>",
        parse_mode="HTML"
    )
    await c.answer("Сохранено!")

