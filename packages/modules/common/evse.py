#!/usr/bin/env python3
import logging
from enum import IntEnum
import time
from typing import Optional, Tuple
from helpermodules.logger import ModifyLoglevelContext

from modules.common import modbus
from modules.common.modbus import ModbusDataType

log = logging.getLogger(__name__)


class EvseState(IntEnum):
    READY = (1, False, False)
    EV_PRESENT = (2, True, False)
    CHARGING = (3, True, True)
    CHARGING_WITH_VENTILATION = (4, True, True)
    FAILURE = (5, None, None)

    def __new__(cls, num: int, plugged: Optional[bool], charge_enabled: Optional[bool]):
        member = int.__new__(cls, num)
        member._value_ = num
        member.plugged = plugged
        member.charge_enabled = charge_enabled
        return member


class Evse:
    PRECISE_CURRENT_BIT = 1 << 7

    def __init__(self, modbus_id: int, client: modbus.ModbusSerialClient_) -> None:
        self.client = client
        self.id = modbus_id

    def get_plug_charge_state(self) -> Tuple[bool, bool, float]:
        time.sleep(0.1)
        set_current, _, state_number = self.client.read_holding_registers(
            1000, [ModbusDataType.UINT_16]*3, unit=self.id)
        # remove leading zeros
        set_current = int(set_current)
        log.debug("Gesetzte Stromstärke EVSE: "+str(set_current) +
                  ", Status: "+str(state_number)+", Modbus-ID: "+str(self.id))
        state = EvseState(state_number)
        if state == EvseState.FAILURE:
            raise ValueError("Unbekannter Zustand der EVSE: State " +
                             str(state)+", Soll-Stromstärke: "+str(set_current))
        plugged = state.plugged
        charging = set_current > 0 if state.charge_enabled else False
        if set_current > 32:
            set_current = set_current / 100
        return plugged, charging, set_current

    def get_firmware_version(self) -> int:
        time.sleep(0.1)
        version = self.client.read_holding_registers(1005, ModbusDataType.UINT_16, unit=self.id)
        return version

    def is_precise_current_active(self) -> bool:
        time.sleep(0.1)
        value = self.client.read_holding_registers(2005, ModbusDataType.UINT_16, unit=self.id)
        with ModifyLoglevelContext(log, logging.DEBUG):
            if value & self.PRECISE_CURRENT_BIT:
                log.debug("Angabe der Ströme in 0,01A-Schritten ist aktiviert.")
                return True
            else:
                log.debug("Angabe der Ströme in 0,01A-Schritten ist nicht aktiviert.")
                return False

    def activate_precise_current(self) -> None:
        time.sleep(0.1)
        value = self.client.read_holding_registers(2005, ModbusDataType.UINT_16, unit=self.id)
        if value & self.PRECISE_CURRENT_BIT:
            return
        else:
            with ModifyLoglevelContext(log, logging.DEBUG):
                log.debug("Bit zur Angabe der Ströme in 0,1A-Schritten wird gesetzt.")
            self.client.write_registers(2005, value ^ self.PRECISE_CURRENT_BIT, unit=self.id)
            # Zeit zum Verarbeiten geben
            time.sleep(1)

    def deactivate_precise_current(self) -> None:
        time.sleep(0.1)
        value = self.client.read_holding_registers(2005, ModbusDataType.UINT_16, unit=self.id)
        if value & self.PRECISE_CURRENT_BIT:
            with ModifyLoglevelContext(log, logging.DEBUG):
                log.debug("Bit zur Angabe der Ströme in 0,1A-Schritten wird zurueckgesetzt.")
            self.client.write_registers(2005, value ^ self.PRECISE_CURRENT_BIT, unit=self.id)
        else:
            return

    def set_current(self, current: int) -> None:
        time.sleep(0.1)
        self.client.write_registers(1000, current, unit=self.id)

    def get_max_current(self) -> int:
        time.sleep(0.1)
        current = self.client.read_holding_registers(2007, ModbusDataType.UINT_16, unit=self.id)
        return current
