/**
 * LiveKit Voice Integration for MakTek Frontend
 * Handles real-time voice conversations with LiveKit agents
 */

import { Room, Participant, Track } from "livekit-client";

const API_BASE_URL = "http://localhost:8000";

class LiveKitVoiceManager {
  constructor() {
    this.room = null;
    this.url = null;
    this.token = null;
    this.isConnected = false;
  }

  /**
   * Request a LiveKit token from the backend
   */
  async getToken(userId, roomName = "support-agent") {
    try {
      const response = await fetch(`${API_BASE_URL}/livekit-token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          room_name: roomName,
          duration_minutes: 60,
        }),
      });

      if (!response.ok) {
        throw new Error(`Token request failed: ${response.status}`);
      }

      const data = await response.json();
      console.log("✓ LiveKit token received");
      return data;
    } catch (error) {
      console.error("Error getting LiveKit token:", error);
      throw error;
    }
  }

  /**
   * Connect to LiveKit room for voice conversation
   */
  async connectToVoiceRoom(userId, roomName = "support-agent") {
    try {
      console.log("Connecting to LiveKit room...");

      // Get token from backend
      const tokenData = await this.getToken(userId, roomName);
      this.token = tokenData.token;
      this.url = tokenData.url;

      // Create and connect room
      this.room = new Room({
        adaptiveStream: true,
        dynacast: true,
      });

      // Set up event listeners
      this.room.on("participantConnected", (participant) => {
        console.log(`Agent joined: ${participant.identity}`);
        this._onAgentConnected(participant);
      });

      this.room.on("participantDisconnected", (participant) => {
        console.log(`Agent disconnected: ${participant.identity}`);
      });

      this.room.on("trackSubscribed", (track, publication, participant) => {
        this._onTrackSubscribed(track, participant);
      });

      // Connect to the room
      await this.room.connect(this.url, this.token);
      await this.room.localParticipant.setMicrophoneEnabled(true);
      this.isConnected = true;

      console.log("✓ Connected to LiveKit room");
      return { success: true, room: roomName };
    } catch (error) {
      console.error("Error connecting to voice room:", error);
      throw error;
    }
  }

  /**
   * Disconnect from LiveKit room
   */
  async disconnect() {
    try {
      if (this.room) {
        await this.room.localParticipant.setMicrophoneEnabled(false);
        await this.room.disconnect();
        this.isConnected = false;
        console.log("✓ Disconnected from LiveKit");
      }
    } catch (error) {
      console.error("Error disconnecting:", error);
    }
  }

  /**
   * Send a message to the agent (text-based, not voice)
   */
  async sendMessage(message, userId, threadId) {
    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: message,
          user_id: userId,
          thread_id: threadId,
        }),
      });

      if (!response.ok) {
        throw new Error(`Message send failed: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error sending message:", error);
      throw error;
    }
  }

  /**
   * Handle when agent connects
   */
  _onAgentConnected(participant) {
    console.log("Agent participant connected:", participant.identity);
  }

  /**
   * Handle when audio track is subscribed
   */
  _onTrackSubscribed(track, participant) {
    if (track.kind === Track.Kind.Audio) {
      const audio = document.createElement("audio");
      audio.autoplay = true;
      audio.playsinline = true;
      audio.muted = false;

      const mediaStream = new MediaStream();
      mediaStream.addTrack(track.mediaStreamTrack);
      audio.srcObject = mediaStream;

      document.body.appendChild(audio);
      console.log("✓ Agent audio track playing");
    }
  }

  /**
   * Get current connection status
   */
  getStatus() {
    return {
      connected: this.isConnected,
      room: this.room?.name || null,
      participants: this.room?.participants.size || 0,
    };
  }
}

// Export for use in main app
export default LiveKitVoiceManager;
