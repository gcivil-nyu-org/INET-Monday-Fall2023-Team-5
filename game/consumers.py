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
    def get_game_state(self):
        # Fetch the game session and related objects from the database
        game_session = GameSession.objects.get(game_id=self.game_id)
        current_turn = game_session.current_game_turn

        # Serialize the game session state into a dictionary
        game_state = {
            "game_id": game_session.game_id,
            "state": game_session.state,
            "is_active": game_session.is_active,
            "playerA": {
                "id": game_session.playerA.id,
                "character_name": game_session.playerA.character_name,
            }
            if game_session.playerA
            else None,
            "playerB": {
                "id": game_session.playerB.id,
                "character_name": game_session.playerB.character_name,
            }
            if game_session.playerB
            else None,
            "current_turn": {
                "id": current_turn.id,
                "turn_number": current_turn.turn_number,
                "state": current_turn.state,
                "active_player_id": current_turn.active_player.id
                if current_turn.active_player
                else None,
                "active_player_character_name": current_turn.active_player.character_name
                if current_turn.active_player
                else None,
            },
            "chat_messages": list(
                game_session.chat_messages.values(
                    "id", "text", "sender__character_name", "timestamp"
                )
            ),
        }

        return game_state

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
                {
                    "error": "You must be logged in to write a message about the moon phase."
                }
            )
            return

        try:
            game_turn = await database_sync_to_async(GameTurn.objects.get)(
                id=self.game_id
            )
            await database_sync_to_async(game_turn.write_message_about_moon_phase)(
                moon_meaning, player
            )
            # Broadcast the new state
            await self.broadcast_game_state()
        except ValueError as e:
            await self.send_json({"error": str(e)})

    async def end_game(self, game_id):
        try:
            game_session = await database_sync_to_async(GameSession.objects.get)(
                game_id=game_id
            )
            await database_sync_to_async(game_session.end_game)()
            await self.broadcast_game_state()
        except ValueError as e:
            await self.send_json({"error": str(e)})

    async def broadcast_game_state(self):
        # Get the current game state
        game_state = await self.get_game_state()
        # Broadcast the new game state to all players in the game session
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                "type": "game_state_update",
                "content": {
                    "command": "refresh",  # Command to tell the client to refresh
                    "game_state": game_state,  # The current game state
                },
            },
        )

    async def game_state_update(self, event):
        # Send the refresh command and game state to the WebSocket
        await self.send_json(event["content"])


# consumers.py in one of your apps

from channels.generic.websocket import AsyncWebsocketConsumer


class EchoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("WebSocket connected!")
        await self.accept()

    async def disconnect(self, close_code):
        print("WebSocket disconnected!")


class TestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("test_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("test_group", self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        await self.channel_layer.group_send(
            "test_group", {"type": "test_message", "message": message}
        )

    async def test_message(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps({"message": message}))
