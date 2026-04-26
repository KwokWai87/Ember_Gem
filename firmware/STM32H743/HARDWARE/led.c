#include "led.h" 

//LED IO初始化
void LED_Init(void)
{	
	RCC->AHB4ENR|=1<<6;	//使能PORTG时钟 
	GPIO_Set(GPIOG,PIN2|PIN3|PIN4,GPIO_MODE_OUT,GPIO_OTYPE_PP,GPIO_SPEED_MID,GPIO_PUPD_PU); //PG2/3/4设置
	LEDR(1);		
	LEDG(1);	
	LEDB(1);		
}







