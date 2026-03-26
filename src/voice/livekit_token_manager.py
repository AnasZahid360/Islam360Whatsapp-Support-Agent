"""
LiveKit token generation for frontend authentication.
Generates access tokens for users to connect to LiveKit rooms.
"""

import os
import logging
import importlib
from datetime import timedelta

logger = logging.getLogger(__name__)


class LiveKitTokenManager:
    """Manages LiveKit token generation and verification"""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
    ):
        """
        Initialize token manager.

        Args:
            api_key: LiveKit API key
            api_secret: LiveKit API secret
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self._token_verifier_cls = None
        self._access_token_cls = None
        self._video_grants_cls = None
        self._load_livekit_sdk()

    def _load_livekit_sdk(self) -> None:
        try:
            livekit_api = importlib.import_module("livekit.api")
        except ImportError as e:
            raise RuntimeError(
                "LiveKit SDK is not installed in this Python environment. Install 'livekit' and restart the backend."
            ) from e

        self._token_verifier_cls = livekit_api.TokenVerifier
        self._access_token_cls = livekit_api.AccessToken
        self._video_grants_cls = livekit_api.VideoGrants
        self.verifier = self._token_verifier_cls(self.api_key, self.api_secret)

    def create_token(
        self,
        user_id: str,
        room_name: str = "support-agent",
        duration_minutes: int = 60,
        can_publish: bool = True,
        can_subscribe: bool = True,
    ) -> str:
        """
        Generate a LiveKit access token.

        Args:
            user_id: User identifier
            room_name: LiveKit room name
            duration_minutes: Token validity duration
            can_publish: Allow user to publish audio/video
            can_subscribe: Allow user to subscribe to others' streams

        Returns:
            Access token string
        """
        try:
            grants = self._video_grants_cls(
                room_join=True,
                room=room_name,
                room_create=True,
                can_publish=can_publish,
                can_subscribe=can_subscribe,
            )

            token = (
                self._access_token_cls(api_key=self.api_key, api_secret=self.api_secret)
                .with_identity(user_id)
                .with_grants(grants)
                .with_ttl(timedelta(minutes=duration_minutes))
            )

            jwt_token = token.to_jwt()
            logger.info(f"Token generated for user: {user_id} in room: {room_name}")

            return jwt_token

        except Exception as e:
            logger.error(f"Error generating token: {e}")
            raise

    def verify_token(self, token: str) -> dict:
        """
        Verify a LiveKit access token.

        Args:
            token: JWT token string

        Returns:
            Token claims dictionary
        """
        try:
            claims = self.verifier.verify(token)
            logger.info(f"Token verified for identity: {claims.identity}")
            return {
                "identity": claims.identity,
                "room": claims.video.room,
                "valid": True,
            }
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return {"valid": False, "error": str(e)}


# Singleton instance
_token_manager: LiveKitTokenManager = None


def get_token_manager() -> LiveKitTokenManager:
    """Get or create the LiveKit token manager"""
    global _token_manager

    if _token_manager is None:
        api_key = os.getenv("LIVEKIT_API_KEY", "devkey")
        api_secret = os.getenv("LIVEKIT_API_SECRET", "secret")

        _token_manager = LiveKitTokenManager(api_key, api_secret)
        logger.info("LiveKit Token Manager initialized")

    return _token_manager
