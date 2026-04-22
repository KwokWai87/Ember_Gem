#include "POWER_IO.h"


void POWER_IO_Init(void)
{
	RCC->AHB4ENR|=1<<0;         //使能PORTA时钟 
	RCC->AHB4ENR|=1<<8;    			//使能PORTI时钟 
	GPIO_Set(GPIOA,PIN15,GPIO_MODE_OUT,GPIO_OTYPE_PP,GPIO_SPEED_HIGH,GPIO_PUPD_PU);
	GPIO_Set(GPIOI,PIN9|PIN10|PIN11,GPIO_MODE_OUT,GPIO_OTYPE_PP,GPIO_SPEED_HIGH,GPIO_PUPD_PU);	//PI9/10/11推挽输出 
  GPIO_Set(GPIOI,PIN12|PIN13|PIN14,GPIO_MODE_IN,GPIO_OTYPE_OD,GPIO_SPEED_HIGH,GPIO_PUPD_PU);
	
	IO_PWR_EN(1);
	IO_PWR_EN1(1);
	IO_PWR_EN2(1);
	IO_PWREN_EINK(0);
	delay_ms(10);
}


void POWER_SET(u8 pow_en,u8 pow_en1,u8 pow_en2,u8 pwren_link)
{
	if(pow_en>1)pow_en=1;
	if(pow_en1>1)pow_en=1;
	if(pow_en2>1)pow_en=1;	
	if(pwren_link>1)pwren_link=1;
	IO_PWR_EN(pow_en);
	IO_PWR_EN1(pow_en1);
	IO_PWR_EN2(pow_en2);
	IO_PWREN_EINK(pwren_link);
	printf("pow_en:%d\r\n",pow_en);
	printf("pow_en1:%d\r\n",pow_en1);
	printf("pow_en2:%d\r\n",pow_en2);
	printf("pwren_link:%d\r\n",pwren_link);
}


void POWER_READ(void)
{
 	printf("IO_CHG_DETECT:%d\r\n",IO_CHG_DETECT);
  printf("IO_PG_DETECT:%d\r\n",IO_PG_DETECT);
	printf("IO_PWR_DETECT:%d\r\n",IO_PWR_DETECT);
}
