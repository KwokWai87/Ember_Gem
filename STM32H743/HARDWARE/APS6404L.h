#ifndef __APS6404L_H_
#define __APS6404L_H_

#include "sys.h"
#include "qspi.h"
#include "delay.h" 

#define Fast_Read_Quad   0xEB
#define into_Quad        0x35
#define Write_Quad       0x38
#define Write_en         0x06
#define Reset_en         0x66
#define Reset            0x99
void APS6404L_Init(void);
void OSPI_Write_Quad(uint32_t addr, uint8_t *pData, uint16_t size);
void OSPI_Read_Quad(uint32_t addr, uint8_t *pData, uint16_t size);
void QSPI_Wait(void);
void QSPI_SendCmd(uint8_t instr);
void QSPI_Cmd1Line(uint8_t cmd);
#endif
