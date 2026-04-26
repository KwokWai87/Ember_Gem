#ifndef __LED_H
#define __LED_H	 
#include "sys.h" 


//LED端口定义
#define LEDR(x)			GPIO_Pin_Set(GPIOG,PIN2,x)		// DSR
#define LEDG(x)			GPIO_Pin_Set(GPIOG,PIN4,x)		// DSG
#define LEDB(x)			GPIO_Pin_Set(GPIOG,PIN3,x)		// DSB

void LED_Init(void);	//初始化		 				    
#endif

















