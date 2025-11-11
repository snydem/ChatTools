import socket
import errno
from datetime import datetime
from typing import Dict, Any


class Chat(object):
    twitch_server = 'irc.chat.twitch.tv'
    twitch_port = 6667

    def __init__(self, oauth_token: str, channel_name: str, nickname: str = "",
                 server: str = twitch_server, port: int = twitch_port):
        self.oauth_token = oauth_token
        self.channel_name = channel_name
        self.channel = "#" + channel_name
        self.nickname = nickname
        self.server = server
        self.port = port

        # Create an internal socket object to manage connection
        self.sock = socket.socket()

    def _send_keep_alive(self, ping_msg: str) -> None:
        """
        Helper function just to handle sending the keep alive message back to
        the server when it is received by the socket.
        """
        self.sock.send(f"PONG {ping_msg}".encode('utf-8'))

    def _send_authenticate(self) -> None:
        """
        Helper function just to send the twitch IRC auth messages to the server
        """
        self.sock.send(f"PASS {self.oauth_token}\n".encode('utf-8'))
        self.sock.send(f"NICK {self.nickname}\n".encode('utf-8'))
        self.sock.send(f"JOIN {self.channel}\n".encode('utf-8'))

    def connect(self) -> None:
        """
        Connect to a the specific twitch IRC

        returns None on success, raises an error on failure.
        """
        try:
            self.sock.connect((self.server, self.port))
            # Make the socket a non-blocking socket
            self.sock.setblocking(False)
        except Exception as e:
            raise Exception("CHAT OBJECT - THE FOLLOWING EXCEPTION OCCURED "
                            "WHEN TRYING TO CONNECT TO THE SERVER:\n" + str(e))

        self._send_authenticate()

    def send_chat(self, msg: str) -> None:
        """
        Send a chat message to the server
        """
        self.sock.send(f"PRIVMSG {self.channel} :{msg}\r\n".encode('utf-8'))

    def read_chat(self) -> Dict[str, Any]:
        """
        Read a chat if one is available on the socket.
        """
        # NOTE: If the size of the receive buffer is too large, it will be
        # the case that two chat messages can get concattenated into one. We
        # don't want this, I think the solution is to read in one byte at a
        # time and once we find the end msg delimeter (\r\n) accept that as
        # one message
        incoming_message = ""
        while True:
            try:
                resp = self.sock.recv(1)
                resp = resp.decode('utf-8')
                incoming_message += resp

                if incoming_message.endswith('\r\n'):
                    print(incoming_message)
                    # First check for for PING message
                    if incoming_message.startswith("PING"):
                        pong_msg = incoming_message.split(" ")[1]
                        self._send_keep_alive(pong_msg)
                        continue
                    # Now we need to parse the message string into a dict
                    # of usable values
                    # return incoming_message
                    split_dict = incoming_message.split(":")
                    meta_data = split_dict[1]
                    try:
                        chat_msg = split_dict[2]
                    except IndexError:
                        chat_msg = ""

                    # split up the meta data
                    chatter_name = meta_data.split("!")[0]
                    msg_type = meta_data.split(" ")[1]
                    dest_chat = meta_data.split(" ")[2]

                    
                    ret_dict = {
                            "name": chatter_name,
                            "message_type": msg_type,
                            "destination": dest_chat,
                            "date_time": datetime.now(),
                            "chat_message": chat_msg
                    }

                    return ret_dict
    
            except socket.error as e:
                # get the error
                err = e.args[0]

                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    # This is the case in the socket where there is no data
                    # available, so just continue as normal and wait for a new
                    # msg
                    continue

                else:
                    # This is the case where an error actually occured:
                    raise Exception(
                        "CHAT OBJECT - THE FOLLOWING EXCEPTION OCCURED "
                        "WHEN TRYING TO READ A CHAT:\n" + str(e))
            except UnicodeDecodeError:
                # TODO: Figure out what to do with this error when it happens
                print(f"found non-decodable byte: {resp}")
                continue

    def __del__(self):
        """ destructor for the object """
        self.sock.close()
