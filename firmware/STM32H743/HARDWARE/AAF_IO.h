#ifndef __AAF_IO_H_ 
#define __AAF_IO_H_

#include "sys.h"
#include "usart.h"

#define IO_SW3_A0(x)   GPIO_Pin_Set(GPIOB,PIN12,x)
#define IO_SW3_A1(x)   GPIO_Pin_Set(GPIOB,PIN13,x)
#define IO_SW3_A2(x)   GPIO_Pin_Set(GPIOB,PIN14,x)

#define IO_SW4_A0(x)   GPIO_Pin_Set(GPIOD,PIN8,x)
#define IO_SW4_A1(x)   GPIO_Pin_Set(GPIOD,PIN9,x)
#define IO_SW4_A2(x)   GPIO_Pin_Set(GPIOD,PIN10,x)


void AAF_IO_Init(void);
void AAF_set_IO(u8 IO_SW3_A0,u8 IO_SW3_A1,u8 IO_SW3_A2,u8 IO_SW4_A0,u8 IO_SW4_A1,u8 IO_SW4_A2);

#endif
