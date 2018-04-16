#!/usr/bin/python
import cstruct
from datetime import date, datetime, timedelta
from bottle import request, response, get, post, run, template, Bottle, error
import time
from crc16 import crc16xmodem
import struct
import sys
import mysql.connector
from mysql.connector import errorcode
import collections
from collections import namedtuple
from pprint import pprint

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
        cksum=sum(map(ord, self.pack()))
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

class DataCRCReq(cstruct.CStruct):
    __byte_order__ = cstruct.BIG_ENDIAN
    __struct__ = """
        unsigned char unknown1;
        char serial[16];
        unsigned char series;
        unsigned short size;
    """

    def print_info(self):
        print("%s,%s,%s,%s,%s" % (self.serial, self.reading.Vac1, self.reading.Iac1, self.reading.Temperature, self.reading.ETotal))

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
        cksum=sum(map(ord, self.pack()))
        self.cksum=cksum
        return self.pack()

@post('/DataCRC')
def datacrc():
    data = DataCRCReq()
    response.set_header('Content-Type', 'application/octet-stream;charset=UTF-8')
    body = request.body.read()
    data.GetMessage(body)
    data.print_info()
    reply=DataCRCResp()
    return reply.GetResponse(data.serial)

@post('/GetSendInterval')
def getsendinterval():
    data = SendIntervalReq()
    body = request.body.read()
    data.unpack(body)

    reply = LocalTimeResp()
    return reply.GetResponse(data.serial)


@post('/GetLocalTime')
def getlocaltime():
    data = LocalTimeReq()
    body = request.body.read()
    data.unpack(body)

    reply = LocalTimeResp()
    return reply.GetResponse(data.serial)

@post('/GetRemoteControl')
def getremotecontrol():
    data = RemoteControlReq()
    body = request.body.read()
    data.unpack(body)

    reply = RemoteControlResp()
    return reply.GetResponse(data.serial)

run(server='cgi')

