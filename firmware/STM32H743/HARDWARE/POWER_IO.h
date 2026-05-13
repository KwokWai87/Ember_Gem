#ifndef __POWER_IO_H_
#define __POWER_IO_H_

#include "sys.h"
#include "delay.h" 
#include "usart.h"

void POWER_IO_Init(void);
void POWER_READ(void);


#define IO_PWR_EN(x)     GPIO_Pin_Set(GPIOI,PIN9,x)	
#define IO_PWREN_EINK(x) GPIO_Pin_Set(GPIOA,PIN15,x)	
#define IO_PWR_EN1(x)    GPIO_Pin_Set(GPIOI,PIN10,x)	
#define IO_PWR_EN2(x)    GPIO_Pin_Set(GPIOI,PIN11,x)	
#define IO_CHG_DETECT    GPIO_Pin_Get(GPIOI,PIN12)	
#define IO_PG_DETECT     GPIO_Pin_Get(GPIOI,PIN13)	
#define IO_PWR_DETECT    GPIO_Pin_Get(GPIOI,PIN14)	

void POWER_SET(u8 pow_en,u8 pow_en1,u8 pow_en2,u8 pwren_link);

#endif

