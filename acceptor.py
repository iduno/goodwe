#!/usr/bin/python3
import cstruct
from bottle import request, response, post, run
import time
from crc16 import crc16xmodem
import sys
import json
import paho.mqtt.client as mqtt
import os

class LocalTimeReq(cstruct.CStruct):
    __byte_order__ = cstruct.BIG_ENDIAN
    __struct__ = """
        char serial[16];
    """

class MsgTime(cstruct.CStruct):
    __byte_order__ = cstruct.BIG_ENDIAN
    __struct__ = """
        unsigned char Year;
        unsigned char Month;
        unsigned char Day;
        unsigned char Hour;
        unsigned char Min;
        unsigned char Sec;
    """

    def GetJson(self):
        return { 'Year' : self.Year, \
        'Month' : self.Month, \
        'Day' : self.Day, \
        'Hour' : self.Hour, \
        'Min' : self.Min, \
        'Sec' : self.Sec }

    def GetJsonTime(self):
        return "20{:02d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format((self.Year%100), self.Month, self.Day, self.Hour, self.Min, self.Sec)
        
    def SetLocalTime(self):
        lt=time.localtime()
        self.Year=lt.tm_year%100
        self.Month=lt.tm_mon
        self.Day=lt.tm_mday
        self.Hour=lt.tm_hour
        self.Min=lt.tm_min
        self.Sec=lt.tm_sec

class LocalTimeResp(cstruct.CStruct):
    __byte_order__ = cstruct.BIG_ENDIAN
    __struct__ = """
        char serial[16];
        unsigned char Year;
        struct MsgTime time;
        unsigned short cksum;
    """

    def GetResponse(self,serial):
        self.serial=serial
        self.time.SetLocalTime()
        self.cksum=0
        print(self.pack())
        cksum=sum(self.pack())
        self.cksum=cksum
        return self.pack()

class RemoteControlReq(cstruct.CStruct):
    __byte_order__ = cstruct.BIG_ENDIAN
    __struct__ = """
        char serial[16];
        char unknown[76];
    """

class RemoteControlResp(cstruct.CStruct):
    __byte_order__ = cstruct.BIG_ENDIAN
    __struct__ = """
    """

    def GetResponse(self,serial):
        return ""


class DataCRCS0(cstruct.CStruct):
    _byte_order__ = cstruct.BIG_ENDIAN
    __struct__ = """
        unsigned short Vpv1;
        unsigned short Vpv2;
        unsigned short Ipv1;
        unsigned short Ipv2;
        unsigned short Vac1;
        unsigned short Iac1;
        unsigned short Fac1;
        unsigned short Pac;
        unsigned short WorkMode;
        unsigned short Temperature;
        unsigned int ErrorMsg;
        unsigned int ETotal;
        unsigned int hTotal;
        unsigned short SoftVersion;
        unsigned short WarningCode;
        unsigned short FunctionsBitValue;
        unsigned short BUSVoltage;
        unsigned short NBUSVoltage;
        unsigned short GFCIFaultValue;
        unsigned short EDay;
        unsigned short unknown;
    """

    def GetJson(self):
            return {
                'Vpv1': round(float(self.Vpv1)/10.0, 1),
                'Vpv2': round(float(self.Vpv2)/10.0, 1),
                'Ipv1': round(float(self.Ipv1)/10.0, 1),
                'Ipv2': round(float(self.Ipv2)/10.0, 1),
                'Vac1': round(float(self.Vac1)/10.0, 1),
                'Iac1': round(float(self.Iac1)/10.0, 1),
                'Fac1': round(float(self.Fac1)/100.0, 2),
                'Pac': round(float(self.Pac), 1),
                'WorkMode': self.WorkMode,
                'Temperature': round(float(self.Temperature)/10.0, 1),
                'ErrorMsg': self.ErrorMsg,
                'OutputTotal': self.ETotal,
                'HoursTotal': self.hTotal,
                'SoftVersion': self.SoftVersion,
                'WarningCode': self.WarningCode,
                'FunctionsBitValue': self.FunctionsBitValue,
                'BUSVoltage': self.BUSVoltage,
                'NBUSVoltage': self.NBUSVoltage,
                'GFCIFaultValue': self.GFCIFaultValue,
                'OutputDay': round(float(self.EDay)/10.0, 2),
                'unknown': self.unknown
            }

