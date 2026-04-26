#ifndef __CH446Q_H_
#define __CH446Q_H_

#include "sys.h" 
#include "delay.h" 

#define IO_SWA_CS1(x)			GPIO_Pin_Set(GPIOD,PIN7,x)		
#define IO_SWA_CS2(x)			GPIO_Pin_Set(GPIOC,PIN8,x)	
#define IO_SWA_CS3(x)			GPIO_Pin_Set(GPIOG,PIN6,x)	
#define IO_SWA_CS4(x)			GPIO_Pin_Set(GPIOG,PIN12,x)	
#define IO_SWA_RST(x)			GPIO_Pin_Set(GPIOE,PIN6,x)	
#define IO_SWA_STB(x)		  GPIO_Pin_Set(GPIOD,PIN5,x)	
#define IO_SWA_AX1(x)			GPIO_Pin_Set(GPIOD,PIN14,x)	
#define IO_SWA_AX2(x)			GPIO_Pin_Set(GPIOD,PIN15,x)	
#define IO_SWA_AX3(x)			GPIO_Pin_Set(GPIOD,PIN0,x)	
#define IO_SWA_AX4(x)			GPIO_Pin_Set(GPIOD,PIN1,x)	
#define IO_SWA_AY1(x)			GPIO_Pin_Set(GPIOE,PIN7,x)	
#define IO_SWA_AY2(x)			GPIO_Pin_Set(GPIOE,PIN8,x)	
#define IO_SWA_AY3(x)			GPIO_Pin_Set(GPIOE,PIN9,x)	
#define IO_SWA_DAT(x)			GPIO_Pin_Set(GPIOE,PIN10,x)	



void CH446Q_init(void);
void CH446Q_MIX_CONTROL(u8 cs,u8 ax,u8 ay,u8 on_off);
void CH446Q_Reset(void);
#endif
