#ifndef __QSPI_H_
#define __QSPI_H_
#include "sys.h"

#define QSPI_NCS(x)   GPIO_Pin_Set(GPIOB,PIN10,x)


u8 QSPI_Wait_Flag(u32 flag,u8 sta,u32 wtime);					//QSPI等待某个状态
u8 QSPI_Init(void);												//初始化QSPI
void QSPI_Send_CMD(u8 cmd,u32 addr,u8 mode,u8 dmcycle);			//QSPI发送命令
u8 QSPI_Receive(u8* buf,u32 datalen);							//QSPI接收数据
u8 QSPI_Transmit(u8* buf,u32 datalen);							//QSPI发送数据
void OSPI_Send_Command(uint8_t instr, uint32_t mode, uint32_t addr_mode, uint32_t data_mode, uint8_t dummy);
#endif