class DataCRCS1(cstruct.CStruct):
    __byte_order__ = cstruct.BIG_ENDIAN
    __struct__ = """
        unsigned short Vpv1;
        unsigned short Vpv2;
        unsigned short Ipv1;
        unsigned short Ipv2;
        unsigned short Vac1;
        unsigned short Vac2;
        unsigned short Vac3;
        unsigned short Iac1;
        unsigned short Iac2;
        unsigned short Iac3;
        unsigned short Fac1;
        unsigned short Fac2;
        unsigned short Fac3;
        unsigned short Pac;
        unsigned short WorkMode;
        unsigned short Temperature;
        unsigned int ErrorMsg;
        unsigned int ETotal;
        unsigned int hTotal;
        unsigned short SoftVersion;
        unsigned short WarningCode;
        unsigned short PV2FaultValue;
        unsigned short FunctionsBitValue;
        unsigned short Line2VFaultValue;
        unsigned short Line3VFaultValue;
        unsigned short BUSVoltage;
        unsigned short NBUSVoltage;
        unsigned short Line3FFaultValue;
        unsigned short GFCIFaultValue;
        unsigned short EDay;
        struct MsgTime time;
        unsigned int unknown2;
        unsigned short ARMSoftVersion;
        unsigned short unknown3;
        unsigned short unknown4;
        unsigned short unknown5;
        unsigned short unknown6;
        char model[10];
    """

    def GetJson(self):
        return { 'Vpv1':  round(float(self.Vpv1)/10.0,1), \
        'Vpv2':  round(float(self.Vpv2)/10.0,1), \
        'Ipv1':  round(float(self.Ipv1)/10.0,1), \
        'Ipv2':  round(float(self.Ipv2)/10.0,1), \
        'Vac1':  round(float(self.Vac1)/10.0,1), \
        'Vac2':  round(float(self.Vac2)/10.0,1), \
        'Vac3':  round(float(self.Vac3)/10.0,1), \
        'Iac1':  round(float(self.Iac1)/10.0,1), \
        'Iac2':  round(float(self.Iac2)/10.0,1), \
        'Iac3':  round(float(self.Iac3)/10.0,1), \
        'Fac1':  round(float(self.Fac1)/100.0,2), \
        'Fac2':  round(float(self.Fac2)/100.0,2), \
        'Fac3':  round(float(self.Fac3)/100.0,2), \
        'Pac':  round(float(self.Pac),2), \
        'WorkMode' : self.WorkMode, \
        'Temperature':  round(float(self.Temperature)/10.0,1), \
        'ErrorMsg': self.ErrorMsg, \
        'OutputTotal': self.ETotal, \
        'HoursTotal': self.hTotal, \
        'SoftVersion': self.SoftVersion, \
        'WarningCode': self.WarningCode, \
        'PV2FaultValue': self.PV2FaultValue, \
        'FunctionsBitValue': self.FunctionsBitValue, \
        'Line2VFaultValue': self.Line2VFaultValue, \
        'Line3VFaultValue': self.Line3VFaultValue, \
        'BUSVoltage': self.BUSVoltage, \
        'NBUSVoltage': self.NBUSVoltage, \
        'Line3FFaultValue': self.Line3FFaultValue, \
        'GFCIFaultValue': self.GFCIFaultValue, \
        'OutputDay':  round(float(self.EDay)/10.0,1), \
        'time': self.time.GetJsonTime(), \
        'unknown2': self.unknown2, \
        'ARMSoftVersion': self.ARMSoftVersion, \
        'unknown3': self.unknown3, \
        'unknown4': self.unknown4, \
        'unknown5': self.unknown5, \
        'unknown6': self.unknown6, \
        'model': self.model.decode("ascii") }

