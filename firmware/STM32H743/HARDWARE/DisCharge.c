#include "DisCharge.h"


void DisCharge_Init(void)
{
	RCC->AHB4ENR|=1<<3;         //使能PORTD时钟 
	GPIO_Set(GPIOD,PIN12|PIN13,GPIO_MODE_OUT,GPIO_OTYPE_PP,GPIO_SPEED_HIGH,GPIO_PUPD_PU);	//PD12/13推挽输出 
	
	DisChargeJ1_en(0);
	DisChargeJ2_en(0);
}

void DisCharge_SET(u8 J1_en,u8 J2_en)
{
	if(J1_en>1) J1_en=1;
	if(J2_en>1) J2_en=1;
	DisChargeJ1_en(J1_en);
	DisChargeJ2_en(J2_en);
	sys_print("DisChargeJ1_en:%d\r\n",J1_en);
	sys_print("DisChargeJ2_en:%d\r\n",J2_en);
}
