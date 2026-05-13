#ifndef __DisCharge_H_
#define __DisCharge_H_


#include "sys.h"
#include "usart.h"


void DisCharge_Init(void);

#define DisChargeJ1_en(x)     GPIO_Pin_Set(GPIOD,PIN12,x)	
#define DisChargeJ2_en(x)     GPIO_Pin_Set(GPIOD,PIN13,x)

void DisCharge_SET(u8 J1_en,u8 J2_en);

#endif
