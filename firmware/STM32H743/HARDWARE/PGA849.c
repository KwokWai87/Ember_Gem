#include "PGA849.h"

//F12:IO_PGA_SET_A0
//F11:IO_PGA_SET_A1
//F13:IO_PGA_SET_A2
//PJ0:IO_SW7_A0
//PJ1:IO_SW7_A1
void PGA849_init(void)
{
  RCC->AHB4ENR|=1<<1;	//使能PORTB时钟
	RCC->AHB4ENR|=1<<4;	//使能PORTE时钟
	RCC->AHB4ENR|=1<<9;	//使能PORTJ时钟
	
	GPIO_Set(GPIOB,PIN2,GPIO_MODE_OUT,GPIO_OTYPE_PP,GPIO_SPEED_MID,GPIO_PUPD_PU);   //PB2设置
	GPIO_Set(GPIOF,PIN11|PIN12|PIN13,GPIO_MODE_OUT,GPIO_OTYPE_PP,GPIO_SPEED_MID,GPIO_PUPD_PD);   //PE11/12/13设置
	GPIO_Set(GPIOJ,PIN0|PIN1,GPIO_MODE_OUT,GPIO_OTYPE_PP,GPIO_SPEED_MID,GPIO_PUPD_PD);   //PJ0/1设置
  IO_PGA_SET_A0(0);
	IO_PGA_SET_A1(0);
  IO_PGA_SET_A2(0);
	IO_SW7_A0(0);
	IO_SW7_A1(0);
	
}

//vref0or1_25=0:1.25v
//vref0or1_25=1:0.0v
void PGA849_set(u8 vref0or1_25,u8 gain,u8 ADG1409_A0,u8 ADG1409_A1)
{
	
if(ADG1409_A0)
{
	IO_SW7_A0(1);
	printf("IO_SW7_A0:1,\r\n");
}
else
{
	IO_SW7_A0(0);
	printf("IO_SW7_A0:0,\r\n");
}

if(ADG1409_A1)
{
	IO_SW7_A1(1);
	printf("IO_SW7_A1:1,\r\n");
}
else
{
	IO_SW7_A1(0);
	printf("IO_SW7_A1:0,\r\n");
}


if(vref0or1_25)
{
	IO_SW6_IN(1);
	printf("IO_SW6_IN:1,vref=0.0v\r\n");
}
else
{
	IO_SW6_IN(0);
	printf("IO_SW6_IN:0,vref=1.25v\r\n");
}
	
	switch(gain)
{
	case 0:IO_PGA_SET_A0(0);
	       IO_PGA_SET_A1(0);
         IO_PGA_SET_A2(0);
		     break;
	case 1:IO_PGA_SET_A0(1);
	       IO_PGA_SET_A1(0);
         IO_PGA_SET_A2(0);
		     break;
	case 2:IO_PGA_SET_A0(0);
	       IO_PGA_SET_A1(1);
         IO_PGA_SET_A2(0);
		     break;
	case 3:IO_PGA_SET_A0(1);
	       IO_PGA_SET_A1(1);
         IO_PGA_SET_A2(0);
		     break;
	case 4:IO_PGA_SET_A0(0);
	       IO_PGA_SET_A1(0);
         IO_PGA_SET_A2(1);
		     break;
	case 5:IO_PGA_SET_A0(1);
	       IO_PGA_SET_A1(0);
         IO_PGA_SET_A2(1);
		     break;	
	case 6:IO_PGA_SET_A0(0);
	       IO_PGA_SET_A1(1);
         IO_PGA_SET_A2(1);
		     break;
	case 7:IO_PGA_SET_A0(1);
	       IO_PGA_SET_A1(1);
         IO_PGA_SET_A2(1);
		     break;
}
printf("IO_PGA_SET_A0:%d\r\n",(gain&0x01));
printf("IO_PGA_SET_A1:%d\r\n",((gain&0x02)>>1));
printf("IO_PGA_SET_A2:%d\r\n",((gain&0x04)>>2));
}
