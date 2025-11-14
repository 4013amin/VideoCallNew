# videocall/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from users.models import Profile  # <<< وارد کردن مدل پروفایل
import asyncio


# --- Async Database Helpers ---
@database_sync_to_async
def get_user_profile(user):
    return Profile.objects.get(user=user)


@database_sync_to_async
def deduct_coin(user):
    profile = Profile.objects.get(user=user)
    if profile.coins > 0:
        profile.coins -= 1
        profile.save()
        return profile.coins
    return 0


class VideoCallConsumer(AsyncWebsocketConsumer):
    active_users = {}
    waiting_users = asyncio.Queue()
    # A dictionary to track active calls {user_id: partner_id}
    active_calls = {}

    async def connect(self):
        if not self.scope["user"].is_authenticated:
            await self.close()
            return

        self.user = self.scope["user"]
        self.peer_id = self.scope['url_route']['kwargs']['peer_id']
        VideoCallConsumer.active_users[self.user.id] = self.peer_id

        print(f"User {self.user.username} (Peer ID: {self.peer_id}) connected.")

        await self.channel_layer.group_add(str(self.user.id), self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if self.user.id in VideoCallConsumer.active_users:
            del VideoCallConsumer.active_users[self.user.id]

        # If user was in a call, notify the partner
        partner_id = VideoCallConsumer.active_calls.pop(self.user.id, None)
        if partner_id:
            VideoCallConsumer.active_calls.pop(partner_id, None)
            await self.channel_layer.group_send(
                str(partner_id),
                {'type': 'call.ended.by.partner'}
            )

        print(f"User {self.user.username} disconnected.")
        await self.channel_layer.group_discard(str(self.user.id), self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'find_partner':
            await self.find_partner_logic()
        elif message_type == 'end_call':
            await self.handle_end_call()

    async def find_partner_logic(self):
        # <<< CHECK COINS BEFORE QUEUING >>>
        profile = await get_user_profile(self.user)
        if profile.coins <= 0:
            await self.send(text_data=json.dumps({
                'type': 'out_of_coins',
                'message': 'You have no coins left. Please purchase more to make a call.'
            }))
            print(f"User {self.user.username} has no coins. Call rejected.")
            return

        # Put user in waiting queue
        if self.user.id not in [uid for uid, _ in VideoCallConsumer.waiting_users._queue]:
            await VideoCallConsumer.waiting_users.put((self.user.id, self.peer_id))
            print(f"User {self.user.username} added to waiting queue.")

        # Try to find a partner
        if VideoCallConsumer.waiting_users.qsize() >= 2:
            user1_id, peer1_id = await VideoCallConsumer.waiting_users.get()
            user2_id, peer2_id = await VideoCallConsumer.waiting_users.get()

            user1 = await User.objects.aget(id=user1_id)
            user2 = await User.objects.aget(id=user2_id)

            # <<< DEDUCT COINS ON MATCH >>>
            new_coins1 = await deduct_coin(user1)
            new_coins2 = await deduct_coin(user2)

            VideoCallConsumer.active_calls[user1_id] = user2_id
            VideoCallConsumer.active_calls[user2_id] = user1_id

            # Notify users about the match
            await self.channel_layer.group_send(str(user1_id), {
                'type': 'partner.found', 'partner_peer_id': peer2_id
            })
            await self.channel_layer.group_send(str(user2_id), {
                'type': 'partner.found', 'partner_peer_id': peer1_id
            })

            # Notify users about their new coin balance
            await self.channel_layer.group_send(str(user1_id), {
                'type': 'coin.update', 'coins': new_coins1
            })
            await self.channel_layer.group_send(str(user2_id), {
                'type': 'coin.update', 'coins': new_coins2
            })

            print(f"Matched {user1.username} with {user2.username}. Coins deducted.")
        else:
            await self.send(text_data=json.dumps({'type': 'waiting_for_partner'}))

    async def handle_end_call(self):
        partner_id = VideoCallConsumer.active_calls.pop(self.user.id, None)
        if partner_id:
            VideoCallConsumer.active_calls.pop(partner_id, None)
            await self.channel_layer.group_send(
                str(partner_id),
                {'type': 'call.ended.by.partner'}
            )
        print(f"User {self.user.username} ended the call.")

    # Handlers for group messages
    async def partner_found(self, event):
        await self.send(text_data=json.dumps({
            'type': 'partner_found', 'partner_peer_id': event['partner_peer_id']
        }))

    async def coin_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'coin_update', 'coins': event['coins']
        }))

    async def call_ended_by_partner(self, event):
        await self.send(text_data=json.dumps({'type': 'call_ended_by_partner'}))