from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import json

from channels.layers import get_channel_layer

from game.models import GameSession, Player


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
                "active_player_character_name": current_turn.active_player.character_name  # noqa
                if current_turn.active_player
                else None,
            },
            "chat_messages": list(
                game_session.chat_messages.values(
                    "id",
                    "text",
                    "sender",
                    "timestamp",
                    "reaction",
                )
            ),
        }

        return game_state

    @database_sync_to_async
    def save_game_turn(self, game_turn):
        game_turn.save()

    # Receive message from WebSocket

    async def receive(self, text_data, bytes_data=None):
        data_json = json.loads(text_data)
        print(data_json)
        action = data_json["action"]
        value = data_json["value"]

        # Map the action to a handler function
        if action == "select_narrative":
            await self.make_narrative_choice(value)
        elif action == "submit_question":
            await self.select_question(value)
        elif action == "submit_answer":
            await self.answer_question(value)
        elif action == "react_emoji":
            await self.react_emoji(value)
        elif action == "moon_phase":
            await self.moon_phase(value)
        elif action == "end_game":
            await self.end_game(value)

    def make_narrative_choice_sync(self, narrative, player):
        game_id = self.game_id
        game_session = GameSession.objects.get(game_id=game_id)
        game_turn = game_session.current_game_turn
        game_turn.make_narrative_choice(narrative, player)
        game_turn.save()

    async def make_narrative_choice(self, narrative):
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.send_json(
                {"error": "You must be logged in to select a question."}
            )
            return

        player = await database_sync_to_async(Player.objects.get)(user=user)

        try:
            await database_sync_to_async(self.make_narrative_choice_sync)(
                narrative, player
            )
            # Broadcast the new state
            await self.broadcast_game_state()
        except ValueError as e:
            await self.send_json({"error": str(e)})

    def select_question_sync(self, question, player):
        game_id = self.game_id
        game_session = GameSession.objects.get(game_id=game_id)
        game_turn = game_session.current_game_turn
        game_turn.select_question(question, player)
        game_turn.save()

    async def select_question(self, question):
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.send_json(
                {"error": "You must be logged in to select a question."}
            )
            return

        player = await database_sync_to_async(Player.objects.get)(user=user)

        try:
            await database_sync_to_async(self.select_question_sync)(question, player)
            await self.broadcast_game_state()
        except ValueError as e:
            await self.send_json({"error": str(e)})

    def answer_question_sync(self, answer, player):
        game_id = self.game_id
        game_session = GameSession.objects.get(game_id=game_id)
        game_turn = game_session.current_game_turn
        game_turn.answer_question(answer, player)
        game_turn.save()

    async def answer_question(self, answer):
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.send_json(
                {"error": "You must be logged in to select a question."}
            )
            return

        player = await database_sync_to_async(Player.objects.get)(user=user)

        try:
            await database_sync_to_async(self.answer_question_sync)(answer, player)
            # Broadcast the new state
            await self.broadcast_game_state()
        except ValueError as e:
            await self.send_json({"error": str(e)})

    def react_with_emoji_sync(self, emoji, player):
        game_id = self.game_id
        game_session = GameSession.objects.get(game_id=game_id)
        game_turn = game_session.current_game_turn
        game_turn.react_with_emoji(emoji, player)
        game_turn.save()

    async def react_emoji(self, emoji):
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.send_json(
                {"error": "You must be logged in to select a question."}
            )
            return

        player = await database_sync_to_async(Player.objects.get)(user=user)
        try:
            await database_sync_to_async(self.react_with_emoji_sync)(emoji, player)
            # Broadcast the new state
            await self.broadcast_game_state()
        except ValueError as e:
            await self.send_json({"error": str(e)})

    def write_message_about_moon_phase_sync(self, message, player):
        game_id = self.game_id
        game_session = GameSession.objects.get(game_id=game_id)
        game_turn = game_session.current_game_turn
        game_turn.write_message_about_moon_phase(message, player)
        game_turn.save()

    async def moon_phase(self, moon_meaning):
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.send_json(
                {"error": "You must be logged in to select a question."}
            )
            return

        player = await database_sync_to_async(Player.objects.get)(user=user)

        try:
            await database_sync_to_async(self.write_message_about_moon_phase_sync)(
                moon_meaning, player
            )
            # Broadcast the new state
            await self.broadcast_game_state()
        except ValueError as e:
            await self.send_json({"error": str(e)})
            # There were partial changes to the game state, so broadcast the new state
            await self.broadcast_game_state()

    async def end_game(self, game_id):
        try:
            end_game_url = f"/game/end_game_session/{game_id}/"
            channel_layer = get_channel_layer()
            group_name = f"game_{game_id}"

            # Broadcast the message to the group
            await channel_layer.group_send(
                group_name,
                {
                    "type": "group_message",
                    "message": {"command": "navigate", "url": end_game_url},
                },
            )

        except ValueError as e:
            await self.send_json({"error": str(e)})

        # Handler for group messages

    async def group_message(self, event):
        # Send a message down to the client
        await self.send_json(event["message"])

    async def broadcast_game_state(self):
        # Get the current game state
        # game_state = await self.get_game_state()
        # Broadcast the new game state to all players in the game session
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                "type": "game_state_update",
                "content": {
                    "command": "refresh",  # Command to tell the client to refresh
                    # "game_state": game_state,  # The current game state
                },
            },
        )

    async def game_state_update(self, event):
        # Send the refresh command and game state to the WebSocket
        await self.send_json(event["content"])