class DataCRCReq(cstruct.CStruct):
    __byte_order__ = cstruct.BIG_ENDIAN
    __struct__ = """
        unsigned char unknown1;
        char serial[16];
        unsigned char series;
        unsigned short datasize;
    """

    def GetJson(self):
        reading_json = self.reading.GetJson() if hasattr(self, 'reading') and self.reading is not None else None
        return {
            'reading': reading_json,
            'unknown1': self.unknown1,
            'serial': self.serial.decode("ascii"),
            'series': self.series,
            'size': self.datasize
        }

    def print_info(self):
        # print("%s,%s,%s,%s,%s" % (self.serial, self.reading.Vac1, self.reading.Iac1, self.reading.Temperature, self.reading.ETotal))
        print ("dump %s" % (json.dumps(self.GetJson())))

    def GetMessage(self,data):
        self.unpack(data[:len(self)])
        if self.series == 0:
            self.reading=DataCRCS0()
        else:
            self.reading=DataCRCS1()
        self.reading.unpack(data[len(self):])

class DataCRCResp(cstruct.CStruct):
    __byte_order__ = cstruct.BIG_ENDIAN
    __struct__ = """
        char serial[16];
        unsigned short unknown1;
        unsigned short unknown2;
        unsigned short cksum;
    """

    def GetResponse(self,serial):
        self.serial=serial
        self.cksum=0
        print("dump :%s:" % self.pack(), file=sys.stderr)
        cksum=sum(self.pack())
        self.cksum=cksum
        return self.pack()

def getPubList():
    return {
        'Vpv1': {'unit_of_measurement': 'V', 'state_class': 'measurement', 'device_class': 'voltage'},
        'Vpv2': {'unit_of_measurement': 'V', 'state_class': 'measurement', 'device_class': 'voltage'},
        'Ipv1': {'unit_of_measurement': 'A', 'state_class': 'measurement', 'device_class': 'current'},
        'Ipv2': {'unit_of_measurement': 'A', 'state_class': 'measurement', 'device_class': 'current'},
        'Vac1': {'unit_of_measurement': 'V', 'state_class': 'measurement', 'device_class': 'voltage'},
        'Vac2': {'unit_of_measurement': 'V', 'state_class': 'measurement', 'device_class': 'voltage'},
        'Vac3': {'unit_of_measurement': 'V', 'state_class': 'measurement', 'device_class': 'voltage'},
        'Iac1': {'unit_of_measurement': 'A', 'state_class': 'measurement', 'device_class': 'current'},
        'Iac2': {'unit_of_measurement': 'A', 'state_class': 'measurement', 'device_class': 'current'},
        'Iac3': {'unit_of_measurement': 'A', 'state_class': 'measurement', 'device_class': 'current'},
        'Fac1': {'unit_of_measurement': 'Hz', 'state_class': 'measurement', 'device_class': 'frequency'},
        'Fac2': {'unit_of_measurement': 'Hz', 'state_class': 'measurement', 'device_class': 'frequency'},
        'Fac3': {'unit_of_measurement': 'Hz', 'state_class': 'measurement', 'device_class': 'frequency'},
        'Pac': {'unit_of_measurement': 'kW', 'state_class': 'measurement', 'device_class': 'power'},
        'Temperature': {'unit_of_measurement': '°C', 'state_class': 'measurement', 'device_class': 'temperature'},
        'OutputTotal': {'unit_of_measurement': 'kWh', 'state_class': 'total_increasing', 'device_class': 'energy'},
        'OutputDay': {'unit_of_measurement': 'kWh', 'state_class': 'total_increasing', 'device_class': 'energy'},
        'HoursTotal': {'unit_of_measurement': 'Hours', 'state_class': 'total_increasing', 'device_class': None}
    }

def getPublishDevice(model):
    return { \
    'identifiers':'Goodwe Inverter', \
    'name':'GoodWe Inverter', \
    'model':model, \
    'manufacturer':'GoodWe' }
def getPublishPayload(data,tag,unit,serial):
    model = None
    if hasattr(data, 'reading') and data.reading is not None and hasattr(data.reading, 'model'):
        try:
            model = data.reading.model.decode("ascii")
        except Exception:
            model = str(data.reading.model)
    else:
        model = "Unknown"
    return {
        'name': f"{tag}",
        'state_topic': f"goodwe/{serial}/Publish",
        'value_template': f"{{{{ value_json.reading.{tag} }}}}",
        'unit_of_measurement': unit['unit_of_measurement'],
        'state_class': unit['state_class'],
        'device_class': unit['device_class'],
        'unique_id': f"goodwe_{serial}_{tag}",
        'device': getPublishDevice(model)
    }

