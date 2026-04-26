#ifndef __PGA849_H_
#define __PGA849_H_


#include "sys.h" 

#define IO_PGA_SET_A0(x)  GPIO_Pin_Set(GPIOF,PIN12,x)	
#define IO_PGA_SET_A1(x)  GPIO_Pin_Set(GPIOF,PIN11,x)
#define IO_PGA_SET_A2(x)  GPIO_Pin_Set(GPIOF,PIN13,x)
#define IO_SW6_IN(x)      GPIO_Pin_Set(GPIOB,PIN2,x)

#define IO_SW7_A0(x)  GPIO_Pin_Set(GPIOJ,PIN0,x)	
#define IO_SW7_A1(x)  GPIO_Pin_Set(GPIOJ,PIN1,x)

void PGA849_init(void);
void PGA849_set(u8 vref0or1_25,u8 gain,u8 ADG1409_A0,u8 ADG1409_A1);
#endif
