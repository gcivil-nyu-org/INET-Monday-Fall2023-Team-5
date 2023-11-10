from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import json

from game.models import GameTurn, GameSession


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
        game_session = await self.get_game_session()
        if game_session.current_game_turn.state == GameTurn.NARRATIVE_CHOICES:
            game_session.current_game_turn.make_narrative_choice(
                narrative, self.scope["user"]
            )
            await self.save_game_turn(game_session.current_game_turn)
        pass

    async def select_question(self, question):
        game_session = await self.get_game_session()
        if game_session.current_game_turn.state == GameTurn.SELECT_QUESTION:
            game_session.current_game_turn.select_question(question, self.scope["user"])
            await self.save_game_turn(game_session.current_game_turn)

        await self.broadcast_to_group(
            self.game_group_name,
            "game.update",
            {
                "action": "question_selected",
                "question": question,
            },
        )
        pass

    async def answer_question(self, answer):
        game_session = await self.get_game_session()
        if game_session.current_game_turn.state == GameTurn.ANSWER_QUESTION:
            game_session.current_game_turn.answer_question(answer, self.scope["user"])
            await self.save_game_turn(game_session.current_game_turn)
        # Update the game state and notify players
        pass

    async def react_emoji(self, emoji):
        game_session = await self.get_game_session()
        if game_session.current_game_turn.state == GameTurn.REACT_EMOJI:
            game_session.current_game_turn.react_with_emoji(emoji, self.scope["user"])
            await self.save_game_turn(game_session.current_game_turn)
        # Update the game state and notify players
        pass

    async def moon_phase(self, moon_meaning):
        # Logic for moon phase
        game_session = await self.get_game_session()
        if game_session.current_game_turn.state == GameTurn.MOON_PHASE:
            game_session.current_game_turn.write_message_about_moon_phase(
                moon_meaning, self.scope["user"]
            )
            await self.save_game_turn(game_session.current_game_turn)
        # Broadcast the update to other players
        # ...

    async def end_game(self, game_id):
        # Handle the end_game action
        # Perform cleanup and notify players
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