def sendmqtt(data):
    mqtt_broker = os.environ.get("MQTT_BROKER", "localhost")
    mqtt_port = int(os.environ.get("MQTT_PORT", 1883))
    mqtt_username = os.environ.get("MQTT_USERNAME")
    mqtt_password = os.environ.get("MQTT_PASSWORD")
    mqtt_client_id = os.environ.get("MQTT_CLIENT_ID", "GoodWe")
    mqtt_keepalive = int(os.environ.get("MQTT_KEEPALIVE", 60))
    test = data
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,mqtt_client_id)
    if mqtt_username and mqtt_password:
        client.username_pw_set(username=mqtt_username, password=mqtt_password)
    #client.tls_set("mqttca.cer",tls_version=ssl.PROTOCOL_TLSv1_2)
    #client.tls_insecure_set(True)

    import threading
    connected_event = threading.Event()

    def on_connect(client, userdata, flags, reason_code, properties=None):
        print(f"Connected to MQTT broker with reason code {reason_code}", file=sys.stderr)
        if reason_code == 0:
            connected_event.set()
        else:
            print(f"MQTT connection failed: {reason_code}", file=sys.stderr)

    def on_publish(client, userdata, mid, reason_code, properties=None):
        print(f"Message {mid} published, reason_code={reason_code}", file=sys.stderr)

    client.on_connect = on_connect
    client.on_publish = on_publish

    client.connect(host=mqtt_broker, port=mqtt_port, keepalive=mqtt_keepalive)
    client.loop_start()
    # Wait for connection (timeout after 5 seconds)
    if not connected_event.wait(timeout=5):
        print("MQTT client failed to connect within timeout.", file=sys.stderr)
        client.loop_stop()
        client.disconnect()
        return

    jsonData = data.GetJson()
    serial = data.serial.decode("ascii")
    pubList = getPubList()
    for tag in pubList:
        jsonPub = getPublishPayload(data, tag, pubList[tag], serial)
        result = client.publish(topic=f"homeassistant/sensor/goodwe_{serial}/{tag}/config", payload=json.dumps(jsonPub))
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            print(f"Failed to publish {tag} config: {mqtt.error_string(result.rc)}", file=sys.stderr)
        print(f"tag: {jsonPub}", file=sys.stderr)
    result = client.publish(topic=f"goodwe/{serial}/Publish", payload=json.dumps(jsonData))
    if result.rc != mqtt.MQTT_ERR_SUCCESS:
        print(f"Failed to publish data: {mqtt.error_string(result.rc)}", file=sys.stderr)
    print(f"data: {jsonData}", file=sys.stderr)
    client.loop_stop()
    client.disconnect()

@post('/Acceptor/DataCRC')
def datacrc():
    data = DataCRCReq()
    response.set_header('Content-Type', 'application/octet-stream;charset=UTF-8')
    body = request.body.read()
    print("DataCRC: %s",body, file=sys.stderr);
    data.GetMessage(body)
    sendmqtt(data)
    print(data)
    reply=DataCRCResp()
    return reply.GetResponse(data.serial)

@post('/Acceptor/GetSendInterval')
def getsendinterval():
    data = SendIntervalReq()
    body = request.body.read()
    print("GetSendInterval: %s",body, file=sys.stderr);
    data.unpack(body)

    reply = LocalTimeResp()
    return reply.GetResponse(data.serial)


@post('/Acceptor/GetLocalTime')
def getlocaltime():
    data = LocalTimeReq()
    body = request.body.read()
    print("GetLocalTime: %s",body, file=sys.stderr);
    data.unpack(body)

    reply = LocalTimeResp()
    return reply.GetResponse(data.serial)

@post('/Acceptor/GetRemoteControl')
def getremotecontrol():
    data = RemoteControlReq()
    body = request.body.read()
    print("GetRemoteControl: %s",body, file=sys.stderr);
    data.unpack(body)

    reply = RemoteControlResp()
    return reply.GetResponse(data.serial)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    debug = os.environ.get("DEBUG", "False").lower() in ("1", "true", "yes")
    run(host="0.0.0.0", port=port, debug=debug)