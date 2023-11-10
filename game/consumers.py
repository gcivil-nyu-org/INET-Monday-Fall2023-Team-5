from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import json

from game.models import GameTurn, GameSession, Player


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope["url_route"]["kwargs"]["game_id"]
        self.game_group_name = f"game_{self.game_id}"

        # Join room group
        await self.channel_layer.group_add(self.game_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.game_group_name, self.channel_name)

    async def send_json(self, content, close=False):
        """
        This method sends a JSON response to the client.
        """
        await self.send(text_data=json.dumps(content), close=close)

    @database_sync_to_async
    def get_game_session(self, game_id):
        return GameSession.objects.get(id=game_id)

    @database_sync_to_async
    def save_game_turn(self, game_turn):
        game_turn.save()

    # Receive message from WebSocket

    async def receive(self, text_data=None, bytes_data=None):
        data_json = json.loads(text_data)
        action = data_json["action"]

        # Map the action to a handler function
        if action == "select_narrative":
            await self.make_narrative_choice(data_json["narrative"])
        elif action == "select_question":
            await self.select_question(data_json["value"])
        elif action == "answer_question":
            await self.answer_question(data_json["value"])
        elif action == "react_emoji":
            await self.react_emoji(data_json["value"])
        elif action == "moon_phase":
            await self.moon_phase(data_json["value"])
        elif action == "end_game":
            await self.end_game(data_json["game_id"])

    async def make_narrative_choice(self, narrative):
        player = self.scope["user"]
        if not player.is_authenticated:
            await self.send_json(
                {"error": "You must be logged in to make a narrative choice."}
            )
            return

        try:
            game_turn = await database_sync_to_async(GameTurn.objects.get)(
                id=self.game_id
            )
            await database_sync_to_async(game_turn.make_narrative_choice)(
                narrative, player
            )
            # Broadcast the new state
            await self.broadcast_game_state()
        except ValueError as e:
            await self.send_json({"error": str(e)})

    async def select_question(self, question):
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.send_json(
                {"error": "You must be logged in to select a question."}
            )
            return

        player = await database_sync_to_async(Player.objects.get)(user=user)
        game_session = await database_sync_to_async(GameSession.objects.get)(
            game_id=self.game_id
        )

        # Call the select_question method on the GameTurn model
        try:
            await database_sync_to_async(
                game_session.current_game_turn.select_question
            )(question, player)
        except ValueError as e:
            await self.send_json({"error": str(e)})
            return

        # Broadcast the update to all players
        await self.broadcast_game_state()

    async def answer_question(self, answer):
        player = self.scope["user"]
        if not player.is_authenticated:
            await self.send_json(
                {"error": "You must be logged in to answer a question."}
            )
            return

        try:
            game_turn = await database_sync_to_async(GameTurn.objects.get)(
                id=self.game_id
            )
            await database_sync_to_async(game_turn.answer_question)(answer, player)
            # Broadcast the new state
            await self.broadcast_game_state()
        except ValueError as e:
            await self.send_json({"error": str(e)})

    async def react_emoji(self, emoji):
        player = self.scope["user"]
        if not player.is_authenticated:
            await self.send_json(
                {"error": "You must be logged in to react with emoji."}
            )
            return

        try:
            game_turn = await database_sync_to_async(GameTurn.objects.get)(
                id=self.game_id
            )
            await database_sync_to_async(game_turn.react_with_emoji)(emoji, player)
            # Broadcast the new state
            await self.broadcast_game_state()
        except ValueError as e:
            await self.send_json({"error": str(e)})


    async def moon_phase(self, moon_meaning):
        player = self.scope["user"]
        if not player.is_authenticated:
            await self.send_json(
                {"error": "You must be logged in to write a message about the moon phase."}
            )
            return

        try:
            game_turn = await database_sync_to_async(GameTurn.objects.get)(id=self.game_id)
            await database_sync_to_async(game_turn.write_message_about_moon_phase)(
                moon_meaning, player
            )
            # Broadcast the new state
            await self.broadcast_game_state()
        except ValueError as e:
            await self.send_json({"error": str(e)})
    async def end_game(self, game_id):

    pass

# Helper methods to send messages to the WebSocket
async def send_chat_message(self, message):
    # Call this method when you want to send a chat message to the group
    await self.channel_layer.group_send(
        self.game_group_name, {"type": "chat_message", "message": message}
    )

async def chat_message(self, event):
    # Handles the messages from send_chat_message
    message = event["message"]

    # Send message to WebSocket
    await self.send(text_data=json.dumps({"message": message}))
