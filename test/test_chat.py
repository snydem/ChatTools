import unittest
import configparser as cfgparse
import path
from chattools.chat import Chat


class ChatTest(unittest.TestCase):
    def setUp(self):
        config = cfgparse.ConfigParser()
        config.read(path.Path("cfg/Oauth.ini"))

        # NOTE: I just needed a 24 hour channel
        self.connect_channel = "starsmitten"

        self.oauth = config["AUTHORIZATION"]["token"]
        self.nickname = config["AUTHORIZATION"]["nickname"]

        self.chat = Chat(self.oauth, self.connect_channel, self.nickname)

    def test_chat_connect(self):
        result = self.chat.connect()
        self.assertIsNone(result)

    def test_chat_read(self):
        self.chat.connect()
        msg = self.chat.read_chat()
        self.assertIsInstance(msg, str)

    def test_chat_multiple_reads(self):
        self.chat.connect()
        for i in range(20):
            msg = self.chat.read_chat()
            print(msg)
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
