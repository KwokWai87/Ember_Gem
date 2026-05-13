#ifndef __24AA025E48T_H_
#define __24AA025E48T_H_


#include "sys.h"
#include "S_IIC.h"
#include "usart.h"

#define U24AA025_ADDRESS     0xA0

#define MAC_ADDRESS          0xFA
//#define IP_ADDRESS           0x00
//#define SN_ADDRESS           0x04
//#define GW_ADDRESS           0x08
//#define DNS_ADDRESS          0x0C

void EEPROM_Init(void);
void U24AA025_READ(u32 addr,u8 *pbuffer,u32 len);
void U24AA025_WRITE(u32 addr,u8 *pbuffer,u32 len);
void MAC_ADDRESS_READ(void);
void EEPROM_Init(void);



#endif
