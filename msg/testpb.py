#!/urs/bin/python
#encoding=utf-8

import heartbeat_pb2

heart = heartbeat_pb2.heart()

heart.region = "zhenru"
heart.timestamp = 1223344

heart_str = heart.SerializeToString()

heart2 = heartbeat_pb2.heart()
heart2.ParseFromString(heart_str)

print heart2.region, heart2.timestamp


