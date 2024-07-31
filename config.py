import configparser
config = configparser.ConfigParser()
config.read("config.conf")

# HOST, PORT = "192.168.137.1", 8000
HOST = config["DEFAULT"]["HostIP"]
PORT = int(config["DEFAULT"]["ReceivePort"])
print(HOST)
print(PORT)