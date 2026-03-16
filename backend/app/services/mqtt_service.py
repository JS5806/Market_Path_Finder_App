"""
MQTT 통신 서비스 - IoT 장치 (ESL, Beacon, NFC) 통신
Mosquitto 브로커와 연결하여 메시지 발행/구독
"""
import json
import logging
from typing import Optional, Callable
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from app.core.config import settings

logger = logging.getLogger(__name__)


class MQTTService:
    """MQTT 클라이언트 관리 (싱글톤)"""

    def __init__(self):
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self._message_handlers: dict[str, list[Callable]] = {}

    def connect(self) -> bool:
        """MQTT 브로커에 연결합니다."""
        try:
            self.client = mqtt.Client(
                client_id="mart_backend_server",
                protocol=mqtt.MQTTv311,
            )
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message

            self.client.connect(
                settings.MQTT_BROKER_HOST,
                settings.MQTT_BROKER_PORT,
                keepalive=60,
            )
            self.client.loop_start()
            logger.info(
                f"MQTT connecting to {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}"
            )
            return True
        except Exception as e:
            logger.warning(f"MQTT connection failed: {e}")
            return False

    def disconnect(self):
        """MQTT 연결 해제"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("MQTT disconnected")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            logger.info("MQTT connected successfully")
            # 기본 토픽 구독
            client.subscribe(settings.MQTT_TOPIC_BEACON + "/#")
            client.subscribe(settings.MQTT_TOPIC_NFC + "/#")
            client.subscribe("mart/esl/status/#")
        else:
            logger.warning(f"MQTT connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        if rc != 0:
            # 비정상 연결 해제 시 재연결 중지 (로그 스팸 방지)
            logger.warning(f"MQTT disconnected (rc={rc}) - stopping reconnect loop")
            try:
                client.loop_stop()
            except Exception:
                pass
        else:
            logger.info("MQTT disconnected normally")

    def _on_message(self, client, userdata, msg):
        """메시지 수신 핸들러"""
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = msg.payload.decode("utf-8", errors="replace")

        logger.debug(f"MQTT recv [{topic}]: {payload}")

        # 등록된 핸들러 호출
        for pattern, handlers in self._message_handlers.items():
            if mqtt.topic_matches_sub(pattern, topic):
                for handler in handlers:
                    try:
                        handler(topic, payload)
                    except Exception as e:
                        logger.error(f"MQTT handler error: {e}")

    def subscribe(self, topic: str, handler: Callable):
        """토픽 구독 + 핸들러 등록"""
        if topic not in self._message_handlers:
            self._message_handlers[topic] = []
        self._message_handlers[topic].append(handler)
        if self.client and self.connected:
            self.client.subscribe(topic)

    def publish(self, topic: str, payload: dict, qos: int = 1, retain: bool = False) -> bool:
        """메시지 발행"""
        if not self.client or not self.connected:
            logger.warning(f"MQTT not connected, cannot publish to {topic}")
            return False
        try:
            message = json.dumps(payload, ensure_ascii=False, default=str)
            result = self.client.publish(topic, message, qos=qos, retain=retain)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            logger.error(f"MQTT publish error: {e}")
            return False

    # ── ESL 관련 ──

    def publish_esl_update(
        self, mac_address: str, product_name: str,
        regular_price: int, sale_price: Optional[int] = None,
        store_name: str = "",
    ) -> bool:
        """ESL(전자가격표) 업데이트 명령 발행"""
        payload = {
            "mac_address": mac_address,
            "product_name": product_name,
            "regular_price": regular_price,
            "sale_price": sale_price,
            "store_name": store_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        topic = f"{settings.MQTT_TOPIC_ESL}/{mac_address}"
        return self.publish(topic, payload, retain=True)

    # ── Beacon 관련 ──

    def publish_beacon_config(
        self, beacon_id: int, uuid: str,
        major: int, minor: int, tx_power: int = -59,
    ) -> bool:
        """비콘 설정 업데이트 발행"""
        payload = {
            "beacon_id": beacon_id,
            "uuid": uuid,
            "major": major,
            "minor": minor,
            "tx_power": tx_power,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return self.publish(f"mart/beacon/config/{beacon_id}", payload)

    # ── NFC 관련 ──

    def publish_nfc_response(
        self, tag_uid: str, product_id: str,
        product_name: str, action: str = "add_to_cart",
    ) -> bool:
        """NFC 태깅 응답 발행"""
        payload = {
            "tag_uid": tag_uid,
            "product_id": product_id,
            "product_name": product_name,
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return self.publish(f"{settings.MQTT_TOPIC_NFC}/response/{tag_uid}", payload)


# 싱글톤 인스턴스
mqtt_service = MQTTService()
