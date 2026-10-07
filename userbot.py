from telethon import TelegramClient, events, Button

client = TelegramClient("my_session", 2040, "b18441a1ff607e10a989891a5462e627")
groups = {}

@client.on(events.NewMessage(incoming=True))
async def incoming(e):
    if e.is_private and not e.is_group:
        await e.forward_to("me")

@client.on(events.NewMessage(outgoing=True))
async def out(e):
    global groups
    if e.is_private and e.chat_id == (await client.get_me()).id:
        t = e.raw_text.strip()
        target_chat = e.chat_id
        
        # 1. حفظ مجموعة ضخمة دفعة واحدة (تصل إلى 1000+ مقطع): /مجموعة 1 1000
        if t.startswith("/مجموعة ") or t.startswith("/savegroup "):
            parts = t.split(" ")
            if len(parts) >= 2 and e.is_reply:
                try:
                    k = parts[1]
                    target_count = int(parts[2]) if len(parts) > 2 else 50
                    reply_msg = await e.get_reply_message()
                    start_id = reply_msg.id
                    
                    await e.edit(f"⏳ جاري فحص وسحب {target_count} مقطع، يرجى الانتظار...")
                    
                    msgs = []
                    # نطاق بحث واسع جداً لضمان تغطية العدد المطلوب حتى لو كانت هناك نصوص كثيرة بين المقاطع
                    search_limit = target_count * 15
                    
                    async for msg in client.iter_messages(target_chat, min_id=start_id - 1, limit=search_limit, reverse=True):
                        if msg.media:
                            msgs.append(msg)
                            if len(msgs) >= target_count:
                                break
                    
                    groups[k] = msgs
                    await e.edit(f"✅ تم حفظ {len(msgs)} مقطع بنجاح (مستهدف: {target_count}) تحت المفتاح: /{k}")
                except Exception as ex:
                    await e.edit(f"❌ حدث خطأ: {str(ex)}")
            else:
                await e.edit("❌ الاستخدام الصحيح: الرد على أول مقطع ثم كتابة /مجموعة <المفتاح> <العدد> (مثال: /مجموعة 1 1000)")
        
        # 2. الإضافة التدريجية مقطع بمقطع: /إضافة 1
        elif t.startswith("/إضافة ") or t.startswith("/add "):
            parts = t.split(" ")
            if len(parts) >= 2 and e.is_reply:
                try:
                    reply_msg = await e.get_reply_message()
                    if reply_msg and reply_msg.media:
                        k = parts[1]
                        if k not in groups:
                            groups[k] = []
                        groups[k].append(reply_msg)
                        await e.edit(f"✅ تمت إضافة المقطع للمفتاح: /{k}\n📁 الإجمالي الحالي: {len(groups[k])} مقطع")
                    else:
                        await e.edit("❌ خطأ: الرسالة المحددة بالرد لا تحتوي على ميديا.")
                except Exception as ex:
                    await e.edit(f"❌ حدث خطأ: {str(ex)}")
            else:
                await e.edit("❌ الاستخدام الصحيح: الرد على المقطع مع كتابة /إضافة <المفتاح>")
        
        # 3. حذف مفتاح: /حذف 1
        elif t.startswith("/حذف ") or t.startswith("/del ") or t.startswith("/delete "):
            try:
                k = t.split(" ")[1]
                if k in groups:
                    del groups[k]
                    await e.edit(f"🗑️ تم حذف المفتاح /{k} بنجاح!")
                else:
                    await e.edit(f"⚠️ المفتاح /{k} غير موجود.")
            except Exception:
                await e.edit("❌ الاستخدام الصحيح: /حذف <المفتاح>")
        
        # 4. عرض اللوحة: /قائمة
        elif t == "/قائمة" or t == "/list":
            if groups:
                buttons = []
                for k in groups.keys():
                    buttons.append([Button.inline(f"📤 إرسال /{k} ({len(groups[k])})", data=f"send_{k}".encode()),
                                    Button.inline(f"🗑️ حذف /{k}", data=f"del_{k}".encode())])
                await e.edit("📋 **لوحة تحكم المفاتيح المحفوظة:**", buttons=buttons)
            else:
                await e.edit("📭 لا توجد مفاتيح محفوظة حالياً.")
        
        # 5. إرسال مباشر بكتابة المفتاح مثل /1
        elif t.startswith("/"):
            k = t[1:]
            if k in groups:
                await e.delete()
                for msg in groups[k]:
                    await client.send_message(target_chat, msg)

# التعامل مع الأزرار الشفافة
@client.on(events.CallbackQuery)
async def callback(event):
    global groups
    data = event.data.decode()
    sender_id = event.chat_id
    
    if data.startswith("send_"):
        k = data.split("_")[1]
        if k in groups:
            await event.answer(f"جاري إرسال مجموعة /{k}...")
            for msg in groups[k]:
                await client.send_message(sender_id, msg)
        else:
            await event.answer("المفتاح غير موجود!", alert=True)
            
    elif data.startswith("del_"):
        k = data.split("_")[1]
        if k in groups:
            del groups[k]
            await event.answer(f"تم حذف المفتاح /{k}")
            await event.edit(f"🗑️ تم حذف المفتاح /{k} بنجاح.")
        else:
            await event.answer("المفتاح غير موجود مسبقاً", alert=True)

print("Bot running with support for up to 1000+ batch items...")
client.start()
client.run_until_disconnected()
