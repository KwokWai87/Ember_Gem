#ifndef __MCP4725_H
#define __MCP4725_H

#include "sys.h" 
#include "S_IIC.h"

//write_mode
#define SAVE   0
#define FAST   1
//out_put_mode
#define OUT_ON                0
#define OUT_OFF_1K_TO_GND     1
#define OUT_OFF_100K_TO_GND   2
#define OUT_OFF_500K_TO_GND   3


#define Vref   3.3f
#define DAC_LSB  (Vref/4096.0f)

#define MCP4725A_ADDR1       0xC0
#define MCP4725A_ADDR2       0xC2
#define RESET_CHIP           0x60
#define WAKE_CHIP            0x90


void MCP4725A_init(u8 chip_numb);
void MCP4725A_Set_DAC(u8 chip_numb,u8 write_mode,u8 out_put_mode,u16 dac_out);
void MCP4725A_Set_Voltage(u8 chip_numb,u8 write_mode,u8 out_put_mode,u16 vol_out);
//void Set_Current(u8 select,u8 chip_numb,u8 write_mode,float current);

#endif
