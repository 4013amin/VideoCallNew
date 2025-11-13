# videocall/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
import asyncio

class VideoCallConsumer(AsyncWebsocketConsumer):
    active_users = {} # Dict to store active users: {user_id: peer_id}
    waiting_users = asyncio.Queue() # Queue for users waiting for a partner

    async def connect(self):
        # Ensure the user is authenticated
        if not self.scope["user"].is_authenticated:
            await self.close()
            return

        self.user = self.scope["user"]
        self.peer_id = self.scope['url_route']['kwargs']['peer_id']

        # Add user to active_users and queue
        VideoCallConsumer.active_users[self.user.id] = self.peer_id
        print(f"User {self.user.username} (Peer ID: {self.peer_id}) connected. Active users: {VideoCallConsumer.active_users}")

        await self.channel_layer.group_add(
            str(self.user.id), # Group name is user's ID
            self.channel_name
        )
        await self.accept()

        # Try to find a partner immediately if someone is waiting
        await self.find_partner_logic()

    async def disconnect(self, close_code):
        # Remove user from active_users and inform partner if any
        if self.user.id in VideoCallConsumer.active_users:
            del VideoCallConsumer.active_users[self.user.id]
            print(f"User {self.user.username} disconnected. Active users: {VideoCallConsumer.active_users}")

        # Remove from waiting queue if present
        if not VideoCallConsumer.waiting_users.empty():
            try:
                # Attempt to remove if user is still in queue (non-blocking)
                # This part is tricky with asyncio.Queue, might need to iterate
                # For simplicity, we just let it be; the next `get` will skip disconnected peers.
                pass
            except ValueError:
                pass # User not in queue

        # Inform the partner if there was an active call
        # This requires keeping track of who is connected to whom,
        # which is best done with a dedicated 'room' or 'call' state.
        # For now, we rely on PeerJS to detect partner disconnect.

        await self.channel_layer.group_discard(
            str(self.user.id),
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'find_partner':
            await self.find_partner_logic()
        elif message_type == 'end_call':
            await self.handle_end_call()

    async def find_partner_logic(self):
        # Put current user in waiting queue
        if self.user.id not in [user_id for user_id, _ in VideoCallConsumer.waiting_users._queue]:
            await VideoCallConsumer.waiting_users.put((self.user.id, self.peer_id))
            print(f"User {self.user.username} added to waiting queue.")

        # Try to find a partner
        while VideoCallConsumer.waiting_users.qsize() >= 2:
            try:
                user1_id, peer1_id = await VideoCallConsumer.waiting_users.get()
                user2_id, peer2_id = await VideoCallConsumer.waiting_users.get()

                # Ensure both users are still connected
                if user1_id not in VideoCallConsumer.active_users:
                    print(f"User {user1_id} is no longer active, skipping.")
                    continue # Try again with next user
                if user2_id not in VideoCallConsumer.active_users:
                    print(f"User {user2_id} is no longer active, skipping.")
                    await VideoCallConsumer.waiting_users.put((user1_id, peer1_id)) # Put user1 back
                    continue

                # If they are the same user (shouldn't happen with queue logic, but for safety)
                if user1_id == user2_id:
                    print(f"User {user1_id} matched with themselves, re-queuing.")
                    await VideoCallConsumer.waiting_users.put((user1_id, peer1_id))
                    continue


                # Notify both users that a partner is found
                await self.channel_layer.group_send(
                    str(user1_id),
                    {
                        'type': 'partner.found',
                        'partner_user_id': user2_id,
                        'partner_peer_id': peer2_id,
                    }
                )
                await self.channel_layer.group_send(
                    str(user2_id),
                    {
                        'type': 'partner.found',
                        'partner_user_id': user1_id,
                        'partner_peer_id': peer1_id,
                    }
                )
                print(f"Matched {user1_id} (Peer:{peer1_id}) with {user2_id} (Peer:{peer2_id})")
                return # A match was made
            except asyncio.QueueEmpty:
                break # No more users in queue to match

        # If only one user is waiting, or no one
        if VideoCallConsumer.waiting_users.qsize() == 1:
            print(f"User {self.user.username} is waiting for a partner.")
            # Optionally, notify the user that they are waiting
            await self.send(text_data=json.dumps({
                'type': 'waiting_for_partner',
                'message': 'You are waiting for a partner to connect.'
            }))
        elif VideoCallConsumer.waiting_users.qsize() == 0:
             await self.send(text_data=json.dumps({
                'type': 'no_partner_found',
                'message': 'No other users currently available.'
            }))


    async def handle_end_call(self):
        # When a user explicitly ends the call, inform their partner
        # This requires tracking current calls, e.g., in a dictionary:
        # {user_id: partner_user_id}
        # For simplicity here, we assume PeerJS will handle the call ending client-side
        # and the WebSocket message is mainly to clean up server-side state if needed.
        # Here, we can just send a message back to the client that initiated the end_call
        # or add logic to find its current partner and inform them.

        # Simple approach: If a partner was established via 'partner_found', try to notify them
        # This requires the consumer to store the current partner's ID
        # For a robust solution, you'd need a room concept on the server side.
        print(f"User {self.user.username} ended call.")
        # You could add logic here to inform the partner if you track active calls server-side.
        # For now, we rely on PeerJS client-side disconnect for the other party.
        # The `endCall()` function on client side will send this message,
        # and also removes their stream.

    # Handlers for messages sent to groups
    async def partner_found(self, event):
        partner_peer_id = event['partner_peer_id']
        await self.send(text_data=json.dumps({
            'type': 'partner_found',
            'partner_peer_id': partner_peer_id
        }))