from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window
from kivy.clock import Clock
import paho.mqtt.client as mqtt
import time

class MQTTClientKivy(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = None
        self.connected = False

    def toggle_connection(self):
        if not self.connected:
            self.connect_mqtt()
        else:
            self.disconnect_mqtt()

    def connect_mqtt(self):
        broker = self.ids.broker_input.text
        port = self.ids.port_input.text
        client_id = self.ids.client_id_input.text
        username = self.ids.username_input.text
        password = self.ids.password_input.text

        if not broker or not port:
            self.log_message("错误: 必须填写Broker地址和端口", "error")
            return

        try:
            port = int(port)
        except ValueError:
            self.log_message("错误: 端口号必须是数字", "error")
            return

        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id or None)

            if username or password:
                self.client.username_pw_set(username, password)

            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_publish = self.on_publish
            self.client.on_disconnect = self.on_disconnect

            self.client.connect(broker, port, 60)
            self.client.loop_start()

            self.ids.connect_btn.text = "断开连接"
            self.log_message(f"正在连接 {broker}:{port}...")
            self.connected = True

        except Exception as e:
            self.log_message(f"连接错误: {str(e)}", "error")

    def disconnect_mqtt(self):
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            self.ids.connect_btn.text = "连接"
            self.log_message("已断开连接")

    def on_connect(self, client, userdata, flags, rc, properties):
        if rc == 0:
            self.log_message("连接成功", "success")
        else:
            self.log_message(f"连接失败，错误码: {rc}", "error")

    def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        self.connected = False
        self.ids.connect_btn.text = "连接"
        self.log_message(f"连接断开，代码: {reason_code}")

    def on_message(self, client, userdata, msg):
        Clock.schedule_once(lambda dt: self.log_message(f"收到 [{msg.topic}]: {msg.payload.decode()}", "received"))

    def on_publish(self, client, userdata, mid, reason_code, properties):
        Clock.schedule_once(lambda dt: self.log_message(f"消息 {mid} 发布成功", "info"))

    def log_message(self, message, tag=None):
        self.ids.log_text.text += f"{time.strftime('%H:%M:%S')} - {message}\n"
        self.ids.log_scroll.scroll_to(self.ids.log_text)

    def publish_message(self):
        topic = self.ids.pub_topic_input.text
        message = self.ids.message_input.text
        if not topic:
            self.log_message("警告: 必须填写发布主题", "error")
            return
        if not message:
            self.log_message("警告: 消息内容不能为空", "error")
            return

        try:
            result = self.client.publish(topic, message)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.log_message(f"已发布到 {topic}: {message}", "published")
                self.ids.message_input.text = ""
            else:
                self.log_message(f"发布失败，错误码: {result.rc}", "error")
        except Exception as e:
            self.log_message(f"发布异常: {str(e)}", "error")

    def publish_number(self, number):
        topic = self.ids.pub_topic_input.text
        if not topic:
            self.log_message("警告: 必须填写发布主题", "error")
            return

        try:
            result = self.client.publish(topic, str(number))
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.log_message(f"已发布数字 {number} 到 {topic}", "published")
            else:
                self.log_message(f"发布失败，错误码: {result.rc}", "error")
        except Exception as e:
            self.log_message(f"发布异常: {str(e)}", "error")


class MQTTApp(App):
    def build(self):
        Window.size = (600, 500)
        return MQTTClientKivy()


if __name__ == "__main__":
    MQTTApp().run()
