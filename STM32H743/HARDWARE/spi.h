#ifndef __SPI_H
#define __SPI_H
#include "sys.h"


// SPI总线速度设置 
#define SPI_SPEED_2   		0
#define SPI_SPEED_4   		1
#define SPI_SPEED_8   		2
#define SPI_SPEED_16  		3
#define SPI_SPEED_32 		4
#define SPI_SPEED_64 		5
#define SPI_SPEED_128 		6
#define SPI_SPEED_256 		7

#define AD9833_CS(x) GPIO_Pin_Set(GPIOE,PIN11,x)	
void SPI1_Init(void);
void SPI1_SetSpeed(u8 SpeedSet);
u8 SPI1_ReadWriteByte(u8 TxData);

void SPI2_Init(void);
void SPI2_SetSpeed(u8 SpeedSet);
u8 SPI2_ReadWriteByte(u8 TxData);

void SPI4_Init(void);
void SPI4_SetSpeed(u8 SpeedSet);
u16 SPI4_ReadWriteByte(u16 TxData);

#endif

