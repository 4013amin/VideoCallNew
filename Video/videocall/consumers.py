# videocall/consumers.py
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from users.models import Profile

# --- Database Helpers ---
@database_sync_to_async
def get_user_coins(user):
    return user.profile.coins

@database_sync_to_async
def deduct_coin(user):
    try:
        profile = Profile.objects.select_for_update().get(user=user)
        if profile.coins > 0:
            profile.coins -= 1
            profile.save()
            return profile.coins
    except Exception as e:
        print(f"Error deducting coin: {e}")
    return -1

class VideoCallConsumer(AsyncWebsocketConsumer):
    # صف انتظار سراسری (در حافظه)
    waiting_users = []
    # قفل برای جلوگیری از تداخل درخواست‌ها
    queue_lock = asyncio.Lock()

    async def connect(self):
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return

        self.peer_id = self.scope['url_route']['kwargs']['peer_id']
        self.room_group_name = f"user_{self.user.id}"

        # پیوستن به گروه اختصاصی کاربر
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        print(f"User {self.user.username} connected. PeerID: {self.peer_id}")

    async def disconnect(self, close_code):
        # حذف کاربر از صف با رعایت قفل
        async with VideoCallConsumer.queue_lock:
            VideoCallConsumer.waiting_users = [
                u for u in VideoCallConsumer.waiting_users 
                if u['channel_name'] != self.channel_name
            ]
        
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"User {self.user.username} disconnected.")

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'find_partner':
            await self.match_logic()
        
        elif message_type == 'end_call':
            # فقط لاگ می‌گیریم، قطع کردن واقعی در فرانت هندل می‌شود
            pass

    async def match_logic(self):
        # 1. بررسی سکه
        coins = await get_user_coins(self.user)
        if coins <= 0:
            await self.send(text_data=json.dumps({'type': 'out_of_coins'}))
            return

        async with VideoCallConsumer.queue_lock:
            # 2. بررسی اینکه آیا کسی در صف هست؟
            if len(VideoCallConsumer.waiting_users) > 0:
                # برداشتن نفر اول از صف
                partner = VideoCallConsumer.waiting_users.pop(0)

                # جلوگیری از اتصال به خود (اگر کاربر سریع دو بار کلیک کرد)
                if partner['user_id'] == self.user.id:
                    VideoCallConsumer.waiting_users.append(partner)
                    return

                # 3. کسر سکه از من (درخواست دهنده فعلی)
                new_coins = await deduct_coin(self.user)
                
                # برای پارتنر: چون سوکتش باز است، پیام می‌فرستیم تا کلاینت او درخواست کسر سکه کند 
                # یا در اینجا هندل کنیم (ساده‌تر: فقط از کسی که مچ شد کم کنیم یا هر دو)
                # در اینجا فرض بر کسر از هر دو است. اما چون Async است، پارتنر را هم خبر می‌کنیم.

                # 4. اطلاع به من (Initiator) -> تو باید تماس بگیری
                await self.send(text_data=json.dumps({
                    'type': 'partner_found',
                    'role': 'initiator',
                    'partner_peer_id': partner['peer_id'],
                    'coins': new_coins
                }))

                # 5. اطلاع به پارتنر (Receiver) -> تو باید تماس دریافت کنی
                await self.channel_layer.send(
                    partner['channel_name'],
                    {
                        'type': 'send_match_info',
                        'partner_peer_id': self.peer_id,
                        'role': 'receiver'
                    }
                )
                
                print(f"Match success: {self.user.username} <--> UserID {partner['user_id']}")

            else:
                # کسی نیست، من میرم تو صف
                VideoCallConsumer.waiting_users.append({
                    'channel_name': self.channel_name,
                    'user_id': self.user.id,
                    'peer_id': self.peer_id
                })
                await self.send(text_data=json.dumps({'type': 'waiting_in_queue'}))

    # --- Group Message Handlers ---
    
    async def send_match_info(self, event):
        # این متد برای پارتنر اجرا می‌شود
        # اینجا سکه پارتنر را کم می‌کنیم
        new_coins = await deduct_coin(self.user)
        
        await self.send(text_data=json.dumps({
            'type': 'partner_found',
            'role': event['role'],
            'partner_peer_id': event['partner_peer_id'],
            'coins': new_coins
        }))